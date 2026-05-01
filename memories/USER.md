用户偏好长时间自运行 Agent 工作流：P10(战略)→P9(任务拆解)→Loop(自动迭代执行)，每轮本地 git commit；除非明确要求，不 push 远程。要持续找新角度直到真正穷尽。
§
用户优化原则: 拒绝丢失功能与精准度，纯增益方案优先。arc-dispatch 项目路径: /Users/charles/Desktop/folder/arc-dispatch，前端项目在 work/ 目录。用户接受自然语言触发工作流（如"开始处理 lark 任务"）。
§
browser-harness 验证针对 work/ 目录项目优化: web-ui (Vue+Element UI 桌面端), uaec-h5 (Vue+Vant 移动端), partner-ui/excloud-ui (React+Ant Design 桌面端)。支持移动端 375px 和桌面端 1280px 视口测试。
§
用户偏好连续 exhaustive loop 执行：说"全部推进"时要求同时推进所有可识别方向，不逐个等待确认；接受自然语言触发大规模并行任务。对"loop并每次全部推进"的指令应理解为：找到所有可推进方向→并行执行→完成后扫描新方向→继续循环，直到用户明确喊停或确实穷尽。
§
供应商代码修补原则：vendor code 补丁被 `hermes update`（git pull）覆盖后，用 `~/.hermes/scripts/post-update-check.py` 自动检测并重打。不直接改 vendor 文件。先检查上游是否已修复（PR #15478 merge 等），避免重复劳动。修复模式 `--fix`。
§
多模型架构: OpenAI Codex/gpt-5.5 已接入(Plus/seat $20/月, codegen主力与cross-patch producer, 边际token成本按0但受滥用防护), MiMo用于低成本日常/T0与备用多样性, Claude用于P10架构/仲裁, DeepSeek按量审查。多模型印证优于单模型盲信。
§
用户对 uvisa-app 的工作模式偏好: (1) "loop 直至无问题" — 要求持续迭代到 0 差距, 不接受"留给后续"; (2) 多模型验证 — 架构决策需多视角审查印证最佳方案; (3) P10 每轮自检 — 每轮 loop 结束做 P10 自检确认真实进展; (4) "不改动UI展示" — 架构/功能填充时保持 UI 布局不变; (5) 全量覆盖 — 要求 PWA、埋点、错误捕获、测试等长期运行功能全部落地, 不留尾巴。
§
用户的 Hermes 是跟踪他人/上游仓库并持续自我调整的个人助理；仅使用 git 做本地版本管理，无需推送代码到远程。上游拉取属于更新升级；对其他项目的分析参考也视为 Hermes 更新进化的一部分，应按自进化规范管理。