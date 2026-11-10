# Measured evaluation results

## Published run

Measured on **10 November 2026 at 15:16 (UTC+7)**, following the evaluator module refactor. The source report timestamp is `2026-11-10T08:16:59.771705+00:00`.

- Host: macOS 26.4.1, Apple Silicon arm64.
- Docker Engine: 29.7.2; container Python: 3.12.16.
- Orchestrator Python: 3.9.6; evaluator uses the standard library.
- Dependencies: exact direct/transitive versions in `requirements.txt`.
- Base image: `python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b`.

Command actually executed:

```bash
python3 -m runner.run_task --task all --mode both --engine docker --output-dir artifacts/english-demo-validation
```

| Challenge | Verifier cases | Baseline pass / fail | Reference pass / fail | Verdict |
|---|---:|---:|---:|---|
| 01 — Banking API | 46 | 22 / 24 | 46 / 0 | Verified |
| 02 — CI pipeline | 10 | 4 / 6 | 10 / 0 | Verified |
| 03 — SQLite retries | 25 | 2 / 23 | 25 / 0 | Verified |
| **Total** | **81** | **28 / 53** | **81 / 0** | **PASS** |

All six evaluations had zero collection/setup errors and zero skipped tests. Baselines exited 1 because real testcases failed; references exited 0. The aggregate CLI exited **0**, with `success: true`.

Elapsed time includes build, startup, verification and cleanup:

| Challenge | Baseline | Reference |
|---|---:|---:|
| 01 | 3.858 s | 1.253 s |
| 02 | 1.802 s | 2.202 s |
| 03 | 1.471 s | 1.598 s |

This is a single measurement with build cache available, not a cold-start benchmark or performance distribution. Timing does not measure AI quality.

The selected report is preserved as [evaluation-results.json](evaluation-results.json). Full logs and JUnit live in `artifacts/english-demo-validation/` in the execution workspace. Report evidence paths are relative to that original artifact directory, not to `docs/`.

## Evaluator regression checks

```bash
python3 -m unittest discover -s tests -v
```

**13/13 checks passed** after the refactor on host Python 3.9.6. They cover mode-specific verdicts, infrastructure exit codes, missing/malformed evidence, setup errors/skips, inconsistent counts, command timeout, source preservation, safe exports, symbolic-link rejection, CLI arguments and report exit codes.

## Demo report checks

```bash
node tests/test_demo.mjs
```

The native JavaScript checks pass against the published report. Coverage includes metrics without double-counting baseline/reference cases, malformed or oversized JSON, invalid counts/statuses/fingerprints, duplicate task modes, candidate-only reports, failed submissions and execution errors.

Browser checks and real screenshot provenance are documented in the [demo guide](demo/README.md). The viewer reads this report; its metrics are not manually entered.

## Earlier execution-path checks

Earlier checks on 10 November 2026, before the internal module split, are retained as supporting evidence:

- Python 3.12 dependency check: `No broken requirements found.`
- Evaluator regressions: 13/13 passed inside Python 3.12.
- Local engine inside a Python 3.12 Linux container: same task outcomes, references 81/81, baselines 53 expected failures.
- Repo was mounted read-only during that local-engine check. This does not claim native Python 3.12/macOS verification.

Candidate end-to-end checks used an exported task 01 workspace:

| Scenario | Test status | Runner exit |
|---|---|---:|
| Reference fix submitted as candidate | `passed` | 0 |
| Original buggy code submitted as candidate | `failed` | 1 |
| Import-time exception | `error` | 2 |
| Import hangs; 3-second timeout | `error` | 2 |

All outcomes matched expectations; no evaluation container remained after timeout. Supporting artifacts are under `artifacts/candidate-*/`, `artifacts/smoke-summary.json`, `artifacts/local-check.log` and `artifacts/validation-local/` on the execution machine.

## What the evidence supports

The authored tasks detect their intended defects, reference solutions meet their verifier contracts, and evaluator failure paths distinguish submission failures from execution failures. Task 03 checks process/thread concurrency, persistence and SQL uniqueness. Task 02 checks test/compile failure gates, repeated builds and source-dependent hashes.

**No AI-model score or RL-training result is claimed.** No pass@k, peak-memory measurement, adversarial certification or difficulty calibration was performed. GitHub Actions is configured but has not been executed remotely from this workspace. Linux amd64 and Windows were not verified in this measured run.

## Reproduce

```bash
python3 -m unittest discover -s tests -v
node tests/test_demo.mjs
python3 -m runner.run_task --task all --mode both --engine docker
```

If supplying `--output-dir`, choose a new directory. Compare counts, failure names and workspace/verifier hashes against the published JSON. File or dependency changes may change fingerprints; timing can vary. Refresh published evidence instead of reusing stale measurements.
