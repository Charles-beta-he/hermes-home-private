# SKILL.md as an Entry Contract: 5 Internal Control-Flow Modes

Extracted from `/Users/charles/.hermes/skills/software-development/hermes-agent-skill-authoring/SKILL.md` on 2026-07-01T08:55:33.664327+00:00 by generic core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

## SKILL.md as an Entry Contract: 5 Internal Control-Flow Modes

Treat `SKILL.md` as the entry contract. Keep the shared routing skeleton stable: `name`, `description`, and—when the surrounding library uses them—`level` and `requires`. `description` remains the primary trigger surface that determines when the skill should load. The main design choice is the internal control-flow shape inside the body.

### The five modes

1. **Wrapper**
   - Shape: `SKILL.md -> reference -> agent capability`
   - Use when the skill's main job is to expose or normalize an external capability, SDK, API, toolchain, or operational surface.
   - Typical body: prerequisites, exact commands, capability map, parameter caveats, verification steps.

2. **Generator**
   - Shape: `SKILL.md -> template + data -> output`
   - Use when the output format is stable and repeatable: reports, contracts, specs, briefs, summaries, checklists, or other templated deliverables.
   - Typical body: input schema, template slots, transformation rules, acceptance examples.

3. **Reviewer**
   - Shape: `input -> checklist -> graded report`
   - Use when the skill is a quality gate, audit pass, static review, or rules-based inspection layer.
   - Typical body: review dimensions, scoring rubric, fail/warn/pass conditions, evidence requirements.

4. **Inversion**
   - Shape: role inversion — the agent leads the interrogation, the user answers, and the agent synthesizes.
   - Use when requirements are unclear, context is missing, or the agent must actively elicit constraints before producing a safe result.
   - Typical body: interview sequence, branching questions, synthesis rules, stop conditions.

5. **Pipeline**
   - Shape: mandatory ordered stages with checkpoints and no step-skipping.
   - Use when the workflow is multi-step and each step must produce a verifiable artifact before the next one begins.
   - Typical body: stage list, inputs/outputs per stage, gating checks, rollback/retry rules.

### Selection heuristic

| Scenario | Prefer |
|----------|--------|
| Calling a complex SDK/API/toolchain | Wrapper |
| Fixed-format deliverable | Generator |
| Quality gate / static audit / review | Reviewer |
| Ambiguous request / missing context | Inversion |
| Multi-step workflow with verifiable artifacts | Pipeline |

### Shared contract across all five modes

Regardless of mode, keep the entry contract stable:

- Frontmatter remains the router-facing contract: `name`, `description`, and—when the surrounding library uses them—`level` and `requires`
- `description` remains the primary trigger surface that decides when the skill should load
- The mode only changes the internal organization of the body, not the external routing contract
- Rich session-specific detail belongs in `references/`, reusable starter artifacts belong in `templates/`, and deterministic repeatable actions belong in `scripts/`

### Context-budget contract (index / load / runtime)

Treat every skill as three cost layers, not one markdown blob:

1. **Index layer** — `name` + `description`
   - Paid in every session for every user
   - Keep the description trigger-oriented, compact, and free of workflow summary
   - Bad pattern: explaining what the skill does
   - Better pattern: stating *when* to load it in the user's language
2. **Load layer** — root `SKILL.md` body
   - Paid after the skill loads and competes with other loaded skills
   - Keep only high-signal workflow decisions, branch points, pitfalls, and verification
   - If the model likely already knows a command sequence, do not spend root-body budget on it
3. **Runtime layer** — `references/`, `templates/`, `scripts/`, `assets/`
   - Paid only when read or executed
   - Move conditional branches, long domain notes, heavy docs, templates, and deterministic helper logic here

Heuristic: if the root body starts reading like a README, command cheat sheet, or long domain memo, split it. Prefer a short SKILL.md plus progressive disclosure into `references/`.

### Description quality checklist

When reviewing or rewriting `description`, check all of these:

- It answers **when to load**, not **what the skill does**
- It uses the user's likely intent language, not internal implementation language
- It avoids summarizing the workflow or tool steps
- It helps separate adjacent skills and reduce off-target loads
- It is short enough that every word earns its place in the global index budget

If the description changed materially, treat it as routing logic and pair it with explicit positive + negative trigger evals.

### Gotcha-first maintenance rule

For mature skills, the highest-value growth is usually append-mostly:

- Agent failed in-domain -> add a gotcha, negative example, or tighter verification step
- Agent loaded off-target -> tighten description and add negative evals
- Agent missed a valid trigger -> add intent phrasing and positive evals

Do **not** default to making the main workflow longer. Prefer recording the sharp edge that caused the failure, and move bulky or conditional detail into `references/`.

### Authoring implication

Do not treat every skill as a generic prose memo. Pick one primary mode first, then structure the skill body to match that control-flow. Hybrid skills are allowed, but the dominant mode should be obvious from the section layout and verification pattern.
