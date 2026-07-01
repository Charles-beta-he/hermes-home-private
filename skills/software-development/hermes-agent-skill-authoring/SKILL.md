---
name: hermes-agent-skill-authoring
description: Use when creating, rehabilitating, or structurally improving Hermes SKILL.md files, including trigger design, frontmatter normalization, mode selection, and peer-shape validation.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - skills
    - authoring
    - hermes-agent
    - conventions
    - skill-md
    related_skills:
    - skill-eval
    - workflow-ecosystem-audit
    - writing-plans
---

# Authoring Hermes-Agent Skills (in-repo)

## Overview

There are two places a SKILL.md can live:

1. **User-local:** `~/.hermes/skills/<maybe-category>/<name>/SKILL.md` — personal, not shared. Created via `skill_manage(action='create')`.
2. **In-repo (this skill is about this case):** `/home/bb/hermes-agent/skills/<category>/<name>/SKILL.md` — committed, shipped with the package. Use `write_file` + `git add`. `skill_manage(action='create')` does NOT target this tree.

## When to Use

- User asks you to add a skill "in this branch / repo / commit"
- User asks whether an existing self-created skill is bloated, unstable, duplicate, poorly triggered, or structurally weak
- You need to rehabilitate a user-local skill under `~/.hermes/skills/` by tightening triggers, refactoring sections, splitting references/templates, or clarifying verification
- You're committing a reusable workflow that should ship with hermes-agent
- You're editing an existing skill under `/home/bb/hermes-agent/skills/` (use `patch` for small edits, `write_file` for rewrites; `skill_manage` still works for patch on in-repo skills, but not for `create`)

## Creation Gate Before Writing

Before creating a new skill or materially changing an existing one, apply the local creation-gate checklist at `/Users/charles/Documents/brain/05-实践与项目/projects/agent-skill-learning/skill-authoring-creation-gates-2026-05-13.md`:

1. Need / anti-proliferation: patch an existing umbrella skill + reference unless a new reusable trigger class is justified.
2. Shape: frontmatter, description length, non-empty body, peer-shaped sections.
3. Trigger evals: at least 3 positive prompts and 2 negative prompts.
4. Deterministic/read-back verification: `skill_view` main + linked files and artifact checks.
5. Graph/steward: run graph-check when routing/edges changed.
6. Closeout: commit tracked skill edits and report exact paths/commands.

## Required Frontmatter

Source of truth: `tools/skill_manager_tool.py::_validate_frontmatter`. Hard requirements:

- Starts with `---` as the first bytes (no leading blank line).
- Closes with `\n---\n` before the body.
- Parses as a YAML mapping.
- `name` field present.
- `description` field present, ≤ **1024 chars** (`MAX_DESCRIPTION_LENGTH`).
- Non-empty body after the closing `---`.

Peer-matched shape used by every skill under `skills/software-development/`:

```yaml
---
name: my-skill-name               # lowercase, hyphens, ≤64 chars (MAX_NAME_LENGTH)
description: Use when <trigger>. <one-line behavior>.
# Include when your library/router uses them as part of the entry contract:
# level: advanced
# requires: [other-skill]
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [short, descriptive, tags]
    related_skills: [other-skill, another-skill]
---
```

`version` / `author` / `license` / `metadata` are NOT enforced by the validator, but every peer has them — omit and your skill sticks out. Likewise, `level` and `requires` are ecosystem-shape fields rather than validator-mandated fields: preserve them whenever the target library uses them as part of routing or prerequisite declaration.

## Size Limits

- Description: ≤ 1024 chars (enforced).
- Full SKILL.md: ≤ 100,000 chars (enforced as `MAX_SKILL_CONTENT_CHARS`, ~36k tokens).
- Peer skills in `software-development/` sit at **8-14k chars**. Aim for that range. If you're pushing past 20k, split the long material into concrete files under `references/` and reference those files from SKILL.md.

## Peer-Matched Structure

See also `references/skill-mode-patterns.md` for a compact mode-selection reference and the shared frontmatter contract, and `references/perplexity-skill-lessons.md` for a concise external rubric on context budgets, trigger-writing, and gotcha-first maintenance.

Every in-repo skill follows roughly:

```
# <Title>

## Overview
One or two paragraphs: what and why.

## When to Use
- Bulleted triggers
- "Don't use for:" counter-triggers

## <Topic sections specific to the skill>
- Quick-reference tables are common
- Code blocks with exact commands
- Hermes-specific recipes (tests via scripts/run_tests.sh, ui-tui paths, etc.)

## Common Pitfalls

Numbered list of mistakes and their fixes.
1. Skipping prerequisite checks and assuming the environment already matches the workflow.
2. Applying the workflow mechanically without confirming that the request still matches this skill's trigger class.
3. Reporting success before reading back the actual outputs, files, or external side-effects.
## Verification Checklist

- [ ] Checkbox list of post-action verifications
- [ ] Preconditions, scope, and tool availability were checked before following this workflow.
- [ ] The key output artifacts, commands, or side-effects were verified by read-back or direct inspection.
## One-Shot Recipes (optional)
Named scenarios → concrete command sequences.
```

Not every section is mandatory, but `Overview` + `When to Use` + actionable body + pitfalls are the minimum for the skill to feel like a peer.

## SKILL.md as an Entry Contract: 5 Internal Control-Flow Modes

Detailed `SKILL.md as an Entry Contract: 5 Internal Control-Flow Modes` guidance moved to `references/skillmd-as-an-entry-contract-5-internal-control-flow-modes.md`.

Load it when this subproblem is directly active. Minimum in-root rule: preserve the current skill's safety/verification boundaries and read the reference before executing this specialized branch.
## Rehabilitating Existing Self-Created Skills

Detailed `Rehabilitating Existing Self-Created Skills` guidance moved to `references/rehabilitating-existing-self-created-skills.md`.

Load it when this subproblem is directly active. Minimum in-root rule: preserve the current skill's safety/verification boundaries and read the reference before executing this specialized branch.
## Directory Placement

```
skills/<category>/<skill-name>/SKILL.md
```

Categories currently in repo (confirm with `ls skills/`): `autonomous-ai-agents`, `creative`, `data-science`, `devops`, `dogfood`, `email`, `gaming`, `github`, `leisure`, `mcp`, `media`, `mlops/*`, `note-taking`, `productivity`, `red-teaming`, `research`, `smart-home`, `social-media`, `software-development`.

Pick the closest existing category. Don't invent new top-level categories casually.

## Workflow

1. **Survey peers** in the target category:
   ```
   ls skills/<category>/
   ```
   Read 2-3 peer SKILL.md files to match tone and structure.
2. **Check validator constraints** in `tools/skill_manager_tool.py` if unsure.
3. **Draft** with `write_file` to `skills/<category>/<name>/SKILL.md`.
4. **Validate locally**:
   ```python
   import yaml, re, pathlib
   content = pathlib.Path("skills/<category>/<name>/SKILL.md").read_text()
   assert content.startswith("---")
   m = re.search(r'\n---\s*\n', content[3:])
   fm = yaml.safe_load(content[3:m.start()+3])
   assert "name" in fm and "description" in fm
   assert len(fm["description"]) <= 1024
   assert len(content) <= 100_000
   ```
5. **Git add + commit** on the active branch.
6. **Note:** the CURRENT session's skill loader is cached — `skill_view` / `skills_list` will not see the new skill until a new session. This is expected, not a bug.

## Cross-Referencing Other Skills

`metadata.hermes.related_skills` unions both trees (`skills/` in-repo and `~/.hermes/skills/`) at load time. You CAN reference a user-local skill from an in-repo skill, but it won't resolve for other users who clone the repo fresh. Prefer referencing only in-repo skills from in-repo skills. If a frequently-referenced skill lives only in `~/.hermes/skills/`, consider promoting it to the repo.

## Editing Existing In-Repo Skills

- **Small fix (typo, added pitfall, tightened trigger):** `skill_manage(action='patch', name=..., old_string=..., new_string=...)` works fine on in-repo skills.
- **Major rewrite:** `write_file` the whole SKILL.md. `skill_manage(action='edit')` also works but requires supplying the full new content.
- **Adding supporting files:** `write_file` to a concrete file under the skill's `references/`, `templates/`, or `scripts/` directory. `skill_manage(action='write_file')` also works and enforces the references/templates/scripts/assets subdir allowlist.
- **Always commit** the edit — in-repo skills are source, not runtime state.

## Common Pitfalls

1. **Using `skill_manage(action='create')` for an in-repo skill.** It writes to `~/.hermes/skills/`, not the repo tree. Use `write_file` for in-repo creation.

2. **Leading whitespace before `---`.** The validator checks `content.startswith("---")`; any leading blank line or BOM fails validation.

3. **Unquoted YAML descriptions with colons.** If `description:` contains a colon (for example `patterns: scoped task prioritization`) or other YAML-significant punctuation, quote the whole value. Validate with `yaml.safe_load` before committing; otherwise the skill may look fine in Markdown but fail frontmatter parsing.

4. **Description too generic.** Peer descriptions start with "Use when ..." and describe the *trigger class*, not the one task. "Use when debugging X" > "Debug X".

4. **Forgetting the author/license/metadata block.** Not validator-enforced, but every peer has it; omitting makes the skill look half-finished.

5. **Writing a skill that duplicates a peer.** Before creating, `ls skills/<category>/` and open 2-3 peers. Prefer extending an existing skill to creating a narrow sibling.

6. **Expecting the current session to see the new skill.** It won't. The skill loader is initialized at session start. Verify in a fresh session or via `skill_view` using the exact path.

7. **Linking to skills that don't exist in-repo.** `related_skills: [some-user-local-skill]` works for you but breaks for other clones. Prefer only in-repo links.

## Verification Checklist

- [ ] File is at `skills/<category>/<name>/SKILL.md` (not in `~/.hermes/skills/`)
- [ ] Frontmatter starts at byte 0 with `---`, closes with `\n---\n`
- [ ] `name`, `description`, `version`, `author`, `license`, `metadata.hermes.{tags, related_skills}` all present
- [ ] Name ≤ 64 chars, lowercase + hyphens
- [ ] Description ≤ 1024 chars and starts with "Use when ..."
- [ ] Total file ≤ 100,000 chars (aim for 8-15k)
- [ ] Structure: `# Title` → `## Overview` → `## When to Use` → body → `## Common Pitfalls` → `## Verification Checklist`
- [ ] `related_skills` references resolve in-repo (or are explicitly OK to be user-local)
- [ ] `git add skills/<category>/<name>/ && git commit` completed on the intended branch

## Routing-Surface Governance and Progressive Loading

Treat skill quality as a routing-and-loading problem, not just a writing problem.

### Description changes are routing changes

If you change `description`, you changed the index-layer routing surface. Do not treat this as a cosmetic edit.

Required follow-through after a description edit:
- Re-run trigger evals with the old and new description against the same prompt set
- Check for **neighbor-load regressions**: prompts that should still match a nearby skill, not this one
- Check for **forbidden/off-target loads**: prompts that should load no skill or a different class entirely
- Record whether the edit narrowed, widened, or merely clarified the trigger boundary

### Define the negative space explicitly

Every skill should name not only what it is for, but what it must *not* steal.

For each skill, maintain at least these buckets while authoring:
- **Positive loads** — prompts that should clearly load this skill
- **Neighbor loads** — prompts that belong to an adjacent skill and must stay there
- **Forbidden loads** — prompts that should not load this skill even if they share vocabulary
- **No-load prompts** — prompts that should remain general reasoning with no skill activation

This negative-space list is the fastest way to catch over-broad descriptions and umbrella skills that eat the graph.

### Accessory files need an explicit load contract

If a skill ships linked files under `references/`, `templates/`, `scripts/`, or `assets/`, declare why each one exists and when it should be read.

Document per file:
- what question or task state unlocks it
- whether it is always-read, conditionally-read, or rarely-read
- the cost of loading it late vs early
- what goes wrong if the agent reads it unnecessarily

Good accessory files reduce context cost. Unscoped accessory files become hidden prompt bloat.

### Progressive loading by graph layer

Use progressive disclosure deliberately:
1. **Index layer** — `name` + `description` decide whether the skill should load at all
2. **Core layer** — SKILL.md body gives the default working procedure
3. **Accessory layer** — linked files load only when the current subproblem actually needs them

Author the graph so most requests stop at layer 1 or layer 2. If routine usage always requires a linked file, move that content up into the core layer or split the skill.

### Append-mostly gotcha maintenance

Skills often decay by endless appends: more caveats, more examples, more edge cases, but no re-organization.

Use this maintenance rule:
- Append for fresh evidence only when the current structure still routes cleanly
- Refactor when new caveats start changing trigger boundaries, load order, or default execution
- If a gotcha can only be understood with a long exception chain, rewrite the section instead of appending again
- Periodically compress repeated caveats into a smaller canonical rule plus one or two examples

### Minimum read-back before you call a skill "improved"

After an authoring pass, read the skill back as a graph artifact and answer:
- What causes this skill to load?
- What nearby prompts should *not* load it?
- Which linked files are safe to defer?
- Did the latest edits increase surface area without increasing clarity?
- Would a different model likely route this the same way from `description` alone?
