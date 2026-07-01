# Daily report GitHub/Product Hunt sidecar candidates

Applicability: use when a generated daily report includes GitHub Trending, Product Hunt, or similar external-source tables and those items should be considered for governed taskpool intake. Anti-condition: ordinary news or weakly-related links should remain report-only unless they have evidence-backed user/Hermes mapping.

## Candidate generation rule

The markdown report body is not enough. If GitHub/PH items should be actionable later, the report flow must also emit a `daily_report_task_candidates_v1` sidecar with one governed candidate per worthwhile item.

For each GitHub Trending repo candidate, include:

- stable `dedupe_key`, e.g. `daily-report:github:<owner>/<repo>`;
- report path as `evidence_bundle`;
- rank/stars/summary in `acceptance_evidence`;
- priority (`P2` for strong Hermes/user-workflow fit, otherwise `P3` watch/analysis);
- anti-drift check: do not implement just because it trended;
- acceptance boundary: evidence extraction, Hermes/user-goal mapping, and decide PoC vs watch.

For each Product Hunt product candidate, include:

- stable `dedupe_key`, e.g. `daily-report:producthunt:<slug>`;
- PH URL, votes, source mode, and open-source/link-resolution state in evidence;
- dependency/order that explicitly covers competitor, customer, feature, monetization, and risk analysis;
- anti-drift check for PH hype, auth/paywall/credential side effects, and reproducibility cost.

## Verification checklist

1. Run `daily_report_task_ingest.py --proposal-json <sidecar> --json` without `--write`.
   - Healthy: all intended candidates are `dry_run`; `invalid_count=0`.
2. If testing writeback, use a temp vault by setting `HERMES_BRAIN_VAULT`, `HERMES_DAILY_REPORT_INGEST_STATE`, and `HERMES_DAILY_REPORT_MANUAL_REQUESTS` to temp paths.
3. Run temp-vault `--write` twice.
   - First run: `created_count == candidate_count`.
   - Second run: `created_count=0`, skipped by `already_emitted_for_report`.
4. Read back at least one temp task to verify evidence, priority, and analysis boundary survived frontmatter/body projection.

## Pitfall: orchestrator enum boundary

`brain_task_orchestrator.py add --architecture-target` accepts a limited enum. Do not emit values such as `hermes-agent` or `browser-automation` unless the CLI supports them. Normalize to an allowed target such as `taskpool`, `local-brain`, `provider-quota`, `skill-graph`, or an `L*` layer, and preserve the more specific mapping in the evidence text if needed.
