---
name: meituan-travel
description: Use when a personal travel, local-food, hotel, attraction, ticket, or same-day activity-card workflow needs fresh Meituan evidence through a configured personal channel. Provides a macOS Keychain-backed, on-demand provider adapter; never books, logs in, pays, or treats provider output as official route or safety proof.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms:
- macos
metadata:
  hermes:
    tags:
    - meituan
    - travel
    - local-food
    - hotels
    - attractions
    - keychain
    related_skills:
    - travel-planning
    - apple
---

# Meituan Travel and Local-Life Adapter

## Scope and Abstraction Boundary

Scope: user-local, personal travel and local-life evidence workflows on macOS.

Applicability: use only when the user has configured a personal Meituan Travel credential and the request needs restaurant, hotel, attraction, ticket, or activity candidate evidence.

Anti-conditions: do not use for merchant operations, delivery dispatch, bookings, orders, login, payment, official road/weather/safety decisions, or any workflow lacking user authority to query the configured personal channel.

Falsifier: if the provider package, channel contract, Keychain identifier, or supported query surface changes, readiness and smoke tests must pass before this procedure remains valid.

This is a reusable domain procedure. Trip-specific routes, dates, coordinates, bookings, and candidate results belong in trip state or project evidence, never in this skill.

## Overview

Use the configured Meituan Travel channel as one evidence adapter for food, hotel, attraction, ticket, and activity-card workflows. The adapter is durable but not a daemon: the credential lives in macOS Keychain, the package is pinned locally, and each query launches a short-lived process.

Canonical command:

```bash
python3 ~/.hermes/scripts/meituan_travel_keychain_query.py
```

Managed runtime:

```text
~/.hermes/modules/meituan-travel/node_modules/.bin/ht-ai
@meituan-travel/ht-ai@0.0.6
channel=meituan-developer
Keychain service=hermes.meituan.ht-ai
```

## When to Use

Load this skill when:

- the user explicitly asks to use Meituan or an existing Meituan Token;
- recommending concrete nearby restaurants, local food, hotels, attractions, tickets, or travel activities;
- a same-day or scheduled travel card needs fresh Meituan candidate evidence;
- a new workflow needs to add Meituan as one evidence source;
- diagnosing whether the configured Meituan channel is available.

Do not load it for generic cooking advice, restaurant copywriting, merchant-side operations, payments, bookings, account login, order management, delivery dispatch, or official road/weather/safety verification.

## Readiness Gate

Always probe readiness before a query:

```bash
python3 ~/.hermes/scripts/meituan_travel_keychain_query.py --check
```

Interpret the JSON without exposing secrets:

- `ok=true`, `credential_present=true`, `managed_binary_present=true`: ready.
- `credential_present=false`: report `credential_missing`; do not ask the user to paste a Token into chat.
- missing managed binary with an available `npx` fallback: usable but degraded; repair the managed package before claiming durable readiness.
- no managed binary and no `npx`: `adapter_unavailable`.

`--check` performs no provider query.

## Query Contract

Use one concrete, merged query instead of many small calls:

```bash
python3 ~/.hermes/scripts/meituan_travel_keychain_query.py \
  --query '<specific request with date/time, location, party size, route, constraints, and required fields>' \
  --city '<city>' \
  --origin-query '<short provenance label>'
```

For nearby food, include:

- the latest user-confirmed coordinates or named location and its timestamp;
- local time, party size, meal window, dietary preferences, and whether food or route efficiency has priority;
- exact branch, address, opening hours, price, rating/review count, parking, recommended dishes, distance/route fit, and provider link;
- a prohibition on booking and on inventing unavailable fields.

For hotels/attractions/tickets, include stay or visit date, people count, city/route, known booking constraints, cancellation or entry-window needs, and the exact fields required for comparison.

## Evidence Rules

Provider output is candidate evidence, not universal truth.

Every response or workflow artifact must label one of:

- `Meituan fresh`: this invocation succeeded and produced current provider output;
- `credential_missing`;
- `provider_query_failed` or `provider_query_timeout`;
- `stale itinerary only`: only prior saved results were available.

Never label an old itinerary link or remembered result as fresh. Verify material claims with the appropriate source:

- POI identity, exact branch, route, distance, entrance, and parking: native map readback;
- official opening/closure and ticket rules: official venue/source;
- road, weather, and safety gates: maps, weather, government, or operator evidence;
- real inventory, queue, or app-only fields: provider output or one targeted user screenshot when unavoidable.

If the provider omits links, say so and give a clearly labeled native-map search handoff; do not claim that a search URI is a verified route.

## Location and Privacy Boundary

- A user-shared pin is a point-in-time location, not continuous tracking.
- Reuse the newest pin only when the active context makes its timestamp and relevance clear.
- If the pin may be stale enough to change nearby results, request one fresh pin or named landmark.
- Never expose, log, persist, or return the Token.
- Never place the Token in prompts, cron JSON, shell arguments, skills, trip state, or evidence files.
- The adapter reads the Keychain secret and injects it only into the child process environment.

## Scheduled and New Workflow Integration

To make a new workflow call Meituan:

1. Attach `meituan-travel` to the workflow's ordered `skills` list, after the domain skill such as `travel-planning`.
2. Ensure the job/agent has `terminal` available.
3. In the workflow prompt, explicitly state which request classes trigger the readiness check and query.
4. Cap routine scheduled cards at one merged query unless the user explicitly requests deeper follow-up.
5. Require the evidence-state label in output.
6. Keep booking, login, payment, messaging, and destructive actions closed.
7. Run a redacted `--check`, then one scoped provider smoke query, and read back the generated artifact before claiming integration.

Example workflow fragment:

```text
skills: [travel-planning, meituan-travel]
enabled_toolsets: [file, terminal, web]
```

Example prompt fragment:

```text
When food, hotel, attraction, ticket, or activity candidates are material, load the
Meituan adapter, run --check, then make at most one merged query. Label the result
Meituan fresh / credential_missing / provider_query_failed / stale itinerary only.
```

## Failure Handling

- `credential_missing`: continue with maps/official evidence and tell the user how to restore the Keychain item without requesting the secret.
- `adapter_unavailable`: repair the pinned local runtime; do not silently depend on an unpinned latest package.
- `provider_query_timeout`: retry once only when the request is still timely; otherwise continue with degraded evidence.
- successful but incomplete output: make one focused follow-up if the missing fields materially change the decision.
- successful output with suspicious or inconsistent details: mark the fields unverified and cross-check rather than laundering them into facts.

## Common Pitfalls

1. Treating the module as a resident daemon. It is an on-demand capability with persistent credentials and runtime files.
2. Assuming skill presence alone forces invocation. New workflows must attach the skill and define the trigger in their prompt.
3. Calling the provider before resolving time and location.
4. Ranking by distance after the user says food quality is the priority.
5. Repeating provider-generated dishes or hours as verified when the output is internally inconsistent.
6. Asking the user to resend a Token that is already in Keychain.
7. Using provider data as proof of road safety, official closure, or booking completion.

## Definition of Done

- [ ] **Outcome:** the workflow can run a fresh provider query through the managed adapter and label its evidence state.
- [ ] **Process:** readiness, scoped query, source cross-check, and redacted readback occur in that order.
- [ ] **Style:** results distinguish provider claims from map/official proof and do not overstate freshness.
- [ ] **Efficiency:** routine workflows use one merged query and at most one material follow-up.
- [ ] **Safety:** no Token disclosure, booking, login, payment, or unauthorized external action occurs.

## Verification Checklist

- [ ] `--check` returns `ok=true`, `credential_present=true`, and `managed_binary_present=true`.
- [ ] The managed binary resolves under `~/.hermes/modules/meituan-travel/node_modules/.bin/ht-ai`.
- [ ] The package lock pins `@meituan-travel/ht-ai` to `0.0.6` with registry integrity.
- [ ] A scoped smoke query exits 0 without a Token marker in stdout/stderr.
- [ ] The workflow attaches `meituan-travel` and has terminal access.
- [ ] Output carries an explicit evidence-state label.
- [ ] No booking, login, payment, external message, or secret disclosure occurred.
