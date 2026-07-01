# Kanban mirror coverage recovery

Use when `python3 ~/.hermes/diagnostics/runner.py --json` reports low `kanban-sync-coverage`, especially when `python3 ~/.hermes/scripts/kanban_coverage.py --json` shows low `projection_coverage`, low `provenance_coverage`, stale projections, or projection drift.

Principle: local-brain task notes / `brain_task_orchestrator.py list --json` are the source of truth; Kanban `brain-mirror` cards are a projection. Repair projection drift, but do not use projection repair to bypass taskpool proof, review, ratification, or human gates.

Safe recovery sequence:

1. Read the exact coverage shape:
   - `python3 ~/.hermes/scripts/kanban_coverage.py --json`
   - Inspect `agent_coverage_v2.metrics`, `projection_drift`, `stale_projection_ids`, and `caps`.
2. Back up runtime state before mutation:
   - `mkdir -p ~/.hermes/backups/kanban-bridge`
   - `cp ~/.hermes/kanban.db ~/.hermes/backups/kanban-bridge/kanban.db.$TS.bak`
   - `cp ~/.hermes/state/kanban_bridge_state.json ~/.hermes/backups/kanban-bridge/kanban_bridge_state.$TS.json.bak`
3. Reconcile only `brain-mirror` projection rows to source status/body. Do not delete tasks. Do not force-close blocked cards.
4. Add source provenance to active note files when missing, e.g. a `## Kanban Projection` section with the mirror id and workspace path.
5. Verify:
   - `python3 ~/.hermes/scripts/kanban_bridge_silent.py`
   - `python3 ~/.hermes/scripts/kanban_coverage.py --json`
   - `python3 ~/.hermes/diagnostics/runner.py --json`
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json`
6. If projection/provenance are repaired but `blockage_coverage` remains low, stop projection repair and run a blocked-card structured-unblock audit instead. Remaining blocked cards are governance/review state, not mirror drift.

Bridge implementation pitfalls:

- The bridge dedupe key must be stable across status changes. Prefer the local-brain task id; do not include status in the hash.
- A mirror bridge that only creates cards will accumulate stale `blocked`/`review` cards. It must also reconcile existing `brain-mirror` rows.
- Record audit events such as `brain_mirror_sync` / projection reconciliation in `task_events` when mutating runtime state.
- Treat `review-required` blocks as review gates, not automatic completion candidates.

Session evidence pattern observed:

- Before repair: score around `0.588`, `projection_coverage=0.146`, `provenance_coverage=0.036`, dozens of stale blocked projections.
- After projection reconciliation + provenance writeback: diagnostics reached 100/100, `projection_coverage=1.0`, `provenance_coverage=1.0`, stale projection count 0.
- Later drift can reappear if new workers create/alter blocked cards; rerun coverage before claiming current health.
