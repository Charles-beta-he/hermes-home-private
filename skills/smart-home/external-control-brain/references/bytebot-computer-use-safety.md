# Bytebot-style computer-use safety boundary

Use this reference when evaluating or integrating local/virtual desktop computer-use agents such as Bytebot.

## Safe default

Treat GUI computer-use as an external-control surface even when it runs inside a container. Mouse, keyboard, file writes, downloads, logins, and app installs can mutate state and leak credentials.

Default capability should be read-only:

- screenshot
- cursor position
- non-sensitive environment status
- static config inspection

All mutating actions require an explicit scoped action packet, audit path, and permission tier.

## Required boundary checks before enabling mutating computer-use

- Target is a container/VM/remote disposable desktop, not the user's host desktop.
- Network exposure is loopback-only or authenticated; no unauthenticated VNC/API on public interfaces.
- No host filesystem mount unless explicitly scoped and read-only by default.
- Credentials are injected through a managed channel, not typed into arbitrary screenshots/logs without a retention/redaction policy.
- Screenshot/action-trace retention is declared up front.
- Action allowlist is minimal: start with screenshot/cursor, then add browser navigation, then typing/clicking, then file writes/downloads.
- Every mutating request has an idempotency key and audit evidence.
- Long-running tasks can pause into `needs_help` or `needs_review`; never silently declare success after a GUI stall.

## Bytebot-specific caution points

From source inspection:

- Default compose exposes desktop/API/UI/Postgres ports.
- Desktop container uses `privileged: true` in the provided compose.
- Desktop API documentation describes no auth by default for localhost development.
- Takeover mode records screenshots/actions during task takeover.

These are not blockers for isolated experiments, but they are blockers for default Hermes integration.

## Recommended staged adoption

1. Isolated read-only spike: screenshot/cursor only; no credentials; no host mounts.
2. Safety wrapper: define Hermes action packet for computer-use with target desktop id, scope, retention policy, confirmation/audit/idempotency.
3. Limited browser workflow: allow navigation/click/type only inside a disposable browser profile.
4. Human takeover trace capture: convert demonstrated workflow into a skill/checklist candidate, not automatic replay.
5. Production gate: auth, network isolation, storage TTL, screenshot redaction, failure-to-review behavior, and selfcheck coverage.
