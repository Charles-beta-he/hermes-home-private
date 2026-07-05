# Dynamic Self-Check Coverage Control Plane

Scoped architecture readback for the July 2026 Hermes dynamic self-check slice.

## Scope

Local-first dynamic coverage control plane for Hermes self-check:
- discover user-system profile;
- build coverage registry;
- map events to coverage plans;
- generate workflow proposals;
- cluster cron errors;
- snapshot provider health;
- emit local repair packets;
- diagnose delivery/proxy failures without sending;
- maintain per-gap lifecycle ledger.

## Boundaries

Allowed in this slice:
- local reads;
- local artifact writes under `~/.hermes/state/selfcheck/`;
- local-only no-agent cron tick;
- success-silent operation;
- scoped skill/docs updates.

Not allowed by this slice:
- external delivery/resend;
- GitHub issue writes;
- provider/proxy credential changes;
- destructive cleanup;
- deploy/publish beyond the explicitly authorized scoped git push.

## Evidence labels

design_doc: This architecture note, `docs/private/dynamic-selfcheck-coverage-architecture-20260706.md`, and `skills/autonomous-ai-agents/hermes-agent/references/dynamic-selfcheck-coverage-control-plane.md` define the scoped design, lifecycle states, local-only execution gate, and rollback boundary for the dynamic self-check coverage control plane.

gate_readback: Local verification readback: `python3 -m pytest scripts/tests/test_dynamic_selfcheck_coverage.py -q` returned 11 passed; `python3 -m py_compile scripts/dynamic_selfcheck_coverage.py` returned exit 0; cron job `29d9eaa6bf48` read back `last_status=ok`, `deliver=local`, `no_agent=true`; `coverage_lifecycle.json` read back active=5, resolved=0, retired=0.

## Rollback

- Remove/pause cron job `29d9eaa6bf48` if needed.
- Revert the scoped git commit that adds `dynamic_selfcheck_coverage.py`, its tests, wrapper, and docs.
- Delete local runtime artifacts under `~/.hermes/state/selfcheck/` only after separate destructive cleanup authorization.
