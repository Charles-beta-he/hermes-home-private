---
name: hermes-experience-ratchet
description: Use when capturing, validating, promoting, or reusing cross-project experience in Hermes without mutating Hermes core. Implements the dev-brain external overlay for ExperienceAtom / MemoryMaze / RatchetConsensus.
---

# Hermes Experience Ratchet

External dev-brain overlay for cross-project experience reuse.

## Trigger

Use this when a session produces reusable project knowledge, repeated project lessons, UI/backend verification patterns, red-line corrections, or a request to make future similar projects "one step to completion".

## Boundary

This is a dev-brain外挂, not Hermes core.

- Store: `~/.hermes/experience-ratchet/`
- CLI: `python3 ~/.hermes/scripts/experience-ratchet-maze.py ...`
- Skill: this file documents operation and gates
- Default policy: proposal-only; never directly writes memory, skills, profiles, taskpool, project docs, or Hermes core

Future Hermes core hooks may consume only `promoted_candidate` or `promoted` proposal artifacts and must remain default-off until separately verified.

## Objects

- `ExperienceAtom`: one reusable claim with source, evidence, applicability guards, anti-conditions, falsifiers, dissent, status, and rollback metadata.
- `MemoryMaze`: directed relations between atoms: `similar_to`, `depends_on`, `contradicts`, `supersedes`, `derived_from`, `applies_to`, `verified_by`, `falsified_by`.
- `RatchetConsensus`: append-only state machine. It can promote, deprecate, roll back, or revoke through versioned evidence; it must not physically erase contradicted experience.
- `PromotionProposal`: proposal artifact for a landing zone. Human/agent review applies the proposal later using the relevant tool/skill.

## State machine

`captured -> normalized -> challenged -> validated -> promoted_candidate -> promoted`

Side paths:

- any non-revoked state may go to `deprecated` or `revoked` with reason
- `promoted` may go to `rolled_back` with reason
- `deprecated` may return to `normalized` only with new evidence

Evidence gates:

- `validated`, `promoted_candidate`, and `promoted` require `evidence_refs`
- `promoted_candidate` and `promoted` require at least one falsifier
- `challenged`, `deprecated`, `rolled_back`, and `revoked` require a reason

## Landing-zone rules

- `skill`: reusable procedure with trigger, steps, pitfalls, verification
- `memory`: stable user/environment fact that will still matter in many sessions; avoid WIP
- `profile`: project-specific convention, red line, credential route, or verification constraint
- `taskpool`: executable future validation, extraction, replay, or automation work
- `project_doc`: repo-local ADR, API contract, architecture note, or migration decision
- `public_consensus`: cross-project rule that survived independent evidence and falsifier review
- `noop`: keep as atom only; no external write proposed

## Commands

Initialize store:

```bash
python3 ~/.hermes/scripts/experience-ratchet-maze.py init
```

Capture an atom:

```bash
python3 ~/.hermes/scripts/experience-ratchet-maze.py new   --project uvisa-admin   --claim 'Admin acceptance must use real auth and real backend data unless user explicitly allows mock.'   --pattern-type testing   --landing-zone profile   --tag frontend --tag acceptance   --applies 'admin project with login-gated pages'   --anti 'explicit user-approved mock-only prototype'   --falsifier 'if backend is unavailable and task is explicitly visual-only prototype, this should not block UI review'   --evidence 'memory:USER PROFILE real backend/mock red line'
```

Validate all atoms:

```bash
python3 ~/.hermes/scripts/experience-ratchet-maze.py validate
```

Promote through gates:

```bash
python3 ~/.hermes/scripts/experience-ratchet-maze.py transition <atom_id> normalized --reason 'deduplicated and guards added'
python3 ~/.hermes/scripts/experience-ratchet-maze.py transition <atom_id> validated --evidence 'command:pytest ...'
python3 ~/.hermes/scripts/experience-ratchet-maze.py propose <atom_id>
```

Add maze relation:

```bash
python3 ~/.hermes/scripts/experience-ratchet-maze.py relate <atom_a> contradicts <atom_b> --reason 'different auth model'
```

## Workflow

1. Capture as `captured`; do not generalize immediately.
2. For abstraction-heavy claims, load `abstraction-governance` and run scope tagging, entity stripping, pattern extraction, anti-condition/falsifier review, and landing-zone selection before promotion.
3. Normalize claim, tags, landing zone, applicability conditions, anti-conditions, and falsifiers.
4. Challenge with dissent or counterexamples before validation.
5. Validate with command/file/session/task evidence.
6. Emit proposal-only artifact for skill/profile/memory/taskpool/project_doc/public_consensus.
7. Apply the proposal using the relevant skill/tool only after reviewing blast radius.
8. If later contradicted, mark `rolled_back`, `deprecated`, or `revoked`; add relation `falsified_by` or `supersedes`.

## Verification

Run before relying on the overlay:

```bash
python3 -m py_compile ~/.hermes/scripts/experience-ratchet-maze.py
python3 ~/.hermes/scripts/experience-ratchet-maze.py init
python3 ~/.hermes/scripts/experience-ratchet-maze.py validate
```

## References

- `references/problem-pattern-registry.md` — cross-session knowledge transfer via symptom→fix registries (detect-and-report, phased implementation)
- `references/skillopt-reflact-pipeline.md` — Microsoft SkillOpt research (arXiv:2605.23904): ReflACT 6-stage pipeline for iterative skill document optimization, minibatch reflection, autonomous learning rate, meta-skill memory, slow update regions. Direct research reference for improving experience-ratchet with formal optimization loop.

## Pitfalls

- Multi-model agreement is not truth. Save it as dissent/consensus evidence, then verify.
- Do not save active task progress to memory.
- Do not promote project-specific red lines into public consensus without cross-project evidence.
- Do not direct-write to Hermes core from this overlay; proposals only.
