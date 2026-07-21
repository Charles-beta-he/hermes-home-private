---
name: agent-skill-design-patterns
description: Use when creating, auditing, classifying, or rehabilitating Agent Skills by choosing a primary design pattern such as Wrapper, Generator, Reviewer, Inversion, or Pipeline, and by checking routing, context budget, artifact contract, safety, and eval requirements.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [skills, design-patterns, skill-authoring, skill-eval, governance]
    related_skills: [hermes-agent-skill-authoring, skill-eval, abstraction-governance, spec-stateful-sdd-workflow]
---

# Agent Skill Design Patterns

## Overview

Use this skill to turn Agent Skill authoring and rehabilitation from ad-hoc prose writing into a pattern-guided control-flow design task.

Scope: reusable Agent Skill authoring and audit work in Hermes-compatible skill ecosystems.

Applicability: use when a future agent needs to classify, create, repair, or evaluate a durable skill package.

Anti-condition: do not apply this as a mandatory process to trivial one-off answers, active task progress, or project-specific facts that belong in a project profile or repo-local documentation.

Falsifier: narrow or revise this skill if pattern labels do not improve routing precision, body structure, artifact verification, or maintainability during real skill audits.

Core formula:

```text
Skill = Routing Contract + Patterned Control Flow + Progressive Context + Artifact Contract + Evidence/Eval Gate
```

The five foundational patterns are:

1. **Wrapper** — expose an external capability safely.
2. **Generator** — produce a stable artifact.
3. **Reviewer** — judge an artifact or decision against a rubric.
4. **Inversion** — elicit/obey external constraints instead of guessing.
5. **Pipeline** — advance ordered stages with gates and evidence.

These are primary control-flow modes, not mutually exclusive categories. A skill may have secondary modes, but one dominant pattern should shape the SKILL.md body.

For the full evidence-backed theory and adoption plan, see the private SSOT document `agent-skill-design-patterns-ssot-20260607.md`.

## When to Use

Use when:

- Creating a new Hermes or Agent Skills `SKILL.md`.
- Auditing whether an existing skill is bloated, misrouted, weakly verified, or structurally confused.
- Deciding whether a capability belongs in `references/`, `templates/`, `scripts/`, or the root `SKILL.md`.
- Classifying a skill library into capability modules.
- Refactoring a README-like skill into an actionable skill contract.
- Adding eval prompts after changing a skill `description` or trigger boundary.

Don't use for:

- Simple one-off answers with no durable skill implication.
- Pure theory writing with no executable skill-authoring decision; use docs/private instead.
- Active task progress or temporary state; use task/session/taskpool surfaces.
- Project-specific facts that belong in a project profile or repo-local docs.

## Pattern Selection Decision Tree

Ask in order:

1. **Does the skill mainly expose an external tool/API/platform/system?**
   - Use **Wrapper**.
2. **Does it mainly produce a stable artifact?**
   - Use **Generator**.
3. **Does it mainly judge an artifact, decision, implementation, or evidence set?**
   - Use **Reviewer**.
4. **Does it mainly prevent guessing by eliciting constraints, seeking falsifiers, reversing perspective, or letting tests/evidence/user/environment drive behavior?**
   - Use **Inversion**.
5. **Does it mainly coordinate ordered stages with gates/evidence?**
   - Use **Pipeline**.
6. **If none dominate**, check adjacent modes: Router, Planner, Memory/Retrieval, Monitor/Watchdog, Guardrail/Policy, Arbiter/Consensus, Evaluator/Benchmark. Do not force-fit if an adjacent mode is honestly dominant.

Record both:

```yaml
primary_pattern: wrapper|generator|reviewer|inversion|pipeline|adjacent
secondary_patterns: []
```

## Pattern 1 — Wrapper

### Use when

- The skill's main job is to expose a CLI, API, MCP server, SDK, local app, platform, or operational surface.
- Auth, permissions, side effects, version drift, or exact commands matter.

### Body shape

```text
Overview
When to Use
Preconditions
Invocation Contract
Safety Gates
Verification
Failure Modes
Common Pitfalls
```

### Must include

- Required commands/tools/auth state.
- Which actions are read-only vs side-effecting.
- What requires human confirmation.
- How to read back target state after a mutation.
- Redaction rule for secrets and credentials.

### Common pitfalls

1. Copying API docs into SKILL.md instead of linking `references/`.
2. Reporting command success without target-state read-back.
3. Letting prompt-injection content from external payloads become instructions.
4. Auto-executing destructive or external side effects without a gate.

### Verification

- Command exit code plus target status/get/list read-back.
- Dry-run or sandbox for destructive paths.
- Schema validation for API responses when possible.

## Pattern 2 — Generator

### Use when

- The skill's main job is to produce a stable document, code file, config, report, diagram, spec, task packet, or evidence bundle.
- Downstream humans/tools/agents expect a predictable structure.

### Body shape

```text
Overview
When to Use
Input Schema
Output Contract
Template / Example Reference
Quality Bar
Verification
Common Pitfalls
```

### Must include

- Required inputs and defaultable inputs.
- Output fields or template location.
- Non-goals and forbidden additions.
- Verification commands or structure checks.

### Common pitfalls

1. Generating plausible text with no artifact contract.
2. Over-generating beyond user scope.
3. Producing code/config without running it.
4. Letting output structure drift between runs.

### Verification

- Template/schema conformance.
- Read-back of written files.
- Build/lint/typecheck/test for executable artifacts.
- Requirement coverage matrix for specs/plans.

## Pattern 3 — Reviewer

### Use when

- The skill's main job is quality judgment, audit, certification, critique, or gatekeeping.
- It should produce findings, severity, and pass/warn/fail results rather than directly implement the main artifact.

### Body shape

```text
Overview
When to Use
Review Dimensions
Severity Rubric
Evidence Requirements
Output Format
False Positive Controls
Verification Checklist
```

### Must include

- Review dimensions.
- Blocker/warning/suggestion boundary.
- Evidence requirements for each claim.
- What the review cannot prove.

### Common pitfalls

1. Generic critique with no file/source/evidence anchors.
2. Treating preference as blocker.
3. Treating model agreement as proof.
4. Failing to separate compliance review from quality suggestions.

### Verification

- Golden defect cases where available.
- Evidence-citation check.
- Severity calibration.
- Downstream fix success when the review drives remediation.

## Pattern 4 — Inversion

### Use when

- The request is ambiguous and guessing would risk wrong work.
- The agent must ask focused questions, seek falsifiers, obey tests, or reason from another role's perspective before acting.
- Human preference, acceptance, domain context, external evidence, or test results materially changes the output.

### Body shape

```text
Overview
When to Use
Minimal Question Set
Defaultable vs Non-defaultable Inputs
Branching / Perspective Rules
Stop Conditions
Synthesis into Spec or Decision
Verification Checklist
```

### Must include

- The smallest useful question set.
- Which ambiguities block work and which can use defaults.
- When to stop asking and proceed.
- How answers become a spec, brief, decision, or gate.

### Common pitfalls

1. Asking broad low-value questions.
2. Asking too many questions and blocking recoverable work.
3. Guessing non-defaultable requirements.
4. Never compiling answers into actionable form.
5. Using Inversion as a junk drawer for unclear skills.

### Verification

- Ambiguous prompt cases.
- No-unnecessary-question cases.
- Answer-to-spec coverage.
- Human gate correctness for high-risk forks.

## Pattern 5 — Pipeline

### Use when

- The skill coordinates multiple stages, tools, subagents, or evidence gates.
- Intermediate artifacts must be compatible and recoverable.
- Closure requires explicit proof or acceptance state.

### Body shape

```text
Overview
When to Use
Stages
Inputs / Outputs per Stage
Gates
Evidence Requirements
Failure / Retry / Rollback
Closure States
Learning Writeback
```

### Must include

- Stage list and no-skip rule.
- Stage input/output contracts.
- Gate conditions before advancing.
- Failure/retry/rollback behavior.
- Closure states: done, waiting_acceptance, blocked, rolled_back, superseded.

### Common pitfalls

1. Checklist without gates.
2. Skipping prerequisite discovery.
3. Letting early wrong assumptions propagate.
4. Infinite Generator/Reviewer repair loops.
5. Losing state across context compression.

### Verification

- Stage-level postconditions.
- End-to-end trace.
- Evidence ledger tied to acceptance criteria.
- Closure-state proof.

## Context Budget Rule

Every skill has three cost layers:

1. **Index layer** — `name` + `description`.
   - Paid in every session.
   - Must answer when to load, not summarize the whole workflow.
2. **Load layer** — root `SKILL.md`.
   - Paid after loading.
   - Keep branch conditions, pitfalls, gates, and verification.
3. **Runtime layer** — `references/`, `templates/`, `scripts/`, `assets/`.
   - Paid only when read or executed.
   - Put long theory, examples, templates, deterministic scripts, and rare branches here.

Heuristic: if SKILL.md reads like a README, split it.

## Artifact Contract Checklist

For any non-trivial skill, answer:

```yaml
artifact_contract:
  consumes:
    - user prompt
    - files/apis/events/etc
  produces:
    - report/spec/code/config/side effect/etc
  verifies:
    - command/test/schema/read-back/human acceptance/etc
  cannot_prove:
    - remaining uncertainty
```

If a skill produces nothing verifiable, label it advisory and avoid using it as a completion gate.

## Safety Gate Checklist

Especially for Wrapper, Inversion, and Pipeline skills:

- Does the skill touch external systems?
- Can it delete, overwrite, send, deploy, pay, close, publish, or control devices?
- Does it process untrusted external payloads?
- Is the operation recoverable?
- Is human confirmation required?
- What read-back proves the side effect happened as intended?

## Routing Eval Minimum

When creating a new skill or changing `description`, define at least:

- 3 positive prompts: should load this skill.
- 2 neighbor prompts: should load a nearby skill instead.
- 2 forbidden prompts: must not load this skill.
- 1 no-load prompt: should remain general reasoning.

Use `evals/prompts.csv` as the canonical skill-eval prompt set. `references/pattern-routing-evals.csv` is kept as a readable reference copy.

## Skill Rehabilitation Procedure

For post-session library updates, prefer class-level maintenance over one-session skill creation: patch a loaded skill first, then an existing umbrella, then add a support file, and create a new class-level skill only if no umbrella fits. See `references/post-session-skill-update-triage.md` for the detailed triage rule.

1. **Inspect trigger surface**
   - Does `description` state when to load?
   - Is it too broad or too narrow?
2. **Classify primary pattern**
   - Wrapper, Generator, Reviewer, Inversion, Pipeline, or adjacent.
3. **Compare body shape**
   - Does the section layout match the primary pattern?
4. **Check context budget**
   - Move long theory/examples to `references/`.
   - Move stable output shapes to `templates/`.
   - Move deterministic actions to `scripts/`.
5. **Add artifact/evidence contract**
   - What does it consume, produce, verify, and not prove?
6. **Add eval prompts for routing changes**
   - Especially negative and neighbor cases.
7. **Read back and verify**
   - Re-open the skill.
   - Check frontmatter, section shape, linked files, and eval references.

## Adjacent Mode Escape Hatch

Do not force every skill into the five foundational patterns. Use an adjacent primary mode if one of these is clearly dominant:

- **Router / Dispatcher** — selecting skill/tool/model/subagent is the main job.
- **Planner / Decomposer** — task breakdown/dependency modeling is the main job.
- **Memory / Retrieval / Contextualizer** — context selection from history/docs is the main job.
- **Monitor / Watchdog** — event/threshold observation is the main job.
- **Guardrail / Policy** — permission/safety enforcement is the main job.
- **Arbiter / Consensus** — conflict resolution across reviewers/models is the main job.
- **Evaluator / Benchmark** — regression testing skill behavior is the main job.

When using an adjacent mode, still apply routing, context budget, artifact contract, safety, and eval checks.

## Common Pitfalls

1. Treating design patterns as a rigid ontology instead of a practical control-flow vocabulary.
2. Creating a new skill for pure theory that belongs in docs/private.
3. Batch-rewriting skill descriptions with a script; description is routing logic.
4. Letting an umbrella skill steal routing from narrower skills.
5. Calling a skill “Pipeline” when it has no stage gates or evidence.
6. Calling a skill “Reviewer” when it has no rubric or severity boundary.
7. Calling a skill “Wrapper” when it has no side-effect safety/read-back rule.
8. Calling a skill “Generator” when it has no output contract.
9. Calling a skill “Inversion” when it merely asks generic questions.
10. Treating multi-model consensus as evidence instead of advisory signal.

## Verification Checklist

- [ ] The skill or candidate skill has one primary pattern and optional secondary patterns.
- [ ] The `description` is a routing trigger, not a mini README.
- [ ] The root body shape matches the primary pattern.
- [ ] Long/conditional content is moved to references/templates/scripts as appropriate.
- [ ] Artifact contract says what is consumed, produced, verified, and not proven.
- [ ] Safety gates exist for side-effecting or untrusted-input paths.
- [ ] Routing eval prompts include positive, neighbor, forbidden, and no-load cases.
- [ ] The final skill was read back after changes.

## Skill Library Coverage Audit

Detailed `Skill Library Coverage Audit` guidance moved to `references/skill-library-coverage-audit.md`.

Load it when this subproblem is directly active. Minimum in-root rule: preserve the current skill's safety/verification boundaries and read the reference before executing this specialized branch.
## References

- Private SSOT: `docs/private/agent-skill-design-patterns-ssot-20260607.md`.
- `references/pattern-matrix.md` — compact comparison matrix and body-shape guide.
- `references/full-library-routing-eval-coverage.md` — full-library eval generation workflow, including manifest verification and nested git/submodule handling.
- `references/post-session-skill-update-triage.md` — class-level triage rule for post-session skill-library updates.
- `references/qianwen-google-cloud-agent-workflow-intake.md` — user-accepted intake from Qianwen/Google Cloud Agent workflow lesson: main-agent/subagent/skill mapping, review-loop boundary, UI visual-diff lane, and poor-man dynamic workflow lane.
- `references/qianwen-ai-workflow-local-model-fullstack-intake.md` — user-shared Qianwen intake for local/offline model fallback, three-stage init/prd/ai workflow, feature/task granularity, context reset, SubAgent-vs-Skill split, bounded review, full-stack closure, and visual workflow observability.
- `references/qianwen-swarm-router-workflow-dsl-intake.md` — user-shared Qianwen intake for Swarm-style flat multi-agent teams, adaptive task router, judgement/orchestration separation, adversarial verification, learning loop, PII/secret outbound filter, evidence arbitration, and JS/Python workflow DSL abstraction.
- `references/public-loop-catalog-agent-patterns-intake.md` — class-level intake for public AI-agent loop catalogs: verify artifacts outside media posts, adapt loop families as bounded evidence workflows, and avoid one-session-one-skill proliferation.
- `references/openai-codex-plugin-cc-intake.md` — evidence-backed intake from OpenAI's Codex plugin for Claude Code: thin model wrappers, deterministic runtime adapters, route-specific authority, structured review contracts, exact-slice stop gates, background-job lifecycle, shared-broker health, argv/shell safety, and session-transfer boundaries.
- `evals/prompts.csv` — canonical routing eval prompt set for skill-eval.
- `references/pattern-routing-evals.csv` — readable reference copy of the starter routing eval prompts.
- `scripts/scan_skill_pattern_coverage.py` — non-mutating coverage scanner for existing skill libraries.
- `scripts/generate_skill_routing_evals.py` — contract-layer bulk helper that creates canonical `evals/prompts.csv` matrices without rewriting skill descriptions or bodies.
