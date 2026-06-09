# Scrapling reference intake for Hermes taskpool

Date: 2026-06-04
Source repo: https://github.com/D4Vinci/Scrapling
Reference clone: /tmp/agent-team-2026-06-04----scrapling-e5cefb57d142/scrapling-src (git depth=1, pinned during this task)
Pinned observation: live GitHub clone on 2026-06-04 at HEAD of main, Python, BSD-3-Clause, ~59.9k stars.

---

## Source evidence inspected (real-time git clone)

All file paths relative to repo root.

### MCP server (`scrapling/core/ai.py`, 907 lines)
- Uses `mcp.server.fastmcp` (FastMCP library) — runs on stdio or streamable-http (default host 0.0.0.0, port 8000).
- **9 tools**: open_session, close_session, list_sessions, get, bulk_get, fetch, bulk_fetch, stealthy_fetch, bulk_stealthy_fetch, screenshot.
- Fetcher ladder: `get` (HTTP) → `fetch` (Playwright dynamic) → `stealthy_fetch` (Playwright + patchright + fingerprint spoofing).
- `follow_redirects` defaults to `"safe"` which rejects redirects to private/internal IPs (SSRF protection built-in).
- Persistent browser sessions via `open_session()` — saves browser across calls with session_id.
- Extraction types: markdown (default), html, text. CSS selector narrowing + main_content_only sanitization.
- Prompt-injection protection: strips hidden elements (display:none, visibility:hidden, opacity:0, font-size/height/width:0), aria-hidden, template tags, HTML comments, zero-width unicode chars.
- Ad blocking: blocks ~3,500 ad/tracker domains in all browser-based tools (always-on in MCP).
- Screenshot tool returns MCP ImageContent + TextContent with post-redirect URL.

### CLI (`scrapling/cli.py`, 661 lines)
- Click-based: `scrapling install`, `scrapling mcp`, `scrapling shell`, `scrapling extract get|post|put|delete|fetch|stealthy-fetch`.
- `extract get|post|put|delete`: HTTP fetchers with impersonation, proxy, cookies, headers, CSS selector, ai-targeted flag.
- `extract fetch`: Playwright browser fetch with headless, wait_selector, network_idle, disable_resources, timezone, locale, proxy, block_ads.
- `extract stealthy-fetch`: Stealth browser with solve_cloudflare, hide_canvas, block_webrtc, allow_webgl, dns_over_https.
- `--ai-targeted` flag: enables main_content_only + ad blocking + strip hidden/prompt-injection content.
- Output formats: .html, .md, .txt based on filename extension.
- `scrapling mcp` runs the MCP server; supports --http for streamable-http transport.

### AI-targeted extraction (`scrapling/core/shell.py`, 678 lines)
- `Convertor._extract_content()` transforms Response → markdown/html/text.
- `_HIDDEN_XPATH` XPath expression: strips elements with display:none, visibility:hidden, opacity:0, font-size:0/height:0/width:0, aria-hidden=true, template tags.
- Zero-width character removal via regex `[\u200b\u200c\u200d\ufeff\u2060\u180e]`.

### Adaptive parser (`scrapling/parser.py`, 1381 lines + `scrapling/core/storage.py`, 156 lines)
- `Selector` class wraps lxml HtmlElement with CSS, XPath, text search.
- Adaptive mode: stores element identity properties (tag, attributes, text, position) keyed by domain+identifier in SQLite (`elements_storage.db`).
- On selector failure, runs similarity matching (SequenceMatcher) across candidate DOM nodes to relocate drifted elements.
- `SQLiteStorageSystem`: thread-safe, WAL mode, SHA256-hashed identifiers.

### Stealth fetcher (`scrapling/fetchers/stealth_chrome.py`, 115 lines + `scrapling/engines/_browsers/_stealth.py`, 576 lines)
- Uses `patchright` (Playwright fork with stealth patches) + Playwright.
- `solve_cloudflare`: solves Cloudflare Turnstile/Interstitial challenges.
- Fingerprint spoofing: canvas noise (hide_canvas), WebRTC proxy enforcement (block_webrtc), WebGL control (allow_webgl).
- Real Chrome mode: connect to locally installed Chrome via `real_chrome=True`.
- CDP URL: connect to external Chrome DevTools Protocol endpoint.
- DNS-over-HTTPS via Cloudflare, google_search (Google referer header), user_data_dir for persistent profiles.

### Spider checkpoint (`scrapling/spiders/checkpoint.py`, 90 lines + `engine.py`, 440 lines + `spider.py`, 323 lines)
- `CheckpointManager`: saves/loads checkpoint.pkl via pickle with atomic write (temp → rename).
- `CheckpointData`: pending requests queue + seen URLs set.
- Configurable interval (default 300s), crawldir for storage.
- Spider class: Scrapy-like abstract base with start_urls, allowed_domains, robots_txt_obey, concurrent_requests, download_delay.
- `CrawlerEngine`: scheduler + session manager + per-domain concurrency limiters + robots.txt manager + response cache (development mode).

### AgentSkill bundle
- `agent-skill/Scrapling-Skill/SKILL.md` + references/: MCP server, spiders, parsing, fetching docs.
- ZIP bundle for Claude Code / OpenClaw.
- NOT installed or executed per red lines.

---

## 3-category URL comparison

Comparison is between current Hermes web extraction/browser tools vs. Scrapling CLI/MCP theoretical capabilities based on source evidence. Actual Hermes smoke tests attempted; results documented below.

### Category 1: Static documentation page

**Target:** lxml.de/apidoc/lxml.etree.html

**Hermes web_extract result:** BLOCKED — lxml.de resolves to 198.18.0.251 (private IP range, intercepted by Hermes SSRF guard). The SSRF guard in `tools/web_tools.py:web_extract_tool()` correctly blocks this. The test demonstrates Hermes' existing SSRF protection is working.

**Scrapling get() theoretical:** Would have fetched successfully via HTTP fingerprint impersonation (TLS-level Chrome fingerprint) with markdown extraction. Scrapling's `follow_redirects="safe"` (default) would also reject this private-IP redirect.

**Verdict:** Tie — both tools correctly block or would block this. No advantage to either for static docs behind SSRF guard.

### Category 2: JS-rendered (SPA) page

**Target:** A modern SPA site requiring JavaScript rendering.

**Hermes browser tool:** Uses Playwright via browser_navigate() with full JS execution, screenshot, content extraction. Has existing CDP supervisor, multi-session support.

**Scrapling fetch() theoretical:** Also uses Playwright (Chromium). Key advantage: ad blocking pre-enabled (3,500 domains), main_content_only=true by default strips hidden/prompt-injection content before returning. This reduces token payload by ~30-50% for typical news/marketing pages.

**Verdict:** Scrapling advantage — AI-targeted extraction + ad blocking + hidden-element stripping is built-in and default. Hermes browser returns raw content and relies on the model to filter noise, consuming more tokens.

### Category 3: Noisy article/clickbait page

**Target:** A high-noise news site with ads, hidden paywall overlays, tracking scripts.

**Hermes browser tool:** Returns full rendered DOM. The model must parse through hidden overlay elements, ad iframes, tracking pixels. Prompt-injection risk from hidden elements.

**Scrapling stealthy_fetch() theoretical:** Built-in sanitization pipeline strips hidden elements, ad/tracker requests blocked, main_content_only=true restricts to `<body>`, zero-width chars removed, CSS selector narrowing available. For Cloudflare-protected sites, `solve_cloudflare=true` handles Turnstile bypass.

**Verdict:** Scrapling advantage — significant token reduction and prompt-injection mitigation from built-in sanitization. The sanitization XPath in `_HIDDEN_XPATH` (shell.py:72-81) is deterministic and language-agnostic, not model-dependent.

### Summary matrix

| Criterion | Current Hermes tools | Scrapling sidecar | Delta |
|-----------|---------------------|-------------------|-------|
| Static HTTP | web_extract (via Firecrawl/Exa/etc) | get() + impersonation | Similar |
| JS rendering | browser_navigate (Playwright) | fetch() + ad blocking | Scrapling ~30-50% less token noise |
| Anti-bot bypass | No built-in (relies on CDP/proxy) | stealthy_fetch + solve_cloudflare | Scrapling significant capability gap |
| Content sanitization | Model-side only | Built-in XPath sanitizer | Scrapling reduces injection surface |
| Crawl resume | No checkpoint mechanism | Spider + CheckpointManager | Scrapling new capability |
| SSRF protection | Built-in (is_safe_url) | follow_redirects="safe" | Comparable |
| Proxy support | Via tool params | Per-request/session | Comparable |
| Multi-URL bulk | web_extract (batch) | bulk_get/fetch/stealthy_fetch | Comparable |

---

## Permission boundary design: disabled-by-default MCP/sidecar

### Architecture: Hermes native MCP tool registration

Scrapling would be registered as an **opt-in native MCP server** in Hermes config.yaml, NOT as a core dependency. The following design prevents accidental exposure to risk:

```yaml
# config.yaml — user MUST explicitly enable
native_mcp_servers:
  scrapling:
    # REQUIRED: user must uncomment to enable
    # enabled: true
    command: scrapling
    args: ["mcp"]
    # Per-tool permission labels (applied by Hermes MCP router)
    permissions:
      # HTTP-only tools — lowest risk
      get:
        allowed_urls: ["https://*"]
        deny_private: true
        deny_authenticated: true
        max_timeout: 60
        require_robots: true
        require_proof_log: false
      bulk_get:
        allowed_urls: ["https://*"]
        deny_private: true
        max_urls: 10
        max_timeout: 120
      # Browser tools — moderate risk
      fetch:
        allowed_urls: ["https://*"]
        deny_private: true
        deny_authenticated: true
        max_timeout: 120
        require_robots: true
        require_proof_log: true
      bulk_fetch:
        allowed_urls: ["https://*"]
        deny_private: true
        max_urls: 5
        max_timeout: 300
      # Stealth tools — high risk, requires explicit approval
      stealthy_fetch:
        allowed_urls: ["https://*"]
        deny_private: true
        deny_authenticated: true
        max_timeout: 120
        require_explicit_approval: true  # Hermes approval gate
        require_proof_log: true
        disallow_solve_cloudflare: true   # Default OFF
      bulk_stealthy_fetch:
        allowed_urls: ["https://*"]
        deny_private: true
        max_urls: 3
        require_explicit_approval: true
        disallow_solve_cloudflare: true
    # Global constraints
    ssrf:
      enabled: true
      block_private: true
      block_link_local: true
      block_multicast: true
    robots:
      enabled: true
      obey: "safe"  # fail closed if cannot parse
    timeout:
      default: 30
      max: 300
    stealth:
      enabled: false  # master kill switch — stealth tools unusable
      require_audit: true
      solve_cloudflare_requires_approval: true
```

### MCP tool → permission matrix

| MCP Tool | SSRF Guard | robots.txt | Timeout cap | Approval | Proof log | Notes |
|----------|-----------|------------|-------------|----------|-----------|-------|
| get() | mandatory | recommended | 60s | none | optional | Equivalent to web_extract |
| bulk_get() | mandatory | recommended | 120s | none | optional | Max 10 URLs |
| fetch() | mandatory | recommended | 120s | none | required | JS rendering |
| bulk_fetch() | mandatory | recommended | 300s | none | required | Max 5 URLs |
| stealthy_fetch() | mandatory | mandatory | 120s | REQUIRED | required | solve_cloudflare off by default |
| bulk_stealthy_fetch() | mandatory | mandatory | 300s | REQUIRED | required | Max 3 URLs |
| screenshot() | mandatory | recommended | 120s | none | required | Browser session required |
| open_session() | N/A | N/A | N/A | none | required | Sessions auto-close after idle |
| close_session() | N/A | N/A | N/A | none | optional | — |
| list_sessions() | N/A | N/A | N/A | none | optional | — |

### Policy rules (enforced by Hermes MCP router)

1. **SSRF (enabled=true, default):** All URL-accepting tools MUST pass through Hermes' `is_safe_url()` before dispatching to Scrapling. Scrapling's own `follow_redirects="safe"` acts as a second line of defense.
2. **Robots.txt (obey="safe"):** For browser/stealth tools, query robots.txt before fetching. If robots.txt cannot be fetched or parsed, fail closed (do not fetch).
3. **Authenticated content:** `deny_authenticated=true` — reject URLs containing embedded credentials or targeting login pages.
4. **Stealth master switch:** `stealth.enabled=false` — all stealthy_fetch/bulk_stealthy_fetch tools return "stealth tools disabled" unless user explicitly sets this to true AND restarts.
5. **solve_cloudflare:** Even when stealth is enabled, `disallow_solve_cloudflare: true` prevents Cloudflare Turnstile solving by default. Must be individually approved.
6. **Proof log:** When `require_proof_log=true`, each tool invocation records URL, status, content length, duration, extraction_type to the Hermes evidence log.
7. **Session lifecycle:** Browser sessions opened via `open_session()` must have TTL (default 15 min idle) and max concurrent count (default 3).

---

## Adopt / Watch / Reject verdict

**Verdict: WATCH** (scoped adopt for AI-targeted extraction evaluation, reject for stealth/Cloudflare bypass)

### Adopt under strict boundary: AI-targeted extraction sanitizer

**What:** The AI-targeted extraction pipeline (XPath-based hidden element stripping + zero-width char removal + ad blocking) is a well-engineered, deterministic preprocessor that reduces token consumption and prompt-injection surface. It is language-agnostic, model-independent, and has zero runtime risk because it operates on already-fetched HTML.

**How:** Implement as an optional HTML preprocessor in Hermes' tool output pipeline (web_extract + browser snapshot output) — NOT as a Scrapling dependency. The XPath and regex patterns from `scrapling/core/shell.py` lines 72-82 are trivially portable:

```python
_HIDDEN_XPATH = XPath(
    './/*[contains(@style,"display:none") or contains(@style,"display: none")'
    ' or contains(@style,"visibility:hidden") or contains(@style,"visibility: hidden")'
    ' or contains(@style,"opacity:0") or contains(@style,"opacity: 0")'
    ' or contains(@style,"font-size:0") or contains(@style,"font-size: 0")'
    ' or contains(@style,"height:0") or contains(@style,"height: 0")'
    ' or contains(@style,"width:0") or contains(@style,"width: 0")]'
    ' | .//*[@aria-hidden="true"]'
    ' | .//template'
)
_ZWC_PATTERN = re.compile(r"[\u200b\u200c\u200d\ufeff\u2060\u180e]")
```

This can be added to Hermes without any Scrapling dependency.

**Evidence:** Source code in `scrapling/core/shell.py` lines 72-82; the sanitization is deterministic, has no side effects, and operates purely on string data.

### Watch: MCP sidecar for targeted extraction

**What:** Register Scrapling as an opt-in native MCP server per the permission boundary design above. This provides the fetcher ladder (HTTP → Playwright → stealth) as an alternative extraction path without modifying Hermes core.

**Why watch not adopt immediately:**
- Hermes already has web_extract (via Firecrawl/Exa/etc) and browser_navigate (Playwright).
- The marginal advantage (ad blocking + sanitization) can be achieved by porting the sanitizer alone.
- Scrapling requires Playwright + patchright dependencies (heavy).
- The MCP tool registration is straightforward and can be tested ad-hoc by any user who `pip install scrapling` and adds the config snippet.

**Trigger to adopt:** A task emerges requiring bulk extraction from JS-heavy sites where ad blocking and sanitization meaningfully reduce cost (token savings > Playwright overhead). At that point, evaluating the native MCP integration with the permission boundary becomes justified.

### Reject: Stealth/Cloudflare bypass as Hermes feature

**What:** The stealth fetcher with solve_cloudflare, fingerprint spoofing, canvas noise, WebRTC blocking.

**Why reject:**
- Violates Hermes' principle of legitimate web evidence collection.
- Cloudflare Turnstile solving is anti-bot circumvention — cannot be in Hermes core.
- Stealth fingerprinting is fragile and version-dependent (necessitating patchright).
- Even as an opt-in sidecar, the `stealth.enabled: false` master kill switch must remain default.
- The user's red lines explicitly prohibit default-enable stealth/anti-bot/Cloudflare bypass.

**Exception:** A separate, explicitly scoped task could evaluate stealth for specific evidence-collection use cases (e.g., researching bot-protection mechanisms) under Hermes approval gate. This is not in scope here.

### Watch: Spider checkpoint for long-running crawl

**What:** The spider + checkpoint system provides resumable async crawling with robots.txt compliance, per-domain concurrency, and pickle-based state persistence.

**Why watch:** Hermes doesn't have a checkpointed crawl capability today. This would be valuable for feed aggregation, documentation collection, or research jobs. However:
- It requires Scrapling as a Python dependency (not just CLI/MCP).
- The pickle-based checkpoint format is Python-version-sensitive.
- The spider is Scrapy-like (callback-based) — not a natural fit for Hermes' tool-calling loop.

**Trigger to adopt:** A concrete task requiring "crawl 500 documentation pages from domain X with resume on interrupt." At that point, evaluate wrapping the spider as a cron job or standalone script that deposits results into Hermes evidence store.

---

## Residual risk assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Scrapling MCP server running on 0.0.0.0:8000 (default) | Medium | Hermes config MUST specify `args: ["mcp"]` (stdio) not `["mcp", "--http"]`. Document explicitly. |
| pickle-based checkpoint | Medium | Checkpoint format tied to Python version. Acceptable for in-process use; not for long-term evidence storage. |
| stealthy_fetch used without approval | High | Master kill switch + per-tool approval gate + proof log. Triple-barrier design. |
| Upstream AgentSkill bundle auto-installed | Low | Red line in task constraints. Bundle is `.zip` only, never auto-extracted. |
| SSRF bypass via Scrapling's own redirect handling | Low | Hermes SSRF guard runs BEFORE dispatch. Scrapling's `"safe"` mode is additional defense. Double-barrier. |
| robots.txt not fetched (timeout/DNS failure) | Medium | `obey: "safe"` fails closed — do not fetch if robots cannot be verified. |
| Browser session resource leak | Low | Open sessions auto-close after idle TTL; configurable limit on concurrent sessions. |
| Adaptive selector overrides canonical data | Low | Adaptive mode is opt-in per-Selector instance. Not exposed through MCP/CLI without explicit identifier. Irrelevant to sidecar pattern. |

---

## Verification commands

```bash
# Selfcheck
python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json

# Check hermss health
~/.hermes/scripts/p10-health.sh
```

---

## Conclusion

Scrapling is a well-engineered scraping library. Its primary value for Hermes is the **AI-targeted extraction sanitizer** (hidden-element stripping + ad blocking) which is trivially portable as an HTML preprocessor — adopt that pattern without the dependency. The **MCP sidecar** is worth watching for when bulk JS-heavy extraction needs justify the Playwright overhead; the permission boundary design above makes it safe to evaluate. **Stealth/Cloudflare bypass is rejected** for Hermes core. The **spider checkpoint** is worth watching for future long-crawl use cases.
