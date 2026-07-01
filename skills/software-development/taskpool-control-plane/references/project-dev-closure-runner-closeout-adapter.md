# Project dev-closure runner to taskpool closeout adapter

Use when a user asks to operationalize workflow/course/agent-pattern learning into an active project until it can take over the development closure loop.

## Purpose

Turn a project-local development workflow into a safe, evidence-gated control loop:

```text
task metadata -> adaptive lane -> local proof commands -> closure packet -> taskpool closeout dry-run -> receipt/intervention packet
```

This pattern is for **project-scoped runner adoption**, not a global Hermes behavior change.

## Applicability

Use when:

- there is a project profile or SSOT root;
- old taskpool tasks exist and can be used as test slices;
- the user wants “接管开发闭环” / “全盘推进”;
- local reversible proof commands can be run;
- taskpool lifecycle/certification gates must remain canonical.

## Anti-conditions

Do not use this pattern to:

- force `done` from `blocked` or `pending`;
- bypass multimodel/certification/project-evidence gates;
- deploy, publish, sign native apps, or execute external side effects;
- write project/task progress into global memory;
- promote one project’s runner as a cross-project default without an experience-ratchet proposal.

## Implementation shape

Create project-scoped artifacts under the project SSOT, for example:

```text
09-dev-closure/
  project-ai-profile.md
  router.md
  review-checklist.md
  evidence-ledger.md
  lessons.md
  RUNNER.md
  packets/
  closeout-adapter/
  scripts/
    dev_closure_runner.py
    taskpool_closeout_adapter.py
    verify_dev_closure.py
```

### `dev_closure_runner.py`

Responsibilities:

1. Locate the task note by task id.
2. Parse enough task metadata/frontmatter to classify risk and surface.
3. Read project profile/SSOT boundary.
4. Classify lane:
   - direct/docs;
   - normal local dev closure;
   - strong reviewer/certification lane;
   - dynamic workflow lane.
5. Run only configured local reversible proof commands.
6. Generate a closure packet with command outputs and safety boundary.
7. Never mutate taskpool lifecycle.

Required output fields:

- schema/version;
- task id and task file;
- lane and reason;
- command results;
- `local_closure_state`;
- `lifecycle_mutation=false`;
- `external_side_effects=false`;
- `canonical_done_boundary`.

### `taskpool_closeout_adapter.py`

Responsibilities:

1. Optionally refresh the packet by invoking `dev_closure_runner.py`.
2. Compute packet hash.
3. Call canonical taskpool closeout in dry-run mode, e.g. `brain_task_orchestrator.py done <task> --authority dry-run`.
4. If dry-run passes, emit a proposal/receipt — still do not mutate unless separately authorized.
5. If dry-run fails, write an intervention packet that preserves blockers and next safe step.

Required behavior:

- dry-run only by default;
- no force-done;
- no deploy/external side effects;
- explicit `INTERVENTION_REQUIRED` when canonical lifecycle rejects closure.

## Verification checklist

Run and record:

```bash
python3 -m py_compile scripts/dev_closure_runner.py scripts/taskpool_closeout_adapter.py scripts/verify_dev_closure.py
python3 scripts/verify_dev_closure.py
python3 scripts/dev_closure_runner.py <old-task-id> --execute --write-packet --json
python3 scripts/taskpool_closeout_adapter.py <old-task-id> --execute-runner --write --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py proof-check --json
```

For UI tasks, also perform browser or screenshot proof before claiming local closure.

## Expected outcomes

A healthy first landing may still end with taskpool `done` dry-run rejected. That is not a failure if the blocker is real, for example:

- `blocked -> done` is illegal;
- task must enter `review` or `certified` first;
- multimodel/certification gate is missing;
- project-evidence review requires browser/API/commit proof.

The correct output is an intervention packet, not a forced lifecycle transition.

## Writeback

Write only scoped artifacts:

- project profile current component status;
- project progress ledger;
- task proof log with packet path/hash and dry-run result;
- runner README;
- closeout adapter receipt/intervention packet.

Do not write task progress to global memory. Durable reusable learning belongs in this skill reference.
