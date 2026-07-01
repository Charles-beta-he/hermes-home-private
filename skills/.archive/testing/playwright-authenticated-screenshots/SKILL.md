---
name: playwright-authenticated-screenshots
description: "Use when take authenticated mobile/desktop screenshots of production apps using Playwright with an existing Chrome profile (no separate auth state management). Use when verifying UI changes against production, capturing visual evidence of fixes, or documenting app state."
triggers:
  - "screenshot production"
  - "verify UI on production"
  - "visual evidence of fix"
  - "capture authenticated screenshot"
  - "playwright chrome profile"
---

# Authenticated Screenshots via Playwright + Chrome Profile

## Overview

Take authenticated mobile/desktop screenshots of production apps using Playwright with an existing Chrome profile (no separate auth state management). Use when verifying UI changes against production, capturing visual evidence of fixes, or documenting app state. This skill is maintained as a `wrapper`-shaped contract: it should guide external tools, APIs, CLIs, platforms, or other side-effecting capability surfaces without stealing adjacent workflows or relying on unstated assumptions.

Use Playwright with the user's existing Chrome profile to take authenticated screenshots of production apps. No need to manage separate auth state files or re-login.

## When to Use

- Verifying a UI fix on production (compare before/after)
- Capturing visual evidence for Lark task closure
- Documenting app state for PRDs or reviews
- Mobile viewport screenshots (375×812 @3x DPR)


- Don't use for: tasks outside this skill's trigger class, requests with a more specific neighboring skill, or situations where required evidence/tooling is unavailable.
## Prerequisites

- `@playwright/test` installed in the target project (pnpm/npm)
- User has an active Chrome session with the target app authenticated
- Chrome profile at `~/Library/Application Support/Google/Chrome/Default` (macOS)

## Step-by-Step

### 1. Create the script (.mts extension required)

```typescript
import { chromium } from '@playwright/test';
import { mkdtempSync, cpSync, rmSync } from 'fs';
import { tmpdir } from 'os';
import { join } from 'path';

// Copy Chrome profile to temp dir (exclude heavy caches)
const tmpRoot = mkdtempSync(join(tmpdir(), 'pw-chrome-'));
const src = join(process.env.HOME!, 'Library/Application Support/Google/Chrome/Default');
try {
  cpSync(src, join(tmpRoot, 'Default'), {
    recursive: true,
    filter: (p: string) =>
      !p.includes('/Cache/') &&
      !p.includes('/Code Cache/') &&
      !p.includes('/Service Worker/'),
  });
} catch { /* locked files ok */ }

const browser = await chromium.launchPersistentContext(tmpRoot, {
  executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  args: ['--profile-directory=Default'],
  viewport: { width: 375, height: 812 },  // iPhone-like
  deviceScaleFactor: 3,
  isMobile: true,
  headless: true,
});

const page = await browser.newPage();

// Navigate with domcontentloaded (NOT networkidle — too fragile on slow prod)
await page.goto('https://example.com/path', {
  waitUntil: 'domcontentloaded',
  timeout: 30000,
});
await page.waitForTimeout(5000);  // let SPA render

const url = page.url();
if (url.includes('/login')) {
  console.log('NOT_AUTHENTICATED — user session expired');
  await page.screenshot({ path: '/tmp/shot-login.png' });
} else {
  console.log('AUTHENTICATED');
  await page.screenshot({ path: '/tmp/shot-page.png' });

  // Interact: click a button, open a picker, etc.
  const btn = page.locator('button:has-text("Some Text")');
  if (await btn.count() > 0) {
    await btn.first().click();
    await page.waitForTimeout(1500);
    await page.screenshot({ path: '/tmp/shot-after-click.png' });
  }
}

await browser.close();
rmSync(tmpRoot, { recursive: true, force: true });
```

### 2. Run from the project directory

```bash
cd /path/to/project  # MUST have @playwright/test in node_modules
npx tsx scripts/my-screenshot.mts
```

### 3. Analyze screenshots

```bash
# Use vision_analyze tool on the output files
```

## Pitfalls

See `references/playwright-pitfalls.md` for detailed troubleshooting. Key ones:

1. **File extension**: MUST be `.mts` not `.ts` — top-level await requires ESM, and tsx defaults to CJS for `.ts`
2. **Import**: Use `@playwright/test` not `playwright` — the bare `playwright` package is rarely installed directly
3. **Working directory**: Script MUST run from a directory where `@playwright/test` is in `node_modules` — tsx resolves modules from the script's location
4. **waitUntil**: Use `domcontentloaded` not `networkidle` — production SPAs often have long-polling/SSE that prevents networkidle from settling
5. **Authentication check**: Always check `page.url()` for redirect to `/login` before assuming auth worked
6. **Profile copy filter**: Exclude `Cache/`, `Code Cache/`, `Service Worker/` to keep the copy fast and avoid locked-file errors

## Viewport Presets

| Device | Width | Height | DPR | isMobile |
|--------|-------|--------|-----|----------|
| iPhone-like | 375 | 812 | 3 | true |
| iPad-like | 768 | 1024 | 2 | true |
| Desktop | 1440 | 900 | 1 | false |

## Alternatives

- **Hermes browser tools**: Use when you need to interact with a page (click, type) without a custom script. Does NOT share Chrome profile — needs its own auth.
- **Playwright codegen**: Use `npx playwright codegen --device="iPhone 14"` to record interactions, then adapt the script.


## Common Pitfalls

1. Applying this skill mechanically after the user's goal has shifted. Re-check the current request before acting.
2. Treating a plan, stale memory, or prior report as proof of completion. Verify with fresh readback.
3. Ignoring neighboring skills or narrower workflows that better match the task. Prefer the most specific applicable skill.

## Verification Checklist

- [ ] Preconditions, scope, and tool availability were checked before following this workflow.
- [ ] The key output artifacts, commands, or side effects were verified by read-back or direct inspection.
- [ ] Any remaining uncertainty, blocker, or human handoff was stated explicitly.
- [ ] For mutations or external-system actions, command success was paired with target-state read-back.
