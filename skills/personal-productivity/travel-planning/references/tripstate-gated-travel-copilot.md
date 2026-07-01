# TripState-gated travel copilot pattern

Applicability: use for active or near-active trips where the user provides booking screenshots, hotel chains, flights, car rentals, live route questions, or asks for a travel-agent/copilot experience rather than a static itinerary. Especially applies to domestic self-drive trips with hard anchors such as hotels, flights, car return, scenic-road gates, and weather/road uncertainty.

Anti-conditions:
- Do not use this to store one trip's hotel names, order IDs, prices, transient location, or task progress as global skill facts.
- Do not present dynamic facts (weather after forecast horizon, road opening, ticket availability, live traffic) as verified unless rechecked from an appropriate current source.
- Do not write trip-specific inference rules to long-term memory; keep them in the scoped TripState or reference artifact.

## Core model

A travel copilot should operate from a scoped TripState rather than from chat memory alone.

TripState fields should distinguish:

- `confirmed`: booking screenshots, user confirmations, flight/car/hotel order facts.
- `inferred`: route topology, likely current phase, plan-derived times.
- `unknown`: insurance, rescue, ticket rules, parking, last-entry, road status.
- `stale`: old weather, old opening rules, outdated platform snippets.
- `dynamic`: day-of weather, traffic, current location, body state, road control.
- `gates`: pass/warn/fail/blocked decision rules.

## Landing-zone rules

- Order screenshots and explicit confirmations become scoped TripState anchors, not general recommendations.
- Stable reusable procedure belongs in this skill or a reference file.
- Trip-specific hotel names, route dates, order IDs, exact prices, and temporary decisions belong in TripState/project artifacts only.
- User style/workflow corrections that affect the class of travel copilot behavior belong in this skill.
- Real-time location, actual departure time, fatigue, and day-of weather are transient; do not save them durably.

## Gate-first live decisions

When the user asks a live question such as “还能去吗 / 今天怎么走 / 能不能加一个点”, default to this sequence:

1. Read the current conversation time.
2. Read the scoped TripState: current day, current/tonight hotel, next hard constraints, flight/car return, planned route, prior confirmations.
3. Use explicit user-provided live facts (current location, actual departure time, body state) to override plan inference.
4. If plan inference and likely reality conflict in a way that affects safety, lodging, car return, flight, or entry gates, ask only the smallest necessary question.
5. Run gates in order: safety → hard time → road/weather → ticket/booking → body state → experience value → optional add-on.
6. Return one main action plus one fallback, not a broad option list.

Key correction: “default infer from current conversation time + plan unless explicitly overridden” is a **TripState gate**, not a global memory preference.

## Order absorption workflow

For booking screenshots:

1. OCR and extract structured facts.
2. Classify each fact as confirmed/inferred/unknown.
3. Patch the affected days, not the whole itinerary blindly.
4. Explain the consequence: e.g. late flight changes D0/D1, car return changes D9, one villa room for four resolves room-count uncertainty.
5. Remove resolved unknowns from the checklist.

## 30-second copilot card

For same-day or on-road use, output:

```text
结论：可以 / 不建议 / 必须降级。
当前推断：按当前时间+TripState，你应在 X→Y；硬约束是 A/B/C。
下一步：导航/行动到 X。
最晚：HH:MM 必须离开/到达。
门禁：时间/天气/道路/票务/体力。
失败分支：如果 gate fail，改走 Z。
不要做：1-3条。
```

## Return-day rule

A return day is not automatically “no sightseeing.” It is a hard-constraint day:

- Allow nearby, low-risk, short, reversible stops with explicit hard-leave times.
- Reject or warn on distant, ticketed, queue-prone, or route-uncertain additions.
- Reverse-plan from flight/car-return/fuel/security/check-in deadlines.
- Treat platform return time as a hard outer bound; define a safer operational target when needed.

## Verification checklist

Before claiming the travel copilot workflow is complete for a trip, verify there is a scoped artifact or equivalent state covering:

- [ ] Flights, hotels, car/rental anchors.
- [ ] D0-DN daily gate cards.
- [ ] T-7 / T-2 / day-of checklists.
- [ ] Evidence ledger separating screenshot/user-confirmed/dynamic facts.
- [ ] Live copilot response template.
- [ ] Memory-write gate: trip facts stay scoped; reusable procedure goes to skill; stable user preference goes to memory.
- [ ] Dynamic facts are explicitly left for recheck rather than fabricated early.
