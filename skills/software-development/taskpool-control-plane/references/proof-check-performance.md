# proof-check performance pitfall

Applicability: `taskpool_watch_report.py --json` or cron/watchdog timeouts where the stack shows `brain_task_orchestrator.py proof-check --json` spending most time in `verify_autorun_proof_hash`, `verify_autorun_proof_chain`, `read_autorun_proof_events`, JSON parsing, and SHA hashing.

Root cause pattern: `proof-check` scans done tasks and, for every `proof:sha256:*` evidence entry on autorun-audited tasks, re-validates and re-reads the entire `auto_run_proof.jsonl` chain. With hundreds of terminal tasks and thousands of proof events this becomes O(evidence_refs × proof_log_lines), easily exceeding watcher timeouts.

Safe fix pattern:
1. Profile first (`cProfile` around `brain_task_orchestrator.py proof-check --json`) and confirm the hot path.
2. Add a read-only chain cache/index keyed by proof log path + `mtime_ns` + size.
3. Validate the proof chain once per signature, cache `(ok, failures, event_hash_set)`, and make `verify_autorun_proof_hash()` check set membership.
4. Do not weaken proof semantics: malformed chain still fails; invalid old terminal proof hashes remain warnings/debt, not passes.
5. Add a regression test that checks several proof hashes and asserts the proof log is read at most once/twice.
6. Verify with live commands:
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py proof-check --json`
   - `python3 ~/.hermes/scripts/taskpool_watch_report.py --json`
   - `python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json`

Evidence pattern from 2026-06-29: live `proof-check` improved from ~85s / watcher timeout to ~0.45–0.50s while preserving `status=PASS`, checked terminal task count, and warning debt visibility.
