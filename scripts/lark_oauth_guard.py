#!/usr/bin/env python3
from __future__ import annotations
"""Single-flight Lark OAuth guard for Hermes.

Avoids the failure mode observed when multiple raw `lark-mcp login` commands
are launched in the background: duplicate Authorization URL notifications,
EADDRINUSE on the configured localhost callback port, and stale watch-pattern
messages after one login already succeeded.

Default behavior is conservative:
- if a valid token already exists, do not spawn anything unless --force-refresh is set;
- if another guarded login is running, do not spawn a second one;
- if the configured OAuth callback port is busy, fail closed unless --cleanup-stale is set;
- when spawning, open the authorization URL at most once.
"""

import argparse
import importlib.util
import json
import os
import platform
import re
import select
import signal
import subprocess
import tempfile
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

HERMES = Path.home() / ".hermes"
STATE_DIR = HERMES / "state"
DEFAULT_LOCK = STATE_DIR / "lark_oauth_guard.lock"
DEFAULT_ROOT = Path.home() / ".nvm/versions/node/v24.14.0/lib/node_modules/@larksuiteoapi/lark-mcp"
DEFAULT_DOMAIN = "https://open.larksuite.com"
DEFAULT_APP_ID = "cli_a96f6a6211f91ed2"
# Current Lark developer-console profile has http://localhost:8765/callback
# registered. Using the old lark-mcp default 3010 triggers Lark error 20029
# (redirect URL mismatch) unless that URL is separately added in the console.
DEFAULT_PORT = 8765
DEFAULT_SCOPES = "auth:user.id:read task:task:read task:tasklist:read"
AUTH_URL_RE = re.compile(r"https?://localhost:\d+/authorize\?[^\s\r\n]+")
NODE_LOGIN_BRIDGE = r"""
let raw = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => { raw += chunk; });
process.stdin.on('end', async () => {
  try {
    const options = JSON.parse(raw);
    const { LoginHandler } = require(process.argv[1]);
    await LoginHandler.handleLogin(options);
  } catch (_) {
    process.exit(1);
  }
});
""".strip()


@dataclass(frozen=True)
class TokenStatus:
    valid: bool
    reason: str
    token_key: str = ""
    expires_at: float | None = None
    token_count: int = 0


@dataclass(frozen=True)
class LoginPlan:
    action: str
    should_spawn: bool = False
    should_kill_stale: bool = False


class SingleFlightLock:
    def __init__(self, path: Path, stale_seconds: int = 330) -> None:
        self.path = path
        self.stale_seconds = stale_seconds
        self.acquired = False

    def is_active(self, now: float | None = None, *, cleanup_stale: bool = True) -> bool:
        now = time.time() if now is None else now
        try:
            stat = self.path.stat()
        except FileNotFoundError:
            return False
        if now - stat.st_mtime > self.stale_seconds:
            owner_pid = 0
            try:
                payload = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(payload, dict) and isinstance(payload.get("pid"), int):
                    owner_pid = payload["pid"]
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                owner_pid = 0
            if owner_pid > 0:
                try:
                    os.kill(owner_pid, 0)
                    return True
                except PermissionError:
                    return True
                except ProcessLookupError:
                    pass
            if not cleanup_stale:
                return False
            try:
                self.path.unlink()
            except FileNotFoundError:
                pass
            return False
        return True

    def acquire(self) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            return False
        with os.fdopen(fd, "w") as f:
            json.dump({"pid": os.getpid(), "created_at": time.time()}, f)
        self.acquired = True
        return True

    def release(self) -> None:
        if not self.acquired:
            return
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass
        self.acquired = False

    def __enter__(self) -> "SingleFlightLock":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.release()


def extract_auth_url(text: str) -> str:
    match = AUTH_URL_RE.search(text or "")
    return match.group(0) if match else ""


def _is_unexpired(token: dict[str, Any], now: float) -> bool:
    expires_at = token.get("expiresAt")
    # Missing/blank expiry is treated as unbounded because older lark-mcp token
    # records may omit the field. Explicit 0/"0" is a real epoch timestamp and
    # must fail closed as expired rather than silently keeping a stale token.
    if expires_at in (None, ""):
        return True
    try:
        return float(expires_at) > now
    except (TypeError, ValueError):
        return False


def token_status_from_snapshot(snapshot: dict[str, Any], app_id: str = DEFAULT_APP_ID, now: float | None = None) -> TokenStatus:
    now = time.time() if now is None else now
    tokens = snapshot.get("tokens") or {}
    local_tokens = snapshot.get("localTokens") or {}
    token_count = len(tokens) if isinstance(tokens, dict) else 0
    if not isinstance(tokens, dict):
        return TokenStatus(False, "tokens_not_dict", token_count=0)
    local_key = local_tokens.get(app_id) if isinstance(local_tokens, dict) else None
    if local_key:
        token = tokens.get(local_key)
        if isinstance(token, dict) and _is_unexpired(token, now):
            exp = token.get("expiresAt")
            return TokenStatus(True, "valid_local_token", str(local_key), float(exp) if exp else None, token_count)
        if isinstance(token, dict):
            return TokenStatus(False, "local_token_expired", str(local_key), token.get("expiresAt"), token_count)
        return TokenStatus(False, "local_token_missing", str(local_key), None, token_count)
    # A configured app identity is a hard binding.  Tokens belonging to another
    # app must never attest readiness for this app merely because they are
    # unexpired.
    if app_id:
        return TokenStatus(False, "local_token_unbound", token_count=token_count)
    for key, token in tokens.items():
        if isinstance(token, dict) and _is_unexpired(token, now):
            exp = token.get("expiresAt")
            return TokenStatus(True, "valid_any_token", str(key), float(exp) if exp else None, token_count)
    if token_count:
        return TokenStatus(False, "all_tokens_expired_or_invalid", token_count=token_count)
    return TokenStatus(False, "no_tokens", token_count=0)


def plan_login(token_valid: bool, lock_active: bool, port_busy: bool, cleanup_stale: bool, force_refresh: bool = False) -> LoginPlan:
    if token_valid and not force_refresh:
        return LoginPlan("token_valid")
    if lock_active:
        return LoginPlan("login_already_in_progress")
    if port_busy and cleanup_stale:
        return LoginPlan("cleanup_stale_then_login", should_spawn=True, should_kill_stale=True)
    if port_busy:
        return LoginPlan("port_busy")
    return LoginPlan("force_refresh_login" if token_valid else "start_login", should_spawn=True)


def _run_json_node(script: str, timeout: int = 20) -> dict[str, Any]:
    result = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout or "node command failed").strip())
    return json.loads(result.stdout or "{}")


def auth_snapshot(root: Path = DEFAULT_ROOT) -> dict[str, Any]:
    store = root / "dist/auth/store.js"
    script = f"""
const {{ authStore }} = require({json.dumps(str(store))});
(async()=>{{
  await authStore.initialize();
  const s = authStore.storageDataCache || {{}};
  process.stdout.write(JSON.stringify({{
    tokens: s.tokens || {{}},
    clients: s.clients || {{}},
    localTokens: s.localTokens || {{}}
  }}));
  process.exit(0);
}})().catch(e=>{{ process.stderr.write(String(e)); process.exit(1); }});
"""
    return _run_json_node(script)


def _scalar_string(value: Any) -> str:
    """Return a safe scalar string from loose auth-store/env values.

    Some auth-store snapshots have historically carried tuple/list-shaped
    values after wrapper code merged credential candidates. Passing those
    directly to subprocess.Popen makes Python fail before lark-mcp starts
    (for example: "sequence item 0: expected str instance, tuple found").
    """
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        for item in value:
            scalar = _scalar_string(item)
            if scalar:
                return scalar
        return ""
    if isinstance(value, (str, bytes, os.PathLike)):
        return os.fsdecode(value)
    return str(value)


def _scope_list(value: Any) -> list[str]:
    """Normalize lark-mcp OAuth scopes to the string-array contract.

    Recent lark-mcp releases call ``options.scope.join(' ')``.  Passing the
    historical space-delimited scalar raises ``TypeError: _a.join is not a
    function`` before an authorization URL can be created.
    """
    values = value if isinstance(value, (list, tuple)) else [value]
    scopes: list[str] = []
    for item in values:
        scopes.extend(part for part in _scalar_string(item).split() if part)
    return scopes


def credentials_from_snapshot(snapshot: dict[str, Any], app_id: str = DEFAULT_APP_ID) -> tuple[str, str]:
    # Prefer explicit env, then token.extra from a previous successful login, then client store.
    # Support both Lark and Feishu aliases because Hermes profiles/docs use both names.
    env_id = _scalar_string(os.environ.get("LARK_APP_ID") or os.environ.get("FEISHU_APP_ID") or os.environ.get("APP_ID"))
    env_secret = _scalar_string(os.environ.get("LARK_APP_SECRET") or os.environ.get("FEISHU_APP_SECRET") or os.environ.get("APP_SECRET"))
    if env_id and env_secret and (not app_id or env_id == app_id):
        return env_id, env_secret
    for token in (snapshot.get("tokens") or {}).values():
        if not isinstance(token, dict):
            continue
        extra = token.get("extra") or {}
        cid = _scalar_string(extra.get("appId") or extra.get("app_id") or extra.get("client_id"))
        sec = _scalar_string(extra.get("appSecret") or extra.get("app_secret") or extra.get("client_secret"))
        if cid and sec and (not app_id or cid == app_id):
            return cid, sec
    for client in (snapshot.get("clients") or {}).values():
        if not isinstance(client, dict):
            continue
        cid = _scalar_string(client.get("appId") or client.get("app_id") or client.get("client_id"))
        sec = _scalar_string(client.get("appSecret") or client.get("app_secret") or client.get("client_secret"))
        if cid and sec and (not app_id or cid == app_id) and not cid.startswith("client_id_for_local_auth"):
            return cid, sec
    return "", ""


def port_busy(port: int = DEFAULT_PORT) -> bool:
    result = subprocess.run(["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN"], capture_output=True, text=True, timeout=10)
    return bool(result.stdout.strip())


def stale_lark_login_pids(port: int = DEFAULT_PORT) -> list[int]:
    ps = subprocess.run(["ps", "axo", "pid=,command="], capture_output=True, text=True, timeout=10)
    pids: list[int] = []
    for line in ps.stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split(None, 1)
        if len(parts) != 2:
            continue
        pid_s, cmd = parts
        if "lark-mcp login" in cmd and f"--port {port}" in cmd:
            try:
                pids.append(int(pid_s))
            except ValueError:
                pass
    return pids


def kill_stale_lark_logins(port: int = DEFAULT_PORT) -> list[int]:
    killed = []
    for pid in stale_lark_login_pids(port):
        if pid == os.getpid():
            continue
        try:
            os.kill(pid, signal.SIGTERM)
            killed.append(pid)
        except ProcessLookupError:
            pass
    if killed:
        time.sleep(1)
    return killed


def _blue_authorize_button_bbox(image_path: Path) -> tuple[int, int, int, int] | None:
    """Find the Lark authorization blue button in a macOS screenshot.

    The OAuth page is localized and the web-view accessibility tree is not
    consistently scriptable from Terminal. The stable visual invariant is the
    large Lark-blue primary button near the lower-right of the authorization
    card. Return its screenshot-pixel bounding box, ignoring small blue links.
    """
    try:
        from PIL import Image
    except Exception:
        return None
    img = Image.open(image_path).convert("RGB")
    width, height = img.size
    pixels = img.load()
    visited: set[tuple[int, int]] = set()
    candidates: list[tuple[int, int, int, int, int]] = []

    def is_lark_blue(x: int, y: int) -> bool:
        r, g, b = pixels[x, y]
        # Primary button is close to #3370ff. Keep the band permissive enough
        # for antialiasing but narrow enough to reject grey/black text.
        return b >= 185 and 25 <= r <= 95 and 80 <= g <= 155 and (b - g) >= 70 and (g - r) >= 20

    # Search where the consent button actually lives. This also avoids the
    # account-switch link near the top of the card.
    x0 = int(width * 0.45)
    y0 = int(height * 0.45)
    for y in range(y0, height, 2):
        for x in range(x0, width, 2):
            if (x, y) in visited or not is_lark_blue(x, y):
                continue
            stack = [(x, y)]
            visited.add((x, y))
            min_x = max_x = x
            min_y = max_y = y
            count = 0
            while stack:
                cx, cy = stack.pop()
                count += 1
                min_x = min(min_x, cx)
                max_x = max(max_x, cx)
                min_y = min(min_y, cy)
                max_y = max(max_y, cy)
                for nx, ny in ((cx + 2, cy), (cx - 2, cy), (cx, cy + 2), (cx, cy - 2)):
                    if nx < x0 or ny < y0 or nx >= width or ny >= height or (nx, ny) in visited:
                        continue
                    if is_lark_blue(nx, ny):
                        visited.add((nx, ny))
                        stack.append((nx, ny))
            box_w = max_x - min_x + 1
            box_h = max_y - min_y + 1
            # The primary 授权 button is large; links are thin/small.
            if box_w >= 80 and box_h >= 30 and count >= 600:
                candidates.append((count, min_x, min_y, max_x, max_y))
    if not candidates:
        return None
    _, min_x, min_y, max_x, max_y = max(candidates, key=lambda item: (item[0], item[2], item[1]))
    return min_x, min_y, max_x, max_y


def _click_screenshot_pixel(x: int, y: int, screenshot_width: int, screenshot_height: int) -> None:
    if platform.system() != "Darwin":
        raise RuntimeError("auto_authorize_click_requires_macos")
    try:
        import Quartz
    except Exception as exc:
        raise RuntimeError(f"quartz_unavailable:{exc}") from exc
    display = Quartz.CGMainDisplayID()
    bounds = Quartz.CGDisplayBounds(display)
    scale_x = float(bounds.size.width) / float(screenshot_width)
    scale_y = float(bounds.size.height) / float(screenshot_height)
    point = Quartz.CGPoint(x * scale_x, y * scale_y)
    Quartz.CGWarpMouseCursorPosition(point)
    time.sleep(0.05)
    for event_type in (Quartz.kCGEventLeftMouseDown, Quartz.kCGEventLeftMouseUp):
        event = Quartz.CGEventCreateMouseEvent(None, event_type, point, Quartz.kCGMouseButtonLeft)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
        time.sleep(0.05)


def auto_click_authorize(timeout: int = 25, *, deadline: float | None = None) -> dict[str, Any]:
    """Best-effort click of the visible Lark 授权 button in the user's browser.

    This intentionally clicks only the large Lark-blue primary button on the
    current screen. It does not type credentials and it fails closed when the
    button cannot be found.
    """
    if platform.system() != "Darwin":
        return {"ok": False, "reason": "unsupported_platform"}
    local_deadline = time.monotonic() + max(1, timeout)
    deadline = min(local_deadline, deadline) if deadline is not None else local_deadline
    last_reason = "not_started"
    attempts = 0
    while time.monotonic() < deadline:
        attempts += 1
        path = Path(tempfile.gettempdir()) / f"hermes_lark_oauth_screen_{os.getpid()}.png"
        remaining = max(0.001, deadline - time.monotonic())
        try:
            shot = subprocess.run(
                ["screencapture", "-x", str(path)],
                capture_output=True,
                text=True,
                timeout=min(10, remaining),
            )
        except subprocess.TimeoutExpired:
            last_reason = "screencapture_timeout"
            break
        if shot.returncode != 0:
            last_reason = (shot.stderr or shot.stdout or "screencapture_failed").strip()
            time.sleep(min(0.5, max(0.0, deadline - time.monotonic())))
            continue
        try:
            from PIL import Image
            with Image.open(path) as img:
                screenshot_width, screenshot_height = img.size
            bbox = _blue_authorize_button_bbox(path)
            if not bbox:
                last_reason = "authorize_button_not_found"
                time.sleep(min(0.7, max(0.0, deadline - time.monotonic())))
                continue
            min_x, min_y, max_x, max_y = bbox
            click_x = (min_x + max_x) // 2
            click_y = (min_y + max_y) // 2
            _click_screenshot_pixel(click_x, click_y, screenshot_width, screenshot_height)
            return {"ok": True, "reason": "clicked", "bbox": [min_x, min_y, max_x, max_y], "attempts": attempts}
        except Exception as exc:
            last_reason = str(exc)
            time.sleep(min(0.7, max(0.0, deadline - time.monotonic())))
        finally:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
    return {"ok": False, "reason": last_reason, "attempts": attempts}


def _process_group_alive(pgid: int) -> bool:
    try:
        os.killpg(pgid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _terminate_login_tree(
    proc: subprocess.Popen[str],
    grace_seconds: int = 2,
    *,
    deadline: float | None = None,
) -> None:
    pgid = proc.pid
    deadline = time.monotonic() + max(0, grace_seconds) if deadline is None else deadline

    def wait_with_budget() -> None:
        remaining = max(0.0, deadline - time.monotonic())
        try:
            proc.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            pass

    try:
        os.killpg(pgid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    wait_with_budget()
    if _process_group_alive(pgid):
        try:
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    wait_with_budget()


def run_login(snapshot: dict[str, Any], app_id: str, domain: str, port: int, scopes: str, open_browser: bool, timeout: int, auto_authorize: bool = False, auto_authorize_timeout: int = 25, handler_path: Path | None = None) -> dict[str, Any]:
    effective_timeout = min(max(1, int(timeout)), 300)
    overall_deadline = time.monotonic() + effective_timeout
    cleanup_reserve = min(0.25, effective_timeout / 4)
    work_deadline = overall_deadline - cleanup_reserve
    real_app_id, app_secret = credentials_from_snapshot(snapshot, app_id=app_id)
    if not real_app_id or not app_secret:
        return {"ok": False, "action": "credentials_missing"}
    handler_path = handler_path or DEFAULT_ROOT / "dist/cli/login-handler.js"
    args = ["node", "-e", NODE_LOGIN_BRIDGE, str(handler_path)]
    child_env = {
        key: os.environ[key]
        for key in ("PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "LC_CTYPE")
        if key in os.environ
    }
    proc = subprocess.Popen(
        args,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        start_new_session=True,
        env=child_env,
    )
    if proc.stdin is None:
        _terminate_login_tree(proc, deadline=overall_deadline)
        return {"ok": False, "action": "login_failed"}
    try:
        proc.stdin.write(json.dumps({
            "appId": _scalar_string(real_app_id),
            "appSecret": _scalar_string(app_secret),
            "domain": _scalar_string(domain),
            "host": "localhost",
            "port": str(port),
            "scope": _scope_list(scopes),
            "timeout": effective_timeout * 1000,
        }))
        proc.stdin.close()
    except (BrokenPipeError, OSError):
        _terminate_login_tree(proc, deadline=overall_deadline)
        return {"ok": False, "action": "login_failed"}
    opened = False
    auto_authorize_result: dict[str, Any] | None = None
    auth_url = ""
    output: list[str] = []
    output_buffer = ""
    while True:
        if proc.poll() is not None:
            break
        remaining = work_deadline - time.monotonic()
        if remaining <= 0:
            _terminate_login_tree(proc, deadline=overall_deadline)
            return {"ok": False, "action": "login_timeout", "auth_url": auth_url, "opened": opened, "auto_authorize": auto_authorize_result, "output_tail": output[-10:]}
        line = ""
        if proc.stdout is not None:
            readable, _, _ = select.select([proc.stdout], [], [], min(0.1, remaining))
            if readable:
                try:
                    line = os.read(proc.stdout.fileno(), 4096).decode("utf-8", errors="replace")
                except (BlockingIOError, OSError):
                    line = ""
        if line:
            output.append(line.rstrip("\n"))
            output_buffer = (output_buffer + line)[-16384:]
            if not auth_url:
                auth_url = extract_auth_url(output_buffer)
            if auth_url and open_browser and not opened:
                try:
                    subprocess.run(
                        ["open", auth_url],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=max(0.001, work_deadline - time.monotonic()),
                    )
                except subprocess.TimeoutExpired:
                    _terminate_login_tree(proc, deadline=overall_deadline)
                    return {"ok": False, "action": "login_timeout", "auth_url": auth_url, "opened": False, "auto_authorize": auto_authorize_result, "output_tail": output[-10:]}
                opened = True
                if auto_authorize:
                    auto_authorize_result = auto_click_authorize(
                        timeout=min(max(1, int(auto_authorize_timeout)), max(1, int(work_deadline - time.monotonic()))),
                        deadline=work_deadline,
                    )
    return {"ok": proc.returncode == 0, "action": "login_completed", "returncode": proc.returncode, "auth_url": auth_url, "opened": opened, "auto_authorize": auto_authorize_result, "output_tail": output[-10:]}


def redact_secret(value: Any, keep_start: int = 8, keep_end: int = 4) -> Any:
    if not isinstance(value, str):
        return value
    if not value:
        return value
    if len(value) <= keep_start + keep_end + 3:
        return "***"
    return f"{value[:keep_start]}...{value[-keep_end:]}"


def redact_result(result: dict[str, Any]) -> dict[str, Any]:
    redacted = json.loads(json.dumps(result, ensure_ascii=False))
    for unsafe_key in ("output_tail", "auth_url", "error"):
        redacted.pop(unsafe_key, None)
    token_status = redacted.get("token_status")
    if isinstance(token_status, dict) and token_status.get("token_key"):
        token_status["token_key"] = redact_secret(token_status["token_key"])
    auto_authorize = redacted.get("auto_authorize")
    if isinstance(auto_authorize, dict):
        safe_auto: dict[str, Any] = {}
        if isinstance(auto_authorize.get("ok"), bool):
            safe_auto["ok"] = auto_authorize["ok"]
        reason = auto_authorize.get("reason")
        allowed_reasons = {"clicked", "unsupported_platform", "authorize_button_not_found", "not_started"}
        safe_auto["reason"] = reason if reason in allowed_reasons else "auto_authorize_failed"
        if isinstance(auto_authorize.get("attempts"), int):
            safe_auto["attempts"] = auto_authorize["attempts"]
        redacted["auto_authorize"] = safe_auto
    for key in ("app_secret", "client_secret", "access_token", "refresh_token", "token"):
        if key in redacted:
            redacted[key] = "***"
    return redacted


def ensure_login(args: argparse.Namespace) -> dict[str, Any]:
    # Token-store inspection is read-only and is required for status-only to
    # distinguish a valid bound token from an actual recovery requirement.
    snapshot = auth_snapshot(Path(args.root))
    token_status = token_status_from_snapshot(snapshot, app_id=args.app_id)
    lock = SingleFlightLock(Path(args.lock), stale_seconds=args.lock_stale_seconds)
    active = lock.is_active(cleanup_stale=not args.status_only)
    busy = port_busy(args.port)
    plan = plan_login(token_status.valid, active, busy, args.cleanup_stale, args.force_refresh)
    result: dict[str, Any] = {
        "ok": plan.action == "token_valid",
        "action": plan.action,
        "token_status": asdict(token_status),
        "port": args.port,
        "port_busy": busy,
        "lock_active": active,
        "status_only": args.status_only,
    }
    if args.status_only:
        result["planned_action"] = plan.action
        if plan.should_spawn:
            result["action"] = "auth_required"
        return result
    if not plan.should_spawn:
        return result
    if args.auto_authorize and args.no_open:
        result.update({
            "ok": False,
            "action": "invalid_args",
            "error": "--auto-authorize requires opening the OAuth URL; remove --no-open or run status-only without --force-refresh",
        })
        return result
    if not lock.acquire():
        result.update({"ok": False, "action": "login_already_in_progress"})
        return result
    try:
        if plan.should_kill_stale:
            result["killed_pids"] = kill_stale_lark_logins(args.port)
        latest = auth_snapshot(Path(args.root))
        latest_status = token_status_from_snapshot(latest, app_id=args.app_id)
        if latest_status.valid and not args.force_refresh:
            result.update({"ok": True, "action": "token_became_valid", "token_status": asdict(latest_status)})
            return result
        login_result = run_login(
            latest,
            args.app_id,
            args.domain,
            args.port,
            args.scope,
            not args.no_open,
            args.timeout,
            args.auto_authorize,
            args.auto_authorize_timeout,
            Path(args.root) / "dist/cli/login-handler.js",
        )
        final_snapshot = auth_snapshot(Path(args.root))
        final_status = token_status_from_snapshot(final_snapshot, app_id=args.app_id)
        result.update(login_result)
        result["token_status"] = asdict(final_status)
        result["ok"] = bool(login_result.get("ok")) and final_status.valid
        if result["ok"]:
            result["action"] = "login_success"
        return result
    finally:
        lock.release()


def _durable_auto_authorize_valid(profile_value: str | None, grant_root_value: str | None) -> bool:
    if not profile_value or not grant_root_value:
        return False
    flow_path = Path(__file__).with_name("lark_task_flow.py")
    try:
        spec = importlib.util.spec_from_file_location("hermes_lark_task_flow_authority", flow_path)
        if not spec or not spec.loader:
            return False
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return bool(module.oauth_recovery_auto_authorized(Path(profile_value), Path(grant_root_value)))
    except (OSError, ImportError, AttributeError, TypeError, ValueError):
        return False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Single-flight Lark OAuth login guard")
    parser.add_argument("--json", action="store_true", help="print JSON result")
    parser.add_argument("--root", default=str(DEFAULT_ROOT), help="lark-mcp installation root")
    parser.add_argument("--app-id", default=os.environ.get("LARK_APP_ID", DEFAULT_APP_ID))
    parser.add_argument("--domain", default=os.environ.get("LARK_DOMAIN", DEFAULT_DOMAIN))
    parser.add_argument("--port", type=int, default=int(os.environ.get("LARK_OAUTH_PORT", DEFAULT_PORT)))
    parser.add_argument("--scope", default=os.environ.get("LARK_OAUTH_SCOPE", DEFAULT_SCOPES))
    parser.add_argument("--lock", default=str(DEFAULT_LOCK))
    parser.add_argument("--lock-stale-seconds", type=int, default=330)
    parser.add_argument("--cleanup-stale", action="store_true", help="terminate stale lark-mcp login on the chosen port before spawning")
    parser.add_argument("--force-refresh", action="store_true", help="run OAuth login even when the current token is still valid; useful for explicit token refresh tests")
    parser.add_argument("--status-only", action="store_true", help="read token, lock, and callback-port state without starting or cleaning up OAuth login")
    parser.add_argument("--no-open", action="store_true", help="do not open browser when auth URL appears")
    parser.add_argument("--no-auto-authorize", dest="auto_authorize", action="store_false", help="explicitly disable auto-authorization, overriding ambient environment")
    parser.set_defaults(auto_authorize=False)
    parser.add_argument("--authorized-auto-authorize-profile", help=argparse.SUPPRESS)
    parser.add_argument("--authorized-auto-authorize-grant-root", help=argparse.SUPPRESS)
    parser.add_argument("--auto-authorize-timeout", type=int, default=int(os.environ.get("LARK_AUTO_AUTHORIZE_TIMEOUT", "25")))
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--bound-defaults", action="store_true", help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.bound_defaults:
        args.app_id = DEFAULT_APP_ID
        args.domain = DEFAULT_DOMAIN
        args.port = DEFAULT_PORT
        args.scope = DEFAULT_SCOPES
        args.auto_authorize_timeout = min(max(1, args.auto_authorize_timeout), 300)
    authority_profile = args.authorized_auto_authorize_profile
    authority_root = args.authorized_auto_authorize_grant_root
    authority_requested = bool(authority_profile or authority_root)
    authority_valid = bool(
        authority_profile
        and authority_root
        and not args.status_only
        and _durable_auto_authorize_valid(authority_profile, authority_root)
    )
    args.auto_authorize = authority_valid
    try:
        if authority_requested and not authority_valid:
            result = {"ok": False, "action": "authority_grant_invalid", "status_only": args.status_only}
        else:
            result = ensure_login(args)
    except Exception:
        result = {"ok": False, "action": "error", "error_code": "unhandled_guard_error"}
    try:
        result["lock_active_after"] = SingleFlightLock(
            Path(args.lock), stale_seconds=args.lock_stale_seconds
        ).is_active(cleanup_stale=not args.status_only and not (authority_requested and not authority_valid))
    except Exception:
        result["lock_active_after"] = False
        result.update({"ok": False, "action": "error", "error_code": "post_readback_failed"})
    try:
        result["port_busy_after"] = port_busy(args.port)
    except Exception:
        result["port_busy_after"] = False
        result.update({"ok": False, "action": "error", "error_code": "post_readback_failed"})
    if args.json:
        print(json.dumps(redact_result(result), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        public_actions = {
            "auth_required", "authority_grant_invalid", "cleanup_stale_then_login", "credentials_missing", "error",
            "force_refresh_login", "invalid_args", "login_already_in_progress",
            "login_completed", "login_failed", "login_success", "login_timeout",
            "port_busy", "start_login", "token_became_valid", "token_valid",
        }
        action = result.get("action")
        print(action if action in public_actions else "operation_failed")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
