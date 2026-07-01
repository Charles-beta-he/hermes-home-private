# Product Hunt page-button fallback test pattern

Use this when a daily report or PH enrichment script marks Product Hunt GitHub/source links as blocked/unresolved, especially `ph_redirect_cloudflare_blocked`, `github_link_detected_unresolved`, or `needs_supplemental_repo_link`.

## Why this exists

Product Hunt official API may expose a `productLinks { type: "Github" | "Source" | ... url: "https://www.producthunt.com/r/..." }` link, but direct terminal or headless-browser reads of `/r/...` can return Cloudflare `403` before the real destination is revealed. A user-observed workaround is to open the PH product page and use the visible product/source/GitHub button rather than fetching `/r/...` directly.

## Durable procedure

1. Parse candidate products from the report and/or PH script JSON.
2. Re-query Product Hunt official API for both:
   - the local report date as UTC, and
   - `report_date - 1` as UTC.
   PH `createdAt` is UTC while local reports may be Asia/Shanghai, so the products in a local-date report often belong to the previous UTC day.
3. For each `productLinks` item whose type or URL suggests GitHub/source/GitLab:
   - try bounded direct `/r/...` redirect resolution;
   - if it returns `403`, `429`, `Cf-Mitigated: challenge`, or Cloudflare HTML, classify as `ph_redirect_cloudflare_blocked` and continue to the product-page fallback;
   - open the canonical PH product page from API/feed;
   - inspect/click visible `Visit`, `Website`, `GitHub`, `Source Code`, or outbound buttons;
   - read back the resulting URL.
4. If the button lands on `github.com/<owner>/<repo>`, normalize and enrich via GitHub API.
5. If the button lands on a product website/GitHub Pages, do one bounded HTML/text scan for canonical GitHub repo links.
6. If both direct redirect and product-page button fallback are blocked by Cloudflare or reveal no repo, stay fail-closed:
   - `open_source_status = ph_redirect_cloudflare_blocked` or a more precise blocked state;
   - `taskpool_ingest_judgement = needs_supplemental_repo_link` / `not_poolable_needs_repo_link`.

## Verification checklist

- [ ] Report path and PH script/API JSON artifact are recorded.
- [ ] Date-window drift was handled by querying both local report date and date-minus-one UTC.
- [ ] Direct `/r/...` result captures status, final URL, and Cloudflare markers (`Cf-Mitigated`, Cloudflare HTML, challenge page title).
- [ ] Product page fallback records whether visible buttons were exposed; do not claim the button path worked if the page itself was Cloudflare-challenged.
- [ ] Any GitHub repo claim includes normalized `owner/repo` and either metadata readback or a precise `metadata_blocked` state.
- [ ] Taskpool candidates remain fail-closed unless repo evidence and Hermes capability mapping are both present.

## Anti-conditions

- Do not ask the user to solve a CAPTCHA just to make an automated daily report succeed.
- Do not treat PH `type: Github` alone as verified open source.
- Do not hard-code that Product Hunt pages are always blocked; the product-page button fallback is valid when a browser/session can see the page.
- Do not store one day’s product names as durable knowledge; use them only as test fixtures or evidence artifacts.
