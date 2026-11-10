"""CLI: export a task, validate reference solutions, or evaluate a candidate."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import shutil
import sys
import tempfile

from .execution import evaluate
from .workspace import ROOT, TASKS, copy_workspace


def positive_seconds(value):
    seconds = float(value)
    if not 0 < seconds <= 86400:
        raise argparse.ArgumentTypeError("timeout must be between 0 and 86400 seconds")
    return seconds


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", choices=[*TASKS, "all"], default="all")
    parser.add_argument("--mode", choices=["baseline", "golden", "both", "candidate"])
    parser.add_argument("--engine", choices=["docker", "local"], default="docker")
    parser.add_argument("--candidate", type=Path, help="full candidate workspace for a single task")
    parser.add_argument("--prepare", type=Path, help="export one task to a new candidate directory")
    parser.add_argument("--output-dir", type=Path, help="new directory for JSON, logs and JUnit")
    parser.add_argument("--timeout", type=positive_seconds, default=120, help="verifier timeout (seconds)")
    parser.add_argument("--build-timeout", type=positive_seconds, default=600)
    args = parser.parse_args(argv)
    mode = args.mode or ("candidate" if args.candidate else "both")
    if args.candidate or args.prepare or mode == "candidate":
        if args.task == "all":
            parser.error("candidate/prepare requires a single --task")
    if (mode == "candidate") != (args.candidate is not None):
        parser.error("--candidate and --mode candidate must be used together")
    if args.prepare and (args.candidate or args.mode or args.output_dir):
        parser.error("--prepare cannot be combined with --candidate, --mode or --output-dir")
    if args.candidate:
        args.candidate = args.candidate.resolve()
        if not args.candidate.is_dir():
            parser.error("candidate directory does not exist")
        protected = ROOT / "tasks"
        if (args.candidate == ROOT or args.candidate in ROOT.parents
                or protected == args.candidate or protected in args.candidate.parents):
            parser.error("export a candidate outside tasks/; do not expose benchmark solutions")
    if args.prepare:
        destination = args.prepare.resolve()
        if destination.exists():
            parser.error("prepare destination already exists; choose a new directory")
        task = ROOT / "tasks" / TASKS[args.task]
        if ROOT / "tasks" in destination.parents:
            parser.error("prepare destination must be outside tasks/")
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(dir=destination.parent) as tmp:
                exported = Path(tmp) / "workspace"
                copy_workspace(task / "environment", exported, task)
                shutil.copy2(task / "instruction.md", exported / "instruction.md")
                exported.rename(destination)
        except (OSError, ValueError) as error:
            parser.error(str(error))
        print(f"Prepared task {args.task}: {destination}")
        return 0
    if args.engine == "local" and sys.version_info < (3, 12):
        parser.error("local execution requires Python 3.12+; Docker runner supports Python 3.9+")
    try:
        if args.output_dir:
            output = args.output_dir.resolve()
            if ROOT / "tasks" in output.parents:
                parser.error("output directory must be outside tasks/")
            if args.candidate and args.candidate in output.parents:
                parser.error("output directory must be outside candidate workspace")
            output.mkdir(parents=True, exist_ok=False)
        else:
            (ROOT / "artifacts").mkdir(exist_ok=True)
            output = Path(tempfile.mkdtemp(prefix="run-", dir=ROOT / "artifacts"))
    except OSError as error:
        parser.error(str(error))
    choices = list(TASKS) if args.task == "all" else [args.task]
    modes = ["baseline", "golden"] if mode == "both" else [mode]
    results = []
    for task_id in choices:
        for current_mode in modes:
            print(f"Running {task_id} {current_mode} ({args.engine})", flush=True)
            result = evaluate(
                task_id, current_mode, args.engine, output, args.timeout, args.build_timeout,
                args.candidate,
            )
            results.append(result)
            print(json.dumps(result, ensure_ascii=False), flush=True)
    success = all(result["verified"] for result in results)
    exit_code = 2 if any(result["status"] == "error" for result in results) else (0 if success else 1)
    report = {
        "schema_version": 1, "created_at": datetime.now(timezone.utc).isoformat(),
        "engine": args.engine, "runner_python": platform.python_version(),
        "platform": platform.platform(), "timeout_seconds": args.timeout,
        "build_timeout_seconds": args.build_timeout, "results": results,
        "success": success, "exit_code": exit_code,
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("BENCHMARK VALIDATION:", "PASS" if success else "FAIL", flush=True)
    print(f"Report: {output / 'report.json'}", flush=True)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
