# Evidence supplement and review-closeout recovery

Use this when a taskpool recovery session has already unblocked/requeued tasks, but `review` items or repair children still cannot close because their evidence is either missing, low-signal, or machine-unreadable.

## Failure signatures

- `auto-close-review --json` skips review tasks with:
  - `ratification-or-selfcheck-review-done requires ratification artifact or deterministic selfcheck/proof evidence`
  - `project-evidence-review-done requires test/build/browser/curl/commit/project-verification evidence`
  - `advisory_only_multimodel_requires_implementation_evidence: PASS_ADVISORY_ONLY cannot authorize done without commit/test/build/browser/real-api evidence`
- Dispatch tick reports `proof_check FAIL` even after evidence was added, often because a human-readable line such as `repair: ...` was added under YAML `evidence:` without a structured prefix.
- A repair child moved `running -> blocked` after collecting partial evidence; parent review remains blocked by a closeout gap.

## Safe recovery sequence

1. Re-read current state.
   - `brain_task_orchestrator.py list --json`
   - `review-gap-scan --max-tasks 50 --json`
   - `blocked-resolve-step --max-tasks 50 --json`
   - `agent_team_controller.py status --json`

2. Produce fresh deterministic evidence before editing notes.
   - `python3 ~/.hermes/scripts/test_brain_task_orchestrator.py`
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json`
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py proof-check --json`
   - `bash ~/.hermes/scripts/p10-health.sh --json`

3. Attach evidence to the repair child and parent review task using structured prefixes only.
   - Good prefixes: `command:`, `artifact:`, `file:`, `proof:`.
   - Good examples:
     - `command:python3 ~/.hermes/scripts/test_brain_task_orchestrator.py PASS`
     - `command:python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json PASS failures=0`
     - `command:bash ~/.hermes/scripts/p10-health.sh --json PASS grade=A V=...`
     - `artifact:/tmp/tp_self_evidence.json`
     - `proof:deterministic-gate-refresh 2026-... selfcheck=PASS proof-check=PASS parent_left_in_review`
   - Bad examples inside YAML `evidence:`:
     - `repair: evidence collected ...`
     - bare prose without a recognized prefix.

4. Re-run `proof-check --json` immediately after any evidence edit.
   - If it fails with `unstructured evidence in <task>: <entry>`, convert that entry to a recognized structured prefix instead of weakening the checker.

5. Let normal closeout gates run.
   - `auto-close-review --max-tasks 50 --json`
   - Do not directly mark parents `done`; attach evidence and let `auto-close-review` consume it.

6. If a repair child is `blocked` only because an earlier worker emitted `command:agent_team_controller consume-claimed worker blocked`, but you have now attached fresh deterministic evidence, move that child back to `review` with explicit evidence and `--force`, then run `auto-close-review`.
   - This is a lifecycle alignment step, not a bypass: the child still closes through `auto-close-review`.
   - Include the same `command:` evidence used in the note.

7. Reconcile parents after child closeout.
   - `reconcile --write --json`
   - A parent may reopen from `blocked` to `pending` when child evidence is now ready.
   - Then run a real dispatch tick only if `proof-check` is PASS.

## Dispatch guardrail

If dispatch tick returns `status=ERROR` but `parallel_dispatch.selected_count > 0`, inspect `errors[].step`. If the hard error is `proof_check` caused by newly introduced unstructured evidence, fix the evidence prefix first; do not dispatch around proof-check.

## Verification bundle

Before reporting completion:

- `proof-check --json` => PASS, failures=0
- `selfcheck --json` => PASS, failures=0
- `review-gap-scan --max-tasks 50 --json` => gap_count=0 when all review gaps are repaired
- `blocked-resolve-step --max-tasks 50 --json` => remaining kept_blocked entries are true gate blockers
- `agent_team_controller.py status --json` => `human_escape_triggered=false`
- `next --json` / dispatch tick explains any no-dispatch state as either active running work, retry window, or true blocked gate.

## Pitfalls

- PASS_ADVISORY_ONLY is not implementation proof. It can support review context, but closing work/product tasks still needs test/build/browser/curl/commit/project-verification evidence.
- Generic control-plane proof (`selfcheck`, `proof-check`, `p10-health`, `py_compile`) can close review-gap repair children or evolution ratification gaps when the gate asks for deterministic proof, but it does not prove product feature delivery by itself.
- Avoid adding session prose to YAML `evidence:`. Put narrative in `## Proof Log`; keep frontmatter evidence machine-readable.
- If a task becomes `pending` and `dispatchable=True`, but dispatch tick refuses with proof-check failure, the pool is not stuck; the proof ledger is correctly blocking unsafe dispatch until evidence is structured.
