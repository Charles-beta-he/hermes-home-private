# Mobile Gateway → Host Multi-Model Router Contract

## Scope / applicability

Use when a mobile/PWA/RN companion should be analyzed or connected through the Hermes host conversation/task multi-model router, especially when the user says “用多模型智能路由分析移动端项目”, “全盘推进”, or challenges whether the mobile app really uses the host router.

This pattern applies to mobile companion products where:
- mobile is not the canonical fact authority;
- Gateway or a server-side bridge owns online authority;
- the host agent has a model router / multi-model consultation layer;
- the first safe landing should be evidence, routing readback, and fail-closed behavior before reviewer/arbitration side effects.

Anti-conditions:
- Do not claim full production multi-model execution from a local app route selector, ASR fallback, or a router probe alone.
- Do not treat a multi-model advisory run as certification if truth/evidence gating returns degraded/not_certified.
- Do not claim reviewer execution/arbitration just because a reviewer model was selected; reviewer metadata is not a second pass.
- Do not make mobile user-visible behavior depend on an unbounded or flaky provider path without fail-closed fallback.

## Correct sequence after user correction

If the user asks for host multi-model routing analysis, do not stop at code search or `model-router.py probe`. Run the actual host multi-model analysis path first or clearly label why it is blocked:

1. Build a compact evidence prompt with current source/test facts.
2. Run the multi-model fan-out/discussion path (for Hermes this is typically `consult_models.py state ...` then `consult_models.py run --discussion ...`).
3. Report whether the run is certified, degraded, or not certified.
4. Then inspect/modify the mobile project as needed.

A router probe/select-pair only proves candidate availability and selection, not that this conversation/project analysis used multi-model review.

## Minimal safe landing: read-only routingDecision

The smallest production-safe bridge is a default-off, fail-closed contract at the Gateway mobile dialog boundary:

```ts
interface MobileDialogRoutingDecision {
  hostRouterUsed: boolean;
  decisionSource:
    | 'feature_disabled'
    | 'host_model_router'
    | 'host_router_fail_closed'
    | 'host_router_error'
    | 'idempotent_replay';
  selectedProvider?: string;
  selectedModel?: string;
  reviewerProvider?: string;
  reviewerModel?: string;
  fallbackReason?: string;
  evidencePolicy: 'session_boundary' | 'host_router_readonly' | 'stored_replay';
  routerReadiness?: { status: 'PASS' | 'FAIL_CLOSED' | 'UNKNOWN'; failures: string[] };
}
```

Recommended behavior:
- Default off unless an explicit env/feature flag is true.
- On each non-replay mobile dialog turn, compute `routingDecision` before calling the existing session boundary.
- Call host router readiness first; only call select-pair when readiness is PASS.
- If readiness fails or router errors, record `fallbackReason` and keep the existing session boundary.
- Include `routingDecision` in the HTTP response and pass it downstream to the session/API bridge.
- For idempotent replay, do not re-run the router; return `decisionSource='idempotent_replay'`.

## Next safe landing: producer execution override

Once the host session/API or CLI boundary supports per-turn model/provider override, upgrade the bridge from “read-only evidence” to “producer execution override” without claiming reviewer closure:

- CLI bridge: when `routingDecision.hostRouterUsed === true` and `selectedModel` exists, pass `--provider <selectedProvider>` when known and `-m <selectedModel>` before the session/oneshot arguments.
- HTTP/API bridge: include `routingDecision`, `provider`, and `model` in the request body or explicit headers, matching the host contract.
- Preserve the existing session key (`mobile:<deviceId>:<conversationId>` or equivalent); routing should choose the model, not fork the conversation boundary.
- Return routing readback in the mobile response, but distinguish selected model from actual-executed model unless the host explicitly returns actual execution metadata.
- Keep reviewer fields as metadata until a real second-pass review/arbitration call is implemented and verified.

### Provider inference from router output

Some `model-router.py select-pair` outputs put `provider` only inside `quota_snapshot`, not on `producer`/`reviewer` directly. Do not pass only `-m` and hope the host infers the same provider. Infer provider by matching the selected model against:

1. `producer.provider` / `reviewer.provider` if present;
2. `producer.quota_snapshot` / `reviewer.quota_snapshot` entries whose `model` equals the selected model;
3. a top-level `quota_snapshot` fallback if the router version emits one;
4. the snapshot key prefix before `::` as last resort.

Add a contract test with a fake router that emits provider only in nested `quota_snapshot`, and assert the downstream mobile dialog client or fake CLI sees both provider and model.

### Task-class override for live smoke

A deterministic production smoke may need a bounded task-class override without changing the default product contract. Keep the product default at `mobile-dialog`, but allow an env such as `HERMES_MOBILE_HOST_ROUTER_TASK_CLASS` for verification or project-specific routing policy.

Use this only to select a live, low-risk provider lane for smoke; record the task class in the evidence/profile. If the default task class explores an unavailable OAuth/CLI provider and the smoke fails with no final response, capture the successful override pattern, not a permanent negative rule about that provider.

## Verification checklist

- Contract tests cover: feature disabled, host router PASS, fail-closed fallback, idempotent replay, downstream receives `routingDecision`.
- Producer execution override tests cover: CLI args include selected provider/model; API body includes routingDecision/provider/model; provider can be inferred from nested quota snapshots.
- Production gate contains anchors for the routing contract, task-class override, and tests so future refactors cannot silently remove them.
- Workspace verification passes after the change: focused Gateway build/test plus full production verification.
- Real smoke with the feature flag enabled returns HTTP 200, `hostRouterUsed=true`, selected producer/reviewer provider+model, routerReadiness PASS, and a known response from the selected producer.
- Project profile/ledger records the default-off/fail-closed boundary, the smoke task class if overridden, and whether reviewer remains metadata-only.

## Reviewer execution lane (second safe landing)

After producer execution override is verified, the next bounded step is a default-off reviewer lane. This still is not full arbitration, but it is a real second model call.

Recommended contract:

```ts
interface MobileDialogReviewerDecision {
  reviewerExecuted: boolean;
  verdict: 'pass' | 'needs_attention' | 'unknown';
  reviewerProvider?: string;
  reviewerModel?: string;
  summary?: string;
  fallbackReason?: string;
}
```

Recommended behavior:
- Default off unless an explicit flag such as `HERMES_MOBILE_HOST_ROUTER_REVIEW_ENABLED=true` is set.
- Execute reviewer only after the producer response is delivered internally and only when `routingDecision.hostRouterUsed === true` and `reviewerModel` exists.
- Use `routingDecision.reviewerProvider` / `reviewerModel` for the reviewer CLI/API override; do not reuse the producer provider/model by accident.
- Reviewer failure must be fail-soft for the user response: preserve the delivered producer answer and return `reviewerExecuted=false`, `verdict='unknown'`, and a bounded `fallbackReason`.
- Reviewer output should be structured JSON when possible, but Hermes CLI may append verification-gate footer text after the model output. Parse the first balanced JSON object from stdout before falling back to plain text; otherwise `summary` can be polluted by `[Hermes verification gate] ...` footer noise.
- Keep reviewer output bounded/sanitized for mobile clients; expose `verdict` and concise `summary`, not raw CLI logs.

Verification additions:
- RED test that `reviewerDecision` is absent before implementation, then GREEN after the reviewer lane is wired.
- Contract test that the reviewer receives the producer response and the reviewer provider/model.
- Contract test that JSON before a Hermes footer is parsed cleanly.
- Real provider smoke can use a deterministic local router shim to force known-good producer/reviewer providers, but label this as an execution-chain proof, not a certified live host-router readiness proof.

## Upgrade path to full reviewer/arbitration closure

To move beyond producer override + reviewer execution into true production multi-model arbitration:

1. Host session/API layer must return actual-executed provider/model readback, not only selected provider/model.
2. Reviewer lane must perform a real second-pass review call and return a structured reviewerDecision.
3. Arbitration policy must consume producer + reviewer results and define what happens on `needs_attention` or reviewer failure.
4. Gateway tests must assert selected-model execution readback, fail-closed fallback, reviewer result handling, and arbitration outcomes.
5. Multi-model certification must be rerun with claim-linked evidence and pass its truth gate.

## Pitfalls

- **Conflating routing layers.** Separate mobile-internal routing (evidence gate/local fallback/ASR), host routing (availability/readiness/producer-reviewer selection/consult_models), and integrated execution (Gateway causes host to actually execute the selected model and returns readback). Only integrated execution plus reviewer call is full multi-model closure.
- **Treating reviewer selection as reviewer execution.** A reviewer model in `routingDecision` is only a plan/readback until a second call is made and its result is consumed.
- **Losing provider on handoff.** Router output may have the selected provider in nested quota snapshots; without provider inference, CLI/API override can silently fall back to the wrong default provider for the model.
- **Letting smoke randomness define product policy.** If router exploration chooses a provider that is currently unavailable, use a task-class/sticky override for the smoke and record the boundary; do not hard-code a session-specific workaround as the default product route.
