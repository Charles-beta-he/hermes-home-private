# Douyin intake — Agent 记忆系统（Memory）选型 + 设计模式 + 核心分类

- Source short URL: `https://v.douyin.com/_m3NZIQf8Dg/`
- Canonical: `https://www.douyin.com/note/7650926105133583652`
- IES extraction URL: `https://www.iesdouyin.com/share/note/7650926105133583652/`
- Author: 青山雨 (`20230620HL`)
- Description: `Agent 记忆系统（Memory）。选型 + 设计模式 + 核心分类，若有不对的地方，希望在评论区交流#备忘录文字 #实习生 #agent #Memory #大模型`
- Published: 2026-06-14 01:01:03
- Stats at extraction: 257 likes, 289 collects, 15 shares, 2 comments
- Local evidence: `/Users/charles/.hermes/docs/private/douyin-agent-memory-system-7650926105133583652/`

## Media evidence

- `router_item.json` — extracted Douyin metadata
- `image_0.webp` ... `image_2.webp` — original images
- `contact_all.jpg` — OCR/contact sheet

## OCR / visible content

### Image 0 — 自建 Memory 选型决策树

Title: `自建 Memory 选型决策树`

Visible tree:

```text
跨会话记忆？
├─ 否 → 直接用对话历史数组
└─ 是 → 记忆量规模？
   ├─ 小（<100 条）→ JSON/SQLite 文件存储
   ├─ 中（100-10000 条）→ 结构化数据库 + 关键词检索
   └─ 大（>10000 条）→ 向量数据库 + 语义检索
```

### Image 1 — 四大通用设计模式

Title: `四大通用设计模式`

Visible bullets:

```text
滑动窗口 + 摘要：近期原文保留 + 早期历史压缩 → 绝大多数场景（推荐）
分层记忆：短期对话 + 长期向量检索 + 实体键值存储 → 生产级精准记忆
工具驱动记忆：Agent 自主调用工具存 / 取记忆 → 复杂 Agent 自主管理
反思循环：定期分析对话，提取信息存入长期记忆 → 持续沉淀偏好 / 经验
```

### Image 2 — Memory 四大核心分类

Title: `Memory 四大核心分类`

Visible bullets:

```text
短期记忆：单次会话内，上下文消息列表 → 保存当前对话记录
长期记忆：跨会话持久化，外部数据库 / 向量库 → 存储用户偏好、学习经验
实体记忆：跨会话，结构化存储 → 记录人名、项目名、团队成员等实体
情景记忆：跨会话，检索式存储 → 记住具体事件（如上次调试 bug 的方法）
```

## What it really is

This is a compact **memory system design cheat sheet**. It is not a new tool or implementation; it is a selection framework for deciding how much memory infrastructure an Agent needs.

Its core value is proportionality:

```text
Do not build vector memory when a sliding window, summary, JSON, SQLite, or structured DB is enough.
```

## Transferable Hermes patterns

### 1. Memory complexity should scale with actual need

Hermes should keep a memory decision rule similar to:

```text
No cross-session need -> use current conversation/context only.
Small durable facts -> memory/user profile.
Session recall -> session_search / FTS.
Project workflow facts -> project profile or taskpool evidence.
Reusable procedure -> skill.
Large semantic corpus -> explicit RAG/vector project with governance.
```

This prevents over-building “vector memory” for every problem.

### 2. Four memory classes map well to Hermes boundaries

| Source class | Hermes boundary |
|---|---|
| Short-term memory | active conversation context / compacted context |
| Long-term memory | `memory` / `user profile` for stable durable facts only |
| Entity memory | project profiles, scoped profiles, structured docs |
| Episodic/contextual memory | `session_search`, taskpool evidence, proof artifacts |

The important distinction: not all memories belong in the global memory store.

### 3. Design pattern selection should be explicit

The “four design patterns” can be turned into a Hermes memory routing policy:

- Sliding window + summary: default conversation compaction.
- Layered memory: global durable facts + project facts + session recall + evidence docs.
- Tool-driven memory: only with guarded memory writes; never let the model autonomously save WIP/status.
- Reflection loop: useful only if it classifies outputs into memory/skill/profile/task/evidence/do-not-save.

### 4. Strong anti-ghost rule

The note makes “反思循环” sound attractive, but Hermes must guard it:

```text
reflection != automatically save everything
```

Any reflection loop must avoid stale ghosts:

- Do not save task progress as durable memory.
- Do not save temporary user intent as stable profile.
- Do not save secrets.
- Require evidence and classification before writing.

## Risks / redlines

- The post is a high-level cheat sheet, not validated architecture proof.
- The scale thresholds (<100, 100–10000, >10000) are reasonable heuristics but not universal; data shape, query latency, privacy, delete semantics, and precision matter more than raw count alone.
- Vector DB is not automatically “large memory”; without provenance/deletion/embedding drift controls, it can create more problems.
- Tool-driven memory can pollute persistent memory if the Agent saves WIP, stale facts, or secrets.
- Reflection loops can reinforce wrong assumptions unless there is a review gate.

## Recommended absorption

Create or update Hermes memory-governance task/design with:

1. Memory landing-zone decision tree.
2. Mapping from memory class to Hermes storage boundary.
3. Explicit anti-ghost save gate.
4. Reflection-loop classifier:
   - user stable preference
   - project scoped fact
   - reusable procedure/skill
   - taskpool/evidence
   - session-only/no-save
5. Vector/RAG escalation rule with provenance, deletion, and cost gates.

## Initial verdict

Worth absorbing as a **memory landing-zone classifier**. It complements the NexSandglass source:

- This post gives the simple decision tree and memory taxonomy.
- NexSandglass gives the preference-drift/product insight.
- Hermes should combine both into memory governance: choose the smallest sufficient memory mechanism, and detect when old durable facts have drifted.

Best one-line abstraction:

```text
Memory 不是越多越好；关键是把不同记忆放到正确边界，并防止旧记忆变成幽灵。
```
