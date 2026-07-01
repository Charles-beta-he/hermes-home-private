# Matt Pocock skills absorption: Hermes safe landing plan

Date: 2026-07-01
Source artifact: https://github.com/mattpocock/skills
Evidence report: /Users/charles/.hermes/docs/private/douyin-mattpocock-skills-analysis-20260701.md

## Objective

Convert the accepted Matt Pocock skill-package lesson into Hermes-native governance without vendoring the upstream package or copying Claude Code plugin mechanics.

## Landed now

1. `real-engineering-workflows` skill refreshed with time-scoped upstream readback at commit `0877403d1e867fd9d574117e9b34ade404f36d2a`.
2. `requesting-code-review` gained a specialist-review-control-plane reference pattern after analysis of Alibaba Open Code Review.
3. New scoped code-review reference file:
   `/Users/charles/.hermes/skills/software-development/requesting-code-review/references/specialist-code-review-cli-reference-pattern.md`

## Next bounded Hermes-native slices

### P1 — Skill invocation taxonomy gate

Problem:
Hermes skills do not yet consistently distinguish model-invoked, user-invoked, draft/in-progress, deprecated, personal, and reference-only packages.

Target:
A deterministic skill-audit report that classifies each skill and flags dangerous default-invocation drift.

Acceptance:
- read-only scan of `~/.hermes/skills`;
- output JSON/Markdown report;
- no skill mutation in first slice;
- flags missing invocation class, stale deprecated skills, oversized SKILL.md, and missing anti-conditions.

### P1 — Project setup skill / project profile bootstrap

Problem:
Project setup details are scattered: taskpool labels, docs path, domain glossary, validation commands, red lines, profile pointer.

Target:
A Hermes project setup workflow that initializes or verifies project profile + domain glossary + taskpool lane/labels + verification commands + docs/SSOT path.

Acceptance:
- local dry-run first;
- no overwrite without explicit merge plan;
- receipt file with before/after summary;
- example output for one non-production temp project.

### P2 — Skill-package hygiene evaluator

Problem:
External skill packages can mix active, personal, deprecated, draft, and host-specific commands.

Target:
A reusable evaluator for external skill packages: README/plugin manifest consistency, active-vs-draft separation, trigger/anti-trigger quality, host-specific command detection.

Acceptance:
- runs on a local cloned/extracted package or fixture;
- no global install;
- report includes adopt/adapt/reject matrix.

### P2 — Vertical-slice taskpool template reinforcement

Problem:
Some capability-intake tasks remain vague instead of becoming independently verifiable tracer bullets.

Target:
Task template fields for `vertical_slice_boundary`, `first_tracer_bullet`, `blocked_by`, `acceptance_evidence`, `negative_cases`, and `AFK/HITL boundary`.

Acceptance:
- template-only or dry-run generation first;
- no lifecycle force-done;
- readback from one generated example card.

## Red lines

- No external package install from social/video evidence alone.
- No copying upstream skills wholesale into Hermes.
- No prompt/runtime default change without tests/readback.
- No taskpool done/certified claim without the existing certification gate passing.
- No credential/API-key entry by agent.
