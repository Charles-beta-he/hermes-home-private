# Goal Calibration Control Plane — SSOT

Date: 2026-05-28
Scope: Hermes default behavior for human-language task intake, especially ambiguous UI/product/API/prompt/prototype requests.

## Decision

Goal calibration is a fixed high-priority internal gate, not a mandatory user-interruption step.

It must run after intent parsing and cheap read-only baseline discovery, but before planning, implementation, file writes, deployments, messages, or other side effects.

Default pipeline:

```text
User input
  -> intent parse
  -> read-only context gathering when useful
  -> goal calibration gate
  -> TaskContract
  -> plan/tool routing
  -> execute
  -> verify against TaskContract
```

## Why

Human instructions are usually goal pointers, not machine specifications. Phrases such as “align”, “optimize”, “follow prototype”, “make consistent”, “fix prompt”, “state is wrong”, or “not implemented” can hide multiple acceptance dimensions: UX, interaction, data, state, business logic, API contract, copy, prompt behavior, and verification evidence.

The failure mode to prevent is literal or structure-bound execution: treating “dropdown alignment” as CSS only, treating prototype mock fields as backend contract, or treating prompt optimization as copy polishing.

## TaskContract

Every calibrated task should leave a compact working contract:

```json
{
  "user_goal": "durable target outcome",
  "task_type": "answer | implement | debug | review | prototype_migration | prompt_optimization | ui_fix | api_design",
  "baseline": "prototype | old_version | sibling_component | design_system | live_behavior | user_examples | none",
  "success_criteria": ["observable checks"],
  "constraints": ["must not break", "scope", "style", "source of truth"],
  "ambiguity_level": "low | medium | high | critical",
  "execution_mode": "act_now | ask_once | propose_then_wait"
}
```

The contract can be implicit for trivial low-risk tasks, but must be explicit in plans, architecture advice, prompt rewrites, UI/prototype migrations, and high-risk implementation.

## Risk Policy

- Low: infer target internally and act.
- Medium: state assumption and continue, or ask one compact multiple-choice question.
- High: ask before implementation because plausible targets produce different edits.
- Critical: list intended side effects and wait for approval.

External clarification is only for ambiguity that changes the work. Do not ask “what is your goal?” for every request.

## Trigger Classes

Strong triggers:

- ambiguous or compressed human wording
- subjective verbs: align, optimize, improve, polish, fix, make right, consistent, follow prototype, same as old version
- UI/product tasks where surface wording may hide data/state/logic/contracts
- prototype, screenshot, old implementation, PRD, or competitor reference
- prompt or agent-behavior optimization
- business/API state wording: failed, success, available, visible, allowed, enabled, notification state
- high-cost or irreversible side effects
- task type changes or phase boundaries
- verification failure that suggests goal mismatch

Non-triggers / light path:

- deterministic fact queries
- arithmetic/time/system state with mandatory tool checks
- exact file/string change with no broader behavior implied
- explicit test/run/read command

## Prototype Rule

Prototypes are UX/effect specifications, not schemas. Extract observable user effects first; treat mock data fields as clues, not contracts. Copy user-perceived behavior and acceptance evidence, not the prototype’s storage/API shape unless explicitly requested.

## Prompt Rule

Prompt tasks are ambiguity tasks. Calibrate target behavior, context boundary, positive cases, negative space, output contract, failure modes, and verification. Do not optimize only for the exact sentence shown.

## Recalibration Points

Recalibrate when:

- task type changes
- baseline conflicts appear
- implementation discovers a hidden contract or state dependency
- the user corrects the target
- verification fails because the target was misread
- plan starts expanding beyond the TaskContract

Do not recalibrate on every turn if the contract still holds.

## Landing Zones

- Norm: active runtime policy for goal calibration before action.
- Skill: `goal-calibration` for detailed workflow and checklists.
- Memory: compact user preference that fuzzy human descriptions require goal calibration.
- Experience atom: public-consensus candidate for future promotion.
- Eval/reference: positive/negative trigger examples for skill routing regression.

## Verification

A landing is complete only if:

- goal-calibration skill exists and is readable
- the skill states flow position, risk policy, TaskContract, prompt/prototype rules, pitfalls, and verification
- active norm snapshot includes the goal-calibration policy
- memory contains the durable preference in compact form
- a scoped git commit records Hermes-local artifacts
- changed artifacts are read back after writing
