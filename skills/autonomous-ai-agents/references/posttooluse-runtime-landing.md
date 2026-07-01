# PostToolUse Runtime Landing Pattern

Applicability: use when turning a post-tool hook pattern (Claude Code `PostToolUse` / `PostToolUseFailure` or equivalent) into a real agent runtime capability, especially in Hermes-like control planes with plugin/shell hooks, tool-result transforms, and evidence ledgers.

Anti-conditions: do not use this as permission to execute external side effects, bypass pre-tool approval, redact already-recorded telemetry, or claim runtime support from docs/skills alone. A post-tool hook is post-execution: it can steer the next step or replace a returned/model-visible result, but it cannot prevent, undo, or erase the original side effect.

## Landing checklist

1. Define the event lanes separately.
   - Success lane: `post_tool_call` / `PostToolUse`.
   - Failure lane: `post_tool_failure` / `PostToolUseFailure`.
   - Keep pre-tool prevention in `pre_tool_call`; post-tool feedback is advisory.

2. Preserve internal vs wire names.
   - Normalize external aliases (`PreToolUse`, `PostToolUse`, `PostToolUseFailure`) to internal events.
   - Preserve the configured wire alias in shell-hook stdin (`hook_event_name`) so portability tests match runtime behavior.
   - Make CLI test helpers (`run_once`, `hooks test`) use the same wire-name serialization and parsing path as runtime callbacks.

3. Keep non-post payloads backward-compatible.
   - Only top-level core fields such as `tool_name`, `args`, `session_id`, `parent_session_id` should be removed from `extra`.
   - Do not accidentally remove event-specific fields (`result`, `duration_ms`, `error_message`, etc.) from non-post events such as `transform_tool_result`.
   - Add a regression test proving non-post payload extras survive.

4. Make success feedback explicit.
   - Accept structured dict feedback, not arbitrary plain strings, for post-tool behavior changes.
   - Support `context` / `additionalContext` and Claude-style `hookSpecificOutput` wrappers.
   - If supporting `updatedToolOutput` / `updatedMCPToolOutput`, document whether replacement affects only the model-visible tool message or the broader returned result pipeline.

5. Keep failure feedback unable to mask failures.
   - Failure hooks may append recovery context.
   - Failure hooks should not replace the sanitized error JSON unless the product explicitly designs and tests that behavior.
   - Add a regression test: a failure hook returning `updatedToolOutput` still leaves the original error visible.

6. Cover every runtime-owned tool path.
   - Generic registry dispatch and agent-runtime-owned tools (todo/memory/session/delegate/clarify style paths) may have separate execution code.
   - Success and exception paths in each ownership lane need hook emission or an explicit anti-condition.
   - Add a regression test for an agent-owned tool exception emitting `post_tool_failure`.

7. Verify in layers before commit.
   - RED tests must fail for missing alias parsing, payload fields, feedback application, and failure emission.
   - GREEN focused tests should cover shell parsing/payloads, runtime result feedback, failure context, and owned-tool exception paths.
   - Run syntax checks and `git diff --check`.
   - Smoke with a temporary home/config, not the user's real config: `hooks test PreToolUse`, `hooks test PostToolUse`, and `hooks test PostToolUseFailure`.
   - Secret-scan the diff for obvious credential patterns.
   - Use an independent reviewer after implementation; if blockers are fixed afterward, rerun either a focused re-review or targeted tests proving each blocker closure.

## Review pitfalls caught in practice

- `hooks test` can diverge from runtime if it serializes internal event names instead of the configured wire alias.
- Normalizing aliases only in config parsing is not enough; response parsing must also normalize aliases such as `PreToolUse` before interpreting block directives.
- Adding new top-level payload fields can silently break older shell hooks if those fields disappear from `extra` for unrelated events.
- `PostToolUseFailure` output replacement can hide a real error unless disabled or explicitly designed.
- Agent-owned tool paths often bypass generic registry dispatch; audit both success and exception paths.
- Full large test modules may time out; report that honestly and combine focused tests, related suites, smoke tests, static checks, and independent review rather than claiming a full-suite pass.
