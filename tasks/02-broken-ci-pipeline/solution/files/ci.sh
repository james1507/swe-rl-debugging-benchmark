#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
python -m pytest -q tests
python -m compileall -q src
python -m tooling.build_manifest
