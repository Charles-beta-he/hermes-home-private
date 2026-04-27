#!/usr/bin/env bash
# p10-health.sh — Hermes 自进化系统形式化健康评分 V(t)
# 用法: bash ~/.hermes/scripts/p10-health.sh [--json]
# 输出: V(t) 健康向量 + V̇(t) 变化率 (当有历史数据时)
set -euo pipefail

HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
TIMESTAMP=$(date -u +%FT%TZ)
JSON_MODE=false
[[ "${1:-}" == "--json" ]] && JSON_MODE=true

# ── 1. Cron Liveness ──
CRON_LIVE=0
CRON_TOTAL=0
CRON_RECENT=0
NOW_EPOCH=$(date +%s)
cron_list=$(python3 -c "
import os, json
p = os.path.expanduser('$HERMES_HOME/cron/jobs.json')
if not os.path.exists(p):
    print('')
else:
    with open(p) as f:
        data = json.load(f)
    jobs = data.get('jobs', data) if isinstance(data, dict) else data
    if isinstance(jobs, list):
        for j in jobs:
            if isinstance(j, dict):
                jid = j.get('job_id', j.get('id','?'))[:12]
                enabled = j.get('enabled', True)
                last = j.get('last_run_at','') or ''
                name = j.get('name','?')
                print(f'{jid}|{enabled}|{last}|{name}')
" 2>/dev/null || echo "")

while IFS='|' read -r jid enabled last name; do
    [[ -z "$jid" ]] && continue
    CRON_TOTAL=$((CRON_TOTAL + 1))
    [[ "$enabled" == "True" ]] && CRON_LIVE=$((CRON_LIVE + 1))
    if [[ -n "$last" && "$last" != "None" && "$last" != "null" ]]; then
        last_epoch=$(date -j -f "%Y-%m-%dT%H:%M:%S" "${last:0:19}" +%s 2>/dev/null || echo 0)
        if [[ $last_epoch -gt $((NOW_EPOCH - 86400)) ]]; then
            CRON_RECENT=$((CRON_RECENT + 1))
        fi
    fi
done <<< "$cron_list"

CRON_HEALTH=$(python3 -c "print(round($CRON_RECENT / max($CRON_TOTAL, 1), 3))")

# ── 2. Route Outcomes (多口径) ──
ROUTE_STATS=$(python3 "$HERMES_HOME/scripts/route_store.py" stats --hours 168 2>/dev/null || echo '{}')
MAIN_PR=$(python3 -c "
import sys,json; d=json.loads('''$ROUTE_STATS''')
views=d.get('views',{}); m=views.get('main',d)
print(m.get('pass_rate', d.get('main_pass_rate', 0)))
" 2>/dev/null || echo 0)
OVERALL_PR=$(python3 -c "
import sys,json; d=json.loads('''$ROUTE_STATS''')
views=d.get('views',{}); o=views.get('overall',d)
print(o.get('pass_rate', d.get('pass_rate', 0)))
" 2>/dev/null || echo 0)
TRACE_COUNT=$(python3 -c "
import sys,json; d=json.loads('''$ROUTE_STATS''')
views=d.get('views',{}); o=views.get('overall',d)
print(o.get('total', 0))
" 2>/dev/null || echo 0)
REAL_COUNT=$(python3 -c "
import sys,json; d=json.loads('''$ROUTE_STATS''')
views=d.get('views',{}); o=views.get('overall',d)
print(o.get('real', 0))
" 2>/dev/null || echo 0)
SYNTH_COUNT=$(python3 -c "
import sys,json; d=json.loads('''$ROUTE_STATS''')
views=d.get('views',{}); o=views.get('overall',d)
print(o.get('synthetic', 0))
" 2>/dev/null || echo 0)
SYNTH_RATIO=$(python3 -c "print(round($SYNTH_COUNT / max($TRACE_COUNT, 1), 3))")

# ── 3. Self-Test ──
SELF_TEST_OUT=$(python3 "$HERMES_HOME/scripts/self-test.py" 2>&1 || true)
SELF_TEST_PASS=false
echo "$SELF_TEST_OUT" | grep -q "ALL PASS" && SELF_TEST_PASS=true
SELF_TEST_COUNT=$(echo "$SELF_TEST_OUT" | grep -c "✓" || echo 0)

# ── 4. Skill Count ──
SKILL_COUNT=$(find "$HERMES_HOME/skills" -name "SKILL.md" 2>/dev/null | wc -l | tr -d ' ')
STAGING_COUNT=$(find "$HERMES_HOME/skills-staging" -name "SKILL.md" 2>/dev/null | wc -l | tr -d ' ')

# ── 5. Memory Size ──
MEMORY_SIZE=$(wc -c < "$HERMES_HOME/memories/MEMORY.md" 2>/dev/null || echo 0)
MEMORY_LINES=$(wc -l < "$HERMES_HOME/memories/MEMORY.md" 2>/dev/null || echo 0)

# ── 6. Gateway Status ──
GATEWAY_RUNNING=false
pgrep -f "hermes.*gateway" > /dev/null 2>&1 && GATEWAY_RUNNING=true

# ── 7. Compute V(t) ──
# V(t) = [self_test_pass, main_pass_rate, cron_health, 1-synth_ratio, gateway_running]
V_SELF=$( [[ "$SELF_TEST_PASS" == "true" ]] && echo 1.0 || echo 0.0 )
V_MAIN_PR=$MAIN_PR
V_CRON=$CRON_HEALTH
V_REAL_RATIO=$(python3 -c "print(round(1.0 - $SYNTH_RATIO, 3))")
V_GW=$( [[ "$GATEWAY_RUNNING" == "true" ]] && echo 1.0 || echo 0.0 )

V_OVERALL=$(python3 -c "
components = [$V_SELF, $V_MAIN_PR, $V_CRON, $V_REAL_RATIO, $V_GW]
weights = [0.25, 0.30, 0.15, 0.20, 0.10]
v = sum(c*w for c,w in zip(components, weights))
print(round(v, 4))
")

# ── 8. V̇(t) — delta from last reading ──
HISTORY_FILE="$HERMES_HOME/logs/health-history.jsonl"
V_DOT="N/A"
if [[ -f "$HISTORY_FILE" ]]; then
    LAST_V=$(tail -1 "$HISTORY_FILE" | python3 -c "import sys,json; print(json.loads(sys.stdin.readline()).get('V', 0))" 2>/dev/null || echo 0)
    V_DOT=$(python3 -c "print(round($V_OVERALL - $LAST_V, 4))" 2>/dev/null || echo "N/A")
fi

# ── 9. Summary Warnings ──
WARNINGS=()
[[ $(python3 -c "print(1 if $MAIN_PR < 0.6 else 0)") == "1" ]] && WARNINGS+=("main_pass_rate < 0.6")
[[ $(python3 -c "print(1 if $SYNTH_RATIO > 0.6 else 0)") == "1" ]] && WARNINGS+=("synthetic_ratio > 0.6 (dilution risk)")
[[ $(python3 -c "print(1 if $CRON_RECENT < 3 and $CRON_TOTAL > 0 else 0)") == "1" ]] && WARNINGS+=("only $CRON_RECENT/$CRON_TOTAL crons ran in 24h (check scheduler)")
[[ "$GATEWAY_RUNNING" != "true" ]] && WARNINGS+=("gateway not running")
[[ $MEMORY_SIZE -gt 2200 ]] && WARNINGS+=("memory file > 2.2KB, may have ghosts")
[[ "$SELF_TEST_PASS" != "true" ]] && WARNINGS+=("self-test not all-pass")
[[ $SKILL_COUNT -gt 80 ]] && WARNINGS+=("skill count > 80, consider reduction")

# ── Output ──
if $JSON_MODE; then
    python3 -c "
import json
print(json.dumps({
    'timestamp': '$TIMESTAMP',
    'V': $V_OVERALL,
    'V_dot': $( [[ "$V_DOT" == "N/A" ]] && echo 'null' || echo "$V_DOT" ),
    'components': {
        'self_test': $V_SELF,
        'main_pass_rate': $V_MAIN_PR,
        'cron_health': $V_CRON,
        'real_ratio': $V_REAL_RATIO,
        'gateway': $V_GW
    },
    'details': {
        'trace_count_7d': $TRACE_COUNT,
        'real_traces': $REAL_COUNT,
        'synthetic_traces': $SYNTH_COUNT,
        'synthetic_ratio': $SYNTH_RATIO,
        'overall_pass_rate': $OVERALL_PR,
        'cron_total': $CRON_TOTAL,
        'cron_enabled': $CRON_LIVE,
        'cron_recent_24h': $CRON_RECENT,
        'skill_count': $SKILL_COUNT,
        'skill_staging': $STAGING_COUNT,
        'memory_bytes': $MEMORY_SIZE,
        'memory_lines': $MEMORY_LINES,
        'gateway_running': $( [[ "$GATEWAY_RUNNING" == "true" ]] && echo 'true' || echo 'false' ),
        'self_test_count': $SELF_TEST_COUNT
    },
    'warnings': $(python3 -c "import json; print(json.dumps(${WARNINGS[@]+${WARNINGS[@]@Q}}))" 2>/dev/null || echo '[]'),
    'grade': '$(
        if [[ $(python3 -c "print(1 if $V_OVERALL >= 0.9 else 0)") == "1" ]]; then echo "A";
        elif [[ $(python3 -c "print(1 if $V_OVERALL >= 0.75 else 0)") == "1" ]]; then echo "B";
        elif [[ $(python3 -c "print(1 if $V_OVERALL >= 0.6 else 0)") == "1" ]]; then echo "C";
        else echo "D"; fi
    )'
}, indent=2, ensure_ascii=False))
"
else
    echo "═══════════════════════════════════════════════"
    echo "  Hermes Health Score — $TIMESTAMP"
    echo "═══════════════════════════════════════════════"
    echo ""
    echo "  V(t) = $V_OVERALL  (V̇ = $V_DOT)  Grade: $(
        if [[ $(python3 -c "print(1 if $V_OVERALL >= 0.9 else 0)") == "1" ]]; then echo "A";
        elif [[ $(python3 -c "print(1 if $V_OVERALL >= 0.75 else 0)") == "1" ]]; then echo "B";
        elif [[ $(python3 -c "print(1 if $V_OVERALL >= 0.6 else 0)") == "1" ]]; then echo "C";
        else echo "D"; fi
    )"
    echo ""
    echo "  Components:"
    echo "    self_test:     $V_SELF  ($SELF_TEST_COUNT checks)"
    echo "    main_pass_rate: $V_MAIN_PR  (7d, excl blank/planner-)"
    echo "    cron_health:   $V_CRON  ($CRON_RECENT/$CRON_TOTAL recent)"
    echo "    real_ratio:    $V_REAL_RATIO  (1 - synth_ratio=$SYNTH_RATIO)"
    echo "    gateway:       $V_GW  ($( [[ "$GATEWAY_RUNNING" == "true" ]] && echo 'up' || echo 'down' ))"
    echo ""
    echo "  Details:"
    echo "    traces_7d:     $TRACE_COUNT (real=$REAL_COUNT synth=$SYNTH_COUNT)"
    echo "    overall_pr:    $OVERALL_PR"
    echo "    skills:        $SKILL_COUNT (+$STAGING_COUNT staging)"
    echo "    memory:        ${MEMORY_SIZE}B / ${MEMORY_LINES} lines"
    echo ""
    if [[ ${#WARNINGS[@]} -gt 0 ]]; then
        echo "  ⚠ Warnings:"
        for w in "${WARNINGS[@]}"; do
            echo "    - $w"
        done
    else
        echo "  ✓ No warnings"
    fi
    echo "═══════════════════════════════════════════════"
fi

# ── 10. Append history ──
mkdir -p "$HERMES_HOME/logs"
echo "{\"ts\":\"$TIMESTAMP\",\"V\":$V_OVERALL,\"grade\":\"$(
    if [[ $(python3 -c "print(1 if $V_OVERALL >= 0.9 else 0)") == "1" ]]; then echo "A";
    elif [[ $(python3 -c "print(1 if $V_OVERALL >= 0.75 else 0)") == "1" ]]; then echo "B";
    elif [[ $(python3 -c "print(1 if $V_OVERALL >= 0.6 else 0)") == "1" ]]; then echo "C";
    else echo "D"; fi
)\"}" >> "$HISTORY_FILE"
