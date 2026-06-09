# MAGMA 多图谱智能体记忆架构截图 intake / gap-analysis

Source artifact: `/Users/charles/.hermes/image_cache/img_2377d6e07be9.jpg`
Captured from user-provided mobile screenshot. No official paper/repository URL was present in the screenshot.

## OCR 摘要

标题：`MAGMA：多图谱智能体记忆架构`

副标题：`突破大模型长上下文推理瓶颈的结构化方案`

Banner 显示来源标识：The University of Texas at Dallas、University of Florida。

三项主张：
- `4维正交图谱（四重逻辑维度）`
- `降低 95% Token 消耗（极致效率）`
- `双流读写机制（零延迟交互）`

正文可见内容：
- `第7集｜MAGMA：四维图谱突破AI记忆瓶颈`
- 目标问题：大语言模型在长对话中注意力稀释、逻辑断层。
- 架构说法：将记忆解构为语义、时间、因果、实体四个正交维度。
- 检索说法：三层解耦方案实现信息精准检索。
- 交互说法：双流读写机制保障交互零延迟，同时异步推理模块动态生成逻辑路径。
- 效果说法：复杂多跳推理任务中降低 95% token 消耗，并显著减少模型幻觉。
- 来源账号：`Agent创世纪`，日期 `4月1日`。

## Source verification note

Initial web/GitHub searches for exact phrases did not find an obvious official MAGMA repository/paper. Treat the screenshot as an **unverified secondary social-media explanation** until an official arXiv/paper/repo/source is located.

Do not accept the `95% token reduction` or `zero latency` claims as fact without primary evidence and benchmark protocol.

## Potential value for Hermes / local brain / taskpool

The useful abstraction is not the exact MAGMA claim, but the memory/indexing pattern:

1. Multi-graph memory index
   - semantic graph: concepts, topics, embeddings, summaries
   - temporal graph: session/task chronology, lifecycle events, evidence timestamps
   - causal graph: decisions, blockers, dependency transitions, proof chains
   - entity graph: projects, repos, people, tools, tasks, files, models, providers

2. Dual-stream read/write
   - foreground/read path: zero- or low-latency retrieval for active task context
   - background/write path: asynchronous consolidation, graph edge extraction, dedup, evidence normalization
   - aligns with user's event-driven preference: trigger on `task.created`, `task.status_changed`, `evidence.added`, `session.closed`, not cron polling.

3. Token efficiency target
   - replace dumping long transcripts/tasks into prompts with graph-selected context packets.
   - measure with real before/after: prompt tokens, retrieval hit rate, hallucination/regression rate, task closeout correctness.

4. macOS binding acceptable
   - Since user explicitly accepts macOS binding, local-first implementation may use macOS-native storage/indexing/notification surfaces if useful.
   - However architecture should keep graph schema and ingestion contracts portable; macOS-specific UI/daemon pieces must remain adapters, not SSOT.

## Proposed task framing

Create a taskpool evolution item to verify MAGMA source and evaluate a Hermes-compatible multi-graph memory architecture. The task should produce a grounded report and implementation plan, not auto-install or adopt any external code.

Acceptance should require:
- official source discovery or explicit falsification/secondary-source classification;
- mapping MAGMA dimensions to Hermes memory/session/taskpool evidence model;
- proposed graph schema and event-driven ingestion pipeline;
- read/write-path latency and token-savings benchmark design;
- comparison with current Hermes memory/session_search/taskpool/evidence-spine;
- safety/anti-drift boundaries: no unverified 95% claim, no auto-running third-party code, no arbitrary file indexing outside allowlist/sandbox.
