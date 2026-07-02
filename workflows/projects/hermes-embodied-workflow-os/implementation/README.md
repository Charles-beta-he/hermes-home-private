# HEWOS P1 Contract Core

Status: validated local slice, no runtime/hardware integration.

This package implements the first local contract-only slice for `hermes-embodied-workflow-os`.

Included:
- CapabilityManifest validation and in-memory registry.
- Observation validation.
- ActionIntent validation with SafetyGate + ExternalControlGate requirements for executable risk classes.
- EvidenceLedgerEntry validation.
- VerificationResult validation.
- Append-only in-memory EvidenceLedger prototype.
- Replay reducer that derives WorldState from ledger entries.
- Mock adapter manifests for CLI, Web, glasses, embedded, and robot actors.
- EntryRecommendationEngine seed logic for first-person visual, workbench editing, and high-risk human gate cases.

Boundaries:
- No hardware calls.
- No robot execution.
- No external dispatch.
- No taskpool mutation.
- No Web/PWA/glasses/platform imports in Core.
- Mock robot capability is a dry-run manifest only; it is not an executor.

Run tests from project root:

```bash
python3 -m unittest discover -s implementation/tests -v
```
