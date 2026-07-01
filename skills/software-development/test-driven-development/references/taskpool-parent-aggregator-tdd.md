# TDD pattern: taskpool parent evidence aggregators

Use when adding a read-only diagnostic/resolver for a taskpool parent that has many child tasks.

## Behaviors to specify first

Write RED tests before implementation for:

1. All declared children are `done`, but parent still has certification blockers -> report `keep_blocked_certification_required`, not `done`.
2. Missing declared child -> report `keep_blocked_children_open` with `missing_children`.
3. Children can be discovered by backlinks (`auto_subtask_parent`) when the parent child list is empty or stale.
4. Stale child-status evidence is detected: parent evidence says `proof:child-task:<id>:status:pending` while child frontmatter says `done`.
5. Malformed YAML-like task frontmatter with unquoted colons does not crash the diagnostic; fallback parse enough fields to continue.
6. CLI emits machine-readable JSON with an explicit `safety` string stating it is read-only.
7. Missing parent raises/returns a specific not-found failure.

## Coverage target

For standalone taskpool diagnostic slices, require 100% statement coverage for the new module before claiming the slice complete. Include both direct unit tests and one CLI/subprocess or `main(argv)` path so command-line parsing and JSON output are covered.

## Verification sequence

1. RED: run targeted pytest and observe failure for each behavior.
2. GREEN: implement the smallest read-only module.
3. Coverage: run `python3 -m coverage run --source=<module> -m pytest <test_file> -q`; append a CLI run if needed; then `python3 -m coverage report -m <module>.py`.
4. Live dry-run: run against a real blocked parent and save the JSON report as evidence.
5. Control-plane readback: run taskpool selfcheck/dispatch summary to prove no lifecycle mutation or warnings were introduced.

## Anti-conditions

- Do not mutate parent lifecycle in the first diagnostic slice.
- Do not force close parents from test success alone.
- Do not count file-level test mapping as coverage; use actual statement coverage for the new module.
