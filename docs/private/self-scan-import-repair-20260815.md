# Self-scan immutable-runtime import repair — 2026-08-15

## Objective / success criteria
Restore the scheduled 4-hour self-scan and dashboard refresh when they run under the immutable Hermes release Python with `cwd=~/.hermes/scripts`; preserve evidence-gated `UNKNOWN` health semantics; verify the exact failing invocation, focused tests, scanner output, ledger append, and dashboard read-back.

## Scope and boundaries
- In scope: `scripts/self-scan-4h.py`, `scripts/refresh-dashboard.py`, focused regression coverage, derived self-scan/dashboard artifacts.
- Non-goals: manufacturing numeric V/Vdot, changing health weights, auto-fixing unrelated diagnostics/cron/log/Kanban findings, updating Hermes, external delivery, or broad cleanup of the dirty `~/.hermes` worktree.

## Source facts
- Failing interpreter: `~/.hermes/releases/hermes-agent/efde1f55f0881e467adbe80082cbfdcc10bfc44f/.venv/bin/python`.
- Failing condition: executing either script from `cwd=~/.hermes/scripts` raises `ModuleNotFoundError: top-level import 'hermes_evolution_store' is unavailable outside the working directory` from release `sitecustomize.py`.
- Control: the same release interpreter succeeds when cwd is `/Users/charles`, proving cwd-sensitive immutable import policy rather than a missing module; `scripts/hermes_evolution_store.py` exists.
- Current health warning is independent: latest strict health record has `V=null`, `V_dot=null`, `measurement_status=insufficient_evidence`, `observed_weight=0`.

## Chosen path and risks
Load the sibling evolution-store module by explicit file location in the two entrypoint scripts, bypassing cwd-sensitive top-level discovery without weakening immutable-runtime policy globally. Risk is limited to duplicated bootstrap code; verify imports, direct entrypoint runs, nullable-health tests, core-script compilation, and dashboard read-back.

## Verification evidence
- Pre-fix reproduction: both entrypoints exited 1 under release Python + `cwd=~/.hermes/scripts`, with the immutable `sitecustomize.py` top-level-import error.
- Post-fix focused regression: `test_self_scan_schema_drift.py` passed 3/3 under the exact release interpreter/cwd.
- Store regression: active Hermes worktree venv ran `test_hermes_evolution_store.py` with 9/9 passing.
- Compile gate: both changed entrypoints, the evolution store, and all three core scripts compiled successfully under the release interpreter.
- Exact post-fix entrypoints: self-scan and dashboard refresh both exited 0 under the formerly failing interpreter/cwd.
- Latest scan at `2026-08-15 02:14:17`: one issue only, `V̇ 最新不可用 (insufficient_evidence)`.
- Dashboard read-back at `2026-08-15T02:14:17.608726`: `DEGRADED`, V/Vdot `UNKNOWN`, 40/40 skills evaluated, S=3/A=9/B=28/C=0/D=0.
- Claim boundary: the import incident is repaired; telemetry availability is not repaired. No numeric health value was manufactured.
