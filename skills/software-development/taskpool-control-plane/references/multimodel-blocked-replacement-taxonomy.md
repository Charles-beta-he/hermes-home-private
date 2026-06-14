# Multimodel blocked tasks: replacement taxonomy and safe partial split

Use this when local-brain taskpool parents are blocked on multimodel non-convergence, but their historical `discussion_result.json` artifacts are missing or unavailable. The goal is to restore a governed path forward without pretending to reconstruct the lost model transcript and without bypassing parent certification.

## When this applies

- `blocked-resolve-step` keeps parents blocked with reasons such as:
  - `keep_blocked_missing_taxonomy_artifact`
  - `multimodel certification still not PASS`
  - `explicit_requires_multimodel`
- The parent frontmatter still has useful fields:
  - `multimodel_last_gate_status`
  - `multimodel_last_decision`
  - `multimodel_last_failures`
  - `multimodel_failure_taxonomy`
  - `multimodel_recommended_axes`
  - `blocked_resolve_taxonomy_axes`
  - `blocked_resolve_axis_rationale`
- The referenced historical discussion artifact is missing from `~/.hermes/tick-*/*discussion_result.json`.

## Safe recovery sequence

1. Build a fresh read-only baseline.
   - Run canonical `list`, `blocked-resolve-step --json`, `review-gap-scan --json`, worker jobs, and projection/coverage checks.
   - Keep Brain canonical task notes separate from Kanban/control-console projections.

2. Generate a replacement taxonomy artifact.
   - Do not claim to recover the lost discussion transcript.
   - Record the replacement source explicitly: current blocked resolver output + parent task frontmatter.
   - Save both machine and human-readable artifacts under `~/.hermes/evidence/taskpool/<topic>/`, e.g.:
     - `replacement-taxonomy.json`
     - `replacement-taxonomy.md`

3. Create only narrowed convergence child tasks for missing axes.
   - Typical axes: `quota_observability`, `fallback_threshold`, `relay_ordering`, `framing`, `patch_normalization`.
   - Each child must preserve the parent objective and declare non-goals:
     - no external side effects
     - no credential use
     - no production config mutation
     - no parent done transition from the child alone
   - Add `auto_subtask_parent`, `auto_subtask_kind: non_convergence_narrowing`, `auto_subtask_axis`, and a pointer to the replacement taxonomy artifact.

4. Let advisory-only multimodel rounds run, but interpret them correctly.
   - `PASS_ADVISORY_ONLY` + `CONTINUE_LOOP` means the evidence/framing direction is advisory-consumed.
   - It is not certification authority and must not close a parent.
   - If a child is document/evidence-only, it can only close through normal lifecycle gates when deterministic evidence is attached; otherwise leave it in `review` for human/closeout.

5. Reconcile parents after children move.
   - Run `reconcile --write` / `auto-subtask-sync --write`.
   - Parent should move from missing-artifact/non-convergence to one of:
     - `await_auto_subtasks` while child tasks remain open/review
     - ready for parent ratification when all child tasks are terminal and evidence is backfilled
     - still blocked if explicit multimodel certification or external side-effect gate remains

## Certification failure interpretation

- `PASS_ADVISORY_ONLY` is not a failed model result; it is a non-authoritative advisory result.
- Parent `missing_multimodel_certification` usually means one of:
  - explicit `requires_multimodel` / safety-sensitive task still needs certification
  - truth gate/readback proof is missing (`api_or_backend_readback_proof`, browser proof, build/test proof, etc.)
  - model panel still has unresolved noop-vs-change, best-within-constraints, vote_reject, or criteria_missing issues
- For compliance/security/external-browser tasks, leave the parent blocked or produce a Human Intervention Packet; do not auto-done from advisory-only children.

## Verification

After the split/repair tranche, verify:

- `brain_task_orchestrator.py selfcheck --json` -> PASS
- `brain_task_orchestrator.py proof-check --json` -> PASS or failures classified
- `brain_task_orchestrator.py blocked-resolve-step --json` shows improved reasons, e.g. `await_auto_subtasks` instead of missing artifact
- `brain_task_orchestrator.py review-gap-scan --json` shows remaining real gaps only
- worker jobs have no stale false-alive processes
- control-console projection remains trustworthy and Human Inbox contains only real gates

## Pitfalls

- Do not convert missing historical artifacts into invented discussion content.
- Do not treat child advisory pass as parent certification.
- Do not force `blocked -> done`; normal closure is review-gated and evidence-gated.
- Do not hide remaining parent gates: `await_auto_subtasks` is progress, not completion.
- If event hooks spawn advisory rounds for new children, wait for them to settle and then reconcile before reporting final parent state.
