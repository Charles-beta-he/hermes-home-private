# SkillOpt Minibatch Reflection → Hermes Experience-Ratchet Prototype Design

Date: 2026-05-29
Parent task: 评估 SkillOpt ReflACT 管线对 Hermes 技能自演化的可迁移性
Source: `~/.hermes/runs/skillopt-reference-review/skillopt/gradient/reflect.py`
Target: `~/.hermes/scripts/experience-ratchet-maze.py`

## 1. Mapping: SkillOpt Reflect → Hermes Atoms

| SkillOpt Concept | Hermes Equivalent | Notes |
|---|---|---|
| Trajectory (conversation + outcome) | ExperienceAtom | Atoms already capture context, action, outcome, evidence |
| Minibatch (M trajectories grouped) | Atom group by `failure_type` or `skill_id` | Grouping key is the critical design choice |
| Error analyst call | `batch-reflect --mode failure` | LLM call over grouped atoms |
| Success analyst call | `batch-reflect --mode success` | Preserve what worked |
| Edit budget (L edits) | Configurable `--max-insights` | Maps to `promoted_candidate` count |
| Meta-skill context | `meta_skill/` directory | Cross-epoch optimizer memory |
| Step buffer context | Previous batch-reflect results in same run | Prevents repeating same insight |

## 2. Current Hermes Gap (validated against code)

`experience-ratchet-maze.py` (425 LOC) has:
- ✅ Atom lifecycle: `captured → normalized → challenged → validated → promoted_candidate → promoted`
- ✅ Evidence gates: `EVIDENCE_REQUIRED = {"validated", "promoted_candidate", "promoted"}`
- ✅ Query: `query` subcommand with status/skill filters
- ✅ Proposals: `propose` subcommand for landing-zone artifacts
- ❌ No batch analysis — atoms processed one-at-a-time
- ❌ No cross-atom pattern extraction
- ❌ No meta-skill memory directory
- ❌ No minibatch grouping strategy

## 3. Proposed: `batch-reflect` Subcommand

### 3.1 CLI Interface

```bash
# Group by failure type, analyze in minibatches of 5
python3 experience-ratchet-maze.py batch-reflect \
  --group-by failure_type \
  --minibatch-size 5 \
  --mode failure \
  --max-insights 3 \
  --skill-filter "taskpool-control-plane"

# Group by skill, analyze successes
python3 experience-ratchet-maze.py batch-reflect \
  --group-by skill_id \
  --minibatch-size 3 \
  --mode success
```

### 3.2 Grouping Strategy

```python
def group_atoms(atoms: list[dict], group_by: str) -> dict[str, list[dict]]:
    """Group atoms for minibatch analysis."""
    groups = {}
    for atom in atoms:
        if group_by == "failure_type":
            key = atom.get("outcome", {}).get("failure_type", "unknown")
        elif group_by == "skill_id":
            key = atom.get("context", {}).get("skill_id", "no_skill")
        elif group_by == "project":
            key = atom.get("context", {}).get("project", "no_project")
        else:
            key = "all"
        groups.setdefault(key, []).append(atom)
    return groups
```

### 3.3 Minibatch Analysis Prompt (adapted from SkillOpt reflect.py)

```
## System
You are an experience analyst. Given a group of related experience atoms
(all sharing the same failure pattern or skill), identify systemic patterns
and propose actionable improvements.

## Current Skill Context
{skill_content_if_applicable}

## Previous Batch Insights (this run)
{step_buffer_context}

## Experience Atoms ({count} total, grouped by {group_by}={group_key})
{formatted_atoms}

## Task
Produce at most {max_insights} insights in JSON:
{
  "pattern": "systemic description of what's going wrong/right",
  "root_cause": "why this keeps happening",
  "insights": [
    {
      "type": "skill_edit" | "process_change" | "new_test" | "config_change",
      "target": "which skill/process/config to modify",
      "description": "what to change",
      "evidence": "which atoms support this"
    }
  ]
}
```

### 3.4 Output: Promoted Candidates

Each insight becomes a `promoted_candidate` atom with:
- `source: "batch-reflect"`
- `group_by`: the grouping key
- `minibatch_size`: how many atoms were analyzed
- `parent_atoms`: list of atom IDs that contributed
- Status: `validated` (has evidence from multiple atoms) → eligible for `promote`

### 3.5 Meta-Skill Memory

```
~/.hermes/experience-ratchet/meta_skill/
  taskpool-control-plane.md    # cross-epoch guidance for this skill
  hermes-agent.md              # cross-epoch guidance for this skill
  _global.md                   # cross-skill patterns
```

Updated after each batch-reflect run:
```python
def update_meta_skill(skill_id: str, new_insights: list[dict], prev_meta: str) -> str:
    """Merge new insights into cross-epoch optimizer memory."""
    # Prompt: given prev_meta + new_insights, produce updated guidance
    # Keep compact (< 2000 chars) — this feeds into future batch-reflect calls
```

## 4. Integration Points

### 4.1 New files needed
- None — all changes go into `experience-ratchet-maze.py` (add `batch-reflect` subcommand)
- New directory: `~/.hermes/experience-ratchet/meta_skill/`

### 4.2 Existing code to reuse
- `load_atoms(home)` — already loads all atoms
- `query(args)` — already filters by status/skill
- `append_log(home, event)` — already logs events
- `write_json(path, data)` — already writes atom files
- `now_iso()` — already timestamps

### 4.3 LLM call
SkillOpt uses `chat_optimizer()` which is its own OpenAI wrapper. For Hermes:
- Use `hermes chat --provider <provider> -m <model> -q '<prompt>' --quiet --max-turns 1`
- Or call the AIAgent directly if running inside Hermes context
- Default: current Hermes main model (no extra cost beyond the analysis call)

## 5. Verification Plan

1. **Dry run**: `batch-reflect --dry-run` shows grouping + prompt without LLM call
2. **Smoke test**: Create 3 test atoms with known failure pattern, run `batch-reflect`, verify pattern extracted
3. **Integration test**: Run on real `~/.hermes/experience-ratchet/atoms/` if any exist
4. **Meta-skill roundtrip**: Run batch-reflect twice, verify second run uses first run's meta-skill context

## 6. Effort Estimate

- Phase 1 (batch-reflect subcommand): ~150 LOC addition to experience-ratchet-maze.py
- Phase 2 (meta-skill memory): ~80 LOC + directory setup
- Phase 3 (integration with bg-review/taskpool hooks): separate task

## 7. Risk Assessment

- **LLM cost**: One call per minibatch (typically 1-3 calls per run). Acceptable.
- **Quality**: Batch analysis may produce generic insights if atoms lack detail. Mitigated by requiring evidence from multiple atoms.
- **Atom availability**: Hermes experience-ratchet currently has few/no atoms in production. This is a forward-looking design; the mechanism needs to exist before atoms accumulate.

## 8. Decision

This prototype design validates the HIGH transferability claim from the gap analysis. The minibatch reflection pattern maps cleanly onto the existing experience-ratchet-maze.py atom lifecycle. Implementation is ~230 LOC total, no new dependencies, and reuses all existing infrastructure.

The design is ready for implementation when the user authorizes a Phase 1 coding session.
