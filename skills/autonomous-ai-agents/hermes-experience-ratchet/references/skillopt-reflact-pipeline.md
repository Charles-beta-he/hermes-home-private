# SkillOpt ReflACT Pipeline — Research Reference for Skill Optimization

## Source

- **Repo**: https://github.com/microsoft/SkillOpt
- **Paper**: arXiv:2605.23904 (May 2026)
- **Authors**: Microsoft Research

## Core Idea

Treat agent skill documents (Markdown) as "model weights" and iteratively optimize them through a training-loop analogy. The skill document is the "model", task rollouts produce "loss signals", and the optimizer proposes "gradient-like edits".

## ReflACT 6-Stage Pipeline

```
Rollout → Reflect → Aggregate → Select → Update → Gate
```

| Stage | Function | Analogy |
|-------|----------|---------|
| **Rollout** | Execute tasks with current skill | Forward pass |
| **Reflect** | Analyze failures in minibatches | Loss computation |
| **Aggregate** | Hierarchical LLM-driven patch merging | Gradient accumulation |
| **Select** | Rank and clip edits (keep top-K) | Gradient clipping |
| **Update** | Apply edits to skill document | Weight update |
| **Gate** | Validate on held-out tasks; accept/reject | Validation gate |

## Key Innovations

### 1. Minibatch Reflection
Instead of reflecting on each failure individually, group M failures and analyze patterns across them. This surfaces systemic issues (e.g., "the skill consistently mishandles edge case X") rather than one-off fixes.

### 2. Autonomous Learning Rate
The optimizer LLM decides how many edits to apply per step. Aggressive edits when errors are systematic; conservative edits when errors are diverse. Maps to cosine/linear/constant LR schedulers.

### 3. Meta-Skill Memory
Cross-epoch guidance stored on the optimizer side. Distills what worked/didn't across iterations into a "meta skill" that improves future edit proposals. Stored as a separate document.

### 4. Slow Update (Epoch-Level)
Longitudinal comparison across epochs. Protected regions in skill documents (`<!-- SLOW_UPDATE_START/END -->`) that shouldn't be changed frequently. Prevents oscillation.

### 5. Step Buffer
Unified context containing: failure patterns from current step + rejected edits from previous step. Fed to the optimizer in the next iteration for richer context.

### 6. Validation Gate
Performance delta on held-out tasks determines accept/reject. If new skill performs worse, revert. This is the key safety mechanism.

## Mapping to Hermes Experience-Ratchet

| SkillOpt | Hermes Experience-Ratchet |
|----------|--------------------------|
| Skill document (Markdown) | SKILL.md files |
| Rollout (task execution) | task_observer monitoring |
| Reflect (failure analysis) | experience_atom capture |
| Aggregate (patch merging) | skill_manage patch |
| Select (edit ranking) | multi-model certification vote |
| Update (apply edits) | skill_manage edit |
| Gate (validation) | evidence gate + completion gate |
| Meta-skill memory | **MISSING** — could be added to `~/.hermes/experience/meta_skill/` |
| Slow update regions | **MISSING** — could use HTML comment markers in SKILL.md |
| Minibatch reflection | **MISSING** — current ratchet processes atoms one-at-a-time |

## Integration Proposal

### Phase 1: Adopt Patterns (no code integration)
- Study reflect prompt templates for batch failure analysis
- Adapt minibatch grouping strategy for experience-ratchet

### Phase 2: Prototype Skill Optimizer
- Build script: skill + test tasks → run → reflect → propose edits → gate → apply
- Use SkillOpt's prompt templates as reference

### Phase 3: Meta-Skill Memory
- Add optimizer-side memory: `~/.hermes/experience/meta_skill/`
- Distill what worked/didn't across optimization iterations

### Phase 4: Full Pipeline
- Integrate SkillOpt as Hermes plugin if Phases 1-3 prove valuable

## Pitfalls

- SkillOpt assumes automated rollouts with measurable scores — only applies to subset of Hermes use cases (automated pipelines, not interactive chat)
- Training-loop paradigm may over-engineer skills that naturally evolve through human authoring
- Meta-skill memory risks "optimizer drift" if not gated by evidence
- Protected regions (slow update) need careful design to avoid blocking legitimate improvements
