# Full-pool advance: bounded loop when the user asks to “全盘推进”

Use this when the user is not asking for a read-only health check, but wants the taskpool actively pushed forward.

## Goal

Advance the pool without doing any of these by accident:
- misreporting `dispatchable` as “already executing”
- leaving an advisory task stuck in `claimed`
- forcing `done`/`review` when only a first evidence tranche landed
- blaming proof debt when the real blocker is `autorun_disabled`

## Proven sequence

1. Re-baseline the live pool first.
   - `list --json`
   - `next --json`
   - `dispatch-dry-run --json`
   - `selfcheck --json`

2. Run the normal automation path before manual intervention.
   - `autorun-runner --json`
   - `auto-claim-and-handoff --json`
   - multimodel intervention step/dry-run as appropriate

3. Interpret the result correctly.
   - If the pool is still `dispatchable=true` but nothing starts and the payload shows `autorun_enabled=false`, `autorun_disabled`, or `allowlist_miss`, treat that as the primary reason full-pool advancement did not auto-execute.
   - Do not misdiagnose this as “no candidate task” if `next --json` still nominates a real task.

4. Manually advance one highest-value dispatchable task.
   - Prefer the current `next --json` candidate.
   - Claim it explicitly.
   - Read the task note before writing.
   - Land one bounded, real evidence tranche tied to the task’s acceptance shape.

5. For advisory / evidence-deposition tasks, release after bounded progress.
   - If you only landed the first evidence tranche and the task is not truly complete, release it back to `pending` with a precise reason.
   - This is better than leaving the task artificially wedged in `claimed`.
   - Keep the note fail-closed: record residual uncertainty and the exact next boundary still missing.

6. Clean up bounded automation claims before final reporting.
   - If `autorun-runner`, `auto-claim-and-handoff`, or the dynamic auto-completer left tasks in `claimed` but no worker body actually ran, release those tasks back to `pending`.
   - Use an explicit reason such as `bounded_full_pool_advance_handoff_or_evidence_verified_release_no_worker_body`.
   - Use a CLI-accepted transition authority; `brain_task_orchestrator.py transition --authority` is an enum. `claim-and-handoff` and `budget-handoff` are both safe cleanup authorities. Do not invent free-form authority labels like `bounded-full-pool-advance-cleanup` because argparse accepts them silently but the transition does nothing. See `references/bulk-taskpool-unclog.md` for the full authority enum table.
   - Verify `claimed=0`, `stale_claims=0`, and that the task remains honestly dispatchable rather than falsely complete.

7. Re-test the pool.
   - `list --json`
   - `next --json`
   - `dispatch-dry-run --json`
   - `selfcheck --json`
   - `proof-check --json`
   - `evidence-spine --json`
   - `python3 ~/.hermes/scripts/post-update-check.py` for Hermes governance drift when the work touched Hermes/taskpool infrastructure
   - For self-evolution/taskpool-governance rounds, run `pua_loop_self_optimize.py p10-check` with explicit `--goal`, `--boundary`, `--evidence`, and `--next-action`; include Tool/Skill/Benchmark wording in evidence when the leverage check should pass.

## Task-type-specific closeout requirements

Do **not** use one generic `proof/selfcheck/py_compile` closeout shape for every task. Before moving any task to `done`, classify what kind of completion it claims and require matching evidence:

- **Feature / implementation tasks**: require a concrete landed implementation artifact plus an end-to-end or realistic smoke proof of the feature path. Examples: script/module path, cron/hook/config wiring, dry-run and real-input run, created task/file/API response, regression test. `py_compile`, `proof-check`, `selfcheck`, or dashboard refresh alone are insufficient.
- **Integration / automation tasks**: require evidence that the automation boundary is actually connected. Examples: cron prompt/script updated, hook invoked, taskpool `add`/`ingest` called in dry-run and write mode, idempotency/dedup checked, fallback behavior observed.
- **Governance / policy tasks**: require the rule to be encoded where the runtime consumes it, plus a failing-before/passing-after test or deterministic selfcheck. A markdown proposal alone is advisory, not done. For local policy/evaluator tasks, acceptable closeout evidence can be a structured `implementation:` script path plus `py_compile` and a deterministic sample-run command; do not require browser/API proof merely because the policy dimensions mention UI/API unless a live UI/API surface was actually implemented.
- **Research / advisory tasks**: require deposited report/artifact evidence and explicit handoff boundaries. These can close without code only if the task objective is advisory and the final handoff says no implementation was promised.
- **Evidence-only / cleanup tasks**: require proof that the specific debt was migrated/cleaned and current gates pass.

If the task's `acceptance_evidence` says “script/control-plane落点/最小实现/验证步骤”, closeout must include those artifacts. If only a bounded tranche landed, return the task to `pending` or keep it in `review`; do not mark `done`.

## What to write into the task note during bounded advancement

For external-repo / advisory tasks, the first bounded tranche should usually include:
- `capability_delta`
- `anti_drift_check`
- `acceptance_evidence`
- structured `evidence:` entries
- validation rows showing what was actually checked
- proof log explaining why the task is still not ready for closeout
- blockers / confusions that preserve fail-closed interpretation
- final handoff that says whether to keep pending, block, or promote later

## Interpretation rules

- `next` staying the same after manual advancement does **not** mean nothing changed.
  - It may simply mean the same task is still the highest-value pending item, now with better evidence.
- Historical `proof-check FAIL` remains secondary if the immediate reason nothing auto-ran is `autorun_disabled`.
- A bounded advisory advancement counts as real progress when the note now contains durable evidence and sharper execution boundaries.

## Pitfalls

- Do not call it “fully advanced” if you only inspected state.
- Do not leave a partially worked advisory task in `claimed` just because you touched it.
- Do not upgrade README marketing claims into repository facts without boundary checks.
- Do not convert “automation disabled” into a fake governance/proof explanation.
- Do not close an advisory task just because the first evidence artifact exists.
- Do not force `done` when a governance/policy task has a real local deterministic implementation but `auto-close-review` still reports `api_or_backend_readback_proof` / `browser_or_ui_surface_proof` missing. Record the mismatch explicitly: implementation artifact, deterministic sample run, hashes, and the gate’s refusal reason. Treat the remaining work as close-gate calibration, not as proof that the implementation did not happen.

## Local deterministic evaluator tranche

For governance / policy / selfcheck-standard tasks, a strong bounded tranche can be a local deterministic evaluator rather than an external API or browser surface. The minimum evidence bundle should include:

- policy/template artifact path and hash;
- executable script path and hash;
- fixture or sample report path and hash;
- syntax check such as `python3 -m py_compile` when applicable;
- deterministic sample run output with the key decision fields;
- explicit no-network/no-side-effect boundary;
- task note validation rows and proof log;
- follow-up note if `auto-close-review` does not yet recognize this evidence class.

If `auto-close-review` still blocks after this bundle, do not weaken the lifecycle gate. Leave the parent in `review`, record the refusal reason, and queue/perform a separate close-gate calibration task only when authorized.

## Multimodel/advisory closeout lifecycle pitfall

For self-evolution or architecture-target tasks, moving a task to `review` can spawn advisory closeout ratification. That background process may temporarily claim lifecycle ownership and move the task back to `running`. Before final `done`, poll the async/advisory job list until no jobs are alive. If a duplicate advisory job appears after closeout and has no log progress past the normal command timeout, inspect its job/log/state files, terminate only that stale job, and re-run list/next/dispatch/selfcheck/proof checks. Do not treat this as a reason to disable advisory ratification globally.

## Workflow-kernel enterprise open-gate closeout

When advancing a Hermes workflow/control-plane runtime from dry-run to production-style external side effects, do not treat “opened” as a single Boolean. Open it in bounded enterprise layers and verify each layer independently:

- **Open manifest**: explicit confirmation string, manifest digest, kill switch, minimal target/purpose, and readiness artifact hashes.
- **Target registry**: explicit target IDs and owners; enabled targets only; no arbitrary discovery; per-target purpose allowlist, daily/hourly/burst limits, compensation path, and kill switch.
- **Payload guard**: dynamic payloads are allowed only after deterministic classification; block secret-like keys/tokens/passwords/private keys, disallowed purposes, empty or overlong payloads; record payload hash.
- **Runtime sender**: compute idempotency per target + purpose + payload digest + manifest digest + day bucket; read both legacy flat ledgers and v2 aggregate ledgers so duplicate detection survives schema evolution.
- **Cron wrapper**: in no-agent production mode, emit compact receipts only on real send, stay silent for expected duplicate/daily-limit suppression, and alert on unexpected blockers (manifest closed, kill switch, payload guard failure, target not allowlisted).
- **Proof**: include one real send or, if daily limit is already exhausted, prove the guard path with a blocked duplicate plus payload-guard negative/positive samples. Re-run cron manually and read back `last_status=ok`.

Pitfall: after moving architecture/evolution tasks to `review`, advisory multimodel hooks may start another background job and move the task back to `running`. Poll `multimodel-intervention-jobs --json` until `alive_count=0`; if a duplicate advisory job has no log output past the command timeout, terminate only that stale job and re-run list/next/dispatch/selfcheck/proof before reporting closure.

## Good end-state for this pattern

A successful bounded full-pool advance often ends like this:
- automation path was exercised and its blocker identified
- one real dispatchable task received a concrete evidence tranche
- that task was released back to the correct lifecycle state
- post-checks confirm the pool is still healthy, still dispatchable, and not falsely reported as running
