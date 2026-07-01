# Implementation Guidance for Dispatch Tick Fixes

Extracted from `/Users/charles/.hermes/skills/software-development/taskpool-control-plane/SKILL.md` on 2026-07-01T08:24:04.829872+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Implementation guidance for dispatch tick fixes

When `max_agents` is hardcoded (e.g. `max_agents=3`) in `brain_task_orchestrator.py` instead of using the dynamic N module, load `references/dynamic-n-integration.md`: it covers the integration pattern for replacing hardcoded defaults with `get_smoothed_n(dispatchable, groups)` calls, the state-pitfall when testing, and the per-call-site computation pattern.

When many tasks share a coarse `parallel_boundary` (e.g. all uvisa-app tasks grouped as one) and dynamic N is capped low despite many dispatchable tasks, load `references/tree-shaped-boundary-refinement.md`: it covers the read-time refinement pattern that extracts page/feature keys from task titles without changing frontmatter, the dual-path implementation (Task objects in orchestrator vs dicts in classifier), and the zero-migration rollback guarantee.

When integrating a new task classification dimension (iceberg tier, capability level, etc.) into the dispatch pipeline, use `references/iceberg-tier-dispatch-integration.md`: the 4 integration points are score weighting, preflight gate, work contract atoms, and dashboard visualization.

When adding or modifying brain-overlay-aware dispatch/runtime behavior, make the contract visible at every consumer boundary, not only in registry files:
- task rows should expose `brain`, `brain_profile`, and a machine-readable `brain_contract`.
- `dispatch-dry-run` execution prompts should include the resolved brain overlay contract.
- `auto-claim-and-handoff` and `parallel-claim-and-handoff` artifacts should include a `## Brain Overlay Contract` section with red lines, required taskpool fields, worker required context/output, stop conditions, and done definition.
- Cover this with a RED/GREEN test that asserts row output, dispatch prompt, and handoff artifact content, using fixture `HERMES_BRAINS_DIR` / `HERMES_BRAIN_REGISTRY` and an isolated project-profile fallback.
- Keep rollout warn-only unless a separate ratified gate explicitly promotes it to fail-closed.

When patching dispatch logic:
- Separate `warnings` from `errors`.
- Keep fail-closed behavior for true safety blockers only.
- Allow bounded `autorun_step` / claim-and-handoff to proceed when only soft governance warnings are present.
- Return a visible non-OK status such as `WARN` when governance is unhealthy, but do not convert that into an execution stop by default.
- Preserve observability: emit warning/error counts and retain the specific failing governance step in the payload/log.
- For resident selfcheck integration, taskpool event hooks should emit a compact selfcheck event after the local hook outcome is known (`OK`/`ERROR`/`TIMEOUT`) with the task id and log artifact as evidence; this observer must be fail-soft and must not make the originating task mutation fail.
- Do not append full task bodies/evidence-spine payloads to hot tick JSONL logs. If `~/.hermes/logs/brain_task_dispatch_tick.jsonl` grows to many GB, `quality_capacity_probe` / recent-event readers can OOM even when list/dashboard are healthy. Use bounded tail reads and compact JSONL projections; preserve full historical logs outside the hot path (for example `~/taskpool-bloat-quarantine/...`) rather than deleting evidence.
