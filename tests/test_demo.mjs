/** Report logic regression checks. Run: node tests/test_demo.mjs */
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import {
  MAX_REPORT_BYTES,
  parseReport,
  passedCount,
  summarizeReport,
  validateReport,
} from "../docs/demo/report.mjs";

const text = await readFile(
  new URL("../docs/evaluation-results.json", import.meta.url),
  "utf8",
);
const report = parseReport(text);
const summary = summarizeReport(report);
assert.equal(summary.groups.size, 3);
assert.equal(summary.cases, 81); // Baseline and golden share cases; do not count 162.
assert.equal(summary.reproduced, 3);
assert.equal(summary.baselineFailures, 53);
assert.equal(summary.solutionPassed, 81);
assert.equal(summary.solutionTotal, 81);
assert.equal(summary.errors, 0);
assert.equal(passedCount(report.results[0]), 22);
assert.equal(passedCount({ tests: null }), 0);
assert.throws(() => parseReport("{"), /valid JSON/);
assert.throws(() => parseReport(" ".repeat(MAX_REPORT_BYTES + 1)), /2 MiB/);

const invalid = [
  (data) => {
    data.schema_version = 2;
  },
  (data) => {
    data.engine = "unknown";
  },
  (data) => {
    data.created_at = "yesterday";
  },
  (data) => {
    data.results = [];
  },
  (data) => {
    data.results.push(data.results[0]);
  },
  (data) => {
    data.results[0].task = "<img onerror=alert(1)>";
  },
  (data) => {
    data.results[0].tests.tests = -1;
  },
  (data) => {
    data.results[0].tests.failures = 1.5;
  },
  (data) => {
    data.results[0].tests.skipped = 100;
  },
  (data) => {
    data.results[0].tests = null;
  },
  (data) => {
    data.results[0].verified = false;
  },
  (data) => {
    data.results[0].failed_tests = ["incomplete"];
  },
  (data) => {
    data.results[0].returncode = 0;
  },
  (data) => {
    data.results[0].elapsed_seconds = Infinity;
  },
  (data) => {
    data.results[0].workspace_sha256 = "invalid";
  },
  (data) => {
    data.success = false;
  },
  (data) => {
    data.exit_code = 2;
  },
  (data) => {
    for (const result of data.results)
      result.tests.tests = Number.MAX_SAFE_INTEGER;
  },
  (data) => {
    for (const result of data.results)
      result.elapsed_seconds = Number.MAX_VALUE;
  },
];
for (const mutate of invalid) {
  const data = structuredClone(report);
  mutate(data);
  assert.throws(() => validateReport(data));
}

const candidate = structuredClone(report);
candidate.results = [
  candidate.results.find((result) => result.mode === "golden"),
];
candidate.results[0].mode = "candidate";
assert.equal(validateReport(candidate).success, true);
assert.equal(summarizeReport(candidate).baselines, 0);
assert.equal(summarizeReport(candidate).cases, 46);
assert.equal(summarizeReport(candidate).solutionPassed, 46);

const failure = structuredClone(report);
failure.results = [failure.results[0]];
failure.results[0].mode = "candidate";
failure.results[0].verified = false;
failure.success = false;
failure.exit_code = 1;
assert.equal(validateReport(failure).success, false);

const error = structuredClone(report);
error.results = [
  {
    ...error.results[0],
    status: "error",
    verified: false,
    tests: null,
    failed_tests: [],
    returncode: null,
    error: "timeout",
    workspace_sha256: null,
  },
];
error.success = false;
error.exit_code = 2;
assert.equal(validateReport(error).exit_code, 2);
assert.equal(summarizeReport(error).errors, 1);

console.log(
  `Demo report checks: PASS (recorded data, ${invalid.length} invalid inputs, candidate, failure, execution error)`,
);
