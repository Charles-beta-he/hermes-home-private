# Mobile legal PDF page rendering

Use this when a mobile/PWA legal page (About → User Agreement, Terms, Privacy Policy, disclosures, etc.) must show authoritative PDF content instead of hand-maintained i18n text.

## Trigger

- Lark/product evidence provides legal PDFs or exported PDF page images.
- The task says Chinese simplified/traditional should use Chinese content and other locales should use English content.
- Chat/comment evidence references page-image URLs like `.../page-01.jpg`, `page-24.jpg`, or `page-*.jpg`.

## Recommended approach

1. Read the task body and comments/attachments. If screenshots mention a CDN/OSS image convention, verify page coverage before coding:
   - Probe the exact provided folder and zero-padded examples (`page-01.jpg`, mid-page examples such as `page-24.jpg`, and the expected last page).
   - Probe each required locale/folder separately; do not infer that an English folder exists because the Chinese folder works.
2. Prefer the provided CDN/OSS page-image URLs when they cover the required pages for a locale, but do **not** make CDN availability a hard dependency unless every target environment has the same CDN path. Production CDN can exist while test/staging lacks it.
3. Always keep a deterministic same-origin fallback for legal docs when non-production environments must work:
   - Default local/test/staging to `/legal-docs/<slug>/<lang>/page-01.jpg`.
   - Enable CDN as primary only for production host or an explicit env such as `VITE_LEGAL_DOCS_ASSET_MODE=cdn`.
   - On `<img onError>`, fall back from CDN to same-origin local page images.
4. Prefer authoritative native task attachments/PDFs as the source of truth for page counts and for any missing CDN locale. Download the PDFs read-only, identify page counts, and render local static images for missing language/page sets and for required non-production fallback.
5. Use deterministic URL generation. Typical resilient layout:
   - Chinese primary CDN in production when provided, e.g. `https://dl.uvisa.cc/uvisa/uvisa-user-agreement-terms-pages/page-01.jpg ...`
   - Same-origin fallback for all required locales, e.g. `public/legal-docs/agreement/zh/page-01.jpg` and `public/legal-docs/agreement/en/page-01.jpg`.
   - Keep local paths stable: `/legal-docs/<slug>/<lang>/page-01.jpg`.
6. Keep page names zero-padded (`page-01.jpg`) even if a conversation initially says `page-*.jpg`; screenshots may later clarify the exact convention.
7. Route language by locale family, not by the current i18n bundle list:
   - `zh`, `zh-CN`, `zh-TW` → Chinese PDF pages.
   - All other locales → English PDF pages.
8. Keep unrelated legal/prospectus/risk-disclosure routes on their existing renderer unless the task explicitly replaces them.
9. Render each page as a full-width image with useful alt text (`<title> 1/41`), but do not assign `src` to every page on initial render. Set `src` immediately only for page 1; use `IntersectionObserver` with a small root margin (for example `360px 0px`) to attach later page URLs near the viewport. `loading="lazy"` alone is not enough because browsers may still discover and queue many image URLs.
10. Record exported page dimensions and reserve layout before the image loads. Prefer manifest/source metadata with `width`, `height`, and `aspect-ratio`; apply the dimensions to both the wrapper and `<img>`. This prevents CLS/layout jumps and makes lazy/IntersectionObserver behavior stable. Do not use a generic `min-height` placeholder when the PDF export dimensions are known.
11. Use a dedicated legal-image load queue for offscreen pages. When a page enters the preload margin, acquire a bounded load slot before assigning the real `<img src>`; release the slot on `load`/`error`. Keep `maxConcurrent` small (1–2; UVISA used 2) so agreement/privacy pages cannot flood mobile network queues or compete with API calls. CDN failure should fall back to same-origin without creating an unbounded request path. Do not render an `<img>` element with `src={undefined}` while queued/pending: browsers show a broken-image icon plus alt text (e.g. `用户协议与服务条款 13/41`) inside the blank PDF card. Render a ratio-preserving skeleton/spinner until a real `src` is assigned.

## Verification checklist

- Unit-test locale routing and page-count mapping.
- Unit-test zero-padded URL generation including a mid-page example such as `page-24.jpg` when the evidence mentions it.
- Route/component-test at least:
  - default/test mode uses same-origin local agreement Chinese first image path and count,
  - default/test mode uses same-origin local privacy Chinese first image path and count,
  - production/CDN mode uses CDN primary for verified Chinese folders and local fallback on image error,
  - agreement English first image path and count,
  - any adjacent legal route that must remain unchanged.
- Check bundle/PWA/performance behavior explicitly:
  - PDF page images should not be `import`ed into JS.
  - Workbox precache should not accidentally include large `jpg` sets unless offline legal docs are a deliberate requirement.
  - `<img loading="lazy">` only controls network fetching; if all pages are rendered as DOM nodes or all pages have `src` at first paint, call that out separately from bundle/precache behavior. Prefer only page 1 `src` on initial render plus `IntersectionObserver` to attach later page `src`s near viewport.
  - Assert non-visible pages have no `src` at first render.
  - Assert dimensions/ratio are present (`width`, `height`, wrapper `aspect-ratio`) for at least one page per distinct export geometry.
  - Unit-test the image preload queue so more than N near-viewport pages cannot start more than `maxConcurrent` image network loads.
- Run TypeScript build; static asset size growth is expected for required non-production fallback and missing CDN variants, and should be called out when large.
- Online/Lark final closeout still needs mobile target-surface visual evidence after deployment; local tests/build only prove implementation sendback.

## Pitfalls

- Do not rely on a CDN folder that only contains the Chinese export if the task also requires English content; either find the English CDN folder or bundle/render English assets.
- Do not assume production CDN availability implies test/staging availability. If test must work, keep same-origin local fallback assets and make CDN opt-in or production-host gated.
- Conversely, do not bundle local images as the only path for a locale whose CDN/OSS page links were explicitly provided and verified for production; use the external links as primary in production and keep local only as fallback/non-production support.
- Do not store only hand-transcribed legal text in i18n when the source of truth is a PDF/image package; transcription can drift from legal-approved formatting.
- Do not update About link labels without updating tests that provide local i18n fixtures.
- Do not let a generic `/legal/:slug` fallback accidentally replace specialized prospectus/risk pages.
- Do not treat `<img loading="lazy">` as sufficient performance control for 18–50 page PDFs. If every page has `src` at first render, mobile browsers may still queue many image requests and interfere with API calls. Gate later page `src`s behind IntersectionObserver and a bounded image load queue.
- Do not leave PDF page placeholders with guessed heights when the source images have deterministic dimensions. Compute/read image sizes once and preserve them in source metadata; otherwise the page can still have layout shifts even if requests are lazy.
