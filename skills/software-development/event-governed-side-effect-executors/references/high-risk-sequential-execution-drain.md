# High-risk sequential execution drain

## Scope

Use when a user asks to push a set of high-risk Agent/control-plane boundaries from governance coverage into real execution, especially wording like “按顺序把每一项都推进到真实执行”.

## Core rule

Sequential approval is not a license to invent real targets. Drain each boundary in order, but classify every boundary by executable exactness:

- exact and reversible now → execute, read back, receipt;
- safe generated smoke target → execute only the generated canary/smoke and label it as smoke;
- attempted but no authoritative readback → record `attempted_not_verified`, not success;
- missing real target, payment/credential, broad fan-out, or unverifiable external send → stop that boundary with an intervention packet and continue later safe boundaries if independent.

## Procedure

1. Run Agent OS/status/route preflight before side effects.
2. Create one receipt ledger for the drain run. Each boundary record should include `boundary`, `idempotency_key`, `executed_at`, exact target, command/tool used, readback handle, and explicit side-effect flags.
3. Process boundaries in user order:
   - scheduler/cron mutation: create or update only an exact local/no-agent job; run/read back if the scheduler surface can prove execution. If scheduler run fails but the script can be executed locally, record scheduler mutation separately from script fallback.
   - taskpool/mission lifecycle write: create/update an exact task/mission idempotently and read back status/events. Do not imply worker execution unless a worker was actually spawned.
   - gateway/external send: require exact platform + target + payload + message/send receipt. A created scheduled job or outbox row is not a verified send.
   - worker spawn/lease: use a bounded worker/subagent smoke with no inherited external/write/destructive authority unless explicitly granted; record dispatch id and completion if available.
   - compensation execution: use an exact failed event or a disposable local canary; verify restore hash equals pre-failure hash.
   - publish/deploy/push: only execute when repo/remote/branch or deploy environment is exact; read back `git ls-remote`/health status.
   - destructive action: use a disposable canary unless a production resource and backup/restore path are exact.
   - payment/credential entry: agent must stop at a human-secret gate; never type secrets, cards, OTPs, seed phrases, API keys, or passwords.
   - broad fan-out: require exact named channel set, payload hash, idempotency, and per-target readback. Do not infer “all contacts”.
4. Generate a sequential execution report that separates `executed`, `spawn_dispatched`, `attempted_not_verified`, `blocked_human_secret_gate`, and `blocked_missing_exact_target`.
5. Run deterministic tests and scoped commit/report updates. If push is one of the boundaries and exact, push after committing and read back remote ref.

## Verification checklist

- [ ] Each boundary has a receipt or explicit blocker.
- [ ] Verified external send has a platform message id or equivalent readback; otherwise it is `attempted_not_verified`.
- [ ] Payment/credential boundary says `agent_may_type_secret=false`.
- [ ] Broad fan-out has an exact channel set before any send.
- [ ] Destructive and compensation smokes include before/after/restored hashes.
- [ ] Report wording does not claim 9/9 real execution if any boundary is blocked or unverified.

## Pitfalls

- Do not conflate cron job creation with successful script execution or delivery.
- Do not conflate scheduling a self-DM job with a verified external send.
- Do not mark worker spawn complete from intent alone; require dispatch id at minimum and completion readback when available.
- Do not silently skip later independent boundaries just because an earlier boundary is blocked; continue the ordered drain and record the blocker.
