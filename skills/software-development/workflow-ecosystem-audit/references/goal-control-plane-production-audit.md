# Goal-Control-Plane Production Audit Pattern

Use this reference when auditing an agent/workflow system that already has pieces like `/goal`, hooks, task pools, missions, cron, dynamic workflows, observers, or proof gates. The reusable lesson is to separate *control-plane contracts* from *executors* and to mark prototype/test-covered layers honestly.

## Landing-zone classifier

- Reusable procedure / pitfall / verification checklist -> update a skill.
- Concrete follow-up engineering work -> taskpool candidate/proposal, not a skill.
- Project-specific paths, commits, docs, or branch names -> scoped reference or project profile, not global memory.
- Session progress -> do not persist as memory.

## Audit sequence

1. Evidence-map current surfaces:
   - goal/session loop and persistence layer;
   - slash command routing;
   - hook bus behavior and failure policy;
   - taskpool/mission/cron promotion or enqueue path;
   - dynamic workflow/checkpoint/proof docs and actual tests.
2. Classify each surface as:
   - production-integrated;
   - test-covered but not integrated;
   - diagnostic/prototype;
   - advisory-only;
   - missing.
3. Land the smallest safe control-plane primitive before executor work:
   - structured spec (for example `goal_spec_v1`);
   - advisory route decision (for example `goal_route_decision_v1`);
   - dry-run-only side effect policy;
   - status output that exposes the route/evidence boundary.
4. Defer executor coupling to gated slices:
   - promotion dry-run candidate;
   - evidence-aware judge/proof bundle;
   - hook manifest fail policy;
   - DAG compiler dry-run;
   - checkpoint sidecar.
5. Verify with targeted tests plus a compatibility test for the existing user-facing route.

## Production-grade warning signs

- A doc says a migration is complete, but the main runtime path never calls the migrated component.
- A hook system catches all handler errors and is being treated as a safety gate.
- A judge reads the last assistant response rather than a proof bundle.
- A checkpoint only stores goal text/status, not plan/proof/remaining work.
- A dynamic workflow can be tested in isolation but cannot be reached from `/goal`, taskpool, or mission control.

## Guardrails

- Never make `/goal set` enqueue taskpool work, create cron jobs, mutate mission state, or execute DAG nodes.
- Promotion must start as `--dry-run` and prove no lifecycle state mutation.
- Hooks need explicit class/fail policy before they are used as gates.
- A proof/evidence bundle must be required before claiming verified completion.
- Checkpoint state should store auditable references, not an opaque context dump.

## Verification checklist

- [ ] Current runtime surfaces were read directly, not inferred from design docs.
- [ ] Test-covered-but-unintegrated layers are labeled as such.
- [ ] The landed slice is a control-plane contract or dry-run, not a hidden executor.
- [ ] Existing commands still pass compatibility tests.
- [ ] Follow-up work is routed to taskpool/proposals rather than encoded as fake skills.
