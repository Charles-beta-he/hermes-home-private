# Prompt Builder 3-Tier Cache Architecture

The system prompt is assembled in three ordered tiers, from most-stable to most-volatile, to maximise LLM prefix cache hits.

## Architecture (run_agent.py `_build_system_prompt_parts`)

```
stable  →  context  →  volatile
(cached)   (session)   (per-turn)
```

### Tier 1: stable (byte-stable across sessions)

Content that is identical across sessions for the same model/provider:
- `DEFAULT_AGENT_IDENTITY` — hardcoded identity string
- `HERMES_AGENT_HELP_GUIDANCE` — static help text
- `TOOL_USE_ENFORCEMENT_GUIDANCE` — tool-use rules
- `OPENAI_MODEL_EXECUTION_GUIDANCE` — model-specific execution rules
- `GOOGLE_MODEL_OPERATIONAL_GUIDANCE` — Google model rules
- Skills system prompt (from snapshot cache)
- Platform hints (per-platform, but static per platform)

### Tier 2: context (stable within a session, changes between sessions)

Content that is stable within one session but may differ between sessions:
- Context files: AGENTS.md, CLAUDE.md, .cursorrules, SOUL.md
- CASI-filtered skills (per-turn skill relevance filtering)
- `build_environment_hints()` — **MUST be here, NOT in stable** (contains CWD)

### Tier 3: volatile (changes per turn)

Content that changes on most turns:
- Memory snapshot
- User profile
- External memory provider block
- Timestamp line ("Conversation started: ...")
- Session ID, Model, Provider

## Critical rule: environment_hints is context, NOT stable

`build_environment_hints()` returns:
```
Host: macOS (26.4.1)
User home directory: /Users/charles
Current working directory: /Users/charles/.hermes/hermes-agent
```

The CWD line changes between sessions → placing it in `stable_parts` breaks the byte-stable prefix → cache misses on every session.

**Fix**: `context_parts.append(_env_hints)` (not `stable_parts`)

## Cache control

- `_cached_system_prompt`: built once per session, reused for all turns.
- `_cached_system_prompt_parts`: keep the layer split (`stable`/`context`/`volatile`) alongside the legacy string so provider adapters can construct content blocks without changing session persistence semantics.
- `_use_long_lived_prefix_cache`: cross-session 1h TTL where the provider supports it; otherwise use the normal short TTL.
- Anthropic system prompt caching should use layered content blocks, not a single opaque string, whenever the prompt was built in the current session:
  - mark `stable` and `context` blocks internally as `_hermes_cacheable: true`;
  - mark `volatile`, ephemeral system hints, and cognitive/turn-local hints as `_hermes_cacheable: false`;
  - place provider `cache_control` only on the last cacheable block, then strip all `_hermes_cacheable` private fields before sending API kwargs.
- If the system prompt came from an old continuation/stored session as an opaque byte-stable string, preserve it as a string fallback rather than trying to reconstruct layers. Byte stability is more important than retroactive block conversion.
- For native Anthropic tools, add `cache_control` to the last tool schema using a deep copy of `agent.tools`. Do not mutate the registry/agent tool list. Be conservative on OpenRouter/chat-completions paths because tool-level `cache_control` compatibility differs.

## TDD pattern for prompt-cache changes

When modifying prompt cache assembly, write RED tests before changing providers:

1. A layered-system test where `stable`/`context` are cacheable and timestamp/ephemeral blocks are not. Assert `cache_control` lands only on the final cacheable block and private `_hermes_cacheable` flags are stripped.
2. A tool-cache test that verifies the last tool gets `cache_control`, empty tools stay empty, and the original tools object is not mutated.
3. A provider integration test for the native Anthropic kwargs path; verify OpenRouter/chat-completions behavior separately instead of assuming the same schema works everywhere.
4. Keep legacy string fallback tests for continuation sessions that load a stored `_cached_system_prompt`.

## Pitfalls

- Adding ANY dynamic content to `stable_parts` breaks prefix cache for ALL subsequent sessions.
- Do not put `cache_control` on the final system block blindly; that usually caches volatile timestamp/memory/ephemeral content and poisons prefix reuse. Use the last cacheable stable/context block instead.
- CASI (Context-Aware Skill Indexing) filters skills per-turn but places result in `context_parts`, not `stable_parts` — this preserves the stable prefix.
- Timestamp MUST stay in `volatile_parts` — it changes every session.
- Ephemeral system prompts and cognitive hints must be appended as non-cacheable blocks after the stable/context prefix; never concatenate them into the cached prefix when prompt caching is enabled.
- Avoid attribute annotations on instance attributes inside non-`__init__` helper functions in Hermes init code; use plain assignment when adding cached state like `_cached_system_prompt_parts`.
