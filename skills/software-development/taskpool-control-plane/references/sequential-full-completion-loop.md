# Sequential Full-Completion Loop

Extracted from `/Users/charles/.hermes/skills/software-development/taskpool-control-plane/SKILL.md` on 2026-07-01T08:22:36.087987+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Sequential full-completion loop (batch processing)

When the user says "全盘推进" and the tasks are evaluation/research items that can each be completed in a single session, use a sequential full-completion loop instead of the bounded single-tranche pattern above.

### Pattern

For each task in priority order:
1. `claim` the task
2. `transition --to running --reason "开始执行评估"`
3. Clone/inspect the external repo or resource
4. Analyze architecture, features, and gaps
5. Write the evaluation report **inside** the task file (use `terminal` + `cat > ... << 'EOF'` to preserve frontmatter — never `write_file` which destroys YAML)
6. Transition status to `done` via `sed` on the task file
7. Create a summary document in the edge-worker repo
8. `git commit + push` to GitHub with version bump
9. Move to next task

### Pitfalls

Detailed taskpool pitfalls and failure modes were moved to `references/pitfalls-and-failure-modes.md`.

Load it when diagnosing repeated closeout failures, false progress, stale claims, proof-shape mismatch, multimodel advisory loops, or parent/child reconciliation drift.

Minimum in-root rule: do not force-close or claim pool health from a dashboard alone; bind every lifecycle claim to fresh command/artifact/readback evidence.
