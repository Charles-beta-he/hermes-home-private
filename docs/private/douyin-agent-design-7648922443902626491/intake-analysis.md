# Douyin 图文：后端转 Agent 开发 / Agent 设计结构 intake

Captured: 2026-06-14

## Source

Original user share text:

> 8.99 复制打开抖音，看看【搁浅（看我主页置顶）的图文作品】分享一下我的agent设计思路。# 后端开发 # ... https://v.douyin.com/cGiRVs06_yw/ 06/17 :6pm GVy:/ i@p.dn

Resolved URL:
- Short: https://v.douyin.com/cGiRVs06_yw/
- Resolved mobile/share: https://www.iesdouyin.com/share/note/7648922443902626491/?from_ssr=1
- Canonical: https://www.douyin.com/note/7648922443902626491

Extracted metadata from page/router data:
- aweme_id: `7648922443902626491`
- author: `搁浅（看我主页置顶）`
- author signature: `某大厂AI工程师，分享一些AI知识 / 👇学习路径➕笔记➕项目`
- description: `分享一下我的agent设计思路。#后端开发 #agent框架 #Agent开发 #程序员 #大模型`
- create_time: 2026-06-08 (router timestamp `1780903536`)
- statistics at capture: 992 likes, 9 comments, 172 shares, 1217 collects
- image count: 7
- downloaded images: `/Users/charles/.hermes/docs/private/douyin-agent-design-7648922443902626491/image_0.webp` ... `image_6.webp`
- raw router summary: `/Users/charles/.hermes/docs/private/douyin-agent-design-7648922443902626491/router_item.json`

## OCR / visible content summary

### Image 0 — project structure

Title: `后端转Agent开发 / 我的Agent（智能体）设计结构`

Proposed `agent-project/` directories:
- `01_planner/` 规划与任务管理: `goal.md`, `plan.md`, `task-breakdown.md`, `roadmap.md`
- `02_memory/` 记忆系统: `long-term-memory.md`, `short-term-memory.md`, `entity-memory.md`, `knowledge-graph.md`
- `03_tools/` 工具系统:
  - `api-tools/`: `search.md`, `weather.md`, `calculator.md`, `news.md`
  - `code-tools/`: `code-executor.md`, `file-reader.md`, `terminal.md`
  - `custom-tools/`: `db-query.md`, `notion.md`, `slack.md`
- `04_knowledge/` 知识库与检索: `documents/`, `embeddings/`, `vector-store.md`, `rag-pipeline.md`, `index-strategy.md`
- `05_agent_core/` Agent 核心配置: `agent.md`, `roles.md`, `persona.md`, `workflow.md`, `system-prompt.md`, `prompt-template.md`
- `06_evaluation/` 评估与测试: `eval-metrics/`, `test-cases.md`, `benchmarks.md`, `result-analysis.md`
- `07_observability/` 观测与监控: `logs/`, `traces.md`, `monitoring.md`, `alert-rules.md`
- `08_deployment/` 部署与运维: `docker/`, `k8s/`, `deploy.md`, `env.example`
- `09_examples/` 示例与用例: `use-cases/`, `demo-flows.md`
- `10_docs/` 文档与知识库

Right-side explanation:
1. 规划与任务管理：定义目标、拆解任务、制定执行计划。
2. 记忆系统：短期/长期/实体记忆，支持上下文持续与个性化记忆。
3. 工具系统：集成 API、代码、自定义工具，扩展能力边界。
4. 知识库与检索：RAG/检索，提高准确性与可靠性。
5. Agent 核心配置：角色、人设、系统提示词、工作流、Prompt 模板。
6. 评估与测试：指标、测试用例、持续评估和优化迭代。
7. 观测与监控：运行状态、性能、异常。
8. 部署与运维：配置、环境、容器化、CI/CD。
9. 示例与用例：典型场景、流程示例、Prompt 示例。
10. 文档与知识库：架构设计、最佳实践、FAQ、版本记录。

### Image 1 — architecture flow

Doc title: `从0-1打造商用 AI Agent（智能体）- 飞书云文档`

Architecture design principles:
- 模块化：职责清晰，易于扩展
- 可迭代：持续优化，快速反馈
- 可观测：全链路监控与告警
- 安全可控：权限控制，数据保护
- 可复用：沉淀资产，提升效率

Flow:
1. Query：用户输入任务
2. 请求 LLM：Query + 历史上下文发送给大模型
3. LLM 思考与决策：生成中间步骤
   - Thinking：分析问题、理解意图、拆解任务
   - Action：决定调用哪个 Function
   - Action Input：生成调用 Function 的参数
4. Observation：Function 调用执行，结果返回 Agent
5. Final Answer：整合信息，生成最终答案
6. 交互展现：智能卡片结果 / 自然语言结果

Functions library examples:
- 预约会议
- 取消会议
- 查找文档
- 澄清问题

Flow key: 接收任务 → 请求 LLM → 决策步骤 → 调用工具 → 获取结果 → 输出答案；循环迭代直到最终答案。

### Images 2-6 — implementation toy example

Implementation steps:
- Step 1: set up Python dependencies: `requests`, `json`, `termcolor`, `dotenv`; install via `pip install requests termcolor python-dotenv`.
- Step 2: define model class `OllamaModel`, using local Ollama API endpoint `http://localhost:11434/api/generate`.
- Step 3: create basic tools as Python functions, e.g. calculator and string reverse.
- Step 4: build `ToolBox`, storing function names and docstrings, returning descriptions to the agent.
- Step 5: create `Agent` class; agent thinks, selects tool, and executes. Prompt asks model to output JSON containing `tool_choice` and `tool_input`; includes rules for `no tool`, `reverse_string`, `basic_calculator`.
- Step 6: run agent loop in CLI; initialize tools, model service, model name `llama2`, stop token, then prompt user until `exit`.

## Engineering interpretation

The post is a beginner-friendly backend-to-Agent tutorial, not a production-grade framework artifact. Its durable value is the **teaching scaffold**:

- split Agent project into planner/memory/tools/knowledge/core/eval/observability/deploy/examples/docs;
- use a ReAct-like loop: Query → LLM → Thought/Action/Input → Function → Observation → Final Answer;
- make tool registry explicit through function docs;
- treat memory, RAG, evaluation, observability, and deployment as first-class directories instead of afterthoughts.

Compared with Hermes, this is much simpler than the existing taskpool/Mission/Workflow Kernel, but it can be absorbed as:

1. **Agent Builder onboarding scaffold** — a beginner-facing template for users transitioning from backend development to Agent design.
2. **Workflow Pack packaging checklist** — ensure every pack declares planner, memory, tools, knowledge, core prompt, eval, observability, deployment, examples, docs.
3. **Agent Card / Skill Pack metadata baseline** — project folders map to explicit capability declarations and safety boundaries.
4. **Toy ReAct fixture** — a small local fixture for testing tool-selection JSON, tool registry docs, and no-tool fallback behavior, without external side effects.

## Anti-drift / red lines

- Do not treat the Douyin post as a canonical production framework.
- Do not install or run the author's code; no repository was linked from the post.
- Do not use this to replace Hermes taskpool/Mission/Workflow Kernel architecture.
- Do not downgrade Hermes evidence gates to a simple ReAct loop.
- Do not connect terminal/code executor/weather/search tools from the toy example to real systems without permission gates.
- Vector/RAG remains candidate context only, never taskpool SSOT or proof authority.

## Recommended task framing

Create a P2 evolution task:

`Douyin Agent设计结构吸收：将后端转Agent项目脚手架转为 Hermes Agent Builder / Workflow Pack 模板`

Acceptance target:
- Produce a Hermes Agent Builder / Workflow Pack scaffold template with modules:
  planner, memory, tools, knowledge, agent_core, evaluation, observability, deployment, examples, docs.
- Map each module to Hermes existing surfaces: taskpool, local-brain, skill graph, Workflow Pack, Agent Card, evidence/proof gates.
- Include a minimal safe ReAct toy fixture only as documentation/test fixture, not as production executor.
- Preserve safety gates for tool execution, terminal/code tools, external APIs, RAG/vector retrieval, and deployment.
