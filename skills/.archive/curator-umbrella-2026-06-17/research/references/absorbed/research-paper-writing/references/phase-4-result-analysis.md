# Research Paper Phase 4 Result Analysis

Extracted from `/Users/charles/.hermes/skills/.archive/curator-umbrella-2026-06-17/research/references/absorbed/research-paper-writing/SKILL.md` on 2026-07-01T08:57:36.131647+00:00 during full core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

## Phase 4: Result Analysis

**Goal**: Extract findings, compute statistics, identify the story.

### Step 4.1: Aggregate Results

Write analysis scripts that:
1. Load all result files from a batch
2. Compute per-task and aggregate metrics
3. Generate summary tables

```python
# Standard analysis pattern
import json, os
from pathlib import Path

results = {}
for result_file in Path("results/").rglob("result.json"):
    data = json.loads(result_file.read_text())
    strategy = result_file.parent.name
    task = result_file.parent.parent.name
    results.setdefault(strategy, {})[task] = data

# Compute aggregate metrics
for strategy, tasks in results.items():
    scores = [t["score"] for t in tasks.values()]
    print(f"{strategy}: mean={np.mean(scores):.1f}, std={np.std(scores):.1f}")
```

### Step 4.2: Statistical Significance

Always compute:
- **Error bars**: Standard deviation or standard error, specify which
- **Confidence intervals**: 95% CI for key results
- **Pairwise tests**: McNemar's test for comparing two methods
- **Effect sizes**: Cohen's d or h for practical significance

See [references/experiment-patterns.md](references/experiment-patterns.md) for complete implementations of McNemar's test, bootstrapped CIs, and Cohen's h.

### Step 4.3: Identify the Story

Detailed `Step 4.3: Identify the Story` guidance moved to `references/step-43-identify-the-story.md`.

Load it only when this specialized branch is directly active; preserve root safety and verification rules.
### Step 4.4: Create Figures and Tables

**Figures**:
- Use vector graphics (PDF) for all plots: `plt.savefig('fig.pdf')`
- Colorblind-safe palettes (Okabe-Ito or Paul Tol)
- Self-contained captions — reader should understand without main text
- No title inside figure — the caption serves this function

**Tables**:
- Use `booktabs` LaTeX package
- Bold best value per metric
- Include direction symbols (higher/lower better)
- Consistent decimal precision

```latex
\usepackage{booktabs}
\begin{tabular}{lcc}
\toprule
Method & Accuracy $\uparrow$ & Latency $\downarrow$ \\
\midrule
Baseline & 85.2 & 45ms \\
\textbf{Ours} & \textbf{92.1} & 38ms \\
\bottomrule
\end{tabular}
```

### Step 4.5: Decide: More Experiments or Write?

| Situation | Action |
|-----------|--------|
| Core claims supported, results significant | Move to Phase 5 (writing) |
| Results inconclusive, need more data | Back to Phase 2 (design) |
| Unexpected finding suggests new direction | Back to Phase 2 (design) |
| Missing one ablation reviewers will ask for | Run it, then Phase 5 |
| All experiments done but some failed | Note failures, move to Phase 5 |

### Step 4.6: Write the Experiment Log (Bridge to Writeup)

Before moving to paper writing, create a structured experiment log that bridges results to prose. This is the single most important connective tissue between experiments and the writeup — without it, the writing agent has to re-derive the story from raw result files.

**Create `experiment_log.md`** with the following structure:

```markdown
# Experiment Log
