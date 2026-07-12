# H5 right-edge header controls and viewport proof

Use when a mobile H5/PWA header has left menu/search plus right-side actions (message, customer service, scan, wallet, etc.) and screenshots show the right controls missing, clipped, or hidden behind the search field.

## Applicability

- Mobile H5/PWA or WebView surfaces with fixed/absolute header controls near the right edge.
- Visual parity tasks where acceptance depends on controls being visible in 375/390/414px mobile widths.
- Headless Chrome screenshot workflows where `--window-size=390,844` is used as evidence.

## Anti-conditions

- Do not apply this as a reason to globally cap desktop/tablet layouts to 390px.
- Do not replace real device/WebView verification with this when the acceptance target is a physical device or native shell.
- Do not store project-specific routes, ports, or screenshots here; keep those in the project ledger/profile.

## Debugging path

1. **Reproduce with visual proof first.** Capture the failing mobile-width screenshot and confirm whether the missing control is actually absent from pixels, not just absent from the accessibility tree.
2. **Check DOM existence separately.** Dump or inspect the rendered DOM for `aria-label`/buttons and the header subtree. If DOM exists but pixels are absent, treat it as layout/viewport/paint, not routing/data.
3. **Verify viewport truth.** `--window-size=390,844` can still produce a wider CSS/layout viewport depending on headless/browser emulation. Read `innerWidth`, `visualViewport.width/scale`, and button `getBoundingClientRect()` before trusting screenshot dimensions.
4. **Probe pixels at the right edge.** For a quick non-LLM check, count dark/icon pixels in the top-right header band and record the bbox, then still inspect the screenshot visually before claiming UI acceptance.
5. **Avoid broad component rewrites.** If a generic Header component is shared, prefer a page-scoped header/layout fix unless the shared component contract is explicitly under test.
6. **Bound right-edge controls to the intended H5 canvas.** When the layout viewport is wider than the captured/mobile target, position the right action group relative to the intended canvas width (for example a max H5 canvas width) and size the search field so it cannot cover that action group.
7. **Verify multiple widths.** At minimum verify 375x812, 390x844, and 414x896 for iPhone-like H5 acceptance; for Android/HarmonyOS add the project’s short-browser viewport if available.
8. **Do not certify on visibility alone.** Visual visibility proves the layout slice; click-through route smoke and business/API state remain separate gates.

## Evidence checklist

- [ ] Screenshot before fix showing missing/clipped right controls.
- [ ] DOM readback proving whether the controls were rendered.
- [ ] Viewport readback (`innerWidth`, `visualViewport`, or equivalent) when headless evidence is used.
- [ ] Screenshot after fix at the primary mobile width.
- [ ] Pixel bbox or equivalent deterministic readback for right-edge controls.
- [ ] At least two adjacent mobile widths verified.
- [ ] Targeted lint/build or equivalent compile gate passed.
- [ ] Ledger/report states whether click-through route smoke is complete or still open.
