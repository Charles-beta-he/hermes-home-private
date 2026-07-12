# Single-model frame-error prevention

Scope: reusable debugging and engineering-review procedure for a single agent/model working without independent model dissent. Use when a bug, UI regression, backend drift, or workflow failure can be caused by accepting the wrong problem representation too early.

Applicability:
- The visible symptom may be downstream of another layer, lifecycle, cache, state machine, ownership boundary, or runtime environment.
- The first plausible fix is tempting, but the same class of issue has already produced repeated patches, route/platform special cases, or new regressions.
- The user challenges the reasoning frame, asks for root cause, or says the thinking process is wrong.

Anti-conditions:
- A freshly reproduced deterministic defect has one directly observed root cause and no alternative mechanism.
- The user explicitly asks for implementation of an already chosen, evidence-backed fix.
- The lesson is task progress or a project-only fact; keep those in the session/project evidence, not this class-level rule.

## Core claim

A single model usually fails on these incidents by converging too early, not by lacking local reasoning ability. It forms a plausible frame from the most salient symptom, then optimizes inside that frame. The defense is not "think harder"; it is to delay convergence with a fixed gate:

```text
R-B-H-F-E-O-S
Representation -> Boundary -> Hypotheses -> Falsifier -> Evidence -> Ownership -> Solution
```

Never jump from symptom to solution on repeated or ambiguous bugs.

## R-B-H-F-E-O-S gate

### 1. Representation

Rewrite the issue as a state/path/mechanism sentence, not a component sentence.

Bad:
```text
The CTA moves when the keyboard opens.
```

Better:
```text
During the mobile input-focus path, the browser viewport, document scroll, app shell, route scroller, page shell, and footer are competing for layout ownership, so the bottom action area loses a single controller.
```

Minimum fields:
- surface: browser, WebView, backend, CLI, deployment, etc.
- path: first open, focus, route return, resume, submit, retry, cache hit, etc.
- time slice: before / during / after the transition.
- visible symptom: what the user sees.
- suspected mechanisms: plural, not one.
- contrast path: where the symptom does not occur.

### 2. Boundary

List every layer that can produce the symptom before choosing a file to edit.

For UI/layout defects, include at least:
- OS/browser/runtime viewport.
- document/body/root ownership.
- app shell and route scroller.
- page shell and component scroller.
- CSS tokens and JS listeners.
- lifecycle/state/cache/deployment identity.
- tests or mocks that may be proving the wrong thing.

For backend/product defects, include:
- request payload and DTO normalization.
- controller/service/domain/repository.
- cache/job/webhook/migration.
- frontend adapter/store/display consumer.
- permission/status/source-of-truth owner.

### 3. Hypotheses

Keep at least three live hypotheses before patching:
- visible component defect;
- upstream shell/state/lifecycle defect;
- environment/runtime/cache/deployment defect;
- ownership conflict between two controllers;
- verification-path defect where tests prove implementation traces rather than behavior.

If only one hypothesis exists, assume anchoring is active.

### 4. Falsifier

Every hypothesis must be falsifiable:

```text
Hypothesis: <mechanism>
If true, observe: <specific state/metric>
If false, observe: <counterexample>
Minimal probe: <readback/test/screenshot/log>
Stop condition: <when to abandon this path>
```

No falsifier means no implementation.

### 5. Evidence

Collect discriminating evidence, not confirmation evidence.

Prefer probes that can kill the favorite hypothesis:
- UI: bounding boxes, computed styles, scrollTop/clientHeight/scrollHeight, visualViewport metrics, activeElement, z-index, route state, before/after screenshots.
- Backend: request payload, normalized internal state, branch taken, DB readback, response, frontend normalization, UI consumer.
- Workflow/control plane: current state source, writer identity, lifecycle transition, receipt/readback, stale claim/cache markers.

### 6. Ownership

Before editing, make an owner map for the variable being changed:

```text
Variable | Current writers/controllers | Correct owner | Forbidden writers | Migration/removal action
```

Examples of variables:
- viewport height, document scroll, route scroll, input visibility, CTA position;
- auth state, cache freshness, status enum, money precision, permission, lifecycle transition.

If multiple controllers write the same variable, prefer deleting or narrowing controllers over adding another special case.

### 7. Solution

Only after the previous gates, choose the smallest fix that:
- reduces state space or controller count;
- explains both broken and working contrast paths;
- avoids platform/route/page special cases unless the boundary proves they are real;
- can be regression-tested through the user path;
- has an explicit rollback/removal path.

## Single-model self-simulation roles

When no independent model is available, run these roles serially and do not merge them early:

1. Builder: state the most likely mechanism.
2. Skeptic: explain how the Builder could be wrong.
3. Boundary auditor: identify any missing layer or too-small system boundary.
4. Evidence accountant: separate facts from explanations and name missing probes.
5. Ownership reviewer: find variables with multiple writers/controllers.
6. Minimalist: remove conflicting mechanisms before proposing additions.

The final answer may be concise, but the gates must have been passed internally for risky/repeated bugs.

## Stop triggers

Stop local patching and rerun this gate when:
- the same symptom receives a second distinct fix;
- fixing one symptom creates another symptom;
- the fix grows platform/route/page/input special cases;
- the proposed patch uses `preventDefault`, scroll restoration, timeout settling, force layout, or global listeners without a proven owner boundary;
- tests assert class names, markers, or token strings but not the actual user path;
- the normal contrast path is unexplained;
- the agent cannot name what would falsify the favorite hypothesis;
- a third flag/escape hatch is about to be added.

## Theory map

Use these works as checks, not as proof:
- Karl Popper, *The Logic of Scientific Discovery*: require falsifiers.
- Charles Sanders Peirce, abduction essays / *Collected Papers*: visible likeness only generates hypotheses.
- Daniel Kahneman & Amos Tversky, "Judgment under Uncertainty"; Kahneman, *Thinking, Fast and Slow*: guard against anchoring, availability, and substitution.
- Russell Ackoff, *The Art of Problem Solving*: avoid solving the wrong problem efficiently.
- C. West Churchman, *The Systems Approach*: system boundaries decide solution quality.
- Donella Meadows, *Thinking in Systems* and "Leverage Points": change structure/ownership before low-leverage parameters.
- Imre Lakatos, *The Methodology of Scientific Research Programmes*: repeated protective-belt patches signal a bad core assumption.
- Argyris & Schon, *Organizational Learning*: use double-loop learning when action fixes repeat.
- Herbert Simon, *The Sciences of the Artificial*: counter satisficing by forcing candidate alternatives.
- Nancy Leveson, *Engineering a Safer World*: model controller/controlled-process/feedback/constraint failures, not only component failures.

## Verification checklist

- [ ] The problem is written as state/path/mechanism.
- [ ] At least three candidate mechanisms were considered or a constrained single-path reason is stated.
- [ ] Each nontrivial hypothesis has a falsifier.
- [ ] Evidence distinguishes hypotheses rather than confirming the favorite.
- [ ] The changed variable has one explicit owner.
- [ ] The proposed fix removes or narrows conflicting controllers before adding new ones.
- [ ] Regression covers the user path and a contrast path, not only implementation traces.
