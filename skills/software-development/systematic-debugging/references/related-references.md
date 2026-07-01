# Systematic Debugging Related References

Extracted from `/Users/charles/.hermes/skills/software-development/systematic-debugging/SKILL.md` on 2026-07-01T08:52:42.874486+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Related references

- `references/pwa-service-worker-first-load-performance.md` — debugging and verification path for weak-network first-screen slowness involving `/registerSW.js`, `/sw.js`, Workbox/VitePWA precache size, and SW registration timing; includes the wrong-repo pitfall and the anti-pattern of using a fixed delay as the primary fix.
- `references/frontend-release-auth-iceberg.md` — generic checklist for browser apps where app-wide runtime hooks interact with public routes, static version manifests, auth telemetry, and post-auth verification locks; anti-condition: use only for frontend/auth/release-runtime flows, not as a project fact store.
- `references/frontend-auth-contract-stale-client-cache.md` — debugging auth/session/OTP/PIN contract changes where current source or served bundles are fixed but a browser/PWA client still sends the old request shape; separates missing body params from missing pending-token headers, deployed artifact proof, SW/update posture, and stale-client remediation.
- `references/frontend-pwa-service-worker-precache.md` — diagnosing weak-network first-screen slowness where `/registerSW.js`, `/sw.js`, Workbox precache, or VitePWA registration competes with initial rendering; key pitfall: fixed 3–5s SW registration delays move the contention instead of removing broad precache payloads.
- `references/text-assertion-mismatch.md` — diagnosing and fixing `assert "X" in CONSTANT` failures (substring, singular/plural, synonym patterns)
- `references/large-merge-regression-debugging.md` — post-merge debugging patterns for large upstream upgrades: duplicate async calls plus non-reentrant locks, service preflight seams, stale monkeypatch paths, nested async tests, reconnect/send-path degradation invariants, and focused verification steps.
- `references/provider-proxy-relay-debugging.md` — diagnosing provider endpoint timeouts across raw API, CLI wrapper, DNS, proxy/TUN fake-ip, health-breaker, and remote relay boundaries.
- `references/provider-runtime-availability-vs-auth.md` — diagnosing multi-provider routers when auth/OAuth probes pass but exact provider/model runtime calls fail; covers runtime-unavailable snapshots, fail-closed candidate filtering, and diversity warm-up verification.
- `references/provider-catalog-vs-runtime-entitlement.md` — diagnosing mismatches where an approval email, public catalog, models.dev, or cached picker lists a model but the exact active key/base URL tuple does not expose it at `/v1/models` or runtime calls.
- `references/react-aria-role-migration.md` — cascading test selector failures when swapping interactive components (Link→Button, a→button); role grep checklist
- `references/pytest-override-flags.md` — clearing xdist `addopts` from pyproject.toml when running serially (`-o "addopts="`)
- `references/runtime-overlay-sensitive-test-fix.md` — fix pattern for tests that depend on runtime overlay/OAuth/provider discovery and need deterministic seeding
- `references/spa-global-runtime-public-auth-401.md` — debugging path for SPA root-level runtime hooks that call protected endpoints on public unauthenticated auth routes, producing repeated 401s and auth-refresh noise
- `references/frontend-auth-state-machine-routing.md` — Applicability: SPA auth/onboarding route regressions with a pending-login state and formal authenticated shell gates. Anti-condition: do not use when product requirements explicitly require global setup gates to preempt local setup flow.
- `references/auth-step-up-token-exchange.md` — debugging checklist for pending-token → second-factor/PIN → formal-token exchange flows; includes FE/BE contract checks, setup-vs-verify routing, duplicate-verification pitfalls, and targeted test boundaries.
