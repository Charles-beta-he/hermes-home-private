# Evidence modality contract

Scope: class-level debugging and engineering-review evidence selection. This reference abstracts repeated UI/mobile incidents into a reusable proof-selection rule for all project types.

Applicability:
- A bug, regression, workflow failure, data mismatch, release issue, or product behavior has received repeated fixes or affects a core path.
- The agent is about to claim completion from a proof type that may not observe the disputed variable.
- The user challenges whether the current evidence gate is too local, too implementation-specific, or not transferable.

Anti-conditions:
- Do not require heavyweight cross-surface evidence for a deterministic one-line defect whose changed variable is directly proven by a focused test.
- Do not require UI-specific screenshots/coordinates for backend, API, workflow, data, release, or control-plane bugs unless the disputed variable is visual.
- Do not treat this reference as permission to skip domain-specific evidence when the domain requires it.

## Core rule

Completion evidence must observe the disputed variable at the right boundary. The modality is domain-specific; the abstraction is universal.

Bad universalization:

```text
UI keyboard completion always needs screenshot/coordinates/scroll-owner evidence.
```

Better universal rule:

```text
For any repeated/core issue, completion requires direct readback of the disputed state variable, its controlling owner/writer, and at least one contrast or negative path. The concrete evidence modality must match the domain.
```

## Universal proof contract

Before claiming fixed/complete/certified, answer:

1. What variable or ownership decision is disputed?
2. Who/what produces or controls that variable?
3. What transforms/adapts it before the user/system sees it?
4. What consumes/displays/acts on it?
5. What readback directly observes the variable after the fix?
6. What contrast/negative path proves the fix did not merely move the symptom?
7. What evidence would falsify the current completion claim?

If the proof type cannot observe the disputed variable, it cannot certify completion.

## Evidence modality map

| Domain | Disputed variable examples | Direct evidence examples | Contrast / negative examples |
|---|---|---|---|
| UI / layout / interaction | geometry, visibility, focus, scroll owner, z-index, interaction affordance | screenshot/visual diff, bounding boxes, computed styles, activeElement, event trace, browser/device harness | nearby route, unfocused state, overlay/sheet, keyboard dismiss, non-input page |
| Backend / API | request normalization, branch decision, response contract, error code | request payload, service trace/log, DB/cache readback, response body/status, schema test | invalid input, permission denied, old enum/unknown state, downstream consumer |
| Data / money / status | precision, rounding, enum/status mapping, source of truth | raw value, normalized value, persisted value, displayed/exported value, invariant test | tiny/large values, legacy state, null/unknown, permission-filtered path |
| Auth / permission | identity state, token/session, role/object permission | token/session readback, guard branch, API 401/403/200, route/action permission probe | expired token, wrong role, cross-object access, stale client cache |
| Workflow / taskpool / control plane | lifecycle state, writer identity, claim/lease, receipt | state file/API readback, event log, receipt, worker/job status, idempotency key | stale claim, duplicate event, unauthorized writer, retry/rollback path |
| Release / deploy / runtime | artifact identity, environment, rollout, client freshness | build hash/version, deployment receipt, health/readiness probe, client asset/runtime readback | previous version, failed health, rollback target, cache/service-worker path |
| External dispatch / side effects | target, payload, delivery/receipt, post-send state | dry-run/receipt, target readback, audit log, idempotency record | wrong target, duplicate send, disabled/allowlist-denied path |

## Claim strength levels

- PROPOSED: source/code reasoning only; no runtime/readback evidence.
- LOCALLY VERIFIED: focused test/static check proves the variable in a controlled environment.
- PATH VERIFIED: user/system path readback proves the variable at its real consumer boundary.
- CERTIFIED: path verified plus contrast/negative path plus ownership/falsifier review for repeated/core issues.

Do not use CERTIFIED language for repeated/core issues unless the evidence reaches the variable’s real consumer boundary and includes a contrast or negative path.

## Operational trigger

When a repeated/core issue is detected, replace local proof slogans with this template:

```text
Disputed variable:
Correct owner/writer:
Forbidden competing writers:
Direct readback:
Consumer/readback boundary:
Contrast/negative path:
Falsifier:
Claim strength: PROPOSED | LOCALLY_VERIFIED | PATH_VERIFIED | CERTIFIED
```

## Common pitfalls

1. Turning one incident’s evidence type into a global rule.
2. Treating implementation traces as behavior evidence.
3. Claiming UI completion from DOM alone when geometry/interaction is disputed.
4. Claiming API completion from frontend display alone when service/persistence is disputed.
5. Claiming workflow completion from a command exit code without state/receipt readback.
6. Requiring screenshots for non-visual variables or DB readbacks for purely visual variables.
7. Forgetting the negative/contrast path after fixing the visible symptom.
