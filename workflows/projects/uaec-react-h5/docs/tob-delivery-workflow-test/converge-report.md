# Converge Report — ToB Delivery Workflow v1

## Completion boundary

`pilot`: the reusable delivery workflow, manifest schema, validator and UAEC progress trial are implemented and locally verified. This does not claim production delivery, client acceptance or a publishable case.

## Spec-to-evidence matrix

| Acceptance claim | Artifact evidence | Executable evidence | Status | Boundary |
|---|---|---|---|---|
| Eight-stage lifecycle covers qualification through operations | `ai-agent-b2b-service/references/delivery-grade-software-workflow.md` | skill readback | PASS | procedure only |
| Each stage defines artifacts and exit gates | same reference | skill readback | PASS | procedure only |
| Machine-readable engagement manifest exists | `templates/delivery-engagement-manifest.json` | JSON lint on write; placeholders deliberately return RED | PASS | starter template |
| Verified claims require scoped, known evidence IDs and exact stage applicability | `scripts/verify_delivery_workflow.py` | unit and mutation tests | PASS | structural validation |
| Accepted closures require a verified outcome and reject unverified/disputed claims; accepted risks require approval, controls and evidence | validator | unit tests | PASS | structural governance |
| Accepted stages require owner, known references, semantic artifacts and a linked verified claim bounded by both claim and cited-source `max_stage` | validator | unit tests | PASS | source capability is structural, not external authentication |
| Absolute local evidence is present, hash-pinned and copied into the candidate evidence packet | RED/GREEN manifests and snapshots | missing/tamper/archive tests | PASS | local immutable bytes only |
| Closure, stage order and maximum completion boundary are consistent; successor records require registered `successor_engagement` evidence | validator | draft/review/accepted/superseded/S6/beyond-boundary tests | PASS | snapshot state machine |
| Allowed external actions require a typed authority grant bound to action/target/scope plus rollback/readback; credential/payment remain human-only | validator | unit tests | PASS | does not grant runtime authority |
| Public/client gates require purpose-specific evidence types; client identity/scope reject exact placeholder tokens and require S6 acceptance | validator | unit tests | PASS | case remains not_ready; client not_requested |
| Malformed nested values do not crash validation | validator | 20,000 seeded mutations | PASS | robustness, not formal proof |
| UAEC progress conflict fails closed | `uaec-progress-red.json` | validator returned 3 errors and expected exit 1 | PASS | negative evidence |
| Reconciled bounded pilot passes | `uaec-progress-green.json` | validator returned boundary=pilot, closure=accepted | PASS | pilot manifest only |
| Existing ToB skill routes to delivery-grade branch | `ai-agent-b2b-service/SKILL.md` v1.3.0 | skill reload/readback | PASS | class-level routing |
| Multi-dimensional technical audit exists | `technical-audit-report.md` | artifact readback and verification matrix | PASS | production gaps remain explicit |

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
PASS .../uaec-progress-green.json: manifest gates passed (boundary=pilot, closure=accepted)
```

## Regression evidence

```text
...................................................
Ran 51 tests in 0.013s
OK
```

Covered dimensions include:

1. unresolved contradiction and verified-claim evidence requirements;
2. source/artifact/metric reference integrity;
3. absolute local evidence existence and SHA-256 tamper detection;
4. observed-date format and future-date rejection;
5. accepted-stage owner/artifact/evidence requirements;
6. ordered stage and closure-state contracts;
7. S6/S7 client-acceptance gates;
8. strict authority booleans and exact external-action grant controls;
9. public-case confidentiality, rights and anonymization;
10. duplicate governed IDs and placeholder rejection;
11. draft, review, blocked and accepted states;
12. malformed nested input resilience.
13. accepted-closure claim settlement and accepted-risk approval controls;
14. publication-rights, anonymization and client-acceptance evidence references;
15. review-ready artifact/evidence packets and reverse S6 acceptance implication;
16. supersession records, registered authority-grant references and stage-linked verified claims;
17. malformed list/dict stage statuses fail closed without crashing.

A seeded 20,000-mutation run returned `CRASHES=0`. Missing and malformed JSON returned exit `2`; a hash-tampered GREEN copy returned exit `1`. `py_compile` also passed. `ruff` and `mypy` were unavailable and are recorded as degraded rather than passed.

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

`accepted` for the internal `pilot` manifest trial only. This means the declared S0–S4 governance artifacts and evidence references satisfy the local validator; it does not mean an end-to-end UAEC business slice, production release or client acceptance was executed.

Remaining stages:

- S5 production delivery: not started; requires a real scoped client delivery target and production evidence.
- S6 acceptance/handover: not started; requires real client/operator UAT and acceptance.
- S7 operations/ratchet: not started; requires a live operating cycle and KPI readback.
