# Hermes tool budget and permission gates

Use this when a task runs into single-session tool-call limits, long autonomous loops, subagent orchestration, or permission/safety problems.

## Core principle

Do not try to turn one Hermes chat session into an unbounded daemon. Treat the session tool-call limit as an engineering boundary: move state, evidence, and execution ticks into durable artifacts and deterministic scripts.

## Tool-call budget pattern

1. **Batch mechanical calls**: combine 3+ repetitive read/check commands into one `execute_code` or local script that emits compact JSON.
2. **Externalize state**: write task state, evidence bundles, issue ledgers, verification outputs, and commit hashes to Markdown/JSON artifacts.
3. **Use resumable ticks**: split long missions into `plan -> execute -> verify -> certify -> commit` ticks. Each tick has explicit inputs, outputs, stop gates, and resume commands.
4. **Delegate or background long work**: use `delegate_task`, background terminal jobs, `hermes chat -q`, tmux sessions, or cron for long-running fanout/tests. The parent session reads verifiable handles, not full transcripts.
5. **Keep deterministic controllers outside the LLM loop**: local scripts should own list/next/claim/release/done/dashboard/selfcheck-style operations so the LLM spends tool calls on decisions and evidence, not repeated state mutations.
6. **Handoff on limit**: if tool-call or context limits interrupt the task, output a recovery handoff with completed gates, incomplete gates, artifact paths, and the next command. Never claim full certification without the required artifact.

## Permission gate tiers

| Tier | Examples | Default |
|---|---|---|
| T0 read-only | read/search/status/diff/audit | allow |
| T1 derived write | dashboards, sorted pools, review artifacts, temp evidence | scoped allowlist |
| T2 canonical mutation | add/claim/release/done/retry task notes | typed command + atomic write + actor/lease/proof log |
| T3 external side effect | PRs, issues, messages, deploys, push | dry-run first + explicit scope + verification |
| T4 destructive/secrets | delete, credentials, prod data, unbounded shell | deny by default; require explicit user authorization |

## Dynamic/typed tool proxy pattern

Inspired by OpenAI Symphony/Codex App Server dynamic tool calls: keep high-privilege credentials and APIs in the host/orchestrator, and expose only typed, allowlisted functions to working agents/subagents.

Rules:
- Subagents get task summaries and read-only evidence by default, not secrets.
- Vault writes go through typed local controllers, not arbitrary shell edits.
- External-system tokens remain in the parent/host tool; return minimum necessary results.
- Destructive or external actions first produce a dry-run plan.
- Every mutating command writes proof/evidence suitable for later audit.

## Verification checklist

- A durable artifact exists for each tick or decision gate.
- Long fanout/test jobs have timeout/degraded records.
- No secrets are copied into prompts, state JSON, Markdown, or git.
- Scoped commits exclude `.env`, `auth.json`, caches, screenshots, checkpoints, and tick directories unless explicitly intended.
