# Mobile multi-model routing verification

Use when a mobile/PWA/RN companion is described as having "多模型智能路由", "model routing", "hybrid/local/Gateway model fallback", or similar.

## Core distinction

Do not collapse three different routing layers into one claim:

1. Mobile product routing: offline deterministic answer, evidence-gated local model adapter, speech recognition path selection, queued handoff, Gateway dialog turn.
2. Gateway / server model routing: ASR provider selection, online dialog model or Hermes session boundary, cost/latency/risk routing.
3. Hermes host multi-model routing: `model-router.py` candidate pool, provider availability, producer/reviewer pair selection, readiness gates, quorum/certification behavior.

A project may pass mobile tests and still not have production-grade multi-model routing if the host/router readiness is fail-closed or the mobile app has only fallback-path routing.

## Verification procedure

1. Locate the project/profile SSOT first and identify which layer the user is asking about.
2. Inspect the mobile code paths for explicit routing functions or contracts:
   - offline/evidence responder;
   - local model adapter acceptance/rejection rules;
   - speech/ASR path selector;
   - Gateway dialog turn client/server boundary;
   - UI receipt showing selected path or degradation reason.
3. Run focused mobile/workspace verification before making claims:
   - offline/local model tests;
   - Gateway contract tests;
   - RN/PWA tests that cover route/path selection;
   - production/readiness gate if present.
4. Separately run Hermes host model-router checks when the claim includes "multi-model":
   - `python3 ~/.hermes/scripts/model-router.py probe`
   - `python3 ~/.hermes/scripts/model-router.py readiness`
   - `python3 ~/.hermes/scripts/model-router.py status`
   - `python3 ~/.hermes/scripts/model-router.py select-pair --task-tier <tier> --task-class <class>`
5. Interpret readiness fail-closed as a boundary, not a failure of all routing:
   - provider availability proves candidate reachability only;
   - pair selection proves router mechanics only;
   - readiness PASS is needed before claiming production-grade automatic multi-model routing.

## Acceptance wording

Good closeout language:

- "Mobile fallback/intention routing is implemented and tested."
- "Hermes host multi-model candidates are available and pair selection works."
- "Production-grade multi-model routing is not certified because readiness is fail-closed: <reasons>."

Avoid:

- claiming "多模型智能路由已完成" solely from mobile tests;
- treating a local model adapter as equivalent to cloud multi-model orchestration;
- treating provider probe availability as quota/diversity/readiness proof;
- hiding fail-closed readiness behind a passing build.

## Anti-conditions

Do not use this as proof of UI acceptance, App Store/TestFlight readiness, real-device microphone quality, deployed production state, or external side-effect authority. Those need their own platform-specific gates.
