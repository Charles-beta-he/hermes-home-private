# Taskpool / Chat Rules Convergence — Multi-model Review

Date: 2026-05-25
Scope: Hermes taskpool execution workers launched with `hermes chat --ignore-rules` versus normal chat rule loading.

## Evidence

- Chat prompt stack: `agent/system_prompt.py::build_system_prompt_parts` loads identity, tool guidance, skills, context files, memory/profile unless skipped.
- CLI boundary: `cli.py` maps `--ignore-rules` to `skip_context_files=True` and `skip_memory=True`.
- Execution worker: `~/.hermes/scripts/agent_team_controller.py::delegate_to_worker` launches `hermes chat ... --ignore-rules`.
- Taskpool handoff: `~/.hermes/scripts/brain_task_orchestrator.py::render_*_handoff` injects Brain Overlay Contract and Project Profile but not a canonical user/Hermes rule digest.

## Model positions

### MiMo
- Keep worker isolation but add compact rules digest to execution-worker prompt.
- Do not use full memory injection.
- Keep `--ignore-rules` for smoke/consult style probes.

### DeepSeek
- Use a two-layer digest: global invariant rules plus task/review-specific rules.
- Inject via task metadata/prompt/env, scoped to the worker lifecycle.
- Test that execution workers receive the digest while review/smoke isolation remains clean.

### Gemini
- Preserve process/workdir/session isolation for multi-model workers.
- Treat `--ignore-rules` as prompt-layer cleanup only; it must never bypass tool/sandbox/proof gates.
- Add prompt/payload isolation tests and state pollution tests where possible.

### GPT-5.5
- Avoid a raw boolean spreading through runtime; prefer explicit runtime kind/scope eventually.
- `ignore_chat_rules` must never affect permission/tool/proof/lifecycle/multimodel truth gates.
- Distinguish task_worker execution from multimodel_review and smoke.

### Claude Code
- The first-pass digest restores global safety invariants, but it does **not** by itself solve the user's main complaint: "I do not want to say the same requirement once in taskpool and again in chat."
- Root cause: `build_worker_context()` included title/id/project/boundary but did not include task-level requirement fields such as `body`, `acceptance_criteria`, `red_lines`, `non_goals`, `workflow_contract`, and `evidence_refs`.
- Correct interpretation of isolation: workers should not inherit chat persona, arbitrary memory, or unrelated conversation history; workers **must** inherit the concrete requirements already persisted into the task record.
- Minimal fix: add a deterministic task-spec snapshot section. Chat says it once, taskpool stores it once, worker receives a compact snapshot once.
- Keep caps/truncation on every injected field to avoid token blowup and prevent reintroducing full chat history through the back door.

## Synthesis

Implement the smallest safe step now:
1. Add a compact canonical execution rules digest builder in repo code, sourced from stable local Hermes files when available:
   - `~/.hermes/AGENTS.md`
   - selected durable memory/profile files if readable later, but avoid full memory dump in this slice.
2. Inject the digest into execution-worker prompts in `agent_team_controller.py` before launching `hermes chat --ignore-rules`.
3. Add a compact task-level requirements snapshot sourced from the task record:
   - `body` / `description`
   - `acceptance_criteria`
   - `red_lines`
   - `non_goals`
   - `evidence_refs`
   - `workflow_contract`
4. Do not inject these sections into consult_models / smoke / independent review paths in this slice unless explicitly scoped later.
5. Add tests proving:
   - digest contains the key execution-worker invariant and source text;
   - task-spec snapshot preserves user requirements already captured in the task;
   - `delegate_to_worker` prompt contains both digest and task-spec snapshot while command still uses `--ignore-rules`;
   - no broad CLI behavior is changed.

## Boundary for this pass

Stop before a broad CLI/runtime-kind migration. That needs a larger contract and could break existing `hermes chat --ignore-rules` workflows. The current pass closes the unsafe execution-worker gap with targeted tests: global safety digest, task-spec requirement inheritance, and scoped environment capability handoff for skills/MCP/local-brain context.

## Claude Code 复审补充：task-level requirements snapshot（2026-05-25）

Claude Code 独立复审指出：第一阶段 `Canonical Rules Digest` 只修复了全局宪法/安全红线漂移，但未完全解决用户痛点“同一个要求任务池修一次、chat 再说一次”。正确边界不是让 worker 继承完整 chat persona/memory/history，而是把已经沉淀到 task record 的任务级 SSOT 稳定传给 execution worker：`body` / `description` / `acceptance_criteria` / `red_lines` / `non_goals` / `evidence_refs` / `workflow_contract`。

因此新增 `TASK-SPEC REQUIREMENTS SNAPSHOT`：执行型 worker 在保留 `--ignore-rules` 隔离的同时，必须读取 task record 内的具体需求、验收、红线、证据要求，并视作任务局部 source of truth；consult/review/smoke 等独立评审路径仍保持隔离。

## Claude Code + 多模型复审补充：skills / MCP / 本地大脑环境能力桥（2026-05-25）

用户进一步追问 chat 环境中的 skills、MCP、本地大脑是否同步支持。复审结论：需要支持，但必须是“scoped capability handoff”，不能把完整 chat 环境、memory、persona、无关历史复制给 worker。

已落地 `ENVIRONMENT CAPABILITY PACK`：

- `required_skills` / `skills`：从 task record 与 project profile 合并、去重，并在 delegate 命令中显式追加 `--skills <name>`，即使保留 `--ignore-rules` 也能加载任务所需 skill。静态验证 Hermes CLI 中 `--ignore-rules` 只控制 `skip_context_files/skip_memory`，显式 `parsed_skills` 会独立构建并合并到 `system_prompt`。
- `required_mcp_tools` / `mcp_tools`：只注入任务需要的 MCP tool 名称与已配置 MCP server 名称（names only），不输出 command/env/token/url/header 等配置值；worker 仍必须真实调用工具，不得伪造 MCP 结果。
- 本地大脑：只注入 task/profile 中已策展字段（如 `brain`、`brain_profile`、`brain_contract`、`brain_context`、`local_brain_refs`），并做长度截断；不导入原始 chat history 或全量 memory。
- 隔离边界：execution worker 支持上述能力桥；consult/review/smoke/多模型评审仍保持纯净隔离。

验证与边界评审：

- TDD 覆盖 secret negative、MCP fallback parser 深度、disabled MCP 排除、skills 合并去重、brain context 截断、空上下文不注入、delegate argv 保留 `--ignore-rules` 且追加 `--skills`、Hermes CLI `--skills` 与 `--ignore-rules` 静态交互。
- pytest：`8 passed`。
- py_compile：PASS。
- `brain_task_orchestrator.py selfcheck --json`：PASS。
- Claude Code 初审提出 secret/fallback/runtime 验证缺口，补测后复审为 `approve_with_minor`，剩余仅静态测试耦合源码布局等非阻断项。
- MiMo 复审：`approve`，无阻断，确认 names-only MCP、scoped skills、brain truncation、no fake MCP 规则边界正确。
- GPT 复审：`approve`，无 finding。
