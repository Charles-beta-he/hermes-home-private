# Daily report external-signal replay and intake verification

Applicability: use when a daily report contains GitHub Trending, Product Hunt, or similar external source sections and the user expects those signals to become governed taskpool candidates. Anti-condition: do not use this as permission to auto-create production tasks for ordinary news; keep task creation behind report evidence, governance fields, and dedupe gates.

## Problem pattern

A composed daily report can mention GitHub/PH items in the markdown body while its `*.tasks.json` sidecar has `candidates: []`. In that case the failure is usually **report body → sidecar candidate generation**, not `daily_report_task_ingest.py` or taskpool writeback.

## Verification path

1. Confirm the report date and inspect the real sidecar summary:
   - `daily_report_task_ingest.py --proposal-json <date>.tasks.json --json`
   - If `proposal_count=0`, record this as a sidecar-generation gap.
2. Build or regenerate a bounded replay sidecar from the same report body:
   - one candidate per GitHub Trending repo worth analyzing;
   - one candidate per Product Hunt product worth analyzing;
   - include `dedupe_key`, evidence bundle, priority, acceptance evidence, anti-drift check, and dependency order.
3. Run ingest dry-run first:
   - expected healthy replay: all candidates are `dry_run`, `invalid_count=0`.
4. For write-path verification, use an isolated temporary vault, not the real brain vault:
   - set `HERMES_BRAIN_VAULT`, `HERMES_DAILY_REPORT_INGEST_STATE`, and `HERMES_DAILY_REPORT_MANUAL_REQUESTS` to temp paths;
   - run `--write` once and expect `created_count == candidate_count`;
   - run `--write` again and expect `created_count=0`, `skipped_count == candidate_count`, reason `already_emitted_for_report`.
5. Read back at least one generated task and verify frontmatter contains report evidence and the intended analysis boundary.

## Pitfalls

- `architecture_target` must be accepted by `brain_task_orchestrator.py add`. If the source signal naturally maps to `hermes-agent` or `browser-automation`, normalize to an allowed control-plane target such as `taskpool` (or another allowed enum) and keep the original mapping in evidence/prose if useful.
- Product Hunt analysis candidates should include competitor/customer/features/monetization/risk analysis in `dependency_order` or objective; do not treat a PH vote count alone as task justification.
- GitHub Trending items may become P2/P3 analysis/watch tasks, not necessarily implementation tasks. Preserve the distinction in priority and acceptance evidence.
- If the replay succeeds but the original sidecar was empty, the next fix belongs in the daily-report generator/prompt, not in taskpool ingest.

## Evidence contract

A good replay report records:

- original report path and original sidecar counts;
- replay sidecar path;
- candidate counts by source (GitHub, PH, etc.);
- dry-run artifact and counts;
- temp-vault write artifact and idempotency result;
- any enum/contract boundary discovered during replay.
