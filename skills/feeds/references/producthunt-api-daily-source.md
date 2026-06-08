# Product Hunt official API for daily reports

Use this reference when adding Product Hunt to a daily report, product-discovery feed, or scheduled digest.

## Source role

Treat Product Hunt as a product-discovery source, not a general news feed. For daily reports, prefer AI/developer-tool/automation/productivity/open-source-infrastructure products and clearly label whether the data came from the official GraphQL API or the Atom feed fallback.

## Official API path

- Docs: https://api.producthunt.com/v2/docs
- GraphQL endpoint: `https://api.producthunt.com/v2/api/graphql`
- Authentication: `Authorization: Bearer <developer token or OAuth access token>`
- Default app scope is read-only/public.
- Product Hunt says the API must not be used for commercial purposes without contacting `hello@producthunt.com`.

For a personal/server-side daily report, use a **Developer Token** from the API dashboard rather than full user OAuth. Developer tokens are intended for simple scripts, do not expire, and are locked to the user's account.

## Dashboard setup quirks

1. Create an app in the API dashboard.
2. The dashboard requires a Redirect URI even if the integration only uses a developer token.
3. `http://localhost/...` may be rejected with `redirect_uri must be an HTTPS/SSL URI.`
4. For a non-OAuth daily-report script, use a harmless HTTPS placeholder such as `https://localhost/callback` or `https://example.com/callback`; this redirect is not used by the developer-token flow.
5. After the app exists, use the `Create Token` button under **Developer Token**.
6. Do not ask the user to paste or screenshot the token. Have them store it locally and only report whether validation passed.

## Secret handling

The dashboard displays API Key, API Secret, and generated developer tokens in clear text. If a screenshot exposes API keys/secrets/tokens, treat them as leaked:

- Do not repeat the values in chat.
- Tell the user to delete/rotate the exposed app/credentials if possible.
- Continue with newly generated credentials only after they are stored locally outside chat.
- Avoid putting literal secret-looking environment variable names in prose that will be committed or pasted into reports; secret scanners may block commits even without values. Use generic wording in prose and reserve exact env names for local setup commands or scripts when necessary.

## Local configuration pattern

Store the developer token in local environment only, never in git:

```bash
cat >> ~/.hermes/.env <<'EOF'
PRODUCTHUNT_TOKEN=replace_with_developer_token
EOF
chmod 600 ~/.hermes/.env
```

Validation query:

```bash
source ~/.hermes/.env
curl -s https://api.producthunt.com/v2/api/graphql \
  -H "Authorization: Bearer $PRODUCTHUNT_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{"query":"{ posts(first: 3) { edges { node { name tagline url votesCount createdAt } } } }"}'
```

A successful response containing `posts.edges` means the daily report can switch from Atom fallback to official API mode.

## Open-source evidence enrichment

When Product Hunt is used in a daily report, do not infer that a product is open source from its category, tagline, or developer vibe. Use evidence tiers:

- **Explicit source repository:** official GraphQL `productLinks` includes a source-code link such as `type: "Github"` / GitLab, or resolving the Product Hunt redirect lands on `github.com`, `gitlab.com`, or another source host. Label the product with the repo URL and, if public metadata is available, include repo name, stars, license, archive/private status, and a one-line repo description.
- **Related-to-GitHub but not proven open-source:** title/tagline mentions GitHub or the product is a GitHub workflow tool, but `productLinks` does not expose a source repository. Label as “GitHub-related; no source repo evidence found,” not as open source.
- **Unknown/no evidence:** only website, social, app-store, or product links are present. Label as “未发现开源证据/unknown.”

Implementation notes:

1. Query `productLinks { type url }` from the official GraphQL API.
2. Treat `type == "Github"` or final resolved URL containing a source host as evidence.
3. Product Hunt URLs may be outbound redirect wrappers; resolve redirects with bounded timeout before classification.
4. If a GitHub repo URL is found, optionally call GitHub’s public repo API to enrich with `full_name`, `stargazers_count`, `forks_count`, `license.spdx_id`, `archived`, `private`, `pushed_at`, and `description`.
5. Keep this as evidence labeling, not endorsement: low-star or restrictive-license repos still count as “repo evidence,” but may not be meaningfully open-source.

## Fallback semantics

If no token is configured or the API returns 401, use `https://www.producthunt.com/feed` as an Atom fallback. Label this as **feed latest** only. Do not present feed fallback as a complete vote/ranking leaderboard, because the Atom feed lacks votes/ranking/website fields.

## Daily digest script pattern

The local daily report integration should use the deterministic script:

```bash
python3 ~/.hermes/scripts/producthunt_daily_digest.py --limit 20 --top 8
python3 ~/.hermes/scripts/producthunt_daily_digest.py --limit 20 --top 8 --markdown
```

Script behavior:

- Loads local environment from `~/.hermes/.env` and uses the official GraphQL API when available.
- Falls back to Atom feed if the API is missing/unauthorized/unavailable; the output status becomes `degraded` and `source_mode` becomes `atom_fallback`.
- Reads `productLinks { type url }` and treats a Product Hunt API link typed as `Github`/source as official open-source evidence even when the `/r/...` redirect cannot be resolved from terminal because of Cloudflare.
- If a final GitHub repo URL is available, enriches it through the public GitHub repo API with repo, stars, forks, license, archived status, and pushed_at.
- Scores products for AI/devtools/automation/productivity/open-source relevance and emits both JSON and a Markdown preview.

Open-source evidence labels:

- `github_repo_verified`: GitHub/source link resolved to a public repo and repo metadata was read.
- `github_link_detected_unresolved`: Product Hunt official API exposed a GitHub/source-code external link, but the terminal could not resolve the Product Hunt redirect to a repo URL. Report this as “GitHub 外链证据，repo 元数据未解析”, not as verified open source.
- `possible_open_source_unverified`: Product text mentions GitHub/open-source/OSS but no repo metadata was verified.
- `unknown`: no open-source evidence found. Never infer open source from product category alone.

Common pitfall: Product Hunt `/r/...` redirect URLs may return Cloudflare 403 from terminal. Do not retry aggressively or mark the product as no-data; preserve the API link type as evidence and downgrade only the repo metadata enrichment.
