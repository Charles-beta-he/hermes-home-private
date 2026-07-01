# Product Hunt external-link audit pattern

Use this reference when auditing Product Hunt (PH) products for GitHub/source links, open-source evidence, or taskpool intake eligibility.

## Applicability

- PH daily/product discovery flows where the question is whether a product has a GitHub/source-code link.
- Cases where the user expects the evidence to come from the product page's visible buttons/links, not from free-text guessing.
- Automated report or taskpool intake flows that must fail closed before creating product-absorption tasks.

## Anti-conditions

- Do not use this as proof that a product is open source unless a normalized repo URL and repo metadata/readback are verified.
- Do not treat PH feed text, tagline, product category, or AI/dev-tool relevance as repository evidence.
- Do not make Cloudflare bypassing a mandatory path for routine reports; classify the block and require supplemental repo evidence.
- Do not store session-specific product names or transient PH redirect IDs in the root skill.

## Evidence-source order

1. Product Hunt official API `productLinks { type url }` when available. Treat this as the stable API representation of the product page's visible buttons/links (Website, Github, Twitter, Source, etc.).
2. Browser/product-page DOM buttons only as corroborating evidence when accessible; if the page is blocked by Cloudflare, record the limitation instead of forcing a bypass.
3. Bounded redirect resolution for PH `/r/...` links.
4. Landing-page scan for explicit GitHub URLs only when a PH button redirects to a non-GitHub landing page.
5. GitHub API or equivalent repo readback for metadata verification.

## Required classification states

- `github_repo_verified`: normalized GitHub repo URL and metadata/readback verified.
- `github_repo_url_resolved_metadata_blocked`: repo URL resolved, but GitHub metadata/readback was blocked or rate-limited.
- `ph_redirect_cloudflare_blocked`: PH `/r/...` redirect could not be resolved because PH/Cloudflare blocked the request.
- `github_link_detected_redirect_to_landing`: PH button reached a landing page but bounded scan found no repo URL.
- `github_link_detected_unresolved`: PH button/source evidence exists, but bounded resolution did not produce a normalized repo.
- `possible_open_source_unverified`: text mentions GitHub/open source but no button/repo readback verifies it.
- `unknown`: no repo/source evidence found.

## Intake gate

Only `github_repo_verified` should proceed to product-absorption or implementation-design intake, and even then only after a Hermes-specific mapping/risk check. All unresolved or blocked states should produce resolver/backfill work or a report note, not a product-absorption task.

## Reporting checklist

- State whether the source was `official_api productLinks`, browser DOM buttons, feed fallback, or text-only.
- Include `state_counts` and decision counts in the report summary when processing multiple products.
- For each product row, show both `open_source_status` and `taskpool_ingest_judgement`.
- Add an audit table for GitHub/source button hits: product, state, intake decision, evidence/limitation.
- When browser DOM is blocked by Cloudflare, explicitly say the API `productLinks` field is being used as the button-link equivalent and that DOM proof was unavailable.
