# React Architecture Migration Pattern

Extracted from `/Users/charles/.hermes/skills/software-development/react-architecture-migration/SKILL.md` on 2026-07-01T08:52:42.874486+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Architecture Pattern

```
src/
├── lib/
│   ├── api.ts           # Axios client + auth interceptor + 401 redirect
│   ├── haptics.ts       # navigator.vibrate patterns
│   ├── sentry.ts        # Sentry init + captureError + setUser
│   ├── vitals.ts        # Core Web Vitals (LCP/FID/CLS/FCP/TTFB)
│   └── analytics.ts     # Event tracking (batched, sendBeacon)
├── services/            # One per domain, all use shared api client
│   ├── auth.service.ts  # sendCode, verify, setupPin, getProfile, logout
│   ├── wallet.service.ts # getWallets, getTotal, getFxRates
│   ├── transaction.service.ts # list, get, getRecent
│   ├── card.service.ts  # getInfo, getCvv, freeze, topup, withdraw
│   ├── wealth.service.ts # getProducts, getHoldings, purchase, redeem
│   ├── exchange.service.ts # getQuote, execute, getHistory
│   ├── remit.service.ts # getPayees, addPayee, preview, execute, timeline
│   ├── payout.service.ts # payoutUsdt, payoutCny, getNetworks
│   ├── topup.service.ts # getSwiftDetails, submitSwift, getUsdtAddress
│   ├── notification.service.ts # list, markRead, markAllRead
│   └── index.ts
├── stores/              # Zustand with loading/error states
│   ├── auth.store.ts
│   ├── wallet.store.ts
│   ├── transaction.store.ts
│   ├── card.store.ts
│   ├── wealth.store.ts
│   ├── notification.store.ts
│   ├── theme.store.ts   # localStorage + data-theme + system detection
│   └── index.ts
├── hooks/
│   ├── useAppBootstrap.ts # Global data init (call in App.tsx ShellLayout)
│   ├── useSwipeBack.ts  # Edge swipe gesture → navigate(-1)
│   └── index.ts
├── i18n/
│   ├── index.ts         # i18next + LanguageDetector + ReactI18next
│   ├── zh.json          # Chinese translations
│   └── en.json          # English translations
├── components/
│   ├── ErrorBoundary.tsx # Class component, retry + go home
│   ├── ScreenSkeleton.tsx # Suspense fallback for lazy routes
│   ├── RouteTransition.tsx # Page transition (forward/back detection)
│   └── ui/
│       ├── SkeletonScreen.tsx # HomeSkeleton, TxListSkeleton, CardSkeleton
│       └── PullToRefresh.tsx  # Touch-based pull-to-refresh wrapper
└── screens/             # All lazy-loaded via React.lazy()

mock-server/
├── server.js            # Express, all endpoints, in-memory mutable state
├── data/mock.js         # Centralized mock data
└── package.json
```
