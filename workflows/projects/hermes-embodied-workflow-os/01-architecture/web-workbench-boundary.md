# P3 Web Workbench Architecture Boundary

Status: spec-only boundary document.
Updated: 2026-07-02T19:34:00+08:00

## Boundary statement

The Web Workbench is an adapter/projection surface. It observes, simulates, and reviews. It does not own truth and it does not execute physical/external actions.

## Allowed dependencies

```text
Workbench UI / local dev server
  -> projection DTOs
  -> hewos_core contracts / registry / ledger replay
```

Allowed imports in future implementation:
- projection DTO definitions
- fixture generators
- read-only capability registry snapshots
- simulation-local EvidenceLedger
- pure validators

## Forbidden dependencies

Workbench code must not import or call:
- hardware SDKs
- robot control libraries
- gateway send clients
- taskpool lifecycle writers
- deploy/publish/push commands
- credential entry/storage modules
- Hermes runtime authority expansion modules

## Projection DTOs

### CapabilityProjection

```json
{
  "capability_id": "cap.web.text_observation",
  "actor_id": "actor.web.mock",
  "adapter_id": "adapter.web.mock",
  "capability_type": "observation",
  "risk_class": "none",
  "dry_run_default": true,
  "status": "available|unavailable|simulated"
}
```

### TaskGraphProjection

```json
{
  "task_graph_id": "tg.example",
  "title": "Install shelf bracket",
  "nodes": [{"id": "step.1", "label": "identify parts", "state": "pending|complete|blocked"}],
  "edges": [{"from": "step.1", "to": "step.2"}],
  "world_state_ref": "replay:latest"
}
```

### ActionIntentProjection

```json
{
  "intent_id": "ai.example",
  "capability_id": "cap.robot.dry_run",
  "risk_level": "physical_action",
  "preview": "dry-run only",
  "required_gates": ["SafetyGate", "ExternalControlGate", "OnsiteHumanGate"],
  "evidence_refs": ["ev.1"],
  "status": "blocked|dry_run_reviewable|approved_simulation_only"
}
```

### EvidenceEntryProjection

```json
{
  "entry_id": "ev.1",
  "timestamp": "2026-07-02T00:00:00Z",
  "kind": "observation|verification|action_intent|review",
  "subject_id": "obs.1",
  "source": "adapter.web.mock",
  "claims": [{"claim": "part visible"}],
  "evidence_refs": ["sha256:..."],
  "redaction_status": "checked"
}
```

## Screen-level gates

| Screen | Read | Simulation write | Real write | External side effect |
|---|---:|---:|---:|---:|
| Dashboard | yes | no | no | no |
| TaskGraph Inspector | yes | optional fixture | no | no |
| ActionIntent Review | yes | dry-run review entry only | no | no |
| EvidenceLedger Browser | yes | no | no | no |
| Adapter Simulation | yes | simulation ledger only | no | no |

## Implementation guardrails

- Put Workbench code under a separate adapter/workbench directory; never inside `hewos_core`.
- Keep `hewos_core` importable and testable without Web dependencies.
- Workbench state is cache/projection only; on refresh it can be rebuilt from ledger/registry fixtures.
- Any future real approval must create an ActionIntentReview ledger entry, not call adapter execution.
- Any future execution path must be separate: ActionIntent -> SafetyGate -> ExternalControlGate -> Adapter -> Verification -> EvidenceLedger.

## Verification commands for future implementation

```bash
python3 -m unittest discover -s implementation/tests -v
# plus future workbench tests once implementation exists
```

P3 spec-only slice has no browser/UI acceptance claim.