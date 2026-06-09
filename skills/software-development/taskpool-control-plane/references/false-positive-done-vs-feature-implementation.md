# False-positive done vs real feature implementation

Use this when a task is marked `done` but the user observes the promised behavior is absent.

## Failure signature

- Task frontmatter says `status: done`.
- Evidence is generic control-plane proof such as `command:py_compile_taskpool PASS`, `proof:sha256:...`, `selfcheck`, or `proof-check`.
- The task objective promises a feature, integration, cron hook, ingestion path, or user-visible behavior.
- The actual runtime path still does not call the new capability.
- Task body acceptance checkboxes / workpad remain unchecked or contain only boilerplate.

## Diagnostic sequence

1. Read the task note, not just `list --json`.
   - Inspect Objective, Acceptance Criteria, Plan / Workpad, Validation, Proof Log, and Final Handoff.
   - Generic lifecycle proof is not enough for implementation tasks.
2. Trace the live runtime path that should exercise the feature.
   - For cron/report features, inspect the cron job prompt/script/session and confirm whether it invokes taskpool `add`, `ingest`, or the intended hook.
   - For source integrations, search scripts/config for the source name and the expected data path.
3. Compare promised acceptance evidence with actual evidence.
   - If acceptance says “script/hook/runner/dry-run/real input verification” but evidence only says `py_compile` or `proof-check`, classify as false-positive done.
4. Correct lifecycle state before claiming success.
   - Reopen to `pending` or `review` with an explicit audit reason such as `false_positive_done: feature not implemented`.
   - Add structured evidence documenting the audit, but do not invent implementation proof.
5. Verify the control plane after reopening.
   - `proof-check --json`
   - `selfcheck --json`
   - `next --json`
   - `dashboard --write --json`

## Implementation-class closeout rule

For evolution tasks whose `capability_delta` promises a concrete feature or integration, `py_compile`, `proof-check`, `selfcheck`, and autorun proof hashes are only control-plane health evidence. They must not be treated as sufficient completion evidence unless paired with at least one feature-specific artifact, such as:

- new or changed script/config/hook path,
- dry-run showing the new pipeline output,
- real input smoke test showing the feature produces the promised behavior,
- generated task/file/report artifact tied to the objective,
- regression test that fails without the implementation and passes with it.

## Example: daily report to taskpool ingestion

A task promising “daily report generates governed taskpool tasks” is not complete merely because the AIHOT daily cron sent a report. Verify all boundaries:

- The report cron prompt/script extracts candidate tasks.
- Candidate tasks are prioritized/deduplicated and carry dependency order / acceptance evidence.
- The pipeline calls taskpool `add` / `ingest` or writes a governed inbox entry.
- A real or fixture daily report produces at least one expected task in dry-run or live mode.
- The taskpool contains the generated task, or the run explicitly reports “no qualifying task” with evidence.

If the cron only reads the website and sends a summary, the report succeeded but task generation is not implemented.