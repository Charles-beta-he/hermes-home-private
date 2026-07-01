# Taskpool Root Reference Index

Extracted from `/Users/charles/.hermes/skills/software-development/taskpool-control-plane/SKILL.md` on 2026-07-01T08:24:04.829872+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## References

References:
- `references/blocked-task-resolution.md` — How to resolve blocked tasks (dual state store, subtask execution, parent unblocking)
- `references/evolution-lane-certification-loop.md` — Root cause analysis of the CONTINUE_LOOP deadloop pattern and prevention mechanisms
- `references/child-closeout-vs-parent-ratification.md` — When all narrowed child subtasks are closed out but the parent still stays blocked because the parent-level multimodel certification artifact was never refreshed.
- `references/no-running-allowlist-vs-blocked-evolution.md` — Diagnose the specific stall where a blocked evolution P1 leaves only advisory dispatchables, but autorun still fail-closes on lane policy / allowlist mismatch (`allowlist_miss`).
- `references/lark-batch-import-dedup.md` — GUID-based deduplication for Lark batch import duplicates; detection via `lark_task_guid`, cleanup priority order, and prevention.
- `references/task-lifecycle-transition-chain.md` — Exact evidence requirements for each lifecycle step (`claimed → running → review → done`), common error messages and solutions, and bypass strategies when orchestrator gates block completion.

## Finished children do not equal a reopened parent

Detailed parent re-open/reconciliation guidance was moved to `references/finished-children-not-reopened-parent.md`.

Load it after child closeout when a parent still has no dispatchable next step or remains blocked.

Minimum in-root rule: verify with `next --json`; don't report dispatchability from child notes alone.

## Blocked-Task Resolution Workflow

For the full blocked-task resolution procedure, load `references/blocked-task-resolution-workflow.md`. Use it when one or more brain markdown tasks are `status: blocked` and you need the diagnostic commands, subtask checks, parent-field repair pattern, kanban-vs-brain readback, and dashboard regeneration steps.

Anti-condition: do not directly patch blocked tasks to ready/certified without evidence that the blocker was resolved and the relevant child/subtask or certification state was read back.

## Evolution Lane Certification Loop Prevention

Detailed evolution-lane certification loop prevention moved to `references/evolution-lane-cert-loop-prevention.md`.

Load it for `loop_non_convergence` / `CONTINUE_LOOP` deadlocks in exploratory evolution tasks.

Minimum in-root rule: disagreement on framing in evolution work is often expected; use thresholds/subtasks/ratify-with-reservations rather than infinite retry loops.

## Taskpool Cleanup & Deduplication

When the pool accumulates duplicates (same title from repeated ingest):
1. Deduplicate first: `DELETE FROM tasks WHERE id IN (...)` — keep most recent per title
2. Then archive stale/low-value: convergence subtasks (细化) whose parents are unblocked, outdated research tasks, already-internalized designs
3. Regenerate dashboard: `python3 scripts/brain_task_orchestrator.py dashboard --write`

Typical cleanup ratio: 86 raw → 38 clean (dedup 32 + archive 16).

For **Lark batch import duplicates**, the canonical dedup key is `lark_task_guid` (not title slug). See `references/lark-batch-import-dedup.md` for detection, cleanup priority (keep review > claimed > pending), and prevention patterns.

### Brain mirror dedup on repeated triggers

The brain mirror script (`brain_task_orchestrator.py mirror-to-kanban`) can create duplicate brain task files when triggered multiple times for the same source task (e.g., multiple cron ticks, manual re-runs). The file naming scheme uses task title slugs without a hash-based dedup key, so repeated mirrors produce numbered copies (`-2`, `-3`, etc.). For Lark tasks specifically, the canonical dedup key is `lark_task_guid` — see `references/lark-batch-import-dedup.md`.

**Detection:**
```bash
# Find duplicate task files by title pattern
ls ~/Documents/brain/05-实践与项目/tasks/ | grep -E "review-claude-code|test-task-delete"
```

**Cleanup:** Keep only the largest (most content) file for each logical task; archive or remove the numbered duplicates.

**Prevention:** The mirror script should check for existing files with matching normalized title before creating new ones. When enriching existing notes (adding Lark metadata, comments), update in-place rather than creating a new file.

### YAML frontmatter escaping explosion

Task files can bloat from ~10KB to 7-60MB when `evidence_bundle` or similar YAML fields contain deeply nested backslash-escaped URLs. The escaping compounds through YAML serialization layers, producing exponential growth of `\` characters.

**Detection:**
```bash
# Find suspiciously large task files
find ~/Documents/brain/05-实践与项目/tasks -name "*.md" -size +100k | xargs ls -lh
```

**Root cause:** `evidence_bundle` field stores URLs like `https://example.com/path` but YAML serialization adds `\\` for each `\`, then another layer adds `\\\\`, etc. After 3-4 layers of escaping, a 50-char URL becomes several KB of backslashes.

**Fix:** Sanitize `evidence_bundle` before writing to YAML: strip excess escaping, or store URLs as a YAML list of plain strings instead of a single escaped blob. Use `yaml.safe_load` to verify the field roundtrips correctly.

### Kanban worker crash loops from missing credentials

When a kanban worker is assigned a task that requires external CLI credentials (e.g., Codex CLI, `hermes auth`), but those credentials are not configured, the worker enters an infinite crash-retry loop (87+ consecutive crashes observed). The crash log shows `No Codex credentials stored` repeating.

**Detection:**
```bash
hermes kanban log t_XXXXXXXX | tail -20
# Look for repeated "No credentials" / "not alive" patterns
```

**Fix:** Run `hermes auth` to configure the required credentials. If the task doesn't actually need that CLI, reassign or change the worker configuration.

**Do NOT** auto-enable expensive external-model autorun just to clear a crash loop. Report the blocker and wait for explicit authorization.

## Blocked Task Resolution Workflow

When evolution lane tasks are blocked by `loop_non_convergence`:
1. Check subtask completion: grep `auto_subtask_children` in task frontmatter, verify each child file has `status: done`
2. Execute pending subtasks: produce narrowed briefs grounded in actual code analysis, mark done
3. Unblock parents via patch: `status: blocked → ready`, clear `blocker_summary`, update multimodel gate fields
4. Regenerate dashboard

Brain task files use YAML frontmatter — patch individual fields with exact string matches. Key fields: `status`, `blocker_summary`, `multimodel_last_gate_status`, `multimodel_last_decision`, `multimodel_round_status`, `multimodel_status`.

## Sequential full-completion loop (batch processing)

The detailed sequential full-completion/batch-processing workflow was moved to `references/sequential-full-completion-loop.md`.

Load it when the user explicitly asks to drain a sequence of tasks through verification and lifecycle updates.

Minimum in-root rule: process each item through fresh evidence, frontmatter readback, pool update, and scoped external/push boundary checks; do not batch-force lifecycle states.

## Verification

Detailed taskpool post-fix verification checks moved to `references/verification-checks.md`.

Load it after fixes or manual interventions to verify dispatchability, tick payloads, governance visibility, blocked resolver, next/reconcile behavior, and pause-gated multimodel tasks.

Minimum in-root rule: verify live CLI/readback after every lifecycle or control-plane intervention.

## References

- `references/blocked-ratification-certification.md` — safe sequence for blocked parent tasks with `multimodel_status: not_certified`: freeze original objective, dry-run blocked-resolve, diagnose certification gaps, split convergence subtasks, and claim only dispatchable children without changing the parent goal.
- `references/manual-targeted-evidence-refresh.md` — parent-level targeted-evidence refresh pattern: run a fresh manual discussion, write the new FAIL/PASS artifact back into the parent, then verify whether a new dispatchable convergence child appears.
- `references/operational-cron-watchdogs.md` — Pattern for no_agent cron watchdog scripts: task pool health monitoring, notification dedup, hook registry integration, budget triage decision matrix, auth-blocked categorization.

- `references/blocked-task-diagnosis.md`: diagnose dashboards with no in-progress work, all-active-tasks-blocked states, `task_not_dispatchable`, multi-model certification blockers, and child-axis/proof-check failures.
- `references/proof-debt-migration.md` — how to migrate historical body proof into structured `evidence:` entries and normalize ad-hoc multimodel status lines so `proof-check`/`evidence-spine` return PASS again.
- `references/blocked-resolver-missing-artifact.md` — runtime case where blocked-resolve taxonomy tried to read a pruned `tick-*/discussion_result.json` and froze dispatch until downgraded to a warning.
- `references/dispatch-gate-triage.md` — triage flow for taskpool stalls where historical evidence debt is already softened but `next`/`eligibility-check` still block on reconcile or apparent allowlist misses.
- `references/dispatch-tick-soft-governance-gating.md` — distinguishes historical proof/evidence debt from live eligibility gates (`allowlist_miss`, `reconcile_required`) when tick is OK but no task is claimed.
- `references/taskpool-dispatch-soft-governance-gating.md` — how to distinguish historical proof/evidence debt from safety-critical dispatch blockers; includes the runtime-only pitfall where `unstructured evidence in ...` still trips dispatch tick.
- `references/fail-safe-claim-vs-governance-warnings.md` — policy note on separating anti-idle claim behavior from historical proof/evidence debt.
- `references/stale-claim-and-finished-subtasks.md` — stale-claim recovery pattern plus the interpretation that blocked parents may already have completed convergence subtasks and now need parent-level evidence reintegration rather than more decomposition.
- `references/auto-subtask-backfill-paused.md` — how to backfill finished child evidence into blocked parents while keeping pause-gated multimodel tasks blocked and non-dispatchable.
- `references/envelope-bus-escape-triage.md` — agent team controller / envelope bus escape mechanism: thresholds, ack watermark, post-ack failure tracing, proof gate error types, and re-enable procedure.
- `references/envelope-bus-escape-triage-cli-patterns.md` — direct sqlite3 CLI queries for envelope bus diagnosis: schema discovery, status distribution, post-ack failure tracing, project-level failure clustering, and the `missing_proof` project-clustering diagnostic signal.
- `references/project-profile-dispatchability-gates.md` — Silent fail-closed gate when `lane=work` tasks are missing `source_weighting_policy_ref`; diagnosis, batch fix, and project rename cascade checklist.
- `references/candidate-governance-to-bounded-slice.md` — How to collapse many proposed human-gate import candidates into consolidated terminal decisions plus one bounded executable slice, preserving runtime/model/write/external-side-effect gates and handling partial transition timeouts idempotently.
- `references/brain-kanban-dual-store-desync.md` — Brain markdown files and kanban.db are independent stores; cleaning one does NOT clean the other. Covers bulk cleanup procedure, kanban.db corruption recovery (dump → fix → recreate), and the rule that brain/kanban status must always be checked in both stores.
- `references/prd-evidence-persistence.md` — Lark PRD extracts in `/tmp/` are ephemeral; persist under `~/.hermes/evidence/<project>/prd-extracts/` at extraction time. Covers detection of missing PRD during audit, evidence authority enforcement, and the 0220b40e wealth-buy routing case study.
