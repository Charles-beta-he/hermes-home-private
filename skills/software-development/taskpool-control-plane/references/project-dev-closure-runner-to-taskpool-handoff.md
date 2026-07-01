# Project dev-closure runner to taskpool handoff

Use this when turning an Agent/workflow methodology into a working project-level development closure loop, especially by testing against old taskpool tasks before allowing it to drive new work.

## Landing zone

Class-level procedure for safely upgrading from a one-off shadow proof refresh to a reusable project runner that can read task metadata, classify a lane, run local evidence commands, generate closure packets, and hand off to taskpool certification/lifecycle gates.

This is not a record that a specific project is complete. Project-specific paths, task IDs, screenshots, or command outputs belong in that project's profile/evidence ledger and task notes.

## Applicability

Use when:

- the user asks to “全盘推进”, “接管开发闭环”, “用旧任务测试”, or equivalent;
- there is an existing taskpool task with acceptance/evidence metadata;
- the safe target is local development proof and closure-packet generation, not immediate `done` mutation;
- a project already has or needs a project profile/SSOT, red lines, evidence ledger, and lessons.

Anti-conditions:

- Do not force `done` when the task has `requires_multimodel`, `certification_status: not_certified`, `completion_gate`, or similar lifecycle gates.
- Do not deploy, publish, send messages, sign native apps, mutate production state, or perform external side effects from the runner without a fresh authority gate.
- Do not write secrets, PII, raw coordinates/screenshots, or customer/private data into global memory or generic skills.
- Do not treat a project-local runner as a global Hermes policy until it has passed multiple task classes and a separate promotion gate.

## Procedure

1. **Model the boundary first**
   - Define the closure loop as: `task metadata -> adaptive lane -> local proof commands -> closure packet -> certification/lifecycle handoff`.
   - Make the runner default to `lifecycle_mutation=false` and `external_side_effects=false`.
   - State the canonical done boundary in every output.

2. **Create project-scoped closure artifacts**
   - `project-ai-profile.md`: objective, red lines, authority model, completion definition.
   - `router.md`: lane classification rules and pilot task classification.
   - `review-checklist.md`: blocker/warning/suggestion checklist.
   - `evidence-ledger.md`: commands, browser/API readback, review result, status.
   - `lessons.md`: reusable project lessons only.
   - `packets/<task-id>.closure-packet.md`: generated handoff packets.
   - `scripts/dev_closure_runner.py`: deterministic runner for supported task classes.

3. **Start with old tasks**
   - Pick an old task with real acceptance metadata and evidence requirements.
   - Run the first pass in shadow mode.
   - If UI is involved, require both deterministic tests and browser/screenshot proof.
   - If backend/API is involved, require real readback.

4. **Upgrade from one-off to project runner**
   - Support a small allowlist of task classes/surfaces first.
   - Read task frontmatter and project profile.
   - Classify each task by lane and risk.
   - Upgrade classification to a strong gate when blocked/review/certification/multimodel flags are present, even for docs-only tasks.
   - Run only configured local proof commands.
   - Generate a closure packet; do not mutate taskpool lifecycle.

5. **Write back to the correct boundary**
   - Project profile: runner status, runner path, evidence path, boundary.
   - Project progress ledger: commands and observed results.
   - Task proof log: packet path and local proof summary.
   - Skill/reference: only class-level procedure and pitfalls.
   - Memory: only stable user/project preferences, not progress.

6. **Verify before claiming upgrade**
   - `py_compile` the runner and verifier.
   - Run the artifact verifier.
   - Run at least one executable task class with `--execute --write-packet`.
   - Run at least one metadata/docs task with `--write-packet` to prove non-execution lanes.
   - Run taskpool `selfcheck --json` and `proof-check --json` when available.
   - Read back a generated closure packet.

## Runner output contract

A project runner should emit JSON containing at least:

```json
{
  "schema": "<project>_dev_closure_runner_vN",
  "classification": {
    "task_id": "...",
    "lane": "Lane C — Strong gate / reviewer lane",
    "surface": "...",
    "requires_multimodel": true,
    "blocked_or_certification_boundary": true,
    "allowed_actions": ["metadata_read", "local_tests", "closure_packet", "ledger_readback"],
    "forbidden_actions": ["taskpool_done_mutation", "deploy", "external_side_effect", "secret_or_pii_write"]
  },
  "mode": "execute",
  "lifecycle_mutation": false,
  "external_side_effects": false,
  "ok": true,
  "local_closure_state": "verified_packet_ready",
  "canonical_done_boundary": "requires taskpool lifecycle/certification gate; not mutated by this runner",
  "closure_packet": "..."
}
```

## Pitfalls

- **Docs-task downgrade trap**: A docs/SSOT task that is `blocked`, `review`, `requires_multimodel`, or `not_certified` is not automatically low risk. Upgrade to strong gate and generate a packet rather than calling it closed.
- **Local proof as done trap**: Passing tests/browser proof means `verified_packet_ready`, not taskpool `done`, when lifecycle/certification gates are still active.
- **One-off runner trap**: A hardcoded single task runner proves only a pilot. Upgrade to task metadata parsing, supported surfaces, packets, and explicit forbidden actions before claiming development-loop takeover.
- **Pretty summary safety trap**: If a final summarizer/readback command is blocked by the runtime safety layer, do not retry the same command shape. Preserve already-passed evidence and continue only after explicit authorization with a distinct safe action.
- **Wrong landing zone trap**: Put project paths and task IDs in the project profile/ledger/task note. Put only the reusable runner/handoff procedure in the skill reference.

## Closeout boundary

The next promotion after a project runner is a `taskpool-closeout-adapter --dry-run` style layer:

```text
runner packet -> proof-chain validation -> certification/closeout dry-run -> proposed transition or blocked packet
```

Do not implement automatic `done` as the next step. The adapter should propose or dry-run lifecycle changes and stop at certification/human gates.
