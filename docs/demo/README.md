# Benchmark Explorer

A static, browser-based viewer for evaluator reports. It presents the actual measured task outcomes, failed test names, execution time and input fingerprints. It does not run an agent, submit code or start an evaluation.

## Run

From the repository root:

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

Open [the viewer](http://127.0.0.1:8000/docs/demo/). No build step, frontend framework, package installation, external font or analytics service is required. Keep the repository's directory structure when serving it so documentation and task-contract links resolve.

The initial report is [evaluation-results.json](../evaluation-results.json), produced by a real Docker baseline/reference run. The page labels it as a **recorded evaluation**; opening the viewer does not refresh its measurements automatically.

## Explore a report

1. Select a challenge to inspect its evidence.
2. Choose **Baseline**, **Reference** or **Candidate**, depending on which modes exist in the report.
3. Expand the failure list to read all observed failing testcase names.
4. Follow **Read task contract** to compare evidence with the written requirements.
5. Use **Download source report** to inspect the underlying JSON.

**Open report** reads a JSON file locally using the browser File API. It does not upload the report to a server. Imports are limited to 2 MiB and checked before rendering. Invalid imports show an error while keeping the previous valid report visible.

A candidate-only report displays no fabricated baseline. An execution-error report remains an error, not a reproduced bug. Reference or candidate results are not model rankings.

## Source layout

| File | Responsibility |
|---|---|
| `index.html` | Semantic markup and accessible controls |
| `styles.css` | Layout, focus, color and responsive breakpoints |
| `report.mjs` | Pure report validation, grouping and metric calculations |
| `app.mjs` | Fetch/file input, selected task/mode and safe DOM rendering |

Report text uses `textContent`. The pure model has no DOM or network access, and can be tested with Node.js 18+:

```bash
node tests/test_demo.mjs
```

Run this command from the repository root. It checks the recorded counts, 19 invalid report mutations, malformed/oversized input, candidate-only data and execution errors. The 81 unique verifier cases must not be counted as 162 by adding baseline and reference runs together.

## Browser checks performed

Checked locally on 10 November 2026:

- Initial report: 81 cases, 3/3 reproduced baselines, 81/81 reference checks and zero execution errors.
- Task 03 selection: 2 passing and 23 failing baseline cases; reference mode: 25 passing cases.
- Failure disclosure: all 23 transaction failure names become visible.
- Invalid report import: visible error, previous valid results preserved.
- Candidate-only report import: 46/46 passing checks, absent baseline shown as not evaluated.
- Desktop 1440-pixel and narrow 390-pixel layouts: document width matches viewport width, with no horizontal overflow.
- Keyboard entry reaches the skip link; its target receives focus on the main content.
- No browser console errors were observed during the final check.

## Screenshot provenance

The images under `docs/images/` are unmodified browser captures of this working viewer, not mockups, generated artwork or manually drawn terminal output.

| Image | Captured state | Browser viewport |
|---|---|---|
| [benchmark-overview.jpg](../images/benchmark-overview.jpg) | Recorded Docker suite, task 01 selected | 1440 × 1000 |
| [transaction-evidence.jpg](../images/transaction-evidence.jpg) | Task 03 baseline, observed transaction failures | 1440 × 1000 |
| [benchmark-mobile.jpg](../images/benchmark-mobile.jpg) | Same recorded report at a narrow breakpoint | 390 × 844 |

Source: `docs/evaluation-results.json`, timestamp **2026-11-10T08:16:59.771705+00:00**. Captures: **10 November 2026**. The report records 3 reproduced baselines, 81/81 passing reference checks, 53 expected baseline failures and no execution errors. Browser screenshots are JPEG; the files preserve the screenshot bytes.

The README embeds the overview and links the evidence view so visitors can understand the project without running it. A screenshot is evidence of the local report viewer; it does not prove remote CI or AI-agent performance.

## Refresh evidence

1. Run the evaluator into a new artifact directory:

   ```bash
   python3 -m runner.run_task --task all --mode both --engine docker --output-dir artifacts/new-demo-run
   ```

2. Inspect JSON, JUnit and logs. Require real baseline failures, complete reference success and no error/skip.
3. Copy the selected `report.json` to `docs/evaluation-results.json`. Update measured counts/timing in `docs/evaluation-results.md` and any demo assertions if the suite changed.
4. Run `node tests/test_demo.mjs`, serve the repository and reload the browser. Check both wide and narrow layouts, including no horizontal overflow.
5. Capture the overview from the page top; select task 03 and navigate to **Test evidence** for the detail image. Take the narrow-layout image from the page top.
6. Save actual screenshots under the documented filenames, update this provenance section and keep the displayed report unchanged between captures.
7. Check valid/invalid file imports, task and mode selection, failure-list expansion and keyboard focus. Do not replace real evidence with hand-edited screenshots.

Static hosting can serve the repository without a build step. No public deployment is configured here; local preview instructions do not claim a hosted URL exists.
