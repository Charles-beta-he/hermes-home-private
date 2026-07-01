# Mobile Offline Travel Copilot / TripState Productization

Extracted from `/Users/charles/.hermes/skills/personal-productivity/travel-planning/SKILL.md` on 2026-07-01T08:52:42.874486+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Mobile offline travel copilot / TripState productization

When travel planning is being productized into a mobile offline assistant, treat it as a local TripState + evidence-gated handoff workflow rather than a generic chatbot. The normal UX should not require the user to repeatedly send location: with permission, the phone derives local/coarse location context, keeps raw coordinates local by default, and sends only minimal summaries to the online agent when current facts/tools are needed.

Key rules:

1. Default location permission should be **while using app**. Background location is an explicit, time-boxed Trip Mode only, with visible pause/expiry and low-frequency use.
2. Use selected-photo/screenshot OCR for booking, ticket, Dianping/Meituan/Xiaohongshu/Douyin/Gaode/Baidu/Ctrip/12306 evidence; do not assume all-library photo access.
3. Maintain TripState labels: confirmed, inferred, user-stated, screenshot-derived, stale, unknown. Never promote a candidate hotel/POI to a booked/visited anchor without explicit proof or user confirmation.
4. Offline mode may answer only from local evidence, or draft/queue a handoff. It must refuse realtime/current facts and external actions rather than pretending to check or execute them.
5. Live responses should be short operational cards: current confirmation, one map-ready next action, gate check, fallback, do-not-do list, and only the single most valuable missing screenshot/location if needed.
6. For live-phase inference, default to **current conversation time + the TripState plan**; explicit user-provided current location/departure time/body state overrides the plan. If the inference may conflict with reality in a way that affects safety, lodging, tickets, car return, or flights, ask only the minimum necessary question.
7. Treat “can we add a stop?” as a gate decision, not a preference. Return-day and transfer-day sightseeing may be allowed only when it is nearby, reversible, has a hard leave time, and does not consume fuel/return/flight buffers.
8. Keep landing zones strict: trip-specific facts and temporary live state go to TripState/session, reusable procedures to this skill/reference, stable user preferences to memory, and concrete engineering gaps to task/proposal tracking. Do not add memory entries for trip-local gates.

For the mobile/PWA/RN implementation pattern, see `mobile-frontend-delivery` reference `references/mobile-offline-avatar-travel-vertical.md`. For a session-derived checklist of TripState-gated travel-copilot completeness, see `references/tripstate-gated-travel-copilot-2026-06.md`.

When a user asks to review or完善 an existing scenic self-drive TripState with confirmed flight/hotel/rental anchors, run a static execution-review supplement: recover the scoped SSOT, preserve anchors, add a P0 gap table, patch D0-Dn execution principles, T-7/T-2/Day-of checklists, evidence-promotion rules, and verification assertions without claiming live ticket/road/weather facts. See `references/scenic-self-drive-tripstate-review-supplement.md`.

When a social video/post introduces a new road-access constraint such as预约通行、分时入口、施工夜闭、车型限制, treat it as a TripState gate signal: extract the claim, seek official readback, add a scoped evidence item, fail closed until the official record/screenshot exists, and test that the gate is high-risk/advisory rather than automatically certified. See `references/social-video-to-road-reservation-gate.md`.

When a webpage-cleaning tool such as Webclaw/browser readability is used for travel evidence, treat it as an evidence preprocessor only: local/public extraction success can create a source-attributed advisory fact, but it must not become reservation, ticket, road-open, or pass/fail authority. Promote only after a domain adapter plus official/user readback evidence.

When a confirmed trip has future reservation/ticket/road gates but the booking window has not arrived, create a T-7 official-entry precheck pack instead of trying to book early or leaving a vague reminder. The pack should list official channels to open, exact screenshots needed, naming conventions, decision mapping, and a `prepared_not_certified` TripState event. See `references/t7-official-entry-precheck-pack.md`.
