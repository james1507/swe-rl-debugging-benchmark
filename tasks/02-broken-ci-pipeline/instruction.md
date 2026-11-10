# Task 02 — Repair the CI pipeline

## Situation

`src/calc.py` is a valid Python module, with public unit tests in `tests/`. `ci.sh` references nonexistent directories. `.github/workflows/ci.yml` invokes nonexistent `build.sh` and does not install pytest.

## Required behavior

1. `bash ci.sh` must run the public unit tests and compile Python source under `src/`.
2. A failing unit test must produce a nonzero exit and stop the build before creating a new manifest.
3. A successful build creates `dist/build_manifest.json` with exactly these keys:

   ```json
   {
     "source": "src/calc.py",
     "sha256": "<64 lowercase hexadecimal characters>"
   }
   ```

4. `sha256` must equal SHA-256 of the actual bytes in `src/calc.py`. No hardcoded digest.
5. Repeated builds of unchanged source must produce byte-identical manifests. Do not include timestamps, absolute paths, random IDs or environment-specific metadata.
6. The GitHub workflow must set up Python 3.12, install pytest and execute `bash ci.sh` from the repository root.
7. Keep `src/calc.py` behavior unchanged: `add(a, b)` returns `a + b`, including negative, zero and large integer inputs.

## Scope

May edit `ci.sh`, `.github/workflows/ci.yml`, and add small build helpers. Keep public unit tests meaningful; do not delete, disable or bypass them. No package publication, deployment or external service is required. Installed Python standard library is sufficient for manifest generation.

Docker build/dependency files are evaluator-owned. Evaluation runs with network disabled, so `ci.sh` must not install dependencies at runtime. Workflow dependency installation runs in its own GitHub setup step.

## Evaluation

Verifier inspects workflow commands, executes the pipeline, checks manifest against source bytes, repeats the build under a different `PYTHONHASHSEED`, injects a failing public test into a temporary copy, and checks calculator behavior. Every verifier case must pass.
