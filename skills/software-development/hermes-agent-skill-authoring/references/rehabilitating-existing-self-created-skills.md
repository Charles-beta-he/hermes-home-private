# Rehabilitating Existing Self-Created Skills

Extracted from `/Users/charles/.hermes/skills/software-development/hermes-agent-skill-authoring/SKILL.md` on 2026-07-01T08:55:33.664327+00:00 by generic core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

## Rehabilitating Existing Self-Created Skills

When improving a user-local skill that already exists under `~/.hermes/skills/`, do not jump straight to rewriting prose. Run a short diagnosis loop first:

1. **Classify the failure mode**
   - Trigger failure: description too vague / too narrow / wrong vocabulary
   - Control-flow failure: wrong primary mode (for example Pipeline written like Wrapper)
   - Scope failure: duplicates an umbrella skill or mixes multiple jobs
   - Artifact failure: missing template / reference / checklist / verification
   - Maintenance failure: body too long, stale examples, broken related_skills, weak pitfalls

2. **Choose the smallest effective repair**
   - Tighten `description` when routing is the problem
   - Re-section the body when control-flow is the problem
   - Split long details into `references/` when density is the problem
   - Add `templates/` for Generator skills
   - Add rubric/checklist tables for Reviewer skills
   - Add stage gates and evidence checks for Pipeline skills
   - Merge into an existing umbrella skill when the standalone trigger class is not justified

3. **Prefer patch over rewrite**
   - Use `skill_manage(action='patch')` for focused repairs
   - Use `skill_manage(action='edit')` or full-file rewrite only when the skill needs a structural reset
   - Preserve the skill name unless the trigger class itself changed

4. **Verify read-back, not intention**
   - Re-open the skill with `skill_view`
   - Confirm frontmatter still parses cleanly
   - Confirm the dominant mode is now obvious from the body
   - Confirm examples/checklists/templates align with the mode

### Rehabilitation heuristics by symptom

| Symptom | Likely fix |
|---------|------------|
| Skill rarely auto-loads | rewrite `description` around trigger class |
| Skill loads but outputs drift | convert toward Generator or add template/checklist |
| Skill skips necessary steps | convert toward Pipeline with explicit gates |
| Skill gives shallow critiques | convert toward Reviewer with rubric/severity |
| Skill asks too little before acting | convert toward Inversion with interview flow |
| Skill feels like random notes | pick one primary mode and move the rest to references |
| Skill overlaps another skill | patch umbrella skill or merge instead of keeping both |

### Multi-skill rehabilitation pass (recommended order)

When auditing a batch of legacy self-created skills, do not review them through only one lens. Use three short passes, then repair in order of confidence:

1. **Trigger/frontmatter pass**
   - Check whether `description` expresses a clear trigger class and preferably starts with `Use when ...`
   - Normalize `version`, `author`, `license`, and `metadata.hermes.{tags,related_skills}`
   - Remove ad-hoc frontmatter fields when they are not part of the stable peer shape

2. **Mode/structure pass**
   - Infer the primary mode (Wrapper / Generator / Reviewer / Inversion / Pipeline)
   - Check whether the body sections make that mode obvious
   - For mature skills, prefer the standard shell: `Overview` -> `When to Use` -> body -> `Common Pitfalls` -> `Verification Checklist`

3. **Ecosystem/governance pass**
   - Identify overlap, umbrella fit, and whether details should move to `references/`
   - Distinguish `patch now` from `merge later`
   - Treat duplicate tails, broken examples, and conflicting command snippets as immediate repairs

Repair order:
- First: low-risk contract fixes (description, frontmatter, related_skills)
- Second: obvious structural corruption (duplicate headings, dangling tails, contradictory command examples)
- Third: deeper body reshaping or umbrella slimming

This sequencing keeps the library improving without overfitting one session's wording or doing unnecessary full rewrites.

### Library-wide bulk rehabilitation rule

When the user asks for a full-library batch pass, split the work into two layers:

- **Safe contract-layer normalization (scriptable):** add missing `version` / `author` / `license`, ensure `metadata.hermes`, move top-level `tags` and `related_skills` into `metadata.hermes`, normalize obvious heading variants, repair invalid frontmatter YAML, and eliminate empty `related_skills` with conservative umbrella fallbacks.
- **Semantic trigger/body rewrites (manual or tightly reviewed):** `description` modernization, primary-mode reassignment, section-shell injection, and umbrella slimming.

Do the contract layer first and verify by exact counts before touching trigger semantics. Do **not** batch-rewrite every `description` into `Use when ...` with a naive script; trigger text is routing logic, not just style.

After the contract layer, the highest-leverage semantic batch order is:

1. **Umbrella/root routing pass** — rewrite placeholder category roots into real routing surfaces with `Routing Guide`, `Selection Rules`, child-skill maps, and explicit counter-triggers.
2. **Verification/pitfall pass** — raise weak shells to a minimum actionable floor (for example 3+ checklist items and 3+ numbered pitfalls) before doing stylistic prose edits.
3. **Overview/counter-trigger pass** — expand obviously thin `Overview` sections and add `Don't use for:` bullets where missing, but stop before overwriting mature hand-written specialist prose.
4. **Residual manual queue** — leave dense expert skills, ambiguous duplicate-heading cases, and umbrella nodes without auto-discovered children for manual refinement instead of forcing a low-signal bulk rewrite.

This sequencing keeps the batch pass moving from safest structural wins toward narrower semantic edits, while preserving high-signal specialist content.

For a reusable checklist and verification counters, see `references/bulk-rehabilitation-playbook.md`.
