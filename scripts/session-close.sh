#!/bin/bash
# Session Close — 对话结束时执行的全套收尾
set -e
echo "═══════════════════════════════════════════════════"
echo "  Session Close — 自动化收尾"
echo "═══════════════════════════════════════════════════"
TASK_TYPE="${1:-general}"
ROUNDS="${2:-1}"
CORRECTIONS="${3:-0}"
echo "[1/6] Recording session..."
python3 /Users/charles/.hermes/scripts/session-end-recorder.py "$TASK_TYPE" "$ROUNDS" "$CORRECTIONS"
echo "[2/6] Triggering PA evolution..."
python3 /Users/charles/.hermes/scripts/pa-evolution-trigger.py
echo "[3/6] Generating daily report..."
python3 /Users/charles/.hermes/scripts/pa-daily-report.py
echo "[4/6] Ingesting governed daily-report task candidates..."
python3 /Users/charles/.hermes/scripts/daily_report_task_ingest.py --write
echo "[5/6] Syncing to Obsidian..."
python3 /Users/charles/.hermes/scripts/sync-to-obsidian.py --push
echo "[6/6] Done"
echo ""
echo "Session close complete"
echo "═══════════════════════════════════════════════════"
