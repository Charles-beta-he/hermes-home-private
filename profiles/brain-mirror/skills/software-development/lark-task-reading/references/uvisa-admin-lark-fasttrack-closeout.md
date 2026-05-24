# UVISA Admin Lark Fast-track Closeout

Use this workflow when UVISA admin Lark tasks need faster throughput without weakening correctness or closeout truthfulness.

## Core invariant

Never conflate these three states:

1. `implementation_done`: code changed + build/test passed + scoped commit.
2. `local_verified`: local/test-env browser evidence covers acceptance atoms.
3. `lark_closed`: user-dispatched online UI retest passed with evidence and Lark was actually marked complete.

If online retest has not been explicitly dispatched/completed, keep Lark open and use `online_ui_retest_pending` or `local_closed_remote_deferred_by_user`.

## Complexity tiers

- `S0`: pure text/field/style quick fix: wording, wrapping, alignment, dropdown width/height, delete extra frontend-only field, key-to-label, amount overflow. Target 10-30 min per item; same page 3-8 items in 1-2h.
- `S1`: single-page UI/interactions: modal/drawer/table/filter layout, prototype-local 1:1 sync. Target 2-4h per page batch.
- `M`: page/module batch: user detail, Debit inflow, dashboard/KYC, wallet/accounting, card activation. Target 0.5-1 day per complex page.
- `L`: backend/API/cross-terminal/real-data contract: admin+backend+C-end sync, computed totals, webhook/third-party data, real API verification.
- `R`: security/review: PII, reveal permissions, role/GA, approval/freeze/deduct/transfer, amount calculation, audit log.
- `B`: blocked: missing prototype/comment image, auth/OTP/access, task explicitly says AI must not close, real data unavailable.

## Fast-track admission

Only S0/S1 may use fast track. Admit if all are true:

- frontend-display only;
- no money calculation, permission, approval, PII, or audit semantics;
- no backend field/contract change;
- no mock;
- page/component target is known;
- acceptance can be proven by build/test/screenshot;
- each Lark GUID has explicit acceptance atoms.

Otherwise upgrade to M/L/R/B.

## Shared evidence rule

Shared evidence is allowed, shared conclusions are not.

Allowed:
- one build for multiple GUIDs;
- one screenshot/browser report for multiple GUIDs **only when the screenshot visibly covers each GUID's named page/module**;
- one scoped commit for a page batch.

Required:
- every GUID maps to checked acceptance atoms;
- screenshot/report lists which atoms it covers;
- final Lark close remains gated by online UI retest when project preference requires it.
- `task_target_surface`, `code_target_surface`, and `evidence_target_surface` must be recorded and must match. A task targeting `用户列表 > 用户详情 > 钱包流水` cannot be closed with a `用户列表` screenshot. A `通道代付记录` task cannot be closed if the account sees a no-permission page.

Fail closed when:
- the target page/module cannot be opened with the production admin account;
- the screenshot only shows a parent/list page while the task targets a detail/drawer/tab/modal;
- required fields/copy from the acceptance atoms are not visible in screenshot/DOM evidence;
- code changes are on a different page/module than the Lark task target.

Before final closeout, call the guard with target-binding metadata, for example:

```bash
python3 ~/.hermes/scripts/lark_task_closeout_guard.py \
  --phase online-ui-retest \
  --user-dispatch-evidence '<user-dispatched online retest>' \
  --remote-build-status deployed \
  --online-url '<production URL checked>' \
  --online-ui-evidence '<native .png/.jpg evidence path>' \
  --ui-regression-status pass \
  --lark-final-evidence '<public-safe Lark evidence text>' \
  --task-target-surface '用户列表>用户详情>钱包流水' \
  --code-target-surface '用户详情钱包流水' \
  --evidence-target-surface '用户详情钱包流水' \
  --required-evidence-keyword TXN_ID \
  --required-evidence-keyword 查看详情 \
  --observed-evidence-keyword TXN_ID \
  --observed-evidence-keyword 查看详情 \
  --json
```

## Upgrade triggers

Upgrade from S0/S1 when:

- same issue appears across multiple pages or requires shared component -> M;
- API field missing, contract unclear, backend computation, C-end sync, real-data proof, local/online inconsistency -> L;
- PII/reveal/roles/GA/funds/approval/freeze/audit -> R;
- prototype image inaccessible, only `[Image]`, auth/OTP missing, explicit do-not-close, no real data -> B.

## Status vocabulary

Use precise states:

- `triaged_fast_track`
- `triaged_page_batch`
- `implementation_done`
- `local_verified`
- `remote_build_pending`
- `online_ui_retest_pending`
- `local_closed_remote_deferred_by_user`
- `lark_writeback_pending`
- `lark_closed`
- `blocked_missing_prototype`
- `blocked_real_api`
- `blocked_manual_owner_required`
- `security_review_required`
- `not_fast_track_eligible`

## Matrix helper

Generate/update the current matrix from a Lark reader JSON snapshot:

```bash
python3 ~/.hermes/scripts/lark_task_reader.py --scope-mode only --no-docs > /tmp/lark_uvisa_current_tasks_with_comments.json
python3 ~/.hermes/scripts/uvisa_admin_lark_fasttrack_matrix.py --input /tmp/lark_uvisa_current_tasks_with_comments.json
```

Outputs:

- `~/.hermes/state/uvisa-admin-lark-fasttrack/matrix.latest.json`
- `~/.hermes/state/uvisa-admin-lark-fasttrack/matrix.latest.md`
- `~/.hermes/state/uvisa-admin-lark-fasttrack/matrix.latest.csv`

If Lark token is expired and auto-auth fails, use the newest existing trusted snapshot but mark the source timestamp and do not claim it is live.

## Batch execution order

1. Build matrix: `GUID -> page -> tier -> batch -> acceptance_atoms -> blocker`.
2. Clear S0/S1 by page batch first.
3. Verify with `git diff --check`, targeted tests if any, and `npm run build`.
4. Capture 14-inch browser evidence for page-level UI work.
5. Write implementation-sendback comments only when evidence is attached.
6. Keep final Lark close for user-dispatched online UI retest.
