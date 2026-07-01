# Skill Library Coverage Audit

Extracted from `/Users/charles/.hermes/skills/software-development/agent-skill-design-patterns/SKILL.md` on 2026-07-01T08:55:33.664327+00:00 by generic core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

## Skill Library Coverage Audit

When the task is to inspect existing skills, coverage, or ecosystem health, prefer a non-mutating audit before any rewrite. If the user asks to “检查遗漏” after a bulk skill-library pass, treat it as an omission review, not as permission for another bulk rewrite.

1. Run the scanner instead of editing skills from intuition:

   ```bash
   python3 scripts/scan_skill_pattern_coverage.py \
     --skills-root ~/.hermes/skills \
     --out-dir ~/.hermes/docs/private/skill-pattern-coverage-$(date +%Y%m%d)
   ```

2. Treat the output as telemetry, not authority.
   - Heuristic `primary_pattern` labels are candidates until reviewed.
   - Section presence does not prove section quality.
   - Eval file presence does not prove runtime routing passed.
3. Separate active skills from archived skills before prioritizing fixes.
4. Fix concrete broken linked-file references before cosmetic reshaping.
5. Do not batch-edit `description` fields automatically; they are routing logic.
6. Do not batch-write heuristic `primary_pattern` metadata without owner review.
7. If the owner explicitly asks for full-library eval coverage, use the contract-layer generator before semantic rewrites:

   ```bash
   python3 scripts/generate_skill_routing_evals.py \
     --skills-root ~/.hermes/skills \
     --manifest ~/.hermes/docs/private/skill-routing-eval-coverage-$(date +%Y%m%d).json
   ```

   This creates canonical `evals/prompts.csv` files without changing `description` or SKILL.md body semantics. For the full workflow, including manifest verification, secret scan, scoped commit, and nested git/submodule handling, see `references/full-library-routing-eval-coverage.md`.
8. Prioritize pilot rehabilitation over full-library churn:
   - start with high-value Wrapper/Pipeline/Reviewer skills;
   - add `evals/prompts.csv` whenever changing a routing trigger;
   - read back the skill and support files before reporting completion.

### Omission review after a bulk pass

When checking for omissions after full-library eval or contract rehabilitation, verify more than the headline scanner counts:

- **Registry/name collisions**: detect duplicate frontmatter `name` values, especially alias/canonical pairs. Alias wrappers should not silently shadow the canonical skill in list/routing views.
- **Heading variants**: treat `## When to Use`, `## When to use`, and `## When to use this skill` as semantically equivalent when auditing coverage; do not report false gaps from case-sensitive heading checks.
- **Template linked references**: separate concrete broken paths from wildcard/template contracts such as references/<topic>.md, references/*.md, or references/{subcommand}.md. They are not broken refs, but they should be called out as P2 semantic debt unless the skill explicitly says they are patterns rather than literal files.
- **Boilerplate debt**: after script-assisted rehabilitation, search for stock phrases like “This skill is maintained as a ... shaped contract” and queue human semantic cleanup. Passing contract coverage does not prove the prose is natural or domain-rich.
- **Nested repo boundaries**: verify target nested skill repos directly, and do not claim recursive submodule verification if `git submodule status --recursive` is blocked by unrelated stale mappings or backup gitlinks.
- **Generated audit artifacts**: remove temporary omission-check reports unless the user asked to keep them; avoid adding untracked noise to an already dirty profile repository.
- **Post-commit closure gate**: after a scoped skill-library commit, verify the commit itself (`git show --check HEAD` or equivalent), re-run the coverage/frontmatter/eval/name/submodule checks, and run a scoped status against the touched paths. If unrelated historical dirty files remain, report them as unrelated rather than claiming the whole repository is clean.

Classify findings as:

- P0/P1: broken concrete refs, invalid frontmatter, missing eval matrix, high-risk side-effect skill without read-back.
- P2: duplicate names, template refs that could be misread as literals, alias/canonical routing ambiguity.
- P3: prose boilerplate, inconsistent heading style, cosmetic section naming.

Boundary: stop for human/owner decision before deleting, merging, archiving, changing descriptions, renaming alias skills, or bulk rewriting skill bodies. Adding missing canonical `evals/prompts.csv` files is allowed after explicit full-library coverage authorization because it adds regression coverage without changing routing semantics.
