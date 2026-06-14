# Scrapling revisit prototype evidence (2026-06-11)

Generated: `2026-06-11T06:37:28.989988+00:00`

## Boundary

- targets: `public HTTPS only`
- no_stealth: `True`
- no_cloudflare_bypass: `True`
- no_browser_install: `True`
- no_private_or_authenticated_targets: `True`
- hermes_llm_processing: `False`

## GitHub read-back

```json
{
  "status_code": 200,
  "full_name": "D4Vinci/Scrapling",
  "stars": 62843,
  "forks": 6114,
  "license": "BSD-3-Clause",
  "updated_at": "2026-06-11T06:36:10Z",
  "pushed_at": "2026-06-07T18:42:12Z",
  "default_branch": "main"
}
```

## Two-URL comparison

| Case | URL | Hermes ok/chars/duration | Scrapling ok/status/text chars/h1/duration | Observation |
|---|---|---:|---:|---|
| static_minimal | https://example.com/ | False/187/12.871s | True/200/142/['Example Domain']/1.44s | selector read-back h1=['Example Domain']; text ratio scrapling/hermes=142/187; Hermes extract error=Blocked: URL targets a private or internal network address |
| public_docs | https://www.python.org/about/ | False/196/0.05s | True/200/4543/['Python is powerful... and fast; plays well with others; runs everywhere; is friendly & easy to learn; is Open.']/0.846s | selector read-back h1=['Python is powerful... and fast; plays well with others; runs everywhere; is friendly & easy to learn; is Open.']; text ratio scrapling/hermes=4543/196; Hermes extract error=Blocked: URL targets a private or internal network address |

## Samples and hashes

### static_minimal — https://example.com/

- Hermes sha256: `f63cc6bd6adcca4e96553c79e39cc90900e7727ab80668d2f5967dce8e22e453` chars=187 duration=12.871s
- Scrapling sha256: `d003f90bc10db991b76e6fb480123cfce2cbb2b2784abe687fccccfa7ecacad8` text_chars=142 duration=1.44s
- Hermes sample:
```text
{ "results": [ { "url": "https://example.com/", "title": "", "content": "", "error": "Blocked: URL targets a private or internal network address" } ] }
```
- Scrapling sample:
```text
Example Domain Example Domain This domain is for use in documentation examples without needing permission. Avoid use in operations. Learn more
```

### public_docs — https://www.python.org/about/

- Hermes sha256: `84569c4ae5ea89513060752a1146aadc1f8b7be44996a77ed9117b2213af3df3` chars=196 duration=0.05s
- Scrapling sha256: `b36ccca9f39aca9e9634a2ccbbd3f8715e97aa62e40bc61fe8d0f12b8dc681a5` text_chars=4543 duration=0.846s
- Hermes sample:
```text
{ "results": [ { "url": "https://www.python.org/about/", "title": "", "content": "", "error": "Blocked: URL targets a private or internal network address" } ] }
```
- Scrapling sample:
```text
About Python™ | Python.org Notice: This page displays a fallback because interactive scripts did not run. Possible causes include disabled JavaScript or failure to load scripts or stylesheets. Skip to content ▼ Close Python PSF Docs PyPI Jobs Community ▲ The Python Network Donate ≡ Menu Search This Site GO A A Smaller Larger Reset Socialize LinkedIn Mastodon Chat on IRC Twitter About Applications Quotes Getting Started Help Python Brochure Downloads All releases Source code Windows macOS Android Other Platforms License Alternative Implementations Documentation Docs Audio/Visual Talks Beginner's Guide FAQ Non-English Docs PEP Index Python Books Python Essays Community Diversity Mailing Lists IRC Forums PSF Annual Impact Report Python Conferences Special Interest Groups Python Logo Python Wi
```

## Decision

WATCH / prototype only: Scrapling HTTP Fetcher produced deterministic parse metrics and selector read-back on both public URLs, but this tranche did not install browser fetchers or prove pause-resume spider checkpoints. Keep disabled-by-default sidecar boundary; next step is a local fixture checkpoint-resume harness before any Hermes integration.

## Closeout gap

- Acceptance evidence for two public URL dry-run/read-back is satisfied by this artifact and JSON result.
- Not yet satisfied: spider checkpoint/pause-resume local fixture; no code/config integration should be marked done until that fixture exists and passes.