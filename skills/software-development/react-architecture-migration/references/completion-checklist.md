# React Migration Completion Checklist

Extracted from `/Users/charles/.hermes/skills/software-development/react-architecture-migration/SKILL.md` on 2026-07-01T08:53:45.426287+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Completion Checklist

- [ ] Infrastructure: 23/23 (api, stores×7, services×10, theme, error boundary, skeleton, route transition, pull-to-refresh, haptics, sentry, vitals, analytics, i18n, PWA, vitest, mock server, validators, pinGuard, pinVerify, exportUtils, featureFlags, retry)
- [ ] Code splitting: 55/55 lazy imports in App.tsx
- [ ] ErrorBoundary + Suspense wrapping all routes
- [ ] ProtectedRoute guarding all non-auth routes
- [ ] useSessionTimeout in App.tsx ShellLayout
- [ ] i18n: 55/55 screens use useTranslation, escapeValue: true
- [ ] Dark mode: 15+ components with dark: variants + theme store
- [ ] Loading states on data-fetching screens
- [ ] PullToRefresh on data screens
- [ ] Zustand persist + devtools on all 7 stores
- [ ] Token refresh with request queuing in api.ts
- [ ] PIN guard (5 attempts/10min) on all PIN screens
- [ ] No hardcoded PINs (use pinVerify.ts)
- [ ] Exchange real countdown timer (not hardcoded string)
- [ ] Payout screens call payoutService (not sessionStore)
- [ ] Transaction CSV export
- [ ] Debounce on financial CTAs
- [ ] OfflineBanner + useOnlineStatus
- [ ] Feature flags system
- [ ] Retry logic (exponential backoff)
- [ ] PWA update notification (registerType: 'prompt' + UpdateBanner with countdown)
- [ ] Manual version check wired to MeScreen
- [ ] Dynamic version display (src/lib/version.ts)
- [ ] Tests: vitest + Playwright E2E
- [ ] TypeScript: 0 errors
- [ ] Mock server: all endpoints matching services
