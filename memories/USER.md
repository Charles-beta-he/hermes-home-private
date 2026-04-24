用户偏好长时间自运行的 Agent 工作流：P10(战略)→P9(任务拆解)→Loop(自动迭代执行)，每轮 git commit + push，直到所有任务完成。不接受"没有新提案就停"——要持续找新角度直到真正穷尽。
§
用户优化原则: 拒绝丢失功能与精准度，纯增益方案优先。arc-dispatch 项目路径: /Users/charles/Desktop/folder/arc-dispatch，前端项目在 work/ 目录。用户接受自然语言触发工作流（如"开始处理 lark 任务"）。
§
browser-harness 验证针对 work/ 目录项目优化: web-ui (Vue+Element UI 桌面端), uaec-h5 (Vue+Vant 移动端), partner-ui/excloud-ui (React+Ant Design 桌面端)。支持移动端 375px 和桌面端 1280px 视口测试。
§
用户偏好连续 exhaustive loop 执行：说"全部推进"时要求同时推进所有可识别方向，不逐个等待确认；接受自然语言触发大规模并行任务。对"loop并每次全部推进"的指令应理解为：找到所有可推进方向→并行执行→完成后扫描新方向→继续循环，直到用户明确喊停或确实穷尽。