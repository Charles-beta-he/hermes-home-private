# Scrapling checkpoint / pause-resume fixture evidence (2026-06-11)

Generated: `2026-06-11T09:50:28.613596+00:00`

## Boundary
- targets: `['https://example.com/', 'https://www.python.org/about/']`
- public_https_only: `True`
- robots_txt_obey: `True`
- no_private_or_authenticated_targets: `True`
- no_browser_fetcher: `True`
- no_stealth_or_cloudflare_bypass: `True`
- no_hermes_core_dependency_change: `True`

## Result
- status: `PASS`
- first run paused: `True`; checkpoint files: `['checkpoint.pkl']`
- resume flag seen: `True`; second run completed: `True`
- first URLs: `['https://example.com/']`
- resumed URLs: `['https://www.python.org/about/']`
- checkpoint cleaned after completion: `True`

## JSON evidence
- artifact:/Users/charles/.hermes/runs/scrapling-revisit-20260611/checkpoint_resume_results.json

## Verdict
Scrapling Spider crawldir checkpoint/pause-resume is viable for a disabled-by-default Hermes evidence sidecar prototype when constrained to public HTTPS, robots-aware, non-browser fetching. This is still not approval to integrate as a core dependency or enable stealth/anti-bot behavior.