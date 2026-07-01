# Provider runtime availability vs auth availability

Applicability: Hermes/model-router or other multi-provider routing systems where a provider has an OAuth/session/API-key path that appears configured, but real invocations fail at runtime (for example `no final response`, suspended account, disabled service, or CLI wrapper failure). Use this when a readiness/probe command says a provider is available but the actual routed task fails.

Anti-conditions:
- Do not mark a provider permanently unavailable for one transient timeout if a retry succeeds.
- Do not encode credential absence as a durable runtime failure; missing credentials are setup state.
- Do not lower readiness gates just to make routing pass; first separate auth/config evidence from real execution evidence.

## Pattern

1. Split evidence into two layers:
   - auth/config availability: credential/OAuth/CLI exists, provider can be considered configured;
   - runtime availability: a real minimal task produced a final response from the exact provider/model path.
2. If auth/config passes but runtime invocation fails, treat runtime evidence as stronger for production routing.
3. Record a scoped runtime-unavailable snapshot keyed by `provider::model` with:
   - `status: unavailable`
   - `last_reason: runtime_provider_error` (or similarly non-credential reason)
   - a short runtime error excerpt
   - timestamp / count
4. Make router candidate filtering honor this runtime-unavailable snapshot before a generic OAuth/session assumption. OAuth means credentials exist; it does not prove the product/account/model can answer now.
5. Add a regression test before changing the router: seed a temp availability snapshot with `status=unavailable` and assert `_model_available()` / candidate filtering excludes the provider even when the provider is OAuth-based.
6. Recovery is a separate state transition: require a real provider/model smoke to pass before changing the snapshot back to available.

## Router-diversity warm-up checklist

When a readiness gate fails due model dominance rather than implementation bugs:

1. Read the readiness JSON and rebalance plan; do not guess the number of calls.
2. Use real, bounded, auditable non-dominant calls; write them as non-synthetic route outcomes.
3. Prefer already working low-cost/observable alternatives for warm-up; avoid providers with unresolved runtime failures.
4. Rerun diversity monitor, then readiness with auto-certification if available.
5. If readiness passes but a routed smoke selects a runtime-failing OAuth/CLI provider, classify and filter that provider as runtime-unavailable rather than weakening the diversity gate.
6. Verify with a default route smoke, not only a forced task-class/shim smoke.

## Example evidence shape

- `model-diversity-monitor --json --threshold 0.8 --window 500` shows `dominance_warning=false`, `gate_failed=false` after warm-up.
- `model-router.py readiness --json --auto-certify` returns `status=PASS`, `failed_checks=[]`.
- Default routed task returns HTTP 200 with `hostRouterUsed=true`, `routerReadiness.status=PASS`, and producer/reviewer both execute or fail closed according to contract.
