# SkillOpt ReflACT → Hermes Skill Self-Evolution: Transferability Gap Analysis

Date: 2026-05-29
Task: 评估 SkillOpt ReflACT 管线对 Hermes 技能自演化的可迁移性
Source: https://github.com/microsoft/SkillOpt (cloned at ~/.hermes/runs/skillopt-reference-review/)
Paper: arXiv:2605.23904 (May 2026, Microsoft Research)

## 1. SkillOpt ReflACT Pipeline Architecture

The 6-stage pipeline maps training-loop concepts onto skill document optimization:

```
Rollout → Reflect → Aggregate → Select → Update → Gate
```

| Stage | Implementation | LOC | Key Mechanism |
|-------|---------------|-----|---------------|
| Rollout | `engine/trainer.py` | 1912 | Execute tasks with current skill document; measure hard/soft scores |
| Reflect | `gradient/reflect.py` | 588 | Minibatch trajectory analysis — group M failures, surface systemic patterns |
| Aggregate | `gradient/aggregate.py` | 253 | Hierarchical LLM-driven patch merging with level-based tree reduction |
| Select | `optimizer/clip.py` | 109 | LLM-driven edit ranking; keep top-L (gradient clipping analogy) |
| Update | `optimizer/rewrite.py` + `lr_autonomous.py` | 167 | Full rewrite from suggestions OR patch application; autonomous LR decides edit count |
| Gate | `evaluation/gate.py` | 73 | Pure accept/reject: candidate score > current → accept; else reject and revert |

Supporting modules:
- `optimizer/meta_skill.py` (87 LOC): Cross-epoch optimizer memory; distills what worked/didn't into guidance for future edit proposals
- `optimizer/slow_update.py` (393 LOC): Protected skill regions via `<!-- SLOW_UPDATE_START/END -->` markers; epoch-level longitudinal comparison prevents oscillation

## 2. Hermes Experience-Ratchet Current State

| Capability | Implementation | Gap |
|------------|---------------|-----|
| Skill documents (Markdown) | SKILL.md files | ✅ Same substrate |
| Task execution / rollout | task_observer monitoring | ⚠️ Passive observation, no structured rollout with measurable scores |
| Failure analysis / reflect | experience_atom capture | ❌ One-at-a-time atoms, no minibatch grouping |
| Patch merging / aggregate | skill_manage patch | ❌ No hierarchical merging; single LLM call |
| Edit ranking / select | multi-model certification vote | ⚠️ Certification exists but not edit-level ranking |
| Update application | skill_manage edit | ✅ Works |
| Validation gate | evidence gate + completion gate | ⚠️ Gate exists but not score-based accept/reject with revert |
| Meta-skill memory | MISSING | ❌ Could go in `~/.hermes/experience/meta_skill/` |
| Slow update regions | MISSING | ❌ Could use HTML comment markers in SKILL.md |
| Autonomous learning rate | MISSING | ❌ Current ratchet has no concept of edit budget per step |

## 3. Transferability Assessment

### HIGH transferability (adopt patterns, no code integration):

1. **Minibatch reflection** — Group experience atoms by failure pattern instead of processing one-at-a-time. Hermes already captures atoms; adding a "batch reflect" mode that feeds M atoms to an LLM for systemic pattern extraction is straightforward. Implementation: new `experience-ratchet-maze.py batch-reflect` subcommand.

2. **Meta-skill memory** — Store optimizer-side guidance in `~/.hermes/experience/meta_skill/`. After each skill optimization round, distill what edits worked vs. failed. Feed this context into future `skill_manage` proposals. Implementation: new file per skill, updated after each promotion cycle.

3. **Protected regions (slow_update)** — Add `<!-- HERMES_SLOW_UPDATE_START/END -->` markers to SKILL.md files. The experience-ratchet should not modify these regions during step-level edits; only epoch-level review can update them. Implementation: regex filter in skill_manage edit path.

### MEDIUM transferability (prototype needed):

4. **Validation gate with revert** — Current Hermes gates check evidence presence, not performance delta. SkillOpt's gate compares candidate score > current score and reverts if worse. For Hermes: run a held-out evaluation prompt set before/after skill edit; accept only if quality improves. Requires defining "quality" metrics for SKILL.md files (e.g., task completion rate, error rate in guided sessions).

5. **Autonomous learning rate** — Let the optimizer decide how many edits to apply per step based on error diversity. Maps to Hermes's `skill_manage` proposing N edits instead of always 1. Implementation: LLM call that inspects the merged patch and returns an edit count.

### LOW transferability (significant adaptation needed):

6. **Full rollout-based training loop** — SkillOpt assumes automated rollouts with measurable scores (SearchQA accuracy, ALFWorld success rate). Hermes skill optimization is mostly interactive (chat sessions, task execution) where "score" is hard to define. The epoch/step/batch structure only applies to automated pipeline use cases.

7. **Environment adapters** — SkillOpt's `EnvAdapter` pattern (ALFWorld, SearchQA, WebArena) is benchmark-specific. Hermes would need a generic "skill evaluation adapter" that runs test prompts and measures quality — a non-trivial design problem.

## 4. Recommended Integration Path

### Phase 1: Adopt patterns (no code) — 1-2 sessions
- Study reflect.py prompt templates for batch failure analysis
- Design minibatch grouping strategy for experience atoms (by project, by failure type, by skill)
- Draft meta-skill memory format

### Phase 2: Prototype — 2-3 sessions
- `experience-ratchet-maze.py batch-reflect --group-by failure_type` subcommand
- `experience-ratchet-maze.py meta-skill --skill <name>` for cross-epoch guidance
- Add slow_update markers to 2-3 existing SKILL.md files as test

### Phase 3: Validation gate — 2-3 sessions
- Define skill quality metric (structured test prompt set + LLM judge)
- Implement accept/reject gate in skill_manage edit path
- Wire revert capability

### Phase 4: Full pipeline plugin — 3-5 sessions
- Hermes plugin wrapping SkillOpt's ReflACT loop for automated pipeline skills only
- Not for interactive chat skills — only for measurable task-completion skills

## 5. Key Risks

1. **Score definition** — SkillOpt's entire loop depends on measurable scores. Hermes skills span interactive chat, code generation, and task automation; defining universal quality metrics is the hardest gap.
2. **Over-engineering** — The training-loop paradigm may be excessive for skills that naturally evolve through human authoring and task-pool feedback.
3. **Meta-skill drift** — Optimizer-side memory could accumulate stale guidance if not gated by evidence.
4. **Cost** — Each ReflACT step requires multiple LLM calls (reflect + aggregate + select + lr + gate). For Hermes with multi-model certification already expensive, adding 5+ LLM calls per skill edit is significant.

## 6. Verdict

SkillOpt ReflACT is a **valuable reference architecture** for formalizing Hermes's ad-hoc skill evolution into a structured optimization loop. The minibatch reflection, meta-skill memory, and protected regions are directly transferable patterns. The full training loop is only applicable to automated pipeline skills, not interactive chat.

The anti-drift check holds: SkillOpt does NOT replace `skill_manage` or `experience-ratchet` — it provides formal optimization loop patterns that can be layered on top.

**Recommendation**: Proceed with Phase 1-2 (pattern adoption + prototype). Defer Phase 3-4 until Phase 2 proves value on real Hermes skill optimization scenarios.
