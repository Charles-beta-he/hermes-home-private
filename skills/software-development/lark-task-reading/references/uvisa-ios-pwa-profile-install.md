# UVISA iOS PWA profile install retry pattern

Use this when a UVISA C-end Lark task reports iOS QR/PWA install issues such as:
- tapping `安装描述文件` does not jump to the profile install flow;
- deleting the iOS profile and scanning again leaves no usable install action;
- installed Web Clip/profile completes but no desktop icon appears.

## Durable diagnosis

The iOS path is not the browser-native `beforeinstallprompt` path. It is a Web Clip `.mobileconfig` download/installation path. Treat these as distinct acceptance atoms:

1. iOS install CTA is visible when `platform === ios` and app is not standalone.
2. A user tap performs a direct top-level navigation to the `.mobileconfig` URL.
3. Same-session rescan/remount can show the CTA again after the user deletes the profile.
4. The `.mobileconfig` artifact is CMS-verifiable and contains a WebClip URL + icon payload.
5. Built production JS references the intended profile URL.
6. A mobile WebKit/browser smoke proves tapping the CTA requests the profile URL.

## Implementation pattern

In the PWA install banner:

- Prefer `window.location.assign(profileUrl)` for iOS profile installation.
- Avoid `window.open(profileUrl, '_self')` for this path; iOS Safari/WebKit can make second-tap behavior flaky and test environments surface it as a partially implemented/window-open path.
- Version the profile URL when fixing install cache behavior, e.g. `/uvisa-ios-pwa.mobileconfig?v=<date-or-task-id>`, so Safari/iOS re-requests the profile after deletion/re-scan instead of reusing stale download/navigation state.
- Do not apply a session-level “install prompt already shown” suppression to the iOS profile guide. Keep one-shot suppression for Android/Chrome native `beforeinstallprompt`, but allow iOS to show again on same-session remount/rescan.

## Regression tests

Add/keep component tests that prove:

- iOS click calls `window.location.assign('/uvisa-ios-pwa.mobileconfig?v=...')` and does not call `window.open` or native `promptInstall()`.
- iOS guide appears again after unmount/remount in the same session.
- Existing installed/standalone suppression still hides the prompt.

If jsdom refuses to spy on `window.location.assign`, stub the global location object inside the test and restore it after each test:

```ts
const assignSpy = vi.fn();
vi.stubGlobal('location', { ...window.location, assign: assignSpy });
// ... assertions ...
afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});
```

## Artifact validation

Run a deterministic profile check before claiming the profile itself is valid:

```bash
python3 - <<'PY'
from pathlib import Path
import base64, re, subprocess, tempfile, os
p = Path('public/uvisa-ios-pwa.mobileconfig')
data = p.read_bytes()
xml_start = data.find(b'<?xml')
xml_end = data.find(b'</plist>') + 8
assert xml_start >= 0 and xml_end > xml_start, 'plist XML missing from CMS payload'
xml = data[xml_start:xml_end].decode('utf-8', 'ignore')
for key in ['PayloadDisplayName', 'Label', 'URL', 'PayloadIdentifier', 'PayloadUUID']:
    m = re.search(r'<key>'+re.escape(key)+r'</key>\s*<string>(.*?)</string>', xml, re.S)
    print(key, m.group(1) if m else None)
icon = re.search(r'<key>Icon</key>\s*<data>\s*(.*?)\s*</data>', xml, re.S)
assert icon, 'WebClip icon missing'
raw = base64.b64decode(''.join(icon.group(1).split()))
assert raw.startswith(b'\x89PNG\r\n\x1a\n'), 'icon is not PNG'
with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
    f.write(raw); name = f.name
try:
    print(subprocess.check_output(['file', name], text=True).strip())
finally:
    os.unlink(name)
PY
openssl cms -verify -inform DER -in public/uvisa-ios-pwa.mobileconfig -noverify -out /tmp/uvisa-profile.plist
```

## Browser smoke

After `pnpm run build`, serve/preview the built app and use a WebKit/iPhone context. The smoke should prove the button is visible and a tap requests the versioned profile URL:

```js
const { webkit, devices } = require('@playwright/test');
(async () => {
  const browser = await webkit.launch({ headless: true });
  const context = await browser.newContext({ ...devices['iPhone 13'] });
  const page = await context.newPage();
  const requests = [];
  page.on('request', req => {
    if (req.url().includes('uvisa-ios-pwa.mobileconfig')) requests.push(req.url());
  });
  await page.goto('http://127.0.0.1:<port>/', { waitUntil: 'networkidle' });
  const button = page.getByRole('button', { name: '安装描述文件' });
  await button.waitFor({ timeout: 10000 });
  await button.click();
  await page.waitForTimeout(500);
  console.log({ profileRequests: requests, url: page.url() });
  await browser.close();
})();
```

## Closeout boundary

This can prove the local implementation and artifact contract, but final Lark completion for UVISA online/UI tasks still requires deployed online and/or real iOS device acceptance evidence when the task explicitly concerns iOS installation behavior. Report local proof as implementation-sendback, not final online closeout, unless real-device evidence is available.
