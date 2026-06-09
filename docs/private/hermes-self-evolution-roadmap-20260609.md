# Hermes self-evolution roadmap — 2026-06-09

schema: hermes_self_optimization_ssot_v1
id: hermes-self-evolution-roadmap-20260609
source: Telegram user authorization on 2026-06-09 after discussion of current evolution directions
status: low-risk process landing complete; engineering work candidates require normal taskpool/code gates

## Authorization snapshot

User认可方向并授权："全盘推进直至边界或需要人工介入"。

Scope granted in this turn:
- Land low-risk Hermes process/skill improvements immediately.
- Classify durable learning into the right boundary: skill, SSOT doc, taskpool candidate, do-not-do.
- Stop before high-blast-radius runtime behavior changes, destructive cleanup, broad config mutation, or external side effects that require a separate implementation plan and verification.

## Objective and cost function

Objective:
- Evolve Hermes from answer generator into an evidence-bound personal engineering control plane.
- Preserve user preferences: evidence-first, real verification, no mock acceptance, no feature loss, no global pollution from local context, and scoped auditable self-changes.

Cost function to minimize:
- Unsupported claims and fabricated proof.
- Repeated user steering for stable workflow boundaries.
- Over-broad memories or skills that freeze transient session facts.
- High-blast-radius code/config changes without SSOT, tests, and rollback path.
- Taskpool noise from vague improvement ideas.

Hard constraints:
- One SSOT artifact controls this self-optimization: this file.
- Skills encode reusable procedure only; this file records evidence/decisions.
- Do not mutate Hermes runtime code/config from this roadmap without a follow-up implementation SSOT, focused tests, and scoped commit.
- Do not enqueue vague future work; taskpool items must have target, artifact, risk, dependency, and verification.

## World model

Key components:
- Chat/TG entrypoint: active human intent and authorization.
- Skills: reusable procedural memory loaded by future sessions.
- Memory: compact stable user/environment facts only; not used for this roadmap because the relevant preferences already exist.
- Taskpool/control-plane: execution ledger for concrete engineering work; not the place for broad ideology.
- Git: audit boundary for Hermes self-modifications.
- Evidence gates: files read/written, skill readback, git status/diff, focused validation.

Dynamic risks:
- Self-evolution requests tend to sprawl across memory, skill, taskpool, docs, and code.
- Existing `~/.hermes` worktree is very dirty; scoped staging is mandatory.
- Creating broad behavior rules can overfit one conversation and degrade ordinary simple tasks.

## Candidate paths considered

### Path A — Memory-only preference update
Prediction: low effort, but wrong landing zone. The user preferences already contain the relevant directives, and adding more memory risks global imperative pollution.
Decision: rejected.

### Path B — New narrow skill plus SSOT doc
Prediction: captures reusable procedure with explicit triggers/counter-triggers, keeps evidence and decisions in one doc, low blast radius, easy to verify.
Decision: selected for immediate landing.

### Path C — Direct Hermes runtime/taskpool code changes
Prediction: potentially valuable but too high blast radius for a chat-derived methodology without implementation SSOT, focused tests, and multi-model/code review.
Decision: blocked as future candidate work only.

### Path D — Enqueue several taskpool evolution items immediately
Prediction: may be useful, but taskpool add hooks can mutate status and create noise unless each item is concrete and deduped against existing backlog.
Decision: list candidates here; enqueue only after explicit taskpool intake/dedup pass or if future request asks to convert candidates to tasks.

## Immediate landing decision

Create a reusable skill:
- name: `objective-model-path-verification`
- category: `software-development`
- purpose: trigger a compact world-model-inspired gate for complex/high-risk tasks.
- boundary: not for simple Q&A; not a replacement for real tool execution; not proof of correctness.

## Taskpool / engineering candidates

These are candidates, not queued work in this landing:

1. Complex-task gate integration
   - Target: Hermes prompt/runtime task classifier or pre-action planning layer.
   - Artifact: default-off gate that asks for objective/cost/model/path/verification before high-risk tool execution.
   - Risk: over-triggering and token bloat.
   - Dependencies: define trigger classifier, compression mode, bypass/counter-trigger rules.
   - Verification: focused unit tests for trigger/counter-trigger cases plus dogfood on real coding task.

2. Evidence spine normalization
   - Target: taskpool evidence schema and final-response templates.
   - Artifact: canonical `claim -> evidence -> risk -> next step` envelope shared by chat/taskpool/closeout.
   - Risk: duplicating existing evidence/proof-debt mechanisms.
   - Dependencies: audit current taskpool evidence fields first.
   - Verification: closeout tests must fail when evidence is missing and pass with real command/file/UI proof.

3. Self-evolution boundary audit automation
   - Target: bg-review or post-session self-review.
   - Artifact: automatic classification into memory/skill/experience-ratchet/taskpool/do-not-do, in suggest mode by default.
   - Risk: silent mutation if suggest/enqueue boundary is blurred.
   - Dependencies: reuse `agent-boundary-audit` skill and existing bg-review suggest-mode rules.
   - Verification: dry-run transcript fixtures showing no memory writes or taskpool enqueue unless explicitly authorized.

4. Multi-model role routing for self-evolution
   - Target: consult_models / taskpool multimodel certification.
   - Artifact: role-specific panels: code implementer, architecture arbiter, reviewer, external evidence gate.
   - Risk: treating model consensus as truth.
   - Dependencies: evidence bundle support and quorum degradation semantics.
   - Verification: degraded provider path remains `degraded_not_certified`; unsupported claims cannot promote runtime changes.

## Do-not-do boundaries

- Do not claim Hermes runtime behavior changed from this landing; only the skill/process doc changed.
- Do not save this roadmap as memory; it is a scoped self-optimization artifact.
- Do not mutate core code/config from this methodology without a new implementation SSOT and tests.
- Do not enqueue taskpool work until deduped and shaped as concrete tasks.
- Do not treat LeCun/JEPA/world-model wording as evidence of technical implementation.

## Verification log

- Read controlling SSOT rule: `/Users/charles/.hermes/docs/private/hermes-self-optimization-ssot-20260526.md`.
- Existing skill search for world-model/objective-path terms returned no direct match.
- Created and read back skill: `/Users/charles/.hermes/skills/software-development/objective-model-path-verification/SKILL.md`.
- Classified engineering follow-ups as candidates only; no taskpool enqueue performed in this landing because dedupe/intake gates were not run.

## Final report checklist

- Name this SSOT path in final response.
- Name changed skill path and readback verification.
- Report git scoped commit hash or explain why not committed.
- Report candidates as not queued unless separately enqueued.
