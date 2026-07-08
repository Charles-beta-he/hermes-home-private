# Architecture Boundary — Context Engineering OS

Timestamp: 2026-07-08T03:18:30Z

## Design Document

This project intentionally lands Context Engineering as an edge-governed capability before touching Hermes core runtime:

- skill: routing and reusable operating procedure;
- project profile: scoped project identity and red lines;
- SSOT: objective, evidence, roadmap, converge matrix;
- scripts: local packet lint and regression eval;
- receipts: local side-effect flags all false for external/deploy/push/cron/taskpool lifecycle/credential/destructive actions.

## Gate Readback

Core prompt/runtime changes are deferred because Hermes source AGENTS.md states:

- prompt caching is sacred;
- core is a narrow waist;
- prefer CLI command + skill before core tool or prompt expansion;
- system prompt should remain byte-stable for an ongoing conversation.

## Next Architecture Gate

Before any core runtime integration:

1. exact target files in `/Users/charles/.hermes/hermes-agent` must be named;
2. default-off config flag must be specified;
3. focused tests must cover enabled, disabled, and tool-unavailable behavior;
4. prompt-cache invariants must be read back;
5. rollback command must be available via git revert/reset.
