# Routing Baseline

## Scope

This baseline is limited to the `wechat-local-export` user-local skill routing contract. It does not certify a real WeChat export implementation.

## Applicability

Re-run after changing the skill description, trigger/counter-trigger language, or default doctor behavior.

## Anti-conditions

Do not interpret prompt classification as authority to access data or as proof that an exact WeChat version is supported.

## 2026-07-28 baseline

- Positive: 3 cases explicitly match user-owned local macOS WeChat readiness/export/query.
- Neighbor: 2 cases remain with media and Apple/macOS permission workflows.
- Forbidden: 2 cases require refusal rather than this capability.
- No-load: 1 generic writing case remains general.
- Accessory scripts: doctor script is conditionally read/executed only after the skill triggers; its test script is verification-only.
- Deterministic behavior: 5 focused doctor tests pass; CLI emits machine-readable JSON and fail-closes real export.
- Current runtime status: `doctor_available / export_blocked`.
