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

## Intervention trigger design — structural-first keyword filtering

When building automatic multi-model intervention triggers for task pools, keyword-based matching alone causes false-positive explosion. In a corpus of related tasks (e.g., all Hermes/local-brain development), common terms like "evidence", "architecture", "skill", "taskpool", "方案", "落地" appear in 60-90% of tasks, making keyword triggers useless for prioritization.

### Pattern: structural-first, keyword-supplemented

1. **Structural triggers are primary** — fire immediately on high-confidence signals:
   - `P0 + evolution lane` → `p0_evolution_blast_radius` (strong, fires alone)
   - `retry_count >= 2` → `loop_non_convergence` (strong, fires alone)
   - `stale_claim` → `stale_claim` (strong, fires alone)

2. **Structural signals need supplementing** — add as reasons but require ≥2 to fire:
   - `status in {running, review}` → `closeout_ratification`
   - `priority == P0` → `P0_priority`
   - `lane == evolution` → `evolution_lane`
   - `architecture_target` non-empty → `architecture_target`
   - `mission_envelope` → `mission_envelope`

3. **Keywords only add when structural exists** — never fire on keywords alone:
   - Search **title + concepts only** (not body/metadata/objective)
   - Use **high-precision keywords** (≤10 hits in corpus, not 30+)
   - Add as supplementary reasons: `accuracy_keyword`, `long_term_keyword`, `one_shot_keyword`

4. **Threshold**: ≥2 reasons to fire (prevents noise from single weak signals)

### Keyword noise analysis methodology

Before deploying keyword matching:
```python
# Count hit frequency per keyword across all tasks
for kw in all_keywords:
    count = sum(1 for t in tasks if kw.lower() in t.read_text().lower())
    hit_counts[kw] = count

# Remove noise: keywords hitting in >50% of corpus
noise = {kw for kw, c in hit_counts.items() if c > len(tasks) * 0.5}

# Keep signal: keywords hitting in 3-25% of corpus
signal = {kw for kw, c in hit_counts.items() if 0.03 * len(tasks) <= c <= 0.25 * len(tasks)}
```

### Search scope restriction

`task_search_text()` concatenates ALL fields (title+body+concepts+objective+acceptance_evidence+capability_delta+anti_drift_check+project+lane+architecture_target). This is too broad for keyword matching.

Use `task_keyword_text()` which searches only `title + concepts`:
```python
def task_keyword_text(task):
    concepts = " ".join(list_value(task.fm.get("concepts")))
    return f"{task.title}\n{concepts}".lower()
```

### Observed results

| Strategy | Trigger rate | Notes |
|----------|-------------|-------|
| Full-text + broad keywords | 98% (55/56) | Useless for prioritization |
| Signal-only keywords (3-25 hits) | 80% (45/56) | Still too noisy |
| Structural-first + tight keywords | 32% (18/56) | Actionable prioritization |

## Ratification gate dual-shape pattern

`ratification_gate_result()` in `brain_task_orchestrator.py` accepts two canonical shapes from `consult_models.py`:

**Shape A (explicit criteria)**: top-level `criteria_satisfied` dict with `accuracy`, `long_term_goal`, `one_shot_landing` all True, plus `final_design` with `next_slice`, `acceptance_evidence`, `rollback_boundary`.

**Shape B (derived from discussion)**: `status: certified`, 4 canonical model votes all approve, `agreement_matrix` >= 0.85, `issue_ledger` empty, `truth_status` grounded, `evidence_bundle` with all claims verified, `fanout_certification` multi_model_certified, `verification` with guard_metrics, `rollback_signal` with auto_rollback_if condition.

Both shapes require all 7 checks to pass:
1. Certification status in {certified, certified_with_minor_risks}
2. Issue ledger: no unresolved severity>=3
3. Canonical four-model votes (exact IDs: claude-opus-4-7, gpt-5.5, deepseek-v4-pro, mimo-v2.5-pro)
4. Agreement matrix >= 0.85 on framing/approach/implementation_order
5. Truth gate: truth_status not in {not_certified, unsupported, contradicted}
6. Criteria: accuracy + long_term_goal + one_shot_landing (explicit or derived)
7. final_design: actionable structure (Shape A fields OR Shape B diagnosis+verification+rollback_signal)

Truth gate supports nested `truth_assessment.truth_status` and `final_design.truth_assessment.truth_status`.

## Convergence stats pattern

`multimodel_convergence_stats()` computes pool-wide convergence:
- `total_active`: non-terminal tasks
- `multimodel_passed`: tasks with multimodel_status in {certified, certified_with_minor_risks}
- `multimodel_triggered`: tasks where `task_multimodel_intervention_required()` is True
- `pass_rate`: passed / total
- `trigger_rate`: triggered / total

Exposed in `multimodel-intervention-dry-run --json` output under `convergence` key.

## Auto-step with env var gating

`multimodel-intervention-step` command executes one bounded step:
1. Check `HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL=1` env var (SKIP if unset)
2. Find top intervention task via dry-run
3. Build state file (`consult_models.py state` via shell=True for && chains)
4. Run discussion (`consult_models.py run --discussion --tier T3 --quorum 4`)
5. Run ratification gate
6. On PASS: write result to task frontmatter

Integrated into `brain_task_dispatch_tick.py`: when env var is set, tick runs step after dry-run. `allowed_statuses` includes SKIP for when env var is not set.

## Task state mutation on gate PASS

`write_multimodel_result_to_task()` writes to task frontmatter on ratification PASS:
- `multimodel_status: certified`
- `multimodel_ratification_artifact: <path to discussion_result.json>`
- `certification_status: certified` (compatibility)

Uses frontmatter line-level update: finds existing keys and updates in-place, appends missing keys.

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
