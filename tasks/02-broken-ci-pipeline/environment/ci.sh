#!/usr/bin/env bash
set -euo pipefail
python -m pytest test  # BUG: directory is named tests
python -m compileall -q source  # BUG: directory is named src
