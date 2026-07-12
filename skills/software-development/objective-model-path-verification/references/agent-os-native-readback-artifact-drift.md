# Agent OS native readback artifact drift

Use when `hermes agent-os status --json` reports missing or empty native projection artifacts even though a newer Personal AI OS / Agent OS packet appears healthy elsewhere.

## Symptom

- `hermes agent-os status --json` returns `ok=false`.
- Missing native artifacts under the project root, typically:
  - `06-projection/capability_graph_projection.json`
  - `06-projection/doctor_report.json`
  - `07-shadow/router-shadow-report.json`
- `projection.node_count=0`, `doctor.ok=null`, or `shadow.records=null`.
- A subpacket such as `12-personal-ai-os/` may still contain healthy artifacts like `10-capability-projection.json` and `09-doctor-report.json`.

## Interpretation

Treat this as an artifact-contract drift, not as proof that Agent OS itself is absent. The native CLI reads `06-projection/` and `07-shadow/`; a healthy subpacket does not satisfy native readback until it is projected or adapted into those native paths.

## Safe P0 repair ladder

1. Run route/status preflight first:
   - `hermes agent-os status --json`
   - `hermes agent-os route --json '<current intent>'`
2. Identify the native read contract in the Agent OS control-plane code before writing files.
3. Regenerate the source subpacket artifacts if generators exist, e.g. capability projection and packet doctor.
4. Prefer a reversible adapter/projection over changing runtime semantics:
   - transform/copy the source capability projection into `06-projection/capability_graph_projection.json`;
   - preserve/readable compatibility fields needed by the native router such as `kind`, `responsibility`, `source_ref`, and `side_effects` when the source schema names them differently;
   - project the source doctor into `06-projection/doctor_report.json` with explicit `ok` and `findings`.
5. Generate a real `07-shadow/router-shadow-report.json` by running the shadow router over bounded sample intents. Do not write an empty shell just to make status green.
6. If quota/provider state is part of the run, write a read-only root/profile diff instead of silently syncing state. Preserve boundaries such as: Fable 5 no-header routes are route-availability evidence only, not exact budget-handoff evidence.
7. Add or refresh the relevant coverage-registry dimension, e.g. `agent-os-projection-health`, so future “100% coverage” claims include native readback health.
8. Update both the project/packet progress ledger and the task/workspace evidence manifest.

## Verification gate

Minimum evidence before claiming repaired:

- `hermes agent-os status --json` -> `ok=true`, `missing=[]`, `projection.node_count > 0`, `doctor.ok=true`, `shadow.records > 0`, `shadow.would_execute_anything=false`.
- `hermes agent-os doctor --json` -> `ok=true`, no error findings.
- `hermes agent-os route --json '<safe audit intent>'` -> suggested nodes present and `would_execute=false`.
- JSON validation for every generated artifact.
- Focused Agent OS tests pass.
- Extra assertions confirm:
  - status/doctor/shadow summaries match their backing files;
  - shadow blocked-count matches blocked records;
  - no external dispatch, publish/deploy/push, destructive action, credential/payment action, unbounded fan-out, or real capability execution occurred;
  - no exact budget claim is made for no-header/unobservable routes.

## Pitfalls

- Do not treat a healthy `12-personal-ai-os/` packet as native CLI health; native Agent OS status may read different paths.
- Do not treat `route --json` returning `ok=true` with `suggested_capability_nodes=[]` as a working router. With an empty graph, it is only a live shell.
- Do not open real runtime routing/tool execution to fix a readback drift. This repair is local artifact projection only.
- Broad test suites may have unrelated failures or timeouts. For P0 artifact drift closure, use focused Agent OS tests plus explicit JSON/readback assertions; report broader-suite failures as separate risk unless they implicate the changed surface.
