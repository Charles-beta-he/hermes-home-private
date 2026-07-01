# Research Paper Phase 0 Project Setup

Extracted from `/Users/charles/.hermes/skills/.archive/curator-umbrella-2026-06-17/research/references/absorbed/research-paper-writing/SKILL.md` on 2026-07-01T08:57:36.131647+00:00 during full core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

## Phase 0: Project Setup

**Goal**: Establish the workspace, understand existing work, identify the contribution.

### Step 0.1: Explore the Repository

```bash
# Understand project structure
ls -la
find . -name "*.py" | head -30
find . -name "*.md" -o -name "*.txt" | xargs grep -l -i "result\|conclusion\|finding"
```

Look for:
- `README.md` — project overview and claims
- `results/`, `outputs/`, `experiments/` — existing findings
- `configs/` — experimental settings
- `.bib` files — existing citations
- Draft documents or notes

### Step 0.2: Organize the Workspace

Establish a consistent workspace structure:

```
workspace/
  paper/               # LaTeX source, figures, compiled PDFs
  experiments/         # Experiment runner scripts
  code/                # Core method implementation
  results/             # Raw experiment results (auto-generated)
  tasks/               # Task/benchmark definitions
  human_eval/          # Human evaluation materials (if needed)
```

### Step 0.3: Set Up Version Control

```bash
git init  # if not already
git remote add origin <repo-url>
git checkout -b paper-draft  # or main
```

**Git discipline**: Every completed experiment batch gets committed with a descriptive message. Example:
```
Add Monte Carlo constrained results (5 runs, Sonnet 4.6, policy memo task)
Add Haiku baseline comparison: autoreason vs refinement baselines at cheap model tier
```

### Step 0.4: Identify the Contribution

Before writing anything, articulate:
- **The What**: What is the single thing this paper contributes?
- **The Why**: What evidence supports it?
- **The So What**: Why should readers care?

> Propose to the scientist: "Based on my understanding, the main contribution is: [one sentence]. The key results show [Y]. Is this the framing you want?"

### Step 0.5: Create a TODO List

Use the `todo` tool to create a structured project plan:

```
Research Paper TODO:
- [ ] Define one-sentence contribution
- [ ] Literature review (related work + baselines)
- [ ] Design core experiments
- [ ] Run experiments
- [ ] Analyze results
- [ ] Write first draft
- [ ] Self-review (simulate reviewers)
- [ ] Revise based on review
- [ ] Submission prep
```

Update this throughout the project. It serves as the persistent state across sessions.

### Step 0.6: Estimate Compute Budget

Detailed `Step 0.6: Estimate Compute Budget` guidance moved to `references/step-06-estimate-compute-budget.md`.

Load it only when this specialized branch is directly active; preserve root safety and verification rules.
### Step 0.7: Multi-Author Coordination

Detailed `Step 0.7: Multi-Author Coordination` guidance moved to `references/step-07-multi-author-coordination.md`.

Load it only when this specialized branch is directly active; preserve root safety and verification rules.
