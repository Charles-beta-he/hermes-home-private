# Agent Skill Design Patterns SSOT

Date: 2026-06-07
Owner: Hermes Agent / default profile
Status: v1 adopted for Hermes skill-library governance

## Executive thesis

Agent Skill design patterns are not prompt templates. They are recurring control-flow shapes for packaging agent capabilities as routable, progressively loaded, evidence-aware, and evolvable skill modules.

Core formula:

```text
Skill = Routing Contract + Patterned Control Flow + Progressive Context + Artifact Contract + Evidence/Eval Gate
```

The five foundational patterns are:

1. Wrapper — adapt external capability.
2. Generator — produce stable artifact.
3. Reviewer — judge artifact or decision against a rubric.
4. Inversion — make the agent elicit/obey external constraints instead of guessing.
5. Pipeline — advance ordered stages with gates and evidence.

These five are a pragmatic foundation, not a closed ontology. Hermes should use them as primary control-flow modes, allow secondary modes, and separately track router/memory/planner/monitor/guardrail/arbiter/evaluator capabilities when those become dominant.

## Source and evidence ledger

### E1 — Anthropic Claude Code Skills

Source: https://docs.anthropic.com/en/docs/claude-code/skills
Retrieved with tool output in this session.

Evidence excerpts from the fetched page:

- “Skills extend what Claude can do. Create a SKILL.md file with instructions, and Claude adds it to its toolkit.”
- “Claude uses skills when relevant, or you can invoke one directly with /skill-name.”
- “Create a skill when you keep pasting the same instructions, checklist, or multi-step procedure into chat, or when a section of CLAUDE.md has grown into a procedure rather than a fact.”
- “Unlike CLAUDE.md content, a skill’s body loads only when it’s used, so long reference material costs almost nothing until you need it.”
- “Skills add optional features: a directory for supporting files, frontmatter to control whether you or Claude invokes them, and the ability for Claude to load them automatically when relevant.”
- “Claude Code skills follow the Agent Skills open standard.”
- Claude Code extends skills with “invocation control, subagent execution, and dynamic context injection.”
- Frontmatter `description` is used by Claude “to decide when to apply the skill.”

Claims supported:

- A skill is a routable capability unit, not always-on global context.
- `description` is a routing surface.
- Progressive loading is intrinsic to the format.
- Supporting files and execution controls are first-class design surfaces.

Claims not proven:

- The exact five-pattern taxonomy is not asserted by Anthropic; it is a Hermes synthesis.

### E2 — Vercel Labs / Agent Skills ecosystem

Source: https://raw.githubusercontent.com/vercel-labs/skills/main/README.md
Retrieved with tool output in this session.

Evidence excerpt:

- “Agent skills are reusable instruction sets that extend your coding agent's capabilities.”
- Skills are defined in `SKILL.md` files with YAML frontmatter containing `name` and `description`.
- Example capability classes include generating release notes, creating PRs following team conventions, and integrating with external tools.
- The CLI targets multiple agents, including Claude Code, Codex, Cursor-like and other harnesses.

Claims supported:

- Skills are portable reusable instruction packages.
- Skills span generation, workflow convention, and external-tool integration.
- Multi-harness portability should be considered in Hermes skill governance.

Claims not proven:

- Cross-harness behavior equivalence. Hermes must verify behavior in its own runtime.

### E3 — Agent Skills documentation index

Source: https://agentskills.io/llms.txt
Retrieved with tool output in this session.

Evidence excerpt:

- The docs include dedicated pages for “Writing effective skills”, “Evaluating skill output quality”, “Optimizing skill descriptions”, “Using scripts in skills”, and the “Specification”.

Claims supported:

- Skill quality includes authoring, description optimization, eval-driven iteration, scripts, and formal specification.
- The discipline is broader than prompt writing.

### E4 — Hermes current skill-authoring/eval skills

Local skills loaded in this session:

- `hermes-agent-skill-authoring`
- `skill-eval`
- `spec-stateful-sdd-workflow`
- `abstraction-governance`

Claims supported by local skill contracts:

- Description changes are routing changes.
- Context has index/load/runtime cost layers.
- SKILL.md is an entry contract.
- Mature skills should be evaluated with positive, neighbor, forbidden, and no-load prompts.
- Durable lessons need the right landing zone; theory belongs in docs/private, executable procedure in skill, temporary progress outside memory.

## Abstraction boundary

This document is a theory and governance SSOT. It should not itself be injected into every task. The executable subset is captured in the `agent-skill-design-patterns` skill.

Landing-zone decision:

- docs/private: the full theory, evidence, taxonomy, anti-conditions, and long-term governance rationale.
- skill: concise procedure for classifying, creating, auditing, and rehabilitating skills using the five patterns.
- memory: no write. This is not a user preference and not a stable personal fact beyond already-known preferences.
- taskpool: only future implementation/audit work if explicitly queued.
- experience-ratchet: candidate if repeated future runs falsify or extend the taxonomy.

## The five foundational patterns

### 1. Wrapper Pattern

Definition:

A Wrapper skill exposes an external capability, API, CLI, SDK, MCP server, local app, platform, or operational surface through a safe agent-facing protocol.

Canonical shape:

```text
SKILL.md -> prerequisites / capability map / safety boundary -> tool or script -> read-back verification
```

Use when:

- The task depends on a specific external tool or platform.
- The agent must avoid guessing API/CLI behavior from memory.
- Side effects, credentials, permissions, or version drift matter.

Typical artifacts:

- command output
- API response
- config file
- external object ID or URL
- read-back status
- audit log

Required sections:

- Preconditions
- Invocation contract
- Safety gates
- Verification
- Failure modes
- Redaction policy for secrets

Failure modes:

- tool unavailable
- auth/permission drift
- CLI/API version drift
- stdout success but target state unchanged
- dangerous external side effect without gate
- prompt-injection content in external payload treated as instruction

Verification patterns:

- status/get/list read-back after mutation
- schema validation
- sandbox integration where possible
- exit code plus target-state check
- dry-run before destructive paths

Hermes examples:

- GitHub PR workflow
- MCP integration
- email/gateway/Telegram setup
- Cloudflare/Vercel deployment
- Apple Notes/Reminders wrappers

### 2. Generator Pattern

Definition:

A Generator skill transforms inputs and constraints into a stable artifact with a declared structure.

Canonical shape:

```text
inputs + constraints + template -> artifact -> format/coverage verification
```

Use when:

- The output format should be repeatable.
- The artifact will be consumed by a human, tool, pipeline, or later agent step.
- Drift in structure would make downstream work unreliable.

Typical artifacts:

- spec packet
- ADR
- PRD
- report
- code file
- config
- test plan
- diagram
- evidence bundle

Required sections:

- Input schema
- Output schema or template
- Non-goals and forbidden additions
- Quality bar
- Examples or template reference
- Verification checklist

Failure modes:

- plausible but unverifiable output
- output format drift
- over-generation beyond scope
- missing required field
- generated code/config not executed
- style mismatch with project conventions

Verification patterns:

- schema check
- lint/typecheck/build/test
- template conformance
- requirement coverage matrix
- read-back of written artifact

Hermes examples:

- spec packet generation
- evidence bundle generation
- ADR/report templates
- UI/design deliverable templates

### 3. Reviewer Pattern

Definition:

A Reviewer skill evaluates an existing artifact, plan, decision, implementation, or evidence set against an explicit rubric and returns pass/warn/fail findings.

Canonical shape:

```text
input artifact -> rubric + evidence lookup -> graded report -> gate decision
```

Use when:

- The main value is judgment rather than production.
- A closure, merge, release, or acceptance claim needs independent scrutiny.
- Multi-model or second-pass critique is helpful but must remain evidence-bound.

Typical artifacts:

- review report
- issue list
- risk register
- severity-ranked findings
- pass/warn/fail gate
- certification packet

Required sections:

- Review dimensions
- Severity rubric
- Blocker/warning/suggestion boundary
- Evidence requirements
- False-positive controls
- Output format

Failure modes:

- generic critique without evidence
- preference treated as blocker
- missed runtime behavior
- model opinion treated as proof
- infinite generator/reviewer loop

Verification patterns:

- known-defect/golden issue set
- evidence citation check
- severity calibration
- downstream fix-success check
- second reviewer only for quality, not as fact proof

Hermes examples:

- code review
- skill quality audit
- UI/accessibility audit
- multi-model certification
- evidence sufficiency review

### 4. Inversion Pattern

Definition:

An Inversion skill changes the default control relationship: instead of the agent guessing and producing immediately, it elicits constraints, lets tests/evidence/user/environment drive behavior, or adopts a required external perspective before acting.

Canonical shape:

```text
ambiguous goal or external signal -> constraint elicitation / role inversion / falsifier search -> compiled spec or decision
```

Use when:

- Requirements are under-specified.
- The risk of guessing exceeds the cost of asking.
- Human preference, acceptance, domain context, or external evidence changes the task materially.
- The agent must think from the reviewer/user/adversary/test/environment perspective.

Subtypes:

- Inquiry inversion: agent interviews the user.
- Perspective inversion: agent adopts user/reviewer/adversary/operator view.
- Evidence inversion: agent seeks falsifiers before conclusion.
- Test inversion: tests/spec drive implementation.
- Responsibility inversion: agent routes to human/subagent/tool for a constraint it cannot infer.

Required sections:

- Minimal question set
- Which questions can be defaulted
- Which cannot be defaulted
- Stop conditions
- Synthesis into spec/brief/gate
- Anti-annoyance rule to avoid over-questioning

Failure modes:

- asking too many low-value questions
- asking vague questions
- pretending ambiguous inputs are clear
- never compiling answers into an actionable spec
- using inversion as a junk drawer for unclassified skills

Verification patterns:

- ambiguity-case evals
- answer-to-spec coverage
- no-unnecessary-question eval
- risk-gate correctness

Hermes examples:

- design intake before prototype
- goal calibration
- career/product strategy intake
- spec-stateful SDD G0/G1 gates

### 5. Pipeline Pattern

Definition:

A Pipeline skill advances a task through ordered stages where each stage has inputs, outputs, gates, evidence, and failure handling.

Canonical shape:

```text
stage_0 context -> stage_1 spec -> stage_2 plan -> stage_3 execute -> stage_4 review -> stage_5 verify -> stage_6 close -> stage_7 ratchet
```

Use when:

- The task spans multiple steps, files, systems, or sessions.
- Completion depends on evidence at intermediate stages.
- The workflow needs recovery, rollback, or handoff.

Typical artifacts:

- spec packet
- task packets
- intermediate files
- evidence ledger
- decision log
- closure state
- ratchet proposal

Required sections:

- Stage list
- Inputs/outputs per stage
- Gate conditions
- Evidence requirements
- Retry/rollback policy
- Closure states
- Learning writeback rule

Failure modes:

- checklist without gates
- skipped prerequisite discovery
- incompatible intermediate artifact
- early mistake propagated downstream
- state lost across context compression
- cost explosion from unbounded loops

Verification patterns:

- stage-level postconditions
- end-to-end scenario run
- artifact compatibility checks
- trace completeness
- closure-state proof

Hermes examples:

- spec-stateful SDD
- TDD implementation
- deployment flow
- research synthesis flow
- skill library rehabilitation pass

## Non-foundational but important adjacent patterns

The five-pattern taxonomy is intentionally compact. It does not fully cover these adjacent dominant behaviors:

| Adjacent mode | When it should become primary | Relationship to five patterns |
|---|---|---|
| Router / Dispatcher | selecting skill/tool/model/subagent is the main job | often wraps the five patterns |
| Planner / Decomposer | task breakdown/dependency modeling is the main job | often precedes Pipeline |
| Memory / Retrieval / Contextualizer | context selection from history/docs is the main job | often supports Generator/Reviewer/Pipeline |
| Monitor / Watchdog | event/threshold observation is the main job | overlaps Wrapper + Inversion + Pipeline |
| Guardrail / Policy | permission/safety enforcement is the main job | stricter than Reviewer |
| Arbiter / Consensus | conflict resolution across reviewers/models is the main job | specializes Reviewer |
| Evaluator / Benchmark | regression testing skill behavior is the main job | governs all patterns |

Hermes policy: use the five patterns as the primary `control-flow mode` unless an adjacent mode is clearly dominant. Do not force every skill into one of the five if doing so hides the actual runtime behavior.

## Pattern selection decision tree

```text
1. Is the skill mainly exposing an external tool/API/platform/system?
   -> Wrapper

2. Is the skill mainly producing a stable artifact?
   -> Generator

3. Is the skill mainly judging an artifact/decision/evidence set?
   -> Reviewer

4. Is the skill mainly preventing guessing by eliciting constraints, using external tests/evidence, or reversing perspective/control?
   -> Inversion

5. Is the skill mainly coordinating ordered stages with gates/evidence?
   -> Pipeline

6. If none dominate, check adjacent modes: Router, Planner, Memory, Monitor, Guardrail, Arbiter, Evaluator.
```

## Required metadata for future Hermes skill graph

Current Hermes frontmatter does not enforce all fields below, so treat this as a proposed classification overlay rather than an immediate hard validator.

```yaml
metadata:
  hermes:
    tags: []
    related_skills: []
    primary_pattern: wrapper|generator|reviewer|inversion|pipeline|router|planner|memory|monitor|guardrail|arbiter|evaluator
    secondary_patterns: []
    artifact_contract:
      consumes: []
      produces: []
      verifies: []
    safety:
      side_effects: none|local_files|external_write|destructive|credentialed|production_sensitive
      human_gate: never|required_for_destructive|required_for_external|required_for_acceptance
    evals:
      routing: missing|planned|present
      behavior: missing|planned|present
```

Do not add this metadata blindly to every existing skill with a script. Pattern labels are semantic routing data and need review.

## Skill creation gate using the five patterns

Before creating a skill:

1. Need gate: does this belong in skill instead of docs/private, experience, taskpool, memory, or project profile?
2. Pattern gate: which primary pattern controls the body shape?
3. Trigger gate: does `description` say when to load, not what it vaguely does?
4. Context gate: what belongs in index, root body, references, templates, scripts?
5. Artifact gate: what does the skill consume/produce/verify?
6. Safety gate: what side effects need confirmation or read-back?
7. Eval gate: what positive/neighbor/forbidden/no-load prompts test routing?
8. Maintenance gate: what future failure should become a gotcha vs a new skill?

## Pattern-specific evaluation matrix

| Pattern | Routing eval | Behavior eval | Evidence requirement |
|---|---|---|---|
| Wrapper | tool/platform intent vs adjacent generic help | mock/sandbox command sequence | command output + target state read-back |
| Generator | artifact request vs general advice | schema/template/build/test | artifact path/content + coverage |
| Reviewer | review/audit request vs implementation request | golden defects/severity calibration | cited evidence + gate result |
| Inversion | ambiguity/risk request vs simple direct action | question quality + synthesis coverage | compiled spec/decision log |
| Pipeline | multi-stage task vs one-shot action | stage postconditions + E2E trace | evidence ledger + closure state |

## Anti-patterns

1. README skill: long prose with no trigger, artifact, or verification.
2. Prompt-only skill: useful text but no maintenance/eval path.
3. Omnibus skill: covers multiple unrelated trigger classes and steals routing.
4. Fake Reviewer: critique without evidence or severity calibration.
5. Fake Pipeline: checklist with no gates or stage outputs.
6. Unsafe Wrapper: external side effects without read-back or human gate.
7. Inversion junk drawer: every ambiguous concept labeled inversion.
8. Eval-free durable skill: promoted to long-term skill without positive/negative trigger cases.

## Hermes adoption plan

### Phase 1 — Low-risk codification (done in this session)

- Create this SSOT document.
- Create `agent-skill-design-patterns` skill with executable classification/audit procedure.
- Add support files for pattern matrix and routing eval prompts.
- Verify read-back and frontmatter parsing.
- Scoped commit only these artifacts.

### Phase 2 — Pilot on 10 representative skills

Select 2 each from Wrapper/Generator/Reviewer/Inversion/Pipeline. For each:

- classify primary/secondary pattern;
- check description routing precision;
- check context budget split;
- record missing artifact/evidence contract;
- add eval prompt set only when editing the skill.

Do not bulk rewrite descriptions in this phase.

### Phase 3 — Skill graph overlay

Build a non-mutating report that scans skills and proposes:

- primary pattern candidates;
- missing verification sections;
- high-risk wrappers;
- bloated root bodies needing references;
- duplicate/umbrella consolidation candidates.

### Phase 4 — Governed migration

Only after pilot evidence:

- patch high-confidence skills;
- add metadata gradually;
- add eval prompts for important skills;
- demote stale or unsafe skills from auto-routing where supported.

## Falsifiers and revision triggers

Revise this taxonomy if:

- more than 20% of audited high-value skills cannot be honestly classified without adjacent modes;
- pattern labels do not predict correct SKILL.md structure;
- routing evals show the taxonomy causes false positives;
- support files become mandatory for every run, indicating poor progressive loading;
- agents using this skill produce more over-engineering than successful repairs.

## Decision record

Decision: adopt five foundational Agent Skill design patterns as Hermes v1 skill-authoring and audit vocabulary, with explicit caveat that adjacent patterns are allowed when dominant.

Reason:

- The five patterns map to distinct runtime control-flow shapes.
- They are actionable for authoring and rehabilitation.
- They preserve the docs vs skill vs memory boundary.
- They align with external Agent Skills evidence: routable `description`, SKILL.md contract, supporting files, scripts, evals, and multi-harness portability.

Consequences:

- Future skill work should identify a primary pattern before writing body structure.
- Description edits remain routing changes and require eval thinking.
- Large theory should stay in docs/private; skill body should remain actionable.
- Hermes should not perform naive batch rewrites based only on this taxonomy.
