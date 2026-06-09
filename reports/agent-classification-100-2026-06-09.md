# Agent architecture classification 100% audit

## Scope

User asked to advance Hermes self-architecture agent classification to 100%.

This is distinct from agent_coverage_v2 coverage:

- Coverage checks profile/flow/projection/provenance/blockage.
- Classification checks active brain task metadata such as lane/layer/project/architecture_target/completion_gate and iceberg fields.

## Baseline findings

Active brain tasks: 14

Initial gaps:

- 2 active notes lacked canonical architecture fields.
- 14 / 14 active notes lacked iceberg_tier / iceberg_scope / iceberg_confidence.
- One projection drift existed: t_8f9a57e5 was Kanban blocked while the canonical brain note still said running.

## Remediation

### t_8f9a57e5 projection alignment

Evidence read from Kanban:

- Task: t_8f9a57e5
- Kanban status: blocked
- Latest run: task_run 20521 blocked
- Summary: `review-required: shipped a read-only external-skill intake audit slice with 5 passing tests; node false-positive hardening and URL-source narrowing are in, but code changes need review before counting done`

Action:

- Changed brain note status from running to review.
- Cleared stale claim fields.
- Added lifecycle projection alignment audit line.
- Did not mark done and did not fabricate proof.

### Active task metadata completion

For all 14 active task notes, ensured these fields are present:

- lane
- layer
- project
- architecture_target
- completion_gate
- iceberg_tier
- iceberg_scope
- iceberg_confidence

Two previously underclassified tasks were completed:

- `2026-05-21-170157-rokid-后台分析图片.md`
  - lane: work
  - layer: L2
  - project: hermes-agent
  - architecture_target: visual-ingest-runtime
  - completion_gate: project-evidence-review-done
  - permission_tier: budget-handoff

- `2026-05-18-分析-sakana-ai-多模型指挥官理念并提炼-hermes-conductor-融入方案.md`
  - layer: L3
  - completion_gate: ratification-or-selfcheck-review-done
  - permission_tier: budget-handoff

For Hermes self-architecture active tasks, `iceberg_tier: L` means system/control-plane/runtime semantics, not product UI/backend layering.

## Final classification distribution

Active brain tasks: 14

Missing canonical classification fields: 0

By status:

- blocked: 7
- ready: 2
- review: 5

By lane:

- evolution: 11
- work: 3

By layer:

- L3: 13
- L2: 1

By project:

- hermes-agent: 7
- hermes: 7

By architecture target:

- local-brain: 5
- taskpool: 5
- skill-graph: 2
- visual-ingest-runtime: 1
- Hermes-native multi-model conductor: 1

By iceberg tier:

- L: 14

By iceberg scope:

- control_plane_local_brain: 5
- control_plane_taskpool: 5
- skill_graph_governance: 2
- visual_ingest_runtime: 1
- multimodel_conductor_architecture: 1

By iceberg confidence:

- high: 14

## Final coverage verification

Command:

```bash
python3 ~/.hermes/scripts/kanban_coverage.py --json
```

Result:

- score: 1.0
- profile_coverage: 1.0
- flow_coverage: 1.0
- projection_coverage: 1.0
- provenance_coverage: 1.0
- blockage_coverage: 1.0
- caps: []
- projection_drift: []
- stale_projection_tasks: 0
- projection_drift_tasks: 0
- blocked_tasks_structured: 4

## v_state and selfcheck

`python3 ~/.hermes/scripts/v_state.py --json`:

- V: 0.963
- grade: HEALTHY
- kanban: 1.0
- bottleneck: envelope

`python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json`:

- status: PASS
- failures: []
- warnings_count: 3

Regression tests:

```bash
cd ~/.hermes/scripts
python3 -m unittest test_kanban_coverage.py test_v_state_kanban_coverage.py -v
```

- 8 tests OK

## Remaining note

The active set is fully classified. Historical inactive/done notes still may not carry iceberg fields; they were intentionally not bulk-mutated because the user request was agent/self-architecture active classification rather than retroactive archival normalization.
