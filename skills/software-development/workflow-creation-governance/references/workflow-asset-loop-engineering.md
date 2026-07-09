# Workflow Asset Loop Engineering Reference

This reference records the stabilized local implementation contract.

## End-to-end local loop CLI

Path: `~/.hermes/scripts/workflow_kernel_loop.py`

Commands:

```bash
# Run the safe local loop once: decide -> module plan -> optional asset scaffold -> usage ledger.
python3 ~/.hermes/scripts/workflow_kernel_loop.py run-once \
  --seed '<seed>' \
  --observed-repetition 3

# Mine the local usage ledger for candidate composite modules.
python3 ~/.hermes/scripts/workflow_kernel_loop.py synthesize
```

The end-to-end loop writes only local receipts under `~/.hermes/workflows/workflow-kernel-loop/` unless `--root` is supplied. It keeps external/cron/taskpool/AgentOS side-effect flags false.

## Helper CLI

Path: `~/.hermes/scripts/workflow_asset_decision.py`

Commands:

```bash
python3 ~/.hermes/scripts/workflow_asset_decision.py decide --seed '<seed>' --observed-repetition 2
python3 ~/.hermes/scripts/workflow_asset_decision.py compile --seed '<seed>' --observed-repetition 2
python3 ~/.hermes/scripts/workflow_asset_decision.py scaffold --seed '<seed>' --observed-repetition 2
python3 ~/.hermes/scripts/workflow_asset_decision.py validate --asset ~/.hermes/workflows/assets/<id>/workflow.json
```

## Fail-closed guarantees

The helper only performs local JSON classification/scaffold writes. It does not:

- send external messages;
- mutate taskpool lifecycle;
- enable cron;
- enable AgentOS runtime mutation;
- publish/deploy/push;
- delete resources;
- write memory.

Scaffolded `state.json` records all side-effect flags as false.

## Route eval minimum before promotion

Every candidate needs:

- positive examples;
- negative examples;
- neighbor workflows if overlap exists;
- forbidden triggers, especially keyword-only prompts;
- evidence readback or dry-run receipt.

Canonical promotion additionally needs validated/common history, regression evidence, rollback/migration plan, and advisory review when risk warrants.
