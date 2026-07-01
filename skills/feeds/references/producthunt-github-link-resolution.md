# Product Hunt GitHub/source link resolution

Use this reference when a Product Hunt daily report says `github_link_detected_unresolved`, `repo metadata unresolved`, or when backfilling historical PH items into evidence/taskpool.

## Problem pattern

Product Hunt official GraphQL `productLinks` often marks a link as `type: Github`, but the URL is a PH tracking redirect such as:

```text
https://www.producthunt.com/r/<token>?utm_campaign=...
```

The redirect does **not** always land directly on `github.com/<owner>/<repo>`. Common durable shapes:

1. `PH /r/... -> github.com/<owner>/<repo>` — direct repo, normal path.
2. `PH /r/... -> project website / GitHub Pages -> HTML contains github.com repo links` — do one bounded landing-page HTML scan before declaring unresolved.
3. `PH /r/... -> website with only org/profile links` — treat as weak evidence unless a valid repo path can be normalized.
4. GitHub API returns 403/rate-limited even after repo URL is found — distinguish `repo URL resolved; metadata blocked` from `repo URL unresolved`.

## Resolution workflow

1. Fetch PH official API first; do not scrape PH pages by default because Cloudflare may block terminal/browser reads.
2. If an official API `productLinks` GitHub/source URL is a PH `/r/...` redirect that returns `403`/Cloudflare in terminal or direct browser navigation, use the product page as an explicit fallback before declaring unresolved:
   - Open the canonical PH product page from API/feed (`https://www.producthunt.com/products/<slug>` or post URL) with browser tools.
   - Inspect/click the visible product/source buttons (for example `Visit`, `Website`, `GitHub`, `Source Code`, launch/post outbound buttons) rather than directly fetching the `/r/...` URL.
   - Capture the resulting URL/readback; if it lands on GitHub, normalize owner/repo and proceed with metadata enrichment.
   - If it lands on a project website/GitHub Pages, do one bounded landing-page HTML scan for canonical `github.com/<owner>/<repo>` links.
3. For each `productLinks` item whose `type` or URL suggests `github`, `source`, or `gitlab`:
   - Resolve the PH `/r/...` redirect when possible.
   - If direct redirect is blocked, apply the product-page button fallback above.
   - If final URL is `github.com`, normalize owner/repo and enrich via GitHub API.
   - If final URL is an HTTP(S) project website, bounded-fetch HTML/text and extract `github.com` URLs from anchors/meta/script text.
   - Normalize only valid repo paths: `github.com/<owner>/<repo>`; ignore `orgs`, `topics`, `login`, `pricing`, etc.
3. When reading historical daily reports, account for timezone drift:
   - Local report date is often Asia/Shanghai.
   - PH `createdAt` is UTC.
   - Backfill by searching both `report_date` and `report_date - 1` UTC day windows.
4. Deduplicate by canonical repo URL after GitHub API redirects. If two inputs resolve to the same `html_url`, keep one.
5. Keep historical daily reports immutable when possible. Write a backfill artifact under `~/.hermes/notes/reports/` rather than editing old report prose.

## Reporting language

Prefer precise states:

- `github_repo_verified`: repo URL and metadata were verified.
- `github_repo_url_resolved_metadata_blocked`: repo URL exists but GitHub metadata failed/rate-limited.
- `github_link_detected_redirect_to_landing`: PH indicates source/GitHub, but final URL is a website and no repo was found yet.
- `github_link_detected_unresolved`: no repo URL found after redirect + bounded landing-page scan.

Avoid collapsing all failures into “repo metadata unresolved”; it hides whether the missing piece is PH redirect, landing-page extraction, or GitHub API rate limit.

## Backfill-to-taskpool handoff

If the user asks to add parsed PH repo candidates to taskpool:

- Create advisory/evidence tasks, not implementation tasks.
- Use the backfill report as `evidence_bundle`.
- Gate acceptance on repo readback, capability mapping, low-coupling/risk check, and prune-or-promote decision.
- Do not promote a PH/GitHub source directly into production code changes.

## Daily-report unresolved recurrence triage

When a scheduled daily report repeatedly shows `github_link_detected_unresolved`, split the outcome into two decisions instead of treating the unresolved state as a final answer:

1. **Product-level candidate decision** — stay fail-closed unless a canonical repo URL or repository metadata is read back. A PH `type: Github` `/r/...` link plus Cloudflare 403 is official source-link evidence, but not enough to create a product-absorption task.
2. **Pipeline/system candidate decision** — if the report pipeline only prints `github_link_detected_unresolved` without a precise state, create or update a governed pipeline-improvement task. The task should target the daily-report/sidecar flow, not the product itself, and should require replay evidence plus dry-run/live ingest verification.
3. **Required precise states in future reports/sidecars** — distinguish at least:
   - `ph_redirect_cloudflare_blocked` / PH `/r/...` returns Cloudflare or 403 before redirect resolution;
   - `github_link_detected_redirect_to_landing` / redirect reaches a landing site but no repo is found after bounded HTML scan;
   - `github_repo_url_resolved_metadata_blocked` / repo URL is normalized but GitHub API metadata is rate-limited or blocked;
   - `github_link_detected_unresolved` / no repo URL found after all bounded steps.
4. **Evidence to capture** — report output path, sidecar path, PH script counts (`github_source_link_count`, `github_repo_count`), representative `/r/...` status/headers, and ingest result (`created/skipped/invalid`).

This pattern keeps ordinary PH discovery from flooding taskpool while still making repeated automation gaps actionable.
