"""Interpret pytest evidence without confusing test failures with execution errors."""
from __future__ import annotations

from pathlib import Path
import xml.etree.ElementTree as ET


def read_verdict(junit: Path, returncode: int | None, mode: str) -> dict:
    """Only real test failures prove a baseline is broken."""
    verdict = {"status": "error", "verified": False, "tests": None, "failed_tests": []}
    if returncode not in (0, 1):
        return {**verdict, "error": f"pytest exited with {returncode}; expected 0 or 1"}
    try:
        root = ET.parse(junit).getroot()
        suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
        counts = {
            name: sum(int(suite.attrib[name]) for suite in suites)
            for name in ("tests", "failures", "errors", "skipped")
        }
        cases = list(root.iter("testcase"))
    except (OSError, ET.ParseError, KeyError, ValueError) as error:
        return {**verdict, "error": f"invalid or missing JUnit report: {error}"}
    verdict["tests"] = counts
    verdict["failed_tests"] = [
        f"{case.get('classname', '')}::{case.get('name', '')}"
        for case in cases if case.find("failure") is not None
    ]
    if not counts["tests"] or counts["tests"] != len(cases):
        return {**verdict, "error": "empty or inconsistent test report"}
    if counts["errors"] or counts["skipped"]:
        return {**verdict, "error": "collection/setup errors and skipped tests invalidate evaluation"}
    if len(verdict["failed_tests"]) != counts["failures"]:
        return {**verdict, "error": "inconsistent failure count"}
    if (returncode == 1) != (counts["failures"] > 0):
        return {**verdict, "error": "pytest exit code disagrees with test report"}
    passed = returncode == 0
    return {
        **verdict, "status": "passed" if passed else "failed",
        "verified": passed == (mode != "baseline"), "error": None,
    }


