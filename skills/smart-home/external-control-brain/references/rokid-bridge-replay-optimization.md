# Rokid Bridge Replay Optimization

Path: `~/.hermes/hermes-rokid-bridge/`

## Architecture

Voice input → Rokid Bridge (`localhost:8787`) → L0 route dispatch (zero-cost) → model_fallback (LLM).

Three route families:
- `text_l0` — fast-path regex/keyword matching, ~40 categories (weather, tasks, reminders, device status, capability, etc.)
- `high_impact_confirm` / `orphan_action_confirmation` — safety gates for destructive actions
- `model_fallback` — general questions that need LLM reasoning

## Replay Verifier

Run all recorded `dev_review` dialogues through current routing logic to detect drift:

```bash
cd ~/.hermes/hermes-rokid-bridge && .venv/bin/python replay_verify.py --limit 200 --json
```

Output: `{ total, matched, drifted, drift_rate, mismatches[] }`.

Drift means: recorded_route_id != replayed_route_id. Most drift is *expected* (we fixed the routing since the recording). Only unexpected drift (replayed route is worse) needs action.

## Pitfalls

### 1. Replay verifier image message corruption

`_build_stub_ctx()` unconditionally sets `messages[0]["type"] = "text"`, which destroys image messages. Fix:

```python
# Only update text messages — preserve image type for extract_image_urls()
if messages and isinstance(messages[0], dict):
    if messages[0].get("type") != "image":
        messages[0]["text"] = user_text
        messages[0]["type"] = "text"
```

This prevents `image_placeholder` records from being falsely flagged as drift.

### 2. needs_attention false positives from route-based triggers

Do NOT use `route_id in {"model_fallback", "camera_view", "image_placeholder"}` as a needs_attention trigger. These routes handle legitimate requests. Route-based triggers create 27% false-positive attention rate.

Correct trigger: only user/answer keyword signals:
- User says: 不对/错了/不是/没听懂/你理解错/纠正
- Answer contains: 请再说一遍/超时/服务有点抖/没有生成有效回复
- Backend error string present

### 3. Capability pattern gaps

Common spoken variations that MUST be in `CAPABILITY_QUERY_PATTERNS` in `l0_routes.py`:
- 你能干什么？ / 你是干什么的？ / 你是什么？ / 介绍一下你自己

Without these, they fall through to model_fallback (slower, inconsistent wording).

### 4. L0 pattern tuning methodology

1. Export `model_fallback` records from dev_review
2. Cluster by intent (capability, task status, device status, general knowledge)
3. For each cluster that has a deterministic answer → add L0 patterns
4. For genuinely open-ended questions → leave in model_fallback
5. Run `replay_verify.py` — all new L0 matches show as "expected drift"

## Smoke test after changes

```bash
cd ~/.hermes/hermes-rokid-bridge
.venv/bin/python -m pytest tests -q -o addopts=
launchctl kickstart -k gui/$(id -u)/com.charles.hermes-rokid-bridge
curl -sS http://127.0.0.1:8787/health | python3 -m json.tool
.venv/bin/python replay_verify.py --limit 200 --json
```

## Key files

- `l0_routes.py` — all L0 pattern definitions
- `app.py` — main routing logic, `extract_user_text()`, `extract_image_urls()`
- `rokid_dev_review.py` — `needs_attention` logic, record saving
- `replay_verifier.py` — offline replay engine
- `replay_verify.py` — CLI runner
- Dev review records: `~/.hermes/brains/rokid-glasses/dev_reviews/records/`
