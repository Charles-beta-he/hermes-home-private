# References

Extracted from `/Users/charles/.hermes/skills/autonomous-ai-agents/hermes-agent/SKILL.md` on 2026-07-01T08:56:29.614759+00:00 during full core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

## References
- `references/rokid-lingzhu-sse-bridge.md` — fixed-domain Rokid Lingzhu custom-agent integration pattern for Hermes: FastAPI SSE bridge, Cloudflare Tunnel, DNS route, launchd persistence, and end-to-end SSE verification.
- `references/budget-relay-delegation.md` — debugging pattern for Hermes budget-relay features that appear wired at the CLI layer but fail on delegated child-agent execution paths; includes the staged-vs-worktree check.

- `references/hermes-self-check-update.md` — explicit Hermes self-check/update workflow and reporting checklist
- `references/rokid-lingzhu-bridge.md` — Rokid 灵珠/Rizon custom-agent bridge architecture, schema, safety red lines, and public exposure options
- `references/hermes-rokid-lingzhu-bridge.md` — implementation/operations notes for FastAPI SSE bridge, temporary Cloudflare tunnels, launchd recovery, and endpoint refresh
- `references/budget-handoff-automation.md` — default-safe budget/context exhaustion handoff automation
- `references/self-evolution-pua-loop.md` — Hermes-hosted OpenClaw SE-AOS fusion
- `references/pa-evolution-daily-reporting.md` — scheduled PA health reporting workflow, trigger interpretation, and when not to create a skill from `unknown`
- `references/openclaw-inspired-hermes-control-plane.md`
- `references/sakana-conductor-pattern.md` — Sakana-inspired multi-model conductor pattern for Hermes: evidence boundary, model capability profiles, role-specific prompting, default-off role plans, and truth-gate-preserving integration points.
- `references/ratchet-upgrades.md` — ratchet upgrade pattern for combining upstream Hermes updates with local overlays using multi-model impact review, fail-closed patch replay, and verified baseline advancement. — OpenClaw/external agent framework → Hermes-local control-plane hardening
- `references/continuation-control-plane.md` — global durable packet architecture for unfinished work across conversation, delegation, taskpool, bg-review, cron, and gateway; includes `agent/continuation.py` contracts and verification commands
- `references/auto-relay-continuation.md` — budget/tool-iteration exhaustion auto-relay with relay packets; includes the `max_iterations_reached(...)` exit-reason pitfall and verification checklist
- `references/taskpool-parallel-dispatch-and-handoff-governance.md` — taskpool parallel dispatch runtime config, dry-run observability, and handoff backlog archive workflow
- New Hermes scripts `~/.hermes/scripts/brain_api.py` and `~/.hermes/scripts/edge_worker.py` implement a local cloud-edge prototype (Brain HTTP API + Edge execution proxy) for validating the brain-tentacle architecture. See `cloud-edge-architecture` skill for the full architecture pattern.
- `references/prompt-builder-cache-layers.md` — 3-tier stable/context/volatile prompt cache architecture
- `references/layered-prompt-cache-implementation.md` — implementation pattern for Anthropic system content blocks, internal `_hermes_cacheable` markers, native tool cache markers, byte-stability fallback, and regression tests
- `references/evolution-lane-cert-loop.md` — evolution lane multimodel certification deadloop pattern and prevention
