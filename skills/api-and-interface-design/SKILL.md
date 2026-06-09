---
name: api-and-interface-design
description: Use when you need guidance on design principles for REST, GraphQL, tRPC, and internal APIs.
version: 1.0.0
author: Hermes Agent
license: MIT
triggers:
- design an API
- create endpoint
- add route
- new tRPC router
- GraphQL schema change
- before exposing any new interface to consumers
model: strong (DeepSeek/Claude) — API design mistakes are expensive
metadata:
  hermes:
    tags:
    - api
    - interface
    - design
    related_skills:
    - domain
    - email
    - router
---

# api-and-interface-design

## Overview


Good APIs are consistent, predictable, and self-documenting. Bad APIs multiply maintenance cost linearly with each consumer.

## When to Use

- You need guidance on design principles for REST, GraphQL, tRPC, and internal APIs
- design an API
- create endpoint
- add route
- new tRPC router
- GraphQL schema change
- before exposing any new interface to consumers
- Don't use for: requests that do not need you need guidance on design principles for REST, GraphQL, tRPC, and internal APIs; choose a more specific child skill or a broader routing skill that actually matches the task.
## Universal Principles (all API types)

### Naming
- Resource names: plural nouns (`/users`, not `/getUser`)
- Actions: HTTP methods (GET/POST/PUT/DELETE), not verbs in URL
- Consistent casing: camelCase (JS/TS), snake_case (Python)
- No abbreviations unless universally understood (`id`, not `identifier`)

### Versioning
- URL prefix: `/v1/users` (explicit, no surprise)
- Or header: `Accept: application/vnd.api+json;version=1`
- Never: silent breaking changes without version bump

### Error Handling
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable description",
    "details": [{ "field": "email", "issue": "invalid format" }]
  }
}
```
- Always return structured errors, never raw stack traces
- Use HTTP status codes correctly (400=client, 500=server)
- Never: `{ "error": "something went wrong" }`

### Pagination
- Cursor-based (preferred): `?cursor=xxx&limit=20`
- Offset-based (simpler): `?offset=0&limit=20`
- Always return `hasMore` or `total` so consumers know when to stop

### Performance
- Support field selection: `?fields=id,name,avatar`
- Default limits: never return unlimited results
- Consider rate limiting on expensive endpoints

### Stateful Mutations and Source-of-Truth Contracts
When an endpoint changes persisted state that the client may also cache locally (trust flags, device/session state, feature entitlements, KYC/profile status, wallet/card state):
- Make the server the explicit source of truth. Client-side fallback/cache may fill missing fields for old backends, but must not override an explicit server `false`, revoked state, or authoritative value.
- Validate mutation bodies strictly. Missing/null booleans must be `400 VALIDATION_ERROR`, not silently coerced to `false`.
- Scope updates by owner/authz and active status (`WHERE user_id = :uid AND revoked = 0`), then check affected row count. `0` rows should return `404`/`403`/domain error, not success.
- Return the database/resulting state, not merely the requested value. Future policy may reject or normalize the request.
- Include contract tests for success, validation failure, wrong owner, already-revoked/not-found, unauthenticated access, and read-after-write/list/login consistency.
- When deprecating an old local fallback, add tests that explicit server values win over stale localStorage/session cache.

### Business Semantics vs Presentation Fields
When reviewing prototype/API gaps for UI-facing features (notifications, status cards, badges, CTAs, error/success states), separate contract semantics from presentation before recommending backend changes:
- First split failures into HTTP/API failure, business-flow failure, and notification/display failure. Do not infer business outcome from request success/failure.
- Backend should own business facts: whether an event happened, who receives it, business category/type/subType/status, title/body/bodyText, read state, timestamps, and stable references (`referenceId`, `relatedJournalId`).
- Frontend should own presentation: icons, colors, tone names, CTA labels, route mapping, spacing, and prototype visual variants.
- Do not ask backend to expose `iconKind`, `ctaText`, `cssTone`, or other display-mechanism fields unless the requirement is explicitly CMS/ops-configurable presentation.
- Do not parse localized title/body text to drive logic. If the frontend needs finer variants, use stable business semantic fields (`type`, `subType`, `status`, `eventType`) rather than template wording.
- Do not limit this analysis to prompts that literally mention "prototype states", "implementation coverage", or "missing fields". Apply it whenever the user's expected direction or conversation goal is a long-term stable product/API boundary.
- Treat prototypes as UX/effect specifications, not schema or storage specifications. Extract observable user effects first: visible states, copy intent, read/unread behavior, success/failure/warning perception, CTA behavior, navigation, empty/loading/error states, and acceptance evidence.
- When comparing against a prototype data file, ask whether the goal is to copy the prototype data structure or reproduce the user experience with the new architecture; prefer semantic contracts plus frontend mapping when feasible.
- For each prototype effect, map the implementation carrier explicitly: backend business event/fact, backend content, frontend visual mapping, frontend route/action, or test evidence. Recommend backend changes only for missing business facts/semantic states, not for missing prototype mock fields.
- Optimize for the user's underlying target direction and durable architecture, not the surface wording of the immediate audit question.

## tRPC-Specific (matrimonial project)
- Input validation: zod schema on every procedure
- Output typing: infer from return type, not manual
- Router organization: one router per domain (user.router, match.router)
- Middleware: auth, logging, rate-limit as reusable middlewares

## Anti-patterns
- Endpoint that does too much: `POST /processEverything`
- Inconsistent response shapes: some return `{data}`, others return raw array
- Breaking change without version: changing field type silently
- No pagination on list endpoints
- Secrets or stack traces in error responses
- Stateful mutation returns success without checking affected row count
- Local fallback/cache masks explicit server source-of-truth values

## Verification Checklist
- [ ] Naming consistent across all endpoints
- [ ] All list endpoints have pagination
- [ ] Error responses follow structured format
- [ ] No breaking changes without version bump
- [ ] Input validation on every endpoint
- [ ] Stateful mutations validate input, enforce authz/ownership, check affected rows, and return resulting persisted state
- [ ] Contract tests cover read-after-write and stale-client-cache edge cases

### Authoritative Financial Field Responses
When a mutation endpoint (confirm, execute, transfer, pay) computes derived values like fee, applied rate, net amount, or balance-after, **always return those authoritative values in the response**. Do not assume the client can reverse-calculate them from inputs:
- Display rates may be rounded (e.g., 4dp) while applied rates carry full precision (8dp). Client-side `amountIn × displayRate ≠ amountOut` with any rounding.
- Fee structures may involve tiering, minimums, or channel-specific logic invisible to the client.
- Idempotency return paths must include the same fields as the primary path — clients retry and read the same response shape.
- Frontend mapping code (service layer) should already handle optional fee/rate fields with `!= null` guards so adding backend fields is backward-compatible.

**Checklist for financial mutation endpoints:**
- [ ] Response includes all computed fields: fee/feeCcy, appliedRate, netAmount, balanceAfter
- [ ] Idempotency return path queries and returns the same fields
- [ ] Frontend service layer already maps these fields (grep for `fee`, `rate`, `appliedRate` in service files)
- [ ] No client-side reverse-calculation of fee or rate from rounded display values
- [ ] Wrapper safety: any side effect is followed by target-state read-back before reporting completion.
## Common Pitfalls

1. Loading this skill outside its trigger class and skipping a simpler, more direct path.
2. Ignoring prerequisites such as platform, credentials, installed commands, or linked reference files.
3. Treating the skill as a static memo instead of verifying the exact commands, artifacts, or outputs in the current environment.
4. Financial mutation endpoints returning only txId/status without fee/rate/amountOut — forces client reverse-calculation with precision loss (UVISA exchange confirm case, 2026-05-30).

