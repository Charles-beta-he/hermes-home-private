---
name: research-paper-writing
description: Use when you need guidance on end-to-end pipeline for writing ML/AI research papers — from experiment design through analysis, drafting, revision, and submission.
version: 1.1.0
author: Orchestra Research
license: MIT
title: Research Paper Writing Pipeline
dependencies:
- semanticscholar
- arxiv
- habanero
- requests
- scipy
- numpy
- matplotlib
- SciencePlots
platforms:
- linux
- macos
metadata:
  hermes:
    tags:
    - Research
    - Paper Writing
    - Experiments
    - ML
    - AI
    - NeurIPS
    - ICML
    - ICLR
    - ACL
    - AAAI
    - COLM
    - LaTeX
    - Citations
    - Statistical Analysis
    category: research
    related_skills:
    - arxiv
    - ml-paper-writing
    - subagent-driven-development
    - plan
    requires_toolsets:
    - terminal
    - files
---

# Research Paper Writing Pipeline

## Overview


End-to-end pipeline for producing publication-ready ML/AI research papers targeting **NeurIPS, ICML, ICLR, ACL, AAAI, and COLM**. This skill covers the full research lifecycle: experiment design, execution, monitoring, analysis, paper writing, review, revision, and submission.

This is **not a linear pipeline** — it is an iterative loop. Results trigger new experiments. Reviews trigger new analysis. The agent must handle these feedback loops.

<!-- ascii-guard-ignore -->
```
┌─────────────────────────────────────────────────────────────┐
│                    RESEARCH PAPER PIPELINE                  │
│                                                             │
│  Phase 0: Project Setup ──► Phase 1: Literature Review      │
│       │                          │                          │
│       ▼                          ▼                          │
│  Phase 2: Experiment     Phase 5: Paper Drafting ◄──┐      │
│       Design                     │                   │      │
│       │                          ▼                   │      │
│       ▼                    Phase 6: Self-Review      │      │
│  Phase 3: Execution &           & Revision ──────────┘      │
│       Monitoring                 │                          │
│       │                          ▼                          │
│       ▼                    Phase 7: Submission               │
│  Phase 4: Analysis ─────► (feeds back to Phase 2 or 5)     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```
<!-- ascii-guard-ignore-end -->

---

## When to Use

- You need guidance on end-to-end pipeline for writing ML/AI research papers — from experiment design through analysis, drafting, revision, and submission
- Don't use for: requests that do not need you need guidance on end-to-end pipeline for writing ML/AI research papers — from experiment design through analysis, drafting, revision, and submission; choose a more specific child skill or a broader routing skill that actually matches the task.
## When To Use This Skill

Use this skill when:
- **Starting a new research paper** from an existing codebase or idea
- **Designing and running experiments** to support paper claims
- **Writing or revising** any section of a research paper
- **Preparing for submission** to a specific conference or workshop
- **Responding to reviews** with additional experiments or revisions
- **Converting** a paper between conference formats
- **Writing non-empirical papers** — theory, survey, benchmark, or position papers (see [Paper Types Beyond Empirical ML](#paper-types-beyond-empirical-ml))
- **Designing human evaluations** for NLP, HCI, or alignment research
- **Preparing post-acceptance deliverables** — posters, talks, code releases

## Core Philosophy

1. **Be proactive.** Deliver complete drafts, not questions. Scientists are busy — produce something concrete they can react to, then iterate.
2. **Never hallucinate citations.** AI-generated citations have ~40% error rate. Always fetch programmatically. Mark unverifiable citations as `[CITATION NEEDED]`.
3. **Paper is a story, not a collection of experiments.** Every paper needs one clear contribution stated in a single sentence. If you can't do that, the paper isn't ready.
4. **Experiments serve claims.** Every experiment must explicitly state which claim it supports. Never run experiments that don't connect to the paper's narrative.
5. **Commit early, commit often.** Every completed experiment batch, every paper draft update — commit with descriptive messages. Git log is the experiment history.

### Proactivity and Collaboration

Detailed `Proactivity and Collaboration` guidance moved to `references/proactivity-and-collaboration.md`.

Load it only when this specialized branch is directly active; preserve root safety and verification rules.
## Phase 0: Project Setup

Detailed Phase 0 project setup moved to `references/phase-0-project-setup.md`.

Load it for archived research-paper setup workflows.

Minimum in-root rule: archived workflow is reference-only; verify current project conventions before use.

## Phase 1: Literature Review

Detailed Phase 1 literature review moved to `references/phase-1-literature-review.md`.

Load it for archived paper-writing literature review patterns.

Minimum in-root rule: verify citations and source quality before using.

## Phase 2: Experiment Design

Detailed Phase 2 experiment design moved to `references/phase-2-experiment-design.md`.

Load it for archived paper experiment planning.

Minimum in-root rule: map claims to experiments and define evaluation before running work.

## Phase 3: Experiment Execution & Monitoring

Detailed Phase 3 execution/monitoring moved to `references/phase-3-execution-monitoring.md`.

Load it for archived experiment execution patterns.

Minimum in-root rule: preserve experiment logs, failure notes, and reproducible outputs.

## Phase 4: Result Analysis

Detailed Phase 4 result analysis moved to `references/phase-4-result-analysis.md`.

Load it for archived result-analysis and paper-story workflows.

Minimum in-root rule: separate statistical evidence from narrative claims.

## Contribution (one sentence)
[The paper's main claim]

## Experiments Run

### Experiment 1: [Name]
- **Claim tested**: [Which paper claim this supports]
- **Setup**: [Model, dataset, config, number of runs]
- **Key result**: [One sentence with the number]
- **Result files**: results/exp1/final_info.json
- **Figures generated**: figures/exp1_comparison.pdf
- **Surprising findings**: [Anything unexpected]

### Experiment 2: [Name]
...

## Figures
| Filename | Description | Which section it belongs in |
|----------|-------------|---------------------------|
| figures/main_comparison.pdf | Bar chart comparing all methods on benchmark X | Results, Figure 2 |
| figures/ablation.pdf | Ablation removing components A, B, C | Results, Figure 3 |
...

## Failed Experiments (document for honesty)
- [What was tried, why it failed, what it tells us]

## Open Questions
- [Anything the results raised that the paper should address]
```

**Why this matters**: When drafting, the agent (or a delegated sub-agent) can load `experiment_log.md` alongside the LaTeX template and produce a first draft grounded in actual results. Without this bridge, the writing agent must parse raw JSON/CSV files and infer the story — a common source of hallucinated or misreported numbers.

**Git discipline**: Commit this log alongside the results it describes.

---

## Iterative Refinement: Strategy Selection

Any output in this pipeline — paper drafts, experiment scripts, analysis — can be iteratively refined. The autoreason research provides empirical evidence for when each refinement strategy works and when it fails. Use this section to choose the right approach.

### Quick Decision Table

Detailed `Quick Decision Table` guidance moved to `references/quick-decision-table.md`.

Load it only when this specialized branch is directly active; preserve root safety and verification rules.
### The Generation-Evaluation Gap

**Core insight**: Autoreason's value depends on the gap between a model's generation capability and its self-evaluation capability.

```
Model Tier        │ Generation │ Self-Eval │ Gap    │ Autoreason Value
──────────────────┼────────────┼───────────┼────────┼─────────────────
Weak (Llama 8B)   │ Poor       │ Poor      │ Small  │ None — can't generate diverse candidates
Mid (Haiku 3.5)   │ Decent     │ Poor      │ LARGE  │ MAXIMUM — 42/42 perfect Borda
Mid (Gemini Flash)│ Decent     │ Moderate  │ Large  │ High — wins 2/3
Strong (Sonnet 4) │ Good       │ Decent    │ Medium │ Moderate — wins 3/5
Frontier (S4.6)   │ Excellent  │ Good      │ Small  │ Only with constraints
```

This gap is structural, not temporary. As costs drop, today's frontier becomes tomorrow's mid-tier. The sweet spot moves but never disappears.

### Autoreason Loop (Summary)

Each pass produces three candidates from fresh, isolated agents:

1. **Critic** → finds problems in incumbent A (no fixes)
2. **Author B** → revises A based on critique
3. **Synthesizer** → merges A and B (randomized labels)
4. **Judge Panel** → 3 blind CoT judges rank A, B, AB via Borda count
5. **Convergence** → A wins k=2 consecutive passes → done

**Key parameters:**
- k=2 convergence (k=1 premature, k=3 too expensive, no quality gain)
- CoT judges always (3x faster convergence)
- Temperature 0.8 authors, 0.3 judges
- Conservative tiebreak: incumbent wins ties
- Every role is a fresh agent with no shared context

### Applying to Paper Drafts

When refining the paper itself through autoreason:
- **Provide ground truth to the critic**: actual experimental data, result JSONs, statistical outputs. Without this, models hallucinate fabricated ablation studies and fake confidence intervals.
- **Use 3 working judges minimum**: A broken judge parser doesn't add noise — it prevents equilibrium entirely.
- **Scope constrain the revision**: "Address these specific weaknesses" not "improve the paper."

### Failure Modes

| Failure | Detection | Fix |
|---------|-----------|-----|
| No convergence (A never wins) | A wins <15% over 20+ passes | Add scope constraints to the task |
| Synthesis drift | Word counts grow unboundedly | Constrain structure and deliverable |
| Degradation below single pass | Baselines score higher than iterated output | Switch to single pass; model may be too weak |
| Overfitting (code) | High public-test pass, low private-test pass | Use structured analysis, not just test feedback |
| Broken judges | Parsing failures reduce panel below 3 | Fix parser before continuing |

See [references/autoreason-methodology.md](references/autoreason-methodology.md) for complete prompts, Borda scoring details, model selection guide, scope constraint design patterns, and compute budget reference.

---

## Paper Drafting, Submission, and Deliverables

The detailed Phase 5+ paper drafting, self-review, submission preparation, workshop/short-paper, post-acceptance, Hermes integration, experiment log, reviewer criteria, common issues, and reference-doc sections were moved to `references/paper-drafting-submission-and-deliverables.md` to keep this archived skill under the Hermes skill-size limit.

Load that reference when rehabilitating or using this archived research-paper-writing workflow.

## Common Pitfalls

1. Loading this skill outside its trigger class and skipping a simpler, more direct path.
2. Ignoring prerequisites such as platform, credentials, installed commands, or linked reference files.
3. Treating the skill as a static memo instead of verifying the exact commands, artifacts, or outputs in the current environment.

## Verification Checklist

- [ ] The task actually matches this skill's trigger class and the current route is still appropriate.
- [ ] All prerequisites, linked references, templates, scripts, and required tools have been checked before execution.
- [ ] Claimed outputs, commands, files, or external side-effects were read back or otherwise verified before completion.
