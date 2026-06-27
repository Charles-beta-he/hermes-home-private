# yd-ai-wf + Stop Hook auto-review pattern

Source: user-provided screenshot `4f1922209c50cb29cc5e1afc8284753c.png` (2026-06). This reference distills transferable patterns for Hermes Agent self-optimization; do not assume the named upstream tools exist locally.

## Observed flow

1. Start workflow with `yd-ai-wf(projectDir, feature)`.
2. Init phase:
   - analyze project;
   - supplement `CLAUDE.md`;
   - supplement `rules/*.md`;
   - reference `AGENTS.md`;
   - maintain a `.claude/` working area.
3. Feature gate:
   - if no feature, return init-only;
   - if feature exists, continue to planning.
4. Plan phase:
   - create/read `requirements.md`, `design.md`, `tasks.md`;
   - parse tasks;
   - group by dependencies;
   - mark skipped items.
5. Execute phase:
   - run task groups in parallel;
   - route by domain to specialized agents: frontend, backend, database, or default;
   - keep role-to-surface mapping explicit.
6. Per-task completion:
   - run a code reviewer / codex review;
   - mark completed tasks in `tasks.md`.
7. P0 auto-fix loop:
   - detect P0/Critical;
   - if found, assign a fix-p0 agent;
   - fix only P0;
   - read rules + AGENTS.md;
   - test/self-check;
   - if fixed, continue; if not, record remaining blocker.
8. `AGENTS.md` self-learning:
   - deduplicate additions;
   - record P0 causes;
   - append follow-up task reading/checklist.
9. Collect summary:
   - results;
   - reviews;
   - p0Fixed;
   - blockers;
   - distinguish already-fixed P0 from non-P0/unfixed P0.

## Stop Hook gate

The screenshot shows a final safety gate around a `Stop` event:

1. Stop event triggers a short pixel hook (`claude-hook.js`, 5s).
2. Then a longer review hook (`codex-review-on-stop.js`, 900s).
3. The hook reads stdin + transcript.
4. If the run is not `/goal` or `yd-ai-wf`, it silently allows.
5. It selects the git worktree directory.
6. If there are no uncommitted changes, it allows.
7. If there are changes, it runs:
   - `codex review --json --wait --scope working-tree`
8. It writes review artifacts under `codex-review/review-*.md`.
9. It classifies outcome:
   - `ALLOW`: allow stop;
   - `BLOCK`: block and request fix;
   - `ERROR`: allow to avoid false blocking.

## Transferable Hermes improvements

- Add an exit/stop review gate for high-risk `/goal` work that is scoped to the current git worktree and dirty diff only.
- Use a fast pre-hook + longer bounded review hook pattern; avoid unbounded stop-time review.
- Fail open on review infrastructure error to avoid trapping the user, but record the error as evidence.
- Write review artifacts to a deterministic directory and link them from taskpool/mission receipts.
- Make P0/Critical auto-fix a separate loop with an exact target and evidence, not a generic “fix all”.
- Feed stable causes into `AGENTS.md`/skills only after deduplication and evidence, avoiding memory pollution.
- Summary must separate `results`, `reviews`, `p0Fixed`, and `blockers`.

## Hermes implementation boundary recommendation

Next safe Hermes slice:

1. Add a default-off config flag such as `goal.stop_review.enabled`.
2. Add a local dry-run stop-review command that consumes transcript + worktree path, detects dirty diff, and writes a review request packet without blocking.
3. Add tests for:
   - non-goal transcript => allow;
   - goal transcript + clean tree => allow;
   - dirty tree => writes review packet;
   - review error => allow + error receipt;
   - P0 finding => blocker packet.
4. Only after this packet layer is verified, wire it into actual stop/exit hooks.

## Pitfalls

- Do not run review on every stop; scope to `/goal` / workflow runs.
- Do not block stop on review infrastructure errors.
- Do not let worker/model output directly mutate lifecycle; P0 findings should become evidence-backed proposals first.
- Do not overwrite AGENTS.md blindly; dedupe and preserve user conventions.
