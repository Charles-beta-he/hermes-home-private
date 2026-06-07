# Hermes Skill Pattern Coverage Audit

Date: 2026-06-07 17:20:50
Skills root: `/Users/charles/.hermes/skills`
Scope: non-mutating heuristic audit of existing `SKILL.md` files.

## Executive summary

- Total skills scanned: 237
- Active skills scanned: 213; archived skills scanned: 24
- Active `## When to Use`: 192/213 (90.1%)
- Active verification or Definition of Done: 197/213 (92.5%)
- Active minimum eval prompts: 3/213 (1.4%)
- Active full routing matrix: 1/213 (0.5%)
- Active broken concrete linked-file references: 19/213 (8.9%)
- Active high-risk skills by heuristic: 27/213 (12.7%)
- Skills with `## When to Use`: 203/237 (85.7%)
- Skills with verification or Definition of Done: 205/237 (86.5%)
- Skills with minimum eval prompts: 3/237 (1.3%)
- Skills with full routing matrix: 1/237 (0.4%)
- Skills with broken concrete linked-file references: 36/237 (15.2%)
- Skills with placeholder/example linked-file contracts: 7/237 (3.0%)
- High-risk skills by heuristic: 47/237 (19.8%)

Interpretation: this is coverage telemetry, not an automatic rewrite mandate. Pattern labels are candidates until human/agent review confirms semantics.

## Primary pattern coverage

| Pattern | Count | Share |
|---|---:|---:|
| wrapper | 88 | 37.1% |
| pipeline | 70 | 29.5% |
| generator | 41 | 17.3% |
| reviewer | 21 | 8.9% |
| memory | 6 | 2.5% |
| router | 6 | 2.5% |
| monitor | 3 | 1.3% |
| inversion | 2 | 0.8% |

## Risk distribution

| Risk | Count | Share |
|---|---:|---:|
| high | 47 | 19.8% |
| medium | 23 | 9.7% |
| low | 167 | 70.5% |

## Category coverage

| Category | Count |
|---|---:|
| software-development | 64 |
| .archive | 24 |
| creative | 20 |
| mlops | 16 |
| devops | 11 |
| productivity | 11 |
| autonomous-ai-agents | 10 |
| github | 8 |
| research | 7 |
| ui-ux-pro-max | 7 |
| apple | 6 |
| media | 5 |
| smart-home | 5 |
| ui-skills | 4 |
| mcp | 3 |
| social-media | 3 |
| data-science | 2 |
| email | 2 |
| note-taking | 2 |
| api-and-interface-design | 1 |
| chinese-platforms | 1 |
| code-simplification | 1 |
| codebase-intelligence | 1 |
| deprecation-and-migration | 1 |
| diagramming | 1 |
| documentation-and-adrs | 1 |
| dogfood | 1 |
| domain | 1 |
| feeds | 1 |
| framework-audit | 1 |
| gaming | 1 |
| gifs | 1 |
| gsd-bridge | 1 |
| incremental-implementation | 1 |
| inference-sh | 1 |
| loop | 1 |
| p10 | 1 |
| p10-architecture-self-check | 1 |
| p7 | 1 |
| p9 | 1 |
| personal-productivity | 1 |
| post-deploy-verification | 1 |
| pro | 1 |
| red-teaming | 1 |
| source-driven-development | 1 |
| workflow | 1 |

## Most common gaps

| Flag | Count | Share |
|---|---:|---:|
| missing_full_routing_matrix | 236 | 99.6% |
| missing_min_eval_prompts | 234 | 98.7% |
| broken_linked_files | 36 | 15.2% |
| missing_when_to_use | 34 | 14.3% |
| missing_verification_or_dod | 32 | 13.5% |
| description_not_use_when | 28 | 11.8% |
| wrapper_missing_read_back_signal | 22 | 9.3% |
| pipeline_missing_gate_signal | 22 | 9.3% |
| reviewer_missing_rubric_signal | 13 | 5.5% |
| large_root_no_references | 13 | 5.5% |
| missing_pitfalls_failure_modes | 13 | 5.5% |

## Broken concrete linked-file references

| Skill | Broken references |
|---|---|
| `.archive/agent-team-parallel` | references/cycle-timeout-diagnostics.md |
| `.archive/devops/icon-asset-pipeline` | references/pwa-splash-screen-config.md<br>references/splash-animation-implementation.md |
| `.archive/devops/macos-network-admin` | references/macos-proxy-app-config-discovery.md<br>references/macos-proxy-commands.md<br>references/shadowrocket-config-analysis.md |
| `.archive/devops/multi-repo-branch-orchestration` | references/remote-multi-repo-git-operations.md |
| `.archive/git-state-aware-debugging` | references/hermes-run-agent-ordering.md |
| `.archive/github/git-conflict-resolution` | references/common-conflict-patterns.md<br>references/two-phase-conflict-example.md |
| `.archive/product-prototype-code-audit` | references/uvisa-admin-exchange-closed-loop.md<br>references/uvisa-admin-users-closed-loop.md<br>references/uvisa-admin-users-pii-action-closure.md<br>references/uvisa-admin-users-prd-secondary-filter.md |
| `.archive/project-profile-maintenance` | references/schema-change-guardrail-propagation-example.md<br>references/uvisa-canonical-profile-mapping.md<br>references/uvisa-project-profile-refresh.md |
| `.archive/software-development/architecture-theory-audit` | references/hermes-selfheal-gap-analysis.md<br>references/hermes-task-system-gap-analysis.md<br>references/theory-domain-quick-reference.md |
| `.archive/software-development/cloud-edge-architecture` | references/agent-team-multi-node.md<br>references/architecture-refactoring-pattern.md<br>references/architecture-self-check-pattern.md<br>references/distributed-management-patterns.md<br>references/edge-worker-update-management.md<br>references/install-troubleshooting.md<br>references/lan-cross-device-deployment.md<br>references/local-cloud-prototype.md<br>references/master-slave-connection-testing.md<br>references/multi-brain-architecture.md |
| `.archive/software-development/concurrent-async-guard` | references/zustand-category-filtered-lists.md |
| `.archive/software-development/external-framework-evaluation` | references/guardrails-evaluation-example.md |
| `.archive/software-development/financial-ledger-frontend-patterns` | references/batch-exchange-fixes-t104020-t104052.md<br>references/exchange-fee-sourcing.md<br>references/fx-dedup-fix.md<br>references/fx-investigation-methodology.md<br>references/t104026-fee-alignment.md<br>references/tx-sign-determination-chain.md |
| `.archive/software-development/pwa-cache-invalidation` | references/uvisa-backend-i18n-architecture.md<br>references/uvisa-update-notification-ux.md |
| `.archive/software-development/task-depth-analysis` | references/uvisa-implementation.md |
| `.archive/taskpool-ingest-triage` | references/blocked-multimodel-diagnostics.md<br>references/multimodel-blocked-resolution.md<br>references/multimodel-intake-semantics.md<br>references/multimodel-taskpool-contracts.md<br>references/no-in-progress-diagnosis.md<br>references/non-convergence-auto-narrowing.md<br>references/non-convergence-closure-loop.md<br>references/taskpool-autostart-and-gating.md<br>references/taskpool-ingest-checklist.md |
| `.archive/testing/playwright-authenticated-screenshots` | references/playwright-pitfalls.md |
| `autonomous-ai-agents/hermes-pipeline` | references/numeric-guardrails.md<br>references/self-optimizing-verification-loop.md<br>references/task-flow-deadlock-detection-and-fix.md |
| `autonomous-ai-agents/kanban-codex-lane` | scripts/run_tests.sh |
| `devops/token-saver-frontend-rtk` | references/rtk_layer12_fewshot.md |
| `devops/token-saver-rtk` | references/rtk_layer12_fewshot.md |
| `loop` | references/event-driven-trigger-timing-and-loop-economy.md |
| `note-taking/obsidian` | references/local-brain-memory-repo-adoption.md<br>references/local-brain-theory-foundation-fill.md |
| `pro` | references/evolution-protocol.md<br>references/platform.md |
| `productivity/powerpoint` | scripts/office/soffice.py |
| `software-development/auto-optimize-loop` | references/mobile-h5-loop-gates.md<br>templates/mobile-h5-issue-ledger.json |
| `software-development/debugging-hermes-tui-commands` | scripts/run_tests.sh tests/gateway/ |
| `software-development/development-closure-consensus` | references/pr-closeout-consensus.md |
| `software-development/hermes-workflow-orchestrator` | references/project-profile-injection-pattern.md<br>references/workflow-patterns.md |
| `software-development/multi-model-thinking` | references/external-memory-system-landing.md<br>references/local-brain-hierarchy-overlay-routing.md<br>scripts/architecture_theory_impact_ratchet.py --json<br>scripts/multimodel_keypoint_coverage_ratchet.py --json |
| `software-development/python-debugpy` | scripts/run_tests.sh |
| `software-development/self-improvement-pipeline` | scripts/test_consult_models_integration.py<br>scripts/test_ensemble_vote_integration.py<br>scripts/test_post_session_autopsy.py<br>scripts/test_self_improvement_pipeline.py<br>scripts/test_usage_score.py |
| `software-development/skill-eval` | evals/prompts.csv |
| `software-development/stuck-diagnosis` | references/agent-team-controller-timeout-pattern.md<br>references/infrastructure-cascade-diagnosis.md |
| `ui-ux-pro-max/.claude/skills/brand` | assets/design-tokens.css<br>assets/design-tokens.json |
| `ui-ux-pro-max/.claude/skills/design-system` | assets/css/slide-animations.css<br>assets/design-tokens.css<br>assets/design-tokens.json |

## High-risk skills to inspect first

| Skill | Pattern | Flags |
|---|---|---|
| `.archive/software-development/cloud-edge-architecture` | wrapper | missing_when_to_use, missing_verification_or_dod, description_not_use_when, missing_min_eval_prompts, missing_full_routing_matrix, broken_linked_files, large_root_no_references, wrapper_missing_read_back_signal |
| `.archive/software-development/pwa-cache-invalidation` | wrapper | missing_when_to_use, missing_verification_or_dod, description_not_use_when, missing_min_eval_prompts, missing_full_routing_matrix, broken_linked_files, wrapper_missing_read_back_signal |
| `devops/token-saver-rtk` | pipeline | missing_when_to_use, missing_verification_or_dod, missing_pitfalls_failure_modes, description_not_use_when, missing_min_eval_prompts, missing_full_routing_matrix, broken_linked_files |
| `software-development/requirement-clarification` | pipeline | missing_when_to_use, missing_verification_or_dod, missing_pitfalls_failure_modes, description_not_use_when, missing_min_eval_prompts, missing_full_routing_matrix, pipeline_missing_gate_signal |
| `.archive/git-state-aware-debugging` | pipeline | missing_when_to_use, description_not_use_when, missing_min_eval_prompts, missing_full_routing_matrix, broken_linked_files, pipeline_missing_gate_signal |
| `.archive/product-prototype-code-audit` | reviewer | missing_when_to_use, missing_verification_or_dod, description_not_use_when, missing_min_eval_prompts, missing_full_routing_matrix, broken_linked_files |
| `.archive/software-development/concurrent-async-guard` | wrapper | missing_verification_or_dod, description_not_use_when, missing_min_eval_prompts, missing_full_routing_matrix, broken_linked_files, wrapper_missing_read_back_signal |
| `.archive/software-development/hybrid-app-packaging` | wrapper | missing_when_to_use, missing_verification_or_dod, missing_pitfalls_failure_modes, missing_min_eval_prompts, missing_full_routing_matrix, wrapper_missing_read_back_signal |
| `.archive/software-development/pwa-install-prompt` | reviewer | missing_when_to_use, missing_verification_or_dod, description_not_use_when, missing_min_eval_prompts, missing_full_routing_matrix, reviewer_missing_rubric_signal |
| `.archive/task-framing-governance` | pipeline | missing_when_to_use, missing_verification_or_dod, description_not_use_when, missing_min_eval_prompts, missing_full_routing_matrix, pipeline_missing_gate_signal |
| `.archive/testing/playwright-authenticated-screenshots` | wrapper | missing_verification_or_dod, description_not_use_when, missing_min_eval_prompts, missing_full_routing_matrix, broken_linked_files, wrapper_missing_read_back_signal |
| `devops/hermes-storage-governance` | reviewer | missing_when_to_use, missing_verification_or_dod, description_not_use_when, missing_min_eval_prompts, missing_full_routing_matrix, reviewer_missing_rubric_signal |
| `devops/token-saver-frontend-rtk` | pipeline | missing_verification_or_dod, missing_pitfalls_failure_modes, description_not_use_when, missing_min_eval_prompts, missing_full_routing_matrix, broken_linked_files |
| `research/last30days` | generator | missing_when_to_use, missing_verification_or_dod, missing_pitfalls_failure_modes, description_not_use_when, missing_min_eval_prompts, missing_full_routing_matrix |
| `smart-home/external-control-brain` | wrapper | missing_when_to_use, missing_verification_or_dod, missing_pitfalls_failure_modes, missing_min_eval_prompts, missing_full_routing_matrix, wrapper_missing_read_back_signal |
| `smart-home/manufacturing-brain` | wrapper | missing_when_to_use, missing_verification_or_dod, missing_pitfalls_failure_modes, missing_min_eval_prompts, missing_full_routing_matrix, wrapper_missing_read_back_signal |
| `software-development/experience-ratchet` | pipeline | missing_when_to_use, missing_verification_or_dod, missing_pitfalls_failure_modes, description_not_use_when, missing_min_eval_prompts, missing_full_routing_matrix |
| `software-development/multi-model-certification-round` | pipeline | missing_when_to_use, missing_verification_or_dod, missing_pitfalls_failure_modes, description_not_use_when, missing_min_eval_prompts, missing_full_routing_matrix |
| `ui-skills/skills/baseline-ui` | generator | missing_when_to_use, missing_verification_or_dod, missing_pitfalls_failure_modes, description_not_use_when, missing_min_eval_prompts, missing_full_routing_matrix |
| `.archive/devops/icon-asset-pipeline` | generator | missing_verification_or_dod, description_not_use_when, missing_min_eval_prompts, missing_full_routing_matrix, broken_linked_files |
| `.archive/devops/macos-network-admin` | reviewer | missing_verification_or_dod, missing_min_eval_prompts, missing_full_routing_matrix, broken_linked_files, reviewer_missing_rubric_signal |
| `.archive/devops/multi-repo-branch-orchestration` | memory | missing_verification_or_dod, description_not_use_when, missing_min_eval_prompts, missing_full_routing_matrix, broken_linked_files |
| `.archive/github/git-conflict-resolution` | pipeline | missing_verification_or_dod, missing_min_eval_prompts, missing_full_routing_matrix, broken_linked_files, pipeline_missing_gate_signal |
| `.archive/project-profile-maintenance` | memory | missing_when_to_use, description_not_use_when, missing_min_eval_prompts, missing_full_routing_matrix, broken_linked_files |
| `.archive/software-development/financial-ledger-frontend-patterns` | wrapper | missing_verification_or_dod, missing_min_eval_prompts, missing_full_routing_matrix, broken_linked_files, wrapper_missing_read_back_signal |
| `.archive/software-development/hermes-self-improvement-pipeline` | monitor | missing_when_to_use, missing_verification_or_dod, description_not_use_when, missing_min_eval_prompts, missing_full_routing_matrix |
| `.archive/software-development/task-depth-analysis` | pipeline | description_not_use_when, missing_min_eval_prompts, missing_full_routing_matrix, broken_linked_files, pipeline_missing_gate_signal |
| `.archive/taskpool-ingest-triage` | pipeline | missing_when_to_use, missing_min_eval_prompts, missing_full_routing_matrix, broken_linked_files, large_root_no_references |
| `devops/kanban-worker` | reviewer | missing_when_to_use, missing_verification_or_dod, description_not_use_when, missing_min_eval_prompts, missing_full_routing_matrix |
| `software-development/hermes-overlay-ratchet-upgrades` | reviewer | missing_when_to_use, description_not_use_when, missing_min_eval_prompts, missing_full_routing_matrix, reviewer_missing_rubric_signal |
| `software-development/hermes-self-audit` | reviewer | missing_when_to_use, missing_verification_or_dod, description_not_use_when, missing_min_eval_prompts, missing_full_routing_matrix |
| `software-development/requesting-code-review` | reviewer | description_not_use_when, missing_min_eval_prompts, missing_full_routing_matrix, large_root_no_references, reviewer_missing_rubric_signal |
| `workflow/qian-meta-synthesis` | pipeline | missing_when_to_use, missing_verification_or_dod, missing_pitfalls_failure_modes, missing_min_eval_prompts, missing_full_routing_matrix |
| `.archive/devops/cli-tool-installation` | wrapper | missing_when_to_use, missing_min_eval_prompts, missing_full_routing_matrix, wrapper_missing_read_back_signal |
| `.archive/software-development/pwa-safe-area-handling` | wrapper | missing_when_to_use, missing_min_eval_prompts, missing_full_routing_matrix, wrapper_missing_read_back_signal |
| `software-development/python-debugpy` | wrapper | missing_min_eval_prompts, missing_full_routing_matrix, broken_linked_files, wrapper_missing_read_back_signal |
| `api-and-interface-design` | wrapper | missing_min_eval_prompts, missing_full_routing_matrix, wrapper_missing_read_back_signal |
| `code-simplification` | wrapper | missing_min_eval_prompts, missing_full_routing_matrix, wrapper_missing_read_back_signal |
| `creative/comfyui` | wrapper | missing_min_eval_prompts, missing_full_routing_matrix, wrapper_missing_read_back_signal |
| `creative/pretext` | wrapper | missing_min_eval_prompts, missing_full_routing_matrix, wrapper_missing_read_back_signal |
| `deprecation-and-migration` | wrapper | missing_min_eval_prompts, missing_full_routing_matrix, wrapper_missing_read_back_signal |
| `devops/local-devops-tooling` | wrapper | missing_min_eval_prompts, missing_full_routing_matrix, wrapper_missing_read_back_signal |
| `incremental-implementation` | wrapper | missing_min_eval_prompts, missing_full_routing_matrix, wrapper_missing_read_back_signal |
| `productivity/lark-docx-reading` | wrapper | missing_min_eval_prompts, missing_full_routing_matrix, wrapper_missing_read_back_signal |
| `software-development/frontend-state-domain-correctness` | wrapper | missing_min_eval_prompts, missing_full_routing_matrix, wrapper_missing_read_back_signal |
| `software-development/mobile-frontend-delivery` | wrapper | missing_min_eval_prompts, missing_full_routing_matrix, wrapper_missing_read_back_signal |
| `source-driven-development` | wrapper | missing_min_eval_prompts, missing_full_routing_matrix, wrapper_missing_read_back_signal |

## Skills missing minimum eval prompts, sample

- `.archive/agent-team-parallel` (pipeline)
- `.archive/devops/cli-tool-installation` (wrapper)
- `.archive/devops/hermes-observability` (pipeline)
- `.archive/devops/icon-asset-pipeline` (generator)
- `.archive/devops/macos-network-admin` (reviewer)
- `.archive/devops/multi-repo-branch-orchestration` (memory)
- `.archive/git-state-aware-debugging` (pipeline)
- `.archive/github/git-conflict-resolution` (pipeline)
- `.archive/product-prototype-code-audit` (reviewer)
- `.archive/project-profile-maintenance` (memory)
- `.archive/software-development/architecture-theory-audit` (pipeline)
- `.archive/software-development/cloud-edge-architecture` (wrapper)
- `.archive/software-development/concurrent-async-guard` (wrapper)
- `.archive/software-development/external-framework-evaluation` (pipeline)
- `.archive/software-development/financial-ledger-frontend-patterns` (wrapper)
- `.archive/software-development/hermes-self-improvement-pipeline` (monitor)
- `.archive/software-development/hybrid-app-packaging` (wrapper)
- `.archive/software-development/pwa-cache-invalidation` (wrapper)
- `.archive/software-development/pwa-install-prompt` (reviewer)
- `.archive/software-development/pwa-safe-area-handling` (wrapper)
- `.archive/software-development/task-depth-analysis` (pipeline)
- `.archive/task-framing-governance` (pipeline)
- `.archive/taskpool-ingest-triage` (pipeline)
- `.archive/testing/playwright-authenticated-screenshots` (wrapper)
- `api-and-interface-design` (wrapper)
- `apple` (wrapper)
- `apple/apple-notes` (wrapper)
- `apple/apple-reminders` (wrapper)
- `apple/findmy` (wrapper)
- `apple/imessage` (wrapper)

## Unclassified skills, sample

None.

## Recommended next actions

1. Do not batch-edit all skills. Use this report as a triage queue.
2. Fix broken linked-file references first; they are silent runtime failures.
3. Pilot 10 representative skills: 2 each from Wrapper, Generator, Reviewer, Inversion, Pipeline.
4. For any skill whose `description` changes, add/refresh `evals/prompts.csv` before committing.
5. Treat high-risk Wrapper skills without read-back signals as safety-priority audits.
6. Promote recurring scan usage into the `agent-skill-design-patterns` skill script; keep generated reports in docs/private.

## Boundary / human intervention

This audit intentionally stops before bulk mutation. Human/owner review is needed before:

- changing many skill descriptions, because descriptions are routing logic;
- deleting or merging skills;
- deciding whether a broken linked reference was intentionally removed;
- labeling a heuristic pattern as canonical metadata for a skill;
- enabling automated routing tests across multiple model families.

## Method limits

- Pattern classification is keyword-based and may over-detect broad workflow words.
- Linked-file detection only catches backtick paths under references/templates/scripts/assets/evals.
- Eval presence is file-coverage only; it does not prove the evals were executed against the active router.
- Verification section presence does not prove verification quality.

