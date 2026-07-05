#!/usr/bin/env bash
set -euo pipefail
python3 "$HOME/.hermes/scripts/dynamic_selfcheck_coverage.py" run --quiet-success
