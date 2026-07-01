# Skill Size Remediation Pattern

Use when an audit reports hard skill-size failures such as `skill_too_large`, or when a class-level skill has accumulated too much root-body detail and needs progressive loading.

## Classifier

- Reusable procedure, pitfall, or verification checklist: keep in the class-level `SKILL.md` only if it is short and on the common path.
- Session-specific detail, generated docs, long command catalogs, transcripts, or external excerpts: move to `references/` with applicability and anti-conditions.
- Starter artifacts: put under `templates/`.
- Re-runnable checks or fixture generators: put under `scripts/`.
- Concrete task/session progress: do not save as skill content.

## Safe extraction workflow

1. Identify the hard failure first; do not start with broad semantic rewrites.
2. Pick one bounded extraction candidate: a long generated block, detailed output contract, command catalog, or archived tail.
3. Write the extracted content to an adjacent `references/<topic>.md` file.
4. Add a provenance header naming the source `SKILL.md`, extraction date, and whether the body is verbatim or normalized.
5. Replace the root section with a compact pointer that says when to load the reference and what anti-conditions remain in force.
6. Re-run the skill auditor or equivalent size check.
7. Read back the root pointer and the reference file before claiming remediation.

## Preservation rule

Do not delete knowledge merely to pass a size gate. Prefer progressive loading unless the material is clearly duplicate, stale, or already captured elsewhere. Deletion should be a separate reviewed cleanup action.

## Good extraction candidates

- Generated API documentation embedded in root `SKILL.md`.
- Long examples or command catalogs needed only after a subproblem is confirmed.
- Detailed presentation/output contracts used late in a workflow.
- Archived skill tails useful only for historical rehabilitation.

## Bad extraction candidates

- The `description` routing surface.
- Minimal `Overview`, `When to Use`, `Common Pitfalls`, and `Verification Checklist` sections.
- Safety gates, anti-conditions, credential rules, destructive-operation warnings, or side-effect boundaries that must be visible on first load.
- Short decision rules that determine whether the skill should run at all.

## Verification checklist

- [ ] Root `SKILL.md` remains valid and under the hard size limit.
- [ ] Root still points to the extracted reference with clear load conditions.
- [ ] Reference has a provenance header and preserves the extracted detail.
- [ ] Auditor reports the hard size failure cleared.
- [ ] No external install, credentials, runtime config change, or unrelated lifecycle mutation was performed as part of remediation.
