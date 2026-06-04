# Hermes dirty-state mechanical review proposal — 2026-06-04

Scope: read-only mechanical review for `media/generated`, `notes/generated-reports`, and `runtime/logs`. No `.gitignore` changes, no deletion, no reset, no operational files changed.

## Bucket summaries

## media/generated
- count: 338
- status: {'??': 338}
- extensions top: [('.png', 302), ('.txt', 35), ('<none>', 1)]
- signatures: {'text-ascii': 5, 'png': 302, 'binary/unknown': 29, 'json-like': 2}
- recommendation: candidate_narrow_generated_review: likely generated media/cache, but do not delete/ignore until path origins and any referenced artifacts are checked.
- next gate: `manual_approve_ignore_or_archive_after_reference_check`

## notes/generated-reports
- count: 107
- status: {' M': 7, '??': 100}
- extensions top: [('.md', 77), ('.json', 25), ('.jsonl', 5)]
- signatures: {'binary/unknown': 77, 'json-like': 30}
- recommendation: candidate_documentation_artifacts: generated reports may be evidence; preserve or archive latest-only, not bulk delete.
- next gate: `manual_select_keep_archive_policy`

## runtime/logs
- count: 35
- status: {' M': 3, ' D': 3, '??': 29}
- extensions top: [('.jsonl', 27), ('<missing>', 3), ('<none>', 3), ('.json', 2)]
- signatures: {'json-like': 29, 'missing': 3, 'text-ascii': 3}
- recommendation: candidate_runtime_logs: logs may be ignorable only after confirming they are not audit/evidence logs; deleted tracked log paths need separate git policy.
- next gate: `manual_approve_log_policy`

## Decision needed before side effects

1. `media/generated`: approve a narrow generated-artifact policy only after checking references from docs/tasks. Candidate actions: ignore future generated files, archive current artifacts, or keep committed evidence artifacts.
2. `notes/generated-reports`: decide whether reports are evidence records. Candidate actions: keep all, archive old, or retain only indexed summaries.
3. `runtime/logs`: separate audit/evidence logs from disposable runtime logs. Candidate actions: ignore append-only runtime logs, preserve audit logs, handle tracked deletions separately.

## Stop conditions

- Any file appears referenced by task evidence, brain workpad, or governance reports.
- Any bucket includes config/memory/DB/cron/protected state.
- Any staged diff outside `docs/private/dirty-mechanical-review-20260604/` and this proposal path.
- Any action would delete tracked history or reset modified files.
