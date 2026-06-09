# Prompt Assembly Cache Optimization

## Architecture (run_agent.py _build_system_prompt_parts)

Three-tier structure for cache-friendly prompt assembly:

1. **stable** — byte-stable across sessions: identity, tool guidance, skills prompt, platform hints
2. **context** — stable within a session: context files (AGENTS.md), CASI filtered skills, environment hints
3. **volatile** — changes per turn: memory snapshot, user profile, external memory, timestamp

Assembly: `stable\n\ncontext\n\nvolatile` → stable prefix maximizes cache hits.

## Key Finding: Environment Hints Misplacement

`build_environment_hints()` was in `stable_parts` but contains dynamic CWD:
```
Host: macOS (26.4.1)
User home directory: /Users/charles
Current working directory: /Users/charles/.hermes/hermes-agent  ← DYNAMIC
```

**Fix**: Move from `stable_parts.append()` to `context_parts.append()` at run_agent.py L5895.

## Caching Mechanisms

1. `_cached_system_prompt` — session-level cache, built once per session
2. `_use_long_lived_prefix_cache` — cross-session 1h TTL for Claude on Anthropic/OpenRouter/Nous
3. `_or_cache_hits` — OpenRouter response cache hit counter
4. CASI (Context-Aware Skill Indexing) — per-turn skill filtering in context tier without breaking stable prefix

## Verification

```bash
# Run prompt_builder tests after any change
python -m pytest tests/agent/test_prompt_builder.py -o "addopts=" -q
```

## Pitfalls

- Any function in `stable_parts` that reads CWD, session_id, or timestamp breaks cross-session cache
- CASI filtering must stay in `context_parts` — it changes per turn based on user message
- Platform hints are per-platform (static per session) — OK in stable_parts
