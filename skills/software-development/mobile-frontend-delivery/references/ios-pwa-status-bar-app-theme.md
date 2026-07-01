# iOS Home Screen PWA status bar must follow the app theme

Scope/applicability: iOS Safari Add to Home Screen / standalone PWA sessions where the phone system light/dark mode and the app's in-app theme can intentionally differ. Use when the top status bar looks black while the app is in light mode, or when a static `apple-mobile-web-app-status-bar-style` no longer matches the resolved app theme.

Anti-conditions: do not apply to Android WebAPK/Chrome status-bar color by itself; Android primarily consumes `meta[name="theme-color"]` and manifest `theme_color`. Do not use this to remove an explicit “Follow System” theme option; fixed `light`/`dark` choices should be app-owned, while explicit `system` can still resolve from OS color scheme.

## Symptom

Matrix failure:

- Phone system dark + app light/day mode -> top status bar is black or translucent-black, visually mismatching the light app surface.
- Phone system light + app dark/night mode -> top status bar looks correct.

This asymmetry often means a static iOS PWA status-bar meta is accidentally matching only the dark app case:

```html
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
```

## Diagnosis split

Keep these surfaces separate:

1. App content: controlled by app CSS/runtime `data-theme`.
2. Android/Chrome PWA status bar: usually controlled by a single app-owned `meta[name="theme-color"]` plus manifest freshness.
3. iOS Home Screen status bar: controlled by `meta[name="apple-mobile-web-app-status-bar-style"]` at startup and should match the resolved app theme.

If `theme-color` is already correct but iOS top chrome is black in app-light mode, inspect the iOS status-bar meta before changing CSS safe-area, layout, or Android system-bar code.

## Recommended implementation pattern

- Keep one authoritative `meta[name="theme-color"]` for Android/Chrome PWA.
- Keep one authoritative `meta[name="apple-mobile-web-app-status-bar-style"]` for iOS Home Screen PWA.
- Resolve app theme from persisted user choice:
  - fixed `light` -> resolved light, independent of phone system;
  - fixed `dark` -> resolved dark, independent of phone system;
  - explicit `system` -> resolve from `matchMedia('(prefers-color-scheme: dark)')`.
- Sync both meta tags from the same resolved app theme:

```ts
const THEME_COLOR = {
  light: '#F2F3F5',
  dark: '#0E0F12',
} as const;

const IOS_STATUS_BAR_STYLE = {
  light: 'default',
  dark: 'black-translucent',
} as const;

function applyTheme(resolved: 'light' | 'dark') {
  document.documentElement.setAttribute('data-theme', resolved);
  setSingleMeta('theme-color', THEME_COLOR[resolved], { removeMedia: true });
  setSingleMeta('apple-mobile-web-app-status-bar-style', IOS_STATUS_BAR_STYLE[resolved]);
}
```

For first paint, do the same in the inline head script before the bundle loads so the installed PWA does not start with stale system-colored chrome.

## Verification matrix

Run at least a PWA/H5 runtime proof for:

| Phone/system | App choice | Expected app theme | `theme-color` | iOS status-bar style |
|---|---|---|---|---|
| dark | light | light | light surface color | `default` |
| light | dark | dark | dark surface color | `black-translucent` |
| dark | system | dark | dark surface color | `black-translucent` |
| light | system | light | light surface color | `default` |

Also assert:

- exactly one `meta[name="theme-color"]`;
- zero media-bound theme-color tags unless the product explicitly wants OS-driven browser chrome outside app state;
- exactly one `meta[name="apple-mobile-web-app-status-bar-style"]`;
- built `dist/index.html` has the light/default startup values.

## Pitfalls

- Do not treat a correct Android `theme-color` chain as proof the iOS Home Screen status bar is correct.
- Do not hard-code `black-translucent` for all app themes; it only happens to match dark app mode.
- Do not use CSS safe-area or layout patches to solve a meta-controlled status-bar color mismatch.
- iOS Home Screen can cache startup shell metadata. If source and deployed HTML are correct but an already-installed icon still shows stale chrome, delete/re-add the Home Screen PWA before calling the fix failed.
