import {
  MAX_REPORT_BYTES,
  parseReport,
  passedCount,
  summarizeReport,
} from "./report.mjs";

const $ = (id) => document.getElementById(id);
const catalog = {
  "01": {
    title: "Banking API",
    subtitle: "Validation · HTTP status · Decimal",
    slug: "01-broken-banking-api",
  },
  "02": {
    title: "CI pipeline",
    subtitle: "Fail-fast tests · Reproducible builds",
    slug: "02-broken-ci-pipeline",
  },
  "03": {
    title: "Transaction retries",
    subtitle: "SQLite · Cross-process idempotency",
    slug: "03-duplicate-transactions",
  },
};
const modeName = {
  baseline: "Baseline",
  golden: "Reference",
  candidate: "Candidate",
};
let currentReport;
let summary;
let selectedTask;
let selectedMode = "baseline";
let downloadUrl;

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function outcome(result) {
  if (!result) return ["Not evaluated", ""];
  if (result.status === "error") return ["Execution error", "error"];
  if (result.mode === "baseline")
    return result.verified
      ? ["Bug reproduced", "amber"]
      : ["Baseline passed", "error"];
  return result.verified ? ["All checks pass", ""] : ["Tests failed", "error"];
}

function resultCell(result, label) {
  const cell = element("div");
  const [text, color] = outcome(result);
  cell.append(element("span", `result-badge ${color}`, text));
  const detail = element(
    "span",
    "result-sub",
    result?.tests
      ? `${passedCount(result)} / ${result.tests.tests} pass · ${result.tests.failures} fail`
      : result
        ? "No test report"
        : "Not in this report",
  );
  detail.dataset.mode = label;
  cell.append(detail);
  return cell;
}

function renderTasks() {
  const rows = [];
  for (const [id, results] of summary.groups) {
    const info = catalog[id] ?? {
      title: `Challenge ${id}`,
      subtitle: "Imported benchmark task",
    };
    const row = element("button", "task-row");
    row.type = "button";
    row.setAttribute("aria-label", `Inspect challenge ${id}: ${info.title}`);
    row.setAttribute("aria-pressed", String(id === selectedTask));
    const identity = element("span", "task-identity");
    const description = element("span");
    description.append(
      element("strong", "", info.title),
      element("small", "", info.subtitle),
    );
    identity.append(element("span", "task-number", id), description);
    row.append(
      identity,
      resultCell(
        results.find((result) => result.mode === "baseline"),
        "Baseline",
      ),
      resultCell(
        results.find((result) => result.mode !== "baseline"),
        "Solution",
      ),
      element("span", "row-chevron", "›"),
    );
    row.addEventListener("click", () => {
      selectedTask = id;
      renderTasks();
      renderEvidence();
    });
    rows.push(row);
  }
  $("task-rows").replaceChildren(...rows);
}

function renderEvidence() {
  const results = summary.groups.get(selectedTask);
  if (!results.some((result) => result.mode === selectedMode))
    selectedMode = results[0].mode;
  const result = results.find((result) => result.mode === selectedMode);
  const info = catalog[selectedTask];
  $("selected-id").textContent = selectedTask;
  $("selected-title").textContent = info?.title ?? `Challenge ${selectedTask}`;
  $("mode-controls").replaceChildren(
    ...results.map((item) => {
      const button = element("button", "", modeName[item.mode]);
      button.type = "button";
      button.setAttribute("aria-pressed", String(item.mode === selectedMode));
      button.addEventListener("click", () => {
        selectedMode = item.mode;
        renderEvidence();
      });
      return button;
    }),
  );
  $("evidence-mode").textContent =
    `${modeName[result.mode]} · EXIT ${result.returncode ?? "UNAVAILABLE"}`;
  $("evidence-status").textContent =
    result.status === "error"
      ? "Evaluation interrupted."
      : result.mode === "baseline" && result.verified
        ? "The bug is reproducible."
        : result.verified
          ? "Every check passed."
          : "The contract is not met.";
  $("evidence-description").textContent =
    result.status === "error"
      ? result.error || "Check the original execution log."
      : result.mode === "baseline"
        ? result.verified
          ? "Real test failures expose the original behavior. This is expected for a valid task."
          : "The original code passed every check. This run does not prove an intentional bug."
        : "Independent verifier cases check the submitted behavior against the written task contract.";
  $("outcome-counts").replaceChildren(
    ...[
      ["Passed", passedCount(result), ""],
      ["Failed", result.tests?.failures ?? "—", "failed"],
      ["Seconds", result.elapsed_seconds.toFixed(2), ""],
    ].map(([label, value, color]) => {
      const node = element("span", color);
      node.append(element("strong", "", value), document.createTextNode(label));
      return node;
    }),
  );
  $("task-instruction").hidden = !info;
  if (info)
    $("task-instruction").href = `../../tasks/${info.slug}/instruction.md`;
  $("test-list-label").textContent = result.failed_tests.length
    ? "OBSERVED TEST FAILURES"
    : "VERIFIER OUTCOME";
  $("test-list-count").textContent = `${result.tests?.tests ?? "—"} checks`;
  const names = result.failed_tests.map((name) =>
    element("div", "test-name", name),
  );
  $("test-list").replaceChildren(...names.slice(0, 5));
  $("remaining-tests").replaceChildren(...names.slice(5));
  $("more-failures").hidden = names.length <= 5;
  $("more-failures").open = false;
  $("more-label").textContent = `Show all ${names.length} failures`;
  if (!names.length) {
    const state = element(
      "div",
      `test-success ${result.status === "error" ? "error" : ""}`,
    );
    state.append(
      element(
        "strong",
        "",
        result.status === "error"
          ? "No complete evaluation"
          : `${passedCount(result)} checks passed`,
      ),
      element(
        "p",
        "",
        result.status === "error"
          ? "Execution errors never count as valid baseline failures."
          : "No failed, skipped or errored verifier cases.",
      ),
    );
    $("test-list").append(state);
  }
  for (const [id, value] of [
    ["workspace-hash", result.workspace_sha256],
    ["verifier-hash", result.verifier_sha256],
  ]) {
    $(id).textContent = value ? `${value.slice(0, 18)}…` : "Unavailable";
    $(id).title = value ?? "Unavailable";
  }
}

function showReport(report, source, text) {
  currentReport = report;
  summary = summarizeReport(report);
  selectedTask = summary.groups.keys().next().value;
  selectedMode = report.results[0].mode;
  const date = new Date(report.created_at);
  $("run-status").textContent = report.success
    ? "Evaluation verified"
    : "Review required";
  $("run-status").classList.toggle("warn", !report.success);
  $("run-date").textContent = new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(date);
  const clock = new Intl.DateTimeFormat("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: "UTC",
  }).format(date);
  $("run-meta").textContent =
    `${report.engine === "docker" ? "Docker" : "Local"} · ${clock} UTC · ${summary.seconds.toFixed(1)}s total`;
  $("nav-count").textContent = summary.groups.size;
  $("case-count").textContent = summary.cases;
  $("case-caption").textContent =
    `Across ${summary.groups.size} independent challenge${summary.groups.size === 1 ? "" : "s"}`;
  $("reproduced-count").textContent = summary.baselines
    ? `${summary.reproduced} / ${summary.baselines}`
    : "—";
  $("reproduced-caption").textContent = summary.baselines
    ? `${summary.baselineFailures} expected failing checks`
    : "No baselines in this report";
  $("solution-count").textContent = summary.solutionTotal
    ? `${summary.solutionPassed} / ${summary.solutionTotal}`
    : "—";
  $("solution-label").firstChild.textContent = report.results.some(
    (result) => result.mode === "candidate",
  )
    ? "Solution checks "
    : "Reference checks ";
  const hasCandidate = report.results.some(
    (result) => result.mode === "candidate",
  );
  $("scoring-explainer").textContent = hasCandidate
    ? "A candidate passes only when every verifier check passes. Errors, skips and missing evidence invalidate evaluation."
    : "Both expectations must hold: the original code fails real tests, and the reference fix passes every check.";
  $("interpretation-title").textContent = hasCandidate
    ? "Submission result ≠ model ranking"
    : "Reference validation ≠ AI score";
  $("interpretation-copy").textContent = hasCandidate
    ? "Model identity and trial budgets are not captured by this report."
    : "This report validates reference fixes, not model performance.";
  $("error-count").textContent = summary.errors;
  $("suite-title").textContent =
    summary.groups.size === 3
      ? "Three bugs. One clear contract."
      : `${summary.groups.size} challenge${summary.groups.size === 1 ? "" : "s"}. One clear contract.`;
  $("suite-meta").textContent =
    `${summary.groups.size} TASK${summary.groups.size === 1 ? "" : "S"} · ${report.results.length} EVALUATION${report.results.length === 1 ? "" : "S"}`;
  $("source-label").textContent = `Source: ${source}`;
  $("load-error").hidden = true;
  $("load-state").hidden = true;
  $("report-view").hidden = false;
  if (downloadUrl) URL.revokeObjectURL(downloadUrl);
  downloadUrl = text
    ? URL.createObjectURL(new Blob([text], { type: "application/json" }))
    : null;
  $("download-report").href = downloadUrl ?? "../evaluation-results.json";
  renderTasks();
  renderEvidence();
}

function showError(error) {
  $("load-state").hidden = true;
  $("load-error").hidden = false;
  $("load-error").textContent =
    `${error.message} ${currentReport ? "The previous report remains displayed." : "Serve this project over HTTP, or open a valid report using the button above."}`;
}

$("open-report").addEventListener("click", () => $("report-file").click());
$("report-file").addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  try {
    if (file.size > MAX_REPORT_BYTES)
      throw new Error("Report exceeds the 2 MiB limit.");
    const text = await file.text();
    showReport(parseReport(text), file.name, text);
  } catch (error) {
    showError(error);
  }
  event.target.value = "";
});

try {
  const response = await fetch("../evaluation-results.json", {
    cache: "no-store",
  });
  if (!response.ok)
    throw new Error(
      `Recorded report could not be loaded (HTTP ${response.status}).`,
    );
  showReport(
    parseReport(await response.text()),
    "docs/evaluation-results.json",
  );
} catch (error) {
  showError(error);
}
