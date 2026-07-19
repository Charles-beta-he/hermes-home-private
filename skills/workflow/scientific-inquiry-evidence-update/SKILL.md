---
name: scientific-inquiry-evidence-update
description: "Use when the primary deliverable is a cross-domain inquiry packet for consequential empirical uncertainty: competing mechanism hypotheses, predictions that differ, validity-aware probes, calibrated updates, and scoped reproduction. Use as a nested kernel inside debugging, research, planning, meta-synthesis, or SDD when disputed assumptions remain. Do not use as the primary route for ordinary bug fixing, source discovery, execution-path comparison without disputed mechanisms, multi-agent ownership coordination, simple lookups, or routine implementation."
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [scientific-inquiry, hypotheses, falsification, evidence, causal-reasoning, reproducibility]
    related_skills: [objective-model-path-verification, systematic-debugging, qian-meta-synthesis, research, spec-stateful-sdd-workflow, abstraction-governance]
---

# Scientific Inquiry and Evidence-Update Kernel

## Overview

This is the class-level inquiry kernel for turning uncertainty into a defensible decision. It operationalizes the useful structure behind Peirce's abduction–deduction–induction, Popper's conjecture and refutation, multiple working hypotheses, strong inference, Bayesian-style evidence updating, experimental design, Deweyan inquiry, Lakatos-style architecture escalation, and Qian-style qualitative-to-quantitative meta-synthesis.

The kernel is not a universal academic ceremony and does not claim that every practical decision is a laboratory experiment. It provides the middle layer between high-level epistemology and domain workflows:

```text
observation -> problem representation -> competing hypotheses
-> discriminating predictions -> smallest valid probe
-> evidence update -> intervention -> reproduction -> ratification
```

Core rule: generate explanations broadly, but raise confidence narrowly. A plausible explanation, majority model vote, passing happy path, or absence of visible error is not established truth.

## When to Use

Use when one or more are true:

- The cause, mechanism, ownership, or best path is materially uncertain.
- A wrong conclusion would make implementation, release, architecture, product, policy, or research work costly.
- Several plausible explanations fit the same observations.
- The user asks for `大胆假设、小心求证`, scientific inquiry, strong inference, competing hypotheses, falsification, causal-mechanism discrimination, bounded causal-evidence assessment, or evidence-calibrated decisions.
- Repeated local fixes suggest the current representation or architecture may be wrong.
- Multi-model or expert discussion must be converted into objective evidence rather than consensus prose.
- A reusable claim needs applicability, anti-conditions, falsifiers, and reproduction evidence before promotion.

Do not use the full protocol for:

- Simple factual lookups with an authoritative source.
- Trivial formatting or obvious one-step reversible actions.
- Routine implementation after the relevant uncertainty has already been resolved and the spec is stable.
- Pure brainstorming where the user explicitly does not want evaluation yet.
- Safety, authority, legal, payment, credential, production, or destructive gates: inquiry can inform them but cannot override them.

Use Lite mode when the uncertainty is real but low-cost. If the workflow adds ceremony without changing a decision, narrow or skip it.

## Position in the Abstraction Stack

| Layer | Question | Hermes surface |
|---|---|---|
| Observation | What happened? | logs, APIs, screenshots, files, source citations |
| Experiment | What evidence can we obtain? | probes, tests, comparisons, interventions |
| Inquiry kernel | Which explanation survives? | this skill |
| Domain workflow | How is it applied here? | debugging, research, product, architecture |
| Method/governance | What makes the result trustworthy? | evidence gates, reproduction, independent review |
| Objective/authority | Should or may we act? | objective model, user authority, safety policy |

This skill selects and tests explanations. It does not choose human values, invent authority, or replace domain acceptance criteria.

## Operating Modes

| Mode | Trigger | Minimum record |
|---|---|---|
| Lite | low-cost uncertainty, one bounded decision | observation, 2 hypotheses or one hypothesis plus `problem.hypothesis_space_constraint`, valid probe, result |
| Standard | consequential multi-step work | inquiry packet, evidence ledger, update decision, reproduction |
| Strong inference | several live explanations or high confirmation-bias risk | 3+ alternatives, prediction matrix, decisive test sequence |
| Meta-synthesis | heterogeneous evidence, experts/models, qualitative + quantitative work | source, dissent, engineering ledgers + arbitration |
| Architecture escalation | repeated failed fixes or accumulating anomalies | failed predictions, invariant violations, competing architecture models |

## The Inquiry Loop

### 1. Problemize the situation

Separate:

- observations: direct source/tool/runtime facts;
- interpretations: what those facts might mean;
- decisions: what action is being considered;
- unknowns: which uncertainty changes the decision.

Write the problem as a disputed variable, causal relation, mechanism, or ownership boundary. Avoid problem statements that already contain the preferred answer.

Bad: `The cache is broken.`
Good: `Which producer or invalidation path explains stale value X at consumer Y after event Z?`

### 2. Establish source and baseline

Capture exact scope, version, environment, input, comparison baseline, and current evidence. Mark each item:

- `verified`: direct readback or authoritative primary source;
- `reported`: user/source statement not independently reproduced;
- `inferred`: interpretation from evidence;
- `missing`: needed but not yet obtained.

Historical sessions, model outputs, summaries, and prior PASS reports are leads until bound to the current target and read back again.

For Standard or stronger packets, baseline `verified`, `reported`, and `inferred` entries are evidence IDs, not free text. Each ID must resolve through the top-level `evidence_ledger` to a hypothesis, probe, exact source reference, observation time, scope, freshness, bounded result, and status. `verified` requires direct readback or an authoritative primary source; the validator checks the provenance contract and links, but cannot authenticate the outside source. A hypothesis update may cite only evidence from the same `valid_result` probe, and the cited evidence claims must cover every updated hypothesis.

### 3. Generate competing hypotheses

Prefer at least:

- `H1`: current leading explanation;
- `H2`: a plausible alternative mechanism;
- `H0`: null, measurement error, environment mismatch, or wrong problem representation.

For high-impact work add an adversarial hypothesis: the apparent success criterion or owner boundary is wrong.

Each hypothesis must state:

- mechanism, not merely correlation;
- scope and applicability;
- assumptions;
- expected observations if true;
- a falsifier or confidence-reducing result;
- competing explanations it must distinguish from.

Do not manufacture weak alternatives just to meet a count. A justified single-path case must state what constrained the space.

### 4. Derive discriminating predictions

A useful prediction differs across hypotheses. Build a small matrix:

| Probe/observation | H1 predicts | H2 predicts | H0 predicts |
|---|---|---|---|
| P1 | ... | ... | ... |

If every hypothesis predicts the same result, the probe cannot discriminate and should not be presented as proof.

Prefer tests with high expected information gain, low risk, low cost, reversibility, and proximity to the real owner/consumer boundary.

### 5. Design the smallest valid probe

For each probe record:

- target variable and owner;
- controlled variables;
- exact input/environment/version;
- expected outcomes by hypothesis;
- validity threats: confounders, selection bias, caching, instrumentation effects, flaky timing, base-rate neglect;
- stop condition and rollback;
- evidence artifact to preserve.

Use a real system boundary when the claim concerns real runtime behavior. Mocks can isolate logic but cannot certify production integration, user acceptance, external state, or data correctness.

### 6. Execute without moving the goalposts

Run one discriminating change or observation at a time where feasible. Preserve raw output before interpretation. If the probe fails to execute, record `invalid_probe` rather than treating it as evidence for or against a hypothesis. Probe result state is one of `not_run | valid_result | invalid_probe | blocked`; the observation itself belongs in claim-linked evidence, not in the result enum.

Do not silently redefine success after seeing the result. If the spec or problem representation was wrong, create an explicit revision and rerun the relevant gate.

### 7. Update confidence and preserve alternatives

Use calibrated states rather than binary rhetoric:

```text
unsupported | weakened | still_live | leading | strongly_supported | falsified
```

For each result state:

- which prediction occurred;
- likelihood under each live hypothesis;
- confidence movement and why;
- residual alternatives;
- whether another probe would change the decision.

Numeric Bayesian calculation is optional; Bayesian discipline is not. Do not assign decorative probabilities without a defensible model or calibration history.

A failure to falsify is not proof. A passing test supports only the exact claim and boundary it observes.

### 8. Decide whether to intervene

Implementation is allowed when:

- the selected mechanism explains the observations better than live alternatives;
- the planned intervention targets the identified owner/cause rather than the symptom;
- evidence is strong enough for the consequence and risk level;
- authority and safety gates independently permit the action.

If evidence is insufficient but delay is costly, choose a reversible experiment or mitigative action and label it as such. Do not relabel it a root-cause fix.

### 9. Reproduce and challenge

After intervention:

1. Demonstrate pre-fix RED or equivalent baseline failure when feasible.
2. Demonstrate focused GREEN at the real affected boundary.
3. Run regression/negative tests.
4. Reproduce in a second environment, fresh process, clean clone, or independent verifier when consequence warrants it.
5. Test the strongest remaining counterexample.

Independent model agreement without direct evidence is expert signal, not reproduction.

### 10. Ratify, narrow, or loop

Close with one state:

- `ratified`: claim is supported at the declared scope with reproduction evidence;
- `provisional`: sufficient for a reversible decision, not general truth;
- `inconclusive`: live alternatives remain and evidence would still change the decision;
- `falsified`: prediction failed under a valid probe;
- `blocked`: necessary evidence or authority is unavailable;
- `reframed`: problem representation changed; start a new loop.

For model-assisted inquiry, ratification must preserve three independent axes:

1. `truth_grounding`: whether normalized claims are linked to objective evidence;
2. `inquiry/review_quality`: whether issue ledgers, counterarguments, and requested evidence are resolved;
3. `orchestration_certification`: whether required planner/verifier participants, quorum, signatures, and final manifest gates passed.

Do not let all-model discussion approval repair a failed planner quorum, and do not let a green truth gate imply live routing or full multi-model certification. Conversely, a provider/quorum failure is not evidence against the underlying hypothesis. Record it as an invalid or degraded review probe, preserve the grounded evidence, and either retry with a fresh state or close at an explicitly degraded scope.

Promote a reusable rule only with scope, applicability, anti-conditions, falsifier, evidence refs, and a demotion path.

## Stop, Escalation, and Loop Policy

Continue automatically while a safe, reversible, evidence-producing probe exists and its result could change the decision.

Stop or escalate when:

- the next probe requires credentials, destructive action, production mutation, external dispatch, payment, legal/device effect, or unavailable human acceptance;
- all feasible probes predict the same outcome and therefore cannot discriminate;
- evidence cost exceeds decision value;
- the question is normative rather than empirical;
- the source of truth cannot be accessed and guessing would alter the path;
- the same valid prediction fails repeatedly across different local fixes.

Architecture escalation:

```text
one failed fix -> update local mechanism hypothesis
multiple related failures -> inspect shared owner/invariant
three or more failed root-cause interventions -> challenge architecture/problem representation
```

The count is a warning, not a theorem. Escalate sooner when safety or systemic evidence warrants it; do not force architecture change when failures were invalid probes or unrelated defects.

## Evidence Quality Ladder

From weakest to strongest for operational claims:

1. intuition or model opinion;
2. secondary report or historical summary;
3. source inspection/static reasoning;
4. isolated unit or synthetic probe;
5. controlled integration evidence;
6. real owner/consumer-boundary evidence;
7. independent reproduction on the exact artifact;
8. longitudinal/adversarial evidence under relevant failure conditions.

Higher rungs do not automatically answer different questions. A screenshot can prove visual state but not backend data correctness; a unit test can prove pure logic but not deployment health.

## Integration Contract

- `objective-model-path-verification`: defines objective, constraints, viable paths, consequences, and acceptance evidence. This skill resolves disputed assumptions inside that model.
- `systematic-debugging`: domain projection for technical bugs. Use its reproduction/data-flow workflow, with this kernel governing competing hypotheses and confidence updates.
- `research`: locates and evaluates sources. This kernel converts sources into testable claims and prevents literature consensus from becoming unbounded truth.
- `qian-meta-synthesis`: use when heterogeneous experts/models and qualitative/quantitative checks require separated ledgers and handback.
- `spec-stateful-sdd-workflow`: stores the canonical spec, task packets, evidence mapping, and closure state for long-running implementation.
- `abstraction-governance`: controls whether a supported local claim becomes a project fact, reusable skill rule, runtime gate, ADR, or no durable write.

Do not duplicate domain procedures here. The kernel supplies the invariant reasoning contract; neighboring skills supply domain-specific sources, tools, experiments, and acceptance tests.

## Required Inquiry Packet

For Standard or stronger mode, use schema `1.1` from `templates/inquiry-packet.json`. Every evidence update must cite same-probe, claim-covering evidence IDs from a `valid_result` probe, and `ratified` closure requires fresh verified reproduction evidence from a `valid_result` probe. Validate with:

```bash
python3 ~/.hermes/skills/workflow/scientific-inquiry-evidence-update/scripts/validate_inquiry_packet.py packet.json
```

The validator fail-closes schema shape, enums, provenance fields, and cross-references. It cannot determine truth, experimental validity, outside-world freshness, authority, or evidence authenticity.

Load `references/theory-to-engineering-map.md` only when theoretical provenance, method selection, or core works are directly relevant. Routine application should not pay that context cost. `assets/example-inquiry-packet.json` is example/evaluator-only and must not be loaded for ordinary inquiry. `scripts/test_validate_inquiry_packet.py` is maintainer-only and must run after validator or schema changes.

## Definition of Done

- [ ] Outcome: a decision or closure state is supported by claim-linked evidence at an explicit scope.
- [ ] Process: observations, interpretations, competing hypotheses, predictions, probes, updates, and remaining alternatives are distinguishable.
- [ ] Style: confidence language is calibrated; no consensus laundering or universalized scoped PASS.
- [ ] Efficiency: the smallest discriminating probe was preferred and the loop stopped when additional evidence no longer changed the decision.

## Common Pitfalls

1. **First-story lock-in**: the first plausible explanation becomes the plan. Keep H2/H0 alive until evidence discriminates.
2. **Confirmation-only testing**: collecting examples compatible with H1 but not diagnostic against H2.
3. **Decorative falsifier**: naming an impossible or irrelevant counterexample. A falsifier must be observable with a valid probe.
4. **Invalid-probe laundering**: treating timeout, missing permission, or broken instrumentation as negative evidence.
5. **Consensus laundering**: converting model/expert agreement into factual proof.
6. **Scope inflation**: promoting a unit test, screenshot, local run, or one dataset into a global claim.
7. **Correlation-to-cause jump**: intervening on a correlated variable without owner/mechanism evidence.
8. **Probability theater**: assigning precise numbers unsupported by calibration or likelihood models.
9. **Research ritualism**: forcing the full protocol onto trivial tasks where it cannot change the decision.
10. **Endless inquiry**: continuing after evidence value falls below cost or the remaining question is normative/authority-bound.
11. **Hypothesis churn**: inventing a new explanation after every result without preserving prior predictions and why they failed.
12. **Fix-as-proof**: a symptom disappearing after a change does not by itself establish the claimed root cause.

## Verification Checklist

- [ ] Trigger class and operating mode match the uncertainty and consequence.
- [ ] Facts, reports, inferences, and missing evidence are separated.
- [ ] At least two meaningful hypotheses exist, or the single-hypothesis constraint is justified.
- [ ] Each material hypothesis has mechanism, prediction, assumptions, and falsifier.
- [ ] At least one probe discriminates among live hypotheses.
- [ ] Probe validity threats and exact environment are recorded.
- [ ] Evidence updates confidence without erasing dissent or alternatives.
- [ ] Intervention has a separate authority/safety gate.
- [ ] Reproduction and negative evidence match the claim's risk and scope.
- [ ] Final state is ratified, provisional, inconclusive, falsified, blocked, or reframed.
- [ ] For model-assisted inquiry, truth grounding, review quality, and orchestration certification are reported separately.
- [ ] Reusable writeback includes applicability, anti-conditions, falsifier, evidence, and demotion path.
