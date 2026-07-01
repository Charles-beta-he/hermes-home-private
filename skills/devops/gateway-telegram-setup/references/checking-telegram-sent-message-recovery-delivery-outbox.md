# Checking Telegram sent-message recovery / delivery outbox

Extracted from `/Users/charles/.hermes/skills/devops/gateway-telegram-setup/SKILL.md` on 2026-07-01T08:56:29.614759+00:00 during full core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

### Checking Telegram sent-message recovery / delivery outbox
When the user asks whether already-generated Telegram replies recovered after a network flap or restart, inspect the delivery outbox before assuming a resend is needed. The current implementation stores bounded plaintext-local records by default at `~/.hermes/state/gateway_delivery_outbox.jsonl` with a 24h TTL unless overridden by `HERMES_GATEWAY_DELIVERY_OUTBOX_CONTENT_STORAGE` / `HERMES_GATEWAY_DELIVERY_OUTBOX_TTL_SECONDS`.

Use a redacted status scan that reports only delivery IDs, statuses, attempts, message IDs, timestamps, and short hashes — do not dump private content:
```bash
cd ~/.hermes/hermes-agent
./venv/bin/python - <<'PY'
import collections, datetime, json, pathlib, time
p = pathlib.Path.home() / '.hermes/state/gateway_delivery_outbox.jsonl'
print('exists:', p.exists(), 'path:', p)
if not p.exists(): raise SystemExit
latest = {}
for i, line in enumerate(p.read_text(errors='replace').splitlines(), 1):
    if not line.strip(): continue
    try: row = json.loads(line)
    except json.JSONDecodeError: continue
    latest[str(row.get('delivery_id'))] = row
now = time.time()
print('latest_records:', len(latest))
print('status_counts:', dict(collections.Counter(r.get('status') or 'unknown' for r in latest.values())))
print('platform_counts:', dict(collections.Counter(r.get('platform') or 'unknown' for r in latest.values())))
def ts(v):
    try: return datetime.datetime.fromtimestamp(float(v)).isoformat(timespec='seconds')
    except Exception: return None
for r in sorted(latest.values(), key=lambda x: float(x.get('created_at') or 0), reverse=True)[:20]:
    print(json.dumps({
      'delivery_id': (r.get('delivery_id') or '')[:12],
      'platform': r.get('platform'),
      'chat_id': (str(r.get('chat_id') or '')[:6] + '…') if r.get('chat_id') else None,
      'status': r.get('status'),
      'attempt_count': r.get('attempt_count'),
      'sent_message_id': r.get('sent_message_id'),
      'last_error': (r.get('last_error') or '')[:180] or None,
      'content_storage': r.get('content_storage'),
      'content_sha256': (r.get('content_sha256') or '')[:12],
      'created_at': ts(r.get('created_at')),
      'expires_at': ts(r.get('expires_at')),
      'expired': float(r.get('expires_at') or 0) <= now,
    }, ensure_ascii=False))
PY
```

Interpretation:
- `pending=0` and `dead_letter=0` with recent `sent` records and `sent_message_id` means there is nothing left to recover.
- `attempt_count>1` on a `sent` record means a retry/recovery path eventually succeeded.
- Startup logs include `Delivery outbox startup drain: ...` only when at least one drain statistic is non-zero; absence of that line can simply mean there were no pending records.
- Calling `pending_redeliveries()` or adding a new outbox row can prune expired latest records; a lower record count after inspection may be normal TTL cleanup, not data loss.
- Do not manually redeliver ambiguous timeout cases unless the outbox row and operator policy prove it is safe; blind retries can duplicate Telegram messages.
