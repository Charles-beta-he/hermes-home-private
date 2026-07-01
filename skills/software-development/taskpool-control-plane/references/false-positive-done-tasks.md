# False-Positive Done Tasks

Extracted from `/Users/charles/.hermes/skills/software-development/taskpool-control-plane/SKILL.md` on 2026-07-01T08:24:04.829872+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## False-positive `done` tasks

If the user asks why a `done` task did not produce the promised behavior, do not defend the lifecycle state. Audit it as a possible false-positive closeout:
1. Read the task note body and check whether Acceptance Criteria / Plan / Workpad / Validation were actually completed.
2. Trace the live feature path promised by the task (cron prompt/script/session, hook, taskpool add/ingest call, generated artifact, etc.).
3. Treat `py_compile`, `proof-check`, `selfcheck`, and autorun proof hashes as control-plane health evidence only. For implementation-class evolution tasks, they do not prove feature delivery by themselves.
4. If the feature path is missing, reopen the task (`done -> pending` or `review`) with an explicit `false_positive_done` reason and structured audit evidence.
5. Re-run `proof-check`, `selfcheck`, `next`, and dashboard generation so the pool reflects the correction.

See `references/false-positive-done-vs-feature-implementation.md` for the detailed pattern and the daily-report-to-taskpool example.
