# Douyin intake — NexSandglass 轻量级 AI 长期记忆 MCP 服务器

- Source short URL: `https://v.douyin.com/mVCY-mjHovM/`
- Canonical: `https://www.douyin.com/note/7648988722738249445`
- IES source used for extraction: `https://www.iesdouyin.com/share/note/7648988722738249445/`
- Author: 苏里 (`SuLi2706`)
- Published: 2026-06-08 19:42:48
- Stats at extraction: 195 likes, 266 collects, 36 shares, 16 comments
- Local evidence: `/Users/charles/.hermes/docs/private/douyin-nexsandglass-7648988722738249445/`

## Media evidence

- `router_item.json` — extracted Douyin metadata
- `image_0.webp` ... `image_3.webp` — original note images
- `contact_all.jpg` — contact sheet for OCR/visual analysis

## Douyin description

> NexSandglass 真！越用越懂。27kb的记忆体，目前就Hermes能直装，其他需要丢给agent改一下
> 对，我不会代码，写给Ai做出来的，果然要学文科
> 用了两天命中率从99.54%提升到99.99%

Important: the “99.54% → 99.99%” claim is author-provided social content, not independently verified evidence.

## OCR / visible content

Title page:

- `NexSandglass`
- `轻量级 AI 长期记忆 MCP 服务器`
- `竞品对比 · 代码审查 · 优化建议 · 安装指南`
- `2026年6月8日`

Project overview:

- NexSandglass is described as a lightweight AI long-term memory MCP server.
- Core idea: not just “remembering”, but “understanding usage / tracking preference shifts”.
- Runtime: `Python 3.11+`
- Size: `2320 行 / 27KB / 零依赖`
- License shown: `MIT`
- Fresh project: `1 star`, new in 2026-06.
- Tools: `10个` including search, recent, timeline, semantic search, preference/bias detection, search filtering, image construction, todo query, counting.

Architecture / storage:

- Storage is deliberately simple: text file + inverted index, no database.
- Row format: timestamp | sender | encrypted message.
- Encryption:
  - Windows: DPAPI (`CryptProtectData` / `CryptUnprotectData`)
  - macOS/Linux: plaintext downgrade shown in the report.
- Tokenization/indexing:
  - Chinese 2-gram + English 2-char.
  - Inverted index mapped to row numbers.
- Index file: `~/.neurobase/sandglass.idx`.

Search mechanism:

- Full-text search via inverted-index intersection.
- Complexity claim: O(1) token lookup, O(n) merge.
- Semantic search via LLM reranking, explicitly “non-vector embedding”; token consumption is harder to control.
- Timeline search supports day/week/month recall.
- Search filtering ranks keyword-filtered results for higher precision.

Competitive comparison matrix visible columns:

- NexSandglass
- AgenticCognition
- Nautilus Compass
- Engram

Visible rows compare rough categories such as positioning, storage target, language dependency, code size, MCP tool count, cross-session support, cross-platform support, maturity.

独创性评估 / code review visible claims:

- Technically not unique: preference detection and cross-session todo both have competitors.
- Differentiation: compresses memory server into a small zero-dependency Python implementation.
- Philosophy described as “not叫你记住，叫你被懂”的 user-understanding framing.
- Inverted-index instead of vector search is positioned as a deliberate memory-system choice.

手机截图 visible summary:

- “协议接入。核心思路是用倒排索引代替向量数据库，用 DPAPI 做本地加密，不依赖任何外部服务。”
- Four modules:
  - 加密落沙：all conversations stored locally encrypted.
  - 倒排索引搜索：no embedding/vector DB.
  - 偏移率检测：when user profile changes by >60%, auto-switch stage.
  - 跨会话待办追踪.
- Advantages:
  - 极简：zero dependencies, old notebook can run it, small resource usage.
  - 本地加密: DPAPI, data does not leave machine.
  - 偏移率 idea: not static profile, tracks changes; lighter than “越存越厚”.
  - MCP integration: one JSON config can connect.
- Problems:
  - Very early: 1 commit, no release, no tests, no issue/PR interaction.
  - Windows-only strong encryption; macOS/Linux downgrade to plaintext.
  - Single-file append storage lacks concurrent write safety.

Installation suggestions visible:

- Current project path in screenshot: `D:\Desktop\first-cc`.
- Steps:
  1. Clone repo to D drive; avoid C drive operations.
  2. Run `install.bat` to create `.neurobase` directory.
  3. Add NexSandglass service in Claude Code MCP config.
  4. Restart Claude Code; use 10 memory tools.
- Notes:
  - Only Windows has full encryption support; macOS/Linux plaintext downgrade.
  - Initial data volume is small; performance/accuracy are sufficient for short-term use, but indexing performance is unvalidated.
  - Preference-shift detection needs accumulated data; suggested after 2 weeks to assess accuracy.
  - Semantic search uses LLM token; large queries may affect cost.

Final summary visible:

- NexSandglass is “理念超前、工程极简”的 memory system.
- It uses ~2320 lines and zero dependencies to implement core functions often seen in MB-level systems.
- Main value: detecting preference shifts during usage, not just search.
- Obvious shortcomings: new project, Windows-only strong encryption, weak indexing scalability/explainability, incomplete cross-platform and tests.
- Suggested staged use:
  - Short term: Claude Code memory enhancement companion, accumulate usage data.
  - Medium term: add semantic tag functions; validate long-term technical debt.
  - Long term: after community validation, cross-platform support, and test system maturity, depend more deeply.
- If pursuing “lightweight + Python-native + user-decision-understanding”, NexSandglass has potential; if pursuing “massive stable retrieval + cross-platform + high precision search”, Engram or `claude-mem-lite` may be more suitable.

## Transferable Hermes patterns

### 1. Tiny local memory sidecar, not a global truth source

The useful idea is a **small local memory sidecar** with explicit boundaries:

```text
conversation event -> append-only local store -> inverted index -> recall candidates -> LLM rerank/explain -> user-visible evidence
```

For Hermes, this should not replace memory/session_search/skill/taskpool SSOT. It can inspire a low-cost memory experiment or fixture.

### 2. Preference-shift / profile-drift detection

The most interesting concept is not storage; it is “偏移率检测”: detect when the user’s stated preferences or behavior are no longer aligned with an old profile.

Hermes value:

- Prevent stale memory from becoming ghosts.
- Detect when a durable preference changed.
- Ask for confirmation before replacing profile facts.
- Separate “temporary session preference” from “stable user preference”.

This maps directly to Hermes memory governance and goal-calibration.

### 3. Inverted index as cheap first-stage recall

A 2-gram inverted index can be useful as a cheap first-stage candidate retriever before LLM reasoning. Hermes already has FTS/session_search, so the lesson is architectural:

```text
cheap deterministic candidate retrieval first; LLM only reranks/explains small sets
```

### 4. Local-first security stance

Local-only + encryption + no external service is aligned with private-agent workflows. But the macOS/Linux plaintext fallback is a redline if adapted.

### 5. MCP memory tool shape

The “10 memory tools” idea can inspire a capability taxonomy:

- write memory event
- exact search
- recent recall
- timeline recall
- semantic rerank
- preference-drift check
- pending todo recall
- count/statistics
- filter/rank
- explain provenance

## Risks / redlines

- Do not install or run NexSandglass in Hermes without explicit approval.
- Do not treat the author’s hit-rate claim as verified.
- Do not store secrets/API keys/connections in memory artifacts.
- Do not accept plaintext downgrade for macOS/Linux if storing private conversations.
- Do not let a sidecar memory become SSOT over Hermes memory/session/taskpool/skills.
- Do not bulk-import unvalidated MCP tools.
- Do not treat social screenshots as code audit; source repository and tests must be verified before implementation.

## Recommended absorption

Create a Hermes task for **local-memory drift detection and lightweight recall governance**:

- Compare NexSandglass ideas with Hermes memory/session_search/skills.
- Extract preference-drift detection as a candidate policy.
- Design a safe local-only memory sidecar experiment or fixture.
- Require encryption parity, no plaintext fallback, provenance, deletion, and stale-memory guard.
- Keep all execution/install behind a human gate.

## Initial verdict

Worth learning, especially the “preference shift / 偏移率检测” idea. The storage implementation is too early to trust directly, but the product insight is valuable:

```text
memory quality is not just recall accuracy; it is knowing when the user has changed.
```
