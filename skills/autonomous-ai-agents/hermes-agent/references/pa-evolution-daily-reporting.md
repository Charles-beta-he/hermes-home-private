# PA evolution daily reporting

Use this reference for scheduled Hermes self-evolution / personal-assistant health jobs that generate a daily report from local PA metrics.

## Core workflow

1. Run `python3 ~/.hermes/scripts/pa-evolution-trigger.py` and capture the trigger report.
2. Run `python3 ~/.hermes/scripts/pa-daily-report.py`.
3. Read the generated report under `~/.hermes/notes/reports/pa-daily-YYYY-MM-DD.md`.
4. Cross-check supporting state when interpreting alerts:
   - `~/.hermes/notes/engineering-cybernetics/pa-health-history.jsonl`
   - `~/.hermes/notes/user-routine-patterns.json`
5. Report both the numeric state (`V_PA`, `V̇_PA`, correction rate) and the trigger interpretation.

## Interpretation rules

- Degradation/root-cause escalation is only required when `V̇_PA < -0.05`.
- `skill_solidify` is meaningful only when the repeated task type is specific enough to become a reusable workflow.
- If the repeated bucket is `unknown`, do **not** recommend creating a dedicated skill yet. Treat it as a taxonomy gap first: improve task-type classification until a stable named domain emerges.
- A flat/stable `V_PA` with `V̇_PA = 0` is not a degradation alert; report it as stable observation, not a failure.

## Reporting guidance

- Call out when the system is stable but below the target threshold; distinguish "no regression" from "meaningful improvement".
- Mention the generated report path explicitly so future jobs can audit the artifact.
- When the scheduler injected a notice that some requested skills were missing/skipped, surface that notice at the start of the report instead of silently ignoring it.

## Pitfalls

- Do not create class-level skills from the `unknown` category alone.
- Do not manufacture root-cause analysis when the degradation threshold was not crossed.
- Do not stop after reading the pretty markdown report; inspect the history and pattern files when asked to evaluate degradation or skill-solidification decisions.
