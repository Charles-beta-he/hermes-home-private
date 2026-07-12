# Multimodel T3 provider-gate debugging

Use when a taskpool parent closeout is ready for T3 certification but the parent stays `pending` / `not_certified`, an async multimodel job exits without a final `discussion_result.json`, or a required reviewer/provider blocks quorum.

## Pattern

1. Do not force `review`, `certified`, or `done` from advisory output.
   - `PASS_ADVISORY_ONLY` is not lifecycle authority.
   - `4/5 approve` is not equivalent to T3 certification when the plan requires `--quorum 5`.
2. Inspect durable async receipts before rerunning:
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py multimodel-intervention-jobs --task <task_id> --json`
   - Check `alive`, `recommended_tier`, `advisory_only`, `log_path`, and `state_path`.
3. If the job is dead and the job JSONL log is empty, separate the two questions:
   - Did the state build succeed?
   - Did model discussion produce checkpoints or a final result?
4. Reproduce the selected plan manually, bounded and with retained artifacts:
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py multimodel-intervention-dry-run --task <task_id> --json`
   - Run the selected `build_state_command` first.
   - Run the selected `run_discussion_command` with an explicit larger per-planner timeout if needed, e.g. add `--timeout 300 --keep` to `consult_models.py run`.
5. If `consult_models.py` exits 143 / -15, do not infer success or failure from stdout. Inspect the retained `tick-*` directory:
   - If `discussion_result.json` exists, run the task-scoped `ratification-gate` and bind the conclusion to that output.
   - If only `discussion/round_001/round_summary.json` exists, treat it as checkpoint evidence for the blocker, not certification.
   - If only model checkpoints exist (`discussion/state.json`, `heartbeat.json`, `parse_status_*.json`, `model_response_*.json`), identify the next incomplete model and provider-health state before rerunning.
6. When a provider/account recovery reopens one bounded parent refresh, run a small smoke first, then the exact parent dry-run. If the dry-run opens `recovery_rerun`, prefer a retained target-bound discussion (`--keep`) so missing/partial artifacts survive interruptions.
7. If the official step is SIGTERM/interrupted but the state is built, a manual retained `consult_models.py run <state> --tier T3 --discussion --max-rounds 1 --keep` can be used as a readback-only diagnostic to force a `discussion_result.json`; then run `ratification-gate`. This is not lifecycle authority and must not lower quorum or mark done.
8. Read the round summary or discussion result:
   - `status_detail.reasons`
   - each vote's `vote` and `best_within_constraints`
   - provider/runtime errors embedded in failed votes.
   - unresolved severity issues and whether the remaining blocker is provider/runtime or content-level disagreement.
9. If a failed ratification attempt leaves the task `running` but no live worker/multimodel job remains, fail-closed back to `blocked` with exact evidence (`discussion_result`, gate FAIL/continue_loop, no-live-owner readback). Do not leave parent tasks running after a failed gate just because a background step was interrupted.
7. If a required participant is missing, inspect the pre-discussion selection pipeline before assuming the model was never configured:
   - compare configured `ratification.required_models` / tier planners with `models_used`, `prompt_chars_by_model`, and `ratification_votes` in the retained tick artifact;
   - inspect model-health/circuit-breaker state and quota-gate snapshots separately;
   - MiMo/Xiaomi can pass tiny probes but fail planner-shaped prompts because reasoning tokens consume the completion budget and `message.content` becomes empty or truncated, producing JSON parse failures that open a temporary health breaker;
   - stable repair is adapter/prompt/observability first: remove baked-in small `max_tokens` caps, make any token budget override configurable, retry once with a compact JSON-only prompt on `finish_reason=length` or empty/truncated `content`, and make probes classify HTTP-200 empty/truncated content as degraded rather than OK;
   - align dispatch capacity probes with required certification participants (for example include required MiMo in `taskpool.api_quota_models`) so taskpool summaries show the model in `models_checked` and expose pass/soft-unknown/hard-blocker status;
   - when this happens, keep the parent not certified, classify it as provider/adapter-budget degradation, and repair the adapter budget/prompt/health state before rerunning target-bound T3.
8. If a required participant failed due to provider/account/quota/auth, stop at a human gate unless existing governance explicitly permits substitution or quorum change.
   - Treat CLI login/auth messages such as `Not logged in`, `Please run /login`, `authentication credentials`, `unauthorized`, or `forbidden` as hard provider-health gates, not transient planner failures; they should not be restored merely to satisfy `min_quorum`.
   - Do not silently remove the model.
   - Do not lower quorum.
   - Do not claim certification from the remaining approvals.
9. Capture the operational bug separately if output/artifacting was poor:
   - use `runtime_issue_capture.py --mode suggest ...`
   - this records a control-plane repair candidate without mutating the project task lifecycle.

## Human-gate packet contents

When blocked by a provider gate, write a packet with:

- parent task id and current status
- async job receipt path
- job log path and whether it was empty
- state path
- retained tick directory
- checkpoint path, if no `discussion_result.json`
- approvals and failed participant
- exact provider error, redacted if necessary
- decision options: repair provider, authorize task-scoped quorum exception, authorize replacement reviewer, or keep parent pending and open control-plane repair
- rollback: keep parent `pending` / `not_certified`; no parent lifecycle mutation
- post-action verification: rerun target-bound T3, confirm `discussion_result.json`, run `ratification-gate`, then normal lifecycle gate only if `PASS/LOOP_DONE`.

## Anti-conditions

- Do not use this to bypass a T3 gate for convenience.
- Do not save project-specific task ids, tick dirs, or provider-account incidents as global memory; keep those in the project profile, ledger, or gate packet.
- Do not treat environment-specific provider failures as a permanent negative tool claim. Capture the fix path or human decision needed instead.
