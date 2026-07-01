# Login-state-assisted public media intake

## When to use

Use when public media evidence collection is blocked by platform login/app gates, but the user explicitly frames the work as system testing and authorizes using their own logged-in browser session.

Applies to:

- WeChat Channels / 视频号 public previews that show QR/App-login gates.
- Douyin pages where public preview or browser playback is incomplete under login overlays.
- Xiaohongshu pages where public content is gated behind the user's own session.

Anti-conditions:

- Do not use this as login bypass, captcha/2FA bypass, stealth evasion, anti-bot circumvention, or bulk scraping.
- Do not ask the agent to type passwords, OTPs, scan QR codes, or handle secrets.
- Do not export raw cookies, localStorage tokens, or authenticated request headers into docs, memory, task records, chat, or evidence bundles.
- Do not publish or external-share login-state evidence without a separate explicit authority gate.

## Safe pattern

1. State the boundary: this is a manual-login, read-only system-test bridge, not a bypass.
2. Use a dedicated local browser profile per platform, e.g. `~/.hermes/state/social-login-profiles/<platform>/`.
3. The human manually logs in/scans QR in that browser profile.
4. The agent runs only read-only probes through browser automation/CDP:
   - page title / URL readback;
   - DOM text sampling with redaction;
   - screenshot capture;
   - access-blocker detection;
   - evidence-level upgrade/downgrade.
5. Keep cookies/session state inside the browser profile. Never print/export cookie jars.
6. Store durable evidence under a private evidence directory with an explicit boundary note.
7. Record `evidence_level` honestly:
   - `E0 Preview only` before login-state assistance;
   - `E1 Login-state-assisted screenshot/DOM evidence` after human login and read-only probe;
   - `E2 External artifact identified` only after official repo/site/package is found;
   - `E3/E4` only after metadata/license/runtime proof.

## Implementation notes

A safe local helper may expose commands like:

```bash
python3 ~/.hermes/scripts/social_login_state_bridge.py launch \
  --platform wechat_channels \
  --url 'https://channels.weixin.qq.com/finder-preview/pages/sph?id=<id>' \
  --port 9229

python3 ~/.hermes/scripts/social_login_state_bridge.py probe \
  --platform wechat_channels \
  --url 'https://channels.weixin.qq.com/finder-preview/pages/sph?id=<id>' \
  --port 9229 \
  --screenshot
```

The helper should support `launch`, `probe`, and `status`, redact common token/cookie fields, and include tests for redaction and profile path scoping before use.

## Human gate wording

When starting a browser profile crosses the local-login-state boundary, ask for the smallest authority:

```text
Allow me to start a dedicated local Chrome profile for <platform> at <url> so you can manually log in. I will not type credentials, export cookies, bypass QR/captcha/2FA, or bulk scrape. After you log in, I will run a read-only DOM/title/screenshot probe and store redacted evidence privately.
```

## Verification checklist

- [ ] Dedicated profile path is platform-scoped and not a shared personal browser profile.
- [ ] User performed login manually; agent did not handle credentials/OTP/QR.
- [ ] Probe output redacts URL query secrets, cookie/session/token/authorization-looking fields, and bearer tokens.
- [ ] Raw cookies/localStorage/sessionStorage values are not written to durable artifacts.
- [ ] Evidence bundle states the access method and residual limits.
- [ ] No bulk crawling, anti-bot evasion, external posting, or credential export occurred.
