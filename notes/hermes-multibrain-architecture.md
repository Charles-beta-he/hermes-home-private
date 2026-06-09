# Hermes 多脑系统方案续讨论备忘

更新时间：2026-05-18

## 目标

下次继续讨论并落地：把本地 Hermes 设计为“单 Runtime + 多 Brain Overlays”的个人 AI 操作系统。

## 当前共识

1. 本地只需要一个 Hermes Runtime。
   - Runtime 负责 CLI、agent loop、tools、memory、skills、taskpool、cron、conductor、多模型路由。
   - 不需要安装多套 Hermes。

2. 不做“角色扮演替换内核”。
   - 内核不变。
   - 通过 Brain Overlay 加载不同领域脑包。
   - 角色 prompt 只是最低级实现，正式方案应包含 profile、skills、toolsets、memory scope、taskpool scope、verification rules、permission rules。

3. 主脑与副脑关系。
   - 主脑：聊天入口、意图识别、任务派发、上下文治理、验收仲裁、自进化沉淀。
   - 副脑：领域专业执行、领域资料/记忆、领域 SOP、领域验证、领域任务池、领域进化 proposal。

4. 一级副脑按长期方向拆，不按端拆。
   - 程序开发副脑
   - 量化交易副脑
   - 短视频运营副脑
   - 研究情报副脑
   - 学习成长副脑
   - 个人助理副脑
   - Hermes 内核副脑

5. 端区分先作为开发副脑内部 profile。
   - 前端 profile
   - 后端 profile
   - 管理端 profile
   - 契约 profile
   - DevOps profile
   - UI/UX profile
   - Hermes 内核 profile

6. 应冻结初始领域脑包。
   - 冻结 base-brain@0.1.0 作为所有副脑基线。
   - 冻结 main-brain@0.1.0、dev-brain@0.1.0、hermes-core-brain@0.1.0。
   - 后续 quant/video/research 等从 base fork。
   - 冻结不是停止进化，而是建立基线、版本、changelog、回滚。

7. Hermes 升级策略。
   - Hermes Runtime 升级后，所有副脑天然运行在新内核上。
   - Brain Overlay 不应该被自动修改。
   - 正确原则：内核同步升级，脑包受控升级。
   - Runtime update 后需要 post-update-check、brain compatibility check、domain brain smoke tests。

## 建议目录

```text
~/.hermes/brains/
├── base/
│   ├── brain.yaml
│   ├── constitution.md
│   ├── evidence-packet.md
│   ├── memory-policy.md
│   ├── tool-policy.md
│   └── evolution-protocol.md
├── main/
│   ├── brain.yaml
│   ├── routing-matrix.md
│   ├── subbrain-registry.md
│   └── acceptance-policy.md
├── dev/
│   ├── brain.yaml
│   ├── profile.md
│   ├── tool-policy.md
│   ├── verification.md
│   ├── routes/
│   │   ├── frontend.md
│   │   ├── backend.md
│   │   ├── contract.md
│   │   └── devops.md
│   └── changelog.md
├── quant/
├── video-ops/
└── registry.yaml
```

## 初始冻结清单

最小可执行版优先创建：

1. `~/.hermes/brains/base/brain.yaml`
2. `~/.hermes/brains/main/brain.yaml`
3. `~/.hermes/brains/main/routing-matrix.md`
4. `~/.hermes/brains/base/evidence-packet.md`
5. `~/.hermes/brains/dev/brain.yaml`
6. `~/.hermes/brains/dev/profile.md`
7. `~/.hermes/brains/registry.yaml`

## Evidence Packet 模板

```text
任务：
领域：
输入上下文：
执行摘要：
产物/变更：
验证证据：
风险：
未完成项：
需要主脑决策：
建议沉淀：
建议后续任务：
版本影响：
```

## 升级/演化流程

1. 发现问题或机会。
2. 分类：memory / skill / profile / route / verification / tool permission / runtime compatibility。
3. 提出变更 proposal。
4. 主脑审核。
5. 修改对应 brain overlay。
6. 更新版本号和 changelog。
7. 跑 smoke test / compatibility check。
8. 通过后标记 stable；失败可回滚。

## 下次继续讨论切入点

- 是否直接创建 `~/.hermes/brains/` 初始目录和 7 个最小文件。
- 是否把 Brain Overlay 注册到 Hermes 现有 skill/profile/taskpool 体系。
- 设计 `brainctl` 或脚本：`brainctl list|show|check|smoke|upgrade`。
- 定义 base/main/dev/hermes-core 的 v0.1.0 具体 YAML schema。
- 定义 Hermes Runtime update 后的 brain compatibility check。
