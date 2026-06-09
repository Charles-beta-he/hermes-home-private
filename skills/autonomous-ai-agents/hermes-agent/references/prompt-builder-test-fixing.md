# Prompt Builder Test-Fixing Patterns

## Architecture

- **Source**: `agent/prompt_builder.py` — string constants assembled into system prompt
- **Tests**: `tests/agent/test_prompt_builder.py` — assert expected substrings exist in constants

Tests use `assert "expected_text" in CONSTANT_NAME` pattern. Failures mean the constant was changed without updating the test, or vice versa.

## Fix Pattern

1. Run targeted tests to identify failures:
   ```bash
   python -m pytest tests/agent/test_prompt_builder.py -v -o "addopts=" --no-header
   ```

2. For each failure, the test asserts a substring that must appear in the constant. Patch the **source constant** (not the test) to naturally include the expected text.

3. Verify: rerun the 3 failing tests, then full suite (121+ tests).

## Pitfalls

### Python substring gotcha
`"dependency" in "dependencies"` → **False**! Python substring matching is literal — "dependency" (ends in 'y') is NOT a substring of "dependencies" (ends in 'ies').

Fix: rephrase to include the exact expected word. E.g., "Resolve dependencies first" → "Resolve each dependency first" (now contains "dependency").

### Keep additions natural
Don't just concatenate expected phrases. Embed them in contextually appropriate sentences:
- Bad: "...session_search. relevant cross-session context exists."
- Good: "...session_search; relevant cross-session context exists there. Don't ask them to repeat."

### Run with `-o "addopts="` to override pyproject.toml
The project's pyproject.toml configures `-n auto` (xdist parallel). Use `-o "addopts="` to run single-threaded for cleaner output during debugging.

## Constant → Test Mapping (key assertions)

| Constant | Test expects substring |
|---|---|
| `SESSION_SEARCH_GUIDANCE` | `"relevant cross-session context exists"`, NOT `"recent turns of the current session"` |
| `TOOL_USE_ENFORCEMENT_GUIDANCE` | `"describe"`, `"promise"`, `"tool call"`, `"MUST"` |
| `OPENAI_MODEL_EXECUTION_GUIDANCE` | `"tool_persistence"`, `"retry"`, `"empty"`, `"prerequisite"`, `"dependency"`, `"correctness"`, `"guess"` |
