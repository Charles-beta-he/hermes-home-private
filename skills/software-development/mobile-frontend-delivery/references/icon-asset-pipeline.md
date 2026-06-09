---
name: icon-asset-pipeline
description: Generate and maintain app icon assets for PWA, iOS, Android, and favicon targets from source artwork. Use when updating manifest icons, generating favicon sets, mapping native app icon packages to web targets, or cleaning SVG sources for production use.
triggers:
  - icon generation
  - favicon update
  - PWA icon
  - apple-touch-icon
  - manifest icons
  - app icon assets
  - icon-maskable
  - mipmap icons
  - AppIcon.appiconset
---

# Icon Asset Pipeline

Generate production icon assets for web (PWA/manifest), iOS, Android, and favicon targets from source artwork.

## When to use

- Updating PWA manifest icons from new design source files
- Mapping iOS `AppIcon.appiconset` or Android `mipmap-*` native icon packages to web targets
- Generating favicon sets (SVG + PNG multi-size)
- Cleaning production SVGs (removing shadow/stroke/filter for web use)
- Ensuring icon content fits within platform safe-area requirements
- Configuring PWA splash screen colors (background_color, theme_color) — see `references/pwa-splash-screen-config.md`
- Building splash screen animations (orb glow, logo reveal, tagline stagger) — see `references/splash-animation-implementation.md`

## Prerequisites

- Source artwork: either a high-res PNG (1024×1024+) or clean SVG
- macOS: `sips` for image resizing (built-in)
- Optional: `imagemagick` for complex compositing

## Step 1: Identify source files

When the user provides a native app icon package (iOS + Android), the source structure is typically:

```
app-icons/
  ios/AppIcon.appiconset/
    AppIcon-{20,29,40,58,60,76,80,87,120,152,167,180,1024}.png
    Contents.json
  android/
    mipmap-{mdpi,hdpi,xhdpi,xxhdpi,xxxhdpi}/
      ic_launcher.png          # square legacy
      ic_launcher_round.png    # round legacy
      ic_launcher_foreground.png  # transparent, dots centered in 66% safe area
      ic_launcher_background.png  # solid white
    mipmap-anydpi-v26/
      ic_launcher.xml          # adaptive icon (foreground + background)
      ic_launcher_round.xml
    ic_launcher-playstore.png  # 512×512, full composite (white bg + dots)
```

**Best source for each web target** (see Step 2 for size mapping):

| Web target | Best source | Why |
|---|---|---|
| apple-touch-icon (180) | `ios/AppIcon-180.png` | iOS squircle, no alpha, production-ready |
| icon-512 | `android/ic_launcher-playstore.png` | 512×512, full composite, white bg |
| icon-maskable (512) | `android/ic_launcher-playstore.png` | Content already in 66% safe area |
| icon-192 | `android/mipmap-xxxhdpi/ic_launcher.png` | 192×192, exact match |
| favicon-32/16 | `ios/AppIcon-1024.png` resized | Highest quality source for downscale |
| favicon.svg | Clean SVG from design source | Vector, no rasterization artifacts |

If no native package exists, use a single 1024×1024 PNG and resize for all targets.

## Step 2: Generate PWA icons

Standard PWA icon set (update paths to your project):

```bash
DST="./public"

# apple-touch-icon: iOS squircle (system adds own rounding)
cp app-icons/ios/AppIcon.appiconset/AppIcon-180.png "$DST/apple-touch-icon.png"

# icon-512: Android playstore composite
cp app-icons/android/ic_launcher-playstore.png "$DST/icon-512.png"

# icon-maskable: same as icon-512 (content in 66% safe area)
cp app-icons/android/ic_launcher-playstore.png "$DST/icon-maskable.png"

# icon-192: Android xxxhdpi exact size
cp app-icons/android/mipmap-xxxhdpi/ic_launcher.png "$DST/icon-192.png"

# favicon PNGs: resize from best high-res source
sips -z 32 32 app-icons/ios/AppIcon.appiconset/AppIcon-1024.png --out "$DST/favicon-32.png"
sips -z 16 16 app-icons/ios/AppIcon.appiconset/AppIcon-1024.png --out "$DST/favicon-16.png"
```

## Step 3: Clean SVG for favicon.svg

SVG sources from designers often include presentation elements that must be stripped for production web use. Common removals:

| Element | What to remove | Why |
|---|---|---|
| `filter` defs (drop shadow) | `<filter id="...">...</filter>` + `filter="url(#...)"` | Shadows are system-rendered, not baked |
| `stroke` rects (edge highlight) | `<rect ... stroke="url(#...)" .../>` | Edge effects are presentation, not brand |
| Unused gradient defs | `<linearGradient id="tileEdge">...</linearGradient>` | Only needed for removed stroke |

**Pattern for SVG cleanup** (Python with regex):

```python
import re

svg = open("source.svg").read()

# Remove filter definitions
svg = re.sub(r'<filter id="[^"]*".*?</filter>\s*', '', svg, flags=re.DOTALL)

# Remove filter usage attributes
svg = svg.replace(' filter="url(#tileShadow)"', '')

# Remove stroke rects (usually a second rect with stroke=)
svg = re.sub(r'<rect x="[^"]*".*?stroke="[^"]*".*?/>\s*', '', svg, flags=re.DOTALL)

# Remove unused gradient defs
svg = re.sub(r'<linearGradient id="tileEdge".*?</linearGradient>\s*', '', svg, flags=re.DOTALL)

with open("favicon.svg", "w") as f:
    f.write(svg)
```

Verify no shadow/filter/stroke references remain: `grep -c 'Shadow\|filter=\|stroke=' favicon.svg` should output `0`.

## Step 4: Brand/icon-mask.svg

If the project has `public/brand/icon-mask.svg`, it must match the favicon.svg design (same dot pattern, same colors) but may use a different viewBox size. When updating favicon.svg, also update icon-mask.svg to stay in sync.

For a 32×32 icon-mask.svg derived from a 1024×1024 SVG source:
- Scale factor: 32/1024 = 0.03125
- Translate to center: use `transform="translate(X Y) scale(S)"` on a `<g>` wrapper
- Keep the same radial gradient definition but adjust `gradientTransform` for the new coordinate space

## Step 5: Verify

```bash
# Check all icon dimensions
for f in public/apple-touch-icon.png public/icon-512.png public/icon-maskable.png \
         public/icon-192.png public/favicon-32.png public/favicon-16.png; do
  sips -g pixelWidth -g pixelHeight "$f" | tail -2
done

# Check SVG has no shadow/stroke artifacts
grep -c 'Shadow\|filter=\|stroke=' public/favicon.svg

# Visual check: open each icon and verify
# - White background (not black)
# - Blue/brand-colored dots
# - No baked-in shadow or stroke
# - Content within 66% safe area (not touching edges)
```

### Source integrity check (MD5)

After copying/generating, verify each deployed file matches its source exactly. This catches stale cache, partial copies, or accidental overwrite with wrong version:

```bash
# Compare deployed icons against source (macOS md5)
md5 public/icon-512.png public/icon-192.png public/apple-touch-icon.png public/icon-maskable.png
md5 app-icons/android/ic_launcher-playstore.png app-icons/android/mipmap-xxxhdpi/ic_launcher.png app-icons/ios/AppIcon.appiconset/AppIcon-180.png

# Expected: matching MD5 pairs per source-target mapping
```

If any MD5 mismatch: re-copy from source, do NOT trust the existing file. Common cause: someone re-ran the pipeline with a different source version, or the file was modified by an image optimizer after copy.

Also verify `icon-maskable.png` vs `icon-512.png` — when both derive from the same source (playstore composite), they should be identical. If they differ, one was sourced from the wrong version.

## Pitfalls

1. **Wrong source version**: Design packages often have multiple versions (dark bg, light bg, with/without shadow). Always verify the source has the correct background color BEFORE generating all sizes. Check with `sips -g pixelWidth -g pixelHeight` and visual inspection. Do not infer the intended icon variant solely from historical commits or brand-preview captions; if the user supplies a screenshot/report, first distinguish "wrong source artwork" from "platform fallback/cache" and confirm the target artwork explicitly.

2. **White-on-black vs black-on-white mix-up**: The most common error is using a dark-theme icon variant for web icons. Web icons often need light/white backgrounds. Verify by opening the source image and by checking the user's stated desired variant before reverting to a prior design.

3. **SVG shadow/filter left in**: Design SVGs commonly embed drop shadows for mockup presentation. These MUST be stripped for production. Always grep for `Shadow`, `filter=`, `stroke=` after cleanup.

4. **`execute_code` terminal() returns dict**: In `execute_code`, `terminal()` returns `{"output": "...", "exit_code": N}`, not a string. Access output via `result["output"]`, not `result.output`.

5. **`sips` on macOS only**: `sips` is macOS-built-in. On Linux, use `convert` (ImageMagick) or `ffmpeg`.

6. **favicon.svg size**: Keep under 20KB. Complex SVGs with many paths can exceed this. If so, consider a simplified version or just use PNG favicons.

7. **PWA manifest reference**: After updating icons, verify `manifest.json` (or `manifest.webmanifest`) references match the new filenames. Common fields: `icons[].src`, `icons[].sizes`, `icons[].type`, `icons[].purpose` (use `purpose: "any"` for regular launcher icons and `purpose: "any maskable"` for maskable icons). If the deployed site serves icon PNGs with long-lived or immutable cache headers, change the manifest icon URL when changing artwork, e.g. `/icon-512.png?v=YYYYMMDD-orb`; Android Chrome/WebAPK may otherwise keep a stale failed/fallback icon even after the PNG content changes.

8. **Android fallback-letter icon diagnostic**: A launcher icon rendered as a solid colored circle with initials (for example `UV`) is usually Android/Chrome fallback artwork, not the app's custom manifest icon. Before changing the design source, verify the live `manifest.webmanifest`, fetch each referenced `icons[].src` URL (including query strings), inspect HTTP status/content-type/cache headers, and open the fetched PNG bytes. If the live PNG is correct but the installed icon is fallback, suspect WebAPK/icon cache staleness and use versioned icon URLs plus reinstall/clear site data for validation.

9. **Apple-touch-icon HTML tag**: Ensure `<link rel="apple-touch-icon" href="/apple-touch-icon.png">` exists in `index.html` `<head>`.

9. **Stale workspace artifacts after icon work**: Icon updates often leave behind design reference directories (`branding/`, `install-promo/`, `tmp/`, screenshot PNGs). These are NOT code artifacts — check with `grep -rn 'dirname' src/ vite.config.ts index.html public/` to confirm no code references. If no references exist, they're safe to delete. Do NOT commit them — they bloat the repo and are design-team-local.

10. **Splash screen color mismatch**: `background_color` and `theme_color` in manifest control the PWA system splash screen, NOT the app's internal UI. Don't set them to app surface colors (`#F2F3F5`) — use the design spec values (e.g. `#FFFFFF` / `#1326FD`). The app TopBar/TabBar uses independent Tailwind tokens; Chrome handles the transition. TWO files must be updated together: `vite.config.ts` manifest AND `index.html` `<meta name="theme-color">` — they serve different purposes (system splash vs browser chrome). See `references/pwa-splash-screen-config.md` for full details and `references/splash-animation-implementation.md` for the animated splash component pattern.
