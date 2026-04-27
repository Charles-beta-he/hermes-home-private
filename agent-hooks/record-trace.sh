#!/usr/bin/env bash
# record-trace.sh — L1 观测层 shell hook (v2: model-aware)
# 注册到 ~/.hermes/config.yaml 的 hooks.post_tool_call 执行
# 接收 stdin JSON, 写入 route_outcomes DB
#
# v2 新增: model_chain 捕获 (从 config.yaml 读取当前模型)

PAYLOAD="$(cat -)"

# 解析关键字段
EVENT=$(echo "$PAYLOAD" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('hook_event_name',''))" 2>/dev/null)
TOOL=$(echo "$PAYLOAD" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null)
TASK_ID=$(echo "$PAYLOAD" | python3 -c "import sys,json; d=json.load(sys.stdin); e=d.get('extra',{}); print(e.get('task_id','') or e.get('session_id',''))" 2>/dev/null)

# 只在 post_tool_call 事件时记录
if [ "$EVENT" != "post_tool_call" ] || [ -z "$TOOL" ]; then
  printf '{}\n'
  exit 0
fi

# 采样: 记录 50% 的工具调用
SAMPLE=$(( RANDOM % 100 ))
if [ "$SAMPLE" -gt 49 ]; then
  printf '{}\n'
  exit 0
fi

# ── v2: 模型解析 (带缓存, 避免每次 yaml parse) ──
MODEL_CACHE="/tmp/.hermes-model-cache"
MODEL=""
# 环境变量优先 (支持模型路由器动态覆盖)
if [ -n "${HERMES_MODEL_OVERRIDE:-}" ]; then
  MODEL="$HERMES_MODEL_OVERRIDE"
else
  # 缓存: 60s TTL
  if [ -f "$MODEL_CACHE" ] && [ "$MODEL_CACHE" -nt ~/.hermes/config.yaml ]; then
    MODEL=$(cat "$MODEL_CACHE" 2>/dev/null)
  fi
  if [ -z "$MODEL" ]; then
    MODEL=$(python3 -c "
import yaml, os
try:
    c = yaml.safe_load(open(os.path.expanduser('~/.hermes/config.yaml')))
    m = c.get('model', {})
    print(m.get('default', '') or m.get('name', '') or '')
except: pass
" 2>/dev/null)
    [ -n "$MODEL" ] && echo "$MODEL" > "$MODEL_CACHE"
  fi
fi
[ -z "$MODEL" ] && MODEL="unknown"

# ── 构建 trace JSON (含 model_chain) ──
export HERMES_TRACE_MODEL="$MODEL"
RESULT=$(echo "$PAYLOAD" | python3 -c "
import sys, json, os
d = json.load(sys.stdin)
extra = d.get('extra', {})
result_str = extra.get('result', '')
verdict = 'unknown'
error = ''
duration_s = 0
tokens_in = 0
tokens_out = 0
try:
    r = json.loads(result_str)
    if isinstance(r, dict):
        ec = r.get('exit_code')
        if ec is not None:
            verdict = 'pass' if ec == 0 else 'fail'
            if ec != 0:
                error = f'exit_code={ec}'
        err = r.get('error')
        if err and str(err).lower() not in ('null', 'none', ''):
            verdict = 'fail'
            error = str(err)[:200]
        if not ec and not err:
            verdict = 'pass'
except (json.JSONDecodeError, TypeError):
    verdict = 'pass'

model = os.environ.get('HERMES_TRACE_MODEL', 'unknown')
verification_pattern = os.environ.get('HERMES_VERIFY_PATTERN', '')
fix_attribution = os.environ.get('HERMES_FIX_ATTRIBUTION', '')
dissent_sig = os.environ.get('HERMES_DISSENT_SIGNATURE', '')
chain_id = os.environ.get('HERMES_CHAIN_ID', '')

print(json.dumps({
    'skill': extra.get('tool_name', '') or d.get('tool_name', ''),
    'task_class': '',
    'route': 'hook:' + d.get('tool_name', 'unknown'),
    'verdict': verdict,
    'duration_s': duration_s,
    'tokens_in': tokens_in,
    'tokens_out': tokens_out,
    'task_id': extra.get('task_id', '') or d.get('session_id', ''),
    'error': error,
    'model_chain': json.dumps([model]),
    'verification_pattern': verification_pattern,
    'fix_attribution': fix_attribution,
    'dissent_signature': dissent_sig,
    'chain_id': chain_id,
}))
" 2>/dev/null)

if [ -n "$RESULT" ]; then
  echo "$RESULT" | python3 ~/.hermes/scripts/route_store.py append --stdin 2>/dev/null
fi

printf '{}\n'
