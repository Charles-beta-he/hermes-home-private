# 400 "out of extra usage" — Time-Based Quota Exhaustion

Extracted from `/Users/charles/.hermes/skills/.archive/curator-umbrella-2026-06-10/autonomous-ai-agents/claude-code/SKILL.md` on 2026-07-01T08:56:29.614759+00:00 during full core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

### 400 "out of extra usage" — Time-Based Quota Exhaustion
Anthropic enforces **time-windowed** usage limits (e.g., per 5-hour window), not just total quota. A 400 error saying "out of extra usage" does NOT mean your account is empty — it means you hit the rate limit for the current time window.

**Diagnosis:**
```bash
# Check if auth is valid (separate from quota)
claude auth status --text

# Quick API connectivity test
echo "ping" | claude -p "reply pong only" --max-turns 1
```

**Recovery:**
1. Wait for the time window to reset (typically 1-5 hours)
2. The quota auto-resets — no manual action needed
3. Verify recovery with the ping test above
4. If using Hermes with Anthropic as provider, the model router should auto-fallback to other providers during the window

**Key distinction:** `authentication_error` = bad API key. `invalid_request_error` with "out of usage" = quota exhaustion (transient).
