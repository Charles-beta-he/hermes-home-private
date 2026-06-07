# Post-session Skill Update Triage

Use this reference when the user asks to review a conversation and update the skill library.

## Principle

Treat post-session skill updates as class-level library maintenance, not as session journaling. Most non-trivial sessions should produce at least one small skill update, but the update should land in an existing umbrella skill whenever possible.

## Triage Order

1. Patch a skill loaded or consulted during the session if it governs the new lesson.
2. If no loaded skill fits, patch an existing umbrella skill rather than creating a narrow one-off skill.
3. Add a support file when the lesson is detailed, evidence-heavy, or session-specific; keep the root `SKILL.md` as the compact routing/control contract.
4. Create a new skill only when the lesson defines a reusable class of work not covered by the library.

## What to Capture

Capture:
- user workflow/style corrections that should shape this class of task next time;
- missing steps, pitfalls, verification gates, or tool-use sequence corrections;
- durable techniques, scripts, or reproducible debugging paths;
- gaps discovered in a loaded skill.

Do not capture:
- one-off task narratives;
- transient setup failures or missing binaries;
- negative claims that a tool or feature is broken;
- active task progress, PR numbers, commit SHAs, or other stale artifacts.

## Root vs Support File Split

Root `SKILL.md` should contain:
- trigger boundary;
- compact ordered procedure;
- pitfalls;
- verification / DOD;
- one-line pointers to support files.

`references/` should contain:
- session-specific evidence or transcripts;
- condensed external docs/research;
- detailed recipes that would bloat the root skill.

`templates/` should contain copy-and-modify starter artifacts.

`scripts/` should contain deterministic probes, scanners, generators, or validation helpers.

## Verification

Before reporting completion:
- read or patch the target skill, not just memory;
- ensure support file paths are linked from `SKILL.md`;
- avoid editing protected bundled/hub-installed skills;
- state exactly which skill and file changed, or say `Nothing to save.` only if no durable lesson exists.
