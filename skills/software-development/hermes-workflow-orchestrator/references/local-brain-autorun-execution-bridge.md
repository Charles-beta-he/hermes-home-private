# Local Brain Autorun / Execution Bridge

Extracted from `/Users/charles/.hermes/skills/software-development/hermes-workflow-orchestrator/SKILL.md` on 2026-07-01T08:55:33.664327+00:00 by generic core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

## Local Brain Autorun / Execution Bridge

When the user asks whether the local-brain task pool lacks automatic dispatch/execution, or asks to implement autonomous task-pool execution, use `references/local-brain-autorun-bridge.md`.

Key rule: safe dispatch and execution are separate. Do **not** convert the no-agent safe tick into a default executor. The safe pattern is a default-off, allowlist-driven `auto-claim-and-handoff` bridge that claims one eligible task and writes a bounded handoff/proof head; an external bounded runner may execute, and completion must still pass proof-gated `review -> done`. Never execute Markdown task bodies or mark `done` directly from a tick.

### When the user says "全盘推进" / "push the whole pool forward"

Treat this as a bounded advancement request, not permission to force-close the queue.

1. Read current health first:
   ```bash
   python3 ~/.hermes/scripts/brain_task_orchestrator.py list --include-done --json
   python3 ~/.hermes/scripts/brain_task_orchestrator.py next --json
   python3 ~/.hermes/scripts/brain_task_orchestrator.py dispatch-dry-run --json
   python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json
   ```
2. Attempt the normal bounded automation path:
   ```bash
   python3 ~/.hermes/scripts/brain_task_orchestrator.py autorun-runner --actor hermes --ttl-minutes 60 --json
   python3 ~/.hermes/scripts/brain_task_orchestrator.py auto-claim-and-handoff --actor hermes --ttl-minutes 60 --json
   python3 ~/.hermes/scripts/multimodel_intervention_dynamic_step.py --json
   ```
3. If both runner and handoff return `eligible=false`, inspect the deny reason instead of treating it as a dead pool. For fail-closed non-execution gates such as `autorun_disabled` or `allowlist_miss`, do **not** stop at reporting. Manually advance one bounded mainline step on the highest-value dispatchable task: `claim` it, reconcile/read the task note, perform one bounded audit or evidence-writing step that preserves architecture direction, write proof back to the note, then `release` it to the appropriate non-terminal state. If `multimodel_intervention_dynamic_step.py --json` reports `worker_already_running`, treat that as compatible background progress, not as a reason to skip the bounded manual slice.
4. For external-repo advisory tasks, prefer evidence slices that narrow uncertainty instead of trying to close the task: repo-family boundary checks, support-repo surface checks, README/package/tree evidence, and explicit notes separating real implementation surface from README/marketing/docs claims. Write the narrowed decision gate back into `Proof Log` and `Blockers / Confusions` so the next pass starts from a tighter question.
5. Re-measure immediately after the manual slice using `next --json` and `selfcheck --json`, plus a status snapshot that is small enough to parse reliably. Prefer `list --json` for active-pool counts and target-task verification; reserve `list --include-done --json` for broad audits because large all-history payloads may be noisy for machine parsing. If all-history parsing is noisy, fall back to `list --json` plus a direct read of the target task note, and in Python use `json.loads(text, strict=False)` for orchestrator output before declaring the payload unusable. Report the delta, not just the latest snapshot: blocked count movement, done count movement, active count movement, and what specifically advanced.

Key interpretation rules during this pass:
- `PASS_ADVISORY_ONLY` is progress but **not** closeout authority; advisory-completed tasks still need a real execution/evidence pass.
- `economy_gate.action=pause` with messages like `task has 10 failed T3 rounds (max=5)` is a fail-closed pause, not a dead worker. Report it as a targeted evidence/human-review gate.
- If active dispatchable work remains while blocked count falls or done count rises, conclude the pool is advancing even if autorun is disabled.
- If a task shows current multimodel state `certified / PASS / LOOP_DONE` but `auto-close-review` or review closeout still skips, inspect the `evidence:` list for stale bare `multimodel_*:...` entries. Normalize/remove them before retrying closeout, and if the orchestrator is the writer, patch it to emit `command:`-prefixed evidence at source to prevent repeated poisoning.

When adding a local-brain task from an external idea artifact such as an image/social-post screenshot, treat it as task creation plus evidence deposition, not as implementation closeout. The task note should include source artifact path, analysis/tick artifacts, certification status, P0/P1/P2 plan, and explicit caveats if multi-model discussion is `not_certified`. If the artifact is a local app-cache image (for example a Lark `sdk_storage/.../resources/images/*.jpg` path), first copy it into a canonical vault evidence folder such as `~/Documents/brain/05-实践与项目/projects/<project>/evidence/screenshots/`, write a sidecar JSON with original path, copied path, sha256, byte size, and observed issue, then reference the canonical copy in the task frontmatter `evidence:` list and body. Enrich the generated task note with screenshot-derived problem statement, verification questions, execution notes, and acceptance criteria; do not leave the auto-generated skeleton as the only context for an executor. After creating or patching the task, regenerate derived dashboards and run `dashboard --write`, `proof-check`, `selfcheck`, `dispatch-dry-run`, `taskpool_watch_report.py`, `brainctl sync`, and `brainctl reindex` to verify the taskpool remains healthy. If `brainctl search` returns no hits for the new task, do not treat that as creation failure; verify via `brain_task_orchestrator.py list --json` and direct `read_file` on the task note, because FTS can lag or over-constrain mixed Chinese/English terms.

### Work delivery vs self-evolution routing

When補入任务池 or scheduling autorun, explicitly classify the task as one of:
- `work/product delivery`: user/project/Lark/PRD/customer-facing delivery, blocker repair, closeout follow-up.
- `evolution/self-improvement`: Hermes skills, router, cron, eval, governance, framework analysis.
- `advisory/research`: evidence-gathering or analysis that may later spawn implementation work.

For `work/product delivery`, set project/workspace/concepts so it cannot be mistaken for Hermes evolution (for example `concepts: work-task,uvisa,lark,backend,product-closeout`), prefer P0/P1 when it is a returned blocker, and ensure the next dispatchable task reflects that priority. Do not let open-ended self-evolution tasks starve P0/P1 work. After adding the note, run:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py dashboard --write --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py proof-check --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py dispatch-dry-run --json
python3 ~/.hermes/scripts/taskpool_watch_report.py
python3 ~/.hermes/scripts/brainctl.py --json sync && python3 ~/.hermes/scripts/brainctl.py --json reindex
```

Report the next executor cron (`local-brain-taskpool-auto-completer`) and occasional report cron times. If a work task is now first in `dispatch-dry-run`, say so explicitly.
