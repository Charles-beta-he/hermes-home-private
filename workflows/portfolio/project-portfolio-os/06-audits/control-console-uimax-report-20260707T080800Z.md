# Hermes Control Console uIMax Audit — 2026-07-07T08:08Z

Scope: local-only UI quality audit for `/Users/charles/Desktop/folder/hermes-control-console` using fresh harness artifacts. No implementation edits, no deploy, no push.

## Evidence

- Full verification log: `/Users/charles/.hermes/workflows/portfolio/project-portfolio-os/06-audits/control-console-pnpm-verify-20260707T065500Z.log`
- UI harness summary: `/Users/charles/Desktop/folder/hermes-control-console/artifacts/ui-harness/2026-07-07_06-47-32-415/summary.json`
- Human inbox summary: `/Users/charles/Desktop/folder/hermes-control-console/artifacts/human-inbox-harness/2026-07-07_06-48-19-715/summary.json`
- Desktop screenshot audited: `/Users/charles/Desktop/folder/hermes-control-console/artifacts/ui-harness/2026-07-07_06-47-32-415/desktop-14/initial.png`
- Mobile screenshot audited: `/Users/charles/Desktop/folder/hermes-control-console/artifacts/ui-harness/2026-07-07_06-47-32-415/mobile-short/initial.png`
- Human inbox screenshot audited: `/Users/charles/Desktop/folder/hermes-control-console/artifacts/human-inbox-harness/2026-07-07_06-48-19-715/desktop-14/human-inbox.png`

## Harness readback

- `pnpm verify`: PASS
- browser topology harness: PASS, issueCount 0
- human-inbox harness: PASS, issueCount 0
- desktop/tablet/mobile consoleCount: 0
- desktop/tablet/mobile pageerrorCount: 0
- desktop/tablet/mobile requestfailedCount: 0

## Code quality metrics

- ARIA attributes: 94
- tabIndex occurrences: 0
- focus/focus-visible CSS rules: 22
- inline style occurrences in TSX: 11
- `<span onClick>` occurrences: 0
- prefers-reduced-motion rules: 5

## Scores

| Dimension | Grade | Evidence / rationale |
|---|---:|---|
| Visual design | B+ | Polished dark operator-console aesthetic, strong neon/semantic status colors, consistent rounded cards. Density is intentionally high but visually heavy. Long engineering titles/paths create cognitive load. |
| Responsiveness | B | Mobile layout is functional single-column and harness passes, but the full-page mobile capture is extremely long and dense; primary operator tasks require substantial scroll. Sticky/full-page capture shows repeated header-like regions, likely acceptable as a screenshot artifact but not A-level mobile IA. |
| Accessibility | A- | Strong ARIA coverage, zero clickable-span anti-patterns, focus styling present. No tabIndex hacks. Needs manual keyboard-flow proof before A+. |
| Code quality | B+ | Low TSX inline style count (11), no span-onClick, reduced-motion present. A would require further inline-style/CSS-var cleanup and explicit style-token report. |
| Interaction | B+ | Browser harness exercises topology and human-inbox flows with issueCount 0. Visual affordances for action buttons are clear. Some operator actions remain dense and require expert context. |
| Console health | A | Harness reports zero console errors, page errors, and request failures across tested viewports. |

Overall grade: **B+ / local-operator-ready**

This is not an A+ or uIMax-final claim. It is a strong local operator-console pass with known information-density and mobile IA limits.

## P0 issues

None found in the audited local harness evidence.

## P1 issues

1. **Mobile information density / scroll burden**
   - Evidence: mobile full-page screenshot is extremely long and dense.
   - Impact: mobile can inspect state but is not yet an elegant command-center experience.
   - Recommended next slice: add mobile section jump nav or collapsible groups for Mission / Human Inbox / Runtime Health / Graph.

2. **Engineering-copy leakage in primary cards**
   - Evidence: long paths, task ids, internal command snippets, and dense gate labels are visible in primary viewport.
   - Impact: acceptable for operator/debug console, not polished end-user UI.
   - Recommended next slice: keep raw paths behind disclosure or copy buttons; surface concise titles and risk labels first.

3. **Manual keyboard-flow proof missing**
   - Evidence: code/harness indicate accessibility support, but this audit did not record a human/Playwright tab-order trace.
   - Impact: blocks A+ accessibility claim.
   - Recommended next slice: add Playwright keyboard traversal assertion for top controls and Human Inbox action buttons.

## P2 issues

1. Reduce remaining TSX inline styles from 11 to lower single digits if easy.
2. Add explicit contrast-token audit if aiming for A/A+.
3. Add screenshot diff baseline to prevent future dashboard-density regressions.

## Boundary statement

- No project implementation edits were made for this uIMax report.
- No deploy/push/external dispatch was performed.
- This report supports `validated-local-operator-ui`, not production A+ visual acceptance.
