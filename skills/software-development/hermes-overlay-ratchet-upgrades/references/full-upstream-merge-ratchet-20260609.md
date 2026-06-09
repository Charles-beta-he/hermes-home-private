# Full upstream merge ratchet pattern — 2026-06-09

Concrete case: `private/main` merged `upstream/main` after many local commits and both-touched core files. Useful pattern for future Hermes private overlay upgrades.

## Durable lessons

1. Protect local state before any real merge.
   - Commit/protect untracked private evidence that should survive.
   - Create both a backup branch and a backup tag at the pre-merge private HEAD.
   - Push `private/main`, the backup branch, and the backup tag before resolving upstream conflicts.

2. When upstream performs an architectural extraction, prefer upstream as the base and replay overlay behavior into the new seam.
   - Example: upstream extracted turn post-loop logic to `agent/turn_finalizer.py`.
   - Private auto-relay helpers remained in `agent/conversation_loop.py`, but invocation moved into `finalize_turn(...)`.
   - Avoid preserving the old monolith just because it contains private behavior.

3. Resolve merge stages separately from text conflict markers.
   - A file can have no `<<<<<<<` markers and still be `UU` until staged.
   - After manual edits, run `git add` on resolved files, then re-check `git diff --name-only --diff-filter=U`.

4. Let post-update-check expose missed overlay seams.
   - In this case targeted tests passed initially, but post-update-check caught that `_run_conductor_intent_router` was not importable after accepting upstream refactor.
   - Restore default-off/fail-soft seam helpers when tests or governance depend on importability, even if runtime is disabled by default.

5. Use evidence-first local certification if external multi-model consult is unavailable.
   - If `consult_models.py` hangs or produces no artifact, do not block forever.
   - Continue with a written carry / absorb / retire table grounded in diff, conflict, tests, and post-update-check output.
   - Record that external multi-model output was unavailable rather than pretending it certified the result.

## Verification slice used

- `py_compile` for conflicted core files and touched tools.
- Auto-relay continuation tests.
- Conductor runtime tests.
- Delegate auto-relay inheritance tests.
- Memory provider / memory tool tests.
- CLI subcommands and update tests.
- Process registry tests.
- `post-update-check.py --fix` using the Hermes venv Python.
- CLI smoke: `python -m hermes_cli.main version`.

## Decision examples

- Carry + redesign: private auto-relay continuation into upstream `turn_finalizer` seam.
- Carry + adapt: kanban budget failure recording after auto-relay gate.
- Carry + combine: memory provider rollback plus upstream core-tool shadow guard.
- Carry: importable conductor intent router helper, default-off and fail-soft.
- Absorb upstream: modularized `hermes_cli/subcommands/*` instead of retaining old `hermes_cli/main.py` monolith drift.
