# Proof-check autorun debt classification

Applicability: `brain_task_orchestrator.py proof-check --json` reports `terminal invalid autorun proof hash debt`, especially after historical tasks accumulated `proof:sha256:*` evidence from more than one proof system.

Anti-conditions:
- Do not whitelist or delete genuine autorun proof debt without append-only proof-log readback.
- Do not weaken the `hermes-autorun review -> done` proof-hash requirement.
- Do not treat every `proof:sha256:*` evidence value as an autorun proof-log membership claim; other proof systems may use labeled hashes such as `proof:sha256:artifact_bundle=...`.

## Root-cause distinction

There are two different meanings that can look similar in task evidence:

1. **Autorun closeout proof**: task body contains a lifecycle line like `Lifecycle transition \`review\` -> \`done\` by \`hermes-autorun...\``. These done tasks must have `proof:<sha256:...>` evidence that is present in the append-only autorun proof log and passes chain verification.
2. **Non-autorun artifact hash label**: task was closed by a bounded non-autorun worker/human path, but evidence contains `proof:sha256:<label>=<hash>` or similar deterministic artifact labels. These should remain structured evidence, but should not be validated against the autorun append-only log.

The durable predicate should classify autorun context from the lifecycle/audit line, not from the existence of a `proof:sha256:` evidence prefix alone.

## Regression pattern

Add a test with a done task containing:

```yaml
evidence:
  - proof:sha256:artifact_bundle=deadbeef
  - command: deterministic closeout PASS
```

and body sections:

```md
## Proof Log
- non-autorun deterministic artifact bundle hash retained.

## Final Handoff
- closed by bounded non-autorun worker.
```

Expected result: `proof-check --json` returns `PASS` and does not emit `terminal invalid autorun proof hash debt`.

Keep the existing autorun tests too:
- `hermes-autorun` done without proof must fail.
- `hermes-autorun` done with a proof hash missing from the append-only log must fail.
- `hermes-autorun` done with a real append-only proof hash must pass.

## Verification

- Run the focused proof-check classification tests.
- Run full `test_brain_task_orchestrator.py` when the touched predicate is shared.
- Run live `proof-check --json` and compare warning count. A drop in warnings is acceptable only when it removes false autorun debt; remaining true autorun debt should stay visible.
