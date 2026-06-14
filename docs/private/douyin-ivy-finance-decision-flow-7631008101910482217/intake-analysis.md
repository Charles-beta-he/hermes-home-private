# Douyin intake — 常青藤金融毕业生决策流程 / TradingAgents reference

- Source short URL: `https://v.douyin.com/13xVwJygPnw/`
- Canonical: `https://www.douyin.com/video/7631008101910482217`
- IES extraction URL: `https://www.iesdouyin.com/share/video/7631008101910482217/`
- Author: 程序员少北晨 (`shaobeichen`)
- Description: `据说这是常青藤金融毕业生决策的一套流程 #AI工具 #OpenClaw #skill #开源项目`
- Published: 2026-04-21 11:50:00
- Stats at extraction: 15,232 likes, 15,495 collects, 2,855 shares, 81 comments
- Local evidence: `/Users/charles/.hermes/docs/private/douyin-ivy-finance-decision-flow-7631008101910482217/`

## Media evidence

- `router_item.json` — extracted Douyin metadata
- `video.mp4` — downloaded video
- `frames/frame_*.jpg` — sampled frames
- `contact_frames.jpg` — OCR/contact sheet

## OCR / visible content

The video shows and explains `TauricResearch/TradingAgents`:

- GitHub user: `Yijia Xiao` / `Yijia-Xiao`
- Project: `TauricResearch/TradingAgents`
- Visible repo title: `TradingAgents: 多智能体 LLM 金融交易框架`
- Visible/voice claims: already over 50k GitHub stars at video time; at fresh verification it has ~85.9k stars.
- Core visible phrase: “这不是一个自动下单软件”, “更像华尔街投资公司的决策架构”, “多个 AI 金融分析师”, “最终形成交易决策”, “模拟真实长期华尔街毕业生在金融公司决策的一套流程”.

Visible architecture pages include:

### TradingAgents framework

The diagram shows a multi-agent trading-decision pipeline:

- Analysts gather multiple data channels:
  - market/trading data
  - news/social sentiment
  - fundamentals
  - social media sources such as Yahoo/Reddit/Google news style inputs
- Analyst opinions enter a debate / research process:
  - bullish researcher
  - bearish researcher
  - research manager
- Trader produces transaction proposal.
- Risk management and portfolio management stages evaluate the decision.
- Final execution is represented as the last stage.

### Analyst team

Visible text describes an analyst team that specializes in evaluating company financial conditions and market metrics:

- Fundamentals Analyst
- Sentiment Analyst
- News Analyst
- Technical Analyst

### Research team

Visible debate goal cards:

- Bullish researcher goal: “Evaluate the investment potential of Apple Inc.”
- Bearish researcher goal: “Assess the risks of investing in Apple Inc.”
- The team debates and distills opposing views before a final recommendation.

### Trader / Transaction agent

Visible goal cards include:

- Trader goal: evaluate and make decision on recommended transactions.
- Example decision card: `Buy Apple Inc. Trading Decision`.
- Final plan/recommendation: buy for long-term growth despite short-term risk.

### Risk management and portfolio management

Visible cards include:

- Risky Analyst
- Safe Analyst
- Neutral Analyst
- Portfolio Manager

The video positions the flow as financial-company style deliberation: multiple analysts + debate + trader + risk + portfolio.

## Verified external source

GitHub API verification for `TauricResearch/TradingAgents`:

- URL: `https://github.com/TauricResearch/TradingAgents`
- Description: `TradingAgents: Multi-Agents LLM Financial Trading Framework`
- Language: Python
- License: Apache-2.0
- Created: 2024-12-28
- Updated: 2026-06-14
- Stars at verification: ~85.9k
- Forks at verification: ~16.6k
- README references arXiv `2412.20138` and recent releases with structured-output agents, checkpoint resume, persistent decision log, multi-model/provider support, ticker path-traversal hardening.

The hashtag mentions `OpenClaw`, but no canonical OpenClaw source was verified from the video itself. Treat OpenClaw as distribution/context tag, not as evidence for the decision flow.

## What it really is

This is a **multi-role financial decision deliberation framework**, not a safe auto-trading recipe.

The reusable architecture is:

```text
multi-source evidence
→ specialized analysts
→ adversarial bull/bear research debate
→ research manager synthesis
→ trader proposal
→ risk committee
→ portfolio manager
→ decision log / execution boundary
```

For Hermes, the key is not trading. The key is **role-separated, evidence-backed, adversarial decision governance**.

## Transferable Hermes patterns

### 1. Decision workflow as committee, not one-shot answer

Useful for high-impact decisions:

- investment / business decision
- product direction
- security approval
- deployment gate
- taskpool closeout
- architecture migration

Hermes can model:

```text
Evidence Analysts -> Pro/Con Debate -> Synthesis Manager -> Executor Proposal -> Risk Review -> Human Gate
```

### 2. Bull/Bear debate as structured alternative testing

The bull/bear split is better than generic “pros/cons” when stakes are high:

- Bull case: why this should work / upside / opportunity
- Bear case: why it fails / downside / hidden risk
- Manager: what survives both sides

### 3. Risk committee before execution

Execution should be separated from analysis. For Hermes, the pipeline should distinguish:

- analysis recommendation
- proposed side effect
- risk review
- permission/human gate
- execution
- read-back evidence

### 4. Decision log / checkpointing

The verified README mentions persistent decision log and checkpoint resume. This maps to Hermes evidence/taskpool ledgers: any high-impact recommendation should preserve assumptions, sources, debate summary, chosen path, and rejected alternatives.

## What not to copy

- Do not use this as auto-trading or financial advice.
- Do not let social/GitHub popularity substitute for backtesting, market data provenance, or risk controls.
- Do not execute trades or place orders.
- Do not claim “Ivy League” quality; the video phrase is marketing framing.
- Do not import TradingAgents runtime into Hermes during intake.
- Do not treat OpenClaw hashtag as verified dependency.

## Recommended absorption

Create a Hermes evolution task for a **decision-committee workflow pattern**:

- Generalize TradingAgents into non-trading governance:
  - evidence collectors
  - domain analysts
  - adversarial pro/con researchers
  - synthesis manager
  - risk reviewers
  - executor proposal
  - human approval gate
- Add templates for:
  - bull case
  - bear case
  - evidence table
  - risk register
  - decision log
  - execution boundary
- Keep financial/trading use read-only and advisory unless separate backtest/risk-engine/paper-trading gates exist.

## Initial verdict

Worth learning as a **decision-governance pattern**. It is highly relevant to Hermes goal-calibration and taskpool gate design, but unsafe to absorb as a trading executor.

Best one-line abstraction:

```text
重大决策不要让一个 Agent 直接拍板；先让多角色用证据互相打穿，再由风险门禁决定是否允许执行。
```
