# Taskpool Evidence Writeback and Multimodel Race Pattern

Scope: Hermes taskpool/control-plane work after a local implementation slice already has deterministic evidence (scripts, reports, tests, receipts) and the agent needs to write proof back to a task record or advance lifecycle. Applicability: use for governed taskpool cards with `claimed/running/review/done/retry/pending` transitions, especially when multimodel or autorun hooks may also touch the card. Anti-conditions: this does not authorize force-done, external dispatch, credential entry, publish/deploy, destructive actions, or treating advisory multimodel output as certification.

## Pattern

1. Read current lifecycle state before every transition.
   - Do not assume the task is still in the state you last wrote.
   - Event hooks, autorun, or multimodel closeout may claim, advance, close, or requeue it between commands.

2. Use legal lifecycle order.
   - `pending -> claimed -> running -> review` for normal evidence writeback.
   - If already `running` and `claimed_by` is another actor, either use the owning actor for the matching transition or wait/read back; do not repeat a no-op `running -> running` command.
   - If already `done`, stop lifecycle writes and report the fresh readback.

3. Evidence strings must be machine-shaped.
   - Prefer prefixes: `command:`, `file:`, `artifact:`, `url:`, `proof:`.
   - Bare absolute paths should be `artifact:/abs/path` or `file:/abs/path` depending on meaning.
   - If a CLI rejects evidence shape, fix the evidence string; do not keep retrying the same transition.

4. Split implementation proof from lifecycle/certification proof.
   - Deterministic evidence such as `py_compile`, selftests, report files, or commit hashes proves the implementation slice.
   - `PASS_ADVISORY_ONLY`, `not_certified`, or `degraded_not_certified` is not lifecycle completion authority for cards requiring certification.
   - If closeout requeues to `pending` after `review`, preserve the implementation evidence and report the certification boundary instead of forcing `done`.

5. Avoid retry loops.
   - After two failed transition attempts, re-read the task note and inspect `status`, `claimed_by`, `run_id`, `multimodel_*`, and the latest proof log lines.
   - Choose the next transition from the fresh state, not from the stale command chain.

## Minimal writeback sequence

```text
read task frontmatter/status
if status == pending:
  transition -> claimed with command:/artifact: evidence
  read task or inspect transition output
if status == claimed by this actor:
  transition -> running
if status == running by this actor or known hook actor:
  transition -> review with deterministic implementation evidence
read task again
if status == done:
  report done with fresh evidence
elif status in {pending,retry} and multimodel/advisory closeout is present:
  report implementation proof plus certification boundary
```

## Common pitfalls

1. Chaining multiple lifecycle commands after the first command triggers hooks; later commands may run against a different state.
2. Treating `PASS_ADVISORY_ONLY` as completion authority.
3. Using free-form evidence text that fails the orchestrator's evidence-shape validator.
4. Forcing a transition to overcome a stale claim without first reading `claimed_by` and the latest proof log.
5. Reporting “blocked” from a transition timeout when the task note later shows the hook actually advanced or requeued the card.

## Verification checklist

- [ ] Latest task frontmatter was read after any failed or timed-out transition.
- [ ] Evidence entries use `command:`, `artifact:`, `file:`, `url:`, or `proof:` prefixes.
- [ ] Implementation proof and certification/lifecycle proof are reported separately.
- [ ] No `done` claim is made from advisory-only multimodel output.
- [ ] The final status is based on fresh task-note readback, not only the transition command that was attempted.
