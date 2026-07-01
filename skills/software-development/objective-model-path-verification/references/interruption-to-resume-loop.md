# Interruption-to-Resume Loop

Use this reference when a task is meant to be driven to a real close-loop outcome but encounters a human-intervention boundary, disagreement point, or full-landing interruption.

## Class-level lesson

Do not model human intervention as a conversational pause. Model it as a recoverable, authorized, evidence-gated state transition:

```text
Observe → Model/Plan → Act → Verify → Decide/Hold → Resume → Learn/Ratchet
```

The failure mode to prevent is:

```text
safe work stops too early OR hard gates are bypassed because the model/multi-model panel agrees.
```

## Required objects

### DecisionPacket

Use for the human decision itself:

- objective/current goal
- blocker class
- options with consequences
- recommendation and rationale
- current state and evidence
- required authority scope
- rollback/escape hatch
- post-action verification
- linked continuation/resume state

### ContinuationPacket

Use for recoverability:

- original objective and success criteria
- completed work with evidence
- remaining work
- exact blocker class
- next action after authorization
- preconditions to resume
- verification after resume

### AuthorityGrant

Use for scoped human authorization. Keep it separate from model output:

- granted actions
- forbidden actions
- scope/environment/task boundary
- expiry/budget if applicable
- evidence of the human decision

## Gate classification

Hard human gates must not be bypassed by model consensus:

- authorization
- credential/secret entry
- production write/deploy
- destructive change/delete
- external publish/send/push
- payment/spend/quota-consuming purchase
- safety/legal risk
- value judgment/product-direction conflict

Low-risk auto-resume candidates:

- read-only lookup
- local reversible edit
- local verification/test
- fact gathering
- dry-run/proof generation

## Multi-model role

Multi-model review is advisory. It can improve options, risks, evidence requests, and recommendations, but it is not:

- a fact source without evidence;
- a human authorization;
- permission to cross hard gates;
- completion proof.

If models disagree, classify disagreement first:

- factual dispute → gather evidence;
- implementation dispute → prefer reversible, verified path;
- risk/authority dispute → hard gate or DecisionPacket;
- value dispute → human decision.

## Verification checklist

A future implementation should be tested with fixtures that prove:

1. external publish/production/destructive gates return `hold_for_human` without AuthorityGrant even when model reviews recommend continuing;
2. matching AuthorityGrant permits only the explicitly allowed actions;
3. forbidden actions remain blocked even after partial authorization;
4. local reversible/read-only/verification gates can auto-resume when evidence is present;
5. interruption output includes both DecisionPacket-style human gate and ContinuationPacket-style resume state;
6. completion still requires real evidence, not a model statement.

## Applicability / anti-conditions

Applicable to agent/runtime/control-plane, taskpool, mission, and long-running workflow work where the user asks for full landing, automatic continuation, or stop-only-at-real-gates behavior.

Do not use this to justify crossing production, credential, destructive, payment, external publish, or safety/legal boundaries without explicit human authority.
