# 4H Self-Scan Cron Runbook

Use when a scheduled Hermes health job asks to run `~/.hermes/scripts/self-scan-4h.py`, inspect the self-scan ledger, and refresh the evolution dashboard.

## Procedure

1. Run the scanner exactly:
   ```bash
   python3 ~/.hermes/scripts/self-scan-4h.py
   ```
2. Read the append-only ledger:
   ```text
   ~/.hermes/notes/engineering-cybernetics/self-scan-log.jsonl
   ```
3. Classify only current or recurring findings as actionable:
   - latest record `issue_count == 0` means current scan is healthy;
   - historical WARNING/ERROR entries are context, not active incidents, unless they recur in the latest record or a recent streak;
   - report the latest healthy streak and last historical issue when useful, but do not create repair work for old resolved warnings.
4. Refresh the dashboard:
   ```bash
   python3 ~/.hermes/scripts/refresh-dashboard.py
   ```
5. Verify by read-back of dashboard head/key fields, especially:
   - `Status:`
   - `V` and `V̇`
   - skill total / evaluated count / D-grade count
   - Darwin coverage.
6. If the cron instruction includes a “silent if nothing new” delivery rule, suppress only when truly no user-visible report is warranted. If the user explicitly asked to execute and update artifacts, a concise evidence report is acceptable even when healthy.

## Interpretation

- Actionable WARNING/ERROR = appears in the latest scan record or recent repeated records.
- Resolved historical WARNING/ERROR = useful evidence for trend context, but not a root-cause repair target.
- Dashboard files and scan logs are derived/runtime state; mention them as updated artifacts, but avoid turning their update into a code-change claim.

## Anti-conditions

Do not use this runbook for generic `hermes doctor`, post-update checks, or taskpool selfcheck incidents; those have separate Hermes/self-audit workflows.
