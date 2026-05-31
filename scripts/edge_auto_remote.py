#!/usr/bin/env python3
"""Automatic read-only remote execution router for Hermes edge nodes.

This is the Phase-3 bridge from brain/task events to edge workers. It does not
create a second task pool: it consumes one explicit event/command, selects an
eligible registered edge node, executes a read-only lease, and writes an audit
record for the canonical brain/taskpool layer to reference.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))).expanduser()
STATE_DIR = Path(os.environ.get("HERMES_STATE_DIR", str(HERMES_HOME / "state"))).expanduser()
LOG_DIR = Path(os.environ.get("HERMES_LOG_DIR", str(HERMES_HOME / "logs"))).expanduser()
REGISTRY_PATH = Path(os.environ.get("HERMES_EDGE_NODE_REGISTRY", str(STATE_DIR / "edge_node_registry.json"))).expanduser()
PAUSE_PATH = Path(os.environ.get("HERMES_EDGE_REMOTE_PAUSE", str(STATE_DIR / "edge_remote_pause"))).expanduser()
AUDIT_PATH = Path(os.environ.get("HERMES_EDGE_REMOTE_AUDIT", str(LOG_DIR / "edge-remote-dispatch.jsonl"))).expanduser()
ENV_PATH = HERMES_HOME / ".env"
DEFAULT_ACCESS_ENV = "HERMES_EDGE_WORKER_ACCESS"
READONLY_COMMANDS = {"date", "uname", "pwd"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_dotenv(path: Path | None = None) -> None:
    path = path or ENV_PATH
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip().strip("'\"")


def load_registry(path: Path | None = None) -> dict[str, Any]:
    path = path or REGISTRY_PATH
    if not path.exists():
        return {"schema": "edge_node_registry_v1", "dispatch_enabled": False, "nodes": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("edge registry root must be an object")
    nodes = data.get("nodes") or []
    if isinstance(nodes, dict):
        data["nodes"] = list(nodes.values())
    elif not isinstance(nodes, list):
        data["nodes"] = []
    return data


def save_registry(data: dict[str, Any], path: Path | None = None) -> None:
    path = path or REGISTRY_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = utc_now()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def set_dispatch_enabled(enabled: bool) -> dict[str, Any]:
    registry = load_registry()
    registry["dispatch_enabled"] = enabled
    registry["read_only_dispatch"] = True
    for node in registry.get("nodes") or []:
        if isinstance(node, dict):
            node["dispatch_enabled"] = enabled
    save_registry(registry)
    return {
        "status": "OK",
        "dispatch_enabled": enabled,
        "read_only_dispatch": True,
        "registry_path": str(REGISTRY_PATH),
        "ux": {
            "mode": "automatic_read_only" if enabled else "paused",
            "escape": f"touch {PAUSE_PATH}",
            "resume": f"rm -f {PAUSE_PATH}",
        },
    }


def validate_command(command: str) -> list[str]:
    try:
        argv = shlex.split(command)
    except ValueError as exc:
        raise ValueError(f"invalid command: {exc}") from exc
    if not argv:
        raise ValueError("empty command")
    if argv[0] not in READONLY_COMMANDS:
        raise PermissionError(f"not in automatic read-only allowlist: {argv[0]}")
    return argv


def node_is_eligible(node: dict[str, Any], registry_enabled: bool) -> bool:
    if not registry_enabled or not bool(node.get("dispatch_enabled")):
        return False
    if str(node.get("status") or "").lower() not in {"healthy", "registered"}:
        return False
    if not node.get("endpoint"):
        return False
    if not node.get("token_configured"):
        return False
    if not node.get("allowed_commands_configured"):
        return False
    return True


def select_node(registry: dict[str, Any], worker_id: str | None = None) -> dict[str, Any]:
    enabled = bool(registry.get("dispatch_enabled"))
    candidates = [n for n in (registry.get("nodes") or []) if isinstance(n, dict)]
    if worker_id:
        candidates = [n for n in candidates if n.get("worker_id") == worker_id]
    eligible = [n for n in candidates if node_is_eligible(n, enabled)]
    if not eligible:
        raise RuntimeError("no eligible edge node; run edge_node_registry.py register-local and enable-dispatch")
    eligible.sort(key=lambda n: (str(n.get("trust_level") or ""), str(n.get("worker_id") or "")))
    return eligible[0]


def make_lease_id(worker_id: str, command: str, event_id: str | None) -> str:
    raw = f"{utc_now()}:{worker_id}:{event_id or ''}:{command}:{os.getpid()}"
    return "edge-lease-" + hashlib.sha256(raw.encode()).hexdigest()[:16]


def post_command(endpoint: str, access_value: str, command: str, timeout: float) -> dict[str, Any]:
    payload = json.dumps({"action": "run_command", "params": {"command": command, "timeout": int(timeout)}}).encode()
    req = urllib.request.Request(
        endpoint.rstrip("/") + "/command",
        data=payload,
        headers={"Content-Type": "application/json", "X-Hermes-Edge-Token": access_value},
        method="POST",
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(req, timeout=timeout + 2) as resp:
            return {"http_status": resp.status, "body": json.loads(resp.read(128_000).decode("utf-8", errors="replace"))}
    except urllib.error.HTTPError as exc:
        body = exc.read(128_000).decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = {"success": False, "error": body[:500]}
        return {"http_status": exc.code, "body": parsed}


def append_audit(record: dict[str, Any]) -> None:
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def build_blocked(reason: str, *, event: dict[str, Any] | None = None, command: str | None = None) -> dict[str, Any]:
    record = {
        "schema": "edge_auto_remote_result_v1",
        "timestamp": utc_now(),
        "status": "blocked",
        "success": False,
        "reason": reason,
        "command": command,
        "event_id": (event or {}).get("event_id"),
        "user_message": f"Remote edge auto-dispatch blocked safely: {reason}",
        "ux": {
            "mode": "safe_block",
            "escape": f"touch {PAUSE_PATH}",
            "audit_path": str(AUDIT_PATH),
        },
    }
    append_audit(record)
    return record


def dispatch(command: str, *, worker_id: str | None = None, event: dict[str, Any] | None = None, timeout: float = 5.0) -> dict[str, Any]:
    if PAUSE_PATH.exists():
        return build_blocked(f"escape pause file exists: {PAUSE_PATH}", event=event, command=command)
    try:
        argv = validate_command(command)
    except PermissionError as exc:
        return build_blocked(str(exc), event=event, command=command)
    except ValueError as exc:
        return build_blocked(str(exc), event=event, command=command)

    load_dotenv()
    access_value = os.environ.get(DEFAULT_ACCESS_ENV) or os.environ.get("HERMES_EDGE_WORKER_TOKEN") or ""
    if not access_value:
        return build_blocked(f"missing access environment: {DEFAULT_ACCESS_ENV}", event=event, command=command)

    registry = load_registry()
    try:
        node = select_node(registry, worker_id)
    except Exception as exc:
        return build_blocked(str(exc), event=event, command=command)

    normalized = " ".join(shlex.quote(part) for part in argv)
    lease_id = make_lease_id(str(node.get("worker_id") or ""), normalized, (event or {}).get("event_id"))
    started = utc_now()
    result = post_command(str(node.get("endpoint")), access_value, normalized, timeout)
    finished = utc_now()
    body = result.get("body") or {}
    proof = {
        "schema": "edge_auto_remote_result_v1",
        "timestamp": finished,
        "status": "completed" if body.get("success") else "failed",
        "success": bool(body.get("success")),
        "lease_id": lease_id,
        "event_id": (event or {}).get("event_id"),
        "event_type": (event or {}).get("event_type"),
        "worker_id": node.get("worker_id"),
        "endpoint": node.get("endpoint"),
        "command": normalized,
        "read_only": True,
        "auto_dispatch": True,
        "http_status": result.get("http_status"),
        "exit_code": body.get("exit_code"),
        "stdout": body.get("stdout", ""),
        "stderr": body.get("stderr", ""),
        "started_at": started,
        "finished_at": finished,
        "access_redacted": True,
        "audit_path": str(AUDIT_PATH),
        "ux": {
            "mode": "automatic_read_only",
            "summary": "Executed on an edge node automatically under a read-only lease.",
            "escape": f"touch {PAUSE_PATH}",
        },
    }
    append_audit(proof)
    return proof


def event_to_command(event: dict[str, Any]) -> str:
    for key in ("command", "readonly_command"):
        value = event.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    payload = event.get("payload")
    if isinstance(payload, dict):
        for key in ("command", "readonly_command"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    raise SystemExit("event does not contain command/readonly_command")


def print_result(result: dict[str, Any], as_json: bool) -> int:
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"status={result.get('status')} success={result.get('success')} mode={(result.get('ux') or {}).get('mode')}")
        if result.get("lease_id"):
            print(f"lease={result.get('lease_id')} worker={result.get('worker_id')} command={result.get('command')}")
        if result.get("reason"):
            print(f"reason={result.get('reason')}")
        stdout = str(result.get("stdout") or "").rstrip()
        if stdout:
            print(stdout)
        print(f"audit={result.get('audit_path') or AUDIT_PATH}")
    return 0 if result.get("success") or result.get("status") == "OK" else 2


def status() -> dict[str, Any]:
    registry = load_registry()
    nodes = [n for n in registry.get("nodes") or [] if isinstance(n, dict)]
    return {
        "status": "OK",
        "schema": "edge_auto_remote_status_v1",
        "dispatch_enabled": bool(registry.get("dispatch_enabled")),
        "read_only_dispatch": bool(registry.get("read_only_dispatch", True)),
        "pause_active": PAUSE_PATH.exists(),
        "eligible_nodes": sum(1 for n in nodes if node_is_eligible(n, bool(registry.get("dispatch_enabled")))),
        "node_count": len(nodes),
        "allowlist": sorted(READONLY_COMMANDS),
        "audit_path": str(AUDIT_PATH),
        "ux": {
            "mode": "automatic_read_only" if registry.get("dispatch_enabled") and not PAUSE_PATH.exists() else "paused_or_disabled",
            "escape": f"touch {PAUSE_PATH}",
            "resume": f"rm -f {PAUSE_PATH}",
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hermes automatic read-only edge dispatch")
    sub = parser.add_subparsers(dest="cmd")
    st = sub.add_parser("status")
    st.add_argument("--json", action="store_true")
    en = sub.add_parser("enable")
    en.add_argument("--json", action="store_true")
    dis = sub.add_parser("disable")
    dis.add_argument("--json", action="store_true")
    run = sub.add_parser("dispatch")
    run.add_argument("command", nargs="?", default="pwd")
    run.add_argument("--worker-id")
    run.add_argument("--timeout", type=float, default=5)
    run.add_argument("--json", action="store_true")
    ev = sub.add_parser("event")
    ev.add_argument("--event-json", required=True, help="JSON object containing event_id/event_type and command")
    ev.add_argument("--worker-id")
    ev.add_argument("--timeout", type=float, default=5)
    ev.add_argument("--json", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.cmd in {None, "status"}:
        return print_result(status(), args.json)
    if args.cmd == "enable":
        return print_result(set_dispatch_enabled(True), args.json)
    if args.cmd == "disable":
        return print_result(set_dispatch_enabled(False), args.json)
    if args.cmd == "dispatch":
        return print_result(dispatch(args.command, worker_id=args.worker_id, timeout=args.timeout), args.json)
    if args.cmd == "event":
        event = json.loads(args.event_json)
        if not isinstance(event, dict):
            raise SystemExit("event JSON must be an object")
        return print_result(dispatch(event_to_command(event), worker_id=args.worker_id, event=event, timeout=args.timeout), args.json)
    parser.error(f"unknown command: {args.cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
