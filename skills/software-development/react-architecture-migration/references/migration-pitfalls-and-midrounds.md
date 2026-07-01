# React Migration Pitfalls and Mid-Round Fix Patterns

Extracted from `/Users/charles/.hermes/skills/software-development/react-architecture-migration/SKILL.md` on 2026-07-01T08:52:42.874486+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Common Pitfalls
1. **#1 FAILURE: Subagent timeout on large scopes**: MiMo model subagents silently return empty response when reading 10+ large files. Diagnostic: "Model returned empty after tool calls". FIX: limit each subagent to 5-8 files. For mass changes (55-screen i18n migration), use `execute_code` with programmatic file manipulation instead of delegating to subagents.

2. **Tool name mismatch**: Skills reference `read_multiple_files` but actual tool is `mcp_filesystem_read_multiple_files`. FIX: use `read_file`/`terminal` in subagent prompts.

3. **i18n subagent timeout**: 55-screen i18n migration via subagent always times out. FIX: use `execute_code` programmatic approach — add import + useTranslation to all files in one script, then do text replacement in a second pass.

4. **npm cache permissions (macOS)**: `npm install --cache /tmp/npm-cache` workaround.

5. **vite-plugin-pwa peer deps**: May need `--legacy-peer-deps` for vite 8.

6. **tsc path (macOS)**: `node node_modules/typescript/bin/tsc --noEmit` (not `npx tsc`).

7. **Mock data separation**: Keep UI config (colors, labels) inline. Only move business data to mock server.

8. **Dark mode without UI changes**: Add `dark:` to existing className strings. Don't change JSX structure.

9. **Screen count reality check**: ~23/55 screens are static/input-only (auth, settings, PIN entry). They don't need stores, loading states, or PullToRefresh. The "58% store adoption" for data-fetching screens is actually 100%.

10. **i18n text overflow**: Chinese → English text expands 2-5x. CRITICAL areas:
    - 4-column action grids (ActionBtn, CardAction): add `truncate` + `overflow-hidden`
    - Tab bars: English labels like "Quantitative" (12 chars) crowd narrow cells
    - Section titles: "Cross-border Remittance (SWIFT / E-wallet / Crypto)" = 51 chars
    - Always add `min-w-0 truncate` to flex children that contain text
    - Use `flex-wrap` on product card metadata rows

11. **web-vitals API change**: `onFID` removed in v5, use `onINP` instead.

12. **Hardcoded version strings**: Use `src/lib/version.ts` with `APP_VERSION` constant, reference in MeScreen + AboutScreen.

13. **PWA icons**: Must be real PNG files (not SVG). Generate with Pillow or download from Figma.

14. **Mock server not in build**: `npm run build` only bundles frontend. Mock server deploys separately (Railway/Render/VPS).

15. **Mock server API path mismatch**: Frontend services may call different paths than mock server endpoints. Always run the path alignment check (Round 9.5) before declaring "done".

16. **browser_console for flow verification**: Can test all API endpoints directly in the browser without Playwright. Faster than E2E tests for verifying endpoint existence and error handling.

17. **vite-plugin-pwa registerType 'prompt'**: Must NOT have `skipWaiting: true` or `clientsClaim: true` in workbox config. The 'prompt' mode handles SKIP_WAITING via the useServiceWorkerUpdate hook.

18. **PWA icons must be real PNG**: Generate with Pillow (`from PIL import Image`) if design tools unavailable. SVG icons don't work for PWA manifest.

### Dark Mode CSS Variable Pattern (Critical Fix)

When dark mode renders as "all black" or nav bar is invisible, the root cause is usually hardcoded rgba/hex colors without dark variants. The fix pattern:

```css
/* BEFORE — hardcoded, no dark variant */
.glass {
  background: rgba(255,255,255,0.72);
  border: 0.5px solid rgba(255,255,255,0.7);
}
.hairline { box-shadow: inset 0 -0.5px 0 #F0F2F5; }

/* AFTER — CSS variables with dark variants in :root and [data-theme="dark"] */
:root, [data-theme="light"] {
  --glass-bg: rgba(255,255,255,0.72);
  --glass-border: rgba(255,255,255,0.7);
  --border: #F0F2F5;
  --surface: #FFFFFF;
}
[data-theme="dark"] {
  --glass-bg: rgba(30,33,40,0.82);
  --glass-border: rgba(255,255,255,0.06);
  --border: #2A2D35;
  --surface: #1B1E25;
}
.glass {
  background: var(--glass-bg);
  border: 0.5px solid var(--glass-border);
}
.hairline { box-shadow: inset 0 -0.5px 0 var(--border); }
```

**Bulk screen dark mode fix** (when 50+ screens have `bg-white` without `dark:`):
```python
# execute_code batch fix
content = content.replace(
    'bg-white shadow-card',
    'bg-white dark:bg-surface-elevated dark:shadow-none shadow-card'
)
content = content.replace('text-ink-900', 'text-ink-900 dark:text-ink-50')
content = content.replace('text-ink-500', 'text-ink-500 dark:text-ink-400')
content = content.replace('bg-ink-50', 'bg-ink-50 dark:bg-ink-800/50')
```

### Build Size Optimization

Target: <250KB gzipped JS+CSS. Add compression and chunk splitting:

```typescript
// vite.config.ts
import viteCompression from 'vite-plugin-compression2';

export default defineConfig({
  plugins: [
    react(),
    VitePWA({ registerType: 'prompt', /* ... */ }),
    viteCompression({ algorithm: 'gzip' }),
    viteCompression({ algorithm: 'brotliCompress' }),
  ],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'i18n-vendor': ['i18next', 'react-i18next', 'i18next-browser-languagedetector'],
          'vendor': ['zustand', 'axios'],
        },
      },
    },
  },
});
```

Verify: `for f in dist/assets/*.js dist/assets/*.css; do gzip -c "$f" | wc -c; done | awk '{s+=$1} END {print s/1024 " KB gzipped"}'`

### i18n Key Alignment Check

After migration, verify zh/en keys match:

```python
def flatten_dict(d, prefix=''):
    items = []
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict): items.extend(flatten_dict(v, key))
        else: items.append(key)
    return items

zh_keys = flatten_dict(json.load(open('src/i18n/zh.json')))
en_keys = flatten_dict(json.load(open('src/i18n/en.json')))
missing_en = set(zh_keys) - set(en_keys)
missing_zh = set(en_keys) - set(zh_keys)
print(f"zh: {len(zh_keys)}, en: {len(en_keys)}, missing_en: {missing_en}, missing_zh: {missing_zh}")
```

### Test Writing Patterns for Stores/Services

```typescript
// Store test — mock the API service
vi.mock('../../services/auth.service', () => ({
  authService: {
    sendCode: vi.fn().mockResolvedValue({ success: true }),
    verifyCode: vi.fn().mockResolvedValue({ token: 'test', user: mockUser }),
  },
}));

// Service test — mock the api client
vi.mock('../../lib/api', () => ({
  api: { get: vi.fn().mockResolvedValue({ data: { success: true, data: [...] } }),
         post: vi.fn().mockResolvedValue({ data: { success: true } }) },
}));

// Hook test — renderHook + act
const { result } = renderHook(() => useOnlineStatus());
act(() => { window.dispatchEvent(new Event('offline')); });
expect(result.current).toBe(false);
```

### P10 Self-Check Checklist (Each Round)

```python
# Run after each round
checks = {
    'TypeScript': os.system('tsc --noEmit') == 0,
    'Tests': os.system('npx vitest run --reporter=json') == 0,
    'i18n aligned': len(zh_keys) == len(en_keys),
    'dark mode screens': dark_screen_count / total_screens >= 0.95,
    'dark mode components': dark_comp_count / total_components >= 0.80,
    'build gzip < 250KB': gzip_size < 256000,
}
for name, ok in checks.items():
    print(f"  {'✓' if ok else '✗'} {name}")
```
