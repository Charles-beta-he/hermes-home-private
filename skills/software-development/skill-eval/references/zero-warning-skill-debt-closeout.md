# Zero-warning skill debt closeout

Use when a session performs Hermes skill-library debt remediation with a deterministic auditor and the user asks to continue until there is no next step.

## Procedure

1. Define the active debt contract from the auditor, not from subjective taste.
   - Hard size/validation findings first.
   - Then quality-shell findings such as trigger-shaped descriptions, `## When to Use`, anti-conditions, `## Common Pitfalls`, and `## Verification Checklist`.
2. Prefer class-level progressive loading over one-session skill proliferation.
   - Keep root `SKILL.md` as the routing/control surface.
   - Move long conditional detail into adjacent `references/` files with provenance headers.
3. For remaining shell warnings, use minimal generic scaffolds only when semantic certainty is low, especially in archives.
   - Do not claim every archived workflow is semantically certified just because it now has the expected headings.
4. Re-run the auditor after every bulk pass and make the closeout claim only from fresh `latest.json` / `latest.md` readback.
5. If the auditor reaches zero findings, stop the debt loop unless the user separately authorizes a larger class of work.

## Git packaging boundary

A zero-warning auditor state is not permission to commit. Before staging:

1. Inspect the repository dirty state with a machine-parseable status format, preferably `git status --porcelain=v1 -z`.
2. Bucket paths into at least:
   - session reports
   - session scripts
   - skill tree changes/untracked files
   - out-of-scope dirty state
3. If broad unrelated state exists, produce a DecisionPacket / ContinuationPacket instead of staging.
4. Offer explicit options:
   - local-only scoped commit plan with exact staging manifest, no push;
   - isolated patch bundle, no git index change;
   - leave uncommitted and treat reports as closeout.
5. If staging is later authorized, verify with `git diff --cached --name-status` and `git diff --cached --check` before committing.

## Anti-conditions

Don't use this as authority for:
- live cross-model routing tests that spend provider budget;
- semantic certification of all skills;
- broad git add/commit/push in a dirty home/control-plane repository;
- deleting or consolidating skills without a separate curator/authority gate.

## Verification checklist

- [ ] Auditor selftest passed.
- [ ] Full auditor report read back with `findings_by_code == {}` and `findings_by_severity == {}`.
- [ ] Closeout report path exists and was read back.
- [ ] Multi-model routing evidence is clearly labeled advisory/dry-run unless real provider calls were authorized and read back.
- [ ] Git staging/push boundaries are explicit; no blind commit is performed from a broad dirty tree.
