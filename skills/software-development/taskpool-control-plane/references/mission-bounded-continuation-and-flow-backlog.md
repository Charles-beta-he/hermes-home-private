# Mission bounded continuation and flow-signal backlog recovery

Use this reference when a long-running Hermes Mission is active but appears stalled by tick budget, stale `mission_flow_signals`, or a large pending flow-signal backlog.

## Safe continuation sequence

1. Read-only baseline first:
   - `hermes mission doctor <mission_id>`
   - `hermes mission report <mission_id> --limit 8`
   - repo `git status --short --branch`
   - DB counts for `mission_flow_signals` by status when backlog size matters.
2. If there are uncommitted code diffs from the previous tick, close them before granting more execution:
   - inspect scope;
   - run focused deterministic tests/static checks;
   - independent review for non-trivial code;
   - commit scoped changes;
   - verify repo is clean.
3. If the mission is `blocked_on_human`, answer only the explicit decision packet. Prefer the recommended safe option when it keeps mutation governed, local, and reversible.
4. Dispatch through the governed runner:
   - `hermes mission dispatch-events <mission_id> --run-due --json`
   - read back doctor/report/git/flow-signal counts.

## Bounded tick authority

Default local continuation authority should be bounded and recorded:

- Auto-extension is only for local, reversible mission continuation.
- Do not infer permission for push, deploy, secrets, deletion, payments, external delivery, or production writes from a tick extension.
- A practical default ceiling for this user's long-running self-architecture Mission is total mission `max_ticks <= 60` since the last human authorization boundary. Earlier 30-tick ceilings should be treated as a conservative first stop, not the maximum interval, after the user explicitly corrected the default to 60.
- At/above the current authorized ceiling, generate a Human Intervention Packet instead of silently extending again.
- Each authorization ledger record should include old/new max ticks, reason, scope, model/reviewer evidence if used, and the ceiling being applied.
- If the installed Mission CLI does not expose a budget command, update `missions.budget_json.max_ticks` only inside the local missions DB, resume/keep the mission `active`, then record a `stage_report` with the authorization boundary. Do not invent unsupported event types such as `budget_authorized` unless `VALID_EVENT_TYPES` actually includes them.

## Flow-signal backlog rule

A large stale backlog is not license to bulk mutate live signals ad hoc. Prefer a governed recovery path:

1. Implement or use a recovery/compaction command with tests.
2. Keep it non-recursive: it must not launch nested agents while marking signals consumed.
3. Preserve evidence accounting: record before/after counts and a stage report.
4. Only mutate live pending signals when either the mission policy explicitly allows the recovery command or the user chose an option authorizing one-time local drain.

### Proven command sequence

Use dry-run before mutation, then apply a bounded batch with an audit reason:

```bash
hermes mission recover-signals <mission_id> \
  --older-than-seconds 900 \
  --max-signals 50 \
  --reason "bounded local stale flow-signal recovery; no agent recursion, no external side effects" \
  --json

hermes mission recover-signals <mission_id> \
  --older-than-seconds 900 \
  --max-signals 50 \
  --reason "bounded local stale flow-signal recovery; no agent recursion, no external side effects" \
  --apply \
  --json
```

For very large already-coalesced historical backlogs, a larger bounded batch such as `--max-signals 200` is acceptable only after dry-run shows the selected signal types and the user/policy has authorized local ledger recovery. Repeat with smaller follow-up batches until `watchdog` is silent.

## Decision packets during recovery

Dispatch/recovery may generate a new decision after the operator already said “continue.” If the recommended option stays inside the established local/reversible boundary, answer that decision instead of leaving the mission blocked. Examples:

- prefer staged/dry-run harness extension over active skill-store mutation unless the user explicitly approved the skill write;
- prefer bounded local ledger recovery over ad hoc DB updates or recursive agent runs;
- preserve active skill/memory/cron/external writes as separate human gates.

### At the tick ceiling, stop instead of inferring continuation

When the mission reaches the agreed ceiling (for example `tick budget: 30/30`) and opens a new decision, do not treat earlier “continue” messages as permission to exceed the ceiling. Produce/answer the Human Intervention Packet only after an explicit new choice. If using `clarify`, a timeout/default-response is not authorization to cross the cap or expand authority.

### Local-only ticks must suppress unintended recursive workers

If a bounded mission tick is scoped as local-only but taskpool lifecycle commands unexpectedly spawn multimodel/agent workers, classify it as an execution-authority leak:

1. Stop the unintended live worker processes and record that they were stopped.
2. Read back mission status, open decision, tick budget, repo status, and any task note status drift.
3. Do not continue dispatching while the mission is at its tick ceiling.
4. Prefer a narrow fix such as an explicit no-multimodel-spawn environment gate in the lifecycle path, with focused tests, but only after human authorization because it changes taskpool execution behavior.
5. Avoid manual frontmatter correction as the long-term path; use it only as a temporary evidence-preserving recovery and then restore normal commands once the no-spawn gate exists.

## Event-hook multimodel spawn suppression

When a bounded Mission tick discovers that taskpool lifecycle transitions are unintentionally spawning multimodel intervention workers, treat that as an authority/recursion boundary problem, not just a noisy process issue.

Durable pattern:

1. Stop live unintended multimodel worker processes only after identifying the exact task/state they came from.
2. Add or use an explicit opt-in suppression gate for local bounded maintenance runs:
   - `HERMES_TASKPOOL_EVENT_HOOK_NO_MULTIMODEL_SPAWN=1`
   - This must override both `HERMES_TASKPOOL_EVENT_HOOK_MULTIMODEL=force` and normal auto routes.
3. Keep default behavior unchanged when the suppression env var is unset.
4. Add a focused test covering both forced and auto event-hook routes returning `enabled=false` with a clear reason such as `multimodel_spawn_disabled_by_env`.
5. Re-run the mission dispatch with the env gate enabled, then read back: no open decisions, watchdog silent, and no matching unintended multimodel processes.

Do not wire this suppression into cron or global runtime config without a separate authorization boundary; runtime env/config mutation is broader than a local one-shot gated dispatch.

## Mission envelope schema gate lessons

When adding a gate for mission tick envelopes, make it genuinely fail-closed:

- Require an explicit `open_decisions: []`; missing human-decision state is not equivalent to no decisions.
- Require budget state to be explicit: `budget_exhausted` must be exactly `false`, and `remaining_ticks` must be a positive non-bool integer. `remaining_ticks_known=true` without a count is not enough.
- Validate mission IDs against the full runtime format (e.g. `msn_YYYYMMDD_HHMMSS_8hex`), not just `startswith("msn_")`.
- Keep `requested_actions` independently allowlisted for local-only actions; reject dangerous/external aliases even if `blocked_actions` omits them.
- Use safe digest/canonicalization so malformed dict-shaped envelopes return a rejected projection rather than crashing validation.
- Tests should cover dangerous requested actions, ambiguous budget, non-string scalars, missing `open_decisions`, non-serializable values, and bare-prefix mission IDs.

## Verification evidence

A healthy closeout should report:

- mission status and open decision count;
- tick budget used/max;
- cron job status and next run;
- pending/consumed/recovered flow-signal counts;
- `hermes mission watchdog <id> --json` with `silent=true` after recovery;
- repo status clean or explicitly scoped remaining diffs;
- latest tests/reviewer evidence for any code change.

## Pitfalls

- Do not report a mission as clean just because the dispatch succeeded; stale flow signals may remain and watchdog may still warn.
- Do not let a new human decision created by dispatch sit unanswered if the user already said “continue” and the recommended option is within the established safe boundary.
- Do not bypass ledger/accounting by direct DB updates to pending signals unless the step is explicitly a governed recovery drain with before/after evidence.
- Do not conflate taskpool/kanban projection drift with mission failure. Report it as the current health bottleneck and let a separate bounded slice repair projection drift.
- When a tick reaches the current `max_ticks`, the mission may auto-pause after `budget_exhausted`; extending budget must also restore/keep status `active` before dispatch can continue.
