# X public post / article intake evidence pattern

Use when a user provides public X/Twitter post links for analysis, evidence capture, or taskpool intake, especially when the tweet body is only a `t.co` article link or the useful content is an X Article / attached video.

## Applicability

- Public X status URLs (`https://x.com/<user>/status/<id>`).
- X Articles reached through `https://x.com/i/article/<id>` or `t.co` redirects.
- Attached X videos where article/body metadata is insufficient and visual evidence is needed.
- Analysis/taskpool intake where social claims must remain leads until verified by authoritative sources.

## Anti-conditions

- Do not use this to bypass login-only/private/protected posts.
- Do not treat X extraction as permission to interact with X, post, like, follow, DM, or scrape at scale.
- Do not promote model/product/repo/pricing claims from a post into skills, config, or code without official-source verification.
- Do not store credentials, cookies, private tokens, or personal account state in evidence.

## Evidence ladder

1. `publish.twitter.com/oembed` for author, date, canonical URL, and simple tweet text.
2. Resolve `t.co` redirects with `allow_redirects=false` to identify whether the link points to media, an X Article, or an external artifact.
3. For X Articles / richer tweet data, fetch the current web bearer token from `https://abs.twimg.com/responsive-web/client-web/main*.js`, activate a guest token against `https://api.x.com/1.1/guest/activate.json`, then call the public GraphQL `TweetResultByRestId` operation using query id discovered from the same `main*.js` bundle.
4. Request article field toggles such as `withArticlePlainText`, `withArticleSummaryText`, and `withArticleRichContentState`; save the raw JSON and a normalized text file.
5. For attached videos, save only the publicly exposed media URL, duration/variant metadata, and a contact sheet or sampled frames for visual inspection. For attached images/media downloads that return 403, retry with browser-like `User-Agent` and `Referer: https://x.com/`; if still blocked, keep the media metadata and write an explicit download-error artifact instead of dropping the post evidence. Mark full transcript/ASR as a separate evidence step if not performed.
6. Write a scoped intake note separating: extracted X facts, visible media/article content, claims requiring official verification, marketing/opinion language, transferable patterns, red lines, and recommended landing zone.

## Minimal Python skeleton

```python
import json, re, urllib.parse, requests

main = requests.get("https://abs.twimg.com/responsive-web/client-web/main.ea67863a.js", timeout=20).text
bearer = re.search(r"Bearer ([A-Za-z0-9%_-]+)", main).group(1)

s = requests.Session()
s.headers.update({
    "authorization": "Bearer " + bearer,
    "User-Agent": "Mozilla/5.0",
    "x-twitter-active-user": "yes",
    "x-twitter-client-language": "en",
})
guest = s.post("https://api.x.com/1.1/guest/activate.json", timeout=20).json()["guest_token"]
s.headers["x-guest-token"] = guest

# Discover this from main*.js; do not hardcode forever.
query_id = "<TweetResultByRestId query id>"
operation = "TweetResultByRestId"
variables = {"tweetId": "<status_id>", "withCommunity": False, "includePromotedContent": False, "withVoice": False}
field_toggles = {
    "withArticleRichContentState": True,
    "withArticlePlainText": True,
    "withArticleSummaryText": True,
    "withArticleVoiceOver": False,
}
features = {"articles_preview_enabled": True, "longform_notetweets_consumption_enabled": True, "responsive_web_twitter_article_tweet_consumption_enabled": True}

url = f"https://x.com/i/api/graphql/{query_id}/{operation}?variables=" + urllib.parse.quote(json.dumps(variables, separators=(",", ":"))) + "&features=" + urllib.parse.quote(json.dumps(features, separators=(",", ":"))) + "&fieldToggles=" + urllib.parse.quote(json.dumps(field_toggles, separators=(",", ":")))
data = s.get(url, timeout=20).json()
```

The feature set changes over time; when a call fails, re-read `main*.js` for the current operation metadata and copy the relevant feature switches rather than concluding X extraction is impossible.

## New logged-out X shell fallback

Applicability: the public status page loads the newer `abs.twimg.com/x-web/x-web/entry-client-logged-out-*.js` shell and contains no `responsive-web/client-web/main*.js`, so the normal bundle-discovery step cannot find the bearer token or `TweetResultByRestId` query id.

Anti-conditions: do not use this to bypass protected/login-only posts, and do not hardcode a captured bearer token or query id into a durable skill/script.

Fallback procedure:

1. Read the status-page SSR payload before escalating. Public logged-out HTML may already contain the canonical article id, title, preview text, author, counts, and `sharedContent`/`article_results` references.
2. Resolve the `t.co` target or extract the article id from SSR, then fetch `https://x.com/i/article/<article_id>`. This route may still serve the legacy responsive-web shell even when the status page uses the new x-web shell.
3. Discover `https://abs.twimg.com/responsive-web/client-web/main.<hash>.js` from the article page, then extract the current web bearer token and `TweetResultByRestId` query id from that bundle.
4. Activate a guest token and call `TweetResultByRestId` using the original status/tweet id, not the article id. Request the article field toggles from the normal evidence ladder.
5. Prefer the returned `article.article_results.result.plain_text` for normalized text. Preserve `content_state.blocks` and `entityMap` separately when headings, embeds, links, media ids, or block types matter; do not reconstruct the article only from broad recursive `text` matches when `plain_text` exists.
6. Save the status SSR metadata, article-page bundle URL, GraphQL JSON, normalized plain text, and extraction boundary. The article page showing an error shell in visible HTML does not disprove availability if its bundle metadata and public GraphQL route succeed.

Verification:

- status id and article id are recorded as different identifiers;
- the bundle URL and query id came from the current fetch;
- GraphQL returned the expected article `rest_id`, title, `plain_text`, and block count;
- no credentials/cookies/private account state were stored.

## Taskpool intake shape

When adding a task from X signals:

- Prefer one consolidated advisory/recertification card for a batch of related X links when the sources are thematically related.
- If the user explicitly asks to analyze/add links “separately” (`分别分析添加任务池`), create separate advisory cards per source, but keep a shared evidence directory and a `created_tasks.json` index for readback.
- Include raw evidence directory, normalized notes, original URLs, per-source text files, media/contact-sheet paths when present, and access boundary.
- Make official-source verification an acceptance criterion for model/product/repo/paper/pricing/capability/trading claims. When a concrete artifact is named, do a lightweight authoritative readback during intake when possible (for example GitHub API metadata/README for repos, package registry for libraries, official docs for product/model claims) and record unresolved exact sources as `unverified`, not as proof or disproof.
- Use anti-drift wording: social popularity, demos, and X Article claims are not implementation proof.
- Keep high-risk domains such as trading, credentialed products, paid model calls, external dispatch, publication, and runtime mutation closed until a later exact authority gate.
- If implementation is recommended, split a later bounded task with deterministic verifier and rollback/readback requirements.

## Batch readback / repair pitfall

`brain_task_orchestrator.py add` may accept a card while collapsing repeated `--accept` or `--acceptance-evidence` values into one visible body item. After batch creation, read back every created task and patch both frontmatter and the body `## Acceptance Criteria` so future workers see all gates.

Minimum readback checks:

- status/priority/lane match the intended advisory intake;
- evidence refs include source URL, per-source evidence text, shared analysis note, and media directory when present;
- body Acceptance Criteria include source-boundary reading, authoritative verification, prior-coverage dedupe, anti-drift/authority boundary, and split-work requirements;
- taskpool selfcheck passes; report parallel-boundary warnings separately from invalid/failure results.
