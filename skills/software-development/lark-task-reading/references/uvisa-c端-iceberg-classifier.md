# C端 Lark 任务冰山分析分类器

> **Superseded** by `references/uvisa-unified-iceberg-multimodel-consensus.md` for new work. This file remains as the C端-specific reference implementation. The unified classifier handles both admin and C端 tasks with a single script.

## 概述

C端（用户端）Lark 任务的 scope 分类不能用正则匹配——中文任务标题描述的是用户操作路径（"点击底部导航栏资产→转出→跨境汇款→输入金额→下一步"），不是技术实现描述。正则会把 90% 的任务误判为"需后端"。

冰山分析器从任务全文做语义信号提取，用权重决策树确定真实 scope。

## 脚本

```bash
python3 ~/.hermes/scripts/uvisa_c端_lark_classifier.py \
  --input ~/.hermes/evidence/lark-sync/uvisa-app-2.0/live-tasks.json \
  --scope c端 \
  --out-dir /tmp/uvisa_c端_iceberg \
  --json
```

## 分层决策树（权重优先级）

1. **B (human_required)** — human_weight ≥ 4：明确说"AI无法"/"人工介入"/"原型缺失"
2. **L (requires_backend)** — backend_weight > 0 且 ≥ fe_logic_weight 且 ≥ ui_weight：
   - `amount_mismatch` (w=4)：到账 vs 发送金额不一致
   - `money_amount_with_currency` (w=3)：具体金额+币种
   - `wallet_balance_logic` (w=3)：余额不足/最多可充值
   - `fx_rate_logic` (w=3)：汇率/兑换/报价
   - `remittance_flow` (w=3)：跨境汇款/SWIFT
   - `websocket_realtime` (w=3)：实时通信/站内信
   - `api_data_issue` (w=3)：需要接入真实数据接口
   - `otp_verification` (w=2)：验证码/OTP
   - `admin_config_dependency` (w=2)：admin后台配置→C端联动
   - `pwa_installation` (w=2)：PWA安装弹窗
3. **F (frontend_logic)** — fe_logic_weight > 0 且 ≥ ui_weight：
   - `navigation_routing` (w=2)：跳转/路由/导航
   - `state_display_logic` (w=2)：处理中/已完成状态
   - `data_formatting` (w=2)：金额格式/适配
   - `transaction_display` (w=2)：交易记录/列表
4. **S0/S1 (simple_ui / compound_ui)** — ui_weight > 0：
   - `visual_parity` (w=1)：1:1复刻/文案/色值
   - `loading_empty_state` (w=1)：骨架屏/空状态
   - `modal_ui_style` (w=1)：弹窗UI样式
   - `layout_overflow` (w=1)：截断/溢出/布局
   - 有截图证据 +1
5. **F (frontend_logic_inferred)** — 通用前端关键词兜底（显示/页面/弹窗/状态/格式/写死/未区分/缺少...）
6. **M (needs_triage)** — 无任何信号

## 域推断

从标题语义聚类推断功能域（不用正则匹配）：
- asset: 钱包/余额/转入转出/交易记录
- exchange: 汇率/币种/兑换
- remit: 跨境/收款人/SWIFT
- topup: 充值/U-VISA/活期宝
- notification: 通知/消息/站内信
- wealth: 理财/持仓/收益/赎回
- auth: 登录/注册/验证/安全中心

## 2026-05-28 首次运行结果

| Tier | 数量 | 含义 |
|---|---|---|
| F | 22 | 前端逻辑 |
| L | 18 | 需后端/接口打通 |
| S0/S1 | 0 | C端确实没有纯快修任务 |
| B | 0 | 无明确人工需求 |

域分布：asset=16, auth=5, topup=4, notification=4, wealth=3, remit=3, exchange=2, unknown=3

与 admin 矩阵对比：
- admin 矩阵（正则）把 90% C端任务误判为 L（需后端）
- 冰山分析准确区分 F(22) vs L(18)

## 关键设计原则

1. **不使用正则做分类决策**——信号提取用语义关键词，决策用权重比较
2. **短语分句是核心**——按中文标点拆分标题，每句独立分析
3. **通用前端关键词兜底**——当无特定信号时，用"显示/页面/状态/格式"等通用词判断为 F
4. **权重可调**——`iceberg_signals` 字段记录了每个信号的权重和证据，便于校准
5. **与 admin 矩阵互补**——admin 用 regex 矩阵（`uvisa-admin-lark-fasttrack-closeout.md`），C端用冰山分析

## 回写字段

分类结果写入任务池 frontmatter：
```yaml
iceberg_tier: L          # S0|S1|F|L|M|B
iceberg_scope: requires_backend
iceberg_domain: remit
iceberg_confidence: high
iceberg_signals: [...]    # 最多5个关键信号
```

## Dispatch 集成

iceberg_tier 已接入 taskpool dispatch 系统（2026-05-28）：
- **Score 加权**：S0=+12, S1=+10, F=+8, L=-3, B=-15 → F 任务排在 L 前面
- **Preflight 门禁**：lane=work + project 有值但缺 source_weighting_policy_ref → 不可 dispatch
- **Work Contract 原子**：L 任务自动加 `A-backend-contract` 验收原子，B 任务加 `A-human-confirmation`
- **Dashboard**：新增 Iceberg Tier Distribution 区块 + 排序表 Tier 列

集成代码在 `brain_task_orchestrator.py`（score/preflight/dashboard）和 `uvisa_lark_work_contract.py`（contract atoms）。通用集成模式见 `taskpool-control-plane/references/iceberg-tier-dispatch-integration.md`。

## 已知局限

- 依赖任务标题质量——标题越详细，分类越准
- 评论/关联文档的信号提取较弱（当前主要分析标题）
- 无法区分"前端调后端API"和"纯前端逻辑"——需要人工判断具体接口依赖
- 域推断可能重叠（如 asset+exchange）
