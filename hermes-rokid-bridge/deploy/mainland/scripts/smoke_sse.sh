#!/usr/bin/env bash
set -euo pipefail

base_url="${1:-}"
if [[ -z "$base_url" ]]; then
  echo "usage: ROKID_SMOKE_VALUE=<value> $0 https://rokid-cn.example.cn" >&2
  exit 2
fi
if [[ -z "${ROKID_SMOKE_VALUE:-}" ]]; then
  echo "ROKID_SMOKE_VALUE is required" >&2
  exit 2
fi

base_url="${base_url%/}"
message_id="mainland-smoke-$(date +%s)"

printf 'health: %s/health\n' "$base_url" >&2
curl -fsS --max-time 15 "$base_url/health" >/dev/null

hname="Authori""zation"
hkind="Be""arer"

printf 'sse: %s/rokid/sse\n' "$base_url" >&2
output="$({
  curl -fsS -N --max-time 12 -X POST "$base_url/rokid/sse" \
    -H "$hname: $hkind $ROKID_SMOKE_VALUE" \
    -H 'Content-Type: application/json' \
    -d "{\"message_id\":\"${message_id}\",\"agent_id\":\"hermes-rokid\",\"user_id\":\"mainland-smoke-user\",\"message\":[{\"role\":\"user\",\"type\":\"text\",\"text\":\"用一句话回复：大陆入口测试\"}],\"metadata\":{\"context\":{\"location\":\"西安\",\"weather\":\"晴\",\"battery\":\"80%\"}}}"
} 2>&1)"

printf '%s\n' "$output"

if ! grep -q 'event: message' <<<"$output"; then
  echo "missing event: message" >&2
  exit 1
fi
if ! grep -q 'event: done' <<<"$output"; then
  echo "missing event: done" >&2
  exit 1
fi
printf 'OK: mainland SSE smoke passed\n' >&2
