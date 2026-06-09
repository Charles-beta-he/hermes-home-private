# Certification unblock and selfcheck upgrade patterns

Use when a blocked task already has substantial evidence but taskpool gates still refuse to advance it.

## Safe multimodel certification unblock

Do not solve a failed certification by lowering the certification threshold for that same task. Treat minority patches that relax ratification/certification gates as governance-changing advisory work when:

- the patch op is threshold/gate/policy related (`tune_threshold`, `relax_gate`, `change_gate`, `update_policy`),
- the target is certification/ratification/control-plane code, and
- the rationale is to let the current failed certification pass with fewer models or weaker quorum.

The correct control-plane fix is to classify that patch as deferred/advisory, remove the false `mixed-noop-vs-change` blocker, and rerun ratification under the existing gate.

## Artifact binding requirements

When rerunning or synthesizing `discussion_result.json` for a specific task, ensure the artifact has explicit target binding fields before using `ratification-gate`:

- `target_task_id`
- `target_task_path`
- optionally matching values under `context.target_task_id` and `context.target_task_path`

Without these, `ratification-gate --task ...` can fail with `target_task_binding_missing` even if the discussion status is certified.

## Evidence-shape compatibility

Lifecycle transitions require structured evidence (`command:`, `file:`, `search:`, `brainctl:`, `artifact:`, `url:`, `proof:` or absolute paths). Historical audit notes like `child-task:` or `child-axis:` should not be passed directly to lifecycle gates.

For resolver/auto-close helpers, filter legacy evidence to structured entries and add an explicit ratification artifact evidence item such as:

`artifact:ratification multimodel certified /path/to/discussion_result.json`

For existing task notes, convert legacy audit evidence to `proof:<legacy-text>` rather than weakening the lifecycle gate.

## Mission envelope selfcheck

If a task has mission-envelope markers, selfcheck requires the full envelope:

- `mission_schema_version`, `mission_id`, `mission_title`, `mission_objective`
- `mission_constraints`, `red_lines`, `non_goals`
- `evidence_refs`, `acceptance_criteria`, `dag_nodes`, `checkpoint_states`
- `permission_gates`, `handoff_artifacts`, `proof_artifacts`
- `rollback_signal`, `certification_status`, `ratification_artifact`

Structured reference fields need evidence prefixes. `ratification_artifact` should be `artifact:/path/to/discussion_result.json` for mission-envelope validation; other runtime artifact fields may still need the raw local path depending on the helper.

## Project profile selfcheck warnings

`profile_control_plane_missing` warnings are usually fixed in `~/.hermes/project-profiles/<project>.json`, not in task files. Add project-specific policy objects:

- `lark_task_execution_policy`
- `lark_evidence_policy.closeout_required_labels`
- `backend_contract_policy`
- `regression_coverage_policy`

Then rerun `brain_task_orchestrator.py selfcheck --json`, `proof-check --json`, and `lifecycle --json`.
