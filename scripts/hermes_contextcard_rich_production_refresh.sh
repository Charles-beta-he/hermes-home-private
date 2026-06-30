#!/usr/bin/env bash
set -euo pipefail

STATE_DB="${HERMES_STATE_DB:-$HOME/.hermes/state.db}"
STAGING_DB="${HERMES_CONTEXTCARD_RICH_CACHE_DB:-$HOME/.hermes/contextcards.rich.staging.db}"
INCREMENTAL_DB="${HERMES_CONTEXTCARD_RICH_INCREMENTAL_DB:-$HOME/.hermes/contextcards.rich.staging.incremental.db}"
PRODUCTION_DB="${HERMES_CONTEXTCARD_CACHE_DB:-$HOME/.hermes/contextcards.db}"
BACKUP_DIR="${HERMES_CONTEXTCARD_BACKUP_DIR:-$HOME/.hermes/backups/contextcards}"
# Cron no_agent scripts are killed after ~120s; keep the rich production
# refresh bounded and incremental by default. Operators can still override
# HERMES_CONTEXTCARD_RICH_LIMIT_SESSIONS for manual backfills.
LIMIT_SESSIONS="${HERMES_CONTEXTCARD_RICH_LIMIT_SESSIONS:-3}"
ALLOWED_SOURCES="${HERMES_CONTEXTCARD_ALLOWED_SOURCES:-cli,telegram}"
MIN_SAMPLE_SIZE="${HERMES_CONTEXTCARD_PROMOTE_MIN_SAMPLE_SIZE:-20}"
MIN_SCORE="${HERMES_CONTEXTCARD_RICH_MIN_SCORE:-80}"
RICH_WRITER="${HERMES_CONTEXTCARD_RICH_WRITER:-$HOME/.hermes/scripts/hermes_contextcard_rich_writer.py}"
LLM_COMMAND="${HERMES_CONTEXTCARD_LLM_COMMAND:-python3 $HOME/.hermes/scripts/hermes_contextcard_llm_command.py}"
QUALITY_REPAIR="${HERMES_CONTEXTCARD_RICH_QUALITY_REPAIR:-$HOME/.hermes/scripts/hermes_contextcard_rich_quality_repair.py}"
PROMOTE="${HERMES_CONTEXTCARD_PROMOTE:-$HOME/.hermes/scripts/hermes_contextcard_rich_promote.py}"
MERGE_STAGING="${HERMES_CONTEXTCARD_RICH_MERGE_STAGING:-$HOME/.hermes/scripts/hermes_contextcard_rich_merge_staging.py}"
LOG_FILE="${HERMES_CONTEXTCARD_RICH_PRODUCTION_LOG:-$HOME/.hermes/logs/contextcard-rich-production-refresh.log}"

mkdir -p "$(dirname "$LOG_FILE")"

set +e
REFRESH_OUTPUT="$(python3 "$RICH_WRITER" \
  --state-db "$STATE_DB" \
  --cache-db "$INCREMENTAL_DB" \
  --limit-sessions "$LIMIT_SESSIONS" \
  --allowed-sources "$ALLOWED_SOURCES" \
  --llm-command "$LLM_COMMAND" \
  --write-cache)"
REFRESH_RC=$?
set -e
if [[ "$REFRESH_RC" -ne 0 ]]; then
  # No new valid sessions is a steady-state no-op, not a production refresh failure.
  # Keep the existing incremental/staging cache and let merge/quality/promote gates
  # read back the current production DB. Other writer failures still fail closed.
  if python3 -c 'import json,sys; p=json.load(sys.stdin); sys.exit(0 if p.get("status")=="error" and "no valid richer ContextCard candidates" in str(p.get("error","")) else 1)' <<< "$REFRESH_OUTPUT"; then
    REFRESH_OUTPUT='{"status":"ok","mode":"noop","reason":"no_valid_richer_contextcard_candidates"}'
  else
    printf '%s\n' "$REFRESH_OUTPUT"
    exit "$REFRESH_RC"
  fi
fi

MERGE_OUTPUT="$(python3 "$MERGE_STAGING" \
  --production-db "$PRODUCTION_DB" \
  --incremental-db "$INCREMENTAL_DB" \
  --output-db "$STAGING_DB")"

REPAIR_OUTPUT="$(python3 "$QUALITY_REPAIR" --staging-db "$STAGING_DB" --min-score "$MIN_SCORE" --write)"

PROMOTE_OUTPUT="$(python3 "$PROMOTE" \
  --staging-db "$STAGING_DB" \
  --production-db "$PRODUCTION_DB" \
  --backup-dir "$BACKUP_DIR" \
  --min-sample-size "$MIN_SAMPLE_SIZE" \
  --min-quality-score "$MIN_SCORE" \
  --promote)"

printf '%s {"refresh":%s,"merge":%s,"repair":%s,"promote":%s}\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  "$REFRESH_OUTPUT" "$MERGE_OUTPUT" "$REPAIR_OUTPUT" "$PROMOTE_OUTPUT" >> "$LOG_FILE"

STATUS="$(python3 -c 'import json,sys; p=json.load(sys.stdin); print(p.get("status","unknown"));' <<< "$PROMOTE_OUTPUT")"
if [[ "$STATUS" != "ok" ]]; then
  printf '%s\n' "$PROMOTE_OUTPUT"
fi

exit 0
