# Phase 38 — claude-workflow-studio → Hermes Workflow/Agent Builder gap mapping

Mission: `msn_20260610_120149_27c88cfc`
Task: `2026-06-14-douyin线索-claude-workflow-studio图形化多agent工作流控制面吸收评估`
Date: 2026-06-14
Scope: read-only source review + local durable evidence. No install, no server start, no Claude Code CLI invocation, no credential write, no external send, no push/deploy.

## 1) Canonical source evidence

Lead source already captured in intake artifact `/Users/charles/.hermes/docs/private/2026-06-13-douyin-claude-workflow-studio-intake.md`:

- Douyin lead resolved to `https://www.douyin.com/note/7648901090390618538`, visible description frames the value claim as a visual workflow DAG with system-level restrictions to stop agents drifting from the graph.
- Canonical repo: `https://github.com/FocuZHe/claude-workflow-studio`, default branch `master`, MIT, JavaScript/TypeScript/Node stack.

Fresh local source review in this slice:

- Clone path: `/Users/charles/.hermes/runs/claude-workflow-studio-review-20260614-0124/repo`
- Commit: `823e6c7be3d7937c3e75417600db3582161b1797`
- Tracked files: 646
- Docs present: `docs/architecture.md`, `docs/architecture_EN.md`, `docs/frontend-backend-mapping.md`, `docs/full-sdk-architecture.md`, migration/optimization docs.
- `package.json`: `name=claude-workflow-studio`, `version=1.5.0`; scripts include `start`, `dev`, `build`, `check:frontend`, `test`, `test:integration`, `test:frontend`; dependencies include `@anthropic-ai/claude-agent-sdk`, `@anthropic-ai/claude-code`, `@anthropic-ai/sdk`, `express`, `ws`, `node-pty`, `p-limit`, `sql.js`, `uuid`.

README evidence:

- README lines 16-18: web platform for orchestrating, monitoring, and managing multiple Claude Code agents; explicitly experimental preview and not production tested for important file changes.
- README lines 60-78: feature list includes dual-loop architecture, visual workflow with six node types, skills market, autonomous judgement nodes, human approval nodes, WebSocket streaming, checkpoint/resume, memory, embedded PTY, multi-workspace isolation, task queues, analytics, crash recovery, read-only AI chat, API key encryption, command whitelist, concurrency protection, workspace sandbox, file access limits.
- README lines 80-90: node taxonomy: start, agent, autonomous judgement, human approval, conditional branch, subworkflow, end.
- README lines 94-103: stack: HTML/CSS/TypeScript/JS SPA, Node.js + Express + TypeScript, WebSocket `ws`, Anthropic API + Claude Agent SDK, `sql.js` + JSON files.

Architecture evidence from `docs/architecture_EN.md` search/read-back:

- Lines 46-50: Browser SPA talks over HTTP + WebSocket to Express/WebSocket server.
- Lines 83-84: execution flow saves checkpoints, returns output, broadcasts via WebSocket.
- Lines 180-182: approval node suspends awaiting human approval.
- Lines 365-367: parallel nodes, approval nodes, merge nodes are first-class node behaviors.
- Lines 378-396: checkpoint files per node plus global state; sync/atomic writes and save-before-failure claims.
- Lines 401-408: startup scans checkpoints, detects incomplete runs, resumes from first pending node.
- Lines 416-419: pause/resume contract and timeout behavior.
- Lines 430-446: approval flow: orchestrator detects approval, emits WebSocket `workflow.approvalRequested`, frontend dialog returns approve/reject, rejection feedback returns to main agent.
- Lines 491-492: parallel execution with independent worktree isolation.

Frontend/API evidence from source search:

- `src/client/js/api.ts` exposes workflow execute/pause/stop, approval response, checkpoint list, and resume-from-checkpoint endpoints.
- `src/client/js/pages/WorkflowCanvas.js` exposes visual nodes for agent, condition, subworkflow, approval and approval config fields.
- `src/client/js/pages/TerminalPage.js` directly writes input to PTY and streams output via WebSocket; this is a high-risk surface for Hermes.
- `src/client/js/pages/SkillsMarket.js` includes install commands such as `npx skills add ...`; this is not acceptable for autonomous Hermes intake.

## 2) Hermes mapping table

| claude-workflow-studio pattern | Hermes landing zone | Absorb? | Required adaptation |
|---|---|---:|---|
| Visual DAG editor | Dashboard / future Agent Builder projection | Yes, projection only | UI must compile to a plan preview; canonical state remains mission ledger/taskpool, not browser-local JSON. |
| Code-governed workflow execution | Workflow kernel / mission runner | Yes | Deterministic graph interpreter with topological ordering, typed nodes, idempotent receipts, proof hashes. |
| Human approval node | `hermes mission handoff` / Human Intervention Packet | Yes | Reuse existing durable decision ledger; approval nodes must pause and create open decisions, not poll hidden UI state. |
| Condition / AI judgement node | proof gate / ratification gate | Yes, guarded | JSON schema validation + claim/evidence binding; advisory model output cannot certify without deterministic checks. |
| Checkpoint/resume | objective ledger + wrapper run receipts | Yes | Use append-only receipts and per-node state; support resume only when input/output hashes match. |
| WebSocket event stream | dashboard/event projection | Yes | Read-only projection from ledger events; no UI direct writes to canonical taskpool/Mission ledgers. |
| Parallel subagents/worktrees | delegated workers / taskpool parallel boundary | Partial | Require lease, conflict group, workspace isolation, and no auto-spawn when task scope forbids multimodel. |
| Embedded PTY/file manager | terminal/computer-use tool plane | Not in this slice | Must remain explicit tool calls with allowlists, audit, and human-gated high-risk surfaces. |
| Skills market install commands | Hermes skills/plugins | No autonomous import | Staged candidate + read-back/proof-check only; no arbitrary external skill install. |
| API key encryption/config UX | Hermes secrets/config | Not from this repo | Do not write credentials; use existing `hermes secrets` governance only. |

## 3) Minimal verifiable integration slice

Recommended next implementation task (separate from this source-review task):

`workflow_dag_projection_preview` — add a local-only CLI that reads a small workflow JSON fixture and emits a Hermes-native projection without executing agents.

Minimum behavior:

1. Parse a workflow fixture with nodes: `start`, `agent`, `condition`, `approval`, `end`.
2. Validate edges form a DAG, reject cycles/orphans, compute topological order.
3. Compile each node to a planned Hermes action class:
   - `agent` → `PLAN_AGENT_STEP` (no model call)
   - `condition` → `PLAN_PROOF_GATE` (schema only)
   - `approval` → `PLAN_HUMAN_HANDOFF` (would call `hermes mission handoff`, but dry-run only)
   - `end` → `PLAN_STAGE_REPORT`
4. Emit JSON report with graph hash, node order, blocked side-effect surfaces, and ledger mapping.
5. Tests: cycle rejection, approval node mapping, no side-effect dry-run, deterministic graph hash.

This slice preserves the valuable “brain to AI, hands to code” pattern while avoiding runtime takeover, external model execution, PTY/file-manager risk, skill install risk, and dashboard write risk.

## 4) Red lines / authority boundaries

Do not do any of the following without a fresh explicit human decision:

- Install or run `claude-workflow-studio`.
- Invoke Claude Code CLI, Anthropic SDK, or any credentialed model smoke from this task.
- Open or expose embedded PTY/file manager surfaces.
- Let a UI directly write taskpool/Mission canonical ledgers.
- Import skills market install commands or auto-install third-party skills/plugins.
- Treat Douyin/social metrics as architecture proof.
- Push, deploy, publish, or send external messages.
- Mutate mission cadence/budget or secrets.

## 5) Follow-up dependency order

1. **Read-only compiler/preview**: implement `workflow_dag_projection_preview` with fixture tests.
2. **Ledger projection**: map preview output to mission/taskpool event projection, still read-only.
3. **Human handoff adapter**: dry-run approval nodes into Human Intervention Packet schema.
4. **Receipt/resume model**: add per-node receipts and replay validation against hashes.
5. **Dashboard rendering**: read-only graph projection from receipts/events.
6. **Only after human authorization**: consider single local sandbox execution of a non-credentialed dummy workflow node. No production scheduler takeover.

## 6) Closeout judgment for current task

The source-review acceptance criteria are substantively satisfied by the intake artifact plus this gap mapping artifact. However, current taskpool frontmatter still has `certification_status: not_certified`, `ratification_artifact: proof:ratification-pending`, and multimodel result `PASS_ADVISORY_ONLY / CONTINUE_LOOP`. Therefore the safe lifecycle judgment is: keep/leave review until deterministic closeout tooling or explicit human direction handles advisory-only ratification semantics. Do not mark done solely from advisory multimodel output.
