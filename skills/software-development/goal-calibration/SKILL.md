---
name: goal-calibration
description: Use when any human request is ambiguous, shorthand, subjective, or prompt-like—e.g. align, fix, optimize, make consistent, follow prototype, improve, write prompt, or vague UI/product/API tasks. First infer the durable target and acceptance dimensions before implementation.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [requirements, ambiguity, goal-alignment, ux, prompts]
    related_skills: [project-evidence-grounding, api-and-interface-design, hermes-agent-skill-authoring]
---

# Goal Calibration

## Overview

Goal calibration is a high-priority front door for human-language tasks. Human requests often compress the real target into a small phrase: "align the dropdown", "make it like the prototype", "optimize this", "fix the prompt", "make it consistent", "not right". These phrases are not small tasks; they are pointers to a target model that may include UX, business logic, data, state, accessibility, copy, validation, routing, and verification.

Use this skill to translate fuzzy language into an explicit acceptance target before changing files or giving architecture advice. The goal is not to ask more questions by default; it is to infer the likely durable target from context, act when the basis is clear, and ask only when competing targets would produce materially different work.

## When to Use

Use this skill for any request with ambiguous or compressed human wording, including:

- UI/product wording: align, match, consistent, restore, follow prototype, same as old version, weird, off, polish, optimize, improve, make it right.
- API/business wording: state, status, notification, failed, success, available, enabled, visible, allowed, should show, should not show.
- Prompt/workflow wording: improve this prompt, make the agent do X, avoid misunderstanding, define workflow, fix instruction, better task description.
- Cross-layer tasks where a surface issue may involve data, logic, state, contract, UX, copy, or test evidence.
- Any task where the user's long-term target may be broader than the literal noun in the sentence.

Don't use for:

- Pure deterministic commands with unambiguous target and no design choice, e.g. "what time is it", "calculate 123*456", "read this exact file".
- Explicitly scoped one-line edits where the user names the exact file/string/change and no broader behavior is implied.
- Situations where a more specific emergency or safety workflow must run first.

## Position in the Agent Flow

Goal calibration is a fixed high-priority internal gate, not a mandatory human interruption. It should run after intent parsing and any cheap read-only context gathering that clarifies the baseline, but before planning, implementation, file writes, deployments, messages, or other side effects.

### Quoted-reply / thread-context intent gate

On Telegram or any platform that prepends a quoted message like `[Replying to: "..."]`, treat the quoted block as **context/evidence only**, not as the active request. Before acting, split the input into:

- `quoted_context`: the message being replied to; useful for resolving references such as “继续”, “这个”, “认可”.
- `active_user_text`: the new user-authored text after the quote; this is the command to satisfy.

Rules:

1. Never let a quoted cron/report/old answer override the active user text.
2. If the active text is a correction like “你理解错了 / 不是这个 / 为什么串线程”, switch to incident diagnosis of the immediately preceding assistant behavior, not the quoted task.
3. If the active text is “继续” while quoting a prior plan, resume that quoted plan; if it adds new clauses, satisfy those clauses in order.
4. If there are multiple plausible anchors (quoted message vs latest conversation topic vs current session task), state the inferred anchor before side effects or ask one compact clarification.
5. Verification must check the active command was answered, not merely that some referenced context was processed.

Default flow:

```text
User input -> intent parse -> read-only context if useful -> goal calibration gate -> task contract -> plan/tool routing -> execute -> verify against task contract
```

Use risk to decide whether calibration stays internal or becomes a user question:

- Low risk: infer the target and act.
- Medium risk: state the assumption and continue, or ask one compact multiple-choice question.
- High risk: ask before implementation because plausible targets produce different edits.
- Critical risk: list planned side effects and wait for approval.

Do not turn calibration into "always ask the user what they mean". That is over-asking. Use external clarification only when it changes the work.

## Task Contract

Calibration should leave behind a compact working contract, even if only in the response/plan:

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

Planner/executor/verifier should stay anchored to this contract. Recalibrate only at task-type switches, phase boundaries, discovered constraint conflicts, or verification failures that imply target mismatch.

## Calibration Pipeline

1. Identify the likely target class.
   - Is the user asking for observable UX/effect parity, business correctness, schema/contract parity, visual polish, prompt behavior, or verification evidence?
   - Prefer the user's durable target and known preferences over the surface wording.

2. Find or infer the baseline.
   - Prototype, PRD, screenshot, old version, existing sibling component, design system, live production, backend contract, previous user correction, or prompt behavior examples.
   - If no baseline exists and multiple plausible baselines conflict, ask a targeted clarification.

3. Expand the ambiguity into dimensions.
   - UI: layout, spacing, typography, color, layering, responsive behavior, accessibility.
   - Interaction: open/close, keyboard, focus, disabled/loading/error, gestures, navigation.
   - Data/options: completeness, ordering, labels, defaults, i18n, value mapping.
   - Business/state: permissions, eligibility, status, success/failure/pending, upstream/downstream dependencies.
   - Contract: API fields, payload, read-after-write, persistence, cache, URL/store sync.
   - Prompt/agent behavior: trigger conditions, negative space, output shape, tool use, verification, stop conditions.

4. Map each target dimension to an implementation carrier.
   - Backend business fact/state/content.
   - Frontend state, visual mapping, interaction, route/action.
   - Prompt/skill instruction, examples, negative cases, verification harness.
   - Test evidence, screenshots, contract tests, or runtime proof.

5. Decide: act, ask, or split.
   - Act when one baseline and target class are clearly dominant.
   - Ask when two or more target interpretations require different edits.
   - Split when the request contains both audit and architecture/implementation advice: produce coverage facts first, then durable target-directed recommendations.

6. Verify against the calibrated target, not the literal phrase.
   - For "align dropdown", verify visual alignment plus any discovered option/state/logic alignment.
   - For "follow prototype", verify observable user effects, not mock field names.
   - For "improve prompt", verify the prompt handles positive cases, negative cases, and likely ambiguity.

## Prompt-Writing Tasks

Prompt requests are also ambiguity tasks. A prompt is an interface between human intent and model behavior, so apply the same calibration:

- Target behavior: what should the model reliably do?
- Context boundary: what information is assumed, injected, or must be requested?
- Positive cases: prompts that should trigger the behavior.
- Negative space: prompts that must not trigger it.
- Output contract: format, tone, length, evidence, tool use, and stop conditions.
- Failure modes: overbroad compliance, literalism, missing prerequisites, hallucinated context, unsafe side effects.
- Verification: small eval set or before/after examples when practical.

Do not optimize a prompt only for the exact wording shown. Optimize it for the user's intended class of future inputs.

## Prototype and Reference Handling

Treat prototypes, screenshots, and old implementations as evidence of desired effects, not as mandatory architecture:

- Extract observable user effects first.
- Treat mock data fields as clues, not contracts.
- Copy the UX/effect unless the user explicitly asks to copy the structure.
- Recommend backend changes only when the effect lacks a stable business fact or semantic state.
- Keep presentation mapping in the frontend unless presentation is explicitly CMS/ops-configurable.

## Evidence Reliability Gate for UI / Prototype Tasks

Scope: UI, prototype, screenshot, issue-tracker, or product-review tasks that say a surface should "show", "display", "match", "align", "restore", or "1:1" some visible fields.

Primary rule: evidence reliability comes before implementation classification. Do not decide whether a task is presentation-only, mapping, or data-source work until the supplied reference has been treated as the source of truth and its evidential limits have been extracted.

Required evidence pass before side effects:

1. Extract the reference literally: visible labels, visible values, zero/non-zero states, absent elements, layout, and annotations.
2. Separate observed facts from inferred implementation. A visible field is evidence of required output, not proof of data source.
3. Identify missing data-contract evidence. If source, eligibility, aggregation, or launch gate is not specified, mark it unknown instead of filling it from historical code.
4. Treat existing comments/history as lower-reliability hints unless their preconditions are verified. A comment like "restore this when upstream is ready" is not proof that upstream is ready now.
5. Preserve the current business data path when evidence is incomplete. Change data semantics only after explicit task text, product contract, runtime proof, or user approval establishes the change.
6. Define a falsifier from the reference/task. Example shape: if the reference establishes a placeholder state and no data-source requirement, any live value is a failure even if layout matches.

Only after this reliability pass should the task be classified as one of:

1. Presentation-only: labels, layout, visual hierarchy, visibility of existing fields; preserve existing business data source and guards.
2. Mapping change: same source, different frontend mapping/filter/format; state the source and invariant.
3. Data-source change: new endpoint/store/aggregation/contract; requires explicit evidence from task text, PRD, backend contract, or user approval.
4. Placeholder/feature-gated surface: visible UI exists but real data must remain disabled or zero until launch criteria are met.

If the task only names UI fields but not data semantics, keep the current data source and business gates. Do not infer that "show X" means "wire raw shared store collection into X".

Calibration questions to answer internally before implementation:

- What does the screenshot/prototype/task text literally prove, and what does it not prove?
- Which claims are observed facts, which are assumptions, and which are historical-code hints?
- Is there an existing placeholder, feature gate, or business guard, and what evidence would authorize removing it?
- Does the task explicitly change source, eligibility, aggregation, or only observable layout/copy?
- Is the displayed collection raw shared state or a page-specific view model?
- What reference-derived negative case must stay true after the change?

## Medium/High Ambiguity Prethink Mode

Use this heavier mode only when the request is important enough that a wrong target would waste work: product/design/strategy/creative planning, workflow or skill design, external-source absorption, cost/permission-sensitive automation, or multi-session implementation. Keep the normal light path for obvious tasks.

Prethink stages:

1. **Define the problem** — classify type (`decision`, `creative`, `analysis`, `planning`, `diagnosis`, `implementation`), boundary/scope, expected output, and what would count as acceptance. Ask only if competing interpretations would change the work.
2. **Recall experience** — search session/skills/memory/project profile when relevant; state whether a past pattern is actual evidence, a reusable lesson, or merely a hint.
3. **External reference** — for research/social/repo/product claims, verify canonical sources directly before judging value. If search is unavailable or irrelevant, mark the gap instead of filling it from intuition.
4. **Choose depth and reasoning route** — do not use every framework by default. Match route to problem type:
   - decision: six-hats / SWOT / trade-off matrix;
   - creative: first principles / divergent options / pyramid synthesis;
   - analysis: critical thinking / Socratic checks / evidence matrix;
   - planning: pyramid / reverse planning / dependency DAG;
   - diagnosis: 5 Whys / fault tree / counterfactuals.
5. **Think in bounded passes** — after each substantial pass, either continue on the selected route or stop at a useful checkpoint. If the path repeats, contradictions appear, or evidence is missing, surface that instead of forcing convergence.
6. **Synthesize with self-check** — every conclusion should identify traceable evidence, confidence, inferred assumptions, discarded alternatives, and the next verification step.
7. **For external inspiration intake, classify landing zones before durable writes** — split the source into reusable class-level pattern, project-specific scoped fact, stable user preference, concrete engineering follow-up, or session-only narrative. Evidence notes may preserve source details; SKILL.md updates should only carry class-level procedure/pitfalls, while concrete work belongs in taskpool with redlines and acceptance evidence.
8. **Persist process only when useful** — for complex or cross-session work, write a concise process artifact with problem definition, evidence, reasoning route, conclusions, and open assumptions. Do not create process files for trivial chat.

Anti-overasking guardrails:
- The user prefers “少问但问准”: infer safe defaults and act when the ambiguity is low.
- `全自动` or broad authorization may suppress routine confirmations, but stuck states, permission/cost/side-effect boundaries, and mutually exclusive strategy choices still require a gate.
- Framework names are not evidence. They structure thinking; they do not replace source verification, tests, runtime proof, or user acceptance.

## Common Pitfalls

1. Keyword-trigger narrowing: only running calibration for specific phrases like "prototype states" or "missing fields". Calibration applies to all fuzzy human-language goals.
2. Human-interruption trap: asking "what is your goal?" for every request. Calibration is usually internal; ask only when competing targets require different work.
3. Literal noun trap: treating "dropdown alignment" as CSS only while ignoring options, disabled state, dependent fields, payload, and read-back behavior.
4. Prototype schema trap: copying mock fields instead of reproducing observable user effects.
5. Prompt literalism: improving a prompt for the shown sentence instead of the future task class and negative space.
6. Goal drift: calibrating once, then letting implementation expand into unrelated refactors or a different success metric.
7. False completion: verifying only the touched layer instead of the calibrated target dimensions.
8. Data-source leap: treating visible field names in UI tasks as authorization to change API source, aggregation, cache, or domain eligibility.

## Regression Evals

See `references/eval-cases.md` for positive triggers, negative/light-path cases, neighbor-skill boundaries, and failure checks. Use it when editing this skill or auditing whether goal calibration is over- or under-triggering.

## Verification Checklist

- [ ] The target class is stated or inferred: UX/effect, business, contract, visual, prompt behavior, or verification.
- [ ] The baseline is identified or a targeted clarification was asked.
- [ ] Ambiguous terms were expanded into relevant dimensions.
- [ ] Each dimension was mapped to the correct implementation carrier.
- [ ] The solution avoids using presentation fields as backend contract unless required.
- [ ] Prompt tasks include positive cases, negative space, output contract, and failure modes.
- [ ] Verification checks the calibrated target rather than only the literal wording.
