# 2026-05-19 Taskpool done closeout audit

## Scope
- 按新 closeout 规则审计既有 `done` 任务：功能/集成类必须有真实链路验收；研究/咨询类必须有可读 artifact 与 acceptance mapping；`py_compile_taskpool PASS` 只能证明脚本语法，不再作为功能完成证据。
- 审计脚本：`/Users/charles/.hermes/scripts/taskpool_done_closeout_audit.py`

## Baseline before repair
- done_count: 142
- plausible_done: 23
- plausible_advisory_done: 7
- needs_manual_review: 1
- unchecked_acceptance_needs_review: 63
- implementation_done_missing_real_chain_validation: 48
- suspicious_count: 112

## Repair applied
- Reopened high-confidence P1 false-done tasks: 19
- Transition target: `pending`
- Audit evidence: `proof:manual_done_closeout_audit_2026-05-19`; `/tmp/taskpool_done_closeout_audit.json`

### Reopened P1 tasks
- `2026-05-14-为-2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移-细化-fallbac`
- `2026-05-14-为-2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移-细化-quota-o`
- `2026-05-14-为-2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移-细化-relay-o`
- `2026-05-14-为-hermes-设计-grace-call-输出结构化-continuation-packet-机制`
- `2026-05-14-为-hermes-设计-new-接-continuation-prefill-的会话恢复协议`
- `2026-05-14-为-taskpool-设计前置固定多模型优先级分析与入池分层机制`
- `2026-05-14-为预算耗尽自动接力设计-non-convergence-auto-narrowing-unblock-shim`
- `2026-05-14-分析-jcode-仓库并优化-hermes-自身多会话代理编排与边界闭环能力`
- `2026-05-14-对预算耗尽后的-grace-call-continuation-new-session-resume-机制做多模型分析并完善方案`
- `2026-05-14-补齐-brain-task-orchestrator-add-流程并在创建时强制写入优先级分层依赖顺序与多模型-triage-结果`
- `2026-05-15-为-2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略-细化-fallback-threshold-收敛前置任务`
- `2026-05-17-为-2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移-细化-relay-o`
- `2026-05-17-为-2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略-细化-framing-收敛前置任务`
- `2026-05-17-建设-hermes-长期可维护的-execution-quality-评估反馈基座以承接-evoagentx-演化闭环建议`
- `2026-05-17-建设-hermes-长期可维护的自动-skill-演化与-prompt-治理闭环以落地-evoagentx-agent-evolver-建议`
- `2026-05-17-沉淀系统提示词五大核心规则并治理-hermes-prompt-模块化与-truthfulness-约束`
- `2026-05-18-为-2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移-细化-patch-n`
- `2026-05-18-为-2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移-细化-relay-o`
- `2026-05-18-将-dreaming-长期经验沉淀与-outcomes-裁判分离机制映射为-hermes-技能复盘-独立质检闭环`

## After repair
- done_count: 123
- plausible_done: 23
- plausible_advisory_done: 7
- needs_manual_review: 1
- unchecked_acceptance_needs_review: 54
- implementation_done_missing_real_chain_validation: 38
- suspicious_count: 93
- suspicious_by_priority: {'': 1, 'P1': 18, 'P2': 69, 'P3': 5}

## Remaining buckets
### implementation_done_missing_real_chain_validation (38)
- P1 `2026-05-10-skill学习路线planning-with-files-文件化规划与上下文压缩抗丢失评估` — hermes-skill-learning / implementation/integration
- P1 `2026-05-10-skill学习路线superpowers-可组合开发流程与-tdd-brainstorming-适配评估` — hermes-skill-learning / implementation/integration
- P3 `2026-05-13-事件式-hook-验证任务创建后立即触发任务池流转` — local-brain / implementation/integration
- P3 `2026-05-13-事件式-hook-验证项目级策略无需预置任务-id` — local-brain / implementation/integration
- P2 `2026-05-13-分析-claude-mem-并优化-hermes-自身记忆-上下文机制` — hermes-agent / implementation/integration
- P2 `2026-05-13-分析-perplexity-agent-skills-文章并优化-hermes-自身技能体系与维护机制` — hermes-agent / implementation/integration
- P3 `2026-05-13-多模型自动-done-验证事件-hook-先认证再自动关闭` — local-brain / implementation/integration
- P1 `2026-05-14-为-2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略-细化-fallback-threshold-收敛前置任务` — hermes-agent / implementation/integration
- P1 `2026-05-14-为-2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略-细化-quota-observability-收敛前置任务` — hermes-agent / implementation/integration
- P1 `2026-05-14-为-2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略-细化-relay-ordering-收敛前置任务` — hermes-agent / implementation/integration
- P2 `2026-05-14-为-2026-05-14-分析-evoagentx-仓库并优化-hermes-自身进化式代理与自动改进机制-细化-quota-observability-收敛前` — hermes-agent / implementation/integration
- P2 `2026-05-14-为-2026-05-14-分析-evoagentx-仓库并优化-hermes-自身进化式代理与自动改进机制-细化-relay-ordering-收敛前置任务` — hermes-agent / implementation/integration
- P2 `2026-05-14-分析-keycompute-仓库并优化-hermes-自身模型路由-算力治理与观测能力` — hermes-agent / implementation/integration
- P2 `2026-05-14-基于-agent-harness-九大组件总结审计并优化-hermes-自身架构` — hermes-agent / implementation/integration
- P2 `2026-05-14-审计-hermes-上下文管理并优化压缩保真与连贯性` — hermes-agent / implementation/integration
- P2 `2026-05-14-审计-hermes-动态提示组装并优化实时注入与缓存命中` — hermes-agent / implementation/integration
- P2 `2026-05-14-审计-hermes-循环执行引擎并优化-ask-execute-observe-闭环` — hermes-agent / implementation/integration
- P2 `2026-05-14-审计-hermes-生命周期钩子并优化关键节点治理与安全护栏` — hermes-agent / implementation/integration
- P1 `2026-05-15-为-2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略-细化-quota-observability-收敛前置任务` — hermes-agent / implementation/integration
- P1 `2026-05-15-为-2026-05-14-为-hermes-设计预算耗尽后的自动接力与回退策略-细化-relay-ordering-收敛前置任务` — hermes-agent / implementation/integration
- P2 `2026-05-15-分析-memos-memos-local-plugin-源码与-hermes-本地插件文档并优化-hermes-本地记忆-任务总结-技能进化集成` — hermes-agent / implementation/integration
- P2 `2026-05-17-分析-agentmemory-仓库并提炼-hermes-在-hybrid-retrieval-shared-memory-server-与-hook-drive` — hermes-agent / implementation/integration
- P2 `2026-05-17-分析-dramadirector-仓库并提炼-hermes-在-schema-first-媒体编排stateful-cli-与-drop-in-skill-集成` — hermes-agent / implementation/integration
- P2 `2026-05-17-分析-hermes-agent-idea-workflow-仓库并提炼-hermes-在-ideaspechandoff-前置工作流与-skillpack-分发` — hermes-agent / implementation/integration
- P2 `2026-05-17-分析-hermesd-仓库并提炼-hermes-在只读-tui-监控面板全局状态聚合与-observability-dashboard-上的可吸收增量` — hermes-agent / implementation/integration
- P2 `2026-05-17-分析-meta-meta-prompting-文章并提炼-hermes-可吸收的-skillify-eval-retrieval-架构增量` — hermes-agent / implementation/integration
- P2 `2026-05-17-分析-paperclip-仓库并提炼-hermes-在公司级多智能体控制面预算治理与-heartbeat-编排上的可吸收增量` — hermes-agent / implementation/integration
- P2 `2026-05-17-分析-plur-仓库并提炼-hermes-在共享-engram-记忆层跨实例注入与-local-first-mcp-记忆上的可吸收增量` — hermes-agent / implementation/integration
- P3 `2026-05-17-分析-public-apis-仓库并提炼-hermes-在公共数据源发现免密-api-选路与外部实时信息接入上的可吸收增量` — hermes-agent / implementation/integration
- P2 `2026-05-17-分析-rtk-hermes-仓库并提炼-hermes-在-pre-tool-command-rewritertk-过滤输出与插件化-token-降耗上的可吸收增` — hermes-agent / implementation/integration
- P2 `2026-05-17-分析-tencentdb-agent-memory-仓库并提炼-hermes-在-symbolic-short-term-memory4-tier-progre` — hermes-agent / implementation/integration
- P2 `2026-05-17-建设-hermes-长期可维护的-workflow-generator-与-orchestration-plan-编译框架以吸收-evoagentx-启发` — hermes-agent / implementation/integration
- P1 `2026-05-18-为-2026-05-13-优化-agent-多模型-子-agent-调度的缓存命中率固定全局前缀分层上下文避免-prompt-工具序列漂移-细化-quota-o` — hermes-agent-cache-optimization / implementation/integration
- P2 `2026-05-18-分析-codex-plugin-cc-仓库并提炼-hermes-在-claude-codecodex-委派评审桥接background-job-生命周期控制面与` — hermes-agent / implementation/integration
- P2 `2026-05-18-分析-context7-平台并提炼-hermes-在最新代码文档检索版本化上下文注入与编码提示去幻觉上的可吸收增量` — hermes-agent / implementation/integration
- P2 `2026-05-18-分析-fireworks-tech-graph-仓库并提炼-hermes-在自然语言技术图表生成svgpng导出与-ai-工作流图模板上的可吸收增量` — hermes-agent / implementation/integration
- P3 `2026-05-18-分析-minimind-仓库并提炼-hermes-在轻量-llm-教学链路可解释训练实验与入门型模型实践上的参考价值` — external-repo-research / implementation/integration
- P2 `2026-05-18-分析-mirofish-仓库并提炼-hermes-在群体模拟预测长时记忆数字沙盒与-what-if-rehearsal-上的可吸收增量` — hermes-agent / implementation/integration

### unchecked_acceptance_needs_review (54)
- P1 `2026-05-08-本地大脑迁移残留闭环清理与-repair-plan-apply-验证` — local-brain-governance / implementation/integration
- P1 `2026-05-10-openai-openai-cli-沙箱评估与-hermes-api-自动化集成决策` — hermes-evolution / implementation/integration
- P1 `2026-05-10-skillclaw-沙箱评估与-hermes-技能进化集成决策` — hermes-evolution / implementation/integration
- P2 `2026-05-10-skill学习路线code-simplifier-重复逻辑合并与安全重构评估` — hermes-skill-learning / implementation/integration
- P1 `2026-05-10-skill学习路线mcp-builder-四阶段-mcp-server-引导与-hermes-mcp-skill-补强评估` — hermes-skill-learning / research/advisory
- P2 `2026-05-10-skill学习路线pptx-直接生成-pptx-文件与-hermes-productivity-流程评估` — hermes-skill-learning / research/advisory
- P1 `2026-05-10-skill学习路线skill-creator-官方元技能与-eval-测试框架适配评估` — hermes-skill-learning / research/advisory
- P2 `2026-05-10-skill学习路线ui-ux-pro-max-风格-配色库与-hermes-ui-审美基线评估` — hermes-skill-learning / research/advisory
- P1 `2026-05-10-从-hermes-hudui-提炼-hermes-native-replay-证据闭环与-hud-安全门` — hermes-agent / implementation/integration
- P1 `2026-05-10-增强本地任务池任务边界与多agent并行处理` — hermes-self-improvement / implementation/integration
- P1 `2026-05-10-多模型分析-agent-development-kit-图片并将-hermes-优化方案落地` — hermes-agentops-engineering / implementation/integration
- P2 `2026-05-12-用户端-底部导航栏第一个资产菜单内法币钱包列表下的人民币修改为cny` — uvisa-app-2.0-work / governance/policy
- P2 `2026-05-12-用户端-底部导航栏第一个资产菜单内点击u-visa-卡可用额度板块跳转到u-visa页面该页面文案和显示内容需要修改当没有任何u-visa卡片时候顶部的待激活应` — uvisa-app-2.0-work / governance/policy
- P2 `2026-05-12-用户端-底部导航栏第一个资产菜单内点击转入选择境内转账输入金额点击下一步收款信息页面点击下一步去app转账后到达挂单页面底部显示挂单已创建的时间未按照当前挂单创` — uvisa-app-2.0-work / governance/policy
- P2 `2026-05-12-用户端-点击我的点击安全中心在手机号这一行右侧缺少-未绑定-的初始化状态标识请设计一个未绑定的初始化标识` — uvisa-app-2.0-work / governance/policy
- P2 `2026-05-12-用户端-点击我的点击安全中心在邮箱这一行右侧缺少-未绑定-的初始化状态标识请设计一个未绑定的初始化标识` — uvisa-app-2.0-work / research/advisory
- P2 `2026-05-12-用户端-点击我的点击安全中心点击登录设备管理点击未信任设备顶部右上角齿轮后再点击设为信任设备然后刷新当前页面或退出账号重新登录后再次进入登录设备管理页面该设备仍` — uvisa-app-2.0-work / governance/policy
- P2 `2026-05-12-用户端-点击我的点击客服后与原型图中的不一致请查看评论区中原型图的文案进行1-1复刻其中红框中在没有联系客服之前的状态文案显示的是联系顾问开始对话已经联系过客服` — uvisa-app-2.0-work / governance/policy
- P2 `2026-05-12-用户端-点击我的点击退出登录时缺少确认退出登录弹框的功能请设计一个确认退出登录弹框` — uvisa-app-2.0-work / governance/policy
- P2 `2026-05-12-用户端-点击资产页面的兑换在支付币种输入框中输入几十位数字后文本直接超出输入框边界输入框未设置合理的金额长度-位数限制输入框中需设置合理的最大金额位数-数值限制` — uvisa-app-2.0-work / research/advisory
- P2 `2026-05-12-用户端-点击资产页面的兑换输入支付金额后显示汇率有效期倒计时等待倒计时结束后系统未自动重新调用接口刷新汇率页面始终显示-0-秒后刷新汇率数据不再更新当汇率有效期` — uvisa-app-2.0-work / governance/policy
- P2 `2026-05-12-用户端-登录时输入账号后使用密码登录连续输入错误密码超5次后的提示请求次数过多请稍后再试应改为密码错误次数过多账户已锁定-30-分钟` — uvisa-app-2.0-work / governance/policy
- P2 `2026-05-12-用户端-登录时输入账号和输入邮箱验证码点击登录后跳转至请输入支付密码页面输入错误支付密码后提示语为英文未跟随当前-app-的系统语言设置进行适配输入错误支付密码` — uvisa-app-2.0-work / governance/policy
- P2 `2026-05-12-用户端-登录时输入账号然后输入邮箱验证码后进行设置登录密码设置登录密码时输入7位数或8位以上纯数字或8位以上纯字母或纯文字或8位以上特殊符号的登录密码时点击完成` — uvisa-app-2.0-work / research/advisory
- P2 `2026-05-12-用户端-登陆帐号页面-点击底部联系平台客服按钮未跳转到客服中心` — uvisa-app-2.0-work / implementation/integration
- P2 `2026-05-13-分析-gbrain-仓库并优化-hermes-自身认知控制面与知识系统` — hermes-agent / research/advisory
- P2 `2026-05-13-分析-hindsight-仓库并优化-hermes-自身回溯记忆与知识工作流` — hermes-agent / research/advisory
- P2 `2026-05-13-分析-orca-仓库并优化-hermes-自身代理编排与执行工作流` — hermes-agent / research/advisory
- P2 `2026-05-13-分析-peekaboo-仓库并优化-hermes-自身能力与工作流` — hermes-agent / research/advisory
- P2 `2026-05-13-分析-rowboat-仓库并优化-hermes-自身协作与自动化工作流` — hermes-agent / research/advisory
- P2 `2026-05-13-分析-spec-kit-仓库并优化-hermes-自身规范驱动开发与工作流` — hermes-agent / research/advisory
- P2 `2026-05-14-为-2026-05-14-分析-evoagentx-仓库并优化-hermes-自身进化式代理与自动改进机制-细化-fallback-threshold-收敛前置` — hermes-agent / research/advisory
- P2 `2026-05-14-分析-cua-仓库并优化-hermes-自身计算机使用与代理执行能力` — hermes-agent / research/advisory
- P2 `2026-05-14-分析-evoagentx-仓库并优化-hermes-自身进化式代理与自动改进机制` — hermes-agent / research/advisory
- P2 `2026-05-14-分析-paseo-仓库并优化-hermes-自身代理运行时与工程化工作流` — hermes-agent / research/advisory
- P2 `2026-05-14-审计-hermes-会话持久化并优化崩溃恢复与审计追踪` — hermes-agent / research/advisory
- P2 `2026-05-14-审计-hermes-内置技能体系并优化开箱即用基础能力` — hermes-agent / research/advisory
- P2 `2026-05-14-审计-hermes-子智能体管理并优化并行调度与验证` — hermes-agent / research/advisory
- P2 `2026-05-14-审计-hermes-工具注册中心并优化能力显式化与权限边界` — hermes-agent / research/advisory
- P2 `2026-05-14-审计-hermes-权限与安全分层并优化高风险操作确认机制` — hermes-agent / research/advisory
- ... 14 more in `/tmp/taskpool_done_closeout_audit_after.json`

### needs_manual_review (1)
- - `2026-05-06-控制论基础理论补齐日志` —  / research/advisory

## Verification
- `brain_task_orchestrator.py selfcheck --json`: PASS
- `brain_task_orchestrator.py proof-check --json`: PASS
- Active task status after reopen: pending=23, retry=3, review=2, blocked=1
