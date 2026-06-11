# Product Workflow OS Landing and Commit Pitfalls

Scope: reusable landing details for product-workflow skill/workspace changes. Applicability: use when creating or committing workflow templates, scaffold scripts, or durable workflow workspaces. Anti-condition: do not treat these as general Git rules for unrelated repos; they are Hermes-local packaging gotchas.

## Lessons from the first full landing

1. **Abstraction-governance gate for global skills**
   - Global/class-level `SKILL.md` files must include explicit scope, applicability, and anti-condition text when they are derived from a concrete source review.
   - Keep source-specific facts in a scoped reference note or project/workflow SSOT, not in the global skill body.
   - If the gate blocks a write as `context_coupled_skill`, strip proper nouns/counts/session facts from the root skill or move them to `references/`.

2. **Secret scanner wording in templates/workspaces**
   - Avoid template labels such as `Credentials/secrets needed` in staged artifacts, even when the value is `no` or a placeholder.
   - Prefer neutral wording like `Private access material needed`.
   - The issue is scanner hygiene, not capability: do not save “secret scanner is broken”; save the wording pattern.

3. **Ignored `tasks/` directories**
   - Hermes' local `.gitignore` may ignore directories named `tasks/` globally.
   - If a workflow workspace intentionally includes `tasks/task-candidates.json` and that artifact must be committed, use `git add -f <path>/tasks/task-candidates.json` and verify it appears in the commit.
   - Alternatively, for future workspace designs that must be tracked by default, consider naming the directory `task-candidates/` or `backlog/` instead of `tasks/`.

4. **Verification sequence before reporting done**
   - Read the skill back with `skill_view`.
   - Validate JSON templates and generated workspace JSON.
   - Run `py_compile` on helper scripts.
   - Run the scaffold script in `--dry-run` and real smoke mode.
   - Check staged files and commit only scoped changes.

## Minimal closeout checklist

- [ ] Root skill contains scope/applicability/anti-condition.
- [ ] Source-specific review facts live in a scoped reference/SSOT note.
- [ ] Template wording avoids secret-like scanner triggers.
- [ ] Ignored workspace artifacts are either force-added intentionally or deliberately left untracked.
- [ ] Verification command output is captured before final reporting.
