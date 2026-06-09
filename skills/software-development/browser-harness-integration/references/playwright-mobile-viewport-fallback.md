# Playwright Mobile Viewport Fallback

When the Hermes browser tool (`browser_navigate`) launches with a desktop viewport (1280×577) and cannot be resized to mobile size, use Playwright from the project's own `node_modules` to capture mobile-viewport screenshots.

## Problem

- `browser_navigate` opens Chromium at desktop resolution.
- `browser_console` with `window.resizeTo()` is unreliable — many browsers block it.
- The Hermes browser tool does not expose viewport configuration.

## Solution

Use the project's installed Playwright (`@playwright/test` or `playwright`) via its pnpm `node_modules` path.

### Finding Playwright in pnpm

pnpm stores packages in `.pnpm/<name>@<version>/node_modules/<name>`. The exact version varies by project lockfile.

```bash
# List available playwright packages
npm ls playwright 2>/dev/null | head -5
npm ls @playwright/test 2>/dev/null | head -5
```

### Require Path Pattern

```javascript
// Direct require from pnpm store (avoids NODE_PATH issues with pnpm symlinks)
const pw = require('./node_modules/.pnpm/playwright@<VERSION>/node_modules/playwright');
```

> **Pitfall**: `NODE_PATH` with pnpm does NOT work because pnpm's symlink structure
> breaks Node's module resolution. Always use the direct path to the `.pnpm` directory.

### Quick Screenshot Script

```javascript
const pw = require('./node_modules/.pnpm/playwright@1.59.1/node_modules/playwright');

(async () => {
  const browser = await pw.chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const page = await ctx.newPage();

  await page.goto('http://localhost:5173');
  await page.waitForLoadState('networkidle');

  // Optional: inject UI elements for preview (e.g. toast, dialog)
  await page.evaluate(() => {
    // ... DOM manipulation ...
  });

  await page.screenshot({ path: '/tmp/mobile-screenshot.png' });
  await browser.close();
})();
```

### Using `npx playwright screenshot` (no script needed)

For simple page screenshots without JS injection:

```bash
cd /path/to/project
npx playwright screenshot --viewport-size=390,844 http://localhost:5173 /tmp/mobile.png
```

### Common Viewports

| Device          | Width | Height |
|-----------------|-------|--------|
| iPhone 14/13/12 | 390   | 844    |
| iPhone SE       | 375   | 667    |
| iPhone 14 Pro Max | 430 | 932    |
| iPad            | 768   | 1024   |
| Desktop 14"     | 1512  | 982    |

## When to Use This Pattern

- User says "take a mobile screenshot" or "截图按移动端"
- User-facing app (H5, PWA, mobile-first) where desktop viewport is wrong
- Need to inject DOM elements (toast, dialog) before screenshot
- Need to wait for specific network/DOM state before capture

## When NOT to Use

- Admin/desktop apps where 14" viewport is correct (use `browser_navigate` directly)
- Simple page screenshots — prefer `npx playwright screenshot` one-liner
- When the Hermes browser tool already supports the needed viewport
