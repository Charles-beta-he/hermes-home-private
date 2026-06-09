---
type: task
lane: evolution
layer: L3
status: done
priority: P1
priority_layer: P1
dependency_order: ["after:P1-A-self-proving-executor;before:RAG-heavy-multimodal-deps;parallel_with:OpenHands-execution-gap-mapping"]
created: 2026-05-19T14:11:08+08:00
updated: 2026-05-19T21:28:39+08:00
expires_at: 2026-06-18T14:11:08+08:00
project: hermes-agent
architecture_target: local-brain
capability_delta: 吸收RAG-Anything的多模态文档解析/内容分解/知识图谱/模态感知检索思想，先落地Hermes taskpool proof/markdown证据的typed manifest与安全检索，强化自证闭环和历史证据召回。
anti_drift_check: 不安装MinerU/OCR/VLM等重依赖到Hermes core；不外发本地私密图片/PDF；先用stdlib索引proof JSON和markdown；所有内容必须保留source_path/hash/redaction_status，检索不得覆盖任务池政策。
acceptance_evidence: 1) live repo inspection evidence; 2) gap analysis doc docs/private/rag-anything-hermes-gap-analysis.md; 3) deterministic evidence_manifest prototype; 4) empty corpus/proof_json/task_markdown/secret-redaction tests; 5) selfcheck/proof-check/tick PASS
workflow_contract: ["[08-模板/task-workflow-contract-template]"]
requires_multimodel: true
multimodel_reason: 需要多模型确认RAG-Anything模式吸收边界、隐私/重依赖红线、以及P1最小切片是否足以强化Hermes自身
expected_participants: ["claude-opus-4-7", "gpt-5.5", "deepseek-v4-pro", "mimo-v2.5-pro"]
truth_gate: evidence_manifest_prototype_then_multimodal_deps_deferred
evidence_bundle: source:https://github.com/HKUDS/RAG-Anything;inspection:README+top-level+docs+modules+tests;repo_stats:stars=20362,forks=2347,language=Python,license=MIT;analysis:/Users/charles/.hermes/hermes-agent/docs/private/rag-anything-hermes-gap-analysis.md
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_triage_result: "P1 evolution: directly strengthens evidence-first taskpool and anti-false-completion; heavy multimodal components deferred behind safety gates"
multimodel_status: certified
multimodel_ratification_artifact: /Users/charles/.hermes/tick-20260519-132205-377036-p27487-e7552b3c-6268c455/discussion_result.json
multimodel_last_checked_at: 2026-05-19T21:28:39+08:00
multimodel_round_status: passed
multimodel_last_gate_status: PASS
multimodel_last_decision: LOOP_DONE
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260519-132205-377036-p27487-e7552b3c-6268c455/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-19-p1-rag-anything式多模态证据索引taskpool-proof-markdown-typed-manifest-与安全检索-state.json
multimodel_last_failures: []
multimodel_failure_taxonomy: ["no_claims"]
multimodel_recommended_axes: ["quota_observability", "framing"]
multimodel_axis_rationale: "{'quota_observability': ['no_claims'], 'framing': ['no_claims']}"
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: 只做Hermes本地证据manifest与词法检索原型；不clone全仓、不接入外部VLM、不处理用户私密文件、不改变现有taskpool lifecycle gate。
evidence:
  - "command: multimodel-intervention-step gate=PASS decision=LOOP_DONE artifact=/Users/charles/.hermes/tick-20260519-132205-377036-p27487-e7552b3c-6268c455/discussion_result.json"
  - proof:sha256:0dae65ea81eb9f4f24beeca8ce5cdc82cade248533e5a49a30e4a8c3861cc824
  - artifact:ratification multimodel certified /Users/charles/.hermes/tick-20260519-132205-377036-p27487-e7552b3c-6268c455/discussion_result.json
concepts: ["RAG-Anything", "multimodal-rag", "evidence-spine", "typed-content-blocks", "LightRAG", "document-parsing", "modal-processors", "proof-json", "secret-redaction", "taskpool-recall"]
multimodel_advisory_only: False
multimodel_certification_authority: True
multimodel_advisory_reasons: ["architecture_target", "closeout_ratification", "evidence_bundle_contract", "evolution_lane", "expected_participants_contract", "explicit_multimodel_reason", "truth_gate_contract"]
multimodel_certification_reasons: ["explicit_requires_multimodel"]
---

# Task - P1 RAG-Anything式多模态证据索引：taskpool proof markdown typed manifest 与安全检索

## Objective

把RAG-Anything的all-in-one multimodal RAG能力转译为Hermes本地脑的证据索引与安全召回层，用于减少假完成、重复诊断和证据丢失。

## Acceptance Criteria

- [x] Observable source-intake result is recorded in Proof Log.
- [x] RAG-Anything → Hermes gap analysis document is created.
- [ ] Deterministic `evidence_manifest.py` prototype exists with no heavyweight multimodal dependencies.
- [ ] Empty corpus / proof JSON / task markdown / secret-redaction tests pass.
- [ ] selfcheck / proof-check / dispatch tick remain PASS after prototype.

## Plan / Workpad

- [x] Reconcile current state, dependency order, and architecture boundaries before execution.
- [x] Inspect live source before taskpool intake.
- [x] Land gap analysis and classified P1 task metadata.
- [ ] Implement stdlib-first typed evidence manifest prototype.
- [ ] Record proof, status, and any next dependency or handoff required.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| GitHub API repo inspection | PASS | HKUDS/RAG-Anything exists; stars=20362, forks=2347, language=Python, license=MIT, default_branch=main |
| Top-level contents inspection | PASS | `raganything/`, `docs/`, `examples/`, `tests/`, `requirements.txt`, `pyproject.toml`, `env.example`, `README_zh.md` |
| README architecture inspection | PASS | all-in-one multimodal RAG; document parsing; content analysis; multimodal KG; modality-aware retrieval; LightRAG base |
| Docs/modules/tests inspection | PASS | docs include context-aware processing/failure modes/offline/vLLM; modules include parser/processor/modalprocessors/query/resilience; tests include parser wiring/resilience/callbacks/LightRAG API |
| Gap analysis document | PASS | `/Users/charles/.hermes/hermes-agent/docs/private/rag-anything-hermes-gap-analysis.md` |
| `brain_task_orchestrator.py add ... --json` | PASS | `/tmp/rag-anything-task-add.json` |

## Proof Log

- 2026-05-19T14:11:08+08:00: Task created from local-brain control point.
- 2026-05-19T14:12:00+08:00: Live source intake completed for `https://github.com/HKUDS/RAG-Anything`: repo exists, Python, MIT, stars=20362, forks=2347, default branch main.
- 2026-05-19T14:12:00+08:00: Architecture signals captured: all-in-one multimodal RAG, LightRAG base, document parsing, content decomposition, modal processors, multimodal knowledge graph, modality-aware retrieval, direct content-list insertion.
- 2026-05-19T14:12:00+08:00: Gap analysis landed at `/Users/charles/.hermes/hermes-agent/docs/private/rag-anything-hermes-gap-analysis.md`; recommended first slice is stdlib typed evidence manifest over proof JSON + markdown, with heavy OCR/VLM dependencies deferred.
- 2026-05-19T14:12:00+08:00: Task classified as P1/evolution/local-brain with requires_multimodel=true; no clone/install/external VLM/private file processing performed.

## Blockers / Confusions

- None for intake/gap analysis. Implementation requires prototype + tests and multimodel confirmation before any heavyweight multimodal dependencies.

## Final Handoff

- Status: Intake and self-strengthening analysis complete; pending deterministic `evidence_manifest.py` prototype.
- Evidence: `/tmp/rag-anything-task-add.json`, `/Users/charles/.hermes/hermes-agent/docs/private/rag-anything-hermes-gap-analysis.md`, plan entry in `/Users/charles/.hermes/hermes-agent/docs/private/autonomous-workflow-execution-plan.md`.
- Residual risk: README/docs/module listing is sufficient for intake and gap mapping, but implementation should inspect target Hermes evidence-spine/taskpool code before writing prototype.

- 2026-05-19T21:22:04+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

- 2026-05-19T21:22:04+08:00: Lifecycle transition `claimed` -> `running` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_external_process_started

- 2026-05-19T21:28:39+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260519-132205-377036-p27487-e7552b3c-6268c455/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-19T21:28:39+08:00: Lifecycle transition `running` -> `review` by `hermes-multimodel`. Evidence: command: multimodel-intervention-step gate=PASS decision=LOOP_DONE artifact=/Users/charles/.hermes/tick-20260519-132205-377036-p27487-e7552b3c-6268c455/discussion_result.json

- 2026-05-19T21:28:39+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:0dae65ea81eb9f4f24beeca8ce5cdc82cade248533e5a49a30e4a8c3861cc824, command: multimodel-intervention-step gate=PASS decision=LOOP_DONE artifact=/Users/charles/.hermes/tick-20260519-132205-377036-p27487-e7552b3c-6268c455/discussion_result.json, artifact:ratification multimodel certified /Users/charles/.hermes/tick-20260519-132205-377036-p27487-e7552b3c-6268c455/discussion_result.json
