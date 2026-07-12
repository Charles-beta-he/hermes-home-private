---
name: read-only-control-plane-probes
description: Use when implementing or reviewing startup/selfcheck/status/dashboard readiness probes, health projections, dependency/update checks, or any operator-facing readback surface that must remain read-only and non-executing.
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags:
      - control-plane
      - selfcheck
      - readiness
      - tdd
      - no-side-effects
---

# Read-only Control-plane Probes

## When to use

Use this skill when adding, changing, or reviewing a local operator/readback surface such as:

- startup handshake or readiness probes
- `selfcheck`, `status`, `doctor`, or dashboard health projections
- update-target or dependency-health checks
- cached gateway/cron/tool/provider summaries
- any probe that should suggest a repair command without running it

Do not use this skill for actual repair/update/install/deploy execution paths. Those belong to the relevant execution/update skill and require their own authority and verification gates.

## Core invariant

A read-only probe reports state and suggests the next command. It does not fix state.

Required boundaries:

- no package installation (`pip`, `uv pip`, `npm`, `pnpm`, etc.)
- no repair commands
- no model/LLM calls
- no external dispatch or messaging
- no lifecycle writes, publish/deploy/push, or destructive operations
- no writes under explicit read-only modes such as `--no-write`
- fail-soft: probe failure should become `deferred`/`warn`, not crash startup

If the user asks to proceed from detection into repair, treat that as a separate execution action, not as part of the probe.

## TDD workflow

1. Write RED tests before implementation.
2. Test each reported class separately.
3. Assert the side-effect boundary in tests, not just the visible message.
4. Implement the smallest local/read-only inspection needed.
5. Run targeted tests, then the relevant regression slice.
6. Run a real readback command and inspect its output/schema.

For startup/selfcheck/readiness probes, tests should assert:

```python
assert probe["action_taken"] is False
assert receipt["side_effects"]["external"] is False
assert receipt["side_effects"]["llm"] is False
assert receipt["side_effects"]["writes"] == []  # under --no-write/read-only mode
```

## Dependency-health probe pattern

A dependency-health probe may report:

- interrupted update marker present
- declared core dependency missing
- active lazy/optional backend drift
- lazy install policy disabled

It must not install anything. It should return a warning and a suggested command, for example `hermes update --force`.

Implementation notes:

- Read `pyproject.toml` with stdlib `tomllib` where possible.
- Respect environment markers before flagging a dependency as applicable.
- Use distribution metadata presence/version checks; avoid importing heavy optional backends just to test availability.
- For lazy/optional features, beware shared-transitive false positives. A lazy registry may consider a feature active if any declared package is present, but shared packages such as `aiohttp` can be present because another feature installed them. Require a feature-owned/primary spec to be present before reporting drift for that feature.
- Cap warning detail to a few items so startup output stays legible.

## Verification checklist

Before claiming completion:

- RED test failed because the probe/interface did not exist or did not report the expected condition.
- GREEN tests cover every warning class added.
- Tests assert no action was taken.
- `--no-write` or equivalent read-only mode reports no writes.
- Real command readback shows the probe in the output.
- If the probe suggests a repair command, that command was not run unless the user separately authorized repair.

## References

- `references/hermes-startup-dependency-health.md` — session-derived pattern for Hermes startup dependency-health and update-target probes.
