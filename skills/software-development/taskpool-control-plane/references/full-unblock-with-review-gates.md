# Full unblock with review/execution-flow gates

Scope: governed local taskpool/control-plane operations where the user asks to continue until there are no active `blocked` tasks. Applicability: mixed queues containing `blocked`, `review`, `pending`, parent/child convergence items, asynchronous worker jobs, and execution-flow gates. Anti-condition: do not use this pattern to bypass destructive actions, external writes, credentials, production changes, payment/budget expansion, or safety/legal/compliance decisions.

## Objective boundary

“No blocked tasks” means active canonical task notes should have `status: blocked` count reduced to zero. It does **not** mean every task must be forced to `done`.

Acceptable terminal/non-blocking states after the unblock pass:
- `done` when lifecycle/proof gates pass with deterministic evidence.
- `review` when the item still needs explicit closeout/readback/acceptance evidence but is not a blocker.
- `pending` when the parent is reopened for ratification or dispatch.
- `archived` when the work is terminal enough to leave the active pool, but cannot be truthfully marked done because certification remains advisory-only or the remaining authority/evidence gate is not safely satisfiable.

Never convert `PASS_ADVISORY_ONLY` / `CONTINUE_LOOP` into fake `done` just to make the queue green.

## Safe sequence

1. Build a read-only baseline:
   - `brain_task_orchestrator.py list --json`
   - `blocked-resolve-step --max-tasks ... --json`
   - `review-gap-scan --max-tasks ... --json`
   - `agent_team_controller.py worker-jobs --json`
   - `multimodel-intervention-jobs --json`

2. Close or normalize narrowed children first.
   - Add deterministic child artifacts (`artifact:`) and real verification (`command:test`, `command:selfcheck`, `command:proof-check`, `command:p10-health`) before trying `review -> done`.
   - If a child is document/evidence-only and the closeout gate demands API/backend/browser proof, leave it in `review`; do not force `done` unless the evidence really satisfies the gate.

3. Reconcile parents after every child tranche:
   - `reconcile --write --json`
   - `blocked-resolve-step --json`
   - If a parent reopens to `pending`, let parent ratification run only through the normal multimodel/lifecycle path.

4. For parents that remain `blocked` only because certification stays advisory/continue-loop despite completed child evidence:
   - If the task’s substantive work is already evidenced and no safe certifying path remains, transition to `archived` with explicit evidence and reason.
   - State that archive is terminal classification, not proof of delivered `done`.
   - Use this instead of fake `done` for evaluation/intake/advisory tasks whose final multimodel gate remains non-authoritative.
   - Verify `reconcile --write` does not revert `archived` back to `blocked`. If it does, patch `sync_auto_subtask_parent()` so pause-gated auto-subtask backfill preserves terminal statuses (`done`/`archived`/`expired`) and only forces `blocked` for non-terminal parents. Expected action after patch: no revert / terminal preserved, not `auto_subtask_parent_backfilled_paused` forcing archive back to blocked.

5. Clean stale async jobs carefully.
   - Before declaring active work, compare worker/multimodel job registries with task status and process command lines.
   - Kill only stale/orphaned jobs whose task has already moved to a terminal or incompatible state, and record structured evidence/reason.

6. Verify final state:
   - `blocked-resolve-step`: `kept_blocked_count=0`, `error_count=0`.
   - `selfcheck`: PASS.
   - `proof-check`: PASS or explicitly classified failures.
   - `worker-jobs`: `alive_count=0` unless intentionally running work remains.
   - `multimodel-intervention-jobs`: `alive_count=0` unless intentionally running certification remains.
   - Control-console/browser readback should show projection trusted and no cards whose display status begins with blocked/阻塞.

## Review gates are not blocked tasks

Execution-flow external-side-effect cards in Human Inbox may remain after active blocked count is zero. Treat them as review/acceptance gates, not unresolved blocked tasks, if their canonical status is `review` and blocked resolver no longer lists them.

Typical remaining review gates:
- API/backend/browser readback proof missing.
- Compliance/external-side-effect closeout requires human acceptance.
- Advisory-only evidence child requires explicit review approval.

Report them separately as “review gates remain,” not “blocked tasks remain.”

## Frontmatter pitfall

When adding evidence to task markdown files, never prepend an `evidence:` block before the opening `---`. That makes the orchestrator unable to find the task or parse frontmatter correctly. Use orchestrator helpers/CLI where possible; if patching manually, insert evidence inside the existing YAML frontmatter and re-run `proof-check` immediately.

## Completion language

Final report should distinguish:
- `blocked=0` achieved.
- Remaining `review`/Human Inbox gates, if any.
- Any archived tasks and why they were archived instead of marked done.
- Verification commands and browser/control-console readback evidence.
