# Hermes skill core-body debt remediation

Date: 2026-07-01
User directive: continue debt remediation and use multi-model intelligent routing.

## Routing / authority evidence

AgentOS route preflight was run for intent:
`继续解决 Hermes skill core_body_large debt with multimodel intelligent routing; local reversible skill compaction only`

Readback:
- domain: `hermes_self_architecture`
- risk_class: `medium`
- requested side effect: `S2`
- prohibited: `S4`, `S5`, `S6`, `S7`
- would_execute: false for AgentOS shadow route

Multi-model routing closure dry-run was run for:
`skill debt compaction route: core_body_large remediation local reversible references extraction`

Readback:
- status: PASS
- selected producer route: `claude-code :: claude-opus-4-8`
- reviewer route recorded: `deepseek :: deepseek-v4-flash`
- externalModelCallsExecuted: false
- budget boundary: no token spend local execution contract; live provider smoke requires separate budget authority

## Objective

Reduce root `SKILL.md` core body debt by moving detailed long-tail content into adjacent `references/` files while keeping the root as the routing/control contract.

## Constraints

- Local reversible file edits only.
- No external model calls, installs, credential entry, dispatch, publish, destructive actions, or force-close.
- Preserve extracted content with provenance headers.
- Add exact root pointers and minimum in-root rules for progressive loading.

## Main changed root skills

### taskpool-control-plane

Root:
`/Users/charles/.hermes/skills/software-development/taskpool-control-plane/SKILL.md`

Size after this session: 13,267 chars.
Findings after this session: none.

New references added in this continuation:
- `references/task-creation-cli-guardrails.md`
- `references/external-repo-doc-analysis-intake.md`
- `references/pitfalls-and-failure-modes.md`
- `references/when-to-use-routing.md`
- `references/cron-provider-429-recovery.md`
- `references/fast-triage-flow.md`
- `references/stale-claimed-recovery.md`
- `references/blocked-parent-finished-children.md`
- `references/finished-children-not-reopened-parent.md`
- `references/sequential-full-completion-loop.md`
- `references/dynamic-runner-human-escape-preclaim.md`
- `references/review-done-lifecycle-proof-pitfall.md`
- `references/task-creation-retry-duplicate-cleanup.md`
- `references/operational-watchdog-cron-scripts.md`
- `references/taskpool-intake-framing-parallel-umbrella.md`
- `references/task-adapter-framework-pointer.md`
- `references/observability-depth-classification.md`
- `references/dispatch-tick-fix-guidance.md`
- `references/false-positive-done-tasks.md`
- `references/evolution-lane-cert-loop-prevention.md`
- `references/verification-checks.md`
- `references/root-reference-index.md`

Also added explicit `Don't use for`, `Common Pitfalls`, and `Verification Checklist` to clear standard-shell warnings.

### research/last30days

Root:
`/Users/charles/.hermes/skills/research/last30days/SKILL.md`

Size after this session: 14,230 chars.
Findings after this session: none.

New references added in this continuation:
- `references/output-contract-badge-laws.md`
- `references/ranked-evidence-clusters.md`
- `references/preflight-resolution-handles-repos-communities.md`
- `references/pre-research-intelligence.md`
- `references/judge-agent-synthesize-all-sources.md`
- `references/skill-and-output-contract.md`
- `references/invocation-contract.md`
- `references/parse-user-intent.md`
- `references/query-quality-preflight.md`
- `references/generate-query-plan.md`
- `references/research-execution.md`
- `references/websearch-supplement.md`
- `references/security-and-permissions.md`
- `references/comparison-and-competitor-mode.md`

Also added exact `Don't use for` anti-conditions.

### lark-task-reading

Root:
`/Users/charles/.hermes/skills/software-development/lark-task-reading/SKILL.md`

Size after this session: 16,949 chars.
Findings after this session: none.

New references added in this continuation:
- `references/executing-lark-task-closeout-before-exploration.md`
- `references/pitfalls-and-verification.md`
- `references/implementation-pattern.md`
- `references/lark-api-shape-notes.md`
- `references/loop-implementation.md`
- `references/fusion-map-arc-github-dispatch.md`

Also added exact `Don't use for` anti-conditions.

### mobile-frontend-delivery

Root:
`/Users/charles/.hermes/skills/software-development/mobile-frontend-delivery/SKILL.md`

Size after this session: 15,016 chars.
Findings after this session: none.

New references added in this continuation:
- `references/routing-by-subproblem.md`
- `references/key-patterns.md`
- `references/common-pitfalls.md`

Also added `Verification Checklist`.

### multi-model-thinking

Root:
`/Users/charles/.hermes/skills/software-development/multi-model-thinking/SKILL.md`

Size after this session: 19,474 chars.
Findings after this session: none.

New references added in this continuation:
- `references/evidence-first-rule.md`
- `references/hermes-current-landing.md`
- `references/lessons-learned.md`
- `references/cross-cutting-concern-recognition.md`
- `references/taskpool-auto-multimodel-intervention.md`

Also added exact `Don't use for` anti-conditions.

## Verification

Commands run:

```bash
python3 /Users/charles/.hermes/scripts/skill_invocation_taxonomy_auditor.py --selftest --pretty
python3 /Users/charles/.hermes/scripts/skill_invocation_taxonomy_auditor.py --write-report --pretty
```

Latest report:
`/Users/charles/.hermes/docs/private/skill-invocation-taxonomy/latest.md`
`/Users/charles/.hermes/docs/private/skill-invocation-taxonomy/latest.json`

Readback summary:

```json
{
  "ok": true,
  "total": 266,
  "severity": {"warn": 277},
  "skill_too_large": 0,
  "core_body_large": 36,
  "target_findings": {
    "research/last30days/SKILL.md": [],
    "software-development/lark-task-reading/SKILL.md": [],
    "software-development/mobile-frontend-delivery/SKILL.md": [],
    "software-development/multi-model-thinking/SKILL.md": [],
    "software-development/taskpool-control-plane/SKILL.md": []
  }
}
```

## Remaining debt

Hard errors remain at 0.

Remaining warning classes:
- `core_body_large`: 36
- `missing_anti_conditions`: 151
- `missing_common_pitfalls`: 45
- `missing_verification_checklist`: 26
- `missing_when_to_use`: 15
- `description_not_trigger_shaped`: 4

Top remaining `core_body_large` roots:
1. `software-development/react-architecture-migration/SKILL.md` — 58,401 chars
2. `ui-ux-pro-max/.claude/skills/ui-ux-pro-max/SKILL.md` — 44,913 chars
3. `github/git-repo-operations/SKILL.md` — 44,194 chars
4. `software-development/systematic-debugging/SKILL.md` — 43,378 chars
5. `smart-home/manufacturing-brain/SKILL.md` — 42,963 chars
6. `personal-productivity/travel-planning/SKILL.md` — 42,871 chars

## Boundary

This was a progressive-loading compaction pass, not a semantic rewrite. No extracted content was intentionally discarded. No external model calls were executed; the multi-model routing closure was local dry-run evidence only.
