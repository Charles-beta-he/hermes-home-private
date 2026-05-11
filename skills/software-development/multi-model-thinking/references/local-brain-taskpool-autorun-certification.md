# Local Brain Task Pool Autorun Certification Pattern

Use this reference when changing local-brain task-pool automation, cron ticks, lifecycle gates, or any bridge that could claim/execute/close tasks.

## Core lesson

For local task-pool automation, do **not** implement a broad autonomous executor that treats Markdown task notes as executable scripts. The certified safe shape is a fail-closed control-plane bridge:

```text
observe/reconcile/select -> eligibility-check -> auto-claim-and-handoff -> external bounded runner -> proof -> review -> done
```

The automation layer may claim and create a bounded handoff. It must not execute the task body and must not mark tasks done.

## Required safety gates

For caller-level write-guard integration details, also apply `references/autonomy-write-guard-caller-integration.md`: the actual caller must invoke `guard_or_raise` before claim/handoff/proof, and `dispatch-hint` must not bypass the central write-surface allowlist.

1. Default off: `HERMES_LOCAL_BRAIN_AUTORUN` must be explicitly `1`; unset/other values deny.
2. Allowlist default deny: missing/empty allowlist denies; allowlist miss denies.
3. Eligibility is fail-closed: selfcheck, proof-chain integrity, task dispatchability, and reconcile state must be PASS/OK before claim.
4. Safe tick default is hint-only: cron/tick should run ingest/reconcile/dashboard/proof-check/dispatch-dry-run only.
5. Optional tick bridge must require explicit opt-in (for example `--autorun`) and run only after safe tick gates pass.
6. Auto layer only does claim + handoff + proof event; never Markdown execution, arbitrary hooks, or automatic done.
7. Autorun-originated done requires `proof:<sha256:...>` evidence from an append-only proof JSONL/hash-chain.
8. Preserve lifecycle invariant: `done` should pass through `review -> done`; do not let runner/tick bypass review.
9. `proof-check` must audit persisted autorun done notes for missing/invalid proof hash, not only enforce transition-time gates.
10. Evidence shape matters: bare filesystem evidence should require an existing absolute path; use explicit prefixes such as `artifact:` for durable-but-not-local artifacts.

## Deterministic verification checklist

Run these before asking models to certify:

```bash
python3 -m py_compile ~/.hermes/scripts/brain_task_orchestrator.py ~/.hermes/scripts/brain_task_dispatch_tick.py ~/.hermes/scripts/test_brain_task_orchestrator.py ~/.hermes/scripts/test_brain_task_dispatch_tick.py
python3 ~/.hermes/scripts/test_brain_task_orchestrator.py
python3 ~/.hermes/scripts/test_brain_task_dispatch_tick.py
python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py proof-check --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py boundary-check --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py parallel-dispatch-dry-run --max-agents 3 --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py eligibility-check --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py auto-claim-and-handoff --json
python3 ~/.hermes/scripts/brain_task_dispatch_tick.py --print-always --no-state
```

When adding task-pool boundary or multi-agent dispatch features, also add those same boundary/parallel commands to the multi-model loop runner's deterministic gate list before seeking certification. The verifier evidence bundle must prove the new gate runs in both direct CLI verification and the ratification runner, not only in ad hoc tests.
```

Expected production-safe disabled-mode observations:

- `eligibility-check`: `eligible=false`, reasons include `autorun_disabled` and `allowlist_empty`.
- `auto-claim-and-handoff`: `claimed=false`; safety says no claim/no execution.
- default safe tick: no `autorun` block; dispatch output remains dry-run/hint-only.

## Multi-model certification loop

1. Package claims and evidence explicitly; link each evidence item to claim IDs.
2. Run T2/T3 quorum4 with `--discussion` when task automation/lifecycle safety is in scope.
3. If the outer command times out, inspect latest `~/.hermes/tick-*` artifacts before rerunning; missing `discussion_result.json` means not certified.
4. Treat amend votes as work, not caveats. Apply concrete verifier patches, rerun deterministic checks, rebuild evidence bundle, then rerun certification.
5. Certification is only final when `discussion_result.json` is `certified` (or intentionally `certified_with_minor_risks`), truth gate is grounded, high-severity issues are resolved, and votes meet the ratification gate.

## Autonomous loop-runner pattern

When the user asks for “loop 推进，每轮多模型分析检验，直到多模型认为结束”, implement a control-plane runner rather than relying on conversational judgment:

```text
deterministic gates -> claim/evidence state -> consult_models T3 quorum4 discussion -> issue ledger -> verify_ratification -> LOOP_DONE | continue_loop
```

Recommended runner API:

- `build_state_payload(question, gates, round_index)`: writes explicit claims, acceptance criteria, deterministic command evidence, and target files.
- `build_consult_run_command(state_file)`: should call `consult_models.py run <state> --tier T3 --quorum 4 --discussion --max-rounds N --timeout S --keep`.
- `verify_ratification(discussion) -> (passed, reasons)`: validates certified/certified_with_minor_risks status, model count, agreement axes, closed severity>=3 issue/risk ledgers, approve votes, `best_within_constraints`, and truth/evidence coverage.
- `should_continue(discussion) -> (bool, reason)`: explicit driver boundary. Return false only when all ratification criteria pass; otherwise return true with blocking reasons.

Pitfalls learned:

- Do not stop because deterministic tests pass. Tests are evidence; `discussion_result.json` is the ratification artifact.
- If live quorum returns `not_certified` because one model claims the stop gate is implicit/ambiguous, patch the runner to expose explicit verifier/terminator APIs and add tests, even if equivalent logic already existed inline.
- For task-pool Mission DAGs, distinguish full mission envelopes from child mission nodes. A child node may carry `mission_id`, `mission_node_id`, `mission_node_depends_on`, and `permission_gates` without being forced to satisfy the full envelope schema. Dispatch readiness must require dependency nodes to be `done`, reject missing/cyclic dependencies via `boundary-check`, expose `mission_node_ready/blockers` in list rows, and render a derived `Mission DAG Progress` dashboard section.
- For proof-gated autorun runner integration, keep the runner as a bounded control-plane bridge: default-off + allowlist + write-guard + proof-chain checks, pause on `permission_gate_pending` / `ask-human`, then at most claim+handoff+proof-head. It must not execute Markdown task bodies or mark tasks `done`; done remains review + `proof:sha256:` gated.
- For task-pool parallelization, model the boundary as data first: add/verify a frontmatter field such as `parallel_boundary`, fall back to `workspace`/architecture target/project, expose a `boundary-check`, and make `parallel-dispatch-dry-run` skip conflicts rather than claiming both tasks. Warnings about same-boundary conflicts are acceptable; invalid boundary invariants must fail closed.
- For agent-team parallel taskpool execution, separate `dry-run dispatch planning` from `real worker execution`. `parallel-dispatch-dry-run --max-agents N` may select independent candidates and emit claim prompts, but real execution must remain disabled while any claim-bound task is `claimed`/`running`/`review` unless an explicit risk-accepted override is logged. A safe rollout is Phase 0 dry-run only → Phase 1 N=1 worker with controller-owned claim/spawn/review → Phase 2 N=2 with workspace/worktree isolation → Phase 3 N=3 via idle/cron allowlist. Workers must never execute Markdown bodies or mark tasks done; they only produce handoff/proof artifacts. The controller owns boundary-check, proof-check, selfcheck, merge review, and any lifecycle transition, with done still requiring review→done plus `proof:sha256:` evidence.
- When using multi-model review for agent-team parallelism, classify timeouts or missing `discussion_result.json` as advisory/not fully ratified even if Claude/Codex/DeepSeek planner artifacts exist. If MiMo/Xiaomi fails with unsupported model, report participant failure and do not claim four-model certification.
- Treat partial provider quorum failures as non-certification, not as approval. If `discussion_result.json` is missing, or the discussion cursor shows an unfinished round (for example 3/4 models completed) due to provider errors such as 403 or unsupported model IDs, preserve the latest tick artifacts, write a synthetic `discussion_result_missing` issue ledger/ratification artifact, and report `NOT_CERTIFIED_MAX_ROUNDS` instead of summarizing the approving models as certified.
- Treat the live issue ledger as the next implementation plan, not as prose feedback. For each `not_certified` round: read `round-N-issue-ledger.json` and the referenced `tick-*/discussion_result.json`, isolate the smallest concrete blocker, write a regression test that fails, patch, rerun deterministic gates, commit locally, and start a new live round.
- Distinguish implementation-required blockers from no-action advisory follow-ups. If a planner explicitly says acceptance criteria already pass / no severity>=3 blockers remain / root cause is no-action, low-risk `tune_threshold`, observability, deprecation, or documentation follow-ups should be classified as advisory/conditional, not concrete implementation patches that create an `implementation_required` + empty `patches=[]` contradiction.
- Outer `consult_models.py` timeouts must fail closed as structured runner output, not traceback. Catch `subprocess.TimeoutExpired`, preserve stdout/stderr tails and any newest matching `discussion_result.json`, mark `timed_out=true`, write the issue ledger, and return `NOT_CERTIFIED_MAX_ROUNDS` or equivalent safe status.
- Preserve `NOT_CERTIFIED_MAX_ROUNDS` as a safe outcome. Without an explicit bounded executor command, the runner should write issue ledger and fail closed rather than self-applying arbitrary model suggestions.
- Commit each successful hardening round locally with scoped files only; do not push unless requested.

## Scoped commit rule

Hermes home often contains many unrelated runtime dirty files (`.env`, logs, sessions, screenshots, checkpoints, tick dirs). For this class of work, always use scoped `git add` with only the changed scripts/tests/brain evidence files; never `git add .`.
