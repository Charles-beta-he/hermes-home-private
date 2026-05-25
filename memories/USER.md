改码前先fetch/pull防覆盖；优先patch skill；短指令未指对象按助手自身纠偏；模糊UI“对齐/处理”需先问对象/参考/验收。
§
用户是贺程，西安资深前端工程师；强项 React/Vue/TS/工程化/组件库/性能/测试。目标：远程居家，薪资 3737U；区块链/金融为职业方向/课程学习。优化原则：不丢功能、不降精度、纯增益。arc-dispatch: `/Users/charles/Desktop/folder/arc-dispatch`，可自然语言触发。
§
用户常用 browser-harness 验证 work/ 项目；Lark/UI验收截图默认用14寸浏览器界面，仅明确移动H5时用375px。验收严禁 mock，除非用户明确允许；必须真实认证/真实后端/真实接口数据。
§
用户偏好 taskpool 更独立：外部仓库/文章类任务应在创建入池前完成固定的多模型优先级分析与 P1/P2/P3 分层，而不是入池后再分析优先级；任务池停住时主动查 hook/cron/policy/eligibility/tick。
§
Vendor 补丁原则：`hermes update` 后用 `~/.hermes/scripts/post-update-check.py --fix` 检测/重打；不直接改 vendor；先查上游是否已修复，避免重复劳动。
§
多模型架构: Codex/gpt-5.5 codegen主力, MiMo低成本T0/备用, Claude P10架构/仲裁, DeepSeek审查；多模型=真实外部模型印证，不等同单模型多角色模拟。
§
红线=不删功能/入口/字段、不修坏H5；PAD不得直接写`kyc_level`授权，须走KYC证据/能力映射。Entity字段变更须检查Flyway migration+确认prod已执行(2026-05-16教训)。画像=canonical profile；必要时TDD修BE。
§
Hermes自身已有私仓，改动完成并验证后可push；项目代码默认不push；长任务需可恢复审计验证。
§
项目/Lark/代码查询需evidence-first+关联面全盘覆盖；work可跨admin/app/backend改动；blocked不阻塞其他任务；先判落点FE/BE/契约/基础设施。
§
用户偏好：任务入池带顺序/依赖；增强任务主链闭环+真实验证；后续任务自动化触发；所有方案默认生产长期级，先多角度审查再给最终版。
§
人工流程沉淀为Hermes skill；多脑结构下，按项目仓库包含范围选择的全局最佳方案/共识规则写公共Hermes共识，项目特定锚点/红线/验证命令写profile。
§
人物画像：长期主义/系统化/证据优先；讨厌假完成；自我优化要按边界落地。
§
Lark闭环SSOT：uvisa-app-2.0有线上地址+完整发布流程，Lark任务必须线上地址UI回收/验收后才能关闭；代码合并/build/proof只到待验收。
§
用户要求 Hermes 自身（~/.hermes scripts/skills 等）改动也必须用 git 做 scoped commit 管理，避免只改不提交。