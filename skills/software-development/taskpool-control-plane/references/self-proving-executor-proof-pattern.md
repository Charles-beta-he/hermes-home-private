# Self-Proving Executor Proof Pattern

Use this when evolving Hermes/taskpool automation and the task needs AutoResearch-style self-verification before lifecycle advancement.

## Pattern

1. Add a bounded executor outside the core taskpool path first.
   - Prefer `~/.hermes/scripts/self_proving_executor.py`-style wrappers over immediately modifying dispatcher internals.
   - The executor should accept a JSON config with repo/path, command bundle, timeout, artifact path, and mode.

2. Emit a machine-readable proof artifact for both success and failure.
   - Required fields: schema/version, status (`PASS`/`FAIL`), command list with exit codes/stdout/stderr excerpts, checkpoint intent/result, and `safe_next_action`.
   - PASS should produce an advancement hint such as `advance_to_review_with_artifact`.
   - FAIL should exit nonzero and produce a retry/reset hint such as `retry_or_reset_with_failure_artifact`.

3. Keep checkpoint side effects opt-in.
   - Default mode should verify and write evidence only.
   - Do not commit, push, reset, or mutate lifecycle state until the proof schema is trusted and covered by tests.

4. Cover the executor with RED/GREEN tests around state and artifact semantics, not just helper functions.
   - Test PASS artifact + zero exit.
   - Test FAIL artifact + nonzero exit + no advancement hint.
   - Assert that default checkpoint behavior is not performed.

5. After updating the task note, re-run control-plane gates.
   - `brain_task_orchestrator.py proof-check --json`
   - `brain_task_orchestrator.py selfcheck --json`
   - A read-only dispatch tick such as `brain_task_dispatch_tick.py --summary --print-always --no-state`

## Practical test command

For standalone scripts under `~/.hermes/scripts`, the system Python may not have pytest. Prefer the Hermes repo venv when present:

```bash
/Users/charles/.hermes/hermes-agent/.venv/bin/python -m pytest ~/.hermes/scripts/test_self_proving_executor.py -q
python3 -m py_compile ~/.hermes/scripts/self_proving_executor.py ~/.hermes/scripts/test_self_proving_executor.py
```

This is a setup pattern, not a claim that system Python is broken.

## Pitfalls

- Do not mark the task `done` just because the executor compiles; proof must include a real PASS and a real FAIL path.
- Do not use generic taskpool health checks as feature-delivery evidence. They are necessary but not sufficient.
- Do not leave “future integration” as a verbal promise. Put the next integration slice into the taskpool and verify cron/follow-through exists.
- Do not add automatic commit/reset behavior before the failure artifact contract is tested.
