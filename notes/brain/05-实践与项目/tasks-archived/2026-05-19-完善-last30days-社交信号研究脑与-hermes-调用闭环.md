---
type: task
lane: evolution
layer: L3
status: done
priority: P2
priority_layer: P2
dependency_order: ["1 create last30days brain + registry route; 2 install skill engine; 3 verify diagnose and routing; 4 optionally add wrapper/cron watchlist once topics are configured"]
created: 2026-05-19T12:50:43+08:00
updated: 2026-05-19T15:58:03+08:00
expires_at: 2026-06-18T12:50:43+08:00
project: local-brain
architecture_target: local-brain
capability_delta: Hermes gains a dedicated last30days brain for recent community/social signal research, installed engine skill, routing keywords, source-availability diagnosis, and replayable raw-output evidence.
anti_drift_check: Do not replace provenance-safe research brain; keep optional source claims gated by last30days diagnose/config evidence; preserve upstream skill as copied external package and avoid committing secrets/env/cookies.
acceptance_evidence: brainctl brains validate PASS; brainctl route last30days/social-signal queries -> last30days; copied skill engine --diagnose runs; taskpool selfcheck/proof-check stay PASS or classified historical debt; follow-through cron/dynamic runner exists.
workflow_contract: ["[08-模板/task-workflow-contract-template]"]
requires_multimodel: 
multimodel_reason: 
expected_participants: []
truth_gate: 
evidence_bundle: 
required_authority: budget-handoff
max_authority: autonomous-execution
permission_tier: budget-handoff
write_surfaces: ["taskpool", "hermes-scripts", "brain"]
completion_gate: ratification-or-selfcheck-review-done
lane_semantics: "self-evolution: deterministic gates plus ratification/proof before review->done"
multimodel_triage_result: "P2/evolution: external repo capability absorption into local-brain research workflow; no immediate expensive multimodel required until changing runtime gates."
claimed_by: 
claim_expires_at: 
run_id: 
retry_count: 0
next_attempt_at: 
workspace: 
parallel_boundary: Brain/routing/install verification only; credential setup and topic watchlists are separate user-approved slices.
evidence:
  - proof:installed last30days brain overlay at /Users/charles/.hermes/brains/last30days/brain.yaml and registered registry v0.5.0
  - artifact:/Users/charles/.hermes/skills/research/last30days/SKILL.md
  - proof:brainctl validate PASS; route(last30days OpenClaw community signal)=last30days; route(最近30天 React 用户真实讨论)=last30days
  - proof:last30days --diagnose PASS with baseline sources reddit,hackernews,polymarket,github and optional sources gated by credentials
  - proof:taskpool selfcheck PASS; proof-check PASS; dispatch tick summary OK; existing cron follow-through triggers present
  - proof:brainctl validate PASS; routes -> last30days; skill discoverable; engine diagnose baseline sources; taskpool selfcheck/proof PASS; dispatch summary OK
  - proof:sha256:d7b70201ba347e0291ae5749c96b5130eb3ff55b358b493cb866a6c5eb994bf2
concepts: ["task"]
---

# Task - 完善 last30days 社交信号研究脑与 Hermes 调用闭环

## Objective

Turn mvanhorn/last30days-skill into a governed Hermes brain capability rather than a one-off repo note.

## Acceptance Criteria

- [x] Observable result is recorded in Proof Log.
- [x] `last30days` brain exists and is registered in the multi-brain registry.
- [x] Hermes skill loader can discover the installed `last30days` skill.
- [x] Engine diagnose reports usable baseline sources and credential-gated optional sources.
- [x] Taskpool selfcheck/proof/dispatch summary remain green after the change.

## Plan / Workpad

- [x] Reconcile current state, dependency order, and architecture boundaries before execution.
- [x] Advance the long-term maintainable mainline plan with the next bounded step and staged evidence.
- [x] Record proof, status, and any next dependency or handoff required.

## Validation

| Command / Check | Status | Evidence |
|---|---|---|
| `python3 -m py_compile ~/.hermes/scripts/brainctl.py` | PASS | route patch syntax verified |
| `python3 ~/.hermes/scripts/brainctl.py --json brains validate` | PASS | registry v0.5.0, 10 subbrains, no warnings |
| `brainctl route "last30days OpenClaw community signal"` | PASS | brain=`last30days` |
| `brainctl route "最近30天 React 用户真实讨论"` | PASS | brain=`last30days` |
| `skills_list(category="research")` | PASS | includes `last30days` |
| `/opt/homebrew/bin/python3.12 ~/.hermes/skills/research/last30days/scripts/last30days.py --diagnose` | PASS | baseline sources: reddit, hackernews, polymarket, github; optional sources missing config or browser permission |
| `brain_task_orchestrator selfcheck --json` | PASS | no failures |
| `brain_task_orchestrator proof-check --json` | PASS | checked_count=120, no failures |
| `HERMES_LOCAL_BRAIN_AUTORUN=1 brain_task_dispatch_tick.py --summary --print-always --no-state` | OK | error_count=0, cron_status=OK, proof/selfcheck PASS |

## Proof Log

- 2026-05-19T12:50:43+08:00: Task created from local-brain control point.
- 2026-05-19T12:53:09+08:00: Installed `last30days` skill package into `~/.hermes/skills/research/last30days`; added `last30days` brain overlay and registry/main/research routing metadata; patched `brainctl.py` route table. Verification passed: brainctl validate PASS, route queries -> last30days, skill discovery includes last30days, engine diagnose usable with baseline sources, taskpool selfcheck/proof PASS, dispatch summary OK.

## Blockers / Confusions

- Optional high-signal sources are credential/browser-permission gated: X/Twitter not authenticated, ScrapeCreators absent, provider keys absent, Safari cookie read blocked by macOS Full Disk Access. Baseline source path still works with Reddit/HN/Polymarket/GitHub.

## Final Handoff

- Status: installed and verified as governed Hermes brain capability; credential/topic watchlists remain separate explicit slices.
- Evidence: `~/.hermes/brains/last30days/brain.yaml`, `~/.hermes/skills/research/last30days/SKILL.md`, registry v0.5.0, brainctl route/validate output, diagnose output, taskpool green checks.
- Residual risk: upstream copy is not yet auto-updated; if you want marketplace-style updates, add a dedicated update cron or npx-skills install path in a follow-up slice.

- 2026-05-19T12:54:39+08:00: Lifecycle transition `pending` -> `claimed` by `hermes`.

- 2026-05-19T12:54:39+08:00: Lifecycle transition `claimed` -> `running` by `hermes`. Reason: claiming_for_verified_closeout

- 2026-05-19T12:54:39+08:00: Lifecycle transition `running` -> `review` by `hermes`. Reason: implemented_verified_last30days_brain_skill_routing Evidence: proof:brainctl validate PASS; routes -> last30days; skill discoverable; engine diagnose baseline sources; taskpool selfcheck/proof PASS; dispatch summary OK

- 2026-05-19T15:58:03+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun-review-close`. Reason: auto-close review after proof-gated evidence Evidence: proof:sha256:d7b70201ba347e0291ae5749c96b5130eb3ff55b358b493cb866a6c5eb994bf2, proof:installed last30days brain overlay at /Users/charles/.hermes/brains/last30days/brain.yaml and registered registry v0.5.0, artifact:/Users/charles/.hermes/skills/research/last30days/SKILL.md, proof:brainctl validate PASS; route(last30days OpenClaw community signal)=last30days; route(最近30天 React 用户真实讨论)=last30days, proof:last30days --diagnose PASS with baseline sources reddit,hackernews,polymarket,github and optional sources gated by credentials, proof:taskpool selfcheck PASS; proof-check PASS; dispatch tick summary OK; existing cron follow-through triggers present, proof:brainctl validate PASS; routes -> last30days; skill discoverable; engine diagnose baseline sources; taskpool selfcheck/proof PASS; dispatch summary OK
