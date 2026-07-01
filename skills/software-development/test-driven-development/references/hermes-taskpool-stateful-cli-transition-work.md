# Hermes Taskpool / Stateful CLI Transition Work

Extracted from `/Users/charles/.hermes/skills/software-development/test-driven-development/SKILL.md` on 2026-07-01T08:55:33.664327+00:00 by generic core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

## Hermes Taskpool / Stateful CLI Transition Work

See also `references/taskpool-parent-aggregator-tdd.md` for the dedicated TDD checklist for read-only parent evidence aggregators that diagnose oversized parent tasks split into many child tasks.
See also `references/historical-idle-window-replay-testing.md` for replaying real idle-window cron/ledger data through the current state transition logic without mutating production state.

When changing Hermes taskpool/control-plane scripts or any stateful CLI/orchestrator:

0. For standalone tools under `~/.hermes/scripts`, test the full CLI/proof-artifact contract with subprocess-based tests. If the system Python lacks pytest, use the Hermes repo venv pytest when available (for this setup: `/Users/charles/.hermes/hermes-agent/.venv/bin/python -m pytest ...`). Treat this as a setup fix, not a reason to skip RED/GREEN.
1. Projection self-ingestion guard (applicability: local agent-history exporters, cache writers, indexers, or report generators that read conversation/session history and write durable projections; anti-condition: ordinary scripts that do not read their own historical outputs). Add RED tests proving the tool’s own prompts, generated JSON, skill/system boilerplate, scheduled-job output, and iteration-relay text are not re-exported as user facts. Run the fixture with those contaminants before implementing filters. When the projection has staging/production promotion, add RED tests for stale-cache fallback, invalid staging rejection, dedup-aware incremental merge (`merged_ids == unique(base_ids ∪ incremental_ids)`), post-promotion readback, and read-only health-report threshold behavior before changing the writer or cron path.
2. Write RED tests around the **state transition**, not just helper functions. Assert frontmatter/body mutations, derived fields, CLI JSON actions, process exit codes, and emitted proof artifacts.
2. Use fixture tasks/artifacts that mimic the real control-plane evidence shape (`discussion_result.json`, blocked/retry status, proof log sections) so the failure proves the workflow, not a toy helper.
3. Add a second-cycle closure test whenever the feature spans phases, e.g.:
   - trigger auto-split from blocked/non-convergence
   - mark generated subtasks done
   - verify parent reopen/sync on `reconcile` or the primary resolver path
4. Treat CLI/control-plane JSON output as part of the contract. Add RED assertions for structured action payloads (`action`, `resolved/kept_blocked`, `taxonomy_axes`, `axis_rationale`, counts, reopen reasons) instead of only checking file text. When diagnostics guide later automation, test that they are returned explicitly, not just implied by side effects.
5. When a control-plane workflow derives follow-up work from failure analysis, add RED coverage that the diagnostic taxonomy survives the whole path: gate/writeback -> task frontmatter/body -> resolver/auto-split JSON result. This prevents "analysis exists but downstream step cannot consume it" regressions.
6. When you introduce new task metadata fields, treat persistence/display as separate contract surfaces. Add RED assertions that the fields survive all of these layers as needed: in-memory task state, serialized frontmatter (`SAVE_FIELDS`/persisted keys), preferred frontmatter ordering for operator readability, and command JSON. A feature is not done if the diagnostic exists only in memory or only in one output path.
7. For goal/workflow/control-plane upgrades, add RED coverage for the **contract and the safety boundary** before implementation:
   - structured state persists and reloads across managers/sessions (for example spec/route/evidence fields);
   - route/classifier decisions are explicit and inspectable;
   - dry-run operations prove they do not mutate taskpool/mission/cron/executor lifecycle state;
   - status/CLI output exposes the contract without breaking existing commands.
8. After GREEN on targeted tests, run a **real task dry verification** against the actual taskpool entry to confirm:
   - idempotent re-run is a no-op
   - already-done parents are safe no-ops
   - proof log is appended, not overwritten
   - structured diagnostics remain present in command output for operators/control-plane consumers
9. For stateful CLI wrappers that expose `main(argv=None)`, add/keep an import-level test that calls `main()` under pytest. Guard against accidental pytest-argv parsing: inside `main`, use `parser.parse_args([] if argv is None else argv)`, and in the script entrypoint call `main(sys.argv[1:])`. This preserves real CLI flags while keeping imported tests deterministic.
10. If unrelated legacy tests fail, classify them explicitly as pre-existing/off-scope instead of silently broadening the task.
