# Hermes 神经启发式模块化记忆：唯一 SSOT

- 状态：locally_implemented_and_verified；等待独立 verifier 结论，不提升为 global certified
- 日期：2026-07-19
- 作用域：当前 `default` profile 的 Hermes Agent，本地、可逆、单机
- 控制规则：`docs/private/hermes-self-optimization-ssot-20260526.md`
- 非声明：本方案不模拟真实生物神经元，也不声称具有生物学意义上的意识或记忆。

## 1. Spec Gate

### 目标

构建适合 Hermes 自身的长期稳定记忆运行时：每个对话轮次先作为不可变事件保存，再从同一来源生成多个目的不同、可追溯的记忆投影；下一轮只装配与当前目标、作用域、时效和权限相符的最小充分记忆簇。

核心函数：

```text
MemoryProjection = Project(
  immutable_evidence,
  module_contract,
  abstraction_level,
  target_scope,
  current_objective,
  validation_policy
)
```

### 非目标

- 不替换 `state.db` 会话事实源、`MEMORY.md`、`USER.md`、skills 或 project profiles。
- 不把推断、摘要、模型共识自动升级为事实、权限或执行授权。
- 不保存凭据、卡号、令牌或未脱敏的工具输出。
- 不递归总结“摘要的摘要”作为新事实；任一高层投影必须回到 L0 事件重新生成或校验。
- 不引入远端服务、外部派发、自动发布、部署或破坏性操作。

### 不变量

1. L0 事件仅追加；投影可降权、归档、替代，但不可改写原始历史。
2. 每个投影必须包含 `source_event_id/source_hash`、模块、抽象层、作用域、可信度、状态、适用条件、反条件。
3. 同一事件可产生多个投影；模块契约不同，不以随机改写制造“不同抽象”。
4. 工作记忆检索为 authority-neutral、reference-only；业务事实与 L0 内容只读，允许仅写入 `access_count`/`last_accessed_at` 激活遥测，但不得改写事实、状态、权限或外部世界。
5. 快速写入与慢速巩固分离；跨会话重复支持且无冲突才提升强度。
6. 冲突不静默覆盖；保留 `contradicts/supersedes` 边和旧节点。
7. L0 永不因遗忘删除；遗忘只影响投影的强度、活跃状态与检索资格。
8. profile、session、task、project、user、domain、global 作用域必须可判定；默认 session。
9. 任何召回包都有字符预算、条目上限、来源锚点和明确边界。
10. 失败时 fail closed：不注入、不写远端、不阻塞主会话。

### 验收标准

- 一个轮次写出两条不可变事件，并从同一来源形成至少两种模块/抽象投影。
- 重放同一轮次幂等，不重复事件或投影。
- 每个投影可追溯至事件 SHA-256；秘密样式文本及通过 Luhn 校验的裸露/分隔式 PAN 在落盘前脱敏。
- 下一轮召回受 query、scope、status、budget、expiry 共同约束。
- 能从同源兄弟投影执行受限模式补全，但不会越作用域。
- 明确纠正可产生冲突/替代关系；旧投影保留但被抑制。
- 纠正只压制与“被替换主题”充分匹配的旧投影；共享一个技术词不能触发跨主题压制。
- 至少两个独立 session 的一致证据才能巩固；单轮推断保持 candidate/reference-only。
- Provider 的显式稳定用户偏好使用不可逆身份摘要形成的 `user:*` scope，跨 session 可巩固；episodic/普通轮次仍保持 `session:*`。
- 时间衰减按 projection 的 `last_decayed_at` 增量计算；同一时间戳重复 maintenance 幂等，可归档低强度投影，但事件计数不减少。
- Local Brain 原有 `brainctl search` 召回仍保留，并与新运行时统一注入。
- 自动测试覆盖正向、幂等、溯源、作用域、脱敏、冲突、巩固、遗忘、预算、错误关闭。

### 风险与回滚

- 风险：错误投影污染上下文。控制：reference-only、候选状态、作用域门禁、字符预算、显式来源。
- 风险：隐私泄露。控制：本地 SQLite、写前脱敏、工具结果默认不持久化、无网络。
- 风险：与现有 provider 冲突。控制：作为单一用户级 provider 包装现有 `brainctl`，不改核心 ABI。
- 回滚：将 `memory.provider` 改回 `localbrain`；保留数据库供审计，或人工备份后删除插件目录。

## 2. 相关学科、论点与工程映射

### 2.1 认知心理学：功能分工而非单一摘要池

- Atkinson & Shiffrin（1968）多存储模型、Baddeley & Hitch（1974）工作记忆、Baddeley（2000）episodic buffer：支持把当轮任务态、跨模态绑定和长期知识分开，而不是把所有内容写进同一个字符串。
- Tulving（1972, *Episodic and Semantic Memory*）：支持区分“发生过什么”与“可泛化地知道什么”。
- Squire（2004, *Memory systems of the brain*）：支持按功能和可访问方式划分记忆系统，而非按数据库表名类比脑区。

工程结论：采用 functional module 轴：`episodic/intent/constraint/decision/evidence/causal/preference/procedure/uncertainty`；working memory 是按轮动态装配结果，不是永久仓库。

### 2.2 互补学习系统与系统巩固：快写、慢学

- McClelland, McNaughton & O'Reilly（1995），DOI `10.1037/0033-295X.102.3.419`：海马样快速学习与新皮层样慢速统计学习互补，可减轻新知识对既有知识的灾难性干扰。
- Kumaran, Hassabis & McClelland（2016），DOI `10.1016/j.tics.2016.05.004`：更新了智能体所需互补学习系统的论证。
- Dudai, Karni & Born（2015），DOI `10.1016/j.neuron.2015.09.004`，*The Consolidation and Transformation of Memory*：巩固包含稳定化与表征转化，不等于复制。

工程结论：单轮只写 fast episodic/candidate projections；跨 session 重复、来源独立、无冲突且通过门禁后才提高稳定强度。`MEMORY.md/USER.md/skills` 仍由现有显式工具治理，不由本插件自动改写。

### 2.3 稀疏表征、模式分离与模式补全

- Marr（1971），DOI `10.1098/rstb.1971.0078`，*Simple memory: a theory for archicortex*：以稀疏表征和少量线索触发回忆为核心思想。
- Hopfield（1982），DOI `10.1073/pnas.79.8.2554`：形式化 content-addressable memory，可由足够子线索恢复完整模式。
- Kanerva（1988），*Sparse Distributed Memory*：高维稀疏地址空间中相似线索的分布式存取。
- Josselyn, Köhler & Frankland（2015），DOI `10.1038/nrn4000`，*Finding the engram*：记忆痕迹由细胞集合与可塑性承载；工程上只借鉴“分布式痕迹+激活条件”，不做脑区等同。

工程结论：用 `(source_hash, module, semantic_key)` 做模式分离；检索命中后仅扩展同源兄弟和显式关系邻居做受限模式补全；不做全图无界扩散。

### 2.4 再巩固、竞争、抑制与遗忘

- Nader, Schafe & LeDoux（2000），DOI `10.1038/35021052`：已提取的记忆可再次进入可变状态，支持“召回后允许修订但保留历史”的类比。
- Anderson, Bjork & Bjork（1994），DOI `10.1037/0278-7393.20.5.1063`：retrieval-induced forgetting 表明检索竞争会抑制相关表征。
- Ebbinghaus（1885），*Über das Gedächtnis*：遗忘随时间变化，但工程实现不直接照搬单一指数曲线。

工程结论：召回只更新激活遥测，不增强知识强度；冲突节点竞争并抑制旧节点；未使用、低置信、短期候选逐步归档。删除的是检索资格，不是证据。

### 2.5 数据库、知识表示与信息检索

- Event Sourcing（Fowler, 2005）：状态由不可变事件派生；适合证据回放与投影重建。
- CQRS（Young/Fowler 体系）：写模型与读模型分离；适合 L0 事件与检索投影分离。
- W3C PROV-O（2013）：`Entity/Activity/Agent` 和 derivation 关系支持来源追踪。
- Temporal Databases（Snodgrass, 1999）：区分 valid time 与 transaction time，避免把“曾经正确”和“现在有效”混为一谈。
- BM25/FTS、向量检索、知识图谱：词法召回负责精确锚点，向量负责语义近邻，图关系负责可解释补全；本地第一版采用 SQLite FTS5+关系边，保留向量适配口，不把 embedding 作为事实判定器。

工程结论：SQLite append-only event log + materialized projections + FTS5 + typed edges；任何 read model 可从事件重建。

### 2.6 Agent memory 文献

- Park et al.（2023），arXiv `2304.03442`，*Generative Agents*：完整经验流、reflection、动态检索共同改善行为；其反思链容易产生摘要漂移，因此本方案要求 reflection 始终携带 L0 锚点。
- Packer et al.（2023），arXiv `2310.08560`，*MemGPT*：以分层存储和上下文换页管理有限上下文。
- Wang et al.（2023），arXiv `2306.07174`，*LongMem*：解耦记忆库与主干模型以保持长期扩展性。
- Zhong et al.（2023），arXiv `2305.10250`，*MemoryBank*：提出长期记忆、反思与遗忘机制。
- Gutiérrez et al.（2024），arXiv `2405.14831`，*HippoRAG*：将知识图谱和 Personalized PageRank 用于长期知识整合与多跳检索。

工程结论：吸收分层、reflection、外部存储、图召回；拒绝“摘要即事实”、无来源 reflection、全量上下文注入和模型自行提升权限。

## 3. 最终架构：M³G（Multi-Module Memory Graph）

### 3.1 三轴坐标

每个投影由三轴唯一定位：

- 功能轴 `module`：episodic、intent、constraint、decision、evidence、causal、preference、procedure、uncertainty。
- 抽象轴 `level`：L0 raw/redacted event；L1 span；L2 claim；L3 relation；L4 pattern；L5 strategy。
- 作用域轴 `scope`：turn、session、task、project、user、domain、global。

同源不同抽象不是随机生成，而是不同 module contract 对同一 L0 提问：

```text
episodic:   发生了什么？
intent:     用户要达成什么？
constraint: 哪些边界不可违反？
decision:   选择了什么路径？
evidence:   哪些可验证结果支持结论？
causal:     哪个条件导致哪个结果？
preference: 哪些稳定偏好只是候选，需何种确认？
procedure:  哪个可复用步骤序列只是候选，需何种验证？
uncertainty:什么仍未知、失效或未验证？
```

### 3.2 数据对象

`events`：不可变、去重、脱敏的 turn 事件。

`projections`：从事件派生的模块化候选，包含来源、状态、强度、时效、适用/反条件。

`edges`：`derived_from/sibling/contradicts/supersedes/supports/related_to`。

`activations`：仅记录召回统计，不回写 claim 文本。

`consolidation_receipts`：记录何时、基于哪些独立 session、按哪个规则提升或归档。

### 3.3 七步循环

1. Capture：对本轮 user/assistant 文本脱敏、哈希、只追加。
2. Project：按模块契约生成 L1/L2 候选；不递归读取旧摘要作为事实源。
3. Separate：按来源、模块、semantic key 去重，创建同源 sibling 边。
4. Compete：同主题冲突不覆盖，创建 contradicts/supersedes 并抑制旧节点。
5. Assemble：下一轮按 query、显式允许的 scope 集、时效、权限、预算选择种子；FTS 缺失/异常或无候选时直接返回空，不退化为 scope 全表扫描。
6. Complete：仅扩展同源 sibling 和一跳显式关系，形成最小充分工作包。
7. Consolidate/Forget：跨 session 一致证据提升强度；冲突、过期、低使用候选降权或归档；L0 不删。

### 3.4 检索评分

```text
score = lexical_relevance
      × scope_gate
      × validity_gate
      × authority_gate
      × (0.45 confidence + 0.35 strength + 0.20 recency)
      + bounded_relation_bonus
```

硬门禁先于排序：scope 不匹配、expired、archived、无 provenance、`source_hash` 非 64 位小写十六进制 SHA-256、或该哈希不等于对应不可变 L0 事件的 `content_hash`、非 reference-only 注入契约均拒绝。primary 与 sibling completion 使用同一组门禁；字符预算和条目上限最终截断。

### 3.5 与 Hermes 的集成边界

- 使用官方 `MemoryProvider` ABI：`prefetch/sync_turn/on_pre_compress/on_session_end`。
- 用户级 provider 包装当前 `brainctl search`，保留 Local Brain 的 canonical path/line/hash 召回。
- 新库位于 `$HERMES_HOME/memory/neural_modular.sqlite3`，profile 自动隔离。
- Provider 默认允许精确当前 `session:*`、由 gateway user/profile identity 单向摘要得到的精确 `user:*`、以及 `global`；原始 identity 不进入 scope。仅显式稳定 preference 和显式 correction 投影进入 durable user scope，普通 episodic/turn 投影不提升。
- `sync_turn` 只做本地、确定性、快速写入；不调用 LLM、网络或工具。
- `prefetch` 输出 authority-neutral/reference-only 记忆包；不会增加工具 schema，不改变 prompt cache 静态前缀。
- built-in memory、USER、skills、project profiles 仍按现有治理工具显式写入；插件只提供候选证据，不自动提升。

### 3.6 全记忆拓扑与唯一控制面

现有 Local Brain 不删除，也不把所有存储物理合并到 SQLite。最终形态是“一个活跃 MemoryProvider 控制面 + 多个职责单一的事实面”。`memory.provider=neural_modular_memory` 由 Hermes 的 memory-provider loader 直接加载；`plugins.enabled` 是普通插件启用列表，两者不是第二个 provider 开关。Hermes `MemoryManager` 仍只挂载一个外部 provider，因此不存在两个 provider 同时争用生命周期或工具 schema 的控制面双轨。

| 记忆面 | Canonical owner | 写路径 | 读路径 | 与 M³G 的关系 |
|---|---|---|---|---|
| `MEMORY.md` / `USER.md` | built-in memory tool | 人工/agent 显式 `add/replace/remove` | 静态系统上下文 | 保持 canonical；成功写入只追加脱敏 `memory_write_receipts` 审计收据，不生成 event/projection/FTS，避免重复召回 |
| Local Brain vault/index | canonical Markdown + `brainctl` 索引 | 现有 brain sync/Obsidian 治理 | `brainctl search`，path/line/hash 引用 | 只读联邦召回；不把 17k+ blocks 复制进 M³G，不从对话自动反写 vault |
| M³G event graph | `neural_modular.sqlite3` | primary agent `sync_turn` | scope/provenance/status/expiry 门禁后的动态召回 | 保存快速事件与派生候选；与 Local Brain 共享单一 provider 字符预算 |
| session transcript | `state.db` | Hermes session runtime | `session_search` 显式查询 | 历史事实源，不自动复制到 graph；需要时作为二级回溯证据，不证明外部当前状态 |
| skills | skill directories | `skill_manage` 显式治理 | 按任务加载 | 稳定可复用程序的 canonical owner；M³G procedure 只能作为候选，不能自动发布为 skill |
| project profile / SSOT / evidence DAG | project files | 受治理文件写入 | 原始路径/readback | 项目事实与验收 canonical owner；Local Brain 可索引其引用，M³G 不覆盖 |
| compaction summary / working context | 当前 session | runtime | 当前上下文 | 临时工作记忆，不作为跨会话 canonical store |

闭环规则：

1. 普通对话只进入 M³G L0/projection；仅 primary context 可写 turn、memory receipt 及 consolidation/decay maintenance，subagent/cron/flush 不落入或重排用户表征。
2. 显式 memory tool 写入先由 built-in canonical store 成功提交，随后通过 `on_memory_write` 追加脱敏、不可更新/删除的审计收据；收据不参与召回，因此不形成双份 prompt。
3. `/new`、`/reset`、`/resume`、`/branch` 或压缩导致 session 切换时，provider 同步更新 session id，防止后续事件写入旧 session。
4. Local Brain 与 M³G 只在 read path 联邦：前者提供 canonical path/line/hash 线索，后者提供 L0-bound projection；共同受一个总字符预算约束。若 canonical excerpt 与 M³G claim 规范化后完全相同，保留 Local Brain 引用并抑制重复 projection 行；不做模糊语义合并，避免误删不同限定条件。
5. M³G 候选需要升级为 `MEMORY/USER`、skill 或 project SSOT 时，必须经过相应显式治理工具和原始来源验证；模型频次、召回次数或多模型共识不能自动晋升。
6. 冲突优先级不是“新库覆盖旧库”：当前原始外部证据/用户明确纠正 > 显式 canonical memory/SSOT > 经原路径核验的 Local Brain 引用 > consolidated M³G > supported > candidate。任何层级都不授予外部副作用权限。
7. Hermes profile backup 覆盖 `$HERMES_HOME` 内 built-in memory、M³G DB、session DB、skills/profile；provider 的 `backup_paths()` 额外声明 Local Brain canonical vault（默认 `~/Documents/brain` 或 `HERMES_BRAIN_VAULT`/`brain_vault_path`），使 `hermes backup/import` 能纳入外部 vault，同时仍保持独立路径和恢复边界。

刻意保留的人类门禁不属于“未闭环”：M³G 到 canonical memory/skill/project SSOT 的 promotion 必须显式批准和读回；自动双向同步反而会造成摘要漂移、重复召回和错误事实扩散。

## 4. 状态机

```text
candidate -> supported -> consolidated
    |            |             |
    +----------> contradicted  |
    +----------> archived <----+

correction: old --superseded_by--> new
```

- `candidate`：单轮、单来源。
- `supported`：至少两个独立 source event 支持（可来自同一 session），但仍未满足跨 session 巩固；召回次数不能替代来源支持。
- `consolidated`：至少两个独立 session 支持、无活跃冲突、达到置信/强度门槛；procedure/causal/decision 还必须在每个支持 session 具有同源 evidence 投影。
- `contradicted`：存在未解决反证；默认不注入为稳定知识。
- `archived`：低强度、过期或长期未用；仍可通过审计接口读取。

## 5. 负面边界

- 任何 projection 都不能授权发送、删除、部署、支付、输入凭据或改写生产状态。
- `assistant` 自述的“已完成”只进入 decision/uncertainty 候选，除非有工具/API/测试证据锚点。
- 用户的“这次这样做”默认 session/task scope；不能自动升为 user/global。
- 显式稳定偏好可进入该用户的 hashed `user:*` scope；这不授权把 episodic、普通 intent 或临时 constraint 自动升为 user/global。
- 显式用户纠正优先于旧推断，但旧记录不删除；必须命中明确被替换主题，不以任意共享 token 判冲突。
- 多次重复的错误不能因频次变成事实；独立来源、无冲突与验证门禁缺一不可。

## 6. Converge Matrix

| 验收项 | 代码证据 | 测试/运行证据 | 状态 |
|---|---|---|---|
| 多模块同源投影 | `MemoryStore._insert_event/_projection_specs/_insert_projection` | `test_one_source_creates_multiple_contract_driven_projections`；实库 4 events→10 projections/16 edges | pass |
| 幂等、不可变与溯源 | `MemoryStore._insert_event`、L0 triggers、recall provenance SQL | turn replay、changed-content、update/delete、伪 hash 与 L0 mismatch 负测 | pass |
| 写前脱敏 | `redact`、`redact_structure` | 私钥、token、Authorization、AWS key、cookie、Luhn-valid PAN、nested metadata 负测 | pass |
| scope/时效/预算门禁 | `MemoryStore.recall`、`NeuralModularMemoryProvider.prefetch` | scope 全矩阵、精确 session+hashed-user scope、sibling 门禁、FTS fail-closed、统一字符预算 | pass |
| 冲突/替代 | `MemoryStore._apply_correction/consolidate` | 同技术词不同主题不误伤；明确替换主题被压制；活跃 contradiction 禁止巩固 | pass |
| 双速巩固 | `MemoryStore.consolidate`、durable-scope 投影 | 单源不升 supported；双 source/single session 仅 supported；双 session 稳定偏好巩固；高风险 evidence 门禁 | pass |
| 召回不自强化 | `MemoryStore.recall` activation telemetry | strength 召回前后不变；只增加 access/activation | pass |
| 遗忘不删 L0 | `MemoryStore.decay`、`last_decayed_at`、L0 triggers | 同一时刻重复衰减幂等，后续仅计算新增时间区间；弱 projection 归档且 event 仍在；数据库拒绝 event update/delete | pass |
| 唯一 provider 控制面 | Hermes loader/`MemoryManager` + `NeuralModularMemoryProvider` | 活跃配置 `memory.provider=neural_modular_memory`；`get_tool_schemas=[]` | pass |
| built-in 显式记忆闭环 | `record_memory_write`、`on_memory_write`、MemoryManager bridge | committed/non-staged 才追加；receipt 脱敏、不可变、不进入 event/projection/FTS/recall | pass |
| session/context 生命周期 | `sync_turn` primary gate、`on_session_switch` | child/subagent 不摄取；session switch 后只写新 session | pass |
| Local Brain 联邦召回 | `_brain_recall`、`prefetch` | 合法 path/line/hash；timeout/non-zero/invalid JSON/hash/path/line fail-closed | pass |
| 跨来源去重 | `_suppress_modular_duplicates` | 已注入 canonical excerpt 精确去重；被预算截断而未注入的 Brain hit 不抑制 M³G | pass |
| 全记忆备份边界 | `backup_paths()`、Hermes backup collector | live collector 读回 `/Users/charles/Documents/brain` 且路径存在 | pass |
| schema v1/v2→v3 迁移 | `_init_schema`、`last_decayed_at`、`memory_write_receipts` triggers | fixture 原地升级保留 event/strength；旧 projection 首次迁移不重复衰减；未知/未来 schema 拒绝打开且不重写 marker；实库 integrity/count/trigger 读回 | pass |
| fail-closed/无权限扩张 | `prefetch`、`sync_turn`、`get_tool_schemas` | storage failure 返回空；authority-neutral 提示；生产代码静态安全扫描 0 findings | pass |

### 运行证据（2026-07-19）

- 解释器 A：`/Users/charles/.hermes/worktrees/hermes-agent-ci-project-base-fix/.venv/bin/python`；40/40，0 failure、0 error、0 skip。
- 解释器 B：`/opt/homebrew/bin/python3`（3.14.3）；40/40，0 failure、0 error、0 skip。macOS `/usr/bin/python3` 为 3.9.6，低于 Hermes 使用 `X | Y` 类型语法的运行时要求，因此不作为支持解释器门禁。
- 重复门禁：100 次完整 suite × 40 = 4000 tests；0 failure、0 error、0 skip；exit 0。
- 静态门禁：`py_compile`、scoped `git diff --check` exit 0；production added-lines secret/shell/eval/pickle/SQL-fstring scan 均为 0。
- 配置：`hermes config check` exit 0；活跃 provider 为 `neural_modular_memory`。
- live backup collector：`BACKUP_EXTERNAL_PATHS=['/Users/charles/Documents/brain']`，`ALL_EXIST=True`。
- 活跃 SQLite：schema `hermes.neural_modular_memory.v3`；4 events、10 projections、16 edges、15 activations、0 memory receipts；`last_decayed_at` 已存在且 10 个迁移 projection 初始为 NULL；`PRAGMA integrity_check=ok`；event/receipt update/delete triggers 均存在。
- v3 迁移逃生备份：`/tmp/neural_modular.pre-v3.20260719-033032.sqlite3`，SHA-256 `558fd1e6dcb2764e56d4b555b3f2216d51a5be0bfead5c2488724943f083352a`，schema v2、integrity `ok`、计数 4/10/16/15/0。更早的 pre-v2 备份及其 SHA-256 `022e8876434631e784657466e8d906e6ff69683bb05c3bca3451d4972a176b10` 继续保留。
- 回滚：运行时切回 `hermes config set memory.provider localbrain`；代码只 revert 精确 scoped commit；数据库/迁移前备份保留审计，禁止对混合工作区全局 reset/clean。
- Gate readback：`workflows/projects/hermes-neural-modular-memory/06-projection/architecture-gate-readback-20260719.md`。
- 认证边界：上述只证明 default profile 的本地实现、迁移与当前验收面；不证明跨设备、长期召回质量、生产恢复演练或全局认证。

## 7. 核心书目

- Atkinson, R. C., & Shiffrin, R. M. (1968). *Human Memory: A Proposed System and its Control Processes*.
- Baddeley, A. D., & Hitch, G. (1974). *Working Memory*.
- Baddeley, A. (2000). *The episodic buffer: a new component of working memory?* DOI `10.1016/S1364-6613(00)01538-2`.
- Tulving, E. (1972). *Episodic and Semantic Memory*.
- Marr, D. (1971). *Simple memory: a theory for archicortex*. DOI `10.1098/rstb.1971.0078`.
- Hopfield, J. J. (1982). *Neural networks and physical systems with emergent collective computational abilities*. DOI `10.1073/pnas.79.8.2554`.
- Kanerva, P. (1988). *Sparse Distributed Memory*. MIT Press.
- McClelland, J. L., McNaughton, B. L., & O'Reilly, R. C. (1995). *Why there are complementary learning systems...* DOI `10.1037/0033-295X.102.3.419`.
- Anderson, M. C., Bjork, R. A., & Bjork, E. L. (1994). *Remembering can cause forgetting*. DOI `10.1037/0278-7393.20.5.1063`.
- Nader, K., Schafe, G. E., & LeDoux, J. E. (2000). *Fear memories require protein synthesis... for reconsolidation*. DOI `10.1038/35021052`.
- Squire, L. R. (2004). *Memory systems of the brain: A brief history and current perspective*.
- Josselyn, S. A., Köhler, S., & Frankland, P. W. (2015). *Finding the engram*. DOI `10.1038/nrn4000`.
- Dudai, Y., Karni, A., & Born, J. (2015). *The Consolidation and Transformation of Memory*. DOI `10.1016/j.neuron.2015.09.004`.
- Kumaran, D., Hassabis, D., & McClelland, J. L. (2016). *What Learning Systems do Intelligent Agents Need?* DOI `10.1016/j.tics.2016.05.004`.
- Fowler, M. (2005). *Event Sourcing*.
- W3C (2013). *PROV-O: The PROV Ontology*.
- Snodgrass, R. T. (1999). *Developing Time-Oriented Database Applications in SQL*.
- Park et al. (2023). *Generative Agents*. arXiv `2304.03442`.
- Packer et al. (2023). *MemGPT*. arXiv `2310.08560`.
- Wang et al. (2023). *LongMem*. arXiv `2306.07174`.
- Zhong et al. (2023). *MemoryBank*. arXiv `2305.10250`.
- Gutiérrez et al. (2024). *HippoRAG*. arXiv `2405.14831`.
