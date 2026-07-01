# Research Paper Phase 2 Experiment Design

Extracted from `/Users/charles/.hermes/skills/.archive/curator-umbrella-2026-06-10/research/research-paper-writing/SKILL.md` on 2026-07-01T08:57:36.131647+00:00 during full core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

## Phase 2: Experiment Design

**Goal**: Design experiments that directly support paper claims. Every experiment must answer a specific question.

### Step 2.1: Map Claims to Experiments

Create an explicit mapping:

| Claim | Experiment | Expected Evidence |
|-------|-----------|-------------------|
| "Our method outperforms baselines" | Main comparison (Table 1) | Win rate, statistical significance |
| "Effect is larger for weaker models" | Model scaling study | Monotonic improvement curve |
| "Convergence requires scope constraints" | Constrained vs unconstrained | Convergence rate comparison |

**Rule**: If an experiment doesn't map to a claim, don't run it.

### Step 2.2: Design Baselines

Strong baselines are what separates accepted papers from rejected ones. Reviewers will ask: "Did they compare against X?"

Standard baseline categories:
- **Naive baseline**: Simplest possible approach
- **Strong baseline**: Best known existing method
- **Ablation baselines**: Your method minus one component
- **Compute-matched baselines**: Same compute budget, different allocation

### Step 2.3: Define Evaluation Protocol

Before running anything, specify:
- **Metrics**: What you're measuring, direction symbols (higher/lower better)
- **Aggregation**: How results are combined across runs/tasks
- **Statistical tests**: What tests will establish significance
- **Sample sizes**: How many runs/problems/tasks

### Step 2.4: Write Experiment Scripts

Detailed `Step 2.4: Write Experiment Scripts` guidance moved to `references/step-24-write-experiment-scripts.md`.

Load it only when this specialized branch is directly active; preserve root safety and verification rules.
### Step 2.5: Design Human Evaluation (If Applicable)

Detailed `Step 2.5: Design Human Evaluation (If Applicable)` guidance moved to `references/step-25-design-human-evaluation-if-applicable.md`.

Load it only when this specialized branch is directly active; preserve root safety and verification rules.
