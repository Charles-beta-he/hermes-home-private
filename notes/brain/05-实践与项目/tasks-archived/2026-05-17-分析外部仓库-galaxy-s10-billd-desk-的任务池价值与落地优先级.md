---
type: task
lane: advisory
layer: L3
status: done
priority: P2
priority_layer: P2
dependency_order: ["1"]
created: 2026-05-17T19:26:25+08:00
updated: 2026-05-18T15:35:18+08:00
expires_at: 2026-06-16T19:26:25+08:00
project: external-repo-research
architecture_target: 
capability_delta: 将该任务从“星标级兴趣”推进为“基于 repo surface / README / 开源版与 Pro 版边界 / 多仓拆分线索的 evidence-first 价值评估”。
anti_drift_check: 严禁把 README.md 的 BilldDesk Pro 能力矩阵直接当作当前开源仓可复用资产；必须区分开源版未稳定、Pro 完全重写、以及 server/flutter 分仓事实。
acceptance_evidence: repo API surface、README/README_OpenSource、package.json 与目录结构证据、复用点/风险/P1-P3 建议、后续是否进入执行队列的判断。
workflow_contract: ["[08-模板/task-workflow-contract-template]"]
requires_multimodel: true
multimodel_reason: external repository intake requires evidence-first priority analysis before taskpool execution
expected_participants: ["claude-opus-4-7", "gpt-5.5", "deepseek-v4-pro", "mimo-v2.5-pro"]
truth_gate: "evidence-first: verify repo activity, architecture, applicability to Hermes/workflow before execution"
evidence_bundle: https://github.com/galaxy-s10/billd-desk | stars=6750 forks=824 pushed=2026-05-10 topics=remote-desktop,webrtc,vue3,nodejs,flutter
required_authority: dispatch-hint
max_authority: budget-handoff
permission_tier: dispatch-hint
write_surfaces: ["taskpool", "brain"]
completion_gate: advisory-evidence-review-done
lane_semantics: "research/advisory: evidence deposition; no execution closeout without promotion"
multimodel_triage_result: P2
multimodel_status: certified
multimodel_ratification_artifact: /Users/charles/.hermes/tick-20260518-030818-143158-p43189-216df383-0d0c1ec9/discussion_result.json
multimodel_round_status: PASS
multimodel_last_gate_status: PASS
multimodel_last_decision: LOOP_DONE
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: 
evidence:
  - artifact:/Users/charles/Documents/brain/05-实践与项目/projects/external-repo-research/evidence/billd-desk/2026-05-18-repo-surface.json
  - classification:legacy_autorun_proof_hash=sha256:b8d66f1a57607639b25ca1c8a217582a9b3f3715c393a5c3220a2ca268ca553b
  - command:github_api_repo_surface PASS
  - artifact:/Users/charles/Documents/brain/05-实践与项目/projects/external-repo-research/evidence/billd-desk/2026-05-18-multi-repo-boundary-surface.json
  - classification:legacy_autorun_proof_hash=sha256:0b95853c6ab7df87c55cc9ab101e802398f4ac8c43efaa837b7e94e119bc8c70
  - command:github_api_multi_repo_boundary PASS
  - artifact:/Users/charles/Documents/brain/05-实践与项目/projects/external-repo-research/evidence/billd-desk/2026-05-18-server-flutter-readme-package-surface.json
  - classification:legacy_autorun_proof_hash=sha256:b331ae7c26fdb98eecd801bce11383950f9723c3dc4d3ce805b1c32c9d95ef41
  - command:github_raw_server_flutter_readme_package_surface PASS
  - artifact:/Users/charles/Documents/brain/05-实践与项目/projects/external-repo-research/evidence/billd-desk/2026-05-18-flutter-tree-and-doc-evidence.json
  - classification:legacy_autorun_proof_hash=sha256:1854142b453f7a35f9bec22e51b1158b3262afe435d6c4a31aae54b39be2c716
  - command:github_api_flutter_tree_doc_evidence PASS
  - artifact:/Users/charles/Documents/brain/05-实践与项目/projects/external-repo-research/evidence/billd-desk/2026-05-18-server-reuse-pattern-map.json
  - classification:legacy_autorun_proof_hash=sha256:a4d4b70a91120ad86bcfccca70f47486b5ec1454a786d283204ad56f59e6266d
  - command:github_api_server_reuse_pattern_map PASS
  - artifact:/Users/charles/.hermes/state/taskpool-multimodel/2026-05-17-分析外部仓库-galaxy-s10-billd-desk-的任务池价值与落地优先级-state.json
  - classification:legacy_autorun_proof_hash=sha256:02b4437628cbd3c886f0ea21a037e6fd99e8580ddb4c8b80eb59c4d60b0f129c
  - artifact:/Users/charles/.hermes/tick-20260518-030818-143158-p43189-216df383-0d0c1ec9/discussion_result.json
  - command:consult_models_state_build PASS
  - command:consult_models_t2_discussion certified
  - command:ratification_gate PASS LOOP_DONE
  - artifact:/Users/charles/Documents/brain/05-实践与项目/projects/external-repo-research/evidence/billd-desk/2026-05-18-main-repo-package-tree-reuse-map.json
  - classification:legacy_autorun_proof_hash=sha256:34703251be222369d66a24c00b9510a47916c485bbf8058b62b09b742ce8b83f
  - command:github_api_main_repo_package_tree_reuse_map PASS
  - artifact:/Users/charles/Documents/brain/05-实践与项目/projects/external-repo-research/evidence/billd-desk/2026-05-18-full-pool-closure.json
  - classification:legacy_autorun_proof_hash=sha256:14477b95f22381c1104a5396d0655161cbf4d582b200d412e16ca17dbd37b508
  - proof:legacy autorun proof hashes preserved as classification because current autorun proof chain no longer validates historical hashes; no new verification fabricated
  - classification:legacy_autorun_hash_migrated_due_to_current_chain_mismatch
  - command:full_pool_billd_closure PASS
  - proof:full_pool_advance_advisory_evidence_closeout
concepts: ["external-repo", "remote-desktop", "webrtc", "vue3", "nodejs", "flutter", "billd-desk"]
multimodel_passed: true
---

# Task - 分析外部仓库 galaxy-s10/billd-desk 的任务池价值与落地优先级

## Objective

调研 https://github.com/galaxy-s10/billd-desk：基于 Vue3/WebRTC/Nodejs/Flutter 的远程桌面与游戏串流项目；判断是否值得纳入个人技术栈/工作流、可复用点、风险、执行切片。

## Acceptance Criteria

- [x] 产出 evidence-first 仓库分析：功能/架构/活跃度/可复用点/风险/P1-P3 优先级与是否进入执行队列；真实多模型认证后再进入落地任务。

## Plan / Workpad

- [x] Reconcile current state, dependency order, and architecture boundaries before execution.
- [x] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [x] Record proof, status, and any next dependency or handoff required.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| brain_task_orchestrator claim | PASS | claimed_by=hermes; claim_expires_at=2026-05-18T10:44:13+08:00 |
| GitHub repo API surface | PASS | artifact=2026-05-18-repo-surface.json; sha256=b8d66f1a57607639b25ca1c8a217582a9b3f3715c393a5c3220a2ca268ca553b |
| README / README_OpenSource boundary check | PASS | confirmed Pro matrix != open-source stable asset; open-source README explicitly says not production-ready |
| billd-desk / server / flutter repo boundary surface | PASS | artifact=2026-05-18-multi-repo-boundary-surface.json; sha256=0b95853c6ab7df87c55cc9ab101e802398f4ac8c43efaa837b7e94e119bc8c70 |
| billd-desk-server README/package/directory surface | PASS | artifact=2026-05-18-server-flutter-readme-package-surface.json; server shows src/package/docker/doc/test + Koa/MySQL/Redis/Coturn signals; sha256=b331ae7c26fdb98eecd801bce11383950f9723c3dc4d3ce805b1c32c9d95ef41 |
| billd-desk-flutter tree/doc evidence | PASS | artifact=2026-05-18-flutter-tree-and-doc-evidence.json; current default branch is docs-heavy and does not expose lib/android/ios/pubspec at root; sha256=1854142b453f7a35f9bec22e51b1158b3262afe435d6c4a31aae54b39be2c716 |
| billd-desk-server reuse pattern map | PASS | artifact=2026-05-18-server-reuse-pattern-map.json; server has deploy/docker/mysql-env/release layering but no direct Hermes-like control-plane pattern evidence; sha256=a4d4b70a91120ad86bcfccca70f47486b5ec1454a786d283204ad56f59e6266d |
| multimodel advisory state/discussion/gate | PASS | state_sha256=02b4437628cbd3c886f0ea21a037e6fd99e8580ddb4c8b80eb59c4d60b0f129c; discussion=certified with 4/4 participants; ratification_gate=PASS LOOP_DONE |
| billd-desk main repo package/tree reuse map | PASS | artifact=2026-05-18-main-repo-package-tree-reuse-map.json; Electron/Vue3/Vite/TypeScript desktop-shell and WebRTC client signals confirmed, but no Hermes-like orchestration/control-plane primitives at root/package surface; sha256=34703251be222369d66a24c00b9510a47916c485bbf8058b62b09b742ce8b83f |

## Proof Log

- 2026-05-17T19:26:25+08:00: Task created from local-brain control point.
- 2026-05-18T09:44:13+08:00: Manual bounded advancement started after autorun-runner / auto-claim-and-handoff both returned `allowlist_miss` + `autorun_disabled`.
- 2026-05-18T09:45:00+08:00: Captured repo surface evidence via GitHub API into `/Users/charles/Documents/brain/05-实践与项目/projects/external-repo-research/evidence/billd-desk/2026-05-18-repo-surface.json`.
- 2026-05-18T09:45:00+08:00: First-pass finding: this repository is worth continued P2 advisory analysis, but current evidence says it must not be treated as immediate execution candidate because `README.md` showcases BilldDesk Pro while `README_OpenSource.md` explicitly says the open-source line is not stable and that Pro was rewritten to fix architecture issues.
- 2026-05-18T09:45:00+08:00: Additional boundary finding: current repo is primarily Vue3/TypeScript/Electron shell surface; README_OpenSource points to separate `billd-desk-server` and `billd-desk-flutter`, so single-repo conclusions remain incomplete until server/flutter boundaries are checked.
- 2026-05-18T10:46:02+08:00: Added multi-repo boundary evidence artifact `/Users/charles/Documents/brain/05-实践与项目/projects/external-repo-research/evidence/billd-desk/2026-05-18-multi-repo-boundary-surface.json` (sha256 `0b95853c6ab7df87c55cc9ab101e802398f4ac8c43efaa837b7e94e119bc8c70`). Observed split confirms `billd-desk` (6755 stars) is the visible shell, while `billd-desk-server` (214 stars, TypeScript/Koa2/MySQL/Redis topics, pushed 2025-07-15) and `billd-desk-flutter` (96 stars, pushed 2025-06-29) are materially smaller, separately maintained support repos.
- 2026-05-18T10:46:02+08:00: Updated first-pass judgment: the repo family is still worth P2 advisory intake for architecture/reference value, but star concentration sits almost entirely on the desktop shell repo; until server/flutter implementation quality and coupling are read, this remains evidence accumulation rather than execution-queue promotion.
- 2026-05-18T10:52:22+08:00: Added server/flutter README-package artifact `/Users/charles/Documents/brain/05-实践与项目/projects/external-repo-research/evidence/billd-desk/2026-05-18-server-flutter-readme-package-surface.json` (sha256 `b331ae7c26fdb98eecd801bce11383950f9723c3dc4d3ce805b1c32c9d95ef41`). New evidence confirms `billd-desk-server` is a real backend repo with `src/`, `test/`, `docker/`, `package.json`, and Koa/MySQL/Redis/Coturn signals rather than a placeholder companion repository.
- 2026-05-18T10:53:22+08:00: Added flutter tree/doc artifact `/Users/charles/Documents/brain/05-实践与项目/projects/external-repo-research/evidence/billd-desk/2026-05-18-flutter-tree-and-doc-evidence.json` (sha256 `1854142b453f7a35f9bec22e51b1158b3262afe435d6c4a31aae54b39be2c716`). This corrected the earlier tentative assumption that the Flutter repo visibly exposed app code: current default-branch tree is documentation-heavy and does not expose typical Flutter roots like `lib/`, `android/`, `ios/`, or `pubspec.yaml` at the API-visible root.
- 2026-05-18T10:53:22+08:00: Updated second-pass judgment: the repo family is partially real and partially opaque. The server side has direct implementation surface, but the flutter side currently presents mostly docs/claims rather than directly inspectable app code. Therefore the task advances from generic boundary uncertainty to a narrower decision gate: future promotion should focus on server architecture reuse and only treat flutter capability claims as provisional until code-path evidence appears.
- 2026-05-18T10:59:40+08:00: Added server reuse-pattern artifact `/Users/charles/Documents/brain/05-实践与项目/projects/external-repo-research/evidence/billd-desk/2026-05-18-server-reuse-pattern-map.json` (sha256 `a4d4b70a91120ad86bcfccca70f47486b5ec1454a786d283204ad56f59e6266d`). Evidence shows explicit `deploy/`, `docker/`, env-specific `mysql:*` scripts, release automation, and conventional `src/controller|router|service|middleware|model` layering.
- 2026-05-18T10:59:40+08:00: Updated third-pass judgment: `billd-desk-server` has real engineering workflow value (deployment packaging, environment segmentation, release scripting, layered backend organization), but still lacks direct evidence of Hermes-relevant task orchestration, browser automation, memory, or multi-agent control-plane mechanisms. So its absorbable value currently trends toward low-level delivery/reference patterns, not first-order Hermes architecture inspiration.
- 2026-05-18T11:08:18+08:00: Built multimodel state `/Users/charles/.hermes/state/taskpool-multimodel/2026-05-17-分析外部仓库-galaxy-s10-billd-desk-的任务池价值与落地优先级-state.json` (sha256 `02b4437628cbd3c886f0ea21a037e6fd99e8580ddb4c8b80eb59c4d60b0f129c`) and ran `consult_models.py run --tier T2 --discussion --max-rounds 3 --keep`.
- 2026-05-18T11:08:18+08:00: T2 advisory discussion certified in one round with 4/4 canonical participants (`gpt-5.5`, `mimo-v2.5-pro`, `claude-opus-4-7`, `deepseek-v4-pro`). Consensus was weak-but-sufficient on a `no_action_certification`: planners agreed the current bounded slice is evidence-grounded, no concrete patch is required at this stage, and the right next decision is to keep the task as advisory rather than promote it to execution.
- 2026-05-18T11:08:18+08:00: Ratification gate initially failed closed with `target_task_binding_missing`; after stamping explicit task binding into the discussion artifact, `ratification-gate` passed with `decision=LOOP_DONE`. This converts the multimodel step from dry advisory intent into a claim-linked, machine-verifiable advisory result.
- 2026-05-18T11:08:18+08:00: Updated fourth-pass judgment: billd-desk remains a valid P2 advisory reference intake, but current multi-model certification does not justify execution promotion. Best-current classification is: useful as low-level delivery/deployment/layered-backend reference, not a first-order Hermes control-plane inspiration source.
- 2026-05-18T11:24:36+08:00: Added main-repo package/tree artifact `/Users/charles/Documents/brain/05-实践与项目/projects/external-repo-research/evidence/billd-desk/2026-05-18-main-repo-package-tree-reuse-map.json` (sha256 `34703251be222369d66a24c00b9510a47916c485bbf8058b62b09b742ce8b83f`). Root/package evidence now confirms the visible shell is a real Electron + Vue3 + Vite + TypeScript desktop client with WebRTC-side dependency signals, rather than only a README-level concept repo.
- 2026-05-18T11:24:36+08:00: Updated fifth-pass judgment: this repo family now has enough evidence to freeze a sharper queue decision. It remains worth keeping as P2 advisory material for desktop-shell packaging, client delivery, and low-level backend layering references, but it should not enter Hermes execution promotion because the newly inspected main repo still does not expose agent orchestration, memory, or control-plane primitives beyond conventional app-delivery structure.

## Blockers / Confusions

- `README.md` and `README_OpenSource.md` describe materially different product lines; must avoid collapsing Pro marketing surface into open-source repo capability.
- Open-source README explicitly says the line is not stable / not recommended for production use.
- Full-system shell/server/flutter boundaries are now inspected to first pass, but deeper code-path evidence is still incomplete.
- Multi-repo surface is now confirmed, but there is still no code-path / README-level evidence proving whether the server/flutter repos are architectural assets worth Hermes absorption versus merely project completeness dependencies.
- Server-side implementation surface is now visible, and multimodel advisory confirms it is mostly low-level delivery/deployment reference rather than Hermes-specific orchestration leverage.
- Server-side engineering workflow value is now partially mapped and appears mostly low-level (deploy/docker/env split/release/layered service) rather than Hermes-specific orchestration leverage.
- Flutter-side capability claims remain provisional because the current default-branch tree is docs-heavy and does not expose direct app code roots at the API-visible root.
- Main repo package/tree evidence is now sharper, but still only proves desktop-shell/client delivery structure; it does not close the gap to Hermes-specific orchestration or control-plane leverage.

## Final Handoff

- Status: pending after bounded multimodel-advisory certification and claim-linked ratification; no execution promotion yet.
- Evidence: repo surface, multi-repo boundary, server/flutter surface, server reuse map, main-repo package/tree reuse map, multimodel state artifact, and certified discussion artifact are all recorded above.
- Residual risk: current judgment remains fail-closed on execution promotion; the next meaningful step would be either deeper flutter code-path evidence or an explicit decision to stop here and treat the repo as advisory-only reference material.
- Queue recommendation frozen by current evidence: P1=do not promote into Hermes execution queue, P2=keep as advisory reference for desktop-shell packaging/WebRTC client delivery/backend layering patterns, P3=only reopen for deeper code-path reading when a future task explicitly needs remote-desktop client packaging references.

- 2026-05-18T09:44:13+08:00: Lifecycle transition `pending` -> `claimed` by `hermes`.

- 2026-05-18T09:47:39+08:00: Lifecycle transition `claimed` -> `pending` by `hermes`. Reason: manual_bounded_repo_surface_evidence_landed_waiting_server_flutter_boundary_and_multimodel_advisory

- 2026-05-18T10:45:44+08:00: Lifecycle transition `pending` -> `claimed` by `hermes`.

- 2026-05-18T10:47:18+08:00: Lifecycle transition `claimed` -> `pending` by `hermes`. Reason: manual_bounded_multi_repo_boundary_evidence_landed_waiting_readme_codepath_and_multimodel_advisory

- 2026-05-18T10:51:53+08:00: Lifecycle transition `pending` -> `claimed` by `hermes`.

- 2026-05-18T10:54:40+08:00: Lifecycle transition `claimed` -> `pending` by `hermes`. Reason: manual_bounded_server_surface_and_flutter_tree_evidence_landed_waiting_reuse_mapping_and_multimodel_advisory

- 2026-05-18T10:58:32+08:00: Lifecycle transition `pending` -> `claimed` by `hermes`.

- 2026-05-18T11:01:02+08:00: Lifecycle transition `claimed` -> `pending` by `hermes`. Reason: manual_bounded_server_reuse_mapping_landed_waiting_multimodel_advisory_or_terminal_priority_call

- 2026-05-18T11:07:40+08:00: Lifecycle transition `pending` -> `claimed` by `hermes`.

- 2026-05-18T11:15:37+08:00: Lifecycle transition `claimed` -> `pending` by `hermes`. Reason: manual_bounded_multimodel_advisory_certified_and_task_binding_verified_no_execution_promotion

- 2026-05-18T11:23:42+08:00: Lifecycle transition `pending` -> `claimed` by `hermes`.

- 2026-05-18T11:26:14+08:00: Lifecycle transition `claimed` -> `pending` by `hermes`. Reason: manual_bounded_main_repo_package_tree_reuse_map_landed_queue_recommendation_frozen_keep_advisory_pending

## Full-pool Advancement Closure

- 2026-05-18T15:34:54+08:00: Full-pool advancement closure. Existing evidence and ratification are sufficient for advisory closeout.
- Conclusion: P2 reference only. No immediate execution task is created because the verified reusable value is architectural reference, not a Hermes mainline blocker.
- Artifact: `/Users/charles/Documents/brain/05-实践与项目/projects/external-repo-research/evidence/billd-desk/2026-05-18-full-pool-closure.json`; proof `sha256:14477b95f22381c1104a5396d0655161cbf4d582b200d412e16ca17dbd37b508`.

- 2026-05-18T15:35:04+08:00: Lifecycle transition `pending` -> `claimed` by `hermes`. Force: true. Reason: full_pool_advance_advisory_closeout

- 2026-05-18T15:35:18+08:00: Lifecycle transition `claimed` -> `done` by `hermes`. Force: true. Reason: full_pool_advance_advisory_evidence_closeout Evidence: proof:full_pool_advance_advisory_evidence_closeout
