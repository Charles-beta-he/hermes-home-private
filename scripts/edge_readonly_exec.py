#!/usr/bin/env python3
"""Explicit Phase-2 read-only command smoke for Hermes edge workers.

This is not taskpool dispatch. It is a manual/explicit probe that sends one
read-only command to one registered edge node and returns a proof bundle.
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))).expanduser()
REGISTRY_PATH = Path(os.environ.get("HERMES_EDGE_NODE_REGISTRY", str(HERMES_HOME / "state" / "edge_node_registry.json"))).expanduser()
ENV_PATH = HERMES_HOME / ".env"
SAFE_COMMANDS = {"date", "uname", "pwd"}


def load_dotenv(path: Path = ENV_PATH) -> None:
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


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"registry not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit("registry root must be object")
    return data


def select_node(registry: dict[str, Any], worker_id: str | None = None) -> dict[str, Any]:
    nodes = registry.get("nodes") or []
    if not isinstance(nodes, list):
        raise SystemExit("registry nodes must be list")
    candidates = [n for n in nodes if isinstance(n, dict)]
    if worker_id:
        candidates = [n for n in candidates if n.get("worker_id") == worker_id]
    if not candidates:
        raise SystemExit("no matching edge node in registry")
    return candidates[0]


def validate_readonly_command(command: str) -> list[str]:
    try:
        argv = shlex.split(command)
    except ValueError as exc:
        raise SystemExit(f"invalid command: {exc}") from exc
    if not argv:
        raise SystemExit("empty command")
    if argv[0] not in SAFE_COMMANDS:
        raise SystemExit(f"command is not in Phase-2 read-only client allowlist: {argv[0]}")
    return argv


def post_command(endpoint: str, token: str, command: str, timeout: float) -> dict[str, Any]:
    payload = json.dumps({"action": "run_command", "params": {"command": command, "timeout": int(timeout)}}).encode()
    req = urllib.request.Request(
        endpoint.rstrip("/") + "/command",
        data=payload,
        headers={"Content-Type": "application/json", "X-Hermes-Edge-Token": token},
        method="POST",
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(req, timeout=timeout + 2) as resp:
            status = resp.status
            body = resp.read(64_000)
    except urllib.error.HTTPError as exc:
        status = exc.code
        body = exc.read(64_000)
    return {"http_status": status, "body": json.loads(body.decode("utf-8", errors="replace"))}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Explicit read-only edge execution smoke")
    parser.add_argument("command", nargs="?", default="pwd", help="read-only command: date, uname, or pwd")
    parser.add_argument("--worker-id")
    parser.add_argument("--token-env", default="HERMES_EDGE_WORKER_TOKEN")
    parser.add_argument("--timeout", type=float, default=5)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    argv_checked = validate_readonly_command(args.command)
    load_dotenv()
    token = os.environ.get(args.token_env, "")
    if not token:
        raise SystemExit(f"missing token env: {args.token_env}")
    registry = load_registry()
    node = select_node(registry, args.worker_id)
    endpoint = str(node.get("endpoint") or "")
    if not endpoint:
        raise SystemExit("selected node has no endpoint")
    result = post_command(endpoint, token, " ".join(shlex.quote(part) for part in argv_checked), args.timeout)
    proof = {
        "schema": "edge_readonly_exec_proof_v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "worker_id": node.get("worker_id"),
        "endpoint": endpoint,
        "command": " ".join(argv_checked),
        "http_status": result["http_status"],
        "success": bool(result["body"].get("success")),
        "exit_code": result["body"].get("exit_code"),
        "stdout": result["body"].get("stdout", ""),
        "stderr": result["body"].get("stderr", ""),
        "token_redacted": True,
    }
    if args.json:
        print(json.dumps(proof, ensure_ascii=False, indent=2))
    else:
        print(f"success={proof['success']} worker={proof['worker_id']} command={proof['command']} exit={proof['exit_code']}")
        print(str(proof["stdout"]).rstrip())
    return 0 if proof["success"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
