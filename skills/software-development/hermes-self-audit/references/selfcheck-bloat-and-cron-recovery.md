# Self-check bloat and cron recovery pattern

Use when Hermes self-check shows a low diagnostics score driven by task-file bloat, taskpool schema timeouts, log bloat, and cron jobs stuck in `last_status=error`.

## Applicability

- Hermes/local-brain health checks where diagnostics report failures such as:
  - `task-file-bloat`
  - `taskpool-schema` timeout
  - `log-file-bloat`
  - `cron-job-health` with scheduler/runtime errors
  - ContextCard refresh job errors
- Task markdown frontmatter has large escaped single-line fields.

## Anti-conditions

- Do not treat old cron errors as current truth until rerunning or reading back the job after the underlying fix.
- Do not delete original task files or logs without a quarantine/backup path.
- Do not encode transient provider/auth/setup failures as durable rules.

## Procedure

1. Run the modular diagnostic first and classify current failures:
   - `python3 ~/.hermes/diagnostics/runner.py --json`
   - Also run the legacy check when task bloat is suspected:
     - `python3 ~/.hermes/scripts/health-check.py --json`
2. If `task-file-bloat` appears, inspect whether the large field is actually `evidence_bundle` or another frontmatter field such as:
   - `dependency_order`
   - `parallel_group`
   - `conflict_group`
   - `workspace_isolation`
3. Use the streaming quarantine repair pattern:
   - move original bloated files under `~/taskpool-bloat-quarantine/<timestamp>/`
   - rewrite the original path with sanitized frontmatter
   - preserve a `manifest.json` containing original path, quarantine path, size before, replaced fields, skipped bytes, and new size
4. Upgrade the bloat repair script, if needed, to cover the actual exploding fields rather than only `evidence_bundle`.
5. Rerun:
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json`
   - `python3 ~/.hermes/diagnostics/runner.py --json`
6. Re-run affected cron jobs after the underlying cause is fixed. The scheduler keeps old `last_status=error` until the job successfully runs again.
7. If a ContextCard rich refresh fails only because there are no new valid rich candidates, treat that as a steady-state no-op, but keep all other writer failures fail-closed.

## Verification checklist

- `task-file-bloat: 0 bloated files`
- `taskpool-schema: status=PASS`
- `cron-job-health: 0 error jobs` after rerunning affected jobs
- bloat quarantine manifest exists and originals are preserved
- focused git commits were made only for changed reusable scripts/docs
- remaining diagnostics failures are explicitly classified rather than hidden

## Pitfalls

- A task file may be only slightly over the size threshold after one cleanup; rerun diagnostics and repair again until count is zero.
- The diagnostic runner can exit `0` even with non-blocking BAD checks; read the JSON result list, not just the shell exit code.
- Log rotation scripts that preserve `.rotated.*` files under the same log directory may still count toward total log size if the diagnostic sums all files. Report this as retained backup size unless the user authorizes archival/deletion.
