# Benchmark integrity rules

- Intentional defects belong in `environment/`; correct replacements belong in `solution/files/`.
- Do not "clean up" a bug from an environment as part of a refactor.
- Keep instruction, verifier and reference behavior aligned. Explain any contract change and rerun both modes.
- Verifiers must check outcomes, include valid inputs and use isolated temporary data.
- Candidate exports must omit golden solutions and external verifier tests.
- A baseline needs at least one genuine test failure and no collection/setup error, skip or inconsistent report.
- Golden/candidate success requires all verifier cases to pass.
- Preserve atomic SQL operations and database uniqueness for cross-process idempotency; an in-memory lock is insufficient.
- Pin dependency versions and base-image digest. Keep network disabled during verification.
- Public test data is not private or hidden. Reference validation is not an AI-model score or an RL-training result.
- Keep execution safety limits visible. Do not describe this demo Docker setup as a hostile-code sandbox.
