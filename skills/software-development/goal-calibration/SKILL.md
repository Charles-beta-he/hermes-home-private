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

## Common Pitfalls

1. Keyword-trigger narrowing: only running calibration for specific phrases like "prototype states" or "missing fields". Calibration applies to all fuzzy human-language goals.
2. Literal noun trap: treating "dropdown alignment" as CSS only while ignoring options, disabled state, dependent fields, payload, and read-back behavior.
3. Prototype schema trap: copying mock fields instead of reproducing observable user effects.
4. Prompt literalism: improving a prompt for the shown sentence instead of the future task class and negative space.
5. Over-asking: asking broad clarification even when context reveals the dominant baseline. Ask only the smallest question that changes the implementation.
6. False completion: verifying only the touched layer instead of the calibrated target dimensions.

## Verification Checklist

- [ ] The target class is stated or inferred: UX/effect, business, contract, visual, prompt behavior, or verification.
- [ ] The baseline is identified or a targeted clarification was asked.
- [ ] Ambiguous terms were expanded into relevant dimensions.
- [ ] Each dimension was mapped to the correct implementation carrier.
- [ ] The solution avoids using presentation fields as backend contract unless required.
- [ ] Prompt tasks include positive cases, negative space, output contract, and failure modes.
- [ ] Verification checks the calibrated target rather than only the literal wording.
