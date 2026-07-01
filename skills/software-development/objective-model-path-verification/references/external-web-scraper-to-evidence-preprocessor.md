# External Web Scraper to Evidence Preprocessor Bridge

## Scope and applicability

Applicability: use when a user asks whether an external web-scraping, web-cleaning, or retrieval-ingestion project should be absorbed into a governed evidence workflow.

Anti-conditions: this note does not authorize global tool installation, MCP enablement, direct network crawling, credentialed/login extraction, CAPTCHA or app-gate bypass, proxy rotation, publishing, deployment, or purchase/reservation execution.

Reusable class-level pattern: absorb the preprocessing capability, not the external tool's full authority surface. Treat scraper success as text/provenance extraction only; the domain gate still decides pass, warn, fail, or blocked.

## Landing-zone classifier

- Reusable procedure: local-file evidence preprocessor bridge, fail-closed promotion, advisory dynamic fact projection.
- Project-specific details: concrete repo URL, sample source, itinerary, gate IDs, observed counts, branch names, and paths. Keep those in a project SSOT or scoped project reference, not in the skill body.
- Concrete follow-up work: adapter wiring, CLI packaging, official-source mapping. Track as task/project candidates, not as a new narrow skill.
- Session progress: do not save.

## Safe default architecture

```text
authorized existing read of public or otherwise permitted source
→ save source content locally
→ run external cleaner in local-file mode
→ normalize to a preprocessor result contract
→ convert to a domain evidence fact
→ domain gate remains advisory/warn unless independent official readback or certification exists
```

Do not start with global MCP install or default network fetching unless the user separately authorizes that exact boundary and it has a rollback/readback path.

## Minimum contract

A preprocessor result should include:

- `tool`, `toolVersion` if available
- `sourceUrl`, `finalUrl` if available
- `observedAt`
- `contentHash`
- cleaned text and/or structured JSON
- `extractionStatus`: `ok | empty | blocked | unsupported | error`
- `boundaryFlags`, at least: `qr_app_gate`, `login_required`, `captcha_or_antibot`, `paywall`, `public_preview_only`, `needs_official_readback`, `license_sensitive`
- `doNotUseFor`, explicitly including domain pass/fail decisions when appropriate

## Promotion rules

Fail closed when:

- `extractionStatus !== ok`
- source URL, observation timestamp, or content hash is missing
- boundary flags include login, app gate, CAPTCHA or anti-bot, or paywall
- the output came from a public preview that cannot prove the private/full content

Even when promotion is allowed, default the domain fact to `warn/advisory`, not `pass`, unless a domain adapter and independent evidence prove the specific gate condition.

For high-risk road, ticket, permit, reservation, medical, legal, or safety gates, extraction success must not become certified execution evidence. Keep the claim at the level of "this source text says X" until authoritative readback verifies the actual state.

## Verification checklist

1. Record external project facts and license in a scoped project reference.
2. Test the tool in isolation before integrating it.
3. Prefer local-file mode first; record whether direct network fetch failed closed or passed.
4. Add type/contract tests for normalization.
5. Add fail-closed tests for blocked, app-gated, login, CAPTCHA, and paywall cases.
6. Add a domain-gate test proving extraction success yields advisory/warn, not pass/certified.
7. Run focused tests and the relevant package build.
8. Update the project SSOT or verify script to include the bridge artifacts.

## Pitfalls

- **Extractor-as-authority trap**: clean text is not proof that a high-risk domain gate passed.
- **MCP-first trap**: installing a crawler as MCP expands the agent authority surface before the preprocessing contract is proven.
- **Bypass creep**: cookie files, app gates, CAPTCHA handling, proxies, and login flows change the task from public evidence preprocessing into private or access-controlled extraction; stop for separate authority and legal/safety review.
- **License creep**: copyleft or server-side licensing can be acceptable for isolated local evaluation but may block embedding in a distributed or hosted product without review.
- **Freshness confusion**: old authoritative notices can seed rules but do not certify dynamic current state.
