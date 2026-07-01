# Human-escape and proof-check recovery

Use this reference when the local-brain taskpool cron/runner appears healthy but no work is dispatched, especially after `taskpool_dynamic_runner.py` reports `human_escape_active_preclaim`, or when `brain_task_orchestrator.py proof-check --json` fails on `unstructured evidence`.

## Human-escape preclaim recovery

Symptoms:

- `local-brain-taskpool-auto-completer` cron shows `last_status=ok`.
- `taskpool_dynamic_runner.py` produces no stdout/stderr or logs a no-op preclaim.
- `envelope_bus.py stats` shows `human_escape_triggered=true` and non-zero `escape_info.since_ack.failures` or `blocks`.

Procedure:

1. Read the breaker state:
   ```bash
   python3 ~/.hermes/scripts/envelope_bus.py stats
   ```
2. If triggered, inspect `~/.hermes/state/envelope_bus.db` read-only and list post-ack `FAILED`/`BLOCKED` rows with:
   - envelope ID
   - status
   - completed/updated timestamp
   - error/retry reason
   - task title / brain_id
   - whether it is terminal historical debt or unfinished work
3. Do not clear the breaker by SQL-updating, deleting, or rewriting envelope rows. Those rows are audit evidence.
4. If the post-ack failures are reviewed terminal debt, advance only the ack watermark:
   ```bash
   python3 ~/.hermes/scripts/envelope_bus.py ack-escape 'reviewed post-ack terminal failures: <ids>; keep envelope audit records; unblock preclaim only'
   ```
5. Re-verify:
   ```bash
   python3 ~/.hermes/scripts/envelope_bus.py stats
   python3 ~/.hermes/scripts/brain_task_dispatch_tick.py --summary --print-always --no-state
   python3 ~/.hermes/scripts/taskpool_dynamic_runner.py
   ```

Expected after safe recovery:

- `human_escape_triggered: false`
- `escape_info.since_ack.failures: 0`
- `escape_info.since_ack.blocks: 0`
- Dispatch tick may still say `idle_no_dispatchable_task`; that is healthy if active tasks are all blocked/done.

Anti-conditions:

- If post-ack failures represent real unfinished work, do not ack them away as solved. Create or unblock a small, evidence-backed task instead, then ack only after classifying the old failures as terminal historical debt.
- Do not use `ack-escape` to bypass active permission, safety, credential, or certification gates.

## Proof-check structured evidence prefix recovery

Symptoms:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py proof-check --json
```

returns `FAIL` with messages like:

- `unstructured evidence ... implementation:/path/to/file`
- `unstructured evidence ... implementation:skill-patch:/path#anchor`

Root pattern:

The proof may be semantically valid, but the evidence prefix is not in the taskpool structured-evidence whitelist. Accepted evidence prefixes include:

- `command:`
- `file:`
- `search:`
- `brainctl:`
- `url:`
- `artifact:`
- `proof:`
- `live_lark_snapshot:`
- `classification:`
- `child-task:`
- `child-axis:`

Minimal fix:

- Convert implementation landing references to `artifact:/absolute/path[#anchor]`.
- Keep or add a separate `proof:<hash-or-readback>` entry for integrity.
- Rerun proof-check before broader taskpool diagnosis.

Example:

```diff
-  - implementation:$HERMES_HOME/scripts/example.py
+  - artifact:$HERMES_HOME/scripts/example.py
```

```diff
-  - "implementation:skill-patch:$HERMES_HOME/skills/software-development/example/SKILL.md#Anchor"
+  - "artifact:$HERMES_HOME/skills/software-development/example/SKILL.md#Anchor"
```

## Blocked multimodel task boundary

If a blocked task has exhausted T3 rounds, e.g. `task has 6 failed T3 rounds (max=5); requires human review or targeted evidence fix`, and `blocked-resolve-step --authority dry-run` fails because the last `discussion_result.json` artifact is missing:

- Do not auto-run another `multimodel-intervention-step` just to force progress.
- Treat the task as requiring an intervention packet:
  1. restore the missing discussion artifact and rerun the resolver, or
  2. create a targeted evidence fix for the specific failed axis, or
  3. get human authorization to archive/close as terminal advisory/not-done.
- Do not move such tasks to `done` unless the task's certification gate is actually satisfied or an explicit audited manual closure path is authorized.
