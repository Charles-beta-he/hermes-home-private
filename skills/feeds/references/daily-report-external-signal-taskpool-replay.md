# Daily report external-signal taskpool replay

Applicability: use when a daily report includes GitHub Trending, Product Hunt, AIHOT, Odaily, or similar external signals but expected taskpool candidates were not created. Anti-conditions: do not use this as a blanket rule to ingest all news; ordinary items with no evidence or no Hermes/user workflow mapping should remain out of taskpool.

## Procedure

1. Split the pipeline into two checks:
   - report/body -> governed `*.tasks.json` sidecar candidates;
   - sidecar -> `daily_report_task_ingest.py` -> taskpool.
2. Run the original sidecar through ingest dry-run. If `proposal_count=0`, the break is candidate generation, not taskpool writing.
3. Build a replay sidecar from the report body with governed fields for each candidate. Include GitHub Trending and Product Hunt items that have a plausible product/workflow/open-source/business absorption path; not only architecture-layer items.
4. For Product Hunt items, include competitor/customer/feature/monetization/risk analysis in the downstream objective or dependency order. Preserve open-source/link-resolution status such as unresolved GitHub evidence.
5. Run ingest dry-run and assert candidate count, `invalid_count=0`, and expected multimodel normalization.
6. For write verification, use an isolated temporary brain vault plus isolated ingest state/manual-request paths. Never replay into the real taskpool unless explicitly asked.
7. Run write twice: first pass should create tasks; second pass should create zero and skip by `already_emitted_for_report`/dedupe.
8. Check `brain_task_orchestrator.py add` enum constraints before blaming ingest. In this setup `architecture_target` is constrained; map broad labels such as `hermes-agent` or `browser-automation` to allowed values like `taskpool`, `local-brain`, `provider-quota`, `skill-graph`, `L*`, or empty.
9. Save artifacts: original sidecar baseline, replay sidecar, dry-run JSON, isolated write JSON, and temp vault path.

## Output contract

Report:

- original sidecar proposal count;
- replay candidate count by source (GitHub/PH/etc.);
- dry-run invalid/skipped/dry-run counts;
- isolated write first-pass created count;
- isolated write second-pass skipped count;
- where the actual break lives: candidate generation vs ingest/taskpool.
