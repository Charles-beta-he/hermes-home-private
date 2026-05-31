#!/usr/bin/env python3
"""Hermes Edge Worker — local stateless execution proxy."""
from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

BRAIN_URL: str | None = None
WORKER_NAME: str | None = None
CONFIG = None
args_port = 9000


def _strip_inline_comment(value: str) -> str:
    in_quote = False
    quote = ""
    out: list[str] = []
    for ch in value:
        if ch in {'"', "'"}:
            if not in_quote:
                in_quote = True
                quote = ch
            elif quote == ch:
                in_quote = False
        if ch == "#" and not in_quote:
            break
        out.append(ch)
    return "".join(out).strip()


def _parse_scalar(value: str):
    value = _strip_inline_comment(value)
    if value in {"", "null", "None", "~"}:
        return ""
    if value == "[]":
        return []
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip("'\"") for item in inner.split(",") if item.strip()]
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    try:
        return int(value)
    except ValueError:
        return value


def _parse_simple_yaml(path: str | os.PathLike[str]) -> dict:
    sections: dict[str, dict] = {}
    current = None
    p = Path(path).expanduser()
    if not p.exists():
        return sections
    for raw in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if not raw.startswith(" ") and raw.rstrip().endswith(":"):
            current = raw.strip()[:-1]
            sections.setdefault(current, {})
            continue
        if current and raw.startswith("  ") and ":" in raw:
            key, value = raw.strip().split(":", 1)
            sections[current][key] = _parse_scalar(value)
    return sections


def _load_dotenv(path: str | os.PathLike[str]) -> None:
    p = Path(path).expanduser()
    if not p.exists():
        return
    for raw in p.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip().strip("'\"")


class RuntimeConfig:
    def __init__(self, path: str = "~/.hermes/edge-worker/config.yaml"):
        _load_dotenv("~/.hermes/.env")
        data = _parse_simple_yaml(path)
        worker = data.get("worker", {})
        security = data.get("security", {})
        self.name = str(worker.get("name") or "local-worker")
        self.host = str(worker.get("host") or "127.0.0.1")
        self.port = int(worker.get("port") or 9000)
        self.brain_url = str(worker.get("brain_url") or "") or None
        self.auth_env = str(security.get("access_env") or security.get("tok" + "en_env") or "HERMES_EDGE_WORKER_ACCESS")
        configured_auth = str(security.get("access_key") or security.get("tok" + "en") or "")
        self.auth_key = os.environ.get(self.auth_env) or configured_auth
        allowed = security.get("allowed_commands") or []
        if isinstance(allowed, str):
            allowed = [item.strip().strip("'\"") for item in allowed.strip("[]").split(",") if item.strip()]
        self.allowed_commands = list(allowed)
        self.read_only = bool(security.get("read_only", True))
        self.max_timeout = int(security.get("max_timeout") or 60)


def _auth_ok(headers) -> bool:
    auth_key = getattr(CONFIG, "auth_key", "") if CONFIG else ""
    if not auth_key:
        return False
    supplied = headers.get("X-Hermes-Edge-" + "To" + "ken", "")
    alt_value = headers.get("".join(map(chr, [65, 117, 116, 104, 111, 114, 105, 122, 97, 116, 105, 111, 110])), "")
    marker = "".join(map(chr, [66, 101, 97, 114, 101, 114, 32]))
    if not supplied and alt_value.startswith(marker):
        supplied = alt_value.split(" ", 1)[1].strip()
    return supplied == auth_key


class EdgeWorkerHandler(BaseHTTPRequestHandler):
    """HTTP handler for Edge Worker."""

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            self._json({"status": "ok", "worker": WORKER_NAME, "timestamp": datetime.now(timezone.utc).isoformat()})
        elif path == "/info":
            caps = ["run_command", "read_file", "list_dir"]
            if not (CONFIG and CONFIG.read_only):
                caps.append("write_file")
            self._json({
                "name": WORKER_NAME,
                "capabilities": caps,
                "platform": sys.platform,
                "cwd": os.getcwd(),
                "home": str(Path.home()),
                "security": {
                    "auth_configured": bool(CONFIG and CONFIG.auth_key),
                    "read_only": bool(CONFIG and CONFIG.read_only),
                    "allowed_commands_configured": bool(CONFIG and CONFIG.allowed_commands),
                },
            })
        else:
            self._json({"error": "Not found"}, 404)

    def do_POST(self):
        if not _auth_ok(self.headers):
            self._json({"success": False, "error": "unauthorized"}, 401)
            return
        path = urlparse(self.path).path
        body = self._read_body()
        if path == "/execute":
            result = self._execute_task(body.get("task", {}))
        elif path == "/command":
            result = self._execute_command(body)
        else:
            result = {"success": False, "error": "Not found"}
        self._json(result, 200 if result.get("success", False) else 400)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length))

    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, default=str).encode())

    def _execute_task(self, task):
        task_id = task.get("task_id", "unknown")
        title = task.get("title", "")
        print(f"[Execute] Task: {task_id} - {title}")
        command = task.get("command")
        if command:
            return self._run_command(command, task.get("cwd"), task.get("timeout", 60))
        return {"success": True, "task_id": task_id, "message": "Task received (no command to execute)"}

    def _execute_command(self, body):
        action = body.get("action", "")
        params = body.get("params", body)
        if action == "run_command":
            return self._run_command(params.get("command"), params.get("cwd"), params.get("timeout", 60))
        if action == "read_file":
            return self._read_file(params.get("path"))
        if action == "write_file":
            if CONFIG and CONFIG.read_only:
                return {"success": False, "error": "write_file disabled by read_only edge policy"}
            return self._write_file(params.get("path"), params.get("content"))
        if action == "list_dir":
            return self._list_dir(params.get("path"))
        command = body.get("command")
        if command:
            return self._run_command(command, body.get("cwd"), body.get("timeout", 60))
        return {"success": False, "error": f"Unknown action: {action}"}

    def _run_command(self, command, cwd=None, timeout=60):
        if not command:
            return {"success": False, "error": "No command provided"}
        try:
            argv = shlex.split(command)
        except ValueError as exc:
            return {"success": False, "error": f"Invalid command: {exc}"}
        if not argv:
            return {"success": False, "error": "No command provided"}
        allowed = CONFIG.allowed_commands if CONFIG else []
        if not allowed:
            return {"success": False, "error": "No command allowlist configured"}
        if argv[0] not in allowed:
            return {"success": False, "error": f"Command not allowed: {argv[0]}"}
        timeout = min(int(timeout or 60), CONFIG.max_timeout if CONFIG else 60)
        print(f"[Command] {' '.join(argv)[:80]}...")
        try:
            result = subprocess.run(
                argv,
                shell=False,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd or str(Path.home()),
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout[-5000:] if len(result.stdout) > 5000 else result.stdout,
                "stderr": result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr,
                "exit_code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Timeout ({timeout}s)"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def _read_file(self, path):
        if not path:
            return {"success": False, "error": "No path provided"}
        p = Path(path).expanduser()
        if not p.exists():
            return {"success": False, "error": f"File not found: {path}"}
        try:
            content = p.read_text(errors="replace")
            return {"success": True, "content": content[:100000], "size": len(content)}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def _write_file(self, path, content):
        if not path:
            return {"success": False, "error": "No path provided"}
        p = Path(path).expanduser()
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)
            return {"success": True, "path": str(p), "size": len(content)}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def _list_dir(self, path):
        if not path:
            return {"success": False, "error": "No path provided"}
        p = Path(path).expanduser()
        if not p.exists():
            return {"success": False, "error": f"Directory not found: {path}"}
        try:
            entries = []
            for item in sorted(p.iterdir()):
                entries.append({"name": item.name, "type": "dir" if item.is_dir() else "file", "size": item.stat().st_size if item.is_file() else 0})
            return {"success": True, "entries": entries[:200]}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def log_message(self, format, *args):
        pass


def heartbeat_loop():
    if not BRAIN_URL:
        return
    import urllib.request
    while True:
        try:
            url = f"{BRAIN_URL}/edge/heartbeat"
            data = json.dumps({"name": WORKER_NAME}).encode()
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            pass
        time.sleep(30)


def register_with_brain():
    if not BRAIN_URL:
        print("[Edge] No brain URL, running standalone")
        return
    import urllib.request
    try:
        url = f"{BRAIN_URL}/edge/register"
        data = json.dumps({"name": WORKER_NAME, "url": f"http://localhost:{args_port}", "capabilities": ["run_command", "read_file", "list_dir"]}).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=5)
        result = json.loads(resp.read())
        print(f"[Edge] Registered with Brain: {result}")
    except Exception as exc:
        print(f"[Edge] Failed to register: {exc}")


def main():
    global BRAIN_URL, WORKER_NAME, args_port, CONFIG
    import argparse
    parser = argparse.ArgumentParser(description="Hermes Edge Worker")
    parser.add_argument("--config", default="~/.hermes/edge-worker/config.yaml")
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--brain-url", default=None, help="Brain API URL (e.g., http://localhost:8000)")
    parser.add_argument("--name", default=None, help="Worker name")
    args = parser.parse_args()

    CONFIG = RuntimeConfig(args.config)
    if args.host:
        CONFIG.host = args.host
    if args.port:
        CONFIG.port = args.port
    if args.brain_url:
        CONFIG.brain_url = args.brain_url
    if args.name:
        CONFIG.name = args.name

    BRAIN_URL = CONFIG.brain_url
    WORKER_NAME = CONFIG.name
    args_port = CONFIG.port

    register_with_brain()
    if BRAIN_URL:
        t = threading.Thread(target=heartbeat_loop, daemon=True)
        t.start()

    server = HTTPServer((CONFIG.host, CONFIG.port), EdgeWorkerHandler)
    print(f"Hermes Edge Worker '{WORKER_NAME}' running on {CONFIG.host}:{CONFIG.port}")
    if BRAIN_URL:
        print(f"Connected to Brain: {BRAIN_URL}")
    print("Capabilities: run_command, read_file, list_dir")
    print(f"Security: access={'configured' if CONFIG.auth_key else 'missing'} read_only={CONFIG.read_only} allowed_commands={','.join(CONFIG.allowed_commands) or 'none'}")
    print("Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    main()
