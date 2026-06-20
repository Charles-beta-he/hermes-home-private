#!/usr/bin/env bash
set -euo pipefail

WATCHER="${HERMES_CONTEXTCARD_SESSION_WATCHER:-$HOME/.hermes/scripts/hermes_contextcard_session_end_watcher.py}"
STATE_DB="${HERMES_STATE_DB:-$HOME/.hermes/state.db}"
STATE_FILE="${HERMES_CONTEXTCARD_SESSION_WATCHER_STATE:-$HOME/.hermes/state/contextcard-session-watcher.json}"
LOCK_FILE="${HERMES_CONTEXTCARD_SESSION_WATCHER_LOCK:-$HOME/.hermes/locks/contextcard-session-watcher.lock}"
REFRESH_COMMAND="${HERMES_CONTEXTCARD_SESSION_REFRESH_COMMAND:-$HOME/.hermes/scripts/hermes_contextcard_rich_production_refresh.sh}"
IDLE_SECONDS="${HERMES_CONTEXTCARD_SESSION_IDLE_SECONDS:-180}"
LOOKBACK_SECONDS="${HERMES_CONTEXTCARD_SESSION_LOOKBACK_SECONDS:-86400}"
MIN_INTERVAL="${HERMES_CONTEXTCARD_SESSION_MIN_REFRESH_INTERVAL_SECONDS:-600}"
# Cron no_agent scripts are killed after ~120s. Keep the nested refresh
# timeout below that so the watcher can emit structured JSON instead of being
# killed by the scheduler.
REFRESH_TIMEOUT_SECONDS="${HERMES_CONTEXTCARD_SESSION_REFRESH_TIMEOUT_SECONDS:-105}"
ALLOWED_SOURCES="${HERMES_CONTEXTCARD_ALLOWED_SOURCES:-cli,telegram}"
LOG_FILE="${HERMES_CONTEXTCARD_SESSION_WATCHER_LOG:-$HOME/.hermes/logs/contextcard-session-watcher.log}"

mkdir -p "$(dirname "$LOG_FILE")"
set +e
OUTPUT="$(python3 "$WATCHER" \
  --state-db "$STATE_DB" \
  --state-file "$STATE_FILE" \
  --lock-file "$LOCK_FILE" \
  --refresh-command "$REFRESH_COMMAND" \
  --idle-seconds "$IDLE_SECONDS" \
  --lookback-seconds "$LOOKBACK_SECONDS" \
  --min-refresh-interval-seconds "$MIN_INTERVAL" \
  --refresh-timeout-seconds "$REFRESH_TIMEOUT_SECONDS" \
  --allowed-sources "$ALLOWED_SOURCES" \
  --json)"
WATCHER_EXIT=$?
set -e

printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$OUTPUT" >> "$LOG_FILE"
STATUS="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("status","unknown"))' <<< "$OUTPUT")"
case "$STATUS" in
  error)
    printf '%s\n' "$OUTPUT"
    exit "$WATCHER_EXIT"
    ;;
  refresh_failed)
    # Session-end refresh is opportunistic; production and deterministic fallback
    # refresh jobs remain the authoritative ContextCard writers. Keep this cron
    # healthy while preserving the failure details in the watcher log.
    ;;
esac
exit 0
