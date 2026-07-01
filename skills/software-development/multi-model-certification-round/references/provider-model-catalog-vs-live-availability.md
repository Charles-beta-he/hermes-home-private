# Provider model catalog vs live availability

Applicability: use when checking whether a provider/model participant is available for Hermes routing, multi-model certification, fallback chains, or `/model` picker entries.

Anti-conditions:
- Do not convert one account's 400/401/quota result into a global model ban.
- Do not treat a third-party catalog entry as proof of runtime availability.
- Do not persist transient setup failures as durable rules; capture the probe sequence and boundary instead.

## Pattern

1. Resolve the Hermes provider alias first.
   - Example: `mimo` normalizes to `xiaomi`.
2. Compare three catalogs separately:
   - Hermes static/fallback catalog (`_PROVIDER_MODELS` / plugin `fallback_models`).
   - Cached picker catalog (`cached_provider_model_ids` or `provider_models_cache.json`).
   - External registry/catalog such as `models.dev`.
3. Force-refresh external registries when the user asks whether models are newly added.
   - `fetch_models_dev(force_refresh=True)` for models.dev-backed discovery.
4. Distinguish catalog discovery from usable runtime access.
   - Some providers expose no reliable `/v1/models` endpoint or return `None`/401 even with valid keys.
   - A model may appear in `models.dev` but still be rejected by the provider API for the current account/region/plan.
5. Smoke-test each candidate through the exact Hermes provider path that production routing would use.
   - Minimal prompt: `hermes chat --provider <provider> -m <model> -q '只回复: OK' --quiet --max-turns 1 --ignore-rules`
   - Treat `OK` as runtime availability evidence for that account/path.
   - Treat `400 Not supported model ...`, auth, quota, or transport errors as scoped runtime boundaries, not proof the model never exists.
6. Report in three buckets:
   - `listed by Hermes`
   - `new in external catalog`
   - `runtime-smoke available now`

## MiMo/Xiaomi example from 2026-06-27

Observed shape:
- Hermes picker/static listed: `mimo-v2.5-pro`, `mimo-v2.5`, `mimo-v2-pro`, `mimo-v2-omni`, `mimo-v2-flash`.
- models.dev listed an extra `mimo-v2.5-pro-ultraspeed`.
- Live smoke accepted `mimo-v2.5-pro`, `mimo-v2.5`, `mimo-v2-pro`, `mimo-v2-omni`.
- Live smoke rejected `mimo-v2-flash` and `mimo-v2.5-pro-ultraspeed` with `Not supported model ...` for the current API path.

Reusable lesson: when MiMo/Xiaomi is used as a multi-model participant, gate eligibility on live smoke evidence for the exact model slug rather than on catalog presence alone.
