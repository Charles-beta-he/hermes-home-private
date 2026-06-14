# Quota Observability Narrowed Brief

Generated: 2026-06-12T05:12:17Z
Mission: msn_20260610_120149_27c88cfc
Task: 2026-06-12-为-2026-06-08-评估-codex-插件能力面接入-hermes能力清单权限分层与-superpowers-增量吸收-2-细化-quota-observ

## File access boundary used for this slice

Allowed reads:
- `/Users/charles/Documents/brain/05-实践与项目/tasks/2026-06-12-为-2026-06-08-评估-codex-插件能力面接入-hermes能力清单权限分层与-superpowers-增量吸收-2-细化-quota-observ.md`
- `/Users/charles/.hermes/scripts/model_quota.py`
- `/Users/charles/.hermes/scripts/consult_models.py` status output
- `/Users/charles/.hermes/scripts/test_model_quota.py`
- `/Users/charles/.hermes/scripts/test_model_router_quota.py`
- `/Users/charles/Code/personal-hermes-brain/hermes/skills/framework-audit/references/provider-usage-telemetry-repo-audit.md`

Allowed writes:
- This evidence brief under `/Users/charles/.hermes/evidence/mission-msn_20260610_120149_27c88cfc/`
- The active task note under `/Users/charles/Documents/brain/05-实践与项目/tasks/` to record proof and handoff status.
- The mission ledger via `hermes mission stage-report`.

Forbidden patterns observed: `~/.hermes/.env`, `~/.ssh/*`, `**/*tok*`, `**/*sec*`, `**/*cred*`. This slice did not read those paths and did not print raw private file contents.

Evidence egress policy: report only command names, proof summaries, paths, and redacted quota state fields. Do not paste private materials, prompts, completion bodies, or raw private headers.

## Source semantics from `model_quota.py`

Evidence path: `/Users/charles/.hermes/scripts/model_quota.py`.

Observed source lines/semantics:
- Lines 2-7 state the module separates exact quota data from estimates/unobservable caps and says unknown is never proof of abundance.
- Lines 38-45 define state/log paths and valid statuses: `ok`, `low`, `unknown`, `unobservable`, `exhausted`, `rate_limited`, `reset_elapsed`, `stale_exhausted`, `malformed`, `unavailable`.
- Line 50 sets `CONFIDENCE_BLOCKING_STATUSES = {low, unknown, unobservable, exhausted, rate_limited, malformed, unavailable}`.
- Lines 355-381 define default snapshots: subscription providers become `status=unobservable`, `quota_type=subscription_cap`, `confidence=0.2`; other providers become `status=unknown`, `quota_type=unknown`, `confidence=0.1`; default stale window is 300 seconds.
- Lines 384-411 define response-header snapshots: rate-limit headers produce `observability=window_exact`, `quota_type=rate_limit_window`, `confidence=0.9`; missing quota headers preserve the low-confidence default state while retaining sanitized usage.

## Live quota_state observation

Command evidence:

```bash
python3 /Users/charles/.hermes/scripts/consult_models.py status
python3 /Users/charles/.hermes/scripts/model_quota.py status --json
python3 /Users/charles/.hermes/scripts/model_quota.py confidence-gate --model claude-fable-5 --model gpt-5.5 --model deepseek-v4-pro --model mimo-v2.5-pro --min-confidence 0.6 --json || true
```

Observed current state, summarized without private material:

| model | provider | status | observability | confidence | source | gate result |
|---|---|---:|---|---:|---|---|
| claude-fable-5 | claude-code | unobservable | unobservable | 0.2 | error_inference | FAIL_CLOSED: status_unobservable, low_confidence |
| gpt-5.5 | openai-codex | unobservable | unobservable | 0.2 | response_headers | FAIL_CLOSED: status_unobservable, low_confidence |
| deepseek-v4-pro | deepseek | unknown | unknown | 0.1 | response_headers | FAIL_CLOSED: status_unknown, low_confidence |
| mimo-v2.5-pro | xiaomi | unknown | unknown | 0.2 | error_inference | FAIL_CLOSED: status_unknown, low_confidence |

Confidence-gate aggregate: `ok=false`, `status=FAIL_CLOSED`, `failure_count=4`, `usable=0`, `low_confidence=4`, `unknown=2`, `unobservable=2`, `stale=0`, `min_confidence=0.6`.

## Unknown/unobservable handling

Policy conclusion for this parent line:
- `unknown` and `unobservable` are advisory-only for routing and cannot certify a budget-handoff/autonomy change.
- Do not treat successful subprocess/model calls with no quota headers as proof of available budget.
- Upgrade to `estimated` only with explicit usage/pricing evidence and stale downgrade semantics.
- Upgrade to `exact` only with direct provider evidence such as accepted rate-limit headers or a separately authorized, redacted official quota probe.
- Official/provider quota probes remain out of scope for this slice because they can touch private-access surfaces; they require a separate redaction-first gate and, where needed, human approval.

## Verification

Command:

```bash
python3 -m pytest /Users/charles/.hermes/scripts/test_model_quota.py /Users/charles/.hermes/scripts/test_model_router_quota.py -q
```

Result: `75 passed in 0.22s`.

## Next bounded step

For the parent Codex capability-registry line, use this brief as the quota-observability evidence input. The next safe local-only step is to synchronize this child evidence back to the parent/taskpool proof spine and decide whether a separate redaction-first provider quota probe task is worth opening. Do not implement an official probe or mutate routing state from the current low-confidence quota_state.
