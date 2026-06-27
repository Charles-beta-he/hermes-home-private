# Claude Code PostToolUse as an evidence-feedback hook pattern

Applicability: use when analyzing Claude Code hooks, designing agent post-tool feedback loops, or hardening Hermes workflows that should react after a tool has produced real output. This pattern is about post-execution observation and feedback, not prevention, not pre-execution permission, and it cannot prevent the already-executed effect.

## Durable facts from Claude Code docs

- `PostToolUse` fires immediately after a tool call completes successfully.
- It matches on tool name, like `PreToolUse`; common matchers include `Bash`, `Edit|Write`, and `mcp__.*`.
- Its input includes `session_id`, `transcript_path`, `cwd`, `permission_mode`, `hook_event_name`, `tool_name`, `tool_input`, `tool_response`, `tool_use_id`, and optional `duration_ms`.
- `tool_input` is the arguments sent to the tool; `tool_response` is the successful result, with a tool-specific shape.
- `duration_ms` excludes permission-prompt and PreToolUse-hook time, so it can support tool-latency observability.
- `PostToolUse` can return event-specific feedback fields: `decision: "block"`, `reason`, `additionalContext`, `updatedToolOutput`, and `updatedMCPToolOutput`.
- `decision: "block"` adds feedback next to the tool result; it does not undo the already-executed tool.
- `additionalContext` injects context alongside the tool result, useful for nudging the next model step with evidence-aware guidance.
- `updatedToolOutput` replaces what Claude sees, but only after the tool already ran; it must match the tool's output shape or built-in tool replacement may be ignored.
- `updatedToolOutput` does not change filesystem, network, or external side effects that already occurred, and original telemetry may already contain the pre-redacted output.
- If a tool call fails, use `PostToolUseFailure`; it receives error information and can add corrective `additionalContext`.
- When parallel tool calls are involved, `PostToolUse` may fire concurrently per tool. Use `PostToolBatch` when context depends on the full set of tools that ran.
- Claude can modify files through `Bash`; `Edit|Write` matchers do not cover all file changes. For compliance-grade coverage, match `Bash` or use a turn-level `Stop` scan.

## Hermes-transferable operating pattern

For Hermes, treat PostToolUse as a **post-execution evidence and steering gate**:

1. **Observe after reality** — consume actual tool input/output, duration, cwd, and session/tool IDs after success.
2. **Classify the outcome** — convert raw results into evidence levels, risk flags, latency metrics, changed-path summaries, or next-step hints.
3. **Steer without pretending to prevent** — inject `additionalContext` or a block reason for the next model step, but never claim the hook prevented an effect that already happened.
4. **Redact with caution** — output replacement can reduce what the model sees, but it is not a privacy boundary for already-recorded telemetry/logs; secret prevention belongs in PreToolUse and command/tool design.
5. **Preserve schema** — if replacing output, keep the exact tool output shape; otherwise the model may still receive the original result.
6. **Use batch-level gates for aggregate facts** — per-tool hooks are unsafe for cross-call conclusions in parallel runs; use a batch/turn-level gate for “all checks passed” claims.
7. **Separate success and failure lanes** — success hooks enrich evidence; failure hooks add diagnosis and retry guidance.
8. **Ledger only derived facts** — store hashes, summaries, IDs, metrics, and artifact pointers; keep raw payloads/secrets out of hot ledgers.

## What Hermes should learn

- PostToolUse is a good model for **evidence capture after every tool**, especially command results, file writes, API responses, and verification receipts.
- It should feed the next step with compact, structured guidance: “test failed because X”, “edited file requires formatter”, “command touched protected area”, “tool latency exceeded threshold”.
- It is not enough for dangerous-action prevention. A bad `rm`, external send, publish, deploy, credential leak, or network write has already happened by the time PostToolUse fires.
- The right Hermes split is:
  - PreToolUse / permission gate: prevent or require authority before action.
  - PostToolUse: capture evidence, redact presentation when safe, steer repair, update local observability.
  - PostToolBatch / Stop: aggregate across a parallel batch or whole turn.
  - Verifier/certifier: decide whether evidence satisfies lifecycle advancement.

## Candidate Hermes slices

Safe documentation/skill slice:

- Add this pattern to autonomous-agent and event-governed-control-plane skills.
- Add a backtest rubric for post-tool evidence handling.

Safe local harness slice:

- Build a dry-run PostToolUse event classifier that accepts sample event JSON and emits derived evidence/risk/context without executing tools.
- Test success cases, schema mismatch, redaction warning, Bash file-change caveat, and parallel-batch caveat.

Higher-risk runtime slice:

- Wiring real Hermes tool calls through an always-on post-tool hook requires a separate runtime design, config switch, privacy review, and tests proving it cannot mutate lifecycle or external systems by itself.

## Backtest rubric

| Criterion | Pass signal | Fail signal |
|---|---|---|
| Post-execution boundary | Explicitly says effects already happened | Claims PostToolUse prevents the tool effect |
| Evidence capture | Uses tool_input/tool_response/tool_use_id/duration/cwd as evidence fields | Treats hook as generic prompt text only |
| Schema safety | Replacement output preserves tool-specific shape | Replaces structured output with arbitrary string |
| Secret/privacy boundary | PreToolUse handles prevention; PostToolUse redaction is presentation-only | Claims redaction removes telemetry/log exposure |
| Parallel safety | Uses PostToolBatch/turn gate for aggregate conclusions | Per-tool hook claims whole batch passed |
| Failure lane | Separates PostToolUseFailure diagnosis from successful PostToolUse | Tries to handle failed calls only through success hook |
| File-change coverage | Notes Bash can modify files and may need Bash/Stop coverage | Assumes Edit|Write covers all file changes |
| Authority boundary | Does not open external/destructive/lifecycle writes | Treats post-tool automation as new authority |

## Anti-conditions

Do not use PostToolUse as a substitute for permission checks, destructive-action prevention, credential handling, or lifecycle certification. Do not store raw tool outputs in durable ledgers by default. Do not claim a Hermes runtime hook exists unless a concrete implementation, config readback, and tests prove it.
