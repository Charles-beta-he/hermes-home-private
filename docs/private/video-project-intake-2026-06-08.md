# 视频号项目 intake：OculOS / career-ops / CopilotKit / Qdrant

Date: 2026-06-08

## Sources inspected

### 1. WeChat 视频号：AEE4EevOG9
- URL: https://weixin.qq.com/sph/AEE4EevOG9
- Visible title: “别再死磕Computer Use了，这个方案又轻又快又便宜”
- Author/date: 耳朵不懂AI, 2026-06-06
- Visual/OCR project name: OculOS
- Mapped repo: https://github.com/huseyinstif/oculos
- Repo description from GitHub: “If it's on the screen, it's an API. Control any desktop app via REST + MCP. Rust.”
- Key repo facts from README: REST API + MCP server, single Rust binary, reads OS accessibility tree, exposes UI elements as JSON endpoints, supports Windows UIA / Linux AT-SPI2 / macOS AXUIElement, no screenshots/pixel coords/GPU/cloud required.

### 2. WeChat 视频号：AfntcVVcwo
- URL: https://weixin.qq.com/sph/AfntcVVcwo
- Visible text: career-ops 是开发者 santifer 开源的一套本地优先求职自动化系统；构建在 Claude Code 之上；内置 14 种技能模式和 Go 看板；自动扫描 Greenhouse / Lever / Ashby；生成 ATS 友好简历；并行 offer 打分。
- Author/date: stan的AI日报, 2026-06-07
- Mapped repo: https://github.com/santifer/career-ops
- Repo facts: ~49.9k stars at inspection; AI-powered job search pipeline built on Claude Code, Node.js + Go dashboard + Playwright; data contract separates user layer from system layer; human review before application submission.

### 3. WeChat 视频号：AJ1vTYIGFi
- URL: https://weixin.qq.com/sph/AJ1vTYIGFi
- Visible text: “Claude Artifacts 彻底开源了！生成式 UI 不再是大厂特权！CopilotKit ... 三条路径：受控模式、声明式 A2UI、开放式 HTML/Excalidraw；双向同步、Human-in-the-Loop、AG-UI 协议。”
- Author/date: 开发者Hailey, 2026-06-07
- Mapped repo: https://github.com/CopilotKit/CopilotKit
- Repo facts: ~33.8k stars at inspection; frontend stack for agents and Generative UI; React/Angular/Vue/React Native/Slack/Teams; AG-UI protocol; shared state, HITL, runtime/agent integration.

## Qdrant / vector DB check

Code search across cloned repos:
- OculOS: no Qdrant/vector DB/RAG dependency in repo; role is deterministic UI accessibility/control, not memory retrieval.
- career-ops: no Qdrant dependency in core; vector DB references are examples/company targets or CV wording (Pinecone, pgvector, Chroma) rather than infrastructure.
- CopilotKit: qdrant/pinecone/chroma/weaviate/milvus appear as optional dependencies in transitive LangChain-style packages and examples; CopilotKit itself is UI/runtime/protocol layer, not a vector DB.

Interpretation for Hermes:
- Qdrant/vector DB should not be treated as replacing taskpool, Kanban, or canonical ledger.
- Suitable role: semantic retrieval over evidence, task notes, docs, screenshots/transcripts, user career artifacts, and reusable project context.
- Non-role: lifecycle authority, done/blocked state, proof gates, deterministic replay source, or canonical task identity.

## Suggested taskpool decomposition

1. OculOS: evaluate MCP/REST accessibility-tree control as a deterministic alternative/complement to screenshot Computer Use for Hermes external-control/browser/desktop tooling.
2. career-ops: adapt useful job-search pipeline patterns into the user's career workflow and Hermes skills without copying personal-data assumptions.
3. CopilotKit/AG-UI: evaluate Generative UI / AG-UI patterns for Hermes taskpool/control-plane UI, evidence dashboard, and HITL surfaces.
4. Qdrant/vector DB: design bounded semantic retrieval layer for Hermes memory/evidence/docs while preserving taskpool SSOT and deterministic proof gates.
