# Agent Optimization Absorption Protocol

Scope: Hermes self-optimization, user corrections, reusable workflow lessons, and requests to make future agent behavior better. This is not for task progress, artifact IDs, secrets, one-off state, or unverified model opinions.

## Rule

When a user offers an optimization item, do not absorb it as a vague global instruction. First convert it into a scoped structure:

```text
Trigger scenario: when does this apply?
Boundary: what A must not be confused with B?
Correct action: what should the agent check or do?
Evidence requirement: what proves the claim or completion?
Scope: user / global / project / repo / domain / session / task?
Anti-condition: when is this wrong or overbroad?
Landing zone: memory / skill / project profile / ADR / gate / script / experience-ratchet proposal / noop?
Falsifier: what would demote, narrow, or revoke it?
```

## Landing-zone classifier

- Stable user preference or red line -> compact declarative user memory.
- Stable environment fact -> memory only if cross-session and not task state; otherwise scoped profile/docs.
- Reusable procedure -> skill or skill reference.
- Project-specific constraint or business ontology -> project profile, SSOT, ADR, or repo docs.
- Evidence/acceptance standard -> skill checklist, project profile, test, or gate.
- Failure mode/debug pattern -> skill, support reference, or experience-ratchet atom.
- Candidate cross-project lesson needing validation -> experience-ratchet proposal first.
- Runtime safety/control invariant -> gate/script/test after exact authority and verification.
- Secrets, credentials, current progress, ephemeral artifacts -> do not save.

## Self-test example

User item: “以后遇到【场景】，不要把【A】当成【B】；应先检查【证据】；适用于【范围】；例外是【反例】；沉淀到【落点】。”

Absorbed structure:

- Trigger scenario: user proposes an agent optimization or correction.
- Boundary: optimization intent is not automatically durable memory or global policy.
- Correct action: run scope tagging, evidence gate, anti-condition/falsifier review, and landing-zone selection.
- Evidence requirement: source statement plus readback of the chosen durable artifact or proposal.
- Scope: Hermes self-optimization workflow; narrower project facts stay project-scoped.
- Anti-condition: current task progress, secrets, one-off state, unverified model opinions, or local facts pretending to be global.
- Landing zone: this skill reference plus an experience-ratchet proposal for review.
- Falsifier: if the item lacks trigger/evidence/scope/anti-condition/landing zone, keep it session-local or ask for clarification.

## Verification checklist

- The candidate has trigger, boundary, evidence, scope, anti-condition, landing zone, and falsifier.
- Local entities are stripped or explicitly scoped.
- Durable writes avoid task progress and secrets.
- The chosen artifact is read back after writing.
- Experience-ratchet validation passes when an atom/proposal is created.
