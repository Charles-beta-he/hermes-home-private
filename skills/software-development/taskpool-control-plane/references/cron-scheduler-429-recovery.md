# Cron Scheduler 429 Recovery

When the default LLM provider is rate-limited (HTTP 429), ALL agent-based cron jobs in the Hermes scheduler stall. Jobs show `Next run` in the past but never fire. The scheduler tick continues (interval=60s), but every job that needs an LLM call retries 3x then errors out.

## Diagnosis

1. Check error log for 429 pattern:
```bash
tail -50 ~/.hermes/logs/gateway.error.log | grep -i "429\|ratelimit\|too many requests"
```

2. Confirm scheduler is ticking but jobs are stale:
```bash
hermes cron list 2>&1 | grep "Next run" | head -5
date  # compare — Next run in the past = stalled
```

3. Confirm which provider is rate-limited:
```bash
grep "429" ~/.hermes/logs/gateway.error.log | grep -oP "provider=\S+" | sort | uniq -c
```

## Mechanism

- Hermes cron jobs use the default model provider (set in config.yaml or .env).
- When the provider returns 429, the scheduler retries 3x with exponential backoff (~2s, ~5.5s).
- After 3 failures, the job fails with `RuntimeError: HTTP 429: Too many requests`.
- The scheduler does NOT skip to the next job — it moves on, but the same 429 will hit the next agent-based job too.
- `no_agent=True` script-only jobs still execute (they don't call LLM).
- The scheduler tick continues running; it's not the tick that's broken, it's every LLM call inside it.

## Recovery Options

### Option A: Wait for rate limit to recover
- Rate limits typically reset in minutes to hours depending on provider.
- Check provider dashboard or API for quota status.

### Option B: Switch default model provider
- Edit `~/.hermes/config.yaml` to change the default model/provider.
- Restart gateway: `hermes restart` or `systemctl restart hermes-gateway`.
- All subsequent cron jobs will use the new provider.

### Option C: Manually execute stuck job via delegate_task (recommended for immediate delivery)
- Bypasses the scheduler entirely; uses the current session's model/provider.
- Works even when the scheduler's provider is rate-limited.
- Pattern:
```
delegate_task(
    goal="Execute the cron job's prompt manually. Include all details from the job prompt.",
    context="The cron scheduler is blocked by 429 rate limiting. Run the job manually.",
    toolsets=["browser", "file", "terminal"]  # match what the job needs
)
```

- For daily report jobs specifically:
  1. Read the job prompt: `hermes cron list` to see the prompt
  2. Spawn delegate_task with the full prompt + today's date
  3. The subagent will fetch sources, generate report, write file, and send via send_message

### Option D: Pause non-essential jobs to reduce load
```bash
hermes cron list  # find job IDs
hermes cron pause <job-id>  # pause non-essential jobs
```

## Detection Automation

Consider adding a `no_agent=True` watchdog cron script that checks for repeated 429 errors:
```bash
# Check last 100 error log lines for 429 count
count=$(grep -c "429" ~/.hermes/logs/gateway.error.log 2>/dev/null)
if [ "$count" -gt 10 ]; then
    echo "ALERT: $count recent 429 errors — cron scheduler likely stalled"
fi
```

## Pitfalls

- Don't assume "Next run in past" means the scheduler tick is broken. Check the error log first.
- Don't restart the gateway repeatedly — the 429 is provider-side, not gateway-side.
- `delegate_task` uses the current session's provider, which may differ from the cron scheduler's default provider. If the user is chatting via Telegram with a different model, the delegate_task call uses THAT model, not the cron's.
- The scheduler will keep retrying failed jobs on the next tick. If the 429 persists, you'll see repeated error entries in gateway.error.log.
