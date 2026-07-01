# Mobile Reference 1:1 Absorption Workflow

Use when a user asks to learn/clone/1:1 restore a Behance/Dribbble/Figma/mobile-product reference rather than merely make a screen "in that style".

## Core correction

Do not mix multiple references on the visible UI. A mixed synthesis can look like a generic AI app but will fail a 1:1 review. Lock one canonical source and one target screen before editing.

## Workflow

1. **Reference lock**
   - Pick one product, one URL, one exact screen as the visible UI master.
   - Write a `REFERENCE_LOCK.md` with source URL, local screenshots, target screen, and anti-conditions.
   - Auxiliary references may feed product-thinking docs only; they must not affect rendered UI without a new lock.

2. **Reference capture**
   - Download full-resolution reference images when allowed by the site.
   - Build a contact sheet so the target screen is selected from actual assets, not search-result thumbnails.
   - Keep copyright boundaries explicit: reproduce layout/hierarchy/interaction/token feel, not proprietary art/logo/assets.

3. **Screen map before code**
   - Create a machine-readable screen map (`screen-map.json`) with approximate viewport, safe-area, top chrome, hero/orb/avatar, text block, controls, composer/sheet areas, colors, radius, spacing, and typography.
   - Do not begin by tuning colors. First match layout ownership and component hierarchy.

4. **Product interaction extraction**
   - Record what each component means in the reference product: avatar presence, listening hint, task text, mic fast lane, side controls, prompt chips, history, settings/details.
   - Map these roles to the local product domain. Keep implementation lanes (online/local/cache/server) out of the main user experience unless the reference itself exposes modes.

5. **Implementation rules**
   - Replace existing product copy and state, but keep the reference layout contract.
   - Move mismatching engineering/status/diagnostic surfaces to secondary details/sheets if the reference screen does not show them.
   - If a composer or prompt chips are not present on the target reference screen, do not keep them on the main canvas just because the app previously had them.

6. **Visual verification loop**
   - Capture the app screenshot at the same device class and orientation.
   - Compare against the reference screen for: top chrome, hero/avatar size/position, main text width/line breaks, control count/shape/position, background glow, and absence of non-reference surfaces.
   - Fix the largest 3 visual deltas per iteration. Do not claim 1:1 after a single pass.

## Pitfalls

- **Style-synthesis trap:** combining Velo-like orb, FlowMate task cards, and Niva assistant copy creates a plausible but non-1:1 result.
- **Engineering-surface leak:** queue cards, diagnostics, provider names, offline/local/online modes, dry-run details, and reset/sync controls usually belong in details, not in a consumer AI reference screen.
- **Search-thumbnail trap:** search result thumbnails are not enough. Use full reference images and a contact sheet.
- **Asset-copy trap:** never copy proprietary logos, icons, or artwork; recreate owned shapes and use local product copy.
- **Screenshot mismatch trap:** if the screenshot shows the OS home screen or splash instead of the app, do not treat it as visual verification; relaunch/read back the app and recapture.

## Evidence checklist

- [ ] `REFERENCE_LOCK.md` written or updated.
- [ ] Local reference screenshot(s) saved and contact sheet created.
- [ ] `screen-map.json` written before large UI edits.
- [ ] Rendered app screenshot captured after release/dev build.
- [ ] Tests/lint/build run for the changed app.
- [ ] Remaining 1:1 gaps listed explicitly.
