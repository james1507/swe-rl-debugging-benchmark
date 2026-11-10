# Architecture rules

- `runner/run_task.py` owns argument parsing, CLI orchestration and final report publication.
- `runner/workspace.py` owns task registration, workspace copying and content fingerprints.
- `runner/execution.py` owns subprocesses, Docker/local execution, timeouts and cleanup.
- `runner/verification.py` owns pytest/JUnit verdict interpretation. It must not spawn processes or mutate workspaces.
- Imports flow from CLI to execution, then workspace/verification. Lower modules never import the CLI. Tests import the module that owns the function.
- `tasks/` contains self-contained fixtures, contracts, verifier tests and reference overlays; application fixtures never import `runner`.
- `docs/demo/report.mjs` owns report validation and derived metrics without DOM access.
- `docs/demo/app.mjs` owns browser input, rendering and file loading. `index.html` and `styles.css` own semantics and presentation.
- The demo reads report files; it never executes candidate code or implies that a recorded result is a live evaluation.
- Keep `rules/` canonical. AI-tool adapters only point to shared guidance.
- Use plain functions and modules. Do not add repositories, factories, services or interfaces with one implementation.
- Update architecture documentation and caller imports whenever ownership changes. Preserve CLI flags and report fields unless a deliberate migration is required.
