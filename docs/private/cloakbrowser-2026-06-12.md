# Durable Evidence: CloakBrowser Evaluation for Hermes
Date: 2026-06-12
Source: https://github.com/CloakHQ/CloakBrowser (clone at ~/.hermes/runs/cloakbrowser-reference-review-2026-06-12/)
Task: eval-cloakbrowser-hermes-combined-compliance-20260609

## Summary
Evaluated CloakBrowser (v0.3.31, 25k GitHub stars) as a potential browser backend for Hermes.
**Recommendation: DOCS-ONLY** — do not integrate as browser backend. Extract MIT-licensed humanization patterns for own harness. Document detection-axis taxonomy.

## Key Findings
1. **Architecture**: CloakBrowser is a custom-patched Chromium binary (proprietary) wrapped in MIT-licensed Playwright shims. 58 claimed C++ patches — not source-verifiable.
2. **License**: MIT wrapper + proprietary binary. Binary redistribution prohibited without OEM license. Hermes Docker image cannot bundle it.
3. **Safety**: Direct constitutional red line conflict — stealth capability would let agent evade anti-bot detection on third-party sites.
4. **Risk**: Evidence truth-gate contamination if CloakBrowser-generated evidence is not provenance-labeled.
5. **Value**: Detection-axis taxonomy (canvas/WebGL/audio/WebRTC/network-timing/CDP-signals) is useful reference for Hermes browser-harness diagnostics.

## Artifacts Generated
- `/tmp/agent-team-2026-06-09-task------clo-cfb1bdc621a8/01-repo-architecture-review.md`
- `/tmp/agent-team-2026-06-09-task------clo-cfb1bdc621a8/02-safety-boundary-matrix.md`
- `/tmp/agent-team-2026-06-09-task------clo-cfb1bdc621a8/03-hermes-impact-map.md`
- `/tmp/agent-team-2026-06-09-task------clo-cfb1bdc621a8/04-recommendation.md`

## Red Line Compliance
- No CloakBrowser binary installed
- No third-party sites touched
- No proxy/daemon/binary install during intake
- No lifecycle decisions from vector/browser-profile state
- Taskpool proof/permission/mission-envelope gates unchanged
- No CAPTCHA bypass, account farming, ToS evasion recommended

## Verification
- Confirm Hermes source has zero CloakBrowser references
- Confirm Hermes browser tool is unchanged
- Taskpool selfcheck: PASS expected
