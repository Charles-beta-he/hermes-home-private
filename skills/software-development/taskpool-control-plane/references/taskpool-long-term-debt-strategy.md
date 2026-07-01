# Taskpool long-term debt strategy

Use this when the user asks for an engineering review of Hermes/taskpool long-term debt, especially when they request actionable patches/scripts/verification order and do not want files modified yet.

## Core interpretation

Do not confuse a healthy idle control plane with unsolved historical debt.

A common live shape is:
- `agent_team_controller.py status --json` shows `dispatchable_tasks=0` and `human_escape_triggered=false`.
- `brain_task_orchestrator.py selfcheck --json` returns PASS, while classifying many old issues as `terminal_or_unrelated_backlog`.
- `brain_task_orchestrator.py proof-check --json` returns PASS with many warnings.
- `v_state.py --json` is HEALTHY but bottlenecked on `envelope` because historical terminal envelope/proof debt is still counted.

In that shape, do **not** force-promote tasks, clear DB rows, or invent proof. Treat the work as debt lifecycle engineering: observe, classify, compact, migrate evidence, then adjust health scoring.

## Read-only baseline first

Run these before proposing edits:

```bash
python3 ~/.hermes/scripts/agent_team_controller.py status --json
python3 ~/.hermes/scripts/envelope_bus.py stats
python3 ~/.hermes/scripts/brain_task_orchestrator.py list --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py proof-check --json
python3 ~/.hermes/scripts/v_state.py --json
python3 ~/.hermes/scripts/taskpool_dynamic_runner.py --json
python3 ~/.hermes/scripts/continuation-gc.py --dry-run
```

Interpretation:
- `human_escape_triggered=false` + no timeouts means no emergency envelope recovery.
- `dispatchable=0` / `next=null` can be healthy final drain, not idle-spin.
- Proof-check PASS with warnings means the gate is fail-softing historical debt; do not relax proof gates just to remove warnings.
- `taskpool_dynamic_runner.py --json` and `continuation-gc.py --dry-run` may intentionally emit empty stdout on a healthy/no-op tick.

## Proven 2026-06-07 closure pattern

A successful long-term debt pass used this sequence:

1. Gather the baseline across health, taskpool, cron, envelope bus, proof-check, dispatch summary, continuation state, and Experience Ratchet. Keep the output read-only until the debt classes are separated.
2. Run a multimodel review in roles, but keep the merged decision concrete:
   - architecture: separate runtime blockers, historical governance debt, and lifecycle backlog;
   - engineering: add a read-only ledger before mutating queues, harden executor/parser first;
   - self-evolution: choose automation level L0/L1/L2/L3/L4 and preserve human/multimodel gates for irreversible or strategy changes.
3. Land only L0/L1 fixes first:
   - `taskpool_debt_ledger.py` read-only summary script;
   - `envelope_executor.py` proof parser supporting single-line, fenced, and multiline `PROOF_JSON`;
   - worker timeout/wall-budget envs so no-agent cron produces classified results before the scheduler timeout.
4. After patching a cron-backed script, run the affected cron job once with `cronjob(action='run', job_id=...)` or the equivalent scheduler command. Manual script success is not enough; prove `last_status=ok` under scheduler context.
5. Re-verify in this order: `py_compile`, parser samples, `cron-health-quarantine.py`, `unified-health-check.py`, `selfcheck --json`, `proof-check --json`, `experience-ratchet-maze.py validate`, debt-ledger summary, scoped git status/commit.

Observed healthy final shape after this pass:
- cron health `bad_count=0`, `stale_count=0`;
- unified health `100/100`, all GREEN;
- ratchet validate `checked=13`, `ok=true`;
- envelope `live_count=0`, but `since_ack.failures=1` remains visible as runtime debt;
- proof warnings remain visible (`terminal_mission_envelope_debt` and `terminal_invalid_autorun_proof_hash_debt`) instead of being hidden;
- continuation active backlog remains a P2 lifecycle debt, not a reason to weaken dispatch gates.

Key lesson: solve the first durable failure mode (unstructured cron timeout / brittle proof parser) and add observability before touching historical proof or continuation debt. Do not treat `Health Score: 100/100` as permission to erase warnings; warnings are the backlog.

## Preferred phased implementation

### Phase 1 — Debt ledger, read-only

Add or run `taskpool_debt_ledger.py` before changing state. It should summarize:
- envelope status totals and top terminal errors from `~/.hermes/state/envelope_bus.db`;
- proof-check warning categories, especially terminal mission envelope debt and invalid autorun proof hash debt;
- active task flow health: status distribution, review-gap count, retry circuit-breaker candidates (`retry_count >= 3`), duplicate/projection drift rows, inferred completion profiles, and advisory/diagnostic evidence-type risks;
- continuation active/archived counts and duplicate active packets by task;
- handoff artifact backlog counts;
- `v_state.py --json` result.

This gives a stable before/after scorecard and prevents confusing historical debt, control-plane liveness, flow debt (`review`/`blocked`/`retry`), and projection drift. Treat this ledger as read-only evidence: it may recommend repair packets or circuit breakers, but it must not mutate task lifecycle by itself.

### Phase 2 — Legacy envelope executor hardening

If `envelope_executor.py` is still cron-driven, harden it rather than relying only on the newer agent-team controller:
- Accept multiline/fenced `PROOF_JSON`, not only single-line `PROOF_JSON:`. DeepSeek/Gemini/MiMo often emit fenced or multiline proof objects; single-line parsing creates false `invalid_proof` / `missing_proof` debt.
- Add a cron wall budget and shorter worker timeout environment variables so no-agent cron does not outlive scheduler expectations:
  - `ENVELOPE_EXECUTOR_WORKER_TIMEOUT_SECONDS`
  - `ENVELOPE_EXECUTOR_WALL_BUDGET_SECONDS`
- If insufficient wall budget remains, return a classified deferred result instead of starting another long worker.

Verification:

```bash
python3 -m py_compile ~/.hermes/scripts/envelope_executor.py
python3 - <<'PY'
import sys, json
sys.path.insert(0, str(__import__('pathlib').Path.home()/'.hermes/scripts'))
from envelope_executor import extract_proof
samples = [
    'x\nPROOF_JSON: {"status":"done","summary":"ok"}',
    'x\nPROOF_JSON:\n```json\n{"status":"blocked","summary":"need auth"}\n```',
    'x\nPROOF_JSON:\n{\n  "status": "done",\n  "summary": "multi"\n}',
]
for s in samples:
    p, sha, err = extract_proof(s)
    print(json.dumps({'proof': p, 'sha': bool(sha), 'err': err}, ensure_ascii=False))
PY
ENVELOPE_EXECUTOR_WALL_BUDGET_SECONDS=20 python3 ~/.hermes/scripts/envelope_executor.py run 1
python3 ~/.hermes/scripts/envelope_bus.py stats
```

### Phase 3 — Continuation lifecycle compaction

`continuation-gc.py` should not only age out active packets. Long-term debt control needs:
- active max cap;
- archived max cap;
- per-task active retention cap, e.g. keep newest 3 packets per task;
- dry-run first;
- gradual real caps, not one huge destructive cleanup.

Suggested environment knobs:
- `CONTINUATION_ACTIVE_MAX=100`
- `CONTINUATION_ARCHIVED_MAX=1000`
- `CONTINUATION_KEEP_PER_TASK=3`

Verification:

```bash
python3 ~/.hermes/scripts/continuation-gc.py --dry-run
CONTINUATION_ARCHIVED_MAX=3000 python3 ~/.hermes/scripts/continuation-gc.py --dry-run
python3 -m py_compile ~/.hermes/scripts/continuation-gc.py
```

Only after reviewing dry-run output should a real run be used, preferably reducing caps in stages.

### Phase 4 — Handoff backlog as artifacts, not task status

Handoff backlog cleanup should start as a read-only report script (`handoff-gc.py`) that scans artifact/state/evidence paths for `*handoff*`, emits count/bytes/largest/oldest/sha256 manifest, and does not edit task status.

Do not delete or move handoff artifacts in the first pass unless the report proves they are redundant and the user approves compaction policy.

### Phase 5 — Proof debt migration dry-run

For `proof-check` warnings, build a dry-run migration plan before writing task notes:
- Map warnings to candidate task files/artifacts.
- Read existing task body proof (`## Proof Log`, `## Final Handoff`, artifact paths, command/browser/build evidence).
- Classify as migratable only when real evidence already exists.
- Never fabricate fresh test/build/browser results for historical closeouts.
- For invalid autorun proof hashes, recover only from a real append-only autorun proof log event (`auto_run_proof.jsonl`) linked to the same task/parent closeout chain. A nearby file digest is not an autorun proof event. If source recovery is exhausted and the user authorizes cleanup, replace the bad `proof:sha256:*` entry with structured debt such as `classification:legacy_unrecoverable_autorun_proof_debt:sha256:<missing>` plus an `artifact:` pointer to the recovery report. See `references/taskpool-proof-source-recovery-and-legacy-isolation.md`.

Batch writes, if approved, should be tiny (e.g. 5 tasks per run) and followed by:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py proof-check --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json
```

### Phase 6 — Health scoring after observability exists

Only after the debt ledger exists should `v_state.py` scoring be adjusted. The envelope score should primarily penalize live risk:
- since-ack failures/blocks;
- RUNNING timeouts;
- PENDING/RUNNING backlog;
- active human_escape.

Historical FAILED/BLOCKED counts should remain visible in diagnostics as historical debt, but should not permanently make a drained, since-ack-safe pool look unhealthy.

## Governed slice interruption / blocked readback

If a taskpool/control-plane slice has already passed focused tests, py_compile, and control-plane checks but a final readback or JSON summarizer command is blocked by the runtime safety layer, do not retry the same command shape, rephrase it, or route around it. Freeze the slice boundary and emit an intervention packet before commit or next-slice work.

See `references/governed-slice-interruption-and-readback.md` for the reusable procedure, pitfalls, and evidence bundle shape.

## Anti-patterns

Avoid these first-round “fixes”:
- clearing historical FAILED/BLOCKED envelope rows;
- acknowledging escape without understanding post-ack failures;
- force-promoting tasks when `dispatchable=0` is a valid no-work state;
- closing or marking done from proof-check warnings alone;
- relaxing proof gates to hide warnings;
- deleting continuation/handoff artifacts without a manifest and dry-run;
- treating empty stdout from no-agent watchdog scripts as failure.

## Final report format for this user

When asked for an engineering review, give:
1. concise diagnosis;
2. actual read-only commands run and their key results;
3. phased patch/script plan;
4. exact verification order;
5. explicit statement that files were not modified if the user requested no changes.
