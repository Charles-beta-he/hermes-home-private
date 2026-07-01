# Task Adapter Framework Pointer

Extracted from `/Users/charles/.hermes/skills/software-development/taskpool-control-plane/SKILL.md` on 2026-07-01T08:24:04.829872+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Task Adapter Framework (pluggable source pattern)

When the taskpool needs to ingest tasks from multiple distinct sources (Lark, brain notes, direct input, GitHub, etc.), use the pluggable TaskAdapter framework. See `references/task-adapter-framework.md`: it covers the TaskAdapter interface (fetch/enrich/classify/preflight/gates/complete), TaskRegistry, TaskPipeline, source-agnostic observer dict pattern, composite tasks (subtasks/parallelism/convergence), parallel execution, adversarial verification, checkpoint/resume, and the pitfalls around observer.observe() signature and gate checking behavior.

When extending Control Tower or any ledger/control-plane path from projection into real adapter mutation, load `references/event-governed-agent-write-through-boundaries.md` first for the staged authorization chain and executor progression. For adapter-specific closeout/rollback implementation, also load `references/digest-bound-closeout-and-rollback-executors.md`. For taskpool brain-note mutation specifically, also load `references/taskpool-external-write-through.md`: keep the slice explicitly adapter/operation allowlisted, consume exact command digests, recheck evidence/authorization freshness before mutation, mutate only frontmatter status plus an audit marker, and test both final-file symlink and ancestor-directory symlink escapes.
