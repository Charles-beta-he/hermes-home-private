# RN/mobile redesign PRD before implementation

Scope: React Native / mobile avatar shells where the implementation is functional and verified, but the user rejects the visual direction as ugly, demo-like, or not product-grade.

Applicability:
- RN/PWA/mobile shell already has routes, tests, screenshots, and possibly an A/A+ verification packet.
- User feedback is about taste, product feel, or visual direction rather than a single broken control.
- The next action would otherwise be another round of local style tweaking in the same codebase.

Anti-conditions:
- Do not use this when the user asked for a small concrete UI fix.
- Do not overwrite RN/production code if the user asks to review a new design first.
- Do not treat an evidence grade (A/A+) as proof of taste acceptance.

Pattern:
1. Stop polishing the rejected visual language. A passing UI gate can still be aesthetically wrong.
2. Build a short PRD that names the problem in product terms: e.g. orb dominance, engineering-demo tone, weak information architecture, too much neon/glass, or diagnostic feel.
3. Define the new design thesis and non-goals before writing UI code. Example thesis: “Quiet OS” — calm personal assistant, task-first, low ornament, diagnostics hidden.
4. Produce a browser-viewable high-fidelity HTML prototype instead of immediately patching RN. Include:
   - one recommended direction;
   - 2–3 variants only if they expose real tradeoffs, not color swaps;
   - theme toggle if palette/tone is part of the decision;
   - primary mobile shell, bottom navigation, Settings, and diagnostics disclosure;
   - explicit statement that prototype data is sample/design data.
5. Verify the prototype in a browser: file exists, local server opens, console has no JS errors, key interactions work, and at least one visual inspection is performed.
6. Give the user a local URL plus file paths and ask them to choose a direction before RN implementation.
7. If approved or the user asks for full safe rollout, implement in RN/mobile slices: tests first → shared tokens/base shell → Home → top bar/bottom nav → Settings/diagnostics → secondary pages → screenshot matrix → production gate. Re-run the native test/gate after each visual-system slice, because cosmetic cleanup can invalidate route-copy tests.
8. Applicability: local RN/mobile shell redesigns where the user has rejected the taste and then asks to continue toward production readiness. Anti-condition: do not use these steps to claim external distribution or real-user release.
9. Run a real visual audit after reinstalling/rerendering the RN shell, not just unit tests. Check for legacy residue from the rejected direction: old top bars, decorative sensors/icons, dark diagnostic containers, low-contrast settings cards, and engineering words that survived in constants.
10. Treat Home-only proof as insufficient for production readiness. Verify Home plus Settings plus diagnostics disclosure; if simulator/device control is blocked, record that as a human permission gate instead of claiming full screenshot-matrix completion.

Pitfalls:
- Do not call the design “A+” just because tests and screenshot matrices pass. Use A+ for local evidence quality; taste acceptance is a separate human gate.
- Do not keep polishing inside the old skin after the user says it is ugly. First change the product thesis/IA, then code.
- Do not claim external release from local verification, simulator build/install/launch, or rollback proof. External distribution remains a human-authority gate for signing, credentials, channel choice, and distribution risk.
- If desktop/simulator automation cannot safely target the app under test, stop clicking and produce a DecisionPacket/ContinuationPacket with the exact screenshots/actions pending. Do not keep probing coordinates on unrelated foreground windows.

Minimum artifacts:
- `docs/design-redesign/<product>-redesign-prd.md`
- `docs/design-redesign/<product>-redesign-prototype.html`
- local URL from a static server for review
