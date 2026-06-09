---
type: task
lane: evolution
layer: L3
status: done
priority: P2
priority_layer: P2
dependency_order: ["1 inventory/security triage -> 2 migration decision matrix -> 3 skill graph patch/prototype -> 4 deterministic verification -> 5 optional multimodel certification"]
created: 2026-05-21T12:35:40+08:00
updated: 2026-05-21T18:10:52+08:00
expires_at: 2026-06-20T12:35:40+08:00
project: hermes-agent
architecture_target: skill-graph
capability_delta: Hermes gains a compact Karpathy-style coding-agent guardrail layer for assumption surfacing, simplicity, surgical diffs, and goal-driven verification, integrated by patching existing Hermes coding workflow skills instead of duplicating policy.
anti_drift_check: Do not treat the superseded OpenClaw awesome-list artifact as the source; do not overwrite Hermes system/developer policy with third-party CLAUDE.md text; preserve act-don't-ask for obvious defaults and long-term architecture exceptions when broad changes are required.
acceptance_evidence: Correct repo source verified; andrej-karpathy-skills gap analysis exists; migration matrix identifies which existing Hermes coding skills to patch; routing/negative-space evals recorded; any skill patches are read back and verified.
workflow_contract: ["[08-模板/task-workflow-contract-template]"]
requires_multimodel: true
multimodel_reason: Changes Hermes skill routing/local retrieval/privacy boundaries; require external model review before broad rollout
expected_participants: ["claude-opus-4-7", "gpt-5.5", "deepseek-v4-pro"]
truth_gate: source-evidence + security/privacy red-lines + deterministic local-only proof before integration
evidence_bundle: docs/private/andrej-karpathy-skills-gap-analysis.md; /tmp/andrej-karpathy-skills@2c60614; superseded first-pass artifact docs/private/openclaw-garden-skills-gap-analysis.md; future skill-routing evals; selfcheck/proof-check
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_triage_result: "P2: high-leverage local-first skill graph reference; not blocking correctness; requires security/privacy review before any import"
multimodel_status: certified
multimodel_ratification_artifact: /Users/charles/.hermes/tick-20260521-043547-443127-p82877-86e509a4-7dda107a/discussion_result.json
multimodel_last_checked_at: 2026-05-21T12:42:53+08:00
multimodel_round_status: passed
multimodel_last_gate_status: PASS
multimodel_last_decision: LOOP_DONE
multimodel_last_discussion_artifact: /Users/charles/.hermes/tick-20260521-043547-443127-p82877-86e509a4-7dda107a/discussion_result.json
multimodel_last_state_path: /Users/charles/.hermes/state/taskpool-multimodel/2026-05-21-absorb-openclaw-garden-skills-patterns-into-hermes-local-skill-graph-state.json
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
parallel_boundary: "Intake/planning only: no ClawHub install, no external skill execution, no secret indexing, no cloud sync, no modification of user project repos."
evidence:
  - artifact:docs/private/andrej-karpathy-skills-gap-analysis.md
  - artifact:docs/private/openclaw-garden-skills-gap-analysis.md
  - "proof:user correction resolved source: yaochang008 variants returned 404; direct clone of forrestchang/andrej-karpathy-skills succeeded at commit 2c60614; GitHub API canonical surface is multica-ai/andrej-karpathy-skills"
  - "proof:corrected repo files inspected: README.md, CLAUDE.md, EXAMPLES.md, skills/karpathy-guidelines/SKILL.md; OpenClaw awesome-list artifact marked superseded"
  - proof:brain_task_orchestrator selfcheck PASS at 2026-05-21T12:38:02+08:00; proof-check PASS with warnings only
  - "command: multimodel-intervention-step gate=PASS decision=LOOP_DONE artifact=/Users/charles/.hermes/tick-20260521-043547-443127-p82877-86e509a4-7dda107a/discussion_result.json"
  - proof:sha256:160b7b096a278ac7a46923fd041268dfb337e1bb070ea0249a869081d544e0a1
  - artifact:ratification multimodel certified /Users/charles/.hermes/tick-20260521-043547-443127-p82877-86e509a4-7dda107a/discussion_result.json
  - proof:sha256:811120e1eb72391181e0b988e30e3efbdfbf3249a8658f728b2eea3c2a17ae00
  - command:py_compile_taskpool PASS
  - proof:sha256:2ded456ea3d159573649aec6c9eda72098030506404d997af9d16767a16f1d85
concepts: ["andrej-karpathy-skills", "karpathy-guidelines", "coding-agent-guardrails", "simplicity", "surgical-changes", "goal-driven-execution", "skill-graph"]
run_envelope_ref: "/Users/charles/.hermes/state/run_ledger/run_events.jsonl#205"
multimodel_advisory_only: False
multimodel_certification_authority: True
multimodel_advisory_reasons: ["architecture_target", "closeout_ratification", "evidence_bundle_contract", "evolution_lane", "expected_participants_contract", "explicit_multimodel_reason", "truth_gate_contract"]
multimodel_certification_reasons: ["explicit_requires_multimodel"]
---

# Task - Absorb Andrej Karpathy Skills guardrails into Hermes coding skill graph

## Objective

Absorb Andrej Karpathy Skills guardrails into Hermes as a compact coding-agent behavior layer, using existing skill patches and evidence-first routing decisions rather than importing the upstream instructions verbatim.

## Acceptance Criteria

- [x] corrected source inspected and gap-analysis artifact written
- [x] wrong first-pass OpenClaw artifact marked superseded
- [ ] migration matrix completed: patch existing coding workflow skill vs new reference vs reject
- [ ] routing/negative-space evals recorded for ambiguous coding, overengineering risk, broad diff risk, and weak success criteria
- [ ] selected Hermes skill patches/read-backs verified, or explicit no-patch decision recorded

## Plan / Workpad

- [ ] Reconcile current state, dependency order, and architecture boundaries before execution.
- [ ] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [ ] Record proof, status, and any next dependency or handoff required.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| initial wrong-source inspection | SUPERSEDED | `/tmp/awesome-openclaw-skills` at `e9ec040`; retained only as historical first-pass artifact |
| corrected GitHub source search/API | PASS | `yaochang008/*` variants returned 404; `forrestchang/andrej-karpathy-skills` clone succeeded; API canonical surface `multica-ai/andrej-karpathy-skills` |
| corrected repo inspection | PASS | `/tmp/andrej-karpathy-skills` at `2c60614`; README, CLAUDE, EXAMPLES, and `skills/karpathy-guidelines/SKILL.md` inspected |
| corrected gap analysis artifact | PASS | `docs/private/andrej-karpathy-skills-gap-analysis.md` |
| brain_task_orchestrator selfcheck --json | PASS | `status: PASS`; warning only: autorun handoff archival/cleanup |
| brain_task_orchestrator proof-check --json | PASS | `status: PASS`; legacy/missing-section warnings only |

## Proof Log

- 2026-05-21T12:35:40+08:00: Task created from local-brain control point.
- 2026-05-21T12:38:02+08:00: Source inspection completed: cloned `VoltAgent/awesome-openclaw-skills` at `e9ec040`, read README/category surfaces, wrote `docs/private/openclaw-garden-skills-gap-analysis.md`.
- 2026-05-21T12:38:02+08:00: Verification completed: `brain_task_orchestrator.py selfcheck --json` PASS; `proof-check --json` PASS with non-blocking warnings.
- 2026-05-21T12:52:00+08:00: User corrected source. Verified `yaochang008/andrej-karpathy-skills`, `yaochang008/tandrej-karpathy-skills`, and `yaochang008/karpathy-skills` return 404; cloned `forrestchang/andrej-karpathy-skills` at `2c60614`; GitHub API canonical surface resolves as `multica-ai/andrej-karpathy-skills`.
- 2026-05-21T12:52:00+08:00: Wrote corrected artifact `docs/private/andrej-karpathy-skills-gap-analysis.md`; marked `docs/private/openclaw-garden-skills-gap-analysis.md` as superseded.

## Blockers / Confusions

- Previous auto-close used the superseded OpenClaw source artifact. This note has been corrected and should not be treated as fully complete until the migration matrix / skill-patch decision is recorded.

## Final Handoff

- Status:
- Evidence:
- Residual risk:

- 2026-05-21T12:35:47+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_inflight_claim

- 2026-05-21T12:35:47+08:00: Lifecycle transition `claimed` -> `running` by `hermes-multimodel`. Force: true. Reason: multimodel_intervention_external_process_started

- 2026-05-21T12:42:53+08:00: Multimodel PUA-loop round `passed`. Gate `PASS`, decision `LOOP_DONE`. Discussion `/Users/charles/.hermes/tick-20260521-043547-443127-p82877-86e509a4-7dda107a/discussion_result.json`. Failures: []. Recommended axes: ["quota_observability", "framing"]. Axis rationale: {"quota_observability": ["no_claims"], "framing": ["no_claims"]}

- 2026-05-21T12:42:54+08:00: Lifecycle transition `running` -> `review` by `hermes-multimodel`. Evidence: command: multimodel-intervention-step gate=PASS decision=LOOP_DONE artifact=/Users/charles/.hermes/tick-20260521-043547-443127-p82877-86e509a4-7dda107a/discussion_result.json

- 2026-05-21T12:50:28+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:160b7b096a278ac7a46923fd041268dfb337e1bb070ea0249a869081d544e0a1, artifact:docs/private/openclaw-garden-skills-gap-analysis.md, proof:repo cloned at /tmp/awesome-openclaw-skills commit e9ec040; README/categories inspected; candidate clusters inventoried for frontend/video/image/local-kb lanes, proof:brain_task_orchestrator selfcheck PASS at 2026-05-21T12:38:02+08:00; proof-check PASS with warnings only, command: multimodel-intervention-step gate=PASS decision=LOOP_DONE artifact=/Users/charles/.hermes/tick-20260521-043547-443127-p82877-86e509a4-7dda107a/discussion_result.json, artifact:ratification multimodel certified /Users/charles/.hermes/tick-20260521-043547-443127-p82877-86e509a4-7dda107a/discussion_result.json

- 2026-05-21T17:42:53+08:00: Lifecycle transition `done` -> `pending` by `hermes`. Force: true. Reason: corrected_source_after_false_positive_done_andrej_karpathy_skills_not_openclaw

- 2026-05-21T18:10:51+08:00: Lifecycle transition `pending` -> `claimed` by `hermes-autorun-step`. Reason: auto-claim-and-handoff

- 2026-05-21T18:10:52+08:00: Lifecycle transition `claimed` -> `running` by `hermes-autorun-step`.

- 2026-05-21T18:10:52+08:00: Lifecycle transition `running` -> `review` by `hermes-autorun-step`. Evidence: proof:sha256:811120e1eb72391181e0b988e30e3efbdfbf3249a8658f728b2eea3c2a17ae00, command:py_compile_taskpool PASS

- 2026-05-21T18:10:52+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:2ded456ea3d159573649aec6c9eda72098030506404d997af9d16767a16f1d85, artifact:docs/private/andrej-karpathy-skills-gap-analysis.md, artifact:docs/private/openclaw-garden-skills-gap-analysis.md, proof:user correction resolved source: yaochang008 variants returned 404; direct clone of forrestchang/andrej-karpathy-skills succeeded at commit 2c60614; GitHub API canonical surface is multica-ai/andrej-karpathy-skills, proof:corrected repo files inspected: README.md, CLAUDE.md, EXAMPLES.md, skills/karpathy-guidelines/SKILL.md; OpenClaw awesome-list artifact marked superseded, proof:brain_task_orchestrator selfcheck PASS at 2026-05-21T12:38:02+08:00; proof-check PASS with warnings only, command: multimodel-intervention-step gate=PASS decision=LOOP_DONE artifact=/Users/charles/.hermes/tick-20260521-043547-443127-p82877-86e509a4-7dda107a/discussion_result.json, proof:sha256:160b7b096a278ac7a46923fd041268dfb337e1bb070ea0249a869081d544e0a1, artifact:ratification multimodel certified /Users/charles/.hermes/tick-20260521-043547-443127-p82877-86e509a4-7dda107a/discussion_result.json, proof:sha256:811120e1eb72391181e0b988e30e3efbdfbf3249a8658f728b2eea3c2a17ae00, command:py_compile_taskpool PASS
