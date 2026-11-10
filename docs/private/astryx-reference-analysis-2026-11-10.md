# Astryx 源码研究与有限增量吸收

schema: hermes_reference_review_v1
id: astryx-2026-11-10
source_repo: https://github.com/meta/astryx
source_commit: 42f1a7615f64c79598b2db67b876ea8789957285
local_checkout: /Users/charles/Code/astryx-reference
impact_classes: docs/skills
model_certification: not_run

## 目标、范围与唯一证据入口

本记录是本次外部项目研究事实的唯一持久化入口；通用操作方法另存技能参考，不在全局记忆复制。用户批准“小范围推进吸收增量”。成功标准是：记录固定源码与修正，将新方法接入现有技能并读回，保护已有未提交改动。非目标：安装或运行上游、引入依赖、修改业务项目、改 Hermes 运行时、部署或发布。

本轮读回确认上述 HEAD、origin URL，`git status --short` 无输出。结论仅适用于该提交，不代表上游未来版本。源码证据可由以下前缀加相对路径及行锚复核：
https://github.com/meta/astryx/blob/42f1a7615f64c79598b2db67b876ea8789957285/

## 源码事实与边界

| ID | 源码位置（仓库相对路径） | 支持的事实 | 不支持的推论 |
|---|---|---|---|
| C1 | `packages/core/src/Button/Button.doc.mjs:5–24,27–81,91–109` | 组件附近维护关键词、使用建议/反例、可访问性要求和 props 描述 | 文档列出要求不等于实测符合；描述内部也可能有宽泛说法与具体反例之间的张力 |
| C2 | `apps/docsite/scripts/generate-data.mjs:588–650`；`apps/docsite/src/app/mcp/route.ts:19–25,46–50,96–110` | 文档生成器扫描并 import 描述符；MCP 消费生成 registry，以 search 简述引导 get 详情 | 共享知识来源不等于 CLI/MCP 共用实时发现与检索实现，也不证明发布后快照一致 |
| C3 | `packages/core/src/utils/themeProps.ts:31–69` | 稳定类名及规范 data 属性形成主题可寻址表面 | 主题机制不能承担业务提交、权限或导航闭环；这些属性本身不证明完整主题兼容 |
| C4 | `internal/vibe-tests/src/interactive.ts:804–838` | 提示直接包含 Expected Components，要求生成者自评并输出 success/escapeHatches | 不能把 README 的公平性规范概括为所有评测路径都答案盲测或独立判定 |
| C5 | `internal/vibe-tests/src/universal-eval.ts:198–234` | correctness 维度使用 tsc 结果或 phantom-prop/结构规则回退 | 类型或文本规则成功不证明业务交互正确 |
| C6 | `packages/cli/foundation/doc-compiler/read.mjs:53–60`；`packages/cli/foundation/doc-compiler/import.mjs:3–22,25–32`；同 C2 生成器第650行 | 描述符加载涉及原生模块导入或 jiti，属于执行代码的信任边界 | 未发现恶意行为；也不能因文件名带 doc 就将加载视为纯数据读取 |
| C7 | `apps/docsite/src/__tests__/mcp-server.test.ts:24–30,37–43` | keywordIndex 直接复用真实模块，评分逻辑则镜像 route，未直接导入 Next route handler | 不能说所有测试均为复制品；镜像评分测试也不能独立证明真实路由返回正确 |

## 修正与未验证项

- 保留纠错：早先对“评测不暴露预期组件”的概括过宽；C4 是实际执行路径的反证。生成与判定是否独立必须逐路径核验。
- “没有 MCP 文件名”不等于没有 MCP；实际入口见 C2。
- 项目方规模/成熟度宣传不作为选型或已验证事实。官网先前主题预览观察不作为本轮持久化验收证据。
- CLI 全命令行为、发布组合、主题深度定制/swizzle 接管出口、无障碍达标及实际业务闭环，均未在本轮运行验证。源码阅读不等于执行通过。

## 吸收决策与落点

即时落地：为 `codebase-intelligence` 添加条件加载入口及 `references/agent-facing-design-system-contracts.md`。只固化以下可检验方法：
1. 组件契约就近维护、渐进发现；多入口同源仍需检验快照与接口差分。
2. 品牌主题、组件交互和业务流程分责；需要深定制时先调查已有源码接管出口及升级责任，不强制创建新机制。
3. 按 oracle 的真实证据能力分级；核答案泄露、镜像测试和描述符执行边界。

这些是有条件的设计/审计方法，不是决定采用 Astryx 或其技术栈。真实项目采用须另定目标、保持现有能力并补消费侧正负交互证据。未授权或未实施：依赖安装、运行时变更、自动任务、业务迁移、外部发布。未进行模型认证。

## 验证与回退契约

持久化验证：读回主技能和新增参考；校验入口链接、源码路径/行范围、固定提交及上游工作区状态；检查本次 Git 增量仅含上述两个技能文件和本记录。结构/文本检查不等于模型已遵循新方法，也不等于产品效果改进。

主技能原本有未提交改动；保留其写前副本与原暂存区快照，提交只包含本次新增入口及新文件，不打包既有改动。不推送。

回退时先确认文件没有后续变更，再仅移除本次入口和本次新增参考/记录，或逆向应用本次提交；不得恢复整个主技能到 HEAD 而丢弃既有脏改动。实际验证命令与提交由当前执行回执提供，不能把此处计划视为已完成证据。
