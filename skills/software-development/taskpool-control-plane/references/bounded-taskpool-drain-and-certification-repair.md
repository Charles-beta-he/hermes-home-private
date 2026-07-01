# Bounded taskpool drain and certification repair

Use this reference when a taskpool drain loop is stuck in `blocked` / `retry` due to multimodel certification, autorun gates, or claimed-handoff wedges.

## Landing-zone

- Reusable procedure / verification checklist for local brain taskpool operations.
- Applies to taskpool control-plane drains, `blocked-resolve-step`, `parallel-claim-and-handoff`, `consume-claimed`, `multimodel-intervention-*`, `proof-check`, and watcher readback.
- Anti-conditions: do not use this as permission to mark tasks done, bypass proof debt, enable global autorun, or change quorum/allowlist policy without explicit scope and readback.

## Safe drain loop

1. Run AgentOS preflight only as advisory when the task touches AgentOS/taskpool surfaces:
   - `hermes agent-os status --json`
   - `hermes agent-os route --json <intent>`
   Treat `would_execute=false` / shadow route as routing evidence, not as execution authority.
2. Read the live pool before mutation:
   - `brain_task_orchestrator.py list --json`
   - `brain_task_orchestrator.py selfcheck --json`
   - `taskpool_watch_report.py --json` (may be human text even when called with `--json`; parse defensively).
3. Prefer bounded control-plane transitions:
   - `reconcile --write --promote-due-retry`
   - `blocked-resolve-step --authority dispatch-hint --max-tasks N`
   - `auto-close-review`
4. If a task is claimed, consume the exact handoff only after reading the claimed JSON. If it is no longer claimed, treat `not_claimed:<status>` as safe no-op.
5. If `consume-claimed` returns a human escape / failure guard, do not force execution. Confirm it released claims to `retry` to avoid a claimed-without-progress wedge.
6. If multimodel intervention is disabled, do not silently bypass it. With explicit user authorization, use a command-scoped environment override only for the specific bounded command, e.g. `HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL=1 ...`, and report that it was not a global config change.
7. Do not close tasks from `PASS_ADVISORY_ONLY`, `CONTINUE_LOOP`, or `FAIL`; these produce evidence artifacts but not certification authority.
8. Finish every loop with same-slice evidence:
   - `selfcheck --json`
   - `proof-check --json`
   - `taskpool_watch_report.py --json`
   - `brain_task_orchestrator.py list --json`
   - scoped `git status` if scripts/skills were touched.

## Heredoc / JSON handoff pitfall

When extracting claimed handoff JSON through a Python heredoc, redirect on the opening heredoc line, not after the terminator:

```bash
python3 - <<'PY' > /tmp/claimed-drain.json
import json
p = json.load(open('/tmp/parallel-claim-drain.json'))
print(json.dumps(p.get('claimed_tasks', []), ensure_ascii=False))
PY
```

Wrong form:

```bash
python3 - <<'PY'
...
PY > /tmp/claimed-drain.json
```

The wrong form is parsed as Python source and fails with `SyntaxError`.

## Reading outcomes

- `blocked -> retry` via resolver is progress only when it avoids a wedge and preserves certification gates.
- `retry` counts may increase after safe release; that is acceptable if `blocked`, `claimed`, and `running` wedges are cleared.
- Persistent `proof_warnings` from autorun hash debt are not automatically clearable. Classify them and only repair with real append-only proof log/readback or task-specific evidence.
- `PASS_ADVISORY_ONLY` discussion artifacts are useful evidence but do not authorize `review -> done`.

## Minimal report format

Report the exact control-plane counts and boundary:

```text
SELF status=PASS task_count=<n> failures=0 warnings=0 boundary=PASS
PROOF status=PASS checked=<n> warnings=<n> failures=0
LIST counts={'retry': <n>, 'pending': <n>, ...}
WATCH <first lines or parsed counts>
GIT scoped=(clean|changed files)
```
