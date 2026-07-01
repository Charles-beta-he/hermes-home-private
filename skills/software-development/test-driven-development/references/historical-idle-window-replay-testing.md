# Historical idle-window replay testing

Applicability: use when a stateful automation/control-plane loop had a long historical idle period: cron looked healthy, but the same target repeated with no state advancement. Anti-conditions: do not replay against production state; do not encode one specific skill/job/date as a permanent rule.

## Pattern

1. Collect real historical records from the run outputs and ledgers, not a hand-written toy fixture.
2. Normalize each record into: timestamp/source file, target, state advancement flag, score/result, reason, proof hash if present.
3. Build a temp state store with the repeated target and at least one plausible alternative target so selector rotation is observable.
4. Import the real selector/state-transition functions. Patch only filesystem paths and logging sinks; do not duplicate selector logic in the test.
5. Replay a minimal prefix of historical no-change records:
   - after first no-change, selector should rotate away or otherwise record an attempt;
   - after the configured threshold, cooldown/blocked state should be written;
   - final selector should not be the repeated target.
6. Save a JSON artifact with input window counts, first/last records, replay steps, final state, and `passed`.
7. Run the focused suite after replay and record both the replay artifact and test command output in the task proof log.

## Pitfalls

- A cron `OK` is not proof of effective progress. Test state advancement explicitly.
- Avoid duplicated selector/matcher logic in replay tests; duplicated logic silently drifts from production.
- Keep historical fixture use bounded: verify the bug class and fix path, not every old run one-by-one.
