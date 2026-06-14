# Cron/provider health-gate pattern

Use when Hermes scheduled automation shows `provider_generation`, network, or delivery failures and you need to reduce red cron noise without blindly retrying jobs or mutating the scheduler.

## Landing sequence

1. **Classify current cron failures read-only**
   - Read `~/.hermes/cron/jobs.json`.
   - Classify `last_status=error` jobs into buckets such as `provider_generation`, `script_network_failure`, `telegram_delivery`, `script_failure`, `network_or_proxy`, `unknown`.
   - Write only local evidence under `docs/private/`.
   - Do not pause/resume/remove jobs or rerun failed jobs.

2. **Probe provider/network reachability without generation**
   - Use bounded unauthenticated probes (`HEAD`/edge reachability) against fixed endpoints.
   - Treat HTTP `401/403/404` as network/TLS/edge reachability evidence, not credential success.
   - Classify endpoint-level failures: `reachable`, `tls_error`, `timeout`, `proxy_or_gateway_error`, `remote_5xx`, etc.
   - Never read/write credentials or send prompts.

3. **Compile a read-only health gate**
   - Consume current `jobs.json`, the latest cron triage report, and the latest provider/network probe report.
   - Emit per-job decisions such as:
     - `skip_provider_health_degraded`
     - `retry_allowed_by_provider_health`
     - `retry_allowed_by_provider_health_manual_only`
     - `skip_fetch_use_no_fetch_fallback`
     - `run_with_degraded_provider_exclusions`
     - `manual_investigation_required`
   - Do not mutate cron or run jobs in this phase.

4. **Only then wire one low-risk wrapper**
   - Pick one provider-generation cron path.
   - If health gate says `skip_provider_health_degraded`, exit `0` with typed local evidence instead of burning a model retry and marking cron red.
   - If health gate permits retry, continue to the existing script path.
   - Do not roll out globally until one wrapper is verified.

## Important pitfalls

- Current `jobs.json` is the source for current failed jobs. A previous triage report may show more failures than the current scheduler state because later runs recovered some jobs.
- For delivery failures, triage class wins over provider inference: a Telegram delivery failure should target the `telegram` endpoint even if the job provider was `openai-codex`.
- Reachability is not auth/generation certification. A provider endpoint returning `401` can be reachable while credentials, quota, or model generation still fail.
- Do not turn broad user authorization (`全盘推进`) into permission to globally enable autorun, migrate config, run npm audit fixes, retry failed cron jobs, or send Telegram messages.

## Verification checklist

- Focused py_compile for changed scripts.
- Focused tests for triage/probe/gate logic.
- Read-back of generated report JSON and expected decision counts.
- `brain_task_orchestrator.py selfcheck --json` and `proof-check --json` when taskpool evidence is updated.
- Scoped commit only for the current phase files; do not stage unrelated dirty files in the Hermes checkout.
