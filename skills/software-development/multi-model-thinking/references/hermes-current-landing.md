# Hermes Current Multi-Model Landing

Extracted from `/Users/charles/.hermes/skills/software-development/multi-model-thinking/SKILL.md` on 2026-07-01T08:21:01.947404+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Hermes 当前落地方式

`consult_models.py` 已落地基础 DiscussionOrchestrator 能力：state builder、issue ledger、ratification gate、`--discussion` CLI、DeepSeek direct API fallback。

### 1. 主模型/编排器生成 state.json

```bash
python3 ~/.hermes/scripts/consult_models.py state \
  '你的问题/落地目标' \
  --context-json '{"repo":"/path/to/repo"}' \
  --constraint 'use four models' \
  --accept 'ratification gates pass' \
  --file consult_models.py \
  --verify 'python3 -m unittest ~/.hermes/scripts/test_consult_models_integration.py -v' \
  --out /tmp/mm-state.json
```

### 2. 四模型 fan-out + 讨论认证

```bash
python3 ~/.hermes/scripts/consult_models.py run /tmp/mm-state.json \
  --tier T3 \
  --quorum 4 \
  --discussion \
  --max-rounds 5 \
  --keep
```

### 3. 离线/测试模式

```bash
HERMES_MULTI_BRAIN_OFFLINE=1 python3 ~/.hermes/scripts/consult_models.py run /tmp/mm-state.json \
  --tier T3 --quorum 4 --shadow --discussion --max-rounds 2 --keep
```

输出 tick 目录中会包含：
- `plans/*.json`：各模型 seed proposal。
- `merged_plan.json`：consensus merge。
- `discussion_result.json`：status、issue_ledger、ratification_votes、agreement_matrix、remaining_risks。

If the outer command times out after planner fan-out but before discussion/ratification finishes, inspect the tick directory before rerunning:

```bash
find ~/.hermes -maxdepth 1 -type d -name 'tick-*' -mmin -60 | sort | tail -5
ls ~/.hermes/tick-*/plans/*.json ~/.hermes/tick-*/merged_plan.json
```

Before `resume-discussion`, verify the tick belongs to the exact target state:
- compare `merged_plan.json.meta.state_hash` with the state file hash when available;
- inspect `evidence_bundle.claims` / `evidence_bundle.evidence` for the target repo, project name, and expected claim IDs;
- reject any tick whose claims mention another project, orchestrator, or old task even if it is the newest tick;
- if a resume output contains unrelated claims, mark it contaminated/not-certified and rerun with a fresh state rather than citing it.

Target-bound artifact hard gate for taskpool/Lark closeout:
- Do not trust a task note's `multimodel_status: certified` or `multimodel_ratification_artifact` at face value. Open the artifact and prove it is bound to the exact task before using it for done/closeout.
- Required checks: explicit task binding fields (`task_id`/`target_task_id`/`task_path`/nested context equivalents) match the target task, no explicit binding candidate points at another task, `models_consulted` and `ratification_votes` contain the expected full set, artifact claims/evidence paths mention the target task/proof/project rather than an unrelated task, and the state/question/target identifiers match the current decision.
- For this user's Lark/taskpool closeout, the expected full set is the canonical four-model panel: Claude + GPT/Codex + DeepSeek + MiMo. A 3/4 artifact is advisory/not-certified, not a closeout certificate, even if an older quorum/fanout field says certified.
- If `brain_task_orchestrator.py ratification-gate` returns PASS on a mismatched artifact, treat that as an infrastructure verifier gap, not as permission to close the task. Report `not_certified_for_target`, keep the task in `review`/`blocked`, and add/plan a target-binding verifier before automatic done/writeback.
- For diagnosis-only questions such as "is task Score X stuck?", separate facts: execution state (`running`/`claimed`/`stale_claim`), closeout state (`review`/human gate), implementation evidence, and certification artifact validity. A task can be not stuck and still not done because the correct gate is waiting for human/code review or remote/Lark closeout.
- When building a diagnostic state, avoid claims phrased as prohibitions that evidence objects can accidentally `contradict`; express positive factual claims (e.g. "old artifact lacks DeepSeek and is target-mismatched") so the truth gate does not fail due to claim/evidence wording rather than the underlying diagnosis.

Interpretation:
- `plans/*.json` for all requested models + `merged_plan.json` means fan-out produced useful evidence.
- To verify Claude Code specifically participated, inspect `plans/claude-*.json` and require `meta.adapter == "claude-code"` (or the expected Claude adapter), a non-empty `diagnosis`/`patches`, and a real `latency_ms`; this proves Claude contributed to seed planning, but does **not** prove final ratification.
- Missing `discussion_result.json` or timeout during consensus means the result is **weak consensus / not fully ratified**, even if 4 models answered.
- If one planned model failed (for example MiMo provider/adapter returns `Param Incorrect` / unsupported provider) while Claude/Codex/DeepSeek produced plans, report participant status per model: `claude_code=participated`, successful planners as advisory, failed planners as missing/failed, and keep final status below full four-model certification.
- Report `fanout_status`, `consensus_verdict`, `unanimous_count`, `majority_count`, `minority_count`, and `arbitration_needed` from `merged_plan.json`. Some merged-plan fields may be nested under `merge_info`; inspect both top-level and nested keys rather than assuming a flat schema.
- After `resume-discussion`, run or inspect `final/certification_manifest.json` when available. Treat it as the conservative gate if it reports count inconsistencies, unsigned `best_within_constraints`, adapter failures, or `discussion status is not_certified`, even when `fanout_certification.certified=true` and truth grounding is 1.0.
- Do not claim full multi-model certification unless the ratification artifact exists and stop conditions pass.
- Prefer summarizing existing artifacts over immediately rerunning an expensive T3 discussion; rerun only if the missing ratification materially changes the decision.

For long-running or repeatedly-timed-out discussions, see `references/long-running-discussion-and-resume.md` and `references/current-code-certification-after-amend.md`. Key point: `--max-rounds` and `--timeout` can extend discussion, but online discussion calls models serially and may retry JSON parsing, so run long T3 certification in the background with `--keep` and inspect `discussion_result.json` afterward. If the session/tool-call budget is near exhaustion, do not start a fresh long T3 run unless you can still poll/read the verdict; prefer preserving the exact state path, tick/process id, and `not_certified_yet` handoff. If interrupted while the background run is still running, the final answer must say ratification is incomplete and must not proceed to commits or imply certification. If a deterministic patch or amend happens after a prior certified tick (even a small safety/redaction fix), that old artifact becomes provenance/advisory for the previous code state only; build a fresh current-code state and require a new `discussion_result.json` + `final/certification_manifest.json` before claiming 4/4 current-code certification. If the blocker is missing runtime evidence, run an Evidence Request Fulfillment Loop before adding more rounds.

For evidence reports, rebase gap analysis, and implementation-order decisions, do not let a silent/long-running T3 consult block deterministic progress. Start `consult_models.py` with a saved state file and `--keep`, continue collecting source/test evidence, and if the consult produces no stdout/artifact within the task budget, label it as `started/no_ratification_artifact` or `not_certified`, stop/clean the background process, and proceed with a report grounded in code, git, docs, and test outputs. Never upgrade such a run to multi-model certification; use it only as advisory provenance if artifacts appear later. If the process tool cannot kill the background job (for example a local `psutil` import failure), clean it with terminal/PGID (`pgid=$(ps -o pgid= -p PID | tr -d ' '); kill -TERM -$pgid`).

For low/medium-risk scoped closeouts where `plans/*.json` and `merged_plan.json` exist but `discussion_result.json` is missing, use `references/fanout-advisory-closeout.md`: treat planner quorum as advisory, inspect reviewer `evidence_requests`, fulfill them with deterministic gates (tests/compile/no-writeback/no-secret/scoped git diff), and report `weak_consensus / not fully ratified` rather than rerunning expensive discussion by default. If you create guard tests for no-writeback/no-secret scans, avoid embedding the forbidden strings literally in the test source or later grep-based gates will self-match; construct those strings dynamically.

For autonomous loop work where the user wants every iteration checked by multiple models until they agree to stop, use the loop-runner pattern in `references/local-brain-taskpool-autorun-certification.md`: deterministic gates first, claim/evidence state second, live `consult_models.py --tier T3 --quorum 4 --discussion --keep` third, then an explicit `verify_ratification()` / `should_continue()` API that converts `discussion_result.json` into `LOOP_DONE` or `continue_loop`. If the request is to check taskpool progress or assess long-running self-run readiness, first use `references/taskpool-autorun-status-review-and-certification.md`: collect the read-only status suite, prove work-lane preemption with `parallel-dispatch-dry-run`, and package claim-linked evidence before T3. Do not pass only a raw `/tmp/status.json` via `--file` and expect truth certification; unlinked files commonly produce `truth_status=unsupported` / `evidence_coverage=0.0` and must be reported as advisory/not-certified. If the first live quorum flags ambiguity in the stop gate, patch the verifier API and rerun; do not claim completion from deterministic gates alone. If later live rounds fail because no-action advisory follow-ups are misclassified as implementation blockers, because an outer consult timeout raises a traceback, or because `consult_result.discussion_result_path` is missing/empty (`Path("")` becomes `.`), harden the merge/verifier path with regression tests and preserve `not_certified`/timeout/missing-discussion as structured fail-closed artifacts.

Local task-pool scheduling pitfall: recording a blocker or `returned_for_backend_completion` in a project Workpad/docs is evidence, not an executable queue item. Before telling the user a returned task will be modified automatically, verify it is a canonical task note under `~/Documents/brain/05-实践与项目/tasks` and appears in `brain_task_orchestrator.py dispatch-dry-run --json` / `taskpool_watch_report.py`; otherwise say it will not auto-run yet and either add a prioritized task via `brain_task_orchestrator.py add ...` or start the implementation immediately. Also report the relevant cron jobs (`local-brain-taskpool-auto-completer`, occasional report) with `next_run_at` so “什么时候会修改” is grounded in scheduler state, not assumptions.

Task-pool architecture-gate pitfall: when adding a new fail-closed metadata contract such as `lane: evolution` requiring `architecture_target` / `capability_delta` / `anti_drift_check` / `acceptance_evidence`, do not stop at temp-vault unit tests. Run the real canonical vault selfcheck/lifecycle with `HERMES_BRAIN_VAULT=/Users/charles/Documents/brain`; legacy Markdown tasks may immediately become invalid. Either provide a migration/repair command or patch the affected canonical task notes with truthful alignment fields, then rerun `selfcheck --json` and `lifecycle --json`. Treat `dispatch-dry-run` PASS alone as insufficient because it can skip misaligned historical tasks while `selfcheck` correctly fails.

Ratification verifiers must validate participant identity, not just counts. For full T3/four-brain certification, require the exact planned canonical participant IDs (for this Hermes stack: `claude-opus-4-7`, `gpt-5.5`, `deepseek-v4-pro`, `mimo-v2.5-pro`) unless a different expected set is explicitly configured in the state; family/role aliases such as `claude`, `codex`, `deepseek`, `mimo`, provider substrings, or same-family shadow names are not enough at the certification boundary. Approval votes must come from the exact consulted canonical IDs, every expected participant must either approve or be represented by an explicit fail-closed missing-vote reason, duplicate approval identities must block certification, and fake/unconsulted voters must not satisfy quorum. Do not derive quorum solely from self-attested `models_consulted`; missing the planned fourth model must fail closed rather than silently lowering the approval requirement. Truth gates must require explicit positive evidence fields: `can_certify_truth`/equivalent must be true, and negative-evidence arrays such as `unsupported_high_severity_claim_ids` and `contradicted_high_severity_claim_ids` must be present and well-typed; missing arrays are malformed evidence, not empty evidence. For PUA-loop/taskpool closeout gates, status/votes/truth shells are still insufficient: require explicit `criteria_satisfied` (accuracy, long-term goal, one-shot landing) or equivalent `final_design` proof, including a non-empty next slice, acceptance evidence, rollback boundary, and long-term goal alignment. If these fields are missing, return `continue_loop`; do not let a `certified` label stop the loop.

For router/readiness certification in autonomous or budget-handoff paths, treat monitor availability and semantic gate fields as first-class evidence. Readiness is not fail-closed if it only checks `dominance_warning`; it must also fail on monitor returncode != 0, empty/invalid JSON, missing required fields, `gate_failed`, warning counts, and route-diversity signals. Preserve parseable non-zero monitor output as actionable gate evidence instead of collapsing it to `*_unavailable`; only malformed/missing required fields should become unavailable. Accept documented JSON shape drift deliberately (for example `route_diversity_signals` may be an empty list or a keyed dict) and add a named regression for the observed shape. Reporting eligible alternates is advisory only: certification artifacts should explicitly prove no automatic rebalance or route mutation occurred.

For provider quota observability, exact evidence must not be downgraded by later empty response headers. Use `references/provider-quota-observability-and-rebalance.md`: preserve fresh higher-confidence balance/window evidence against lower-confidence unknown/header-empty snapshots, still let 429/rate-limit/exhausted safety blockers overwrite OK evidence, make refresh actions actionable rather than stale, and use bounded real smoke/warm-up calls (not synthetic traces) to resolve diversity dominance before re-running router/autonomy gates.

- `references/autonomous-certification-scope-and-provider-evidence.md` — certification must be scoped to explicit provider set/mode/write surfaces/budget/revocation conditions, quota-unobservable providers cannot participate in clean budget-handoff/autonomous-execution certification, and deterministic gate passes do not override reject votes or unresolved severity>=3 ratification risks. Prefer a provider-limited certification claim over globally certifying Hermes when Claude/Codex/MiMo quota evidence is unavailable; otherwise label the result as risk-accepted limited autonomy or truth-grounded advisory.
- `references/multi-model-root-cause-analysis.md` — **Root cause diagnosis with 6 theoretical frameworks**: Kahneman (System 1/2), Meadows (leverage points), Ousterhout (tactical/strategic), Pragmatic Programmer (DRY), Fowler (code smells), Evans (ubiquitous language). Use when user asks "why did the agent miss this?" or after a returned-for-improvement task.

Router quota/readiness success payloads must use a strict positive schema, not truthiness or defaulted success shells. A payload such as `{"ok": true}` is incomplete evidence and must fail closed. Require explicit `ok is True`, `status in {PASS, OK}`, `failure_count == 0` as a real non-bool int, and `failures == []` as an explicit list; do not default missing `status`, `failure_count`, or `failures` to passing values. For autonomy/budget-handoff readiness, also bind the artifact to the caller's expected threshold: `quota.min_confidence` must be present, finite, in range, and `>= expected_min_confidence`; per-model `passes`, `snapshots`, and `observability_evidence.by_model` must cover exactly the checked model set and include explicit model/status/confidence/timestamp evidence. Reject aggregate-only observability counts, hollow snapshots, missing confidence defaults, or self-declared `min_confidence: 0.0` shells even when `ok=true`. When tightening this gate, update old happy-path fixtures to include the full strict schema rather than weakening the verifier.

For long PUA-loop certification/fusion sessions, do the scoped commit as soon as deterministic gates pass and the evidence note is updated; do not leave commit until after extra exploratory checks if the tool/context budget is near exhaustion. Before committing inside a dirty Hermes repo, run `git diff --cached --stat` and `git status --short -- <task paths>`, `git restore --staged .` if unrelated paths are staged, then re-add only scoped task files. Immediately after commit, run `git log -1 --oneline` plus `git status --short -- <task paths>`; if any task path is still dirty because late fixes/tests landed after the commit, stage only those paths and `git commit --amend --no-edit`, then re-check. Delete or ignore transient runtime artifacts (for example synthetic selfcheck JSON under `~/.hermes/state/`) before declaring the scoped commit clean. If the task also changes `~/.hermes/hermes-agent` and the outer `~/.hermes` repo tracks it as a submodule, commit inside `hermes-agent` first, then stage/commit the outer submodule pointer separately after checking `git diff --submodule -- hermes-agent`; do not accidentally bundle the entire upstream sync history as if it were the scoped patch. If interrupted before commit or before this post-commit clean check, final output must say commit is not done/clean and list exact scoped paths plus next commands; never imply landed/local committed from tests alone.

For Hermes post-update fusion reviews (e.g. new v0.13 surfaces need integration with existing L0-L5+LX/local-brain/taskpool architecture), use `references/post-update-fusion-verifier-gates.md`: collect claim-linked update/health/provider evidence, fix verifier gaps such as p10-health self-test parser drift and model-diversity dominance false-health labels, map new upstream surfaces onto existing mechanisms instead of duplicating them, and keep the outcome as `truth_grounded_advisory` / `not_certified_for_autonomous_execution` until router diversity enforcement, provider/quota confidence, and autonomy precondition gates are actually fail-closed. When the fusion touches autonomy/write surfaces, also use `references/autonomy-write-guard-caller-integration.md`: prove the real caller invokes `guard_or_raise` before mutation, keep `dispatch-hint` bounded to claim+handoff+proof, and require surface allowlist even in dispatch-hint mode.

When repeated timeouts or recurring governance needs make this a long-term infrastructure project, use `references/resumable-multimodel-certification-system.md`: treat the target as RMCS (checkpoint → audit-certification → resume-discussion → background runner → evidence-first split), not as a one-off timeout increase. Defer dependent high-risk hook/state automation such as `TaskCreate -> next-round ralph` until RMCS P0-P2 pass.

注意：
- `~/.hermes/config/quorum.yaml` 的 T2/T3 虽列出 4 个 planners，但默认 quorum=3 会截断为 3 个模型；完整四模型必须 `--quorum 4`。
- 第三方框架/仓库评估可用多视角 delegate reviewers 作为轻量“多脑”替代，但最终必须标注为 multi-view review，而不是完整 `consult_models.py --discussion` certification；若用户要求真正四模型认证，仍需运行 `consult_models.py` 并保留 artifact。
- 从 Ruflo/外部编排框架评估中采纳治理原语时，优先 Hermes-native 小切片落地，不整体引入第三方运行时。P0 长期进化控制面是 `~/.hermes/scripts/long_evolution_guard.py`：
  - `inventory` / `witness` / `verify`：生成 capability inventory、本地 HMAC witness、检测 tool/skill/script 漂移。
  - `claim` / `claim-status` / `release` / `handoff` / `steal` / `ledger-verify`：给 cron、subagent、多模型任务建立 claim/lease/handoff ledger，使用 SQLite `BEGIN IMMEDIATE` 做本地互斥，并用 event hash chain 做篡改检测。
  - `budget-check`：对递归委派、多模型 fanout、agent 调 agent 强制 max_hops/max_tokens/max_usd/max_tool_calls/max_wall_seconds；缺失/NaN/负数/超限都 fail-loud。
  - `verify` 必须重建当前 inventory，检测 `inventory_drift` / `added_capability` / `hash_mismatch`，避免 witness 只检查旧清单。
  - 运行模式必须 local-first、no network、禁止 shell 模式执行；仅允许 bounded `git rev-parse HEAD` 作为 provenance；witness key 是本地 runtime secret，不提交 git。
- Claude Code 需要完整能力时优先 `claude -p`；Hermes Anthropic adapter 是 fallback。
- Codex/gpt-5.5 走 openai-codex provider。
- MiMo 走 xiaomi provider。
- Hermes CLI 当前不接受 `--provider deepseek` 时，`consult_models.py` 对 `provider: deepseek` 使用 DeepSeek direct API fallback。
- 所有跨模型上下文必须 structured summary relay；不要假设 provider 共享上下文。
- Claude budget 是硬约束；预算不足时可降级，但必须在 final output 写明缺席模型，不能声称完整四模型认证。
- `delegate_task`/子代理审查可以作为补充 reviewer，但不是完整 `consult_models.py --discussion` 的替代品；如果任何 reviewer 超时、被截断或未完成，最终状态必须降级为 `certified_with_minor_risks` 或 `not_certified`，并在 provenance 中写明缺席/超时模型和由主编排器补充的证据。
- 对本地任务池/cron/autorun 这类状态机自动化，区分“事实诊断已 grounded”和“实现方案已 certified”：truth gate 证明缺口存在，不等于 patch plan 可以落地。若 `discussion_result` 里 severity>=3 issue 未解决、`final_design.patches=[]` 但 planner patch summary 显示 `implementation_required`，最终保持 `not_certified` 或 `amend`。尤其不要把“自动执行 Markdown task body 并自动 done”当成认证方案；正确方向是 fail-closed 的 `auto-claim-and-handoff` + 外部 bounded runner + proof-gated `review -> done`。具体实现/验收模式见 `references/local-brain-taskpool-autorun-certification.md`：默认关闭、allowlist 默认拒绝、safe tick 默认 hint-only、autorun done 必须 proof hash-chain、`proof-check` 要审计 persisted autorun closure、提交时必须 scoped add 避免带入 Hermes runtime 脏文件。
