# Mobile Offline Avatar with Travel Vertical

Scope: class-level pattern for a mobile/PWA/RN assistant companion where a travel copilot is the first production vertical. Applicability: mobile offline assistant, PWA/RN/Capacitor shell, local evidence assistant, TripState, selected-photo OCR, map deep links, and cloud handoff. Anti-conditions: do not use this to justify offline tool execution, permanent background tracking, raw trajectory upload, or project-specific repo/path decisions.

## Product model

Treat the mobile offline avatar as the edge runtime of an online agent, not a separate personality. Travel is a high-value vertical and acceptance harness because it exercises location, screenshots/OCR, maps, time gates, offline/weak network, privacy, and handoff in one scenario.

When the initial travel vertical starts accumulating shared platform capabilities, promote the framing to a mobile platform without renaming stable project IDs casually:

```text
Mobile Platform Core
  -> shared entry/readiness contract
  -> shared offline/evidence core
  -> Gateway projection/sync boundary
  -> RN/PWA/native shells
  -> vertical registry: travel first, future verticals gated
```

Travel should then be `first_vertical=travel`, not the whole product boundary. Future verticals (portfolio dashboard, persona/wake/voice, work-project companion) must be explicit plugins with their own authority gates. Work/client companion verticals are disabled by default and require an explicit user project switch before use.

Recommended split:

- Mobile owns local projection, TripState, selected screenshots/OCR, local evidence answers, drafts, vertical-local state, and handoff queue.
- Gateway owns device registration, sync cursors, bootstrap/changes, no-store handoff, revoke/wipe, and reconciliation status.
- Online agent owns canonical facts, current information, tools, side effects, memory/task truth, and audit.
- A platform `verticalRegistry` or equivalent owns vertical metadata only; it must not become another fact source.

## Permission UX defaults

Do not make “send me your location” the normal path. Prefer permission-scoped local context:

1. Location: default to “while using app”; cloud receives coarse location summaries by default.
2. Background location: off by default; only an explicit active Trip Mode may enable low-frequency, time-boxed sensing with a visible pause/expiry state.
3. Photos: selected-photo picker for orders, tickets, local-app screenshots, and map evidence; avoid all-library scans.
4. Microphone: optional for voice queries/notes.
5. Notifications: trip gates such as last entry, return car, flight, hotel, weather/fatigue reminders.
6. Calendar/reminders: optional; contacts are not required for the travel vertical.

## Data and safety contracts

- `ContextCard` / `EvidenceSpan`: synced online context and extracted screenshot evidence.
- `TripState`: current phase, coarse location band, confirmed anchors, inferred plan, open unknowns, hard gates, risk flags, completed/cancelled POIs.
- `OfflineAnswer`: answer/cautious/refusal/draft-only plus evidence hits and sync status.
- `HandoffPacket`: user query, local decision, evidence ids, minimal TripState/location summary, requested action class, confirmation state.

Offline rules:

- Realtime/current facts: refuse offline and queue handoff.
- External actions: draft-only offline; never auto-execute on reconnect without authority/confirmation.
- High-risk requests: refuse or require online safety checks.
- Local model output is a wording/rerank adapter only; accept it only when cited ids are non-empty and a subset of retrieved evidence.
- Candidate hotel/POI evidence must not become a confirmed booking/visited fact without explicit proof or user confirmation.

## Travel live-copilot response shape

For live travel, return a short operational card instead of a long guide:

```text
Current confirmation: ...
Go now: <map deep link + text fallback>
Gate: ticket / reservation / last entry / open status / parking / weather / sunset
Fallback: ...
Do not do: ...
One missing proof: <ask only if it changes the decision>
```

For mainland China travel, prefer Gaode/Baidu deep links and local-app evidence from Dianping/Meituan/Xiaohongshu/Douyin/Gaode/Baidu/Ctrip/12306 screenshots over broad web sources. If direct platform access is blocked, ask for screenshot/OCR rather than fabricating rankings.

## Implementation order

1. Build a pure shared offline core first: retrieval, intent gate, TripState reducer, local model citation gate, handoff queue.
2. Add Pocket/Mobile Gateway dry-run: device pairing, bootstrap/changes, handoff/result, revoke/wipe, no-store headers.
3. Add a platform entry/readiness contract for RN/PWA/operator surfaces; expose metadata only, not facts.
4. Add a vertical registry with tests:
   - `travel` is the only default-enabled validated local vertical at first.
   - `portfolio-dashboard` and other expansions start as candidates.
   - `persona/wake/voice` is gated for microphone/wake/external-send authority.
   - work-project companion verticals are disabled unless the user explicitly switches to that work project.
   - every vertical forbids canonical fact writes and external side effects without handoff.
5. Package as PWA/RN/Capacitor without forking the offline core.
6. Add travel fixtures: hotel proof vs candidate, POI already visited, food decision, ticket/last-entry unknown, return/airport phase.
7. Harden privacy/security/release before beta: encryption, redaction, telemetry, wipe, rollback, UI/interaction tests.

## React Native/Jest mapping pitfall

If the RN native Jest config maps a workspace package directly to TypeScript source (for example `@hermes-pocket/offline-core -> packages/offline-core/src/index.ts`), every `.js`-suffixed internal export from that source needs a corresponding `moduleNameMapper` entry. Adding a new shared-core file and exporting `./newModule.js` can pass workspace Vitest/TypeScript build but fail RN Jest with `Cannot find module './newModule.js'`. Patch the native Jest resolver when adding shared-core exports, then run native Jest and full production verification.

## Verification checklist

- Offline core tests cover answer/cautious/refusal/draft-only and local model citation rejection.
- Realtime and external-action queries never return fake offline execution.
- TripState labels confirmed/inferred/unknown and blocks candidate-to-booked promotion without proof.
- Gateway responses are `Cache-Control: no-store` and revoke returns wipe.
- Mobile UI truthfully shows Local/Hybrid/Online and queue/reconciliation state.
- Travel card includes a map link, gate check, fallback, and do-not-do when relevant.
- Platform vertical registry tests prove only safe/default verticals are enabled, work-project companions require explicit switch, and all verticals forbid canonical fact writes.
- RN native Jest, workspace tests/build, production gate, rollback proof, and dependency audit pass before calling the platform slice production-ready locally.
