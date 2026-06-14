# Douyin intake — Harness Engineering

- Source short URL: `https://v.douyin.com/_c-48CVWst4/`
- Canonical: `https://www.douyin.com/note/7620458417325441512`
- IES extraction URL: `https://www.iesdouyin.com/share/note/7620458417325441512/`
- Author: 光影织梦 (`LuminousDream`)
- Description: `Harness Engineering.你怎么看Harness Engineering？你觉得AI Agent的未来是更强大的模型还是更完善的系统？ #AI #Agent #HarnessEngineering #Anthropic #OpenAI`
- Published: 2026-03-23 22:30:39
- Stats at extraction: 1,347 likes, 1,531 collects, 233 shares, 4 comments
- Local evidence: `/Users/charles/.hermes/docs/private/douyin-harness-engineering-7620458417325441512/`

## Media evidence

- `router_item.json` — extracted Douyin metadata
- `image_0.webp` ... `image_2.webp` — original images
- `contact_all.jpg` — OCR/contact sheet

## OCR / visible content

### Image 0

Title:

```text
最近AI圈最火的概念！Harness Engineering到底是什么？
```

Conclusion:

```text
模型是引擎，Agent是整辆车。引擎再强，没有方向盘和刹车，哪都去不了。
最近刷到一个视频讲Harness Engineering，颠覆了我对AI Agent的认知，必须来分享下。
```

Definition:

```text
中文可以叫“驾驭工程”或“控制系统工程”。
这个词来自马具——缰绳，只能驾驭马匹的工具。

核心比喻：
马 = AI模型（强大、快速，但自己不知道往哪走）
骑手 = 人类工程师（提供方向，不亲自跑）
Harness = 控制系统（连接模型和目标的桥梁）
```

LangChain case:

```text
LangChain的Coding Agent，在Terminal Bench排行榜上，从30多名一路冲到前五。
关键点来了：底层模型一行没换！始终是同一个模型！
他们只改了三个东西：
1. 系统提示
2. 工具配置
3. 中间件钩子
这直接挑战了AI开发中的深层假设——更好的性能需要更大或更新的模型。
事实证明：模型不变，先调优周围的系统，就能带来数量级的提升！
```

### Image 1 — Harness 到底包含什么？6个关键词

1. 上下文架构

```text
不是给Agent塞越多信息越好；研究发现，当上下文利用率超过40%后，Agent性能反而下降。
正确做法：给Agent一张“地图”，让它按需查找，而不是一开始就灌百科全书。
OpenAI的做法：把agents文件控制在大约100行，只突出目录，指向更深层的文档。
```

2. 架构约束

```text
prompt里的规则本质上是建议；模型可以听也可以不听。
前沿团队的做法：用确定性工具和格式执行约束，比如自定义linter和结构化测试。
有一个反直觉发现：Verso一开始给Agent提供大量工具，结果Agent反而困惑；做了很多冗余调用。后来移除80%的工具，只留最必要的，Agent反而更快更可靠。
```

3. 自验证循环

```text
Agent再冷静也会犯错。
输入无循环：对同一个文件反复编辑
交付时跳过验证
LangChain的方案：用中间件钩子跟踪每个文件的编辑次数，超过阈值就提醒Agent重新审视方案。

推理三明治策略：
规划阶段：最高推理强度
执行阶段：降到低等推理强度
验证阶段：拉回最高推理强度
全程最高反而浪费算力，因为内部规划好、实现力存在刀刃上效果最好。
```

4. 上下文隔离

```text
多Agent协作时，关键不是把角色分工（前端Agent、后端Agent），而是把子Agent当作“上下文防火墙”。
父Agent只看到给子Agent的指令和最终结果，中间所有工具调用都被隔离掉。
```

### Image 2

5. 自我治理

```text
Agent持续运行越久，系统混乱度越高：文档过时、架构漂移、知识库和代码不一致。
OpenAI的方案：引入后台文档梳理Agent，定期扫描并自动修复，形成自维护闭环。
```

6. 可拆卸性

```text
更好的模型会上来替代Harness组件变成瓶颈。
2024年需要复杂流水线的任务，2026年可能一个prompt就搞定。
Harness必须是模块化、可拆卸的！
```

Author's summary:

```text
AI开发的范式正在转变。
以前我们总觉得“模型至上”，不断追求更大更强的模型。但现在越来越多的人意识到：
系统的可靠性根本不在模型，在模型周围的系统。
这就像一辆车，引擎再牛，没有方向盘和刹车，就是废铁一堆。
而且Harness的投入是复利式生效的：
今天加一个Linter规则，未来所有任务都预防这个错误；
今天加一个验证中间件，未来所有任务交付质量都提升。
结尾: 也更像被称为工程化。一个很多实的原则：只在Agent确实犯过的错误上投入Harness，不要预防性地解决还没出现的问题。
```

## External corroboration

Public sources checked:

- Martin Fowler: `Harness engineering for coding agent users` — describes harnesses around coding agents to increase confidence, including feedforward/feedback, steering loops, maintainability harness, architecture fitness harness, behaviour harness, human role.
- LangChain: `The Anatomy of an Agent Harness` — defines `Agent = Model + Harness`; harness includes code/config/execution logic around the model such as state, tool execution, feedback loops, enforceable constraints, system prompts, tools, skills, MCPs, planning, subagents.
- LangChain: `Improving Deep Agents with harness engineering` — reports a coding agent improving from Top 30 to Top 5 on Terminal Bench 2.0 by changing harness, not model; emphasizes traces, system prompts, tools, middleware, self-verification, deterministic context injection, local context middleware, pre-completion checklist.
- OpenAI page exists in search results but direct fetch returned 403; not used as a primary source here.

## What it really is

Harness Engineering is not a new magic architecture. It is the engineering discipline of designing the **control system around a model**:

```text
model capability
+ context delivery
+ tool surface
+ constraints
+ feedback loops
+ verification gates
+ observability traces
+ subagent isolation
+ lifecycle maintenance
= agent reliability
```

The important shift is from:

```text
“换更强模型”
```

to:

```text
“在模型周围建立可验证、可约束、可观测、可拆卸的工程系统”。
```

## Transferable Hermes patterns

### 1. Hermes already is a harness-heavy agent

Hermes has many harness components:

- tools with schemas and side-effect boundaries
- skills and skill loading rules
- taskpool / mission envelope / lifecycle gates
- evidence artifacts
- session_search / memory governance
- cron/process lifecycle
- browser/computer verification
- taskpool multimodel advisory/ratification

So this source mainly validates Hermes' direction: better system around model, not only better model.

### 2. Context delivery should be map-first, not dump-first

Useful rule:

```text
Give the agent a map, then let it fetch details on demand.
```

For Hermes this means:

- project profile as index, not whole repo dump;
- skills as focused procedures, not massive prompt injection;
- session_search windows, not full transcript dumps;
- evidence refs and readback, not giant ungrounded summaries.

### 3. Tool minimalism and deterministic constraints

The “remove 80% of tools” story maps to Hermes tool governance:

- narrow enabled toolsets per cron/agent task;
- prefer deterministic validators over prompt rules;
- keep dangerous side-effect tools behind explicit gates;
- route task-specific surfaces only when needed.

### 4. Self-verification loops and exit hooks

LangChain-style pre-completion checklist is close to Hermes' “finishing the job” discipline:

- before final answer, force verification against task spec;
- if code/file/UI changed, read back or run tests/browser checks;
- if external side effects are blocked, report exact boundary.

### 5. Subagents as context firewalls

This is highly relevant: subagents should isolate context and tool outputs, not just mimic org chart roles.

Hermes rule candidate:

```text
delegate when the subtask would flood context, needs independent reasoning, or benefits from isolation; return compact evidence handles, then parent verifies.
```

### 6. Modular/deletable harness

Do not ossify every 2026 trick as a permanent global rule. A harness component should have:

- trigger condition;
- evidence that it solves an observed failure;
- cost/latency/token overhead;
- rollback/remove path;
- owner/expiry.

This matches the user's preference: don't elevate local context into global forced gates.

## Risks / redlines

- “Harness Engineering” can become a buzzword for ordinary engineering; avoid renaming everything without adding evidence.
- Do not add harness layers preemptively for imagined failures; add them when there is observed recurring failure.
- Extra harness can increase latency, token cost, user friction, and hidden state complexity.
- Too many tools, skills, middleware, and checks can make the agent less reliable.
- Self-maintenance agents can corrupt docs/skills if not gated by evidence and review.
- Subagent isolation is useful, but subagent self-reports are not proof; parent must verify handles/artifacts.

## Recommended absorption

Create a Hermes task for a **Harness Engineering audit and module registry**:

1. Inventory existing Hermes harness components.
2. Classify each component by purpose:
   - context delivery
   - tool constraint
   - verification loop
   - observability
   - side-effect gate
   - subagent isolation
   - lifecycle maintenance
3. Add a rule: new harness components must be failure-driven, measurable, scoped, and removable.
4. Define a pre-final verification hook pattern for high-risk tasks.
5. Define tool-minimalism policy for cron/subagents/workflows.

## Initial verdict

Very worth absorbing. It directly matches Hermes' direction:

```text
可靠 Agent = 模型能力 × 工程化 Harness
```

But the best absorption is not to create more buzzword layers. It should become an audit lens:

```text
每加一个 skill/tool/hook/gate，都要回答：它解决了哪个真实失败？证据是什么？成本是什么？怎么删除？
```
