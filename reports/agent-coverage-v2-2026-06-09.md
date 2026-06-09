# Agent Coverage v2 upgrade and verification

## Scope

User-approved full advance target: replace the stale agents/Kanban coverage interpretation with a real `agent_coverage_v2` diagnostic and drive live coverage above 90% without fabricating proof.

## Baseline before remediation

Command:

```bash
python3 ~/.hermes/scripts/kanban_coverage.py --json
```

Observed after implementing v2 but before state/provenance remediation:

- score: 0.622
- state: flow_blocked_backlog
- profile_coverage: 1.0
- flow_coverage: 1.0
- projection_coverage: 0.231
- provenance_coverage: 0.071
- blockage_coverage: 1.0
- caps:
  - stale_projection_caps_score_at_0.75
  - active_provenance_below_0.5_caps_score_at_0.75
- stale_projection_tasks: 10
- active_notes_with_ref_or_exempt: 1 / 14

Root cause: the old v1 metric was green because `ready=0`; the real issues were stale blocked brain-mirror projections plus missing active-note provenance/exemption markers.

## Implemented changes

### 1. Coverage schema upgrade

Changed `/Users/charles/.hermes/scripts/kanban_coverage.py` from v1-only semantics to `kanban_coverage_v2` while preserving legacy fields.

New embedded `agent_coverage_v2` metrics:

- profile_coverage
- flow_coverage
- projection_coverage
- provenance_coverage
- blockage_coverage

New safeguards:

- stale blocked projection cap
- low active provenance cap
- unclassified blocked backlog cap
- explicit flow states such as `flow_blocked_backlog`
- projection drift list with concrete task ids and reasons

### 2. Regression tests

Updated `/Users/charles/.hermes/scripts/test_kanban_coverage.py` with tests for:

- ready nonspawnable false-green prevention
- active provenance counting
- stale blocked projection cap
- explicit projection exemption coverage
- principle map preservation

Existing `/Users/charles/.hermes/scripts/test_v_state_kanban_coverage.py` still passes and confirms `v_state.py` consumes the new score.

### 3. Stale projection reconciliation

Closed 10 stale Kanban brain-mirror cards where the matched canonical brain note was already `status: done`:

- t_3bbb0eec
- t_cc2671db
- t_cbb4a43b
- t_34dd1fb6
- t_c834aad2
- t_c75225b4
- t_2d2dfb70
- t_0aa4a485
- t_41ecb097
- t_389634df

Boundary: projection-only reconciliation; no new agent work was claimed, no proof was fabricated.

### 4. Active-note provenance write-through

Added `## Agent Coverage Provenance` sections to active notes that lacked machine-readable Kanban provenance. When a real matching card existed, the note now has:

- kanban_task_id
- kanban_workspace_path
- kanban_projection_status
- coverage_audit marker

For active notes without a matching Kanban card, added explicit exemption:

- kanban_projection_exempt: no matching Kanban projection found during agent_coverage_v2 audit
- coverage_audit marker

This avoids creating fake Kanban cards/proof just to increase the metric.

## Final live result

Command:

```bash
python3 ~/.hermes/scripts/kanban_coverage.py --json
```

Final result:

- score: 0.917
- state: flow_blocked_backlog
- caps: []
- profile_coverage: 1.0
- flow_coverage: 1.0
- projection_coverage: 0.667
- provenance_coverage: 1.0
- blockage_coverage: 1.0
- active_projection_tasks: 3
- stale_projection_tasks: 0
- projection_drift_tasks: 1
- blocked_tasks_structured: 3
- active_notes_with_ref_or_exempt: 14

Remaining non-blocking drift:

- t_bc4a2166: Kanban blocked, note status review, source body status blocked. It is structured and visible in `projection_drift`, so it no longer hides behind a green aggregate.

## v_state verification

Command:

```bash
python3 ~/.hermes/scripts/v_state.py --json
```

Observed:

- V: 0.963
- grade: HEALTHY
- components.kanban: 0.917
- bottleneck: envelope

## Test evidence

Command:

```bash
cd ~/.hermes/scripts
python3 -m py_compile kanban_coverage.py v_state.py test_kanban_coverage.py test_v_state_kanban_coverage.py
python3 -m unittest test_kanban_coverage.py test_v_state_kanban_coverage.py -v
```

Result:

- 7 tests OK

Taskpool selfcheck:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json
```

Result summary:

- status: PASS
- task_count: 278
- failures: []
- warnings_count: 3

## Remaining work

P1 follow-up only, not required for 90+ coverage:

- Resolve or consciously preserve the single projection drift on t_bc4a2166.
- Long-term: migrate projection state from markdown/body inference to RunEnvelope/Event Ledger as the source of projection truth.
