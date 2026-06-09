# Taskpool bounded advancement pass

Use this when the user says "全盘推进" / "push the whole pool forward" and the pool is healthy but automatic execution is fail-closed.

## Canonical pass

1. Read health and next-task state:
   - `brain_task_orchestrator.py next --json`
   - `brain_task_orchestrator.py dispatch-dry-run --json`
   - `brain_task_orchestrator.py selfcheck --json`
   - optionally `brain_task_orchestrator.py list --include-done --json` for broad audit only
2. Attempt bounded automation:
   - `brain_task_orchestrator.py autorun-runner --actor hermes --ttl-minutes 60 --json`
   - `brain_task_orchestrator.py auto-claim-and-handoff --actor hermes --ttl-minutes 60 --json`
   - `multimodel_intervention_dynamic_step.py --json`
3. If runner/handoff both return `eligible=false` because of `allowlist_miss` or another fail-closed non-execution gate, do not stop at reporting. Claim the highest-value dispatchable task and land exactly one bounded slice.
4. Write proof back to the canonical task note, then release to the correct non-terminal state.
5. Re-measure with `next --json`, `selfcheck --json`, and a small status snapshot.

## JSON parsing / sizing pattern

- Prefer `list --json` for active-pool counts and target-task verification.
- Reserve `list --include-done --json` for broader audits because the all-history payload can contain control characters or become noisy for strict parsers.
- When parsing orchestrator JSON in Python, use `json.loads(text, strict=False)`.
- If an all-history parse is noisy, fall back to:
  - `list --json` for active counts
  - direct `read_file` on the target task note
  - `next --json` / `selfcheck --json` for verification

## External-repo advisory slice ladder

Prefer slices that narrow uncertainty instead of trying to close the task:

1. repo surface / star / topic / pushed-at evidence
2. README vs README_OpenSource / marketing-vs-open-source boundary
3. repo-family boundary (main repo vs support repos)
4. support-repo README/package/tree evidence
5. reusable-pattern mapping: what is low-level engineering value vs true Hermes-relevant control-plane value
6. only after the above, queue/consume the required multimodel advisory pass

## Interpretation rules

- `worker_already_running` from multimodel intervention is compatible background progress, not a blocker to landing a manual bounded slice.
- `PASS_ADVISORY_ONLY` is progress, not closeout authority.
- If blocked count does not move but the target task gained new evidence and a narrower decision gate, that still counts as real advancement.
- For external-repo tasks, explicitly separate real implementation surface from docs/README capability claims in `Proof Log` and `Blockers / Confusions`.
