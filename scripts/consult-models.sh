#!/usr/bin/env bash
# consult-models.sh — 多模型 fan-out 编排器 (v2: 替代 consult-claude.sh)
# 并发调用 N 个 planner 模型，收集计划，运行 consensus，输出合并方案
#
# 用法: bash consult-models.sh <state.json> [--quorum N] [--tier T2]
# 输出: merged_plan.json 到 stdout
#
# 环境变量:
#   MULTI_BRAIN_QUORUM=3         # 默认 3
#   MULTI_BRAIN_TIER=T2          # 默认 T2
#   SKIP_CLAUDE=1                # Claude budget 不足时自动设置

set -euo pipefail

STATE_FILE="${1:-}"
QUORUM="${MULTI_BRAIN_QUORUM:-3}"
TIER="${MULTI_BRAIN_TIER:-T2}"
SKIP_CLAUDE="${SKIP_CLAUDE:-0}"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
TICK_DIR="$HERMES_HOME/tick-$(date +%Y%m%d-%H%M%S)"
PLANS_DIR="$TICK_DIR/plans"

if [ -z "$STATE_FILE" ] || [ ! -f "$STATE_FILE" ]; then
  echo "Usage: consult-models.sh <state.json>" >&2
  exit 1
fi

mkdir -p "$PLANS_DIR"

# ── 1. 选择 planner 模型 ──
echo "[multi-brain] Selecting $QUORUM planners for tier=$TIER..." >&2

# 从 model-router 获取候选
PLANNERS=$(python3 "$HERMES_HOME/scripts/model-router.py" select-pair \
  --task-tier "$TIER" 2>/dev/null | \
  python3 -c "
import sys, json
d = json.load(sys.stdin)
models = []
# producer + reviewer (去重)
for role in ['producer', 'reviewer']:
    m = d.get(role, {}).get('model', '')
    if m and m not in models:
        models.append(m)
print(','.join(models[:$QUORUM]))
" 2>/dev/null)

# Fallback: 硬编码默认池
if [ -z "$PLANNERS" ]; then
  PLANNERS="mimo-v2.5-pro,deepseek-v4-pro"
  # 如果 Claude budget 充足且未跳过, 加入
  if [ "$SKIP_CLAUDE" != "1" ]; then
    ALLOWED=$(python3 "$HERMES_HOME/scripts/claude-budget-tracker.py" can-use 2>/dev/null && echo "yes" || echo "no")
    if [ "$ALLOWED" = "yes" ]; then
      PLANNERS="$PLANNERS,claude-opus-4-7"
    fi
  fi
fi

echo "[multi-brain] Planners: $PLANNERS" >&2

# ── 2. 计算 state_hash ──
STATE_HASH=$(sha256sum "$STATE_FILE" | cut -d' ' -f1)
echo "[multi-brain] State hash: $STATE_HASH" >&2

# ── 3. Fan-out: 并发调用 N 个模型 ──
IFS=',' read -ra MODEL_ARRAY <<< "$PLANNERS"
PLAN_FILES=""

for MODEL in "${MODEL_ARRAY[@]}"; do
  MODEL=$(echo "$MODEL" | xargs)  # trim
  [ -z "$MODEL" ] && continue
  
  PLAN_FILE="$PLANS_DIR/${MODEL}.json"
  PLAN_FILES="$PLAN_FILES $PLAN_FILE"
  
  echo "[multi-brain] → $MODEL planning..." >&2
  
  # 构建 planner prompt
  python3 -c "
import json, os
state = json.load(open('$STATE_FILE'))
prompt = '''You are a Hermes Agent architecture planner.

Read the state below and produce a structured improvement plan.

STATE (sha256: $STATE_HASH):
''' + json.dumps(state, indent=2)[:8000] + '''

Output ONLY valid JSON matching this schema:
{
  \"meta\": {\"planner_model\": \"$MODEL\", \"planner_role\": \"architect\", \"state_hash\": \"$STATE_HASH\", \"tier_target\": \"$TIER\", \"confidence\": 0.0-1.0},
  \"diagnosis\": {\"root_cause_class\": \"regression|router_skew|verifier_gap|kill_switch_oscillation|consensus_drift|pricing_overrun|schema_mismatch|no_action\", \"evidence_field_ids\": [\"field1\", ...], \"summary\": \"...\"},
  \"patches\": [{\"id\": \"unique\", \"target_file\": \"path\", \"op\": \"tune_threshold|swap_model|add_verifier|modify_router_weight|raise_tier|lower_tier|noop\", \"rationale\": \"...\", \"risk\": \"low|med|high\", \"blast_radius\": \"single_tier|router|all_tiers|kill_switch\", \"depends_on\": []}],
  \"verification\": {\"expected_metric_delta\": {\"main_pass_rate\": 0.0}, \"guard_metrics\": [\"main_pass_rate\"], \"tier_eval_plan\": \"T0_only|T0_T1|T1_T2|full_T0_T3\"},
  \"rollback_signal\": {\"auto_rollback_if\": \"main_pass_rate < pre - 0.05\", \"kill_switch_inc\": false}
}

Keep patches ≤ 5. Be concrete. Confidence must be honest.
'''
print(prompt)
" > "$PLANS_DIR/${MODEL}_prompt.txt"
  
  # 实际调用模型 (这里用 claude -p 作为示例，生产环境通过 delegate_task ACP)
  # Phase 0 shadow: 仅生成模板, 不实际调用
  cat > "$PLAN_FILE" << 'PLANEOF'
{
  "meta": {
    "planner_model": "MODEL_PLACEHOLDER",
    "planner_role": "architect",
    "state_hash": "STATE_HASH_PLACEHOLDER",
    "tier_target": "TIER_PLACEHOLDER",
    "confidence": 0.8,
    "cost_usd": 0.01,
    "latency_ms": 5000
  },
  "diagnosis": {
    "root_cause_class": "no_action",
    "evidence_field_ids": [],
    "summary": "Phase 0 shadow plan — no changes proposed"
  },
  "patches": [],
  "verification": {
    "expected_metric_delta": {"main_pass_rate": 0.0},
    "guard_metrics": ["main_pass_rate"],
    "tier_eval_plan": "T0_only"
  },
  "rollback_signal": {
    "auto_rollback_if": "main_pass_rate < pre - 0.10",
    "kill_switch_inc": false
  }
}
PLANEOF
  
  echo "[multi-brain]   $MODEL → $PLAN_FILE (shadow template)" >&2
done

# ── 4. Consensus ──
echo "[multi-brain] Running consensus on $(echo $PLAN_FILES | wc -w) plans..." >&2
MERGED=$(python3 "$HERMES_HOME/scripts/consensus-plans.py" merge $PLAN_FILES 2>/dev/null || echo '{"error":"consensus_failed"}')
echo "$MERGED" > "$TICK_DIR/merged_plan.json"

# ── 5. 输出 ──
cat "$TICK_DIR/merged_plan.json"

echo "[multi-brain] Done. Artifacts in $TICK_DIR/" >&2
