# Cron / Kanban / Selfcheck Repair Pattern

Use when Hermes diagnostics shows yellow/red from a mix of cron failures, Kanban projection drift, and selfcheck judgement backlog.

## Landing-zone classifier

- Cron job last_status errors -> operational repair / verification, not memory.
- Kanban stale projection -> projection/index repair; source task truth remains canonical.
- Selfcheck `waiting_for_judgement` explosion -> projection/noise-control repair unless distinct plan ids represent genuinely separate decisions.
- Provider/network transient -> retry/gate pattern; capture endpoint probe + governed rerun, not the transient error itself.

## Procedure

1. Baseline with modular diagnostics:
   - `python3 ~/.hermes/diagnostics/runner.py --json`
   - classify failed checks by component and blast radius.
2. For cron failures:
   - inspect `~/.hermes/cron/jobs.json` and latest `~/.hermes/cron/output/<job_id>/...`.
   - run provider/network probes before retrying provider jobs when available.
   - rerun only bounded jobs through `hermes cron run <job_id>` then `hermes cron tick`; read back `last_status`, `last_error`, and delivery error.
3. For taskpool dynamic runner failures:
   - if `human_escape_active_preclaim` is present, the safe behavior is OK/no-op at preclaim: no task claim, no autorun, no proof-check escalation.
   - verify with the runner's focused tests and a live no-op run.
4. For Kanban projection drift:
   - treat local-brain notes/task records as source-of-truth and Kanban DB as projection.
   - backup `~/.hermes/kanban.db` before mutation.
   - archive stale Kanban rows whose canonical source is already `done`; do not change the source task note.
   - structured blocked + source `review` may be an aligned review gate, not drift; coverage checks should classify that separately.
   - regenerate dashboard and rerun `kanban_coverage.py --json`.
5. For selfcheck backlog:
   - do not rewrite append-only ledgers.
   - projection surfaces should count unique open `waiting_for_judgement` plan ids, not every repeated append of the same deterministic plan id.
   - rebuild/read projections after patching projection logic.
6. Final verification:
   - focused tests for changed scripts/source.
   - `python3 ~/.hermes/diagnostics/runner.py --mode status` and `--json`.
   - read back affected cron job statuses and Kanban coverage.

## Anti-conditions

- Do not mark taskpool tasks done from diagnostics alone.
- Do not delete selfcheck ledgers to reduce counts.
- Do not globally disable cron/provider jobs because one provider retry failed.
- Do not record the incident itself in memory; only the reusable repair pattern belongs here.
