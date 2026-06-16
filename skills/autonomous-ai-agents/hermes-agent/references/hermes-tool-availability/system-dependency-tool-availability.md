# System dependency tool availability notes

Scope: session-derived troubleshooting details for local Hermes Agent tool availability checks. These notes are examples of how to diagnose gates; they are not permanent claims that any tool is broken.

## Pattern: `system dependency not met` needs check-function inspection

`hermes doctor` may print `system dependency not met` whenever a toolset's registered check function returns false and no missing env vars are attached to the registry entry. The label can mean:

- a missing binary/package;
- a missing reachable endpoint;
- an OAuth/login requirement;
- no configured provider backend;
- a platform/session context requirement.

Therefore the reusable move is to inspect the check function with the active Hermes venv before installing anything.

## Observed gates and fixes

### Vision screenshot prompt

Prompt:

```text
Feature 'tool.vision' requires: Pillow>=12.2.0
Install into the active venv now? [Y/n]
```

Useful fix:

```bash
~/.hermes/hermes-agent/venv/bin/python -m pip install -U 'Pillow>=12.2.0'
```

Verification can import `PIL`, assert the version, and open/verify the image that triggered the issue.

### `computer_use`

Check function condition: macOS plus `cua-driver` binary on PATH or configured override.

Fix used:

```bash
hermes computer-use install
hermes computer-use status
```

Direct verification:

```bash
cd ~/.hermes/hermes-agent
./venv/bin/python - <<'PY'
import sys
sys.path.insert(0, '.')
from tools.computer_use.tool import check_computer_use_requirements
from tools.computer_use.cua_backend import cua_driver_binary_available
print('cua_driver_binary_available=', cua_driver_binary_available())
print('computer_use check=', check_computer_use_requirements())
PY
```

Second-stage caveat: macOS TCC permissions can remain unknown or ungranted after installation. Use `cua-driver permissions grant/status` if actual desktop capture/control fails.

### `browser-cdp`

Check function condition: normal browser requirements pass and `_get_cdp_override()` returns a reachable CDP URL from `BROWSER_CDP_URL` or `browser.cdp_url`.

Important behavior split:

- Default `browser_navigate` / `browser_snapshot` should use the local headless `agent-browser` path when no CDP override is set.
- A configured `browser.cdp_url` is an explicit visible-browser/CDP override. It makes Hermes skip the default local headless launcher and attach to the supplied Chrome DevTools endpoint. If that endpoint was launched from `/Applications/Google Chrome.app` with `--remote-debugging-port`, the user may see a new Chrome window/profile.

If the user reports unexpected Chrome popups, diagnose in this order:

```bash
python3 - <<'PY'
import os, yaml
cfg = yaml.safe_load(open(os.path.expanduser('~/.hermes/config.yaml'))) or {}
print('browser.cdp_url=', repr((cfg.get('browser') or {}).get('cdp_url')))
print('BROWSER_CDP_URL=', repr(os.environ.get('BROWSER_CDP_URL')))
PY
lsof -iTCP:9223 -sTCP:LISTEN -n -P || true
ps aux | grep -Ei 'remote-debugging-port|hermes-chrome|chrome-debug' | grep -v grep || true
```

To restore silent/default browser behavior:

```bash
hermes config set browser.cdp_url ''
# Then stop only the isolated debug profile if one exists; do not kill normal Chrome.
pgrep -af -- '--remote-debugging-port=.*--user-data-dir=.*hermes' || true
```

Verify with Hermes' active venv:

```bash
cd ~/.hermes/hermes-agent
./venv/bin/python - <<'PY'
from tools.browser_tool import _get_cdp_override, _is_local_mode
from tools.browser_cdp_tool import _browser_cdp_check
print('cdp_override=', repr(_get_cdp_override()))
print('browser_cdp_check=', _browser_cdp_check())
print('browser_local_headless_path=', _is_local_mode())
PY
```

Expected after clearing: `cdp_override=''`, `browser_cdp_check=False`, and `browser_local_headless_path=True`.

If a default Chrome profile already has an unusable/odd listener on a port and the user explicitly wants CDP/browser-dialog tooling, launch a separate profile on a different port and persist that endpoint:

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9223 \
  --user-data-dir="$HOME/.hermes/chrome-debug-9223" \
  --no-first-run \
  --no-default-browser-check >/dev/null 2>&1 &

hermes config set browser.cdp_url http://127.0.0.1:9223
```

Verify `/json/version` returns a non-empty DevTools response and `_browser_cdp_check()` returns true.

### Credential/session gates that can be mislabeled as system dependency

In the inspected runtime, these false-ish checks were not local binary fixes:

- `homeassistant`: check was `bool(os.getenv("HASS_TOKEN"))`.
- `spotify`: check was `get_auth_status("spotify").get("logged_in")`.
- `video_gen`: check was at least one registered video provider reporting available; FAL/xAI both unavailable without suitable credentials/gateway.
- `hermes-yuanbao`: check required Yuanbao gateway session context or active adapter.

Future handling: report the precise gate and ask/proceed only if credential/login/session setup is in scope.
