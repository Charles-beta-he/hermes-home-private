# Taskpool Pitfalls and Failure Modes

Extracted from `/Users/charles/.hermes/skills/software-development/taskpool-control-plane/SKILL.md` on 2026-07-01T08:21:01.947404+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Pitfalls

- **Frontmatter destruction**: `write_file` replaces the entire file. Always use `terminal` + `cat > ... << 'EOF'` heredoc when writing to task files. After writing, verify with `grep "^status:" <file>` that frontmatter survived.
- **Status field not updating**: If `sed -i '' 's/^status: running$/status: done/'` produces no output, the file was likely overwritten without frontmatter. Recreate the full file.
- **Version bumping**: Update `version.txt` before each commit to track progress.

### Verification after each task

```bash
# Confirm frontmatter survived
grep "^status:" <task-file>

# Confirm task pool updated
python3 ~/.hermes/scripts/brain_task_orchestrator.py dashboard 2>&1 | head -5

# Confirm git push succeeded
git log --oneline -3
```

## Pitfalls

- **GitHub repo name verification**: When the user provides a repo name verbally or from memory, the actual GitHub URL may differ in punctuation (dots vs hyphens, underscores, etc.). Always confirm the live repo URL before committing to navigation. Example: user said "architecture-of-internet-product" but the real repo was `architecture.of.internet-product`. Search GitHub or use the API to verify exact repo path before browser navigation.
- Do not add a vague "analyze repo X" task without checking the actual repo/doc shape.
- Advisory-only / certification-without-project-evidence review pitfall: `PASS_ADVISORY_ONLY` / multimodel discussion artifacts prove consultation, and `PASS/LOOP_DONE` proves design ratification, not product delivery. For work/product tasks lacking test/build/browser/curl/commit/project-verification evidence, write a review-gap artifact, requeue to `pending`, and let a project worker produce the proper closeout chain. Do not close or keep them stranded in `review`.
- Certification unblock pitfall: never resolve a failed multimodel certification by accepting a minority patch that relaxes the same certification gate. Classify self-relaxing threshold/gate patches as advisory governance work, bind `discussion_result.json` explicitly to the target task, keep lifecycle evidence structured, and rerun selfcheck/proof/lifecycle. See `references/certification-unblock-and-selfcheck-upgrade.md`.
- Dry-run spawnability is not enough. If `hermes kanban dispatch --dry-run --json` says a task can spawn but the real run dies immediately with `pid ... not alive`, inspect `hermes kanban log <task>` before blaming dispatch logic. A durable bootstrap failure is `Unknown skill(s): kanban-worker` caused by `~/.hermes/config.yaml` listing `kanban-worker` under `skills.disabled`; runtime skill loading respects the disable list even when the skill file exists. See `references/kanban-worker-disabled-bootstrap.md`.

- Brain task frontmatter `blocker_summary` may be outside the YAML frontmatter block (e.g., line 90+). Always `grep -n` the exact location before patching.
- `multimodel_last_failures` is a JSON array in YAML — don't try to patch it inline; read the full field first.
- Task kanban.db and brain markdown files are separate systems. Kanban status may already be "ready" while brain files still show "blocked". Always check both.
- Brain markdown `status: blocked` ≠ kanban.db status (DB shows "ready"). Patch brain files, not DB.
- `blocker_summary` may be outside YAML frontmatter (e.g., line 90+). Use `grep -n` before patching.
- Frontmatter `multimodel_last_failures` is a YAML list — contains structured failure reasons like `agreement_below_threshold:approach:0.65`
- `execute_code` file writes may not persist to disk. Use `patch` tool or `terminal` with `sed` for brain markdown edits.
- **`brain_task_orchestrator.py` subprocess timeout mismatch.** The `list --json` command scans all `.md` files in `~/Documents/brain/05-实践与项目/tasks/` (300+ files). On macOS with Xcode Python 3.9, this takes 60-90+ seconds. Any wrapper script (e.g., `kanban_bridge.py`, cron watchdogs) calling it must use `timeout≥120`. The default 30s timeout causes silent bridge/watchdog failures. **Zombie processes** of `brain_task_orchestrator.py` (especially `next --reconcile`) can accumulate and consume 7.5GB+ RAM. Before running any orchestrator-dependent script, check `ps aux | grep brain_task_orchestrator | grep -v grep` and kill stale processes. See `references/brain-orchestrator-subprocess-timeout.md`.
- **`write_file` destroys YAML frontmatter on task markdown files.** When writing evaluation reports or task body content, `write_file` replaces the ENTIRE file — including the YAML frontmatter block. This silently removes `status`, `priority`, `lane`, `multimodel_*`, `evidence_*`, and all other structured metadata, making the task invisible to the orchestrator and breaking lifecycle transitions. Observed twice in one session: both times the file had to be fully recreated with `terminal` + `cat > ... << 'EOF'` heredoc. **Safe alternatives**: (1) `patch` tool for targeted body edits that preserve frontmatter, (2) `terminal` + `sed` for status field changes, (3) `terminal` + `cat > ... << 'EOF'` when you must rewrite the entire file (include the full frontmatter block). After any task file write, always `grep "^status:"` the file to confirm frontmatter survived.

- `lane=work` tasks with a `project` but missing `source_weighting_policy_ref` are **silently non-dispatchable**. `is_dispatchable()` fails closed on this field. The symptom is `eligibility-check` returning `eligible=false` + `no_dispatchable_task` with no obvious error. Fix: add `source_weighting_policy_ref: ~/.hermes/project-profiles/<project>.json#source_weighting_policy` to the task frontmatter. This affects batch intake of Lark/imported tasks where the project was renamed (e.g. `uvisa-app-2.0` → `uvisa-app-2.0-work`) — both the project name AND the policy ref must be present and matching. See `references/project-profile-dispatchability-gates.md`.
- PRD extracts saved only to `/tmp/` will be lost on reboot/cleanup, making rank-1 product evidence unavailable when Lark tasks are later audited. Always persist PRD extracts under `~/.hermes/evidence/<project>/prd-extracts/` and reference the persisted path in `evidence_refs`. Closing a task as "product-verified" without a surviving PRD artifact is a false-positive closeout risk. See `references/prd-evidence-persistence.md`.
- Do not start with `brainctl.py dashboard` / `brainctl.py eligibility-check` unless live help shows those subcommands exist; on this setup they live under `brain_task_orchestrator.py`.
- When programmatically editing task markdown frontmatter, prefer `brain_task_orchestrator.py` helpers (`find_task`, mutate `task.fm`, `save_task`) or the CLI. Avoid dumping task notes with generic PyYAML: block-style lists and `null` scalars can make the orchestrator's yamlish parser lose `depends_on_task` or treat `claimed_by: null` / `run_id: null` as truthy strings, making tasks non-dispatchable. After edits, verify `work_dispatch_blockers`, dependency lists, and `is_dispatchable()`.
- `blocked-resolve-step` is a no-op when the blocker is infrastructure (missing API keys, quota expired). It only resolves analysis-quality blockers.
- `--force` does NOT bypass `multimodel_certification_required_before_done` gate. For evolution tasks blocked on infrastructure (quota, credentials), archive with `--to archived` instead of trying `--to done --force`. See `references/task-lifecycle-transition-chain.md` for the full chain of evidence requirements at each step.
- Skipping the `review` step and going directly from `running → done` always fails with `illegal lifecycle transition`. The required chain is `running → review` (with structured `--evidence`) → `done` (with project-verification evidence + multimodel certification). See `references/task-lifecycle-transition-chain.md`.
- Do not equate `proof-check FAIL` with `current task unsafe to claim` without checking why it failed.
- Do not let historical `done task missing evidence` automatically block the only dispatchable priority task.
- If `dispatchable=true` but `eligibility-check` says `autorun_disabled`, do not misdiagnose the stall as "no candidate task".
- Do not “fix” the symptom only by manual claim; always inspect and repair the tick/runner policy afterward.
- Do not collapse all non-PASS control-plane signals into one fatal bucket.
- **Never hardcode project-specific domain patterns in orchestrator/classifier code.** Domain groups, keyword mappings, and page-level classification rules belong in the project profile (`domain_aliases` / `fullstack_domain_map`), not in `brain_task_orchestrator.py` or `task_classifier.py`. New projects should only need to add config to their profile — zero code change. User correction (2026-05-30): "为什么是硬编码？寻找相关论点以及核心著作". See `references/tree-shaped-boundary-refinement.md` for the config-driven pattern.
