# Context Engineering：论点、核心著作与 Hermes 进化落地

生成时间：2026-07-08
目标：把“Context Engineering”从趋势词转成 Hermes/个人 AI OS 的可执行能力栈。

## 1. 核心判断

Context Engineering 不是 Prompt Engineering 的同义词，而是 LLM/Agent 推理时“信息有效载荷”的系统工程：

> Context = Assemble(instructions, knowledge, tools, memory, state, query, evidence, constraints)

真正要工程化的不是一句 prompt，而是：
- 取什么信息；
- 何时取；
- 如何结构化；
- 如何压缩/隔离/缓存；
- 如何绑定权限、工具与状态；
- 如何验证输出是否由正确上下文支撑。

对 Hermes 的直接含义：Hermes 不应只做“会用工具的聊天机器人”，而应进化成“上下文操作系统”：把 profile、memory、skill、SSOT、taskpool、evidence、tool authority、readback 统一为可审计的 Context Runtime。

## 2. 关键论点

### 论点 A：Agent 失败常是 context failure，不是纯模型能力失败

证据/出处：
- coleam00/context-engineering-intro：明确提出“Most agent failures aren't model failures - they're context failures”。
- A Survey of Context Engineering for Large Language Models：LLM performance is fundamentally determined by contextual information provided during inference。

工程推论：
- 不能只升级模型；必须升级上下文选择、组装、验证和状态治理。
- “更长上下文”不是答案；错误/污染/过期上下文会扩大失败面。

### 论点 B：Prompt 是字符串；Context 是系统

证据/出处：
- Awesome Context Engineering 给出形式化拆分：context = Assemble(instructions, knowledge, tools, memory, state, query)。
- DSPy 反对硬编码 prompt template，主张把 LM 调用编译成可优化 pipeline。

工程推论：
- Hermes 的 skill/profile/memory/tool schema 不是附属物，而是 prompt 之前的系统层。
- 必须把上下文组装函数当成可测试、可度量、可回滚的工程对象。

### 论点 C：RAG 只是 Context Engineering 的一个子集

证据/出处：
- RAG: Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks。
- Survey 将 foundational components 分为 context retrieval/generation、processing、management，再落到 RAG、memory、tool-integrated reasoning、multi-agent systems。

工程推论：
- 不要把 CE 落地窄化为“加向量库”。
- Hermes 需要同时处理：检索、记忆、工具权限、任务状态、证据链、交互历史、设计/代码上下文。

### 论点 D：工具调用把 context 从“给模型看的资料”扩展为“可执行环境边界”

核心著作：
- ReAct: Synergizing Reasoning and Acting in Language Models。
- Toolformer: Language Models Can Teach Themselves to Use Tools。

工程推论：
- 工具列表、参数 schema、权限、side-effect 风险、readback receipt 都是 context。
- Context Engineering 必须包含 Authority Engineering，否则 Agent 会把“知道”误当“可做”。

### 论点 E：长期任务需要 memory OS，不是无限 transcript

核心著作：
- MemGPT: Towards LLMs as Operating Systems。
- Generative Agents: Interactive Simulacra of Human Behavior。
- Reflexion: Language Agents with Verbal Reinforcement Learning。

工程推论：
- Hermes 的 memory/skill/session_search/project profile 应分层：用户稳定事实、项目事实、程序性技能、事件证据、临时状态。
- 记忆不是越多越好；要有 landing zone、scope、decay、falsifier。

### 论点 F：长上下文模型并不等于有效上下文使用

核心著作：
- Lost in the Middle: How Language Models Use Long Contexts。
- RULER: What's the Real Context Size of Your Long-Context Language Models?
- SmoothAgent: Efficient Long-Horizon LLM-Based Agent Serving with Lookahead Context Engineering。

工程推论：
- 需要 context ranking、positioning、compression、isolation、offloading、KV/cache-aware runtime。
- Hermes 要减少“把所有东西塞进 prompt”的冲动，改为 evidence-selected assembly。

### 论点 G：可验证上下文比“模型自信”重要

核心著作/工具：
- Ragas: Automated Evaluation of Retrieval Augmented Generation。
- RAG evaluation survey。
- Agent observability/telemetry stacks。

工程推论：
- 每个关键输出要能追溯到 source/evidence/tool readback。
- 对代码/产品工作，必须有 spec -> implementation -> test/UI/API/log 的收敛表。

## 3. 核心著作 / 资料清单

### A. 直接命名 Context Engineering

1. A Survey of Context Engineering for Large Language Models
   https://arxiv.org/abs/2507.13334
   作用：CE 的学术总纲；定义、taxonomy、研究缺口。

2. Awesome Context Engineering
   https://github.com/Meirtz/Awesome-Context-Engineering
   作用：资料索引；把 CE 延伸到 agent runtime、memory、protocol、observability。

3. Context Engineering Template
   https://github.com/coleam00/context-engineering-intro
   作用：AI coding 实践；CLAUDE.md + examples + INITIAL.md + PRP + validation gates。

4. SmoothAgent: Efficient Long-Horizon LLM-Based Agent Serving with Lookahead Context Engineering
   https://arxiv.org/abs/2607.00151
   作用：系统/推理服务视角；context transformation、offloading、reduction、isolation、KV cache/TTFT。

### B. 前置基础：RAG / Retrieval / Knowledge

5. Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks
   https://arxiv.org/abs/2005.11401

6. GraphRAG / Microsoft GraphRAG
   https://github.com/microsoft/graphrag
   作用：把检索从 chunk 扩展到 entity/relation/community summary。

### C. Agent 行动与工具上下文

7. ReAct: Synergizing Reasoning and Acting in Language Models
   https://arxiv.org/abs/2210.03629

8. Toolformer: Language Models Can Teach Themselves to Use Tools
   https://arxiv.org/abs/2302.04761

### D. Memory / Long-running agents

9. MemGPT: Towards LLMs as Operating Systems
   https://arxiv.org/abs/2310.08560

10. Generative Agents: Interactive Simulacra of Human Behavior
    https://arxiv.org/abs/2304.03442

11. Reflexion: Language Agents with Verbal Reinforcement Learning
    https://arxiv.org/abs/2303.11366

### E. Long Context 与上下文质量

12. Lost in the Middle: How Language Models Use Long Contexts
    https://arxiv.org/abs/2307.03172

13. RULER: What's the Real Context Size of Your Long-Context Language Models?
    https://arxiv.org/abs/2404.06654

### F. Prompt/Program Optimization

14. DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines
    https://arxiv.org/abs/2310.03714

### G. Evaluation

15. Ragas: Automated Evaluation of Retrieval Augmented Generation
    https://arxiv.org/abs/2309.15217

## 4. Hermes 进化落地：Context Runtime 七层

### L1 Intent / Spec Gate
输入：用户请求、目标、非目标、硬约束、验收标准。
产物：Spec Brief、Objective Model、negative cases。

### L2 Source / Evidence Graph
输入：文件、网页、PRD、issue、session_search、API docs、截图、日志。
产物：Evidence DAG：source_id、claim、confidence、freshness、scope。

### L3 Knowledge Retrieval / Index
输入：代码库、文档、历史会话、项目 SSOT、外部资料。
产物：hybrid search、symbol graph、entity graph、chunk + relation。

### L4 Memory / Skill / Profile Router
输入：user memory、project profile、skills、workflow references。
产物：最小充分上下文包，而不是全量注入。

### L5 Tool & Authority Context
输入：可用工具、权限、side-effect、目标、rollback、readback。
产物：AuthorityGrant / denial / human gate。

### L6 Execution Loop
输入：plan、tools、tests、UI/API/CLI actions。
产物：patches、commands、receipts、runtime observations。

### L7 Verification & Learning
输入：测试、截图、日志、API readback、diff、用户反馈。
产物：Converge check、skill patch、profile update、taskpool proof、do-not-save boundary。

## 5. 可立即落地的 Hermes 改造顺序

### S1：Context Packet 标准化
为复杂任务生成一个 Context Packet：
- objective
- constraints
- sources
- selected skills
- project profile
- authority boundary
- validation commands
- evidence map

### S2：Context Assembly Score
每次组装上下文前做四项评分：
- relevance：是否直接支撑当前目标；
- freshness：是否过期；
- authority：是否可作为行动依据；
- cost：token/噪音/污染成本。

### S3：Evidence DAG 化
将 source -> claim -> decision -> action -> readback 串起来，避免“看过资料但输出无出处”。

### S4：Memory Landing Zone Gate
任何 durable write 先分类：
- user stable preference
- project scoped fact
- skill procedure
- SSOT/ADR
- task evidence
- do-not-save

### S5：Context Regression Eval
为 Hermes 增加评测：同一任务在不同上下文包下是否：
- 不丢约束；
- 不引入过期项目事实；
- 不错误扩大权限；
- 能引用正确证据；
- 能跑正确验证命令。

## 6. 对当前 Hermes 的定位升级

旧定位：工具增强型 AI Agent。

新定位：Context-Governed Personal AI OS。

核心差异：
- 不是“更多工具”，而是“正确上下文 + 权限边界 + 可验证行动”。
- 不是“更长记忆”，而是“分层记忆 + 证据选择 + 反污染”。
- 不是“更强 prompt”，而是“Context Assembly Runtime”。

## 7. 一句话产品化表达

Context Engineering for Hermes：
把用户目标、项目事实、历史经验、工具权限、实时证据和验证结果组装成最小充分上下文包，让 Agent 在复杂任务中持续做对事、少犯错、可追溯、可进化。
