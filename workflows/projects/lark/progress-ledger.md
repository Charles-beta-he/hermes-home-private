# Progress Ledger — lark

Created: 2026-07-06T17:33:11.521568+00:00

## Current truth

- The user granted a persistent, revocable `oauth_recovery_only` authority on 2026-07-10. Canonical grant: `authority-grants/lark-oauth-recovery-persistent-20260710.json`.
- Non-health Lark flows may automatically run bounded single-flight OAuth recovery only when the token is missing, invalid, or expired. Ordinary selfcheck remains status-only.
- The grant does not authorize task reads, Lark writes, password/OTP/secret entry, or external message sends; those retain separate authority boundaries.
- Live auth-only recovery succeeded: browser opened once, the visible primary authorize control was clicked, token readback became valid, and callback port 8765 plus the single-flight lock were released. Runtime evidence: `~/.hermes/state/selfcheck/lark-oauth-recovery-evidence-20260710T071221122044Z.json`.
- Procedure Registry now records `lark.oauth.recovery` as `e2e_passed / partially_landed`, with 1 of 2 independent successes. It is not fully connected or promotion-eligible yet.
- Status is evidence-gated; no global certification or canonical promotion follows from this local recovery.
