# Proof debt migration: body proof -> structured evidence

Use when `brain_task_orchestrator.py proof-check --json` fails on historical tasks that are already `done` but still have `evidence: []` or ad-hoc evidence tokens.

## Symptoms

- `done task missing evidence: <task-id>`
- `unstructured evidence in <task-id>: multimodel_gate:FAIL`
- `evidence-spine --json` reports `gate_status: WARN/FAIL` even though the active control plane is otherwise healthy

## What worked

### 1) Migrate historical body proof instead of fabricating new verification

Several closed work tasks had:
- detailed `## Proof Log`
- detailed `## Final Handoff`
- but frontmatter `evidence: []`

Repair pattern:
- read the existing note
- extract the already-recorded verification themes (browser/test/build/curl/commit/etc.)
- add one concise structured frontmatter entry such as:

```yaml
evidence:
  - "proof: legacy body evidence migrated from Proof Log / Final Handoff; keywords=browser, test, build, curl, commit, verification; summary=..."
```

This keeps history truthful while satisfying machine checks.

### 2) Normalize ad-hoc multimodel status lines

These failed proof-check as unstructured evidence:

- `multimodel_gate:FAIL`
- `multimodel_decision:CONTINUE_LOOP`
- `multimodel_status:not_certified`
- `multimodel_auto_outcome:certification_failed`

A working normalization is:

- `classification:multimodel_gate=FAIL`
- `classification:multimodel_decision=CONTINUE_LOOP`
- `classification:multimodel_status=not_certified`
- `classification:multimodel_auto_outcome=certification_failed`

This preserves machine-readable taxonomy without pretending those are test proofs.

### 3) Split mixed legacy proof lines

If a legacy `proof:` line embeds both an artifact path and a prose summary, split it into:

- `artifact:/absolute/path/...`
- `proof: concise deterministic summary ...`

## Verification sequence

Run in this order:

1. `python3 ~/.hermes/scripts/brain_task_orchestrator.py proof-check --json`
2. `python3 ~/.hermes/scripts/brain_task_orchestrator.py evidence-spine --json`
3. `python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json`
4. `HERMES_LOCAL_BRAIN_AUTORUN=1 python3 ~/.hermes/scripts/brain_task_dispatch_tick.py --print-always --autorun-step --no-state`

Expected outcome after cleanup:
- `proof-check`: `PASS`
- `evidence-spine`: `gate_status: PASS`
- dispatch tick remains `OK` and can continue advancing unrelated tasks

## Notes

- This is a governance cleanup pattern, not a license to backfill imaginary evidence.
- Prefer fixing notes over teaching runtime to ignore debt when the note already contains the necessary proof.
- Remaining `semantic control-plane warning:` items are a separate class of work from proof debt cleanup.
