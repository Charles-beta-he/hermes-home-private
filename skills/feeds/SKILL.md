---
name: feeds
description: Use when you need guidance on monitor, validate, and summarize RSS/Atom/JSON feeds and blog update sources.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags:
    - feeds
    - rss
    - atom
    - monitoring
    - blogwatcher
    related_skills:
    - research
    - blogwatcher
    - cronjob
---

# Feeds

## Overview


Use this skill when the task involves RSS, Atom, JSON feeds, blog monitoring, newsletter-like web sources, update detection, feed validation, or scheduled feed summaries.

## When to Use

- You need guidance on monitor, validate, and summarize RSS/Atom/JSON feeds and blog update sources


- Don't use for: tasks outside this skill's trigger class, requests with a more specific neighboring skill, or situations where required evidence/tooling is unavailable.
## Inputs / 输入

Collect the minimum feed task contract before acting:

- Feed source: URL, OPML file, blog homepage, existing feed list, or a named source already configured locally.
- Desired action: discover feed, validate feed, fetch latest items, summarize changes, create/update monitor, or debug a failing monitor.
- Time window: latest N items, since last run, last 24h/7d, or full backfill.
- Output target: direct reply, markdown report, local file, cron delivery, or downstream notes.
- Filters: keywords, authors, categories, language, domain allow/deny list, duplicate policy.
- Freshness requirements: one-shot check vs recurring watch cadence.

If a homepage is supplied instead of a feed URL, first discover feed links from `<link rel="alternate" type="application/rss+xml|application/atom+xml">`, common paths (`/feed`, `/rss`, `/atom.xml`, `/feed.xml`), and site metadata before declaring no feed exists.

## Outputs / 输出

Return a compact, auditable result:

- Feed identity: title, canonical URL, detected format, final resolved URL.
- Fetch status: HTTP status, redirect target, content type, item count, newest item timestamp.
- Change summary: new/changed items, duplicates skipped, filters applied.
- Health verdict: `ok`, `degraded`, `invalid_feed`, `unreachable`, `empty`, or `needs_auth`.
- Next action: no action, repair URL, reduce cadence, add parser exception, or create/update cron job.
- For monitoring jobs: state file path and schedule, plus a note that cron prompt must be script-first and bounded.

## Workflow

Reference: `references/aihot-daily-browser-cron.md` documents a browser-first daily-report pattern for AIHOT (`/daily`) plus cronjob delivery.
Reference: `references/odaily-crypto-daily-source.md` documents the Odaily 星球日报 pattern: use its public JSON endpoints as a crypto/Web3 market-signal section, not a whole-site news stream, with strict noise filtering and taskpool-candidate gating.
Reference: `references/producthunt-api-daily-source.md` documents Product Hunt official API setup for daily reports, including developer-token flow, HTTPS redirect placeholder, Atom fallback semantics, and credential-leak handling.
Reference: `references/producthunt-github-link-resolution.md` documents PH GitHub/source backfill: `/r/...` redirect handling, landing-page HTML repo extraction, UTC date-window drift, precise unresolved states, and taskpool handoff gates.
Reference: `references/producthunt-button-fallback-test.md` documents the test/replay pattern for PH `/r/...` Cloudflare 403 cases: query report date plus date-minus-one UTC, try direct redirect, then use product-page visible buttons before failing closed.
Reference: `references/producthunt-github-link-resolution.md` documents the backfill/debug pattern for Product Hunt GitHub/source links that resolve through `/r/...` redirects, product landing pages, or GitHub Pages before reaching a repo.
Reference: `references/daily-report-external-signal-taskpool-replay.md` documents how to replay GitHub/Product Hunt/AIHOT daily report signals through governed sidecar generation and isolated taskpool ingest when report body and `*.tasks.json` diverge.
Reference: `references/daily-report-github-ph-sidecar-candidates.md` documents how daily reports should turn GitHub Trending / Product Hunt table rows into governed sidecar candidates, then verify ingest with dry-run, isolated temp-vault writeback, and idempotency checks.


1. **Discover**
   - If given a page URL, discover candidate feed URLs.
   - Prefer explicit feed links over guessed paths.
   - Preserve redirects and canonicalize final URLs.

2. **Fetch safely**
   - Use bounded timeouts and a clear user agent.
   - Avoid retry storms; retry only transient network errors.
   - Record HTTP status, content type, and final URL.

3. **Parse and normalize**
   - Normalize RSS/Atom/JSON Feed into a common item schema: `id`, `title`, `url`, `published`, `updated`, `author`, `summary`, `content_hash`.
   - Deduplicate by stable GUID/id first, then canonical URL, then `(title, published)`.

4. **Compare state**
   - For monitors, compare against a local state file under `~/.hermes/state/feeds/` or the existing watcher state.
   - Do not overwrite state until the fetch and parse phase succeeds.
   - If state is missing, treat the run as bootstrap and avoid sending a noisy “all items are new” alert unless the user requested backfill.

5. **Summarize**
   - Summaries should separate facts from interpretation.
   - Include source links and timestamps.
   - For multi-source reports, group by source, then sort by time descending.

6. **Persist / schedule when requested**
   - Prefer deterministic scripts for recurring feed checks.
   - Cron prompts should only summarize injected JSON/text output in 2–3 lines.
   - Do not create recursive cron jobs from a cron run.

## Boundary Conditions / 边界条件

- **Invalid XML/HTML returned:** report `invalid_feed`, include content type and first parse error; try homepage discovery once if safe.
- **HTTP 403/401/auth wall:** report `needs_auth`; do not scrape private/authenticated feeds without credentials.
- **HTTP 429/rate limit:** report `degraded`; reduce cadence or back off, never increase retry pressure.
- **No timestamps:** use fetch time for ordering only as a fallback and label it as inferred.
- **Duplicate GUIDs with changed content:** compare content hash; report as `changed` rather than `new`.
- **Timezone ambiguity:** keep original timestamp and normalized UTC where possible.
- **Large feeds:** cap parsed items by requested window; do not dump full feed content into context.
- **Binary/non-text response:** stop and report content type; do not attempt to parse as feed.
- **Redirect loops:** stop after a small fixed limit and report `unreachable`.
- **Cron monitoring:** never put arguments in Hermes cron `script`; create a no-argument wrapper if arguments are needed.

## Checkpoints / 检查点

- [ ] Source URL or feed list is explicit and normalized.
- [ ] Fetch used bounded timeout and captured final URL/status/content type.
- [ ] Feed format and item count are reported.
- [ ] Dedupe key is documented.
- [ ] State update is atomic and only after successful parse.
- [ ] Output includes source links and timestamps.
- [ ] Recurring monitor is script-first, bounded, and emits non-empty JSON/text.
- [ ] Failures are classified (`invalid_feed`, `unreachable`, `needs_auth`, `degraded`) instead of silently ignored.

## Examples / 示例

- AIHOT daily report: use browser tools against `https://aihot.virxact.com/daily`, extract `最新一期`, and schedule a cronjob for a concise Chinese briefing.

### Example 1: Validate a feed URL

User: “检查 https://example.com/feed.xml 是否可用”

Expected behavior:

```text
Fetch with timeout → parse RSS/Atom/JSON → report status, final URL, item count, newest timestamp, and health verdict.
```

### Example 2: Discover a blog feed

User: “帮我监控这个博客的新文章：https://example.com/blog”

Expected behavior:

```text
Discover alternate feed links → validate the best candidate → propose or create a bounded script-first monitor if the user requested scheduling.
```

### Example 3: Summarize latest feed changes

User: “总结这 5 个 RSS 最近 24 小时的新内容”

Expected behavior:

```text
Fetch each source with bounded timeout → normalize items → filter by 24h → dedupe → grouped markdown summary with links and timestamps.
```

### Example 4: Debug a noisy feed monitor

User: “这个 feed 每次都把旧文章当新文章”

Expected behavior:

```text
Inspect state and item identifiers → compare GUID/URL/title+published/content hash → identify unstable ids or missing state update → recommend a stable dedupe key.
```

## Minimal Python Pattern

```python
from urllib.request import Request, urlopen

req = Request(url, headers={"User-Agent": "HermesFeedMonitor/1.0"})
with urlopen(req, timeout=20) as resp:
    status = resp.status
    content_type = resp.headers.get("content-type", "")
    body = resp.read(2_000_000)
```

Keep network and parsing code bounded. For recurring jobs, write JSON with `status`, `source`, `items_seen`, `new_items`, `error`, and `state_path` so the cron agent only summarizes deterministic output.

## Related Skills

- `research`: turn feed items into research digests.
- `blogwatcher`: monitor blogs/RSS sources over time.
- `cronjob`: schedule bounded recurring feed checks.

## Common Pitfalls

- Treating a homepage curl `403` as proof the source is unavailable when the site is still browser-readable.
- Summarizing the homepage mixed feed when the user asked for a daily issue page like AIHOT `/daily`.
- Scheduling recurring checks without enabling the toolset actually needed by the source (for dynamic pages, use browser tools).
- For mixed editorial/news sites like Odaily, treating the whole site as a daily feed creates noise. First classify the source role (for example, crypto/Web3 market signal), then encode include/exclude filters and a dedicated report section.
- Letting ordinary news automatically create governed taskpool candidates. Feed-derived candidates should be limited to directly transferable, evidence-backed control-plane opportunities.
- Putting literal credential environment-variable names into durable cron prompt prose or user-facing report text. Secret scanners can block commits on secret-like variable names even without a value; use generic wording in prose and reserve exact names for executable code when necessary.
- For Product Hunt, assuming the app Redirect URI can be `http://localhost/...`; the dashboard may require HTTPS/SSL even when the integration only needs a developer token. Use an HTTPS placeholder and document that the redirect is unused for server-side read-only reports.
- For Product Hunt GitHub/source enrichment, treating `github_link_detected_unresolved` as a final result. First distinguish: PH `/r/...` redirect unresolved, landing page found but repo not normalized, repo URL resolved but GitHub metadata unavailable, or truly no repo evidence. A `Github` productLink may redirect to a product website/GitHub Pages page whose HTML contains the actual repo.
- For Product Hunt backfills, querying only the local report date. The composed daily report may be local-time while Product Hunt `createdAt` is UTC; include the prior UTC day when matching historical posts.
- Repeating API keys, API secrets, or developer tokens from screenshots. Product Hunt dashboard exposes credentials in clear text; if the user shares a screenshot, identify the page/state without echoing credential values and advise rotation/deletion.
- After adding a new source to an existing daily report flow, only validating the source script but not regenerating/reposting the composed report. For preview requests, insert the new section into the current report artifact and resend the full report.
- For Product Hunt, treating `type: Github` PH `/r/...` redirects as unresolved when they land on a project website. Resolve the redirect, then do one bounded landing-page HTML scan for canonical `github.com/<owner>/<repo>` links before declaring unresolved.
- For Product Hunt `/r/...` GitHub/source redirects returning Cloudflare `403`, do not stop at the direct fetch. Use the PH product page visible-button fallback (`Visit` / `Website` / `GitHub` / `Source Code`) when the browser/session can see the page; if the product page is also Cloudflare-challenged, record that separately and fail closed.
- For Product Hunt backfills, searching only the local report date. PH `createdAt` is UTC while local reports may be Asia/Shanghai; inspect both report-date and report-date-minus-one UTC windows.

1. Loading this skill outside its trigger class and skipping a simpler, more direct path.
2. Ignoring prerequisites such as platform, credentials, installed commands, or linked reference files.
3. Treating the skill as a static memo instead of verifying the exact commands, artifacts, or outputs in the current environment.

## Verification Checklist

- [ ] The task actually matches this skill's trigger class and the current route is still appropriate.
- [ ] All prerequisites, linked references, templates, scripts, and required tools have been checked before execution.
- [ ] Claimed outputs, commands, files, or external side-effects were read back or otherwise verified before completion.
