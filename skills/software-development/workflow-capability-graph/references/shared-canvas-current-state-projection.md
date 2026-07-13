# Shared Canvas Current-State Projection

Use this pattern when a task has multiple files, decisions, branches, roles, dependencies, agents, or a long execution horizon and the chronological chat no longer reliably communicates the current state.

## Core distinction

```text
Chat/session transcript = event history: what was said and tried.
Canonical state graph = current truth: what is active, superseded, blocked, owned, and evidenced.
Canvas = human-editable spatial projection of that graph.
Markdown/files = detailed content and source evidence.
Tasks/agents = execution over validated state transitions.
```

A Canvas must not silently become the SSOT merely because it is visually convenient. Treat it as a projection unless a project explicitly defines a schema, revision protocol, ownership rules, conflict handling, validation and readback.

## Source basis

- Sensecape, UIST 2023: multilevel canvas/hierarchy exploration can help users explore more topics and organize knowledge hierarchically, while the paper also reports novelty, learning-curve, clutter and interface-cost limits: <https://arxiv.org/abs/2305.11483>
- CanvasConvo, 2026 working draft: a five-day field study with 24 participants observed longer canvas sessions (34.1 minutes) than chat sessions (13.0 minutes), branching and revisitation; it also reports navigation, view-switching and branch-relationship challenges: <https://arxiv.org/abs/2605.15848>
- JSON Canvas 1.0: open `nodes` + `edges` format with text/file/link/group nodes and explicit geometry: <https://jsoncanvas.org/spec/1.0/>
- Cursor Canvas: durable, agent-created interactive artifacts alongside terminal/browser/source control; vendor-described uses include incident response, PR review, eval analysis and autoresearch: <https://cursor.com/blog/canvas>
- Formulasearch article analyzed on 2026-07-13: <https://x.com/formulasearch/status/2076288803786887245>

## Governed round-trip architecture

```text
canonical state graph / ledger
  -> deterministic projector
  -> one or more Canvas views
  -> human or agent edits
  -> Canvas diff
  -> typed ChangeIntent[]
  -> schema + authority + conflict + evidence gates
  -> apply to canonical state
  -> regenerate Canvas
  -> readback / revision receipt
```

Never implement this unsafe shortcut:

```text
Canvas edit -> immediate destructive mutation or side effect
```

## Minimum state contract

Every current-state node should have stable machine semantics outside presentation-only color and position:

```yaml
id: stable_id
kind: goal | decision | requirement | task | risk | question | evidence | artifact | agent
status: proposed | confirmed | in_progress | blocked | superseded | done | archived
owner: human | agent_id | shared
revision: integer
summary: short current-state statement
source_refs: []
evidence_refs: []
depends_on: []
supersedes: []
authority: read_only | human_owned | agent_writable | joint_review
```

Every material edge should be typed:

```yaml
kind: depends_on | blocks | produces | supports | contradicts | supersedes | responsible_for | input_to
from: node_id
to: node_id
label: optional human-readable label
```

Spatial proximity may aid humans but must not be treated as a machine relationship. Color may project status but cannot be the only status representation.

## Human/agent edit policy

| Edit | Default interpretation | Required gate |
|---|---|---|
| Move/resize node | Layout-only preference | schema readback |
| Relabel/retype node | semantic change intent | revision + validation |
| Add typed edge | relationship change intent | endpoint/type validation |
| Change status | lifecycle transition request | state-machine + evidence gate |
| Delete node | soft tombstone/request | ownership + dependency + confirmation when destructive |
| Edit human-owned region | human authority | preserve exact edit and revision |
| Edit agent-owned projection | local reversible write | regenerate + diff readback |
| Trigger tool/HTTP/task execution | separate side effect | exact authority, target, payload, rollback and receipt |

An Agent must not “clean up” human-owned nodes, delete facts, or rewrite confirmed decisions merely to improve layout.

## Layering and scale

Do not create one infinite project map.

Recommended views:

1. Project overview: goals, phases, owners, major risks and current closure state.
2. Domain/feature canvas: requirements, decisions, flows and dependencies.
3. Execution canvas: task/agent status and evidence links.
4. Archive/history view: superseded decisions and completed branches.

Use semantic zoom or level-specific summaries. Keep detailed prose, reports, source material and acceptance evidence in Markdown/files; Canvas nodes should link to them.

## Hermes operating rule

Until Hermes has a bidirectional Canvas UI, emulate the safe semantic core:

1. For complex work, maintain an explicit project SSOT/progress ledger that states the current objective, chosen path, confirmed/superseded decisions, open questions, blockers, tasks and evidence.
2. Treat chat as event input, not current truth.
3. When a user supplies or edits `.canvas`, parse it as a proposed state delta unless the project contract grants it canonical authority.
4. Convert edits into typed change intents and validate them before changing files, tasks, lifecycle state or external systems.
5. Project the accepted state back into a human-readable graph/Canvas and read it back before claiming alignment.
6. Keep source/evidence references attached to nodes so a visually plausible graph cannot overwrite grounded facts.

## Applicability

Use when:

- the user says the conversation is mixing old and new decisions;
- a project has multiple branches, agents, artifacts or dependencies;
- direct manipulation would communicate structure better than another correction prompt;
- a project needs a current-state view distinct from a chronological log;
- integrating JSON Canvas, Obsidian Canvas or another graph/whiteboard with an agent workflow.

Do not use when:

- the task is a short question, one-file edit or linear command sequence;
- creating a graph would cost more than reconstructing the state;
- the user only wants a static diagram;
- the source format has no stable IDs or revision/conflict rules and is being mistaken for a transactional state store.

## Falsifiers

Narrow or reject this pattern if:

- users spend more time maintaining the graph than executing work;
- the canonical state and Canvas repeatedly diverge;
- layout changes are misread as semantic changes;
- branch inheritance cannot be made explicit;
- the projection loses source/evidence provenance;
- a simpler ledger or task board supplies the same current-state clarity with lower cost.

## Owned local projector and change-classifier slice

A deterministic, side-effect-free projection and proposal-only classification slice is included with this skill:

- Input template: `templates/shared-canvas-state.sample.json`
- Projector: `scripts/project_shared_canvas_state.py`
- Projector tests: `scripts/test_project_shared_canvas_state.py`
- Canvas change classifier: `scripts/classify_shared_canvas_changes.py`
- Classifier tests: `scripts/test_classify_shared_canvas_changes.py`

Run:

```bash
python3 scripts/project_shared_canvas_state.py \
  templates/shared-canvas-state.sample.json \
  /tmp/project.canvas \
  --receipt /tmp/project.canvas.receipt.json

# After editing a copy of /tmp/project.canvas:
python3 scripts/classify_shared_canvas_changes.py \
  /tmp/project.canvas \
  /tmp/project.edited.canvas \
  /tmp/project.change-intents.json \
  --source-revision 1

python3 -m unittest discover -s scripts -p 'test_*.py' -v
```

The input contract is `shared_canvas_state.v1`. The projector validates stable node/edge IDs, supported node/edge kinds, lifecycle status, authority, revisions and edge endpoints. It emits JSON Canvas-compatible `nodes` and `edges` plus an optional SHA-256 receipt.

The classifier validates baseline and edited Canvas structure, then emits `shared_canvas_change_intents.v1`. Layout/color changes remain advisory; text/content changes become `semantic_edit_request`; additions/removals become reviewable node or relationship requests; node removal is explicitly a non-applied `node_delete_request`. Every packet records `apply_performed=false`, `external_side_effects=false` and `runtime_effect=proposal_only`.

Boundary: this slice is local and cannot apply any change. It does not mutate canonical state, invoke tools, call networks or execute nodes. A bidirectional bridge still requires revision comparison against live canonical state, authority and evidence gates, an idempotent apply adapter, negative side-effect tests, regeneration and readback acceptance.

## Verification checklist

- [ ] Event history and current state are stored separately.
- [ ] Canonical ownership is explicit; Canvas is not accidental SSOT.
- [ ] Nodes have stable IDs, typed status, revision, ownership and evidence refs.
- [ ] Material edges are typed; proximity/color are not sole semantics.
- [ ] Canvas edits become typed change intents.
- [ ] Semantic edits pass schema, authority and conflict gates.
- [ ] Deletes are soft/gated and cannot silently remove confirmed facts.
- [ ] Side effects remain separately authorized.
- [ ] Large workspaces are split into layered views.
- [ ] Accepted changes are regenerated and read back.
