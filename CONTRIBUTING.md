# Contributing

Read [AGENTS.md](AGENTS.md) and the [project rules](rules/README.md) before editing. All documentation, comments, errors and UI text must be in English.

## Development checks

From the repository root:

```bash
python3 -m unittest discover -s tests -v
node tests/test_demo.mjs
```

Python checks use the standard library; demo checks use Node.js 18+ built-in assertions. No test framework installation is needed for these fast checks.

For changes to runner behavior, contracts, verifiers, reference fixes, dependencies or Dockerfiles:

```bash
python3 -m runner.run_task --task all --mode both --engine docker
```

Verifier dependencies are installed inside Docker, not into your system Python. Existing output directories are deliberately never overwritten.

## Module ownership

- CLI flags, argument checks and final JSON publication: `runner/run_task.py`.
- Task registration, copying and fingerprints: `runner/workspace.py`.
- Process execution, timeouts and cleanup: `runner/execution.py`.
- Scoring from pytest/JUnit: `runner/verification.py`.
- Report schema validation and UI metrics: `docs/demo/report.mjs`.
- Browser state and rendering: `docs/demo/app.mjs`.

Keep functions in the module that owns their responsibility. Do not add generic layers or dependencies for behavior already covered by standard libraries or browser features.

## Add a challenge

1. Create `tasks/<id>-<name>/` with `instruction.md`, `environment/`, `tests/` and `solution/files/`.
2. Define inputs, outputs, errors, bounds and out-of-scope behavior. Do not include solution hints in the contract.
3. Put intentionally broken code in `environment/`. Keep the reference fix and external verifier outside this directory. Reuse the pinned Docker base and evaluator-supplied `requirements.txt`.
4. Write behavior-focused verifiers with at least one failing baseline case and valid inputs that prevent a reject-everything submission from passing.
5. Put minimal replacement files under `solution/files/`, preserving relative paths. Overlays support added/replaced files, including hidden files; deletion overlays are outside current scope.
6. Register the task in `runner/workspace.py::TASKS`; update the CI matrix, demo presentation metadata, published counts and relevant tests/documentation.
7. Run baseline and golden together. Require genuine baseline failures, full golden success and no error/skip. Inspect failure names and logs, not only the final verdict.
8. Export with `--prepare`, grade with `--candidate` and confirm no reference/verifier leakage. Record actual results and refresh public evidence when appropriate.

## Change an existing challenge

- Keep the original intentional defect intact. Repair the reference overlay or a separate candidate workspace.
- Update instruction, verifier and reference solution together when changing the contract.
- Assert observable behavior. Do not require exact error wording unless the contract needs it.
- Concurrency tests use independent temporary databases. Cross-process guarantees need process tests, not only threads.
- Reproducibility checks compare output bytes and confirm changed source changes the digest.
- Verifiers must not depend on network or external services. Nested subprocess timeouts must fit inside the evaluation timeout.
- Never weaken tests just to make the reference pass. Explain and verify legitimate contract/test corrections.

## Update dependencies

`requirements.txt` pins direct and transitive versions. Resolve updates in a clean Python 3.12 environment, run `pip check`, record exact versions and rerun Docker validation. Do not freeze an unrelated system environment.

Update the base-image digest in all task Dockerfiles together. Version pinning does not replace artifact hashes or dependency security review. No frontend dependencies are currently required.

## Update the demo and screenshots

Serve the repository using `python3 -m http.server 8000 --bind 127.0.0.1`, then open `/docs/demo/`. Test task/mode selection, valid/invalid report imports, keyboard access and narrow/wide layouts. Run the demo report checks.

Screenshots must show the actual running viewer backed by an actual report. Follow [capture instructions](docs/demo/README.md); keep source report and screenshots synchronized. Never create fake terminal output or present a recorded run as a live service.

## Preserve honest evidence

- Distinguish goals, expectations and measured results.
- Dependency failures do not prove a baseline is valid.
- Reference passes do not mean an AI model solved the tasks.
- Public verifier code is not a hidden evaluation set.
- Do not commit full `artifacts/`, environments, candidates, caches or secrets. Curated public reports belong in `docs/`.
- Only add repository badges or deployment links when real URLs and outcomes exist.
- Update canonical rules in `rules/`; keep tool-specific adapters short and linked to that source.
