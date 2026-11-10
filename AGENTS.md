# Working on SWE RL Debugging Benchmark

This file is the entry point for human maintainers and AI coding tools. Read it before editing this repository. All source comments, UI copy, rules and documentation must be in English.

## Read first

1. [Project overview](README.md): purpose, commands and expected results.
2. [Rule index](rules/README.md): mandatory project-wide working rules.
3. [Architecture](docs/architecture.md): module ownership and execution boundaries.
4. The task's `instruction.md` before touching its verifier or reference solution.

## Non-negotiable invariants

- `tasks/*/environment/` contains intentional bugs. Never fix them while maintaining the benchmark; repair a separate candidate workspace or `solution/files/` instead.
- A baseline is valid only when real verifier tests fail. Build errors, collection errors, timeouts and skipped tests never count as success.
- Reference solutions and successful candidates must pass every verifier case.
- Never export reference solutions, external verifier tests or maintainer rules to a task-solving agent.
- Preserve the existing CLI (`python3 -m runner.run_task`) and report schema unless a requested change explicitly requires otherwise.
- Prefer standard-library functions and browser features. Add dependencies or architecture layers only when current requirements need them.
- Report actual measurements. Screenshots must come from the running demo and identify their source report.

## Required checks

```bash
python3 -m unittest discover -s tests -v
node tests/test_demo.mjs
```

For runner, task, dependency or Docker changes, also run:

```bash
python3 -m runner.run_task --task all --mode both --engine docker
```

For demo changes, serve the project, test report loading and task selection in a browser, and check narrow and wide layouts. Refresh screenshots if visible behavior changes; see [demo guide](docs/demo/README.md).

## Completion

Summarize changed behavior, checks actually run and remaining limits. Do not claim GitHub CI, deployment, model performance or security certification without evidence. Do not commit generated `artifacts/`, candidates, secrets or local environments.

Tools that do not discover `AGENTS.md` automatically must be given this file explicitly. Tool-specific entry points link here; detailed rules have one canonical home in `rules/`.
