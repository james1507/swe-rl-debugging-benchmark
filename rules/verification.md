# Verification and evidence rules

- Run `python3 -m unittest discover -s tests -v` for runner changes.
- Run `node tests/test_demo.mjs` for report validation or demo changes.
- Run all Docker baseline/golden evaluations for changes to execution, task contracts, verifiers, reference solutions, dependencies or Dockerfiles.
- Keep actual failure names, exit codes, test counts and hashes. Infrastructure failures do not prove that a task is valid.
- For browser work, check loading, task selection, mode selection, report import/error behavior and a narrow layout.
- Capture screenshots from the real running viewer after its report has loaded. Do not draw fake terminal output or use AI-generated screenshots.
- Record source report, capture date, viewport and how to reproduce the image in `docs/demo/README.md`.
- Refresh screenshots and the published report together when displayed measurements change.
- Store selected public evidence in `docs/`; keep complete execution artifacts in ignored `artifacts/`.
- Do not publish a local screenshot as proof of a remote CI run. State which platforms and checks remain unverified.
- Hand off changed behavior, verification results and material limits. Never invent successful checks.
