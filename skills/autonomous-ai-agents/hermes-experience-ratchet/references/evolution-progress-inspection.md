# Evolution progress inspection pattern

Use when the user asks to check existing evolution direction/progress, 自进化进度, 经验棘轮进度, or whether Hermes self-improvement is actually advancing.

## Goal

Do not only inspect ExperienceAtom counts. Produce an evidence-backed cross-plane status that separates:

1. capture/proposal health;
2. proposal landing backlog;
3. PA/autonomous evolution signals;
4. self-improvement queue/actionability;
5. cron/runtime health;
6. taskpool dispatchability and safety pauses.

## Minimal evidence bundle

Run/read the equivalent of these checks when available:

```bash
python3 ~/.hermes/scripts/experience-ratchet-maze.py validate
python3 ~/.hermes/scripts/experience-ratchet-maze.py query
python3 ~/.hermes/scripts/pa_evolution_daily_noagent.py
python3 ~/.hermes/scripts/autonomous_evolution_nightly_noagent.py
python3 ~/.hermes/scripts/self-improvement-pipeline.py
python3 ~/.hermes/scripts/cron-health-quarantine.py
python3 ~/.hermes/scripts/behavioral-benchmark-runner.py
python3 ~/.hermes/scripts/unified-health-check.py
python3 ~/.hermes/scripts/brain_task_orchestrator.py dashboard --json
python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json
python3 ~/.hermes/scripts/taskpool_dynamic_runner.py --json
```

If commands differ on the live machine, use the local skill/docs and report the exact replacements.

## Interpretation rules

- `experience-ratchet validate OK` plus many `promoted_candidate` atoms means capture/proposal is healthy but landing may be stalled.
- Proposal backlog is a first-class progress blocker even when runtime health is green.
- `state_advanced=false` in nightly evolution is not automatically failure; distinguish safe audit/no-op from missed low-risk patch proposal opportunities.
- If self-improvement reports cron issues, cross-check live cron health before treating stale/aggregated signals as current blockers.
- `dispatchable=true` with `autorun_skipped_reason=human_escape_active_preclaim` means work exists but safety pause is gating auto-execution. Diagnose/ack/fix the human-escape failures before calling the pool idle.
- Historical proof debt in taskpool selfcheck should be reported separately from current dispatch blockers.

## Output shape

Prefer a compact layered report:

- one-line verdict;
- evidence commands and observed statuses;
- per-plane status: Experience Ratchet, PA, nightly/autonomous evolution, self-improvement pipeline, behavioral benchmark, unified health, taskpool, upstream ratchet;
- P0/P1/P2 next actions.

Avoid implying that green health checks equal delivered evolution. Separate “system healthy”, “experience captured”, “proposal landed”, and “taskpool actively executing”.
