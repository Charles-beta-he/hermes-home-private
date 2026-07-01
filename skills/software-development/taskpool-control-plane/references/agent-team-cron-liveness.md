# Agent-team no-agent cron liveness

Applicability: Hermes/local-brain taskpool `agent-team-cycle-*` or similar no-agent cron wrappers that call `agent_team_controller.py cycle`, `execute-cycle`, or worker delegation. Use when cron `last_status=error`/timeout is caused by long model workers or queued PENDING claim envelopes, while direct control-plane health checks otherwise pass.

Anti-conditions:
- Do not use this to bypass lifecycle/proof gates or let workers mark tasks done.
- Do not treat async worker handoff as completion proof; it is only liveness/control-plane ownership transfer.
- Do not kill async workers just because cron returned quickly; verify worker job ownership/aliveness first.

## Root cause pattern

`agent_team_controller.py cycle` can exceed no-agent cron budgets when `execute-cycle` synchronously waits on `delegate_to_worker()` model chains. Individual providers may have long per-call timeouts and fallback chains, so an hourly cron tick can turn into a long worker run and finish as scheduler `error` even though taskpool selfcheck/proof/boundary are healthy.

## Durable fix pattern

1. Keep default/manual worker behavior unchanged.
2. Add env-gated liveness controls used only by cron wrappers:
   - `HERMES_AGENT_TEAM_WORKER_TIMEOUT_CEILING`: cap each provider timeout for cron-owned workers.
   - `HERMES_AGENT_TEAM_MODEL_CHAIN_LIMIT`: limit provider attempts per cron tick.
   - `HERMES_AGENT_TEAM_EXECUTE_ASYNC=1`: make `execute-cycle` spawn `consume-claimed` as a durable async worker and return quickly.
3. In the cron wrapper, run a small bounded tick, e.g. `--max-claims 1 --max-workers 1 --claim-wall-budget-seconds 5 --execute-wall-budget-seconds 15`.
4. The parent cron tick should report started async worker metadata; the worker process owns claimed→running→review/retry/blocked and still cannot mark done.

## Regression tests / verification

Minimum checks before claiming fixed:

```bash
python3 -m py_compile ~/.hermes/scripts/agent_team_controller.py ~/.hermes/scripts/agent_team_controller_cycle.py ~/.hermes/scripts/test_agent_team_controller_safety.py
python3 ~/.hermes/scripts/test_agent_team_controller_safety.py
python3 ~/.hermes/scripts/test_agent_team_controller.py
time python3 ~/.hermes/scripts/agent_team_controller_cycle.py >/tmp/agent_cycle.out 2>&1; echo EXIT:$?; tail -n 80 /tmp/agent_cycle.out
python3 ~/.hermes/scripts/agent_team_controller.py worker-jobs
```

Then trigger/read back the cron job and final taskpool gates:

```bash
# via Hermes cron tool or scheduler UI: run/list the specific job id
python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json
python3 ~/.hermes/scripts/brain_task_dispatch_tick.py --summary --print-always --no-state
```

Required evidence:
- cron `last_status=ok` for the agent-team job.
- taskpool `selfcheck=PASS`, `proof_check=PASS`, `boundary_check=PASS`, `cron_status=OK`.
- `review_total` remains governed by proof gates; no worker direct-done bypass.
- `worker-jobs` may show alive async workers immediately after a tick; that is expected if they own claimed work. Later alive_count should naturally drain or be explained by active ownership.

## Test isolation pitfall

Default-on agent-card routing and multimodel conductor can add extra subprocess calls inside worker tests. If a safety test asserts exact `subprocess.run` call counts for worker fallback behavior, isolate the old boundary explicitly:

```python
patch.dict("os.environ", {
    "HERMES_AGENT_CARD_ROUTING_MODE": "off",
    "HERMES_ENABLE_AGENT_CARD_CONTEXT": "0",
    "HERMES_MULTIMODEL_CONDUCTOR_MODE": "off",
}, clear=False)
```

This keeps tests about worker fallback/liveness from being polluted by advisory routing/certification extensions while leaving production defaults intact.
