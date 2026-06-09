# AgentMemory reference architecture notes

Use when evaluating local-first or cross-agent memory architectures for Hermes-like coding agents. Source examined in session: `https://github.com/rohitg00/agentmemory` at commit `bc641077913c0ac043e702a8f6519189e89b1721` (2026-05-21). Treat these as source-backed patterns, not a drop-in integration mandate.

## Verification pattern

When a user supplies or corrects a GitHub repo URL for an architecture-reference task:

1. Verify the URL by clone or GitHub API before analyzing.
2. Record canonical repo metadata: `full_name`, default branch, license, package/version if present, and commit hash.
3. Read repository-specific agent instructions (`AGENTS.md`, `CLAUDE.md`, etc.) after clone; they often contain consistency/update rules.
4. Inspect the concrete source files behind claimed capabilities, not only README marketing claims.
5. If prior task records used a wrong source, mark the mismatch explicitly and append corrected evidence to the task proof log instead of silently continuing.

## AgentMemory patterns worth reusing conceptually

- Shared local/self-hosted memory server used by multiple agents through MCP/REST/hook integrations.
- Lifecycle hooks: prefetch before LLM call, turn sync after events, pre-compress context reinjection, session-end consolidation, memory-write mirroring.
- Durable memory types and metadata: type, concepts, files, TTL, source observation IDs.
- Supersession/version chain for near-duplicate memories to reduce stale ghosts.
- Layered retrieval: lexical baseline plus optional vector/graph accelerators.
- Graceful vector degradation: embedding/index failures should not block a memory save; expose degraded state separately.
- Governance surfaces: retention, forget, audit, privacy, replay-sensitive checks, export/import, viewer security.

## Hermes-specific caution

- Do not replace Hermes `MEMORY.md` / `USER.md` policy with upstream defaults.
- Do not trust upstream benchmark claims as acceptance evidence until reproduced locally.
- Do not enable an upstream Hermes plugin blindly; first test with a temporary profile and isolated data directory.
- Cross-agent memory must still pass Hermes ghost-prevention policy: stable facts to memory, procedures to skills, WIP/session state to session search/logs, sensitive/short-lived facts to TTL or reject.

## Recommended absorption order

1. Read-only compatibility spike with temporary config/profile and isolated data dir.
2. Policy wrapper that classifies memory candidates before writing.
3. Optional retrieval bridge that labels source IDs, confidence and degraded mode while preserving existing Hermes memory/session search baseline.
4. Consolidation job that proposes memory/skill candidates from sessions with deterministic ghost-prevention checks.
5. Selfcheck coverage for server reachability, vector health, retention policy, data directory size, auth and HTTPS/token safety.
