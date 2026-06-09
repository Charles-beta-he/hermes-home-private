# CloakBrowser browser-harness / taskpool risk review

Date: 2026-06-09
Task: Task - 评估 CloakBrowser 对 Hermes 浏览器执行链的合规收益与风险边界
Boundary: hermes-browser-harness-cloakbrowser-risk-review
Recommendation: docs-only now; sandbox-spike only behind explicit owned/synthetic-surface approval. No implementation/default integration.

## Scope and execution boundary

This review grounded CloakBrowser claims against Hermes browser-harness and taskpool truth-gate needs without installing CloakBrowser, running its binary, launching Docker, using proxies, or visiting third-party detection/CAPTCHA services.

Evidence gathered:
- Existing intake note: `/Users/charles/.hermes/docs/private/video-intake-cloakbrowser-2026-06-09.md`.
- Local shallow clone for read-only inspection: `/tmp/agent-team-2026-06-09-task------clo-cfb1bdc621a8/repo-review/CloakBrowser`.
- CloakBrowser commit reviewed: `b06499b0c15e1f988db0bbbd001831e88e9b483b` (`test(humanize): deterministic timing for password CDP test`, 2026-06-09T17:38:09+02:00).
- Hermes repo sources reviewed: browser tool truth-gate tests and Camofox backend code under `/Users/charles/.hermes/hermes-agent`.

Non-evidence / explicitly not done:
- No claim that CloakBrowser actually passes the listed detection sites was independently verified.
- No binary/package/proxy/daemon was installed or run.
- No third-party site bypass, CAPTCHA bypass, account automation, scraping, or ToS-evasion test was performed.

## Objective model / path gate

Success criteria:
1. Repo/package architecture review note exists and names concrete files, claims, and uncertainty.
2. Safety matrix distinguishes permitted owned/synthetic QA from prohibited anti-bot abuse.
3. Hermes impact map covers browser harness, evidence truth gate, taskpool intake/lifecycle, observability/provenance, and browser profile/vector-state SSOT boundary.
4. Recommendation is risk-gated and keeps implementation evidence-gated.

Constraints / red lines:
- No CAPTCHA bypass, account farming, scraping third-party services, or ToS evasion.
- No proxy/daemon/binary install during intake.
- Do not weaken taskpool proof, permission, mission-envelope, or lifecycle gates.
- Do not treat browser profile, retrieval, or vector state as taskpool SSOT.

Chosen path:
- Read-only repository/package/source review plus Hermes code/test review.
- Produce docs-only recommendation with optional future sandbox-spike requirements.

## CloakBrowser repo/package architecture review

### Public positioning and package surface

The README positions CloakBrowser as “Stealth Chromium that passes every bot detection test” and a drop-in Playwright/Puppeteer replacement. It explicitly claims:
- A custom Chromium binary with source-level C++ fingerprint patches rather than only JS injection or config flags (`README.md` lines 23-49, 244-258).
- 58 source-level patches across canvas, WebGL, audio, fonts, GPU, screen, WebRTC, network timing, automation signals, and CDP input behavior (`README.md` lines 43, 253).
- `humanize=True` replacing fast Playwright/Puppeteer actions with human-like mouse/keyboard/scroll timing (`README.md` lines 541-614).
- reCAPTCHA v3 score 0.9, Cloudflare Turnstile pass, FingerprintJS pass, BrowserScan normal, and 30+ live detection-site tests (`README.md` lines 183-229).
- Anti-bot operating advice using residential proxies, GeoIP matching, headful mode, and humanized interactions (`README.md` lines 78-98).

Package metadata reinforces the same risk profile:
- `pyproject.toml` marks keywords including `scraping`, `anti-detect`, `recaptcha`, `cloudflare`, `turnstile`, `captcha`, `bot-detection`, `fingerprint`, and depends on `playwright>=1.40` + `httpx>=0.24`.
- `js/package.json` exports Playwright/Puppeteer wrappers and uses similar anti-detect keywords; peer dependencies include `playwright-core`, `puppeteer-core`, optional `mmdb-lib` and `socks-proxy-agent`.

### Runtime architecture observed from source

Primary Python surface:
- `cloakbrowser/browser.py` exposes `launch`, `launch_async`, `launch_context`, and `launch_persistent_context` wrappers around Playwright. Each calls `ensure_binary()` and launches Playwright with `executable_path` pointing at CloakBrowser’s patched Chromium.
- `build_args(...)` path injects stealth fingerprint flags and suppresses Playwright defaults such as `--enable-automation` and `--enable-unsafe-swiftshader` via `IGNORE_DEFAULT_ARGS` in `cloakbrowser/config.py`.
- `geoip=True` can resolve timezone/locale/WebRTC exit-IP alignment through proxy-mediated external HTTP calls (`README.md` lines 285-294; `browser.py` flow around `maybe_resolve_geoip`).
- Persistent context stores cookies/localStorage/cache/profile state across sessions and is explicitly framed as avoiding incognito detection and building realistic browsing history (`README.md` lines 377-386).
- `humanize=True` monkey-patches browser/page/context APIs so normal Playwright calls emit delayed, curved, per-character, actionability-aware interactions (`browser.py` lines 144-150, 364-369, 595-600; README lines 541-614).

Binary/download surface:
- `cloakbrowser/download.py` downloads a ~200MB patched Chromium into `~/.cloakbrowser` by default, with fallback from `cloakbrowser.dev` to GitHub Releases.
- Checksum verification exists but has escape hatches: if `CLOAKBROWSER_SKIP_CHECKSUM=true`, verification is disabled; if checksums are missing or do not list the tarball, code logs a warning and continues (`download.py` lines 165-188).
- Auto-update checks are built into `ensure_binary()` unless disabled; this is an external supply-chain and reproducibility consideration.
- `BINARY-LICENSE.md` says the wrapper source is MIT, but the compiled Chromium binary has a separate proprietary license restricting redistribution, reverse engineering, modification, and OEM/SaaS embedding. It permits internal use but says hosted service / third-party serving requires a separate OEM/SaaS license.

Tests/examples:
- `tests/test_stealth.py` includes local browser-signal assertions plus slow live tests against bot-detection services, FingerprintJS, reCAPTCHA, and Cloudflare-like/anti-bot surfaces. These are project claims/tests, not Hermes acceptance evidence because this task intentionally did not run them.
- Examples include `examples/recaptcha_score.py`, `examples/fingerprint_scan_test.py`, proxy arguments, and third-party detection targets. These are high-risk examples under Hermes red lines.
- CI (`.github/workflows/publish.yml`) runs Python tests with `pytest tests/ -v -m "not slow"` and JS tests; the live detection tests are excluded from normal CI by marker.

### Architecture judgment

CloakBrowser is not just a browser-profile manager or testing convenience. It is an anti-detection browser distribution plus wrapper layer, with explicit features for hiding automation, spoofing/cohering fingerprints, aligning proxy geography, persisting realistic profiles, and humanizing automation. That can be technically relevant to Hermes browser-harness reliability, but the default semantics conflict with Hermes evidence-governance unless tightly constrained.

## Hermes current-state review

### Browser harness truth gates already present

Hermes browser tooling currently has explicit truth-gate behavior:
- `tools/browser_tool.py` wraps browser snapshots with an untrusted-content header, caps prompt size, detects prompt-injection text, and classifies anti-bot/Cloudflare pages as `validation_status=degraded` with `degraded_reason=anti_bot_or_cloudflare_challenge`.
- `tests/tools/test_browser_snapshot_truth_gate.py` verifies prompt-injection degradation, anti-bot challenge degradation, auth/unreachable classification, and propagation of truth-gate metadata into Camofox snapshots.
- `tools/browser_camofox.py` is already an optional anti-detection backend behind `CAMOFOX_URL`, not default. It routes through the same snapshot validation machinery.
- `tools/browser_camofox_state.py` stores optional profile-scoped persistent browser identity under profile-local state, but this is browser state only, not task lifecycle authority.

### Taskpool truth gates and SSOT

The local taskpool control plane is markdown/task-note canonical and fail-closed:
- `/Users/charles/.hermes/scripts/brain_task_orchestrator.py` states markdown task notes are canonical and dashboards/queue views are derived.
- Mission envelopes require evidence refs, acceptance criteria, red lines, non-goals, and certification fields.
- Project profile `/Users/charles/.hermes/project-profiles/hermes.json` weights external repos/trend artifacts at 0.55 until mapped to Hermes primitives with reproducible evidence, while runtime selfcheck/proof/evidence-spine output has highest authority.

Implication: CloakBrowser-derived browser success must never upgrade task lifecycle status by itself. It can at most add one labeled browser-evidence artifact, subject to the same truth-gate metadata and mission-envelope constraints.

## Safe / unsafe use matrix

| Use case | Status | Required boundary | Why |
|---|---:|---|---|
| Read-only repo/package review | SAFE | No install/run; cite files/commits | Current task scope. |
| Docs-only policy note on anti-bot evidence classification | SAFE | No runtime behavior change | Improves worker guidance without adding stealth capability. |
| Synthetic local challenge fixture owned by Hermes | SAFE WITH GATE | Local-only fixture, no third-party domains, no proxy, no real CAPTCHA | Can test truth-gate classification and observability without evasion. |
| Owned/consented staging site QA where anti-bot blocks legitimate internal acceptance | SAFE WITH STRICT GATE | Written owner approval, domain allowlist, no CAPTCHA/account abuse, evidence labels, no default enablement | May diagnose false negatives while preserving permission and provenance. |
| CloakBrowser as default browser backend | UNSAFE | Reject | It normalizes stealth/evasion and can hide anti-bot blocks that Hermes should report honestly. |
| Replacing degraded anti-bot classification with stealth retry | UNSAFE | Reject | Weakens truth-gate evidence by converting a blocker into unproven success. |
| CAPTCHA/Turnstile/reCAPTCHA bypass on third-party services | PROHIBITED | Block | Direct red-line violation. |
| Residential proxy + GeoIP matching for third-party scraping | PROHIBITED | Block | ToS/abuse/evasion risk and contrary to task red lines. |
| Account creation/login farming, credential stuffing, or auth circumvention | PROHIBITED | Block | Legal/abuse red line and also prohibited by CloakBrowser binary license. |
| Persistent browser profile as taskpool state/lifecycle proof | PROHIBITED | Block | Browser state is not canonical task state or lifecycle authority. |
| Auto-installing CloakBrowser binary/Docker/manager during intake | PROHIBITED | Block | Explicit task red line; supply-chain and daemon risk. |
| Hosted browser-as-a-service integration for third-party users | BLOCKED | Legal/licensing review needed | Binary license requires separate OEM/SaaS license. |

## Hermes impact map

### Browser harness

Potential benefit:
- CloakBrowser’s architecture highlights capability gaps Hermes can represent more safely as observability: detection fixture taxonomy, browser-signal probes, explicit anti-bot boundary labels, and separation between `rendered page verified` vs `challenge/interstitial reached`.

Risk:
- If wired as a fallback backend, it may make browser tools “succeed” by evading site defenses rather than honestly reporting anti-bot friction. That would degrade acceptance proof.

Boundary:
- Keep current default: local Chromium / configured cloud providers / optional explicit Camofox mode. Do not add CloakBrowser as default or automatic fallback.

### Evidence truth gate

Potential benefit:
- Add documentation/tests that any browser backend, including anti-detection backends, must still surface `validation_status`, `degraded_reason`, prompt-injection metadata, URL/proxy/profile provenance, and backend identity.

Risk:
- A stealth backend could hide `anti_bot_or_cloudflare_challenge` evidence. Hermes should not interpret “page loaded” as “business flow passed” without route/action/content assertions.

Boundary:
- A future spike must assert that stealth mode cannot suppress untrusted-content wrapping, token caps, screenshot/DOM provenance, or failed-auth/unreachable classifications.

### Taskpool intake/classification

Potential benefit:
- Add intake language that classifies anti-detect browser repos as reference-only / high-risk until an owned-surface sandbox plan exists.

Risk:
- Trend/social claims and screenshots can look like proof. Project profile says external repo/trend artifacts are lower authority until mapped to reproducible Hermes evidence.

Boundary:
- Taskpool acceptance should require repo note + safety matrix + impact map, not an implementation or lifecycle transition.

### Observability/provenance

Potential benefit:
- If any future backend is evaluated, log backend name/version/commit, binary source/hash, install path, auto-update disabled/enabled, proxy usage (without secrets), target domain class, profile persistence mode, and evidence artifact paths.

Risk:
- External binary auto-download/update and checksum-skip knobs create reproducibility and supply-chain gaps.

Boundary:
- Future sandbox must pin version/source and disable auto-update for test reproducibility; no secret/proxy values in artifacts.

### Profile/vector/SSOT boundary

Potential benefit:
- Persistent browser profiles can make manual QA sessions repeatable when explicitly scoped.

Risk:
- Browser cookies/history/localStorage or vector retrieval can be mistaken for canonical task status.

Boundary:
- Browser profile state is runtime evidence only. Canonical lifecycle remains markdown task note + orchestrator transitions + proof artifacts.

## Recommendation

Recommendation: docs-only now.

Do not implement CloakBrowser integration from this intake. Do not install or run it. Do not add stealth-bypass as a default browser capability.

Allow only a future sandbox-spike proposal if all gates below are satisfied:
1. Target is owned, local, synthetic, or written-consented staging surface; no third-party CAPTCHA/detection service, no account farming, no scraping, no ToS evasion.
2. Scope is diagnostic: compare truth-gate classification and evidence provenance, not bypass success.
3. CloakBrowser version/source/binary hash is pinned; auto-update disabled; no proxy unless explicitly approved for an owned lab.
4. Test asserts Hermes still emits untrusted-content wrapper, `validation_status`, `degraded_reason` when applicable, console/network/screenshot evidence, and backend provenance.
5. Taskpool closeout remains evidence-gated and cannot be advanced by browser/profile/vector state alone.
6. Legal/licensing review happens before any bundled/hosted/SaaS use because the binary license is not the same as the MIT wrapper license.

Smallest maintainable next step, if desired later:
- Add a Hermes docs/skill note for “anti-bot boundary evidence classification” and a pure unit fixture asserting that every browser backend must report backend/provenance + truth-gate metadata. This is docs/test-only and does not require CloakBrowser installation.

## Verification log

Commands actually run for this review:
- `git -C /Users/charles/.hermes status --short && git -C /Users/charles/.hermes/hermes-agent status --short --branch`
- `python3 /Users/charles/.hermes/scripts/brain_task_orchestrator.py list --json`
- `git clone --depth 1 https://github.com/CloakHQ/CloakBrowser.git /tmp/agent-team-2026-06-09-task------clo-cfb1bdc621a8/repo-review/CloakBrowser`
- `git -C /tmp/agent-team-2026-06-09-task------clo-cfb1bdc621a8/repo-review/CloakBrowser rev-parse HEAD`

Validation result:
- `brain_task_orchestrator.py list --json` returned `status: OK`, `task_count: 0` at 2026-06-09T23:59:09+08:00.
- This task remains evidence-gated before implementation; no implementation was performed.
