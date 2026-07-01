# Active-claim reconciliation and public-media intake readback

Scope: taskpool/control-plane sessions where dispatch appears stalled, capacity is full, or a public media link is converted into a governed task card. Applicability: Hermes local brain/taskpool with `brain_task_orchestrator.py`, `taskpool_active_claim_guard.py`, and event hooks. Anti-conditions: do not use this to delete tasks, mark work done, bypass proof gates, bypass QR/App gates, or release a claim while a real worker process is still present.

## Active accounting false-full loop

Symptoms:

- Kanban shows no or few `running` tasks, but dispatch dry-run reports no capacity / no boundary-safe slots.
- `taskpool_active_claim_guard.py --json` reports `active_count > 0` with `orphan_count > 0`.
- Individual rows have `status: claimed/running`, a `run_id`, but `worker_process_detected: false`.

Procedure:

1. Re-check current state first; do not rely on stale handoff summaries.
2. Run the active-claim guard in report mode:

```bash
python3 ~/.hermes/scripts/taskpool_active_claim_guard.py --json
```

3. If and only if rows are classified `orphan_active_claim` and no worker process is detected, release through the governed lifecycle path, not by editing task files:

```bash
python3 ~/.hermes/scripts/taskpool_active_claim_guard.py \
  --release-orphans \
  --reason 'operator reviewed orphan worker claim; worker process absent; release to pending via governed lifecycle' \
  --json
```

4. Read back `post_release.active_count == 0` and `post_release.orphan_count == 0`.
5. Run the correct dry-run command name for this orchestrator:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py dispatch-dry-run --json
```

Do not use `dispatch --dry-run`; this CLI uses `dispatch-dry-run`.

6. If a subsequent dynamic/event tick starts workers, re-run the guard. A healthy state is `orphan_count: 0` and `worker_process_detected: true` for active rows. In that case, do not release them just to make capacity available.

## Event-hook errors after task add

`brain_task_orchestrator.py add` can return top-level `status: OK` while the `event_hook` reports `ERROR`. Treat this as a mixed result, not an automatic failed add.

Common non-blocking case:

- `event_hook.multimodel_step.reason: allowlist_miss`
- `safety: task not in multimodel intervention allowlist`

Procedure:

1. Preserve the top-level create result and generated path/id.
2. Read back the created task markdown.
3. If frontmatter/body projection collapsed repeated `--accept`, `--red-line`, or evidence detail into incomplete body text, patch the task card immediately so the visible Acceptance Criteria and Red Lines match the intended evidence gates.
4. Report the hook error as a gate/queue condition, not as proof that the card was not created.

## Public media intake card quality gate

For QR/App-gated previews such as WeChat Channels:

- Create an evidence directory under `docs/private/` with `media-index.json`, cover/screenshot when available, and `analysis.md`.
- The task card must include source link, resolved URL, access boundary, visible preview facts, current verification status, red lines, and acceptance criteria.
- If the named artifact cannot be identified from public sources, the correct task is source-identification + overlap review, not adoption.
- Marketing claims (line counts, fear/framing claims, star counts) become verification requirements, not accepted facts.

## Verification checklist

- [ ] Active-claim guard report captured fresh.
- [ ] Orphans released only when `worker_process_detected: false`.
- [ ] Release used `taskpool_active_claim_guard.py --release-orphans`, not direct file mutation.
- [ ] `dispatch-dry-run --json` was used for dry-run readback.
- [ ] If new live workers appear, `orphan_count == 0` was verified.
- [ ] For new media task cards, the generated markdown was read back and patched if acceptance/red-line projection was incomplete.
