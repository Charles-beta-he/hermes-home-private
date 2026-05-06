---
type: moc
status: active
created: 2026-05-06T08:48:00Z
folder: 60-reviews
---

# L6 Reviews 评审层

## 用途

多模型评审、架构审查、自检报告；必须标注证据边界。

## 收录规则

- 只收与本目录语义直接相关的 Markdown artifact。
- 每个新增笔记应有清晰标题、来源/边界、与其他目录的链接。
- 任务/WIP 放入 `30-tasks/` 并设置 expiry；稳定事实再晋升到 atoms/project/review。
- 不保存真实凭证、token、password、connection string；如出现统一写 `[REDACTED]`。

## 当前直接笔记

- [[60-reviews/2026-05-06-hermes-brain-hierarchy-multi-model-review|2026-05-06-hermes-brain-hierarchy-multi-model-review]]
- [[60-reviews/2026-05-06-multimodel-thinking-keypoint-coverage-review|2026-05-06-multimodel-thinking-keypoint-coverage-review]]
- [[60-reviews/2026-05-06-multimodel-thinking-landing-and-fill-review-log|2026-05-06-multimodel-thinking-landing-and-fill-review-log]]

## 子目录

- 无直接子目录。

## 维护规则

每次本目录新增 3 个以上笔记，更新本索引；每次本地大脑结构变更后运行 `brainctl sync && brainctl reindex && brainctl search` 验证。
