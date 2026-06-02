# Agent Psychology Core Works for Abstraction Governance

This reference is loaded when the task needs theory-backed abstraction control rather than only an operational checklist.

## Cognitive science and abstraction

| Work | Core claim | Agent implication |
|---|---|---|
| David Marr, `Vision` | Analyze systems at computational, algorithmic/representational, and implementation levels. | Do not solve a goal-level problem with only an implementation-level command. Identify whether the issue is target, representation, rule, tool, or meta-rule. |
| Allen Newell, `The Knowledge Level` | Explain intelligent behavior by goals, knowledge, and rational action under beliefs. | Incident review should inspect belief state: what did the agent know, infer, miss, or confuse? |
| Frederic Bartlett, `Remembering` | Memory is reconstructed through schemas, not merely replayed. | Treat memories/reflections as reconstructed candidates; preserve provenance and avoid automatic promotion. |
| Rumelhart; Schank & Abelson | Schemas/scripts guide understanding but can mislead when slots are guessed. | Make default task scripts explicit; mark unknown slots rather than filling them silently. |
| Gick & Holyoak; Gentner | Transfer and analogy depend on deep structure/relations, not surface similarity. | Strip project names and map roles/relations before claiming a cross-context rule. |
| Perkins & Salomon; Barnett & Ceci | Far transfer requires deliberate abstraction and boundary analysis. | Use scope tagging and anti-conditions before moving project experience to domain/global guidance. |
| Chi, Feltovich & Glaser | Experts categorize by deep principles; novices by surface features. | Reclassify incidents by failure mechanism (role confusion, verification gap, gate missing) rather than tool label (Git/frontend/backend). |
| Flavell; Nelson & Narens; Stanovich | Metacognition monitors and controls object-level cognition. | Add an abstraction self-check: level, evidence, transfer distance, counterexamples, and confidence. |

## Organizational psychology, cybernetics, and error recovery

| Work | Core claim | Agent implication |
|---|---|---|
| Argyris & Schoen, `Organizational Learning` | Single-loop learning changes actions; double-loop learning changes governing assumptions. | Ask whether the fix is a command tweak, workflow rule, runtime gate, or meta-policy about how rules are formed. |
| Karl Weick, `Sensemaking in Organizations` | Actors construct actionable meanings under ambiguity; old frames can collapse in crises. | Maintain an explicit situation model and competing frames before abstracting a user correction. |
| Herbert Simon, `The Sciences of the Artificial` / bounded rationality | Agents satisfice under limits; design uses hierarchy and decomposition. | State information limits; choose enough evidence for the risk level; do not pretend global certainty. |
| Wiener / Ashby / Beer | Control requires feedback; necessary variety; viable systems need layered control. | Experience governance needs multiple surfaces: profile, skill, gate, ADR, eval, not one global memory blob. |
| Powers; Carver & Scheier | Behavior controls perception relative to reference goals in layers. | When results disappoint, inspect which goal layer failed: action, task, relation, safety, or value. |
| Schoen; Dreyfus; Klein | Expertise is situation recognition plus reflection-in-action. | Advanced agents should detect anomalies and know when an old pattern no longer fits. |
| James Reason; Rasmussen; Hollnagel | Accidents reflect layered defense failures; behavior can be skill/rule/knowledge based; resilient systems recover. | Classify errors by layer and build defenses: clarification, preflight, verification, rollback, review. |

## AI agent / HCI / AI safety parallels

| Work | Core claim | Agent implication |
|---|---|---|
| ReAct | Reasoning, action, and observation should be separated. | Tool observations are local facts until promoted through evidence gates. |
| Reflexion / Self-Refine | Verbal reflection can improve later attempts. | Reflection is a candidate, not memory; scope and verify before landing. |
| Generative Agents | Memory stream plus reflection and planning supports continuity. | Keep raw events and higher-level reflections separate. |
| MemGPT / Letta | Working, core, and archival memory need explicit management. | Put only stable, high-value user facts in core memory; project facts stay scoped. |
| Voyager | Reusable skills should be parameterized and environment-independent. | A skill should say how to discover a base branch, not hardcode a branch name. |
| Lost in the Middle | Long context can hide important information. | Preserve key constraints in structured summaries and verification checklists. |
| TruthfulQA / calibration work | Fluency is not truth; models need uncertainty calibration. | Bind confidence to evidence, not rhetorical certainty. |
| Concrete Problems in AI Safety / specification gaming | Optimizing the wrong metric causes harmful shortcuts. | Avoid fake completion, skipped verification, and over-broad rules made to look decisive. |
| Corrigibility / Off-Switch Game / HAI guidelines | Agents should be interruptible, correctable, and transparent to users. | High-risk abstraction/rule changes need clear state, approval, rollback, and correction paths. |

## Minimal reading sequence

1. Marr + Newell — level separation and belief-state framing.
2. Bartlett + schema/script theory — why default frames contaminate abstraction.
3. Gentner + Gick/Holyoak — structure mapping and far transfer.
4. Flavell/Nelson/Narens — metacognitive monitoring.
5. Argyris/Schoen + Reason/Rasmussen — double-loop learning and error layers.
6. ReAct + Reflexion + MemGPT + Voyager — agent-specific equivalents.

## Practical maxim

Engineering theory tells the agent where a rule should live. Cognitive theory tells the agent why it might put the rule in the wrong place, and which self-check can catch that before the mistake becomes durable state.
