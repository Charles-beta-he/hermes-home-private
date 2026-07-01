# Claude Code CLI Subcommands, Print Mode, and Flags

Extracted from `/Users/charles/.hermes/skills/.archive/curator-umbrella-2026-06-10/autonomous-ai-agents/claude-code/SKILL.md` on 2026-07-01T08:57:36.131647+00:00 during full core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

## CLI Subcommands

Detailed `CLI Subcommands` guidance moved to `references/cli-subcommands.md`.

Load it only when this specialized branch is directly active; preserve root safety and verification rules.
## Print Mode Deep Dive

### Structured JSON Output
```
terminal(command="claude -p 'Analyze auth.py for security issues' --output-format json --max-turns 5", workdir="/project", timeout=120)
```

Returns a JSON object with:
```json
{
  "type": "result",
  "subtype": "success",
  "result": "The analysis text...",
  "session_id": "75e2167f-...",
  "num_turns": 3,
  "total_cost_usd": 0.0787,
  "duration_ms": 10276,
  "stop_reason": "end_turn",
  "terminal_reason": "completed",
  "usage": { "input_tokens": 5, "output_tokens": 603, ... },
  "modelUsage": { "claude-sonnet-4-6": { "costUSD": 0.078, "contextWindow": 200000 } }
}
```

**Key fields:** `session_id` for resumption, `num_turns` for agentic loop count, `total_cost_usd` for spend tracking, `subtype` for success/error detection (`success`, `error_max_turns`, `error_budget`).

### Streaming JSON Output
For real-time token streaming, use `stream-json` with `--verbose`:
```
terminal(command="claude -p 'Write a summary' --output-format stream-json --verbose --include-partial-messages", timeout=60)
```

Returns newline-delimited JSON events. Filter with jq for live text:
```
claude -p "Explain X" --output-format stream-json --verbose --include-partial-messages | \
  jq -rj 'select(.type == "stream_event" and .event.delta.type? == "text_delta") | .event.delta.text'
```

Stream events include `system/api_retry` with `attempt`, `max_retries`, and `error` fields (e.g., `rate_limit`, `billing_error`).

### Bidirectional Streaming
For real-time input AND output streaming:
```
claude -p "task" --input-format stream-json --output-format stream-json --replay-user-messages
```
`--replay-user-messages` re-emits user messages on stdout for acknowledgment.

### Piped Input
```
# Pipe a file for analysis
terminal(command="cat src/auth.py | claude -p 'Review this code for bugs' --max-turns 1", timeout=60)

# Pipe multiple files
terminal(command="cat src/*.py | claude -p 'Find all TODO comments' --max-turns 1", timeout=60)

# Pipe command output
terminal(command="git diff HEAD~3 | claude -p 'Summarize these changes' --max-turns 1", timeout=60)
```

### JSON Schema for Structured Extraction
```
terminal(command="claude -p 'List all functions in src/' --output-format json --json-schema '{\"type\":\"object\",\"properties\":{\"functions\":{\"type\":\"array\",\"items\":{\"type\":\"string\"}}},\"required\":[\"functions\"]}' --max-turns 5", workdir="/project", timeout=90)
```

Parse `structured_output` from the JSON result. Claude validates output against the schema before returning.

### Session Continuation
```
# Start a task
terminal(command="claude -p 'Start refactoring the database layer' --output-format json --max-turns 10 > /tmp/session.json", workdir="/project", timeout=180)

# Resume with session ID
terminal(command="claude -p 'Continue and add connection pooling' --resume $(cat /tmp/session.json | python3 -c 'import json,sys; print(json.load(sys.stdin)[\"session_id\"])') --max-turns 5", workdir="/project", timeout=120)

# Or resume the most recent session in the same directory
terminal(command="claude -p 'What did you do last time?' --continue --max-turns 1", workdir="/project", timeout=30)

# Fork a session (new ID, keeps history)
terminal(command="claude -p 'Try a different approach' --resume <id> --fork-session --max-turns 10", workdir="/project", timeout=120)
```

### Bare Mode for CI/Scripting
```
terminal(command="claude --bare -p 'Run all tests and report failures' --allowedTools 'Read,Bash' --max-turns 10", workdir="/project", timeout=180)
```

`--bare` skips hooks, plugins, MCP discovery, and CLAUDE.md loading. Fastest startup. Requires `ANTHROPIC_API_KEY` (skips OAuth).

To selectively load context in bare mode:
| To load | Flag |
|---------|------|
| System prompt additions | `--append-system-prompt "text"` or `--append-system-prompt-file path` |
| Settings | `--settings <file-or-json>` |
| MCP servers | `--mcp-config <file-or-json>` |
| Custom agents | `--agents '<json>'` |

### Fallback Model for Overload
```
terminal(command="claude -p 'task' --fallback-model haiku --max-turns 5", timeout=90)
```
Automatically falls back to the specified model when the default is overloaded (print mode only).

## Complete CLI Flags Reference

### Session & Environment

Detailed `Session & Environment` guidance moved to `references/session-environment.md`.

Load it only when this specialized branch is directly active; preserve root safety and verification rules.
### Model & Performance
| Flag | Effect |
|------|--------|
| `--model <alias>` | Model selection: `sonnet`, `opus`, `haiku`, or full name like `claude-sonnet-4-6` |
| `--effort <level>` | Reasoning depth: `low`, `medium`, `high`, `max`, `auto` | Both |
| `--max-turns <n>` | Limit agentic loops (print mode only; prevents runaway) |
| `--max-budget-usd <n>` | Cap API spend in dollars (print mode only) |
| `--fallback-model <model>` | Auto-fallback when default model is overloaded (print mode only) |
| `--betas <betas...>` | Beta headers to include in API requests (API key users only) |

### Permission & Safety
| Flag | Effect |
|------|--------|
| `--dangerously-skip-permissions` | Auto-approve ALL tool use (file writes, bash, network, etc.) |
| `--allow-dangerously-skip-permissions` | Enable bypass as an *option* without enabling it by default |
| `--permission-mode <mode>` | `default`, `acceptEdits`, `plan`, `auto`, `dontAsk`, `bypassPermissions` |
| `--allowedTools <tools...>` | Whitelist specific tools (comma or space-separated) |
| `--disallowedTools <tools...>` | Blacklist specific tools |
| `--tools <tools...>` | Override built-in tool set (`""` = none, `"default"` = all, or tool names) |

### Output & Input Format
| Flag | Effect |
|------|--------|
| `--output-format <fmt>` | `text` (default), `json` (single result object), `stream-json` (newline-delimited) |
| `--input-format <fmt>` | `text` (default) or `stream-json` (real-time streaming input) |
| `--json-schema <schema>` | Force structured JSON output matching a schema |
| `--verbose` | Full turn-by-turn output |
| `--include-partial-messages` | Include partial message chunks as they arrive (stream-json + print) |
| `--replay-user-messages` | Re-emit user messages on stdout (stream-json bidirectional) |

### System Prompt & Context

Detailed `System Prompt & Context` guidance moved to `references/system-prompt-context.md`.

Load it only when this specialized branch is directly active; preserve root safety and verification rules.
### Debugging
| Flag | Effect |
|------|--------|
| `-d, --debug [filter]` | Enable debug logging with optional category filter (e.g., `"api,hooks"`, `"!1p,!file"`) |
| `--debug-file <path>` | Write debug logs to file (implicitly enables debug mode) |

### Agent Teams
| Flag | Effect |
|------|--------|
| `--teammate-mode <mode>` | How agent teams display: `auto`, `in-process`, or `tmux` |
| `--brief` | Enable `SendUserMessage` tool for agent-to-user communication |

### Tool Name Syntax for --allowedTools / --disallowedTools
```
Read                    # All file reading
Edit                    # File editing (existing files)
Write                   # File creation (new files)
Bash                    # All shell commands
Bash(git *)             # Only git commands
Bash(git commit *)      # Only git commit commands
Bash(npm run lint:*)    # Pattern matching with wildcards
WebSearch               # Web search capability
WebFetch                # Web page fetching
mcp__<server>__<tool>   # Specific MCP tool
```
