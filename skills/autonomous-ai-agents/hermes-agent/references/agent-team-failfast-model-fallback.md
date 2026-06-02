# Agent Team Controller: Fail-Fast Model Fallback and Workspace Sync

Use this reference when debugging or extending `agent_team_controller.py` parallel worker execution, especially when workers burn timeout on infrastructure failures instead of falling back to the next model.

## Problem

When running parallel workers via `agent_team_controller.py consume-claimed`, infrastructure errors (MCP connection failures, SDK crashes, auth/quota exhaustion) cause workers to hang for the full 600s timeout instead of detecting the failure and retrying with the next model in the fallback chain.

## Model Fallback Chain

For codegen tasks (`requires_codegen`), the fallback order is:

```
GPT-5.5 (openai-codex) → Claude Sonnet (anthropic) → MiMo (xiaomi)
```

For non-codegen tasks, MiMo (xiaomi) executes directly.

Key rule: infrastructure failures trigger model switch; terminal task outcomes (valid `PROOF_JSON`, `BLOCKED`/blocked proof, or proof-consistency failure) return as-is. Provider proof-contract failures (`PROOF_JSON` marker with unparsable JSON, or non-blocked output with no `PROOF_JSON`) should continue to the next provider before failing closed after the chain is exhausted; never synthesize DONE proof from prose output.

## Infra Error Detection

`_detect_infra_failure(output, stderr)` checks for 4 patterns:

| Pattern | Signal | Keyword |
|---------|--------|---------|
| Codex SDK null response | `SDK parse_response crashed on null response.output` | `codex_sdk_null_response` |
| MCP connection loop | stderr contains 4+ "MCP server" lines | `mcp_server_connection_loop` |
| OpenAI client closed | `Detected closed shared OpenAI client; recreating before use` | `openai_client_closed` |
| Codex auth/quota | `openai-codex error 401/429/503` | `codex_auth_or_quota` |

Returns `(is_infra: bool, keyword: str)`. When `is_infra` is True, the worker should log `infra_failure_fallback` trace event and immediately retry with the next model.

## Workspace Sync Barrier

`_verify_workspace_ready(task_id)` runs BEFORE spawning workers:

1. Derives workspace path: `/tmp/agent-team-{task_id[:16]}`
2. Checks directory exists → mkdir if not
3. Checks directory is writable → fail-fast if not
4. Returns `(ok, path, error)`

If `ok` is False, the task transitions to `pending` with `workspace_not_ready` trace event instead of wasting a worker slot.

## Trace Events

New trace events added to the parallel dispatch flow:

- `worker_attempt` — logged per model attempt with `model`, `provider`, `attempt`
- `infra_failure_fallback` — infra error detected, switching model
- `timeout_infra_fallback` — timeout + infra error on stderr, switching model
- `workspace_not_ready` — workspace verification failed
- `worker_exception` — exception in worker spawn/execution

## MCP Server Path Pitfall

The MCP launcher does NOT expand `~` in server args. Config like:

```yaml
git:
  args:
  - ~/.hermes/scripts/mcp-git-server.py  # BROKEN
```

resolves to `/Users/charles/.hermes/hermes-agent/~/.hermes/scripts/mcp-git-server.py`.

Fix: use absolute path:

```yaml
git:
  args:
  - /Users/charles/.hermes/scripts/mcp-git-server.py  # CORRECT
```

Symptom: repeated `can't open file ... No such file or directory` in `~/.hermes/logs/mcp-stderr.log`, each worker wasting 7s × 3 retries.

Detection: `grep '~' ~/.hermes/config.yaml` in the `mcp_servers` section.

## Advisory evaluation task routing pitfall

Reference-review / external-framework evaluation tasks often mention `Hermes`, `worker`,
`control-plane`, or `taskpool` because they map a repo/framework back to Hermes primitives.
Do not classify those words alone as codegen intent. If the title/body contains advisory
markers such as `评估`, `参考价值`, `reference review`, `framework evaluation`, or `gap analysis`
and lacks explicit implementation markers such as `实现`, `修复`, `patch`, or `code change`,
route it as analysis first instead of starting with GPT-5.5/openai-codex. Otherwise workers
can burn the whole codegen timeout, leave only a stub checkpoint, and move to retry without
final `PROOF_JSON`.

Regression shape:
- `评估 OpenAgents ... 对 Hermes ... 参考价值` + project `hermes-agent` => analysis route
- `实现 Hermes agent_team_controller worker timeout fallback 修复` => codegen route

## Verification

```bash
# Compile check
python3 -m py_compile ~/.hermes/scripts/agent_team_controller.py

# Unit tests
cd ~/.hermes && python3 -m pytest scripts/test_agent_team_controller.py scripts/test_agent_team_controller_safety.py scripts/test_agent_team_controller_split.py -x -q

# Smoke test for new functions
python3 -c "
import sys; sys.path.insert(0, '/Users/charles/.hermes/scripts')
from agent_team_controller import _detect_infra_failure, _verify_workspace_ready
assert _detect_infra_failure('SDK parse_response crashed on null response.output') == (True, 'codex_sdk_null_response')
assert _detect_infra_failure('normal output') == (False, '')
ok, path, err = _verify_workspace_ready('test-task-123')
assert ok, f'Expected ok, got {err}'
print('PASS')
"

# MCP path check
grep '~' ~/.hermes/config.yaml | grep -v '^#' | grep -i mcp
```
