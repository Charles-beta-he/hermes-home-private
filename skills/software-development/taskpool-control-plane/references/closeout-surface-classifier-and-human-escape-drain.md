# Closeout surface classifier and human-escape drain recovery

Use this reference when operating Hermes local-brain/taskpool drains, especially after a false UI/API closeout blocker or a Human escape stop.

## 1. Closeout surface classification before requiring UI/API proof

Pitfall: keyword matching on `browser`, `public-preview`, `external-search`, `verify`, or `readback` can falsely require UI/API implementation proof for evidence/intake tasks.

Classifier procedure:

1. Read these fields together, not as isolated keywords:
   - `lane`
   - `workflow_stage`
   - `completion_boundary`
   - `completion_gate`
   - `harness_surfaces`
   - red lines / no-execution clauses
   - acceptance criteria and proof log requirements
2. Classify surfaces into:
   - **source/input surfaces**: public preview, browser readback, external search, repo/site readback, docs/license/readme verification.
   - **implementation/output surfaces**: built UI, shipped/deployed preview, API endpoint, executable harness, code change requiring smoke proof.
3. If the task explicitly says `no-execution`, `workflow_stage: evidence`, `completion_boundary: taskpool_candidate`, or equivalent source-intake language, require source/readback evidence and ratification evidence as applicable, but do **not** require UI/browser implementation closeout proof merely because browser/public-preview appears in the source surfaces.
4. Keep implementation tasks fail-closed. A `work` lane task with implement/build/ship/deploy/fix UI/API language still requires command/readback proof plus UI/API proof when those are output surfaces.
5. Implement the classifier as a deterministic function returning auditable `reasons` (for example: `source_intake_no_execution`, `work_lane_output_surface`, `non_work_explicit_output_obligation`). Avoid one-off hard exemptions.
6. Multimodel analysis is useful to refine the classifier design and catch rigid logic, but advisory model output alone is not closeout proof. Treat it as design input unless it is bound to a certified evidence artifact accepted by the lifecycle gate.

Anti-conditions:

- Do not use this as a blanket exemption for `browser` or `API` tasks.
- Do not downgrade work-lane implementation closeout just because the task also includes evidence language.
- Do not mark tasks done directly from a worker; run normal lifecycle gates.

## 2. Human-escape ACK and bounded drain recovery

When `agent_team_controller.py consume-claimed` or `cycle` is stopped by Human escape, do not force-close claimed tasks. Recover through explicit review and small batches.

Procedure:

1. Inspect the active escape rows:
   ```bash
   python3 ~/.hermes/scripts/taskpool_escape_guard.py --json
   ```
   Review `post_ack_terminal_count`, `worker_timeout_count`, `since_ack`, and the terminal row errors.
2. If the user/operator explicitly authorizes resuming and the rows are reviewed stale terminal envelopes, acknowledge with a receipt that names the reviewed failure classes and preserves gates:
   ```bash
   python3 ~/.hermes/scripts/taskpool_escape_guard.py \
     --ack-reviewed \
     --reason 'reviewed post-ack terminal rows; mapped brain tasks preserved; preserve proof/lifecycle/multimodel gates; resume bounded drain'
   ```
3. Confirm readback includes:
   - `post_ack_readback.human_escape_triggered=false`
   - `since_ack.blocks=0`
   - `since_ack.failures=0`
4. Resume narrowly first:
   ```bash
   python3 ~/.hermes/scripts/agent_team_controller.py cycle \
     --max-claims 1 \
     --max-workers 1 \
     --claim-wall-budget-seconds 120 \
     --execute-wall-budget-seconds 420
   ```
5. After each bounded cycle, immediately run:
   ```bash
   python3 ~/.hermes/scripts/brain_task_orchestrator.py blocked-resolve-step --max-tasks 10 --authority dispatch-hint --json
   python3 ~/.hermes/scripts/brain_task_orchestrator.py auto-close-review --max-tasks 10 --authority dispatch-hint --json
   python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json
   python3 ~/.hermes/scripts/brain_task_orchestrator.py proof-check --json
   ```
6. If workers are still alive, report that honestly; do not claim drain completion from old summaries or from a process list alone.

## 3. Shell heredoc pitfall during claim consumption

When transforming claimed task JSON in shell, do not put redirection inside the Python heredoc body:

Wrong:

```bash
python3 - <<'PY'
...
PY > /tmp/claimed.json
```

This can be parsed as Python text and raise `SyntaxError`.

Safer patterns:

```bash
python3 - <<'PY' > /tmp/claimed.json
import json
p=json.load(open('/tmp/parallel-claim.json'))
print(json.dumps(p.get('claimed_tasks', []), ensure_ascii=False))
PY
```

or write the file from Python:

```bash
python3 - <<'PY'
import json
p=json.load(open('/tmp/parallel-claim.json'))
open('/tmp/claimed.json','w',encoding='utf-8').write(json.dumps(p.get('claimed_tasks', []), ensure_ascii=False))
PY
```

Then consume with:

```bash
python3 ~/.hermes/scripts/agent_team_controller.py consume-claimed \
  --claimed-json "$(cat /tmp/claimed.json)" \
  --max-agents 1
```
