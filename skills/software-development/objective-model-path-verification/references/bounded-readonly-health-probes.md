# Bounded read-only health probes

## Applicability

Use when a local health check wraps another command or guard and must return status without opening browsers, reading business data, writing external systems, refreshing credentials, or waiting indefinitely.

Anti-conditions:

- This pattern does not authorize OAuth, secret entry, credential refresh, external reads, or writes.
- Do not turn an unavailable credential into a fabricated healthy result.
- Do not encode one provider's transient auth state as a permanent rule.

## Budget rule

For nested probes, the inner worst-case runtime must be strictly lower than the outer runner timeout:

```text
inner_timeout + cleanup_padding + serialization_margin < outer_timeout
```

If an inner command uses `auth_timeout + fixed_padding`, setting `auth_timeout` below the outer timeout is not sufficient. Compute or conservatively cap the full inner worst case. Otherwise the wrapper returns a generic timeout and hides the actionable terminal state.

## Status-only contract

Force and test these invariants where applicable:

- auth/status-only mode enabled;
- browser opening disabled;
- auto-authorization disabled;
- force refresh disabled;
- business-object reads disabled;
- external writes disabled;
- secrets/tokens redacted;
- bounded timeout and explicit non-zero degraded result.

A degraded health probe is successful observability when it returns a specific fail-closed state such as `no_tokens`, `login_in_progress`, `expired`, or `misconfigured` within budget. Do not confuse probe execution success with dependency health.

## Verification sequence

1. RED test the expected bounded timeout and side-effect flags.
2. Patch the smallest timeout/guard boundary; do not alter the auth state machine.
3. Run focused unit tests proving no browser/read/write calls occur.
4. Execute the real probe with an outer timeout.
5. Read back the structured status and confirm it is specific rather than wrapper-timeout noise.
6. Run the parent self-check and confirm the result is an operational finding, not a missing engineering check.
7. Stop at a human gate when OAuth or credential entry is required.

## Reporting

Separate:

- engineering coverage: the health watch exists and is tested;
- operational health: the dependency is healthy or degraded now;
- authority boundary: what exact human action is required.
