# Meituan Travel Skill Eval Baseline

Date: 2026-07-13
Scope: user-local macOS personal travel/local-life provider adapter.

## Routing boundary

- Positive: explicit Meituan/Token use, provider field verification, or adding Meituan evidence to a travel/activity workflow.
- Neighbor: route/weather planning and calendar/booking-record tasks remain with their domain skills.
- Forbidden: login, payment, order placement, merchant order operations, and delivery dispatch.
- No-load: generic food writing without live provider evidence.

## Deterministic baseline

- Adapter unit tests: 4 passing.
- Keychain readiness: credential present.
- Managed package: pinned `@meituan-travel/ht-ai@0.0.6` under `~/.hermes/modules/meituan-travel`.
- Prior scoped provider queries exited 0 with no Token marker in stdout/stderr.

## Progressive loading

The core SKILL.md is self-contained. No accessory file is required for routine calls. `evals/` is test evidence and should not be loaded during normal execution.
