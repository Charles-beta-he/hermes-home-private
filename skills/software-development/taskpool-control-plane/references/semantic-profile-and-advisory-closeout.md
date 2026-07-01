# Semantic profile policy and advisory-only closeout pitfalls

Use when taskpool `selfcheck`/`dispatch_tick` is otherwise healthy but semantic control-plane warnings, advisory-only multimodel state, or handoff backlog prevent clean progress.

## 1. Semantic control-plane WARN on project profile fields

Symptom:

- `brain_task_orchestrator.py selfcheck --json` returns `status=PASS`, but `semantic_control_plane.status=WARN`.
- Warnings look like:
  - `profile_control_plane_missing:lark_task_execution_policy`
  - `profile_control_plane_missing:lark_evidence_policy.closeout_required_labels`
  - `profile_control_plane_missing:backend_contract_policy`
  - `profile_control_plane_missing:regression_coverage_policy`

Safe resolution pattern:

1. Treat it as a profile-governance gap, not a runtime failure.
2. Patch the relevant project profile, not global memory and not the orchestrator, unless the schema itself is wrong.
3. Add only project-scoped policy fields:
   - `lark_task_execution_policy`: primary goal, default task classification, supported task classes, closeout rule.
   - `lark_evidence_policy.closeout_required_labels`: baseline / implementation delta / verification / rollback or degradation guard / authority boundary.
   - `backend_contract_policy`: canonical authority, schema rules, compatibility, side-effect boundaries.
   - `regression_coverage_policy`: required checks and blocked closeout conditions.
4. Append a short progress-ledger entry if the project has a ledger.
5. Verify with selfcheck readback: semantic status should become `OK` and warnings should be empty.

Anti-conditions:

- Do not add broad global rules to memory for a single project profile.
- Do not force a missing semantic profile warning into a fail-closed taskpool failure unless there is fresh policy ratification.
- Do not claim product/runtime completion from adding policy fields; it is governance/profile cleanup only.

## 2. Advisory-only multimodel rounds do not authorize `done`

Symptom:

- A task reaches `review`, but `transition --to done` fails with:
  `advisory_only_multimodel_requires_implementation_evidence: PASS_ADVISORY_ONLY cannot authorize done without commit/test/build/browser/real-api evidence`
- Common after event hooks run a weak advisory multimodel sidecar for `architecture_target` or closeout metadata.

Safe resolution pattern:

1. Separate advisory state from lifecycle proof. `PASS_ADVISORY_ONLY` only consumes scheduler churn; it is not completion authority.
2. For evidence-only/governance children, provide structured evidence that satisfies the work closeout gate without pretending there was app/runtime work:
   - `command: ... verification test PASS ...`
   - `artifact:/absolute/path ... project evidence verification ...`
   - explicit `proof:ui_surface_not_applicable...` or `proof:api_readback_not_applicable...` only when the task is documentation/governance-only and no UI/API surface changed.
3. If an event hook already started an advisory sidecar and the task is safely in review, the final `review -> done` transition may be run with `HERMES_TASKPOOL_EVENT_HOOK_DISABLED=1` to avoid duplicate sidecar churn, but only after lifecycle evidence is complete.
4. Verify by reading the task back with `list --include-done --json` and running dispatch/selfcheck/proof/boundary readback.

Anti-conditions:

- Do not use advisory-only evidence to close implementation tasks that actually changed UI/API/code.
- Do not disable event hooks before the task has concrete evidence and a valid lifecycle state.
- Do not use `--force` merely to bypass missing proof; satisfy the gate or stop at an intervention packet.

## 3. Manual claims can create actor-mismatch envelopes

Symptom:

- Manual `parallel-claim-and-handoff --write --actor X` creates claimed tasks, but `agent_team_controller.py execute-cycle` skips with `claimed_by_mismatch` because it expects `agent-team-controller` claims.

Safe resolution pattern:

1. Prefer the normal dynamic runner / agent-team controller claim path for execution-bound work.
2. If a manual claim was created only to free/inspect capacity, release it back to `retry` or `pending` with an explicit reason before invoking agent-team execution.
3. Do not mix actors in the same execute-cycle unless the consumer explicitly supports that actor.

## 4. Handoff backlog may grow during manual progress

Symptom:

- `handoff_backlog_count` rises from 100 to 101 after manual claim/handoff work.

Safe resolution pattern:

1. Run `handoff-gc.py --archive --keep-newest 50 ...` first as dry-run.
2. Then run the same command with `--apply` if the plan only moves old files into `archived/<timestamp>/`.
3. Re-run dispatch tick; backlog should return to 100 and warning should be empty.

Anti-condition: never delete handoffs directly; archive with manifest only.
