"""Evaluator regressions; stdlib only, no Docker/dependencies needed."""
from contextlib import redirect_stderr, redirect_stdout
import io
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from runner.execution import run_command
from runner.run_task import main
from runner.verification import read_verdict
from runner.workspace import ROOT, TASKS, copy_workspace, fingerprint


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.junit = self.root / "junit.xml"

    def report(self, failures=0, errors=0, skipped=0, tests=1):
        children = "<failure/>" * failures + "<error/>" * errors + "<skipped/>" * skipped
        self.junit.write_text(
            f'<testsuites><testsuite tests="{tests}" failures="{failures}" '
            f'errors="{errors}" skipped="{skipped}">'
            f'<testcase classname="case" name="check">{children}</testcase>'
            '</testsuite></testsuites>', encoding="utf-8",
        )

    def test_assertion_failure_validates_only_baseline(self):
        self.report(failures=1)
        self.assertTrue(read_verdict(self.junit, 1, "baseline")["verified"])
        for mode in ("golden", "candidate"):
            self.assertFalse(read_verdict(self.junit, 1, mode)["verified"])

    def test_passing_tests_invalidate_baseline(self):
        self.report()
        self.assertFalse(read_verdict(self.junit, 0, "baseline")["verified"])
        self.assertTrue(read_verdict(self.junit, 0, "golden")["verified"])
        self.assertTrue(read_verdict(self.junit, 0, "candidate")["verified"])

    def test_infrastructure_exit_codes_never_validate_baseline(self):
        self.report(failures=1)
        for code in (None, -9, 2, 3, 4, 5, 125, 137):
            with self.subTest(code=code):
                result = read_verdict(self.junit, code, "baseline")
                self.assertEqual(result["status"], "error")
                self.assertFalse(result["verified"])

    def test_missing_or_malformed_report_is_error(self):
        self.assertEqual(read_verdict(self.junit, 1, "baseline")["status"], "error")
        self.junit.write_text("not XML", encoding="utf-8")
        self.assertEqual(read_verdict(self.junit, 1, "baseline")["status"], "error")

    def test_setup_errors_skips_and_empty_reports_are_invalid(self):
        for values in ({"errors": 1}, {"skipped": 1}, {"tests": 0}, {"tests": 2}):
            with self.subTest(values=values):
                self.report(**values)
                self.assertEqual(read_verdict(self.junit, 1, "baseline")["status"], "error")

    def test_exit_code_must_match_report(self):
        self.report(failures=1)
        self.assertEqual(read_verdict(self.junit, 0, "golden")["status"], "error")
        self.report()
        self.assertEqual(read_verdict(self.junit, 1, "baseline")["status"], "error")

    def test_command_timeout_keeps_logs(self):
        log = self.root / "run.log"
        started = time.monotonic()
        code, error = run_command([sys.executable, "-c", "import time; print('started', flush=True); time.sleep(30)"], log, 0.2)
        self.assertIsNone(code)
        self.assertIn("timeout", error)
        self.assertLess(time.monotonic() - started, 5)
        self.assertIn("started", log.read_text())

    def test_missing_executable_is_error(self):
        code, error = run_command([str(self.root / "missing")], self.root / "run.log", 1)
        self.assertIsNone(code)
        self.assertTrue(error)

    def test_copy_preserves_source_and_excludes_solutions(self):
        task = ROOT / "tasks" / TASKS["01"]
        before = fingerprint(task / "environment")
        destination = self.root / "candidate"
        copy_workspace(task / "environment", destination, task)
        self.assertTrue((destination / "app/main.py").is_file())
        self.assertTrue((destination / "requirements.txt").is_file())
        self.assertFalse((destination / "solution").exists())
        self.assertFalse((destination / "tests").exists())
        (destination / "app/main.py").write_text("changed", encoding="utf-8")
        self.assertEqual(fingerprint(task / "environment"), before)

    def test_symlinks_are_rejected_without_following(self):
        source = self.root / "source"
        source.mkdir()
        (source / "external").symlink_to(ROOT / "README.md")
        with self.assertRaisesRegex(ValueError, "symbolic links"):
            copy_workspace(source, self.root / "copy", ROOT / "tasks" / TASKS["01"])

    def test_prepare_exports_instruction_and_refuses_overwrite(self):
        destination = self.root / "candidate"
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--task", "01", "--prepare", str(destination)]), 0)
        self.assertTrue((destination / "instruction.md").is_file())
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            main(["--task", "01", "--prepare", str(destination)])
        self.assertEqual(error.exception.code, 2)

    def test_invalid_cli_combinations(self):
        cases = [
            ["--candidate", str(self.root)],
            ["--task", "01", "--mode", "candidate"],
            ["--task", "01", "--mode", "golden", "--candidate", str(self.root)],
            ["--task", "01", "--candidate", str(ROOT)],
            ["--timeout", "0"], ["--timeout", "nan"], ["--timeout", "inf"],
            ["--prepare", str(self.root / "new")],
        ]
        for args in cases:
            with self.subTest(args=args), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                main(args)
            self.assertEqual(error.exception.code, 2)

    def test_report_and_cli_exit_distinguish_failure_from_error(self):
        import json
        for status, verified, expected in [("passed", True, 0), ("failed", False, 1), ("error", False, 2)]:
            destination = self.root / status
            result = {"status": status, "verified": verified}
            with patch("runner.run_task.evaluate", return_value=result), redirect_stdout(io.StringIO()):
                code = main(["--task", "01", "--mode", "golden", "--output-dir", str(destination)])
            report = json.loads((destination / "report.json").read_text())
            self.assertEqual(code, expected)
            self.assertEqual(report["success"], verified)
            self.assertEqual(report["exit_code"], expected)


if __name__ == "__main__":
    unittest.main()
