/** Pure report boundary and metrics. No DOM, network, or evaluator execution. */
export const MAX_REPORT_BYTES = 2 * 1024 * 1024;
const MODES = new Set(["baseline", "golden", "candidate"]);
const STATUSES = new Set(["passed", "failed", "error"]);
const count = (value) => Number.isSafeInteger(value) && value >= 0;
const hash = (value) =>
  value === null || (typeof value === "string" && /^[a-f0-9]{64}$/.test(value));

export function validateReport(report) {
  const check = (condition, message) => {
    if (!condition) throw new Error(message);
  };
  check(
    report && report.schema_version === 1,
    "Expected a benchmark report with schema_version 1.",
  );
  check(
    ["docker", "local"].includes(report.engine),
    "Report engine must be docker or local.",
  );
  check(
    typeof report.created_at === "string" &&
      /^\d{4}-\d{2}-\d{2}T/.test(report.created_at) &&
      Number.isFinite(Date.parse(report.created_at)),
    "Report timestamp is invalid.",
  );
  check(
    typeof report.success === "boolean",
    "Report success must be a boolean.",
  );
  check(
    Array.isArray(report.results) &&
      report.results.length > 0 &&
      report.results.length <= 2000,
    "Report must contain between 1 and 2000 results.",
  );
  const seen = new Set();
  for (const result of report.results) {
    check(
      result &&
        typeof result.task === "string" &&
        /^[a-zA-Z0-9_-]{1,80}$/.test(result.task),
      "Invalid task ID.",
    );
    check(
      MODES.has(result.mode) && STATUSES.has(result.status),
      "Invalid result mode or status.",
    );
    const key = `${result.task}:${result.mode}`;
    check(!seen.has(key), "Duplicate task/mode result.");
    seen.add(key);
    check(
      typeof result.verified === "boolean",
      "Result verified must be a boolean.",
    );
    const expected =
      result.status !== "error" &&
      (result.mode === "baseline"
        ? result.status === "failed"
        : result.status === "passed");
    check(
      result.verified === expected,
      "Result verification disagrees with its mode and status.",
    );
    check(
      result.returncode === null || Number.isInteger(result.returncode),
      "Invalid process exit code.",
    );
    check(
      Number.isFinite(result.elapsed_seconds) && result.elapsed_seconds >= 0,
      "Invalid elapsed time.",
    );
    check(
      hash(result.workspace_sha256) && hash(result.verifier_sha256),
      "Invalid content fingerprint.",
    );
    check(
      Array.isArray(result.failed_tests) &&
        result.failed_tests.every((name) => typeof name === "string"),
      "Failed test names must be strings.",
    );
    if (result.tests === null) {
      check(
        result.status === "error",
        "Only execution errors may omit test counts.",
      );
      check(
        result.failed_tests.length === 0,
        "Missing counts cannot include failure names.",
      );
      continue;
    }
    const tests = result.tests;
    check(
      tests &&
        ["tests", "failures", "errors", "skipped"].every((key) =>
          count(tests[key]),
        ),
      "Test counts must be nonnegative safe integers.",
    );
    check(
      tests.failures + tests.errors + tests.skipped <= tests.tests,
      "Test outcomes exceed the total.",
    );
    check(
      result.failed_tests.length === tests.failures,
      "Failure names disagree with failure count.",
    );
    if (result.status !== "error") {
      check(
        tests.tests > 0 && tests.errors === 0 && tests.skipped === 0,
        "Successful evaluation needs nonempty, unskipped tests.",
      );
      check(
        (result.status === "failed") === tests.failures > 0,
        "Status disagrees with failure count.",
      );
      check(
        result.returncode === (result.status === "passed" ? 0 : 1),
        "Status disagrees with process exit code.",
      );
    }
  }
  check(
    Number.isSafeInteger(
      report.results.reduce(
        (sum, result) => sum + (result.tests?.tests ?? 0),
        0,
      ),
    ),
    "Aggregate test count exceeds the safe integer range.",
  );
  check(
    Number.isFinite(
      report.results.reduce((sum, result) => sum + result.elapsed_seconds, 0),
    ),
    "Aggregate elapsed time is invalid.",
  );
  check(
    report.success === report.results.every((result) => result.verified),
    "Overall success disagrees with results.",
  );
  const exit = report.results.some((result) => result.status === "error")
    ? 2
    : report.success
      ? 0
      : 1;
  check(report.exit_code === exit, "Overall exit code disagrees with results.");
  return report;
}

export function parseReport(text) {
  if (
    typeof text !== "string" ||
    new TextEncoder().encode(text).length > MAX_REPORT_BYTES
  ) {
    throw new Error("Report exceeds the 2 MiB limit.");
  }
  let report;
  try {
    report = JSON.parse(text);
  } catch {
    throw new Error("Report must be valid JSON.");
  }
  return validateReport(report);
}

export function passedCount(result) {
  return result?.tests
    ? result.tests.tests -
        result.tests.failures -
        result.tests.errors -
        result.tests.skipped
    : 0;
}

export function summarizeReport(report) {
  const groups = new Map();
  for (const result of report.results) {
    if (!groups.has(result.task)) groups.set(result.task, []);
    groups.get(result.task).push(result);
  }
  const baselines = report.results.filter(
    (result) => result.mode === "baseline",
  );
  const solutions = report.results.filter(
    (result) => result.mode !== "baseline",
  );
  return {
    groups,
    cases: [...groups.values()].reduce(
      (sum, results) =>
        sum + Math.max(...results.map((result) => result.tests?.tests ?? 0)),
      0,
    ),
    reproduced: baselines.filter((result) => result.verified).length,
    baselines: baselines.length,
    baselineFailures: baselines.reduce(
      (sum, result) => sum + (result.tests?.failures ?? 0),
      0,
    ),
    solutionPassed: solutions.reduce(
      (sum, result) => sum + passedCount(result),
      0,
    ),
    solutionTotal: solutions.reduce(
      (sum, result) => sum + (result.tests?.tests ?? 0),
      0,
    ),
    errors: report.results.filter((result) => result.status === "error").length,
    seconds: report.results.reduce(
      (sum, result) => sum + result.elapsed_seconds,
      0,
    ),
  };
}
