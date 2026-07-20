# Converge Report — ToB Delivery Workflow v1

## Completion boundary

`pilot`: the reusable delivery workflow, manifest schema, validator and UAEC progress trial are implemented and locally verified. This does not claim production delivery, client acceptance or a publishable case.

## Spec-to-evidence matrix

| Acceptance claim | Artifact evidence | Executable evidence | Status | Boundary |
|---|---|---|---|---|
| Eight-stage lifecycle covers qualification through operations | `ai-agent-b2b-service/references/delivery-grade-software-workflow.md` | skill readback | PASS | procedure only |
| Each stage defines artifacts and exit gates | same reference | skill readback | PASS | procedure only |
| Machine-readable engagement manifest exists | `templates/delivery-engagement-manifest.json` | JSON lint on write | PASS | starter template |
| Verified claims require scope/evidence | `scripts/verify_delivery_workflow.py` | unit tests | PASS | structural validation |
| Accepted stages require owner/artifacts/evidence | validator | unit tests | PASS | structural validation |
| Allowed external actions require target/rollback/readback | validator | unit tests | PASS | does not grant authority |
| Public case requires rights/anonymization/no sensitive markers | validator | unit tests | PASS | case remains not_ready |
| Completion boundary cannot skip prior stages | validator | unit tests | PASS | manifest consistency |
| UAEC progress conflict fails closed | `uaec-progress-red.json` | validator returned 3 errors and expected exit 1 | PASS | negative evidence |
| Reconciled bounded pilot passes | `uaec-progress-green.json` | validator returned PASS | PASS | pilot structure only |
| Existing ToB skill routes to delivery-grade branch | `ai-agent-b2b-service/SKILL.md` v1.1.0 | skill reload/readback | PASS | class-level routing |

## RED evidence

Command:

```bash
python3 ~/.hermes/skills/business/ai-agent-b2b-service/scripts/verify_delivery_workflow.py \
  ~/.hermes/workflows/projects/uaec-react-h5/docs/tob-delivery-workflow-test/uaec-progress-red.json
```

Observed errors:

```text
unresolved contradiction: X_SCOPE_100
claim C_GLOBAL_100 cannot remain verified in unresolved contradiction
claim C_MODULE_GAPS cannot remain verified in unresolved contradiction
```

Expected exit: `1`.

## GREEN evidence

Command:

```bash
python3 ~/.hermes/skills/business/ai-agent-b2b-service/scripts/verify_delivery_workflow.py \
  ~/.hermes/workflows/projects/uaec-react-h5/docs/tob-delivery-workflow-test/uaec-progress-green.json
```

Observed:

```text
PASS .../uaec-progress-green.json: b2b_delivery_workflow_v1 is structurally converged
```

## Regression evidence

```text
.......
Ran 7 tests in 0.000s
OK
```

Covered negative cases:

1. unresolved contradiction;
2. verified claim without evidence;
3. accepted stage without artifact;
4. allowed external action without exact controls;
5. public case without rights/anonymization;
6. completion-boundary stage skipping;
7. valid bounded pilot.

`py_compile` also passed for validator and test script.

## Reconciliation decision

The historical “100% Android functional parity” statement is preserved but marked `superseded` in the trial manifest because its denominator is not established and a newer module plan reports substantial remaining gaps. The newer plan is used to block a current whole-project claim, but its percentages are not promoted into runtime acceptance.

## Negative evidence and authority

- No UAEC business code changed.
- No project status/profile was rewritten to manufacture convergence.
- No historical evidence was deleted.
- No push, deploy, external send, credential entry, payment or production mutation occurred.
- Public-case status remains `not_ready` with sensitive markers recorded.
- Client acceptance remains `not_requested`.

## Closure state

`accepted` for the internal `pilot` workflow trial only.

Remaining stages:

- S5 production delivery: not started; requires a real scoped client delivery target and production evidence.
- S6 acceptance/handover: not started; requires real client/operator UAT and acceptance.
- S7 operations/ratchet: not started; requires a live operating cycle and KPI readback.
