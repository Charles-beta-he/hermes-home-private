# Native multimodel task contracts

Use this note when evolving Hermes/local-brain taskpool intake, dispatch, or multimodel certification flows.

## Durable lesson

When taskpool multimodel analysis is treated as a heuristic inferred from priority, lane, status, or title keywords, the system drifts and external intake can lose the user's intended verification requirement. Long-term maintainable landing is to make multimodel analysis a task creation/intake contract.

## Contract shape

Separate two layers:

1. Intake governance / scheduling triage
   - `priority_layer`
   - `dependency_order`
   - `multimodel_triage_result`
   These describe pre-creation or entry triage: priority band, dependency order, and whether the task deserves multimodel attention.

2. Multimodel certification contract
   - `requires_multimodel`
   - `multimodel_reason`
   - `expected_participants`
   - `truth_gate`
   - `evidence_bundle`
   These describe the actual certification requirement and should persist in task frontmatter and be visible in list/row JSON.

Do not collapse these layers: triage answers "how should this enter the pool?"; certification contract answers "what verification does this task require?".

## Implementation checklist

For native landing in `brain_task_orchestrator.py`-style control planes:

1. Add CLI `add` arguments for the certification contract.
2. Persist the fields in frontmatter with deterministic render order.
3. Add parser support in inbox/intake metadata so external repo/article tasks do not lose the contract.
4. Pass parsed metadata through `ingest-inbox`'s `argparse.Namespace` into `command_add`.
5. Make `task_multimodel_intervention_reasons()` consume explicit contract fields before heuristic signals.
6. Treat `requires_multimodel` as a strong trigger, e.g. `explicit_requires_multimodel`.
7. Expose the contract in `Task.row()` / list JSON for observability.
8. Keep expensive autorun fail-closed; contract expression should not automatically imply model execution unless the existing explicit autorun gate is enabled.
9. Add tests for both direct `add` and `ingest-inbox` contract preservation.

## Test harness pitfall

If the control plane has fail-closed creation governance, existing positive-path tests may need default governance fields injected by helpers/harnesses:

- `--priority-layer`
- `--dependency-order`
- `--multimodel-triage-result`

Do not add those defaults to negative tests that intentionally verify the missing-field fail-closed behavior. For negative tests about another gate, provide these governance fields explicitly so the test reaches the intended gate instead of failing earlier.

## Verification

Minimum verification after modifying this class of flow:

```bash
cd ~/.hermes/scripts
python3 -m py_compile brain_task_orchestrator.py test_brain_task_orchestrator.py
python3 test_brain_task_orchestrator.py

cd ~/.hermes
python3 scripts/taskpool_run_validation_suite.py --dry-run
```

If a mirrored source repo also has tests that call the live `~/.hermes/scripts/brain_task_orchestrator.py`, run the mirror tests too because they may fail against the newer live control plane even when their local copy is older.
