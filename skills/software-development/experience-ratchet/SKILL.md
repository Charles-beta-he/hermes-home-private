---
name: experience-ratchet
category: software-development
description: "Use when cross-project experience capture, validation, and promotion system. Ratchet-based promotion with evidence gate. Zero core modification."
---

# Experience Ratchet

## Overview

Cross-project experience capture, validation, and promotion system. Ratchet-based promotion with evidence gate. Zero core modification. It is organized as a gated workflow: advance through explicit stages, preserve evidence at each boundary, and leave neighboring domains to their own skills.

## When to Use

Use this skill when the request matches the `experience-ratchet` trigger and the domain-specific boundaries in this skill apply.

Do not use it for:
- generic one-off questions that do not need this workflow;
- neighboring specialist workflows with a narrower matching skill;
- durable memory or project-profile writes unless this skill explicitly governs that landing zone.

Cross-project experience capture, validation, and promotion system.
Lives entirely outside Hermes core. Uses plugin + hook + script boundary.


- Don't use for: tasks outside this skill's trigger class, requests with a more specific neighboring skill, or situations where required evidence/tooling is unavailable.
## ExperienceAtom v1 Schema

```json
{
  "id": "uuid-v4",
  "version": 1,
  "state": "draft|validated|promoted|demoted|expired",
  "source_task_id": "string",
  "source_skill": "string",
  "pattern": "string — what was learned",
  "context": {
    "project": "string",
    "domain": "string",
    "tools_used": ["string"]
  },
  "evidence": {
    "type": "manual|automated|multi-model",
    "ref": "string — path or URL to evidence artifact",
    "confidence": 0.0
  },
  "ratchet": {
    "promote_count": 0,
    "demote_count": 0,
    "last_transition": "ISO8601",
    "promotion_threshold": 2
  },
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "ttl_days": 90
}
```

## Ratchet State Machine

```
draft ──[gate pass]──> validated ──[N validations]──> promoted
promoted ──[contradiction]──> demoted ──[re-validation]──> validated | expired
any state ──[ttl exceeded]──> expired
```

## Evidence Gate (experience-gate.sh)

Exit 0 = pass, exit 1 = fail. Stdout = JSON verdict.
Required fields: id, version, state, pattern, evidence.confidence >= 0.7.
Valid transitions: draft->validated, validated->promoted, promoted->demoted, demoted->validated|expired.

## Storage

- Draft/validated atoms: ~/.hermes/experience/atoms/{uuid}.json
- Promoted atoms: ~/.hermes/experience/promoted/{pattern_hash}.json
- Expired atoms: deleted after ttl_days

## Promotion Threshold

2 independent validations required (different source_task_id).
Each validation increments ratchet.promote_count.

Independence is semantic, not merely a distinct receipt or task ID. Reject records that reuse the same execution, authority grant, evidence snapshot, or producer identity when policy requires independent validations. Exact-authority validations must bind the grant to the execution/receipt identity or carry an explicit bounded multi-use policy; changing only an ID must never advance promotion.

All lifecycle and ratchet counters are strict nonnegative integers: reject booleans, strings, floats, and negative values before comparison or increment. Do not coerce with `int(value)` or rely on Python's `bool`-is-`int` behavior. Invalid counters must produce a fail-closed finding without mutating lifecycle or promotion state.

## Components

- Skill: this file (canonical schema + protocol)
- Script: ~/.hermes/scripts/experience-gate.sh (evidence gate)
- Plugin: ~/.hermes/plugins/experience-overlay/ (capture + validate + promote)
- Hook: registered in ~/.hermes/hooks/registry.yaml

## Rollback

```bash
rm -rf ~/.hermes/skills/software-development/experience-ratchet/
rm -f ~/.hermes/scripts/experience-gate.sh
rm -rf ~/.hermes/plugins/experience-overlay/
rm -rf ~/.hermes/experience/
# Revert registry.yaml: remove experience-overlay from plugin_hooks
```

## Common Pitfalls

1. Advancing stages without a gate, evidence artifact, or closure-state check.
2. Skipping prerequisite checks and assuming the environment already matches the workflow.
3. Reporting success before reading back the actual outputs, files, or external side effects.

## Verification Checklist

- [ ] Preconditions, scope, and tool availability were checked before following this workflow.
- [ ] The key output artifacts, commands, or side effects were verified by read-back or direct inspection.
- [ ] Any remaining uncertainty, blocker, or human handoff was stated explicitly.
- [ ] Every stage passed its gate before the next stage advanced, with evidence recorded.
