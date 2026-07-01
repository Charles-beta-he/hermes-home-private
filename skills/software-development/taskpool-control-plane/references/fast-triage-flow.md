# Taskpool Fast Triage Flow

Extracted from `/Users/charles/.hermes/skills/software-development/taskpool-control-plane/SKILL.md` on 2026-07-01T08:22:36.087987+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Fast triage flow

0. Confirm which CLI owns taskpool subcommands on this machine.
   - Do **not** assume `brainctl.py` exposes taskpool operations just because a memory note mentions it for brain index operations.
   - First check `python3 ~/.hermes/scripts/brain_task_orchestrator.py --help` and use its taskpool subcommands (`dashboard`, `eligibility-check`, `autorun-runner`, `proof-check`, `evidence-spine`, `selfcheck`) when present.
   - Treat `brainctl.py` as a separate brain/index utility unless its live `--help` output proves otherwise.

0.5. Check the dynamic runner first — it's the cron entrypoint:
   - `python3 ~/.hermes/scripts/taskpool_dynamic_runner.py --json`
   - Key fields: `autorun_skipped_reason` (why autorun was skipped), `summary.next_task_id` (next task to run), `summary.dispatchable` (whether any task is dispatchable)
   - If `autorun_skipped_reason` is `human_escape_active_preclaim` → escape is active, see `references/envelope-bus-escape-triage.md`
   - If `autorun_skipped_reason` is `no_additional_boundary_safe_slots` → all boundary-safe slots are occupied by active claims
   - If `next_task_id` is empty but `dispatchable: true` → eligibility gate is blocking (check `source_weighting_policy_ref`, project name, allowlist)

1. Inspect whether the pool is actually empty.
   - Check active task count and status distribution (`pending`, `blocked`, `claimed`, `running`, `done`).
   - Do not assume `0 running` means `0 work`.

2. Check whether a dispatchable task exists.
   - Run `eligibility-check` and inspect the selected task id / reasons.
   - Inspect `dashboard` or `list` output to confirm the highest-priority candidate.

3. Check whether the control plane is blocked by hard safety gates or only soft governance warnings.
   - Hard blockers usually include: kill switch, permission gate pending, write allowlist/guard failure, current task not dispatchable, invalid autorun proof chain, or self-check failure that affects safe claim.
   - Soft governance warnings include: historical `done` tasks missing evidence, proof-check failures unrelated to the current candidate, evidence-spine `WARN`, or dry-run multimodel advisories.

4. If active work exists but nothing is `claimed`/`running`, manually advance one highest-priority dispatchable P1 task to `claimed` as fail-safe.
   - This is a temporary anti-idle action, not a substitute for fixing automation.
   - Prefer the same task `eligibility-check` nominates.

5. Then fix the automation path.
   - Inspect `brain_task_dispatch_tick.py` behavior and taskpool dynamic-runner logs.
   - Verify the tick distinguishes hard errors from soft governance warnings.
