# Memory Ownership Gate

Scope: Hermes durable-state and self-optimization landing decisions, especially after public-media or external-repo absorption. Applicability: use before writing memory, skills, project profiles, project docs, taskpool candidates, or experience-ratchet atoms. Anti-condition: do not use this gate as a reason to stop safe local SSOT/proposal work; if a write target is blocked, land evidence/proposal locally and continue the next safe reversible slice.

## Source pattern

Derived from the Raven/EverOS reference absorption pack:

- SSOT: `/Users/charles/wechat_video_analysis/project_absorption/raven-everos-absorption-ssot/`
- Evidence: `evidence/source-evidence.json`
- Capability graph: `graph/raven-everos-capability-graph.json`
- Experience atom: `raven-everos-absorption-385789b84700`

EverOS exposes a useful ownership split: user-owned memories (`episode`, `profile`) and agent-owned memories (`agent_case`, `agent_skill`). Hermes should preserve this separation conceptually even when landing zones differ.

## Gate

Before any durable write, classify the candidate into exactly one primary landing zone:

| Candidate | Primary landing zone | Write now when | Do not write when |
|---|---|---|---|
| Stable user preference, recurring correction, personal detail | `memory(target=user)` | Still true across many sessions; declarative; compact | WIP, project status, one-off repo fact, raw transcript |
| Stable environment/tool fact | `memory(target=memory)` | Rediscovery is costly; broadly reusable | Temporary failure, stale version/count, task outcome |
| Reusable procedure/pitfall/checklist | `skill` or skill `references/` | Has trigger, anti-condition, steps, pitfalls, verification | Broad ideology, one-off advice, unverified external claim |
| Project-specific rule, profile pointer, SSOT path | `project_profile` or project SSOT | Stable for that project | Global memory would overgeneralize it |
| Evidence from media/repo/session | `SSOT evidence` / `project_doc` | Needed to ground future work | It is being used as a general rule without abstraction |
| Cross-project behavior change | `experience-ratchet proposal` | Has evidence, applicability, anti-condition, falsifier | It would directly mutate core behavior without review |
| Concrete future implementation | `taskpool candidate` | Has target, artifact, risk, dependencies, verification | Vague improvement wish or already-completed work |
| Authority-expanding side effect | `do-not-do` until exact gate | Exact target, rollback, receipt, readback exist | User gave only broad trust or media/demo inspiration |

## Procedure

1. State the candidate claim in one sentence.
2. Strip source-specific names unless they are evidence refs.
3. Assign one primary landing zone using the table above.
4. Add anti-condition and falsifier for any reusable rule.
5. If the correct landing zone cannot be written safely now, write only a local SSOT/proposal and continue safe reversible preparation.
6. Never downgrade a blocked external/publish/destructive/credential action into a fake memory or vague skill.

## Verification

- Read back the artifact actually written.
- For skill/reference writes, load the skill or file and confirm the trigger/anti-condition survived.
- For experience-ratchet atoms, run `python3 ~/.hermes/scripts/experience-ratchet-maze.py validate`.
- For scoped self-changes under `~/.hermes`, stage exact files only and inspect `git diff --cached --name-only` before commit.
