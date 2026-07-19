---
name: qian-meta-synthesis
description: Use when a task requires 钱学森式从定性到定量综合集成、多脑研讨厅、source/evidence/dissent separation, or research→dev capability-gap handback governance.
---

# Qian Meta-Synthesis for Hermes 多脑

## Overview

Use when a task requires 钱学森式从定性到定量综合集成、多脑研讨厅、source/evidence/dissent separation, or research→dev capability-gap handback governance. It is organized as a gated workflow: advance through explicit stages, preserve evidence at each boundary, and leave neighboring domains to their own skills.

## When to Use

Use this skill when the request matches the `qian-meta-synthesis` trigger and the domain-specific boundaries in this skill apply.

Do not use it for:
- generic one-off questions that do not need this workflow;
- neighboring specialist workflows with a narrower matching skill;
- durable memory or project-profile writes unless this skill explicitly governs that landing zone.

Use this skill when:
- The user asks for “多模型思考/多脑会商/综合集成/从定性到定量”。
- A Hermes evolution task affects brain routing, dev filling, taskpool governance, memory/skills, or long-term architecture.
- A domain brain has a claim but needs dev to build a verification tool, connector, harness, or task contract.


- Don't use for: tasks outside this skill's trigger class, requests with a more specific neighboring skill, or situations where required evidence/tooling is unavailable.
## Core principle

Do not treat “multi-model agreement” as truth. Numeric probability remains null unless a defensible prior/likelihood model or calibration history is recorded in `probability_basis`. 钱学森式综合集成 requires three separated ledgers:
1. Source/evidence ledger — what is verified, uncertain, or missing.
2. Expert/model dissent ledger — what each brain/model believes and where it disagrees.
3. Engineering verification ledger — what dev/hermes-core actually tested or instrumented.

## Roles

| Role | Hermes mapping | Output |
|---|---|---|
| 总体设计部 | main | problem framing, constraints, final accept/amend/split/escalate decision |
| 知识体系 | research + local/session brain | source packet, confidence, falsifier |
| 专家体系 | domain brain + external models | proposals, risks, dissent |
| 机器体系 | dev + hermes-core/mlops | scripts, connectors, tests, quantitative checks |
| 沉淀体系 | workflow | protocol/skill/atom/taskpool writeback |

## Mandatory session schema

Record or produce these fields for any serious session:

```yaml
meta_synthesis_session:
  problem: "..."
  desired_state: "..."
  constraints: []
  source_packet:
    verified: []
    uncertain: []
    missing: []
  qualitative_hypotheses:
    - claim: "..."
      owner_brain: research|main|domain
      confidence:
        state: unsupported|weakened|still_live|leading|strongly_supported|falsified
        numeric_probability: null
        probability_basis: null
      falsifier: "..."
  quantitative_checks:
    - owner_brain: dev|hermes-core|mlops
      artifact: "path_or_command"
      result: PASS|FAIL|WARN
  dissent:
    - participant: "..."
      objection: "..."
      resolution: accepted|rejected|split|deferred
  handback:
    requesting_brain: "..."
    implementation_brain: dev
    return_to_brain: "..."
  decision: accept|amend|split|escalate_to_human
```

## Procedure

1. Frame the desired state and red lines first.
2. Ask research/source tools to establish source boundaries before accepting claims.
3. Convert qualitative claims into falsifiers:
   - If claim is true, what observation/test should pass?
   - If claim is false, what counterexample would disprove it?
   - When several explanations remain live, apply `scientific-inquiry-evidence-update` to derive competing predictions and select a discriminating probe; expert agreement alone does not close the claim.
4. Route engineering gaps to dev only when an artifact is required:
   - script, CLI, connector, browser harness, API/MCP bridge, dashboard, validator, or regression test.
5. Preserve dissent; do not collapse minority warnings into a “consensus” summary.
6. Hand back to the requesting brain after dev implementation. dev does not decide domain truth.
7. Deposit durable outputs into one or more of: atom, skill, protocol, taskpool evolution task, runtime test.

## Acceptance gates

- Gate A: source/evidence is separated from model opinion.
- Gate B: at least one falsifier or verification path exists for nontrivial claims.
- Gate C: dev handback includes artifact, invocation example, verification results, limits, and return_to_brain.
- Gate D: dissent ledger exists when models/brains disagree.
- Gate E: a durable artifact or next task exists; no “analysis-only evaporation”.

## Anti-patterns

- “多模型同意，所以是真的”。
- dev replaces research/design/media/mlops judgment.
- research writes production code instead of sending a capability-gap request.
- No handback contract after cross-brain engineering.
- Model output is saved as core knowledge without source boundary and falsifier.

## Canonical references in personal brain

- `brain/03-理论与元认知/钱学森核心著作系统吸收索引.md`
- `brain/03-理论与元认知/系统工程协议/综合集成研讨厅协议.md`
- `brain/03-理论与元认知/系统工程协议/dev跨脑工程使能交还协议.md`
- `brain/04-知识原子/atoms/综合集成方法论.md`
- `brain/04-知识原子/atoms/社会系统工程三层.md`

## Common Pitfalls

1. Advancing stages without a gate, evidence artifact, or closure-state check.
2. Skipping prerequisite checks and assuming the environment already matches the workflow.
3. Reporting success before reading back the actual outputs, files, or external side effects.

## Verification Checklist

- [ ] Preconditions, scope, and tool availability were checked before following this workflow.
- [ ] The key output artifacts, commands, or side effects were verified by read-back or direct inspection.
- [ ] Any remaining uncertainty, blocker, or human handoff was stated explicitly.
- [ ] Every stage passed its gate before the next stage advanced, with evidence recorded.
