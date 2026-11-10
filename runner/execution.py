"""Execute one evaluation and own subprocess/container cleanup."""
from __future__ import annotations

import os
from pathlib import Path
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import uuid

from .verification import read_verdict
from .workspace import ROOT, TASKS, copy_workspace, fingerprint


def run_command(args, log: Path, timeout: float, *, cwd=None, env=None):
    """Keep logs on disk and kill process group on timeout/interruption."""
    with log.open("a", encoding="utf-8") as output:
        output.write("+ " + shlex.join(map(str, args)) + "\n")
        output.flush()
        try:
            process = subprocess.Popen(
                args, cwd=cwd, env=env, stdout=output, stderr=subprocess.STDOUT,
                start_new_session=os.name == "posix",
            )
        except OSError as error:
            return None, str(error)
        try:
            return process.wait(timeout=timeout), None
        except BaseException as error:
            try:
                if os.name == "posix":
                    os.killpg(process.pid, signal.SIGKILL)
                else:
                    process.kill()
            except ProcessLookupError:
                pass
            process.wait()
            if isinstance(error, subprocess.TimeoutExpired):
                return None, f"command exceeded {timeout:g}s timeout"
            raise


def evaluate(task_id, mode, engine, output, timeout, build_timeout, candidate=None):
    task = ROOT / "tasks" / TASKS[task_id]
    label = f"{task_id}-{mode}"
    logs = output / label
    logs.mkdir()
    junit = logs / "junit.xml"
    log = logs / "run.log"
    result = {
        "task": task_id, "mode": mode, "status": "error", "verified": False,
        "tests": None, "failed_tests": [], "returncode": None, "error": None,
        "log": f"{label}/run.log", "junit": f"{label}/junit.xml",
        "build_seconds": 0, "workspace_sha256": None,
        "verifier_sha256": fingerprint(task / "tests"),
    }
    started = time.monotonic()
    identity = "swe-rl-" + uuid.uuid4().hex
    try:
        with tempfile.TemporaryDirectory(prefix="swe-rl-") as tmp:
            workspace = Path(tmp) / "workspace"
            copy_workspace(candidate or task / "environment", workspace, task)
            if mode == "golden":
                shutil.copytree(task / "solution" / "files", workspace, dirs_exist_ok=True)
            result["workspace_sha256"] = fingerprint(workspace)
            if engine == "docker":
                build_started = time.monotonic()
                code, error = run_command(
                    ["docker", "build", "--progress=plain", "-t", identity, str(workspace)],
                    log, build_timeout,
                )
                result["build_seconds"] = round(time.monotonic() - build_started, 3)
                if error or code:
                    result["error"] = error or f"Docker build exited with {code}"
                    return result
                args = [
                    "docker", "run", "--rm", "--name", identity, "--network", "none",
                    "--memory", "512m", "--cpus", "1", "--pids-limit", "128",
                    "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
                    "--tmpfs", "/tmp:rw,size=64m",
                    "--mount", f"type=bind,src={task / 'tests'},dst=/verifier,readonly",
                    "--mount", f"type=bind,src={logs},dst=/results",
                    "-e", "PYTHONPATH=/workspace", "-e", "PYTHONDONTWRITEBYTECODE=1",
                    "-e", "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1", identity,
                ]
                test_root, report_path = "/verifier", "/results/junit.xml"
                env = None
            else:
                args = []
                test_root, report_path = str(task / "tests"), str(junit)
                env = os.environ.copy()
                env.update({
                    "PYTHONPATH": str(workspace), "PYTHONDONTWRITEBYTECODE": "1",
                    "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTEST_ADDOPTS": "",
                    "PYTEST_PLUGINS": "",
                })
            args += [
                "python" if engine == "docker" else sys.executable,
                "-m", "pytest", "-q", "-p", "no:cacheprovider", "-c", os.devnull,
                "--import-mode=importlib", f"--confcutdir={test_root}",
                f"--junitxml={report_path}", test_root,
            ]
            code, error = run_command(args, log, timeout, cwd=workspace, env=env)
            result["returncode"] = code
            result.update(read_verdict(junit, code, mode))
            if error:
                result["error"] = error
    except (OSError, ValueError) as error:
        result["error"] = str(error)
    finally:
        if engine == "docker":
            for args in (["docker", "rm", "-f", identity], ["docker", "image", "rm", identity]):
                run_command(args, log, 15)
        result["elapsed_seconds"] = round(time.monotonic() - started, 3)
    return result


