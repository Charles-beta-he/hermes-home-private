# Douyin 图文：4大交易系统全套意图识别分析

Captured: 2026-06-14

## Source

Original share text:
> 4.15 复制打开抖音，看看【AU萧沐晨（猫叔）的图文作品】4大交易系统全套意图识别，等你来点评。1️⃣开始交... https://v.douyin.com/K__B7SlZFUQ/ :6pm e@O.kp lPx:/ 04/05

Resolved:
- short: https://v.douyin.com/K__B7SlZFUQ/
- share: https://www.iesdouyin.com/share/note/7650744842159774902/?from_ssr=1
- canonical: https://www.douyin.com/note/7650744842159774902

Metadata extracted from router data:
- aweme_id: `7650744842159774902`
- author: `AU萧沐晨（猫叔）`
- desc: `4大交易系统全套意图识别，等你来点评...`
- create_time: 2026-06-13
- stats at capture: 80 likes, 101 collects, 18 shares, 0 comments
- images_count: 12
- evidence dir: `/Users/charles/.hermes/docs/private/douyin-trading-intent-systems-7650744842159774902/`

## Main content

The post is a screenshot carousel describing a trading-agent intent-recognition and system-selection layer. It maps market state into four trading systems:

1. `trend_scalp` 趋势刷单
2. `key_levels` 卡单系统
3. `channel_t` 通道做T
4. `lock_range` 震荡锁单

User commands visible in caption:
- `开始交易`: synchronize real-time data, output recommended system + reason, start a 4-minute wall-tracking heartbeat.
- `结束交易`: stop automated heartbeat/tracking.
- `墙体追踪 — 做市商雷达`: every 4 minutes scan wall displacement, force/兵力 change, spoofing/fake walls.
- `展开波段 — 倒V猎杀路径图`: caption mentions this, but detailed slide content is not fully visible in extracted images.

## Six-factor scoring model

Visible formula: total score is six weighted dimensions, each likely 0-10 then weighted:

- intent match / 意图匹配: 20%
- wall proximity / 墙体逼近度: 22%
- OI highness / OI 背离或高度: 20%
- λvol vulnerability / λvol 脆弱度: 18%
- Jump: 10%
- channel / 通道: 10%

The output chooses the highest-scoring system and reports a reason.

## Dimension notes

### 意图匹配度
Classifies intent into categories like:
- `directional`: directional breakout/trend
- `wall_bound`: wall constraint / stop-hunt around orderbook wall
- `range_bound`: range / market-maker control

Data source visible: `order_flow_intent.py scan -> memory/order_flow_intent.json -> intent`.

### 墙体逼近度
Measures distance to orderbook wall in ATR units and direct distance. Visible thresholds:
- <=0.5 ATR / within tight wall = high score
- 0.5-1.0 ATR = wall approaching
- 1.0-1.5 ATR = moderate
- >2.5 ATR = low score

Also uses wall force / wall cluster info from `bid_clusters` / `ask_clusters`.

### OI 高度
Formula shown: `OI综合 = OI_热变化率 * 0.6 + OI_4h变化率 * 0.4`.
It maps OI + price moves into cases such as 爆多/爆空/空头被扎/吸筹/派发.
Data sources visible: `okx_data_bridge.py sync -> price_cache.json -> oi_history`.

### λvol 脆弱度
Formula shown: `λvol = σ(5根15m蜡烛) + σ(20根15m蜡烛)`.
Buckets:
- >2.0: market very fragile / 市场极脆
- 1.2-2.0: somewhat fragile
- 0.8-1.2: neutral
- 0.4-0.8: thick / quiet
- <0.4: very thick, suitable for range/做T

## Four systems

### System 1: 趋势刷单 `trend_scalp`
Intent: price has broken key area and market continues in a direction. Uses OI divergence, λvol > 1, jump detection. The slide frames it as continuation / FOMO / market-maker push after a breakout.

### System 2: 卡单系统 `key_levels`
Intent: price approaches a wall / stop-loss pile. Looks for wall-bound intent, wall force, entry near wall price ±0.3 ATR, and stop-hunt continuation or fake breakout. It is the system chosen in the test screenshot.

### System 3: 通道做T `channel_t`
Intent: price oscillates inside an inclined channel. Buy near lower rail, sell near upper rail. Conditions include detected channel, λvol < 0.8, OI stable, no jump.

### System 4: 震荡锁单 `lock_range`
Intent: no trend, no wall, no channel; price is in a range. Conditions include wall distance >2.5 ATR, no channel, λvol < 0.4, and `range_bound` intent. Operates as upper-range short / lower-range long, waiting for confirmed breakout before reversing.

## Test output shown

A user says: `测试一下，开始交易`.
The bot replies:
- trading started
- system judgment: `卡单系统 -> 距压制墙 4228.800 仅 29.5 点，兵力 180K 手`
- wall-tracking heartbeat enabled; every 4 minutes scans wall displacement, force changes, spoofing fake wall, breakpoint expansion, λvol changes.

Another screenshot shows heartbeat messages with:
- 波动 around 4228
- upper/lower walls and distances
- targets such as integer level stop-loss clusters / low-wall hunting reversal
- bid/ask liquidity and wall movement to 4255.4, interpreted as market-maker lifting zone.

## Interpretation

This is not a finished quantified strategy proof. It is a trading-agent decision router / intent classifier spec. It combines orderbook walls, OI, volatility, jump/channel signals, and free-text commands into an agent that picks one of four playbooks and keeps monitoring walls every 4 minutes.

Value:
- Clear separation between intent recognition and execution playbook.
- Explicit weights and thresholds make it auditable.
- Heartbeat monitor / stop command pattern is useful for agent safety.
- Good example of turning trading slang into structured state machine.

Limitations:
- No backtest, no exchange/market/timeframe validation, no PnL evidence.
- Thresholds look hand-tuned; high overfit risk.
- Orderbook wall/spoofing signals are noisy and exchange-dependent.
- No explicit risk management: position sizing, stop loss, max loss, leverage, slippage, fees, liquidation, news/event filters.
- `兵力`, `墙体`, `λvol` need formal definitions and deterministic data source contracts.

Recommended absorption:
- Treat as a pattern for intent-router/state-machine design, not as trade advice.
- If adopted, first implement as read-only classifier/backtest harness.
- No live trading until there is deterministic replay, exchange adapter spec, risk engine, paper-trading proof, and human approval.
