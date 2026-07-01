# Dirty control-plane repo scoped commit boundary

Use when a completed local remediation or governance task produces many files under a Hermes/control-plane home and the user asks to continue, package, or commit.

## Pattern

1. Treat commit/push as a separate authority boundary from local remediation.
2. Read git state with a machine-parseable command such as `git status --porcelain=v1 -z`.
3. Bucket changes before staging:
   - intended session artifacts, reports, scripts;
   - skill-tree changes and newly extracted references;
   - unrelated runtime outputs, notes, project profiles, cron outputs, submodules, workflow artifacts;
   - deletions whose provenance is unclear.
4. If unrelated state is broad, do not stage automatically. Produce a DecisionPacket with:
   - objective;
   - completed evidence;
   - candidate packaging paths;
   - requested authority;
   - rollback/escape hatch;
   - post-action verification.
5. Offer packaging choices:
   - local-only scoped commit plan with exact staging manifest;
   - isolated patch bundle under docs/private without touching the index;
   - leave uncommitted and use reports/readbacks as closeout evidence.

## Pitfalls

1. **Zero-test-pass-is-not-commit-authority**: a clean auditor/test run proves the local artifact state, not that every dirty file belongs in the same commit.
2. **Broad dirty home trap**: Hermes home repos often contain runtime outputs, cron records, notes, project profiles, submodules, and workflow evidence. Never `git add skills/ docs/ scripts/` blindly in that state.
3. **Deleted-file ambiguity**: large numbers of deletions may be cleanup, curator output, or unrelated drift. Do not stage deletions without exact provenance.

## Verification checklist

- [ ] `git status --porcelain=v1 -z` or equivalent was parsed without truncation.
- [ ] Candidate stage list excludes unrelated dirty state.
- [ ] No staging was performed before the human chose a packaging option.
- [ ] If staging is authorized later, `git diff --cached --name-status` and `git diff --cached --check` are read back before commit.
- [ ] Push remains a separate exact remote/branch authority gate.
