# Absorbed Hermes operations package: `hermes-tool-availability`

Applicability: Hermes Agent operations/extension tasks that need this narrow operational lane. Anti-condition: do not load as a separate skill root; route through `hermes-agent` and read this reference only when the lane is relevant.

## Re-homed support files
- `references/hermes-tool-availability/system-dependency-tool-availability.md`

---

---
name: hermes-tool-availability
description: Use when diagnosing or repairing Hermes Agent `hermes doctor` Tool Availability warnings, especially `system dependency not met`, vision/image dependency prompts, browser-cdp, computer_use, video_gen provider gates, Home Assistant, Spotify, or platform/session-gated tools.
---

# Hermes Tool Availability

## Scope, applicability, and anti-conditions

Scope: Hermes Agent installations on a local developer machine where the user asks to make tools available, understand `hermes doctor` tool warnings, or repair a tool dependency prompt.

Applicability: use for toolset readiness checks and setup triage only: package dependencies, local binaries, reachable local endpoints, OAuth/login gates, environment tokens, and gateway/session preconditions.

Anti-conditions:

- Do not use this as a general Hermes self-update or core-code modification workflow; use the protected `hermes-agent` umbrella as the authority.
- Do not encode one machine's missing dependency as a global negative claim about a tool.
- Do not perform credential setup, account authorization, or platform login unless the user explicitly asks or provides the needed secret/interactive authorization.
- Do not change project application code; this is only for Hermes runtime/tool availability.

## When to use

Use this skill when Hermes reports unavailable tools in `hermes doctor`, startup banners, or a tool invocation prompt, including:

- `Feature 'tool.<name>' requires ...`
- `Tool Availability` warnings
- `system dependency not met`
- missing tool-specific provider/backend availability
- a tool that should be visible but is absent from the active toolset list

## Core workflow

1. Start with the live doctor output.
   - Run `hermes doctor` and focus on the `Tool Availability` section.
   - Do not assume `system dependency not met` means a binary is missing; Hermes uses the same label for any toolset check returning false without env-var metadata.

2. Identify the exact gate before fixing.
   - Inspect the registered toolset check function rather than guessing from the displayed label.
   - Use Hermes' active venv for imports, not system Python.
   - Diagnostic pattern:
     ```bash
     cd ~/.hermes/hermes-agent
     ./venv/bin/python - <<'PY'
     import sys, inspect, traceback
     sys.path.insert(0, '.')
     import model_tools  # triggers tool discovery
     from tools.registry import registry

     wanted = ['browser-cdp', 'computer_use', 'homeassistant', 'video_gen', 'hermes-yuanbao', 'spotify']
     entries, checks = registry._snapshot_state()
     for ts in wanted:
         names = [e.name for e in entries if e.toolset == ts]
         check = checks.get(ts)
         print('\n==', ts, '==')
         print('tools=', names)
         print('check=', check, getattr(check, '__module__', None), getattr(check, '__name__', None))
         if check:
             try:
                 print('source_file=', inspect.getsourcefile(check), 'line=', inspect.getsourcelines(check)[1])
                 print('\n'.join(inspect.getsource(check).splitlines()[:60]))
             except Exception as exc:
                 print('no source:', exc)
             try:
                 print('result=', check())
             except Exception:
                 traceback.print_exc()
     PY
     ```

3. Fix only gates that are actually fixable without user secrets or account authorization.
   - Binary/package/runtime dependency: install or repair it, then verify the check function returns true.
   - Browser CDP endpoint: start or attach a real Chromium-family browser with remote debugging and persist `browser.cdp_url` only if that is the user's desired default.
   - Credential/login gates: report the exact missing token/login and stop unless the user provides credentials or requests an interactive login.
   - Platform/session-gated tools: do not force them on locally; explain the required gateway/session context.

4. Verify at two levels.
   - Directly call the relevant check function and confirm it returns `True`.
   - Re-run `hermes doctor` and confirm the toolset line moved from warning to checkmark.

## Known gates and fixes

### Screenshot / vision dependency prompt

Symptom:

```text
Feature 'tool.vision' requires: Pillow>=12.2.0
Install into the active venv now? [Y/n]
```

Fix into the Hermes active venv:

```bash
~/.hermes/hermes-agent/venv/bin/python -m pip install -U 'Pillow>=12.2.0'
```

Verify:

```bash
~/.hermes/hermes-agent/venv/bin/python - <<'PY'
from packaging.version import Version
import PIL
assert Version(PIL.__version__) >= Version('12.2.0'), PIL.__version__
print('Pillow dependency OK:', PIL.__version__)
PY
hermes doctor
```

### `computer_use`

Gate: macOS plus `cua-driver` binary available.

Fix:

```bash
hermes computer-use install
hermes computer-use status
```

Verify with the active venv:

```bash
cd ~/.hermes/hermes-agent
./venv/bin/python - <<'PY'
import sys
sys.path.insert(0, '.')
from tools.computer_use.tool import check_computer_use_requirements
print('computer_use check=', check_computer_use_requirements())
PY
```

macOS TCC is a second-stage runtime requirement. If desktop capture/control fails after the tool is visible, grant Accessibility and Screen Recording for CuaDriver/Hermes:

```bash
~/.local/bin/cua-driver permissions grant
~/.local/bin/cua-driver permissions status
```

### `browser-cdp`

Gate: normal browser tooling available plus a reachable CDP override from `BROWSER_CDP_URL` or `browser.cdp_url`.

First decide whether the user wants browser automation to be visible. A persistent `browser.cdp_url` deliberately attaches Hermes to a real Chrome/Chromium profile and can pop or keep a visible browser window. If the user expects silent/default browser tools, do **not** persist `browser.cdp_url`; leave it empty so `browser_navigate` uses the normal local headless `agent-browser` path. Use CDP only when the user explicitly wants `/browser connect`, dialog/CDP tooling, or an already-running browser profile.

Preferred interactive path inside Hermes is `/browser connect`. For a persistent local default, launch a separate Chrome profile on a dedicated port and set config:

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9223 \
  --user-data-dir="$HOME/.hermes/chrome-debug-9223" \
  --no-first-run \
  --no-default-browser-check >/dev/null 2>&1 &

hermes config set browser.cdp_url http://127.0.0.1:9223
```

Verify the endpoint is a real DevTools endpoint before declaring success:

```bash
curl -fsS http://127.0.0.1:9223/json/version
cd ~/.hermes/hermes-agent
./venv/bin/python - <<'PY'
import sys
sys.path.insert(0, '.')
from tools.browser_cdp_tool import _browser_cdp_check
print('browser-cdp check=', _browser_cdp_check())
PY
```

Pitfall: if another Chrome already owns a port but returns empty/404 for `/json/version`, choose a different port and a separate `--user-data-dir` rather than fighting the existing user profile.

Pitfall: when the complaint is “Hermes browser tools pop a new Chrome window”, check persistent CDP before touching code. Look for `browser.cdp_url` in `~/.hermes/config.yaml`, `BROWSER_CDP_URL`, a listener such as `lsof -iTCP:9223 -sTCP:LISTEN`, and Chrome processes containing `--remote-debugging-port` plus a Hermes-specific `--user-data-dir`. To restore silent/default behavior, clear the persistent override (`hermes config set browser.cdp_url ''`) and stop only the isolated debug Chrome profile; verify `_get_cdp_override()` is empty and `_browser_cdp_check()` is false. Do not kill the user's normal Chrome profile.

### Credential or session-gated toolsets

These may show as `system dependency not met` when their check function has no env-var metadata. Diagnose the check function first, then report the real gate:

- `homeassistant`: requires `HASS_TOKEN` in the environment/config-loaded env.
- `spotify`: requires Spotify OAuth login, e.g. `hermes auth spotify login`.
- `video_gen`: requires at least one available registered video provider such as FAL (`FAL_KEY` or managed gateway) or xAI credentials/OAuth.
- `hermes-yuanbao`: usually requires a Yuanbao gateway session or active Yuanbao adapter; do not treat it as a local binary install.

## Pitfalls

- Do not save one machine's missing dependency as a durable negative claim about Hermes tools. Capture the fix or diagnosis pattern instead.
- Do not use system Python to inspect Hermes modules; system Python may fail on Hermes code syntax/runtime assumptions. Use `~/.hermes/hermes-agent/venv/bin/python`.
- Do not run broad `hermes doctor --fix` when the user asked to repair only tool availability unless the config migration itself is in scope.
- Distinguish visibility from runtime permission: `computer_use` can be visible while macOS Screen Recording/Accessibility is still not granted.
- Avoid expanding scope from system dependencies into API-key setup without explicit user intent.

## References

- `references/hermes-tool-availability/system-dependency-tool-availability.md` — session-derived details and command examples for Pillow, `computer_use`, `browser-cdp`, and credential/session-gated tools.
