# Hermes skill core-body debt remediation — round 2 full proceed

Date: 2026-07-01
User directive: `认可，全盘推进`

## Objective

Continue the prior skill debt cleanup until the `core_body_large` warning class is fully cleared, staying inside the safe local/reversible boundary.

## Objective model / chosen path

Success criteria:
- `skill_too_large` remains 0.
- `core_body_large` becomes 0 across the full skill library, including archives.
- Edited root `SKILL.md` files keep route/control instructions and progressive-loading pointers.
- Extracted content remains in adjacent `references/` files with provenance headers.
- No external installs, credentials, dispatch, publish, destructive actions, or prompt/runtime mutation.

Chosen path:
- Progressive-loading compaction over semantic rewrites.
- Extract long conditional sections into `references/`.
- Add only minimal missing `Don't use for` / pitfalls / verification shell where needed to prevent auditor regressions on touched high-frequency skills.

## Route / multi-model evidence

AgentOS route preflight for this continuation returned:
- domain: `devops`
- risk_class: `medium`
- requested side effect: `S2`
- prohibited: `S4`, `S5`, `S6`, `S7`
- would_execute: false; shadow route only

Multi-model routing closure was run for closeout verification:
- status: PASS
- selected execution route: `claude-code::claude-opus-4-8`
- reviewer route: `openai-codex::gpt-5.5`
- `externalModelCallsExecuted`: false
- budget boundary: `no_token_spend_local_execution_contract; live provider smoke requires separate budget authority`

Readback file:
`/Users/charles/.hermes/state/multimodel-routing-closure/multimodel_routing_closure_latest.json`

## Major root skills compacted in this round

High-frequency active skills cleared:
- `software-development/react-architecture-migration/SKILL.md` → 14,514 chars, findings []
- `github/git-repo-operations/SKILL.md` → 14,306 chars, findings []
- `software-development/systematic-debugging/SKILL.md` → 13,429 chars, findings []
- `personal-productivity/travel-planning/SKILL.md` → 16,793 chars, findings []
- `smart-home/manufacturing-brain/SKILL.md` → 17,833 chars, findings []
- `software-development/requesting-code-review/SKILL.md` → 12,647 chars, findings []

Additional active/non-archive skills compacted by the generic progressive-loading pass:
- `ui-ux-pro-max/.claude/skills/ui-ux-pro-max/SKILL.md`
- `software-development/multi-model-architecture/SKILL.md`
- `software-development/post-update-patch-healing/SKILL.md`
- `software-development/browser-harness-integration/SKILL.md`
- `incremental-implementation/SKILL.md`
- `autonomous-ai-agents/hermes-agent/SKILL.md`
- `software-development/objective-model-path-verification/SKILL.md`
- `creative/humanizer/SKILL.md`
- `devops/gateway-telegram-setup/SKILL.md`
- `software-development/self-improvement-pipeline/SKILL.md`
- `software-development/hermes-workflow-orchestrator/SKILL.md`
- `creative/p5js/SKILL.md`
- `software-development/hermes-agent-skill-authoring/SKILL.md`
- `autonomous-ai-agents/hermes-pipeline/SKILL.md`
- `software-development/test-driven-development/SKILL.md`
- `creative/comfyui/SKILL.md`
- `software-development/uimax-audit/SKILL.md`
- `p10-architecture-self-check/SKILL.md`
- `software-development/agent-skill-design-patterns/SKILL.md`
- `software-development/frontend-state-domain-correctness/SKILL.md`
- `software-development/event-governed-side-effect-executors/SKILL.md`
- `creative/claude-design/SKILL.md`

Archive/root copies also compacted to remove global `core_body_large` warnings:
- `.archive/curator-umbrella-2026-06-10/autonomous-ai-agents/claude-code/SKILL.md`
- `.archive/curator-umbrella-2026-06-10/research/research-paper-writing/SKILL.md`
- `.archive/curator-umbrella-2026-06-17/research/references/absorbed/research-paper-writing/SKILL.md`
- `.archive/software-development/cloud-edge-architecture/SKILL.md`
- `.archive/taskpool-ingest-triage/SKILL.md`
- `.archive/curator-umbrella-2026-06-10/github/github-pr-workflow/SKILL.md`
- `.archive/curator-umbrella-2026-06-10/research/llm-wiki/SKILL.md`
- `.archive/curator-umbrella-2026-06-17/research/references/absorbed/llm-wiki/SKILL.md`

## Example reference readback

The following extracted files exist and were read back by file-stat verification:
- `/Users/charles/.hermes/skills/software-development/react-architecture-migration/references/unified-production-server-and-flow-checks.md`
- `/Users/charles/.hermes/skills/github/git-repo-operations/references/core-workflow.md`
- `/Users/charles/.hermes/skills/software-development/systematic-debugging/references/phase-1-root-cause-investigation.md`
- `/Users/charles/.hermes/skills/personal-productivity/travel-planning/references/core-workflow.md`
- `/Users/charles/.hermes/skills/smart-home/manufacturing-brain/references/multi-model-chain-policy.md`
- `/Users/charles/.hermes/skills/autonomous-ai-agents/hermes-pipeline/references/common-pitfalls.md`
- `/Users/charles/.hermes/skills/.archive/curator-umbrella-2026-06-10/autonomous-ai-agents/claude-code/references/cli-subcommands-print-mode-and-flags.md`

## Verification commands

```bash
python3 /Users/charles/.hermes/scripts/skill_invocation_taxonomy_auditor.py --selftest --pretty
python3 /Users/charles/.hermes/scripts/skill_invocation_taxonomy_auditor.py --write-report --pretty
```

Latest audit reports:
- `/Users/charles/.hermes/docs/private/skill-invocation-taxonomy/latest.md`
- `/Users/charles/.hermes/docs/private/skill-invocation-taxonomy/latest.json`
- `/Users/charles/.hermes/docs/private/skill-invocation-taxonomy/skill-taxonomy-audit-20260701T085758Z.md`
- `/Users/charles/.hermes/docs/private/skill-invocation-taxonomy/skill-taxonomy-audit-20260701T085758Z.json`

Audit readback:

```json
{
  "ok": true,
  "total": 266,
  "findings_by_severity": {"warn": 232},
  "findings_by_code": {
    "description_not_trigger_shaped": 4,
    "missing_anti_conditions": 147,
    "missing_common_pitfalls": 43,
    "missing_verification_checklist": 24,
    "missing_when_to_use": 14
  },
  "skill_too_large": 0,
  "core_body_large": 0
}
```

## Remaining debt

Hard/size debt:
- `skill_too_large`: 0
- `core_body_large`: 0

Remaining quality-shell warnings:
- `missing_anti_conditions`: 147
- `missing_common_pitfalls`: 43
- `missing_verification_checklist`: 24
- `missing_when_to_use`: 14
- `description_not_trigger_shaped`: 4

## Boundary

No external model execution was used for the skill edits; the multi-model route was local dry-run/readback only. No external dispatch, scheduler/worker activation, taskpool lifecycle mutation, credential entry, destructive action, publish/deploy/push, or broad fan-out was performed.

This round is a structural progressive-loading compaction, not a semantic rewrite or certification of every extracted skill workflow.
