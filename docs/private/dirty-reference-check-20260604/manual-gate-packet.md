# Dirty-state reference check and manual gate packet — 2026-06-04

Scope: read-only reference check for `media/generated` and conservative classification for `runtime/logs`. No generated files, logs, `.gitignore`, configs, DBs, memories, skills, profiles, scripts, or brain/workpad files were modified.

Important: governance inventory/report artifacts were excluded from reference search to avoid self-references created by this cleanup process.

## media/generated

- total: 338
- referenced by searched non-governance text corpus: 7
- no references found in searched non-governance text corpus: 331
- extension counts: {'<none>': 1, '.png': 302, '.txt': 35}
- signature counts: {'other': 1, 'png': 302, 'text': 35}
- search scope: 28566 text files under ['docs', 'notes', 'scripts', 'cron', 'config', 'memories']

Interpretation: most items are untracked PNG/TXT generated artifacts. A no-reference result is not deletion authority; it only supports a narrow candidate policy after manual approval.

Candidate policy requiring approval:

1. Add a narrow ignore rule for future `media/generated/` artifacts if this directory is confirmed as reproducible cache/output.
2. Archive or leave current untracked files untouched until an owner confirms they are not evidence attachments.
3. Do not delete files referenced by docs/tasks/evidence; preserve them as artifacts if any are referenced.

## runtime/logs

- total: 35
- status counts: {' M': 3, ' D': 3, '??': 29}
- class counts: {'audit_or_evidence_log_manual_review': 10, 'tracked_deleted_manual_review': 3, 'disposable_runtime_candidate': 22}

Interpretation: runtime logs split into disposable candidates and audit/evidence-looking logs. Tracked deletions require separate manual review; do not auto-commit deletions.

Candidate policy requiring approval:

1. Ignore only disposable append-only runtime logs after excluding audit/evidence logs.
2. Preserve audit/evidence-looking logs (`health`, `quarantine`, `missed`, `ensemble`, `model-router`, `cross-patch`, etc.) until source-of-truth policy is explicit.
3. For tracked deleted logs, choose restore vs commit deletion explicitly; no automatic action.

## Manual intervention point

The next side-effect would be a policy change (`.gitignore`) or file disposition (archive/delete/restore). This requires explicit approval of one of the candidate policies above.
