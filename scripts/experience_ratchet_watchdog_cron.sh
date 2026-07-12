#!/usr/bin/env bash
set -euo pipefail
python3 "$HOME/.hermes/scripts/experience_ratchet_watchdog.py" --quiet-success --require-cron
