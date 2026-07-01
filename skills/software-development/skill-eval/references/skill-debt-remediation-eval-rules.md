# Skill Debt Remediation Eval Rules

Use when auditing or repairing skill-library debt such as oversized root `SKILL.md` files, missing anti-conditions, missing pitfalls, missing verification checklists, or weak trigger/frontmatter shape.

## What to evaluate

Treat skill debt remediation as a library-quality regression task, not just markdown editing.

Evaluate these surfaces separately:

1. **Hard limits** — invalid frontmatter, `skill_too_large`, missing required fields.
2. **Context cost** — `core_body_large`, always-read material, root skills that read like README/docs mirrors.
3. **Routing boundary** — description trigger, positive/neighbor/forbidden/no-load prompt matrix.
4. **Progressive loading** — root `SKILL.md` carries the entry contract; `references/` carries conditional detail.
5. **Safety boundary** — local skill edits do not imply external model calls, installs, credential entry, dispatch, publish/deploy/push, destructive cleanup, or force-close.

## Progressive-loading regression check

When a large root is compacted:

- The extracted reference exists under `references/` with provenance.
- The root section names the exact reference path.
- The root says when to load the reference.
- The root keeps a minimum rule/anti-condition usable without loading the reference.
- The root remains class-level, not a one-session report.
- The patch did not silently discard content; the original detail is recoverable from root + reference.

## Deterministic auditor loop

Recommended eval loop:

1. Run/read the skill taxonomy auditor report.
2. Select a bounded batch by risk/payoff.
3. Patch/extract with progressive-loading pointers.
4. Rerun auditor selftest.
5. Rerun auditor report generation.
6. Read back:
   - global hard error count;
   - warning counts by code;
   - each target skill's `size_chars` and `findings`;
   - representative reference files.

A remediation pass is not complete because files were written. It is complete only after fresh audit/readback shows the intended finding reduction.

## Full-drain pattern for size debt

When the user explicitly authorizes full skill-debt remediation:

1. Clear hard failures first (`skill_too_large`, invalid frontmatter), then clear `core_body_large`, then quality-shell warnings.
2. Prioritize active/high-frequency skills before archives, but if the goal is a global zero-count class, include archives in the final pass.
3. Use manual extraction for high-value skills where section names and safety boundaries matter; use a conservative generic extraction pass only for remaining large sections that are clearly conditional details.
4. Skip or preserve core routing sections such as `Overview`, `When to Use`, `Common Pitfalls`, `Verification Checklist`, and `Definition of Done` unless you are deliberately repairing that shell.
5. For each extracted section, create a same-skill `references/<slug>.md` with provenance and replace the root section with: exact reference path, when to load it, and a minimum in-root rule.
6. Rerun the auditor until the target count is actually zero; do not stop at “reduced”.
7. Write a round report that records route/multi-model boundary, changed roots, representative references, exact latest report paths, and remaining non-target warning classes.

## Multi-model routing evidence rule

If a user asks to use multi-model intelligent routing during skill governance:

- Record whether routing was a local dry-run/advisory artifact or a real external provider execution.
- Do not claim multi-model certification when `externalModelCallExecuted=false`.
- Use model routing as planning/review evidence; use deterministic auditor output as closeout proof for local skill compaction.
- If live provider smoke is needed, it requires separate budget/authority and fresh readback.

## Report template

```markdown
# Skill Debt Remediation Report

## Routing / Authority
- route/domain/risk:
- side-effect boundary:
- multi-model evidence: live external execution OR local dry-run/advisory

## Changed Roots
- `<skill>/SKILL.md`: before/after size, findings after, references added

## Verification
- auditor selftest command/result
- auditor report command/result
- latest report paths
- target findings readback

## Remaining Debt
- hard errors:
- warning counts by code:
- next recommended queue:

## Boundary
- no external model calls unless explicitly true
- no installs/credentials/dispatch/destructive/publish/force-close
```
