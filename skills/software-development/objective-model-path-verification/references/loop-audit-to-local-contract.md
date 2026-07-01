# Loop audit → local dry-run contract landing

Use when a user accepts an architecture/agent-loop audit and says to proceed at project level, but runtime execution, scheduler activation, taskpool writes, mission lifecycle changes, or external side effects would be too broad to enable immediately.

## Pattern

1. Treat the audit conclusion as a project-level architecture change, not just a report.
2. Create or identify one SSOT artifact for the new boundary before code/taskpool/cron changes.
3. Land the first safe slice as a local dry-run contract:
   - schema for the proposed loop/runtime contract;
   - doctor/validator script that emits deterministic receipts;
   - TDD tests that prove rejection of unsafe contracts;
   - local `docs/private/` SSOT and receipt artifact;
   - scoped commit containing only the slice.
4. Keep the runtime disabled unless separately authorized:
   - no scheduler enabled;
   - no worker spawned;
   - no taskpool or mission lifecycle write-through;
   - no credential reads;
   - no external adapter calls;
   - no publish/destructive side effects.
5. If a Mission exists, append a stage report with evidence, but do not resolve unrelated human gates merely because this slice landed.

## Contract gates to encode

A loop/runtime contract should fail closed unless it declares:

- all five Loop Engineering moves: discovery, handoff, verification, persistence, scheduling;
- all six parts: automations, worktrees, skills, connectors, sub-agents, memory;
- an evaluator independent from the generator;
- evaluator veto authority and evidence refs;
- budget ceilings: turns, runtime, subagents/retries, daily token budget;
- human-gate triggers before scheduler activation, worker spawn, taskpool/mission write-through, external writes, publish, destructive actions;
- rollback/kill-switch path;
- explicit `external_side_effects=false` in the dry-run boundary.

## TDD evidence shape

Write RED tests first for:

- example contract produces deterministic PASS receipt and declares all required moves/parts;
- missing or non-independent evaluator fails;
- evaluator without veto/evidence fails;
- write-authority loop without isolated workspace fails;
- missing/non-positive budget fails;
- missing human gate fails;
- receipt writing only creates a local artifact and does not enable runtime.

Then implement the minimal validator and run focused tests plus py_compile.

## Pitfalls

- Do not confuse schema/doctor landing with runtime enablement.
- Do not mark a mission/task done from deterministic contract proof when an unrelated subjective or authority gate remains open.
- Do not commit pre-existing dirty files; stage only the contract slice.
- Do not put session progress in memory; keep evidence in the SSOT/receipt and reusable procedure here.
