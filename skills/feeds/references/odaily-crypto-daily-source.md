# Odaily crypto/Web3 daily-report source pattern

Use this when adding Odaily 星球日报 to a daily briefing or similar feed digest.

## Source positioning

- Treat Odaily as a **crypto/Web3 market signal source**, not as a whole-site news stream.
- Keep it in a dedicated section such as `加密/Web3 市场（Odaily星球日报）`.
- Do not let ordinary crypto news create taskpool / implementation candidates by default. Only create a candidate when the item is directly transferable to Hermes/local-brain/taskpool/browser automation and has evidence.

## Public API endpoints observed

Odaily's frontend currently reads public JSON endpoints under `https://web-api.odaily.news`:

- Info flow: `/infoFlow/list?page=1&size=10`
- Latest posts: `/post/page?page=1&size=10`
- Newsflash: `/newsflash/page?page=1&size=10`
- Hot rank: `/hotRank/list?hotRankType=WEEKLY&entityType=POST`
- Hot words: `/hotWord/list?limit=20`
- Hotspots: `/hotspot/page?page=1&size=5`
- Core market quotes: `/market/listBySymbols?symbols[]=btcusdt&symbols[]=ethusdt&symbols[]=solusdt&symbols[]=bnbusdt&exchange=1`

Use bounded requests, include a normal browser referer (`https://www.odaily.news/zh-CN`), and tolerate schema/endpoint drift.

## Daily section shape

Recommended output:

1. Market overview: BTC/ETH/SOL/BNB price + 24h change.
2. Today's mainlines: 1-3 hotspot topics.
3. Important newsflash: 3-6 items, only if `isImportant=true` or the title/summary hits strong crypto keywords.
4. Hot narratives: 3-7 hot words / ranked themes.
5. Worth reading: 1-2 long-form posts, labeled as reporting/analysis/opinion when possible.
6. Source evidence: endpoint/homepage URLs and any degraded modules.

## Filtering rules

Prefer:

- 24H crypto hot coins and key news
- BTC / ETH / SOL / BNB market changes
- regulation, enforcement, taxes, ETF, stablecoins, exchanges
- security incidents, exploits, hacks, chain-risk events
- whale positions, liquidation, leverage, major on-chain activity
- RWA / prediction markets / tokenization when directly crypto-relevant

Filter or downgrade:

- ads, project marketing, ordinary events, signup announcements
- duplicate stories across hotspot/post/newsflash
- stock/semiconductor/robotics/AI/macro items without crypto impact
- pure price movements without context
- title-only predictions or opinion pieces presented as facts

## Implementation notes

- Use a deterministic script for recurring cron jobs; have the cron agent summarize injected JSON/markdown instead of crawling the full site each run.
- Keep JSON fields stable: `schema_version`, `source.status`, `market`, `hotspots`, `important_newsflash`, `hotwords`, `selected_articles`, `hotrank`, `selection_policy`.
- Mark hot-rank items as narrative/attention signals, not factual importance.
- For degraded API calls, keep the section but explicitly list missing modules instead of inventing data.
- When embedding the source into a durable Hermes cron prompt or report template, avoid literal credential environment-variable names in prose. Secret scanners may block commits on secret-like variable names even when no secret value is present. Phrase as “Product Hunt official API access configured” / “API credential env var” unless the exact variable name is required inside executable code.
- If integrating into an already-generated daily report for preview, update the same day's markdown file and resend the full report after inserting the Odaily section; do not only prove the script works separately.

## Verification

- Run the script once in JSON mode and assert: schema version, source status, market count, and at least one crypto-relevant item.
- Run compact markdown output and check that obvious non-crypto noise (e.g. stock/semiconductor/robotics headlines) is absent.
- Verify the daily cron prompt contains the dedicated Odaily section and the no-taskpool-candidate rule for ordinary crypto news.
- Before committing cron/report changes, run the repository's normal staged secret scan/pre-commit path or attempt a real commit; if blocked by a secret-like variable name in prose, redact the prose and restage only the intended scoped changes.
