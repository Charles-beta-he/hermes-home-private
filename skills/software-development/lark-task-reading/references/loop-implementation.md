# Lark Task Reading Loop Implementation

Extracted from `/Users/charles/.hermes/skills/software-development/lark-task-reading/SKILL.md` on 2026-07-01T08:22:36.087987+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Loop implementation

When the user asks to "loop" Lark reading or to fuse patterns into the skill tree, use this loop:

0. **Audit first, then execute.** Before implementing any task, run `lark_task_reader.py --scope-mode prefer --summary` to get the full task list. Cross-reference each guid against git log, test files, and source code comments. Many tasks from previous sessions are already done. Classify each as DONE / PARTIAL / TODO. Only start implementing TODO or PARTIAL tasks. This prevents re-doing work and surfaces backend blockers early.

0b. **Classify before executing.** After reading a task, classify it as:
   - **Point fix**: isolated to one location, no similar patterns elsewhere
   - **Cross-cutting concern**: validation, security, error handling, data transforms, i18n → must be implemented as shared infrastructure (extend `validators.ts` / `utils.ts`), not point fixes
   - **Infrastructure task**: changes to shared utilities, project config, or build tooling
   - **Supplement / acceptance-gap task**: a later Lark task repeats or narrows a requirement that already appeared inside an earlier task. Match by page/module, key entities, and requirement phrase overlap. Treat this as `supplement_of:<original-task>` and default to targeted delta repair + regression/visual proof, not a new workflow-improvement task.

   Scan for existing shared infrastructure and duplicated patterns before implementing. The user explicitly requires this: "有些对于项目属于基础设施或者常规限制，不能因为任务只说了一个地方就只改这一个地方" (some things are infrastructure-level constraints that can't be fixed at just one location because the task only mentions one place).

   For supplement / acceptance-gap tasks, avoid the previous miss next time by atomizing the original task into checklist-style acceptance atoms before implementation. For each atom record: target surface, exact requirement, verification method, and evidence artifact. Do not close the original task until every atom is checked or explicitly marked blocked. Only create a workflow-improvement/evolution item if the supplement proves a repeated or structural gate failure such as long-task parsing truncation, missing UI evidence coverage, or recurring unchecked acceptance atoms.

1. **Inspect** both reference projects:
   - `lark_task_reader.py`
   - collector/comment/doc enrichment code
   - router project mapping and staged/fan-out routing
   - tests around scope filtering, comment extraction, doc links, and dry-run behavior
2. **Extract reusable patterns** into this skill or a linked reference. Do not copy secrets or transient task data.
3. **Patch the project code only if needed**; otherwise keep the improvement in the skill tree.
4. **Verify**:
   - skill frontmatter parses and description length is below Hermes limits
   - `python3 ~/.hermes/scripts/skill-steward.py --graph-check --json`
   - project tests/compile for any project code touched
5. **Commit scoped files only**. In a dirty `~/.hermes` repo, run:
   ```bash
   git diff --cached --stat
   git restore --staged .
   git add scripts/lark_task_reader.py scripts/test_lark_task_reader.py \
     skills/software-development/lark-task-reading/SKILL.md \
     skills/software-development/lark-task-reading/references/tasklist-scope-enrichment.md
   git status --short -- scripts/lark_task_reader.py scripts/test_lark_task_reader.py skills/software-development/lark-task-reading
   git commit -m "feat: add Hermes-native Lark task reader"
   ```
6. **Continue** if verification finds missing coverage or graph violations; stop only when the skill tree audit passes and the scoped commit is clean.
