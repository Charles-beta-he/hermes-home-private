# Layered prompt cache implementation pattern

Use when implementing or reviewing Hermes prompt-cache changes for Anthropic/native message paths.

## Pattern

Separate prompt material into three classes:

1. `stable`: global durable instructions and invariant tool/workflow policy.
2. `context`: project/environment context that changes occasionally but should still be part of the reusable prefix.
3. `volatile`: dynamic state such as timestamps, current cwd hints, ephemeral cognitive hints, continuation notes, or per-turn runtime status.

For Anthropic messages, do not concatenate all three into one cacheable system string. Build system content blocks and mark cache intent internally:

- stable block: `_hermes_cacheable=True`
- context block: `_hermes_cacheable=True`
- volatile/ephemeral blocks: `_hermes_cacheable=False`

At the provider boundary:

- find the last `_hermes_cacheable=True` block
- add Anthropic `cache_control` only to that block
- strip every `_hermes_cacheable` field before sending the API payload
- do not cache volatile/ephemeral suffix blocks

## Native Anthropic tools

For the native Anthropic messages path, tool schemas can also be cache-marked. Use a deep copy of `agent.tools` and add `cache_control` only to the last tool entry.

Guardrails:

- never mutate `agent.tools`
- do not inject native Anthropic tool `cache_control` into generic OpenRouter/chat-completions paths unless that provider explicitly supports it
- keep existing tool ordering deterministic before cache marking

## Byte-stability guard

Only reuse cached system prompt parts when the active system prompt exactly matches the cached string. If the session restored an opaque stored system prompt that cannot be safely split, fall back to the legacy single-string system prompt rather than guessing a split.

## Regression tests to add

- stable/context blocks get cache intent, volatile/ephemeral blocks do not
- API payload contains Anthropic `cache_control` at the last cacheable system block
- `_hermes_cacheable` does not leak to provider payload
- native Anthropic tools are deep-copied and only the last tool gets `cache_control`
- invalidating `_cached_system_prompt` also invalidates `_cached_system_prompt_parts`
- real CLI smoke still starts and returns a minimal answer

## Pitfalls

- A green unit test on `apply_anthropic_cache_control` is not enough; also test the conversation-loop/system-prompt builder boundary so ephemeral prompt additions do not silently get concatenated into the cacheable prefix.
- If a broad Anthropic adapter suite fails in credential/keychain tests, classify whether it is credential-state/off-scope before treating it as a cache regression.
