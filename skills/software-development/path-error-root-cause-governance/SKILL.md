---
name: path-error-root-cause-governance
description: "Use when a debugging or review task may be following the wrong path: repeated fixes, symptom-fixing, visible-component fixation, or a user correction that asks why rather than asking for another patch."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [debugging, root-cause, systems-thinking, incident-review, governance]
    related_skills: [systematic-debugging, abstraction-governance, qian-meta-synthesis]
---

# Path-Error Root-Cause Governance

## Scope / Applicability / Anti-conditions

Scope: reusable software debugging and incident-review workflow. It applies to UI, backend, DevOps, automation, and agent-workflow bugs where the main risk is choosing the wrong investigation path.

Applicability: use after repeated failed fixes, symptom masking, user correction of the reasoning frame, or any case where the visible broken component may be downstream of state, lifecycle, layout, cache, deployment, or control-flow mechanisms.

Anti-conditions: do not use for a simple freshly reproduced bug with a direct root cause, pure implementation after root cause is already proven, or storing task progress/PR/commit/session status.

## Overview

This skill governs the failure mode where the agent controls the wrong variable because it accepted the wrong problem representation. The goal is to reset the frame before another patch: represent the problem, build an evidence matrix, keep competing hypotheses alive, define falsifiers, then choose the smallest root-cause fix.

## When to Use

- The same bug has already received two or more fixes and keeps changing shape.
- The fix path is becoming platform-specific, timing-specific, or workaround-like.
- A user says “不是这个”, “你在修表现”, “先查为什么”, or otherwise challenges the frame.
- The apparent target is a visible component, but upstream state/lifecycle/layout/cache/auth/deployment can produce the same symptom.
- Multi-model or research output produced methodology that must become an executable gate.

Don't use for:

- A deterministic one-line bug with no ambiguity about cause.
- A task where the user explicitly asks only for an already chosen implementation.
- Durable writes of task-local artifacts; those belong in task/session evidence.

## Core Claim

Path error happens when the problem is represented at the wrong layer, wrong time slice, or wrong causal chain.

Bad loop:

```text
Visible symptom -> first plausible cause -> patch same component -> partial change -> patch same path again
```

Governed loop:

```text
Visible symptom -> problem representation -> evidence matrix -> competing hypotheses -> falsifier -> root-cause fix -> regression
```

Problem-finding chain before patching:

```text
User wording / artifact -> intended outcome -> time slice -> surface owner -> causal boundary -> candidate mechanisms -> discriminating evidence -> root-cause path
```

For visual/product bugs, do not collapse this into a single component diagnosis. First split:

- User intent: what stage/effect is being judged?
- Time slice: first paint, loading, transition, hydrated state, steady state, resume, deploy update, etc.
- Surface owner: OS shell, browser/WebView, app shell, route, component, animation layer, backend data, cache, deployment.
- Boundary of control: what the suspected layer can actually control, and what is upstream/downstream of it?
- Candidate mechanisms: at least two plausible layers that can produce the same visible symptom, including the agent/process layer when there have been repeated fixes or user frame corrections.
- Self/process suspect: ask whether the current investigation is anchored on project-level root cause while missing a class-level method failure, ownership-contract failure, or verification-gate failure.
- Falsifier: one observation that would make the current path wrong.

Recent commits, obvious components, and model guesses are only leads. They must not replace this chain.

## RPEPR Procedure

### 1. Representation — rewrite the problem

Write the problem as a state/path/mechanism sentence, not a component sentence.

Bad:

```text
The bottom navigation is gone.
```

Better:

```text
A restored startup path enters a state where bottom chrome is not visible after the loading layer should have released ownership.
```

Minimum fields:

- Surface: browser, installed app, WebView, backend, CLI, deployment, etc.
- Path: first open, refresh, resume, cold start, route return, deploy update, etc.
- Time slice: T0 first paint, T1 loading/skeleton, T2 hydrated/steady state, T3 resume/update/teardown.
- Layer: OS/browser ownership, render, CSS geometry, state marker, lifecycle, cache, auth, API, deployment.
- Control boundary: what the suspected layer can and cannot change.
- Contrast: where the symptom does not occur.

If the user supplied a video/screenshot/log, extract the observed facts by time slice before reading code. Do not let recent commits or the most visible component choose the time slice for you.
### 2. Proof Matrix — measure before changing

Scope: class-level debugging proof selection across software projects. Applicability: use when the issue is repeated, core-path, or framing-sensitive. Anti-condition: skip the expanded matrix for a deterministic one-line defect with direct proof.

Build evidence that distinguishes causes. Include both the broken path and a working contrast path.

Use the evidence-modality contract: first name the disputed variable and owner boundary, then choose the proof type that can directly observe that variable. Different domains require different readbacks; do not promote one domain's proof shape into a universal rule.

Minimum proof matrix fields:

- Disputed variable or ownership decision.
- Current producers/controllers/writers.
- Transformers/adapters/fallbacks.
- Consumers/displays/action users.
- Direct readback at the variable's real boundary.
- Broken path evidence and contrast/negative path evidence.
- Falsifier that would demote the current explanation.

Load `references/evidence-modality-contract.md` when the evidence type is unclear or the issue is repeated/core.
### 3. Entry Gate — judge candidate paths

Before editing, score each candidate fix:

1. Does it explain all broken cases?
2. Does it explain the non-broken contrast cases?
3. Does it reduce uncertainty, or only change appearance?
4. Does it touch the layer where evidence shows the mechanism lives?
5. Does it add special cases or reduce state space?
6. Is it reversible and minimal?
7. Can it be regression-tested?
8. What observation would make this path wrong?

If the path fails questions 1, 2, 4, or 8, stop and gather more evidence.

### 4. Prediction / Counterfactual — define falsifiers

Template:

```text
Hypothesis: <mechanism>
If true, we should observe: <specific measurable state>
If false, we might observe: <counterexample>
Minimal test: <one-variable probe>
Stop condition: <when to abandon this path>
```

A useful hypothesis predicts both the broken path and the working contrast path.

### 5. Regression — lock the path, not only the fix

Regression must cover the path that generated the bug.

Include:

- One unit/component test for the exact lifecycle/state transition.
- One integration/harness test for the user path where practical.
- One negative/contrast assertion proving a nearby working path still works.
- Build/type/lint gates when code changed.

## Stop Rules

Stop patching and re-run this skill when:

- Two fixes in a row fail or trade one symptom for another.
- The fix set grows by platform, route, or timeout special cases.
- The target component appears correct by direct evidence but the symptom persists.
- The user challenges the frame rather than the implementation.
- You cannot state what observation would disprove the current path.
- The proposed patch hides, delays, or masks a symptom without explaining the owner layer.

## Landing-Zone Classifier

| Lesson shape | Landing zone |
|---|---|
| One-off event, PR, task status | session transcript / task evidence only |
| Stable project-specific fact | project profile or repo docs |
| Reusable debugging procedure | skill or skill reference |
| Mandatory safety/process boundary | runtime gate, CI, PR template, taskpool policy |
| Architecture/product decision | ADR |
| Stable user preference/red line | compact user memory |
| Multi-model theory packet | skill reference with source/evidence/falsifier separation |

Do not put project facts into global skills unless stripped into a transferable pattern.

## Theory Map

Use theory as a reasoning check, not as evidence.

- Karl Popper, *The Logic of Scientific Discovery*: hypotheses must be falsifiable.
- Thomas Kuhn, *The Structure of Scientific Revolutions*: frames decide which anomalies are noticed.
- Imre Lakatos, *The Methodology of Scientific Research Programmes*: repeated protective-belt patches can preserve a bad core assumption.
- Charles Sanders Peirce, abduction: “looks like X” only generates a hypothesis; it does not prove it.
- Herbert Simon, *The Sciences of the Artificial*: bounded rationality and satisficing cause early convergence.
- Daniel Kahneman, *Thinking, Fast and Slow*: salience, availability, and anchoring bias pull attention to visible symptoms.
- Russell Ackoff, *The Art of Problem Solving*: many failures solve the wrong problem.
- C. West Churchman, *The Systems Approach*: bad system boundaries create bad optimization.
- Donella Meadows, *Thinking in Systems*: changing low-leverage parameters is weaker than fixing structure and feedback.
- Argyris & Schön, *Organizational Learning*: double-loop learning questions assumptions and rules, not only actions.
- David J. Agans, *Debugging*: understand the system, make it fail, change one thing at a time, keep an audit trail.

## Linked References and Templates

- `references/problem-finding-chain.md` — reusable method for converting user wording/artifacts into an evidence-led causal path: intent → time slice → surface owner → control boundary → hypotheses → discriminating evidence → root-cause path.
- `references/pwa-kill-reopen-bottom-chrome-case.md` — scoped mobile/PWA example for kill/reopen bottom-chrome disappearance, including the classification gate for DOM/CSS/geometry/state/lifecycle/cache and splash-marker teardown failure.
- `references/mobile-keyboard-layout-control-ownership.md` — class-level pattern for mobile Web/PWA/WebView soft-keyboard regressions where global body locks, app route shells, component shells, visualViewport listeners, and page-specific pointer/focus handlers compete for the same scroll/viewport ownership.
- `references/single-model-frame-error-prevention.md` — single-agent R-B-H-F-E-O-S gate for avoiding early convergence on the wrong problem frame: Representation → Boundary → Hypotheses → Falsifier → Evidence → Ownership → Solution.
- `references/eval-mobile-input-layout-frame-error.md` — class-level eval fixture: repeated mobile input-layout fixes with multiple viewport/scroll/action controllers must block implementation and force an ownership-contract pass.
- `references/evidence-modality-contract.md` — class-level proof-selection rule for repeated/core issues: completion evidence must observe the disputed variable at its correct boundary; screenshots/coordinates are UI-specific examples, while backend/API/data/workflow/release issues require their own direct readbacks, contrast paths, and falsifiers.
- `references/root-cause-ownership-engineer-role.md` — reusable development role template for high-risk/repeated problems: problem representation auditor + ownership-convergence architect + regression evidence gatekeeper.
- `templates/rpepr-debugging-note.md` — fill-in working note for the RPEPR procedure before applying a third patch or when the user challenges the frame.

## Common Pitfalls

1. Treating the visible component as the causal component.
2. Letting recent commits anchor the search without testing alternative mechanisms.
3. Mistaking a workaround for a root-cause fix.
4. Adding platform/route/timing special cases before proving the system boundary.
5. Running only a “does it now look okay” check instead of a falsifier.
6. Saving the incident story as global memory instead of extracting a scoped reusable rule.
7. Flattening multi-model agreement into truth; keep dissent and evidence separate.
8. Omitting anti-conditions, making the new rule over-trigger later.

## Verification Checklist

- [ ] The problem was rewritten as a state/path/mechanism sentence.
- [ ] At least two alternative hypotheses were kept alive before fixing.
- [ ] Evidence distinguishes the candidate paths.
- [ ] The chosen fix targets the layer shown by evidence.
- [ ] A falsifier/stop condition was named.
- [ ] Regression covers the failing path and at least one contrast path.
- [ ] Any durable learning was stored in the correct landing zone with scope and anti-conditions.
