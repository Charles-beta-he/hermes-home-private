#!/usr/bin/env python3
from __future__ import annotations
"""Single-flight Lark OAuth guard for Hermes.

Avoids the failure mode observed when multiple raw `lark-mcp login` commands
are launched in the background: duplicate Authorization URL notifications,
EADDRINUSE on localhost:3010, and stale watch-pattern messages after one login
already succeeded.

Default behavior is conservative:
- if a valid token already exists, do not spawn anything;
- if another guarded login is running, do not spawn a second one;
- if port 3010 is busy, fail closed unless --cleanup-stale is set;
- when spawning, open the authorization URL at most once.
"""

import argparse
import json
import os
import re
import signal
import subprocess
import sys
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
DEFAULT_PORT = 3010
DEFAULT_SCOPES = "auth:user.id:read task:task:read task:tasklist:read"
AUTH_URL_RE = re.compile(r"https?://localhost:\d+/authorize\?[^\s\r\n]+")


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
    def __init__(self, path: Path, stale_seconds: int = 180) -> None:
        self.path = path
        self.stale_seconds = stale_seconds
        self.acquired = False

    def is_active(self, now: float | None = None) -> bool:
        now = time.time() if now is None else now
        try:
            stat = self.path.stat()
        except FileNotFoundError:
            return False
        if now - stat.st_mtime > self.stale_seconds:
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
    for key, token in tokens.items():
        if isinstance(token, dict) and _is_unexpired(token, now):
            exp = token.get("expiresAt")
            return TokenStatus(True, "valid_any_token", str(key), float(exp) if exp else None, token_count)
    if token_count:
        return TokenStatus(False, "all_tokens_expired_or_invalid", token_count=token_count)
    return TokenStatus(False, "no_tokens", token_count=0)


def plan_login(token_valid: bool, lock_active: bool, port_busy: bool, cleanup_stale: bool) -> LoginPlan:
    if token_valid:
        return LoginPlan("token_valid")
    if lock_active:
        return LoginPlan("login_already_in_progress")
    if port_busy and cleanup_stale:
        return LoginPlan("cleanup_stale_then_login", should_spawn=True, should_kill_stale=True)
    if port_busy:
        return LoginPlan("port_busy")
    return LoginPlan("start_login", should_spawn=True)


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


def credentials_from_snapshot(snapshot: dict[str, Any], app_id: str = DEFAULT_APP_ID) -> tuple[str, str]:
    # Prefer explicit env, then token.extra from a previous successful login, then client store.
    env_id = os.environ.get("LARK_APP_ID") or os.environ.get("APP_ID")
    env_secret = os.environ.get("LARK_APP_SECRET") or os.environ.get("APP_SECRET")
    if env_id and env_secret:
        return env_id, env_secret
    for token in (snapshot.get("tokens") or {}).values():
        if not isinstance(token, dict):
            continue
        extra = token.get("extra") or {}
        cid = extra.get("appId") or extra.get("app_id") or extra.get("client_id")
        sec = extra.get("appSecret") or extra.get("app_secret") or extra.get("client_secret")
        if cid and sec and (not app_id or cid == app_id):
            return str(cid), str(sec)
    for client in (snapshot.get("clients") or {}).values():
        if not isinstance(client, dict):
            continue
        cid = client.get("appId") or client.get("app_id") or client.get("client_id")
        sec = client.get("appSecret") or client.get("app_secret") or client.get("client_secret")
        if cid and sec and not str(cid).startswith("client_id_for_local_auth"):
            return str(cid), str(sec)
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


def run_login(snapshot: dict[str, Any], app_id: str, domain: str, port: int, scopes: str, open_browser: bool, timeout: int) -> dict[str, Any]:
    real_app_id, app_secret = credentials_from_snapshot(snapshot, app_id=app_id)
    if not real_app_id or not app_secret:
        return {"ok": False, "action": "credentials_missing"}
    args = [
        "lark-mcp", "login",
        "--app-id", real_app_id,
        "--app-secret", app_secret,
        "--domain", domain,
        "--port", str(port),
        "--scope", scopes,
    ]
    proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    opened = False
    auth_url = ""
    output: list[str] = []
    deadline = time.time() + timeout
    while True:
        if proc.stdout is not None:
            line = proc.stdout.readline()
        else:
            line = ""
        if line:
            output.append(line.rstrip("\n"))
            if not auth_url:
                auth_url = extract_auth_url(line)
            if auth_url and open_browser and not opened:
                subprocess.run(["open", auth_url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                opened = True
        if proc.poll() is not None:
            break
        if time.time() > deadline:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            return {"ok": False, "action": "login_timeout", "auth_url": auth_url, "opened": opened, "output_tail": output[-10:]}
        if not line:
            time.sleep(0.1)
    return {"ok": proc.returncode == 0, "action": "login_completed", "returncode": proc.returncode, "auth_url": auth_url, "opened": opened, "output_tail": output[-10:]}


def redact_secret(value: Any, keep_start: int = 8, keep_end: int = 4) -> Any:
    if not isinstance(value, str):
        return value
    if len(value) <= keep_start + keep_end + 3:
        return value
    return f"{value[:keep_start]}...{value[-keep_end:]}"


def redact_result(result: dict[str, Any]) -> dict[str, Any]:
    redacted = json.loads(json.dumps(result, ensure_ascii=False))
    token_status = redacted.get("token_status")
    if isinstance(token_status, dict) and token_status.get("token_key"):
        token_status["token_key"] = redact_secret(token_status["token_key"])
    for key in ("app_secret", "client_secret", "access_token", "refresh_token", "token"):
        if key in redacted:
            redacted[key] = "***"
    return redacted


def ensure_login(args: argparse.Namespace) -> dict[str, Any]:
    snapshot = auth_snapshot(Path(args.root))
    token_status = token_status_from_snapshot(snapshot, app_id=args.app_id)
    lock = SingleFlightLock(Path(args.lock), stale_seconds=args.lock_stale_seconds)
    active = lock.is_active()
    busy = port_busy(args.port)
    plan = plan_login(token_status.valid, active, busy, args.cleanup_stale)
    result: dict[str, Any] = {
        "ok": plan.action == "token_valid",
        "action": plan.action,
        "token_status": asdict(token_status),
        "port": args.port,
        "port_busy": busy,
        "lock_active": active,
    }
    if not plan.should_spawn:
        return result
    if not lock.acquire():
        result.update({"ok": False, "action": "login_already_in_progress"})
        return result
    try:
        if plan.should_kill_stale:
            result["killed_pids"] = kill_stale_lark_logins(args.port)
        latest = auth_snapshot(Path(args.root))
        latest_status = token_status_from_snapshot(latest, app_id=args.app_id)
        if latest_status.valid:
            result.update({"ok": True, "action": "token_became_valid", "token_status": asdict(latest_status)})
            return result
        login_result = run_login(latest, args.app_id, args.domain, args.port, args.scope, not args.no_open, args.timeout)
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Single-flight Lark OAuth login guard")
    parser.add_argument("--json", action="store_true", help="print JSON result")
    parser.add_argument("--root", default=str(DEFAULT_ROOT), help="lark-mcp installation root")
    parser.add_argument("--app-id", default=os.environ.get("LARK_APP_ID", DEFAULT_APP_ID))
    parser.add_argument("--domain", default=os.environ.get("LARK_DOMAIN", DEFAULT_DOMAIN))
    parser.add_argument("--port", type=int, default=int(os.environ.get("LARK_OAUTH_PORT", DEFAULT_PORT)))
    parser.add_argument("--scope", default=os.environ.get("LARK_OAUTH_SCOPE", DEFAULT_SCOPES))
    parser.add_argument("--lock", default=str(DEFAULT_LOCK))
    parser.add_argument("--lock-stale-seconds", type=int, default=180)
    parser.add_argument("--cleanup-stale", action="store_true", help="terminate stale lark-mcp login on the chosen port before spawning")
    parser.add_argument("--no-open", action="store_true", help="do not open browser when auth URL appears")
    parser.add_argument("--timeout", type=int, default=90)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = ensure_login(args)
    except Exception as exc:
        result = {"ok": False, "action": "error", "error": str(exc)}
    if args.json:
        print(json.dumps(redact_result(result), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(result.get("action", "unknown"))
        if result.get("auth_url"):
            print(result["auth_url"])
        if result.get("error"):
            print(result["error"], file=sys.stderr)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
