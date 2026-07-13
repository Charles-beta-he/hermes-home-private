# Formulasearch: Obsidian Canvas × Agent 协作 — 证据核验、Hermes 缺口与吸收落地

Date: 2026-07-13
Status: local reusable landing complete; runtime Canvas bridge intentionally not opened

## Objective model

- Goal: 核验 X 文章的核心论点，区分事实、作者推演和产品营销，并把可复用部分吸收到 Hermes 的复杂任务工作流。
- Non-goals: 不安装 Obsidian/社区插件；不把 Canvas 直接设为项目 SSOT；不从社媒文章直接修改全局系统提示词、任务池运行时或外部系统；不声称已具备双向可视化 Canvas UI。
- Constraints: 复杂任务必须保留当前状态、来源、证据、权限与回滚；线性聊天仍保留为快速交流入口；现有脏工作树不得被覆盖或混入本次提交。
- Chosen path: 公开原文提取 → 一手研究/官方规范/项目 README 核验 → Hermes 能力映射 → 现有 `workflow-capability-graph` umbrella 下新增 class-level reference → 读回、校验与 scoped commit。
- Rejected path: 直接安装 Canvas LLM/Cannoli，或把 Obsidian Canvas 当执行控制面。理由是第三方插件拥有 API key、Vault 读写和 HTTP side-effect surface，且文章没有提供足够的代码安全与权限证据。

## Source evidence

Canonical intake:

- `/Users/charles/.hermes/workflows/intake/2026-07-13-formulasearch-obsidian-canvas-evidence.json`

Article:

- Status: <https://x.com/formulasearch/status/2076288803786887245?s=46>
- X Article: <https://x.com/i/article/2076285136212013056>
- Title: `还在用原始对话框？教你用 Obsidian Canvas 与 Agent 协作`
- Author: 阿哲Phil (`@Formulasearch`)
- Public extraction: anonymous X SSR metadata plus `TweetResultByRestId` GraphQL with `withArticlePlainText`
- Extracted plain text: 8,107 characters, 266 lines
- SHA-256: `7102cf590e9590d33d38663dac5b59b02624384d8799e9bb727b42e1afdf2b0a`

Primary/official verification sources:

1. Sensecape, UIST 2023: <https://arxiv.org/abs/2305.11483>
2. CanvasConvo, 2026 working draft: <https://arxiv.org/abs/2605.15848>
3. JSON Canvas 1.0 spec: <https://jsoncanvas.org/spec/1.0/>
4. Obsidian JSON Canvas repository: <https://github.com/obsidianmd/jsoncanvas>
5. Cursor Canvas product article: <https://cursor.com/blog/canvas>
6. Microsoft 365 Copilot Wave 2 / Pages: <https://www.microsoft.com/en-us/microsoft-365/blog/2024/09/16/microsoft-365-copilot-wave-2-pages-python-in-excel-and-agents/>
7. Canvas LLM: <https://github.com/farlenkov/obsidian-canvas-llm>
8. Cannoli: <https://github.com/DeabLabs/cannoli>

## Article thesis

The article's strongest distinction is:

```text
Conversation history tells us what was said.
A project needs to tell us what is true now.
```

It proposes this division of labor:

```text
Chat: immediate communication
Canvas: structure and current state
Markdown/files: detailed content and memory
Agent: reading, execution and updates
```

The article then turns Canvas from a final diagram into a round-trip workbench:

```text
chat → structure → human direct manipulation → agent reread → execution → state writeback
```

This is directionally stronger than merely adding a mind-map export. It treats the visual artifact as part of the control loop.

## What the evidence supports

### Sensecape

Supported:

- The 2023 UIST paper explicitly frames linear conversation as inadequate for complex nonlinear information tasks.
- Sensecape combines Canvas and hierarchy views, multilevel abstraction, semantic zoom and semantic dive.
- The within-subject study reports broader topic exploration and more hierarchical organization.

Limits omitted or underweighted by the article:

- Novelty and limited exposure may bias perceived usefulness.
- Some users found the hierarchy view complex or overwhelming.
- The paper identifies visual clutter, context-switching cost and learning curve as real design problems.
- The study supports exploration/sensemaking, not a general claim that Canvas improves every project outcome.

### CanvasConvo

Supported:

- The fetched arXiv paper reports a five-day field study with 24 participants.
- It reports mean Canvas sessions of 34.1 minutes versus 13.0 minutes for chat sessions.
- Users created and revisited branches, used timeline navigation, and treated chat and canvas as complementary interfaces.
- The paper itself says the added structure introduced navigation, view-switching and branch-relationship challenges.

Important correction:

- The PDF identifies itself as an unpublished working draft. The duration comparison is observational telemetry, not causal proof that Canvas produced better work.

### Cursor Canvas

Supported as a vendor product claim:

- Cursor describes canvases as durable artifacts living beside terminal, browser and source control.
- It describes nonlinear/data-heavy uses including incident response dashboards, PR review, eval analysis and autoresearch experiments.
- It uses React-based first-party visual components and allows skills to teach agents canvas patterns.

Boundary:

- This is vendor-authored product evidence, not an independent effectiveness study.

### JSON Canvas / Obsidian

Supported:

- JSON Canvas is an open format whose top level contains `nodes` and `edges`.
- Nodes can be text, file, link or group and have explicit IDs, coordinates, dimensions and optional color.
- This makes `.canvas` files machine-readable and writable without screenshot OCR.

Missing from the article's optimistic interpretation:

- JSON Canvas does not define canonical project-state authority.
- It does not supply revision control, provenance, permissions, conflict resolution, lifecycle gates or transactional side-effect semantics.
- Position and color are insufficient for critical machine semantics unless the project adds a protocol.

### Community plugins

Supported by project READMEs:

- Canvas LLM offers visual branching, per-node model selection and file/web inputs; it requires users' own provider keys.
- Cannoli allows Canvas-defined LLM scripts, Vault read/write, variables, loops/branches and HTTP requests.

Risk boundary:

- These are executable community plugins with credential, Vault and network side-effect surfaces. Popularity and an open license do not prove safe installation. No plugin was installed in this absorption.

## Critical analysis

### What the article gets right

1. **History is not state.** A complete transcript can still fail to identify the active decision, superseded option, blocker or next action.
2. **Complex work is graph-shaped.** Goals, artifacts, tasks, dependencies, risks and evidence are not a single sequence.
3. **Direct manipulation can be high-bandwidth feedback.** Moving or reconnecting a node can be clearer than writing another corrective paragraph.
4. **Canvas and Markdown should be layered.** Structure belongs in the graph; details and evidence remain in files.
5. **One infinite canvas is a failure mode.** Hierarchical/layered views are required.
6. **Permissions matter.** The article correctly warns against unlimited Agent modification rights.
7. **Chat remains useful.** The right target is multimodal collaboration, not replacing every interaction with a graph.

### What must be amended before engineering adoption

1. **Canvas is a projection, not automatic truth.** A visual file becomes trustworthy only after canonical ownership, schema, revision, validation, conflict and readback rules are defined.
2. **Direct manipulation is not direct understanding.** An edit must become a typed `ChangeIntent`, pass authority and consistency gates, update canonical state, then be reprojected and read back.
3. **Layout is not semantics.** Proximity, vertical position and color help humans but cannot safely encode dependencies, lifecycle states or authority alone.
4. **Delete cannot mean immediate destruction.** Node deletion should default to a tombstone/change request; dependencies, ownership and evidence must be checked.
5. **Tasks and evidence are missing from the compact formula.** Governed execution needs `Chat + Canvas + Files + Tasks + Agents + Evidence + Gates`.
6. **Branch inheritance needs explicit semantics.** A branch must say which revision and constraints it inherits; otherwise the graph recreates the same context ambiguity it was meant to solve.
7. **Canvas maintenance has a cost.** The pattern should trigger only when state complexity exceeds the cost of maintaining the projection.

## Hermes capability gap map

| Capability | Current Hermes state | Gap |
|---|---|---|
| Separate event history from current state | Strong: session history, todo, plans, project profiles, progress ledgers, taskpool lifecycle and SSOT | Small; behavior exists but is distributed across surfaces |
| Persistent detailed artifacts | Strong: Markdown/files, evidence bundles, skills, project workspaces | Small |
| Typed task/dependency/authority model | Strong in capability graph, taskpool and AgentOS governance | Small |
| Human-editable spatial current-state view | No unified standard Canvas surface | Large |
| Bidirectional Canvas round trip | No standard Canvas diff → ChangeIntent → canonical apply → reprojection loop | Large |
| Visual direct manipulation as feedback | Possible only by editing files/UI manually; not a first-class Hermes interaction | Large |
| Multi-agent shared visual projection | Taskpool/dashboard exists, but not a common editable graph | Medium-large |
| Evidence attached to visual nodes | Evidence ledgers exist; no standard Canvas binding | Medium |
| Hierarchical/semantic zoom | Can generate layered diagrams, but no persistent interactive zoom state | Medium-large |
| Permissioned visual zones and conflict resolution | Governance concepts exist; no Canvas-specific implementation | Medium |
| Real execution and verification | Stronger than the article's examples: tools, tests, browser/API/readback, authority gates | Hermes advantage |

Summary: Hermes already has much of the **semantic/control-plane core**, but lacks the article's **human-facing spatial collaboration surface and safe bidirectional bridge**.

## Absorbed class-level rule

For complex work:

```text
Do not treat the conversation transcript as the current project model.
Maintain a canonical current-state graph/ledger.
Expose human-readable projections when useful.
Treat Canvas edits as proposed typed deltas, not immediate authority.
Validate, apply, reproject and read back before claiming alignment.
```

The reusable procedure is landed at:

- `/Users/charles/.hermes/skills/software-development/workflow-capability-graph/references/shared-canvas-current-state-projection.md`

The class-level lesson was also normalized, challenged and validated in the proposal-only experience ratchet:

- Atom: `/Users/charles/.hermes/experience-ratchet/atoms/hermes-self-optimization-0e33aa534a4d.json`
- Proposal: `/Users/charles/.hermes/experience-ratchet/proposals/proposal-hermes-self-optimization-0e33aa534a4d-20260713T081028Z.json`
- State: `promoted_candidate`; write policy remains `proposal_only_no_direct_mutation`

It defines:

- event history versus current state;
- canonical graph versus Canvas projection;
- typed node/edge contracts;
- Canvas diff → `ChangeIntent` round trip;
- human/agent ownership and deletion policy;
- layered views and semantic zoom;
- side-effect separation;
- applicability, anti-conditions, falsifiers and verification checklist.

## Why runtime/plugin implementation is not included

The article justifies a reusable workflow rule, but does not by itself justify installing Obsidian plugins or modifying the Hermes runtime. A production bridge would need:

1. a canonical state schema and stable IDs;
2. deterministic JSON Canvas projection;
3. Canvas diff classification that separates layout-only and semantic edits;
4. revision/conflict handling;
5. authority zones and soft-delete behavior;
6. task/evidence adapters;
7. negative tests proving that layout edits cannot trigger side effects;
8. UI/readback acceptance;
9. a separate exact authorization for any plugin installation, provider credential or HTTP execution.

Until those conditions exist, Hermes should apply the semantic rule through its existing SSOT/progress-ledger/capability-graph surfaces rather than pretend that a bidirectional Canvas runtime is complete.

## Converge matrix

| Claim | Evidence | Status | Remaining gap |
|---|---|---|---|
| X article was read beyond preview | anonymous GraphQL, 8,107 chars/266 lines, SHA-256 in intake | pass | X may update engagement metadata; article body was captured at stated time |
| Core research claims were checked | arXiv metadata and fetched PDFs for Sensecape/CanvasConvo | pass | CanvasConvo is still an unpublished working draft |
| JSON Canvas is machine-readable | official spec and repository | pass | no governance semantics supplied by the format |
| Plugin capabilities are real | project READMEs and GitHub metadata | pass with boundary | no source-code security audit or installation test |
| Hermes gaps were mapped | current skill/runtime surfaces compared above | pass | no interactive Canvas UX exists |
| Reusable behavior was absorbed | skill reference created and linked from umbrella skill | pass | runtime bridge intentionally not claimed |
| External/destructive side effects did not occur | no installation, credential entry, X interaction, publish or external write | pass | none |

## Closure

Closure state: `done` for evidence analysis and class-level workflow absorption.

Not claimed:

- production-ready Obsidian/JSON Canvas integration;
- installed or audited Canvas LLM/Cannoli runtime;
- bidirectional visual state UI;
- causal proof that Canvas improves all task outcomes;
- permission for external writes or executable Canvas nodes.
