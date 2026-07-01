# Social video / Agent pattern intake for taskpool

Use this when a user asks to analyze a Douyin/TikTok/video/social post and add it to the Hermes taskpool as an advisory/evolution candidate.

## Landing-zone classification

- Treat the source as social-post inspiration, not implementation proof.
- Create or update a taskpool candidate, not a skill, when the durable output is future analysis/engineering work.
- Store source-specific details in an evidence bundle or task note, not in global memory.
- Only promote to implementation after current Hermes surfaces are inspected and a read-only mapping/spec exists.

## Intake shape

Recommended task fields:

- lane: `advisory` for social/video idea analysis unless the user explicitly asks for implementation.
- priority: normally `P2` unless it is urgent/production-impacting.
- architecture_target: the Hermes surface being evaluated, e.g. `taskpool`, `runtime`, `skill-graph`.
- truth_gate: `social-post-is-inspiration-not-proof; verify against Hermes current behavior before implementation`.
- completion_boundary: `taskpool_candidate` for analysis-only intake.
- anti_drift_check: explicitly forbid direct production changes from a single social source.
- acceptance_evidence: source metadata/intake note + current-state mapping + gap/risk list + recommendation or read-only spec.
- parallel_boundary: prefer a source-stable key such as `boundary:source:<platform>:<video_id>:<pattern>` to avoid broad project-level conflicts.

## Evidence bundle minimum

Capture concise evidence, not a mirror of the source:

- original short URL and resolved URL, if available;
- title, author, video ID, publication time, visible tags/summary;
- capture method and limitations, e.g. metadata/visible chapter text only, no video download;
- extracted class-level pattern;
- anti-conditions: what must not be copied or inferred from this source alone.

## Agent-pattern example

For Agent Loop / runtime videos, map the idea to Hermes governance primitives instead of copying the content:

`observe -> context/evidence pack -> missing-field gate -> tool proposal/permission gate -> execute -> state/evidence writeback -> review/repair`

Compare this against Hermes objective-model-path, prerequisite checks, permission/evidence gates, tool loop, and taskpool lifecycle before proposing any implementation.

## Verification checklist

- Run taskpool selfcheck after adding the task.
- Run proof-check after adding evidence references.
- Read back the new task note and evidence bundle.
- If selfcheck reports a new broad `project:<name>` parallel-boundary conflict, add a source-specific `parallel_boundary` to the new task and rerun selfcheck.
