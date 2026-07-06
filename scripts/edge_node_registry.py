#!/usr/bin/env python3
"""Hermes Edge Node Registry selfcheck.

This module observes local/registered edge nodes and reports health/capability
security warnings. Dispatch remains SSOT-safe: the registry can enable automatic
read-only edge leases, but it never owns tasks and never mutates the canonical
task pool.
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))).expanduser()
STATE_DIR = Path(os.environ.get("HERMES_STATE_DIR", str(HERMES_HOME / "state"))).expanduser()
REGISTRY_PATH = Path(os.environ.get("HERMES_EDGE_NODE_REGISTRY", str(STATE_DIR / "edge_node_registry.json"))).expanduser()
EDGE_CONFIG_PATH = Path(os.environ.get("HERMES_EDGE_WORKER_CONFIG", str(HERMES_HOME / "edge-worker" / "config.yaml"))).expanduser()
DEFAULT_HEARTBEAT_STALE_SECONDS = int(os.environ.get("HERMES_EDGE_HEARTBEAT_STALE_SECONDS", "120"))
DEFAULT_PROBE_TIMEOUT_SECONDS = float(os.environ.get("HERMES_EDGE_PROBE_TIMEOUT_SECONDS", "0.75"))
DANGEROUS_REMOTE_CAPABILITIES = {"write_file", "run_command", "browser_action", "browser_screenshot", "deploy"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_iso(value: str) -> float | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value).timestamp()
    except Exception:
        return None


def stable_worker_id(name: str, host: str, port: int) -> str:
    safe = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in (name or "edge-worker"))
    return f"local:{safe}:{host}:{port}"


def _strip_inline_comment(value: str) -> str:
    in_quote = False
    quote = ""
    out = []
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


def _parse_scalar(value: str) -> Any:
    value = _strip_inline_comment(value)
    if value in {"", "null", "None", "~"}:
        return ""
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    if value == "[]":
        return []
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    try:
        return int(value)
    except ValueError:
        return value


def _dotenv_has_key(key: str) -> bool:
    env_path = HERMES_HOME / ".env"
    if not key or not env_path.exists():
        return False
    prefix = key + "="
    return any(line.strip().startswith(prefix) for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines())


def read_edge_config(path: Path = EDGE_CONFIG_PATH) -> dict[str, Any]:
    """Read the small edge-worker config shape without requiring PyYAML.

    The parser is deliberately tiny and only extracts top-level section scalars
    used by the selfcheck. It never returns credential values; presence is
    represented by token_configured=True only for registry compatibility.
    """
    if not path.exists():
        return {"exists": False, "path": str(path)}
    sections: dict[str, dict[str, Any]] = {}
    current: str | None = None
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if not raw.startswith(" ") and raw.rstrip().endswith(":"):
            current = raw.strip()[:-1]
            sections.setdefault(current, {})
            continue
        if current and raw.startswith("  ") and ":" in raw:
            key, value = raw.strip().split(":", 1)
            parsed = _parse_scalar(value)
            if current == "security" and key in {"access_key", "token"}:
                sections[current]["token_configured"] = bool(parsed)
            else:
                sections[current][key] = parsed
    security_section = sections.get("security", {})
    access_env = str(security_section.get("access_env") or security_section.get("token_env") or "")
    if access_env and (os.environ.get(access_env) or _dotenv_has_key(access_env)):
        security_section["token_configured"] = True
    worker = sections.get("worker", {})
    security = sections.get("security", {})
    return {
        "exists": True,
        "path": str(path),
        "worker": worker,
        "security": security,
        "logging": sections.get("logging", {}),
    }


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    if not path.exists():
        return {"schema": "edge_node_registry_v1", "nodes": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"schema": "edge_node_registry_v1", "nodes": [], "load_error": str(exc)}
    if isinstance(data, dict):
        nodes = data.get("nodes", [])
        if isinstance(nodes, dict):
            data["nodes"] = list(nodes.values())
        elif not isinstance(nodes, list):
            data["nodes"] = []
        return data
    return {"schema": "edge_node_registry_v1", "nodes": [], "load_error": "registry root must be object"}


def local_config_node(config: dict[str, Any]) -> dict[str, Any] | None:
    if not config.get("exists"):
        return None
    worker = config.get("worker") or {}
    security = config.get("security") or {}
    name = str(worker.get("name") or socket.gethostname() or "local-edge")
    host = str(worker.get("host") or "127.0.0.1")
    try:
        port = int(worker.get("port") or 9000)
    except Exception:
        port = 9000
    probe_host = "127.0.0.1" if host in {"0.0.0.0", "::", ""} else host
    capabilities = ["run_command", "read_file", "list_dir"]
    if not bool(security.get("read_only", True)):
        capabilities.append("write_file")
    return {
        "worker_id": stable_worker_id(name, host, port),
        "name": name,
        "source": "local_config",
        "endpoint": f"http://{probe_host}:{port}",
        "bind_host": host,
        "port": port,
        "brain_url": str(worker.get("brain_url") or ""),
        "standalone_mode": bool(worker.get("standalone_mode") or worker.get("standalone")),
        "heartbeat_interval_s": int(worker.get("heartbeat_interval") or 30),
        "capabilities": capabilities,
        "trust_level": "local_configured",
        "token_configured": bool(security.get("token_configured")),
        "allowed_commands_configured": bool(security.get("allowed_commands")),
        "lease_policy": str(security.get("lease_policy") or ""),
        "max_timeout_s": int(security.get("max_timeout") or 300),
    }


def registry_nodes(registry: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for node in registry.get("nodes") or []:
        if isinstance(node, dict):
            clean = dict(node)
            if "token" in clean:
                clean.pop("token", None)
                clean["token_configured"] = True
            result.append(clean)
    return result


def merge_nodes(*node_lists: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for nodes in node_lists:
        for node in nodes:
            worker_id = str(node.get("worker_id") or node.get("id") or node.get("name") or "")
            if not worker_id:
                continue
            existing = merged.get(worker_id, {})
            existing.update(node)
            merged[worker_id] = existing
    return list(merged.values())


def _urlopen_no_proxy(req_or_url: Any, *, timeout: float):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    return opener.open(req_or_url, timeout=timeout)


def probe_endpoint(endpoint: str, timeout: float = DEFAULT_PROBE_TIMEOUT_SECONDS) -> dict[str, Any]:
    if not endpoint:
        return {"probe_status": "missing_endpoint"}
    base = endpoint.rstrip("/")
    try:
        with _urlopen_no_proxy(f"{base}/health", timeout=timeout) as resp:
            raw = resp.read(32_000)
        health = json.loads(raw.decode("utf-8", errors="replace"))
    except urllib.error.URLError as exc:
        return {"probe_status": "unreachable", "error": str(exc.reason)}
    except Exception as exc:
        return {"probe_status": "error", "error": str(exc)}
    info: dict[str, Any] | None = None
    try:
        with _urlopen_no_proxy(f"{base}/info", timeout=timeout) as resp:
            info = json.loads(resp.read(32_000).decode("utf-8", errors="replace"))
    except Exception:
        info = None
    return {"probe_status": "ok", "health": health, "info": info}


def classify_node(node: dict[str, Any], *, now: float, probe: bool, registry_dispatch_enabled: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    capabilities = list(node.get("capabilities") or [])
    endpoint = str(node.get("endpoint") or node.get("url") or "")
    last_seen = str(node.get("last_seen_at") or node.get("last_heartbeat") or "")
    heartbeat_ts = parse_iso(last_seen)
    heartbeat_age_s = None if heartbeat_ts is None else max(0, int(now - heartbeat_ts))
    status = str(node.get("status") or "unknown")

    if heartbeat_age_s is not None and heartbeat_age_s > DEFAULT_HEARTBEAT_STALE_SECONDS:
        status = "offline"
        warnings.append(f"heartbeat stale: {heartbeat_age_s}s")
    elif heartbeat_age_s is not None and status in {"registered", "unknown"}:
        status = "healthy"

    if not node.get("brain_url") and not node.get("standalone_mode"):
        warnings.append("brain_url missing; node is standalone")
    if not node.get("token_configured"):
        warnings.append("token not configured")
    if str(node.get("bind_host") or "") == "0.0.0.0" and not node.get("token_configured"):
        errors.append("0.0.0.0 endpoint without token is unsafe")
    if "run_command" in capabilities and not node.get("allowed_commands_configured"):
        warnings.append("run_command has no command allowlist; remote auto-dispatch must stay disabled")
    risky = sorted(DANGEROUS_REMOTE_CAPABILITIES.intersection(capabilities))
    if risky and not node.get("lease_policy"):
        warnings.append(f"dangerous capabilities present: {','.join(risky)}; require explicit lease policy")

    probe_result = None
    if probe and endpoint:
        probe_result = probe_endpoint(endpoint)
        if probe_result.get("probe_status") == "ok":
            status = "healthy" if status in {"unknown", "registered", "offline"} else status
            warnings = [w for w in warnings if not w.startswith("heartbeat stale:")]
            heartbeat_age_s = 0
            info = probe_result.get("info") or {}
            if isinstance(info, dict) and info.get("capabilities"):
                capabilities = list(info.get("capabilities") or capabilities)
        else:
            warnings.append(f"health probe {probe_result.get('probe_status')}: {probe_result.get('error', '')}".strip())
            if status not in {"disabled", "quarantined"}:
                status = "degraded"

    dispatch_eligible = (
        registry_dispatch_enabled
        and bool(node.get("dispatch_enabled"))
        and status == "healthy"
        and bool(node.get("token_configured"))
        and bool(node.get("allowed_commands_configured"))
        and not errors
    )
    return {
        "worker_id": node.get("worker_id"),
        "name": node.get("name"),
        "source": node.get("source", "registry"),
        "endpoint": endpoint,
        "status": status,
        "dispatch_eligible": dispatch_eligible,
        "capabilities": capabilities,
        "heartbeat_age_s": heartbeat_age_s,
        "trust_level": node.get("trust_level", "unknown"),
        "warnings": warnings,
        "errors": errors,
        "probe": probe_result,
    }


def save_registry(registry: dict[str, Any], path: Path = REGISTRY_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def register_local(*, path: Path = REGISTRY_PATH) -> dict[str, Any]:
    config = read_edge_config(EDGE_CONFIG_PATH)
    local = local_config_node(config)
    if not local:
        return {"status": "FAIL", "error": f"edge worker config missing: {EDGE_CONFIG_PATH}", "registry_path": str(path)}
    registry = load_registry(path)
    def _same_local_worker(node: dict[str, Any]) -> bool:
        return (
            node.get("source") == "local_config"
            and node.get("name") == local.get("name")
            and int(node.get("port") or 0) == int(local.get("port") or 0)
        )

    nodes = [
        node for node in registry_nodes(registry)
        if node.get("worker_id") != local.get("worker_id") and not _same_local_worker(node)
    ]
    now = utc_now_iso()
    node = dict(local)
    node.update({
        "registered_at": now,
        "last_seen_at": now,
        "status": "registered",
        "dispatch_enabled": bool(registry.get("dispatch_enabled", False)),
    })
    # Never persist plaintext token material.
    node.pop("token", None)
    nodes.append(node)
    out = {
        "schema": "edge_node_registry_v1",
        "read_only_dispatch": True,
        "dispatch_enabled": bool(registry.get("dispatch_enabled", False)),
        "updated_at": now,
        "nodes": nodes,
    }
    save_registry(out, path)
    return {"status": "OK", "registered": node.get("worker_id"), "registry_path": str(path), "dispatch_enabled": bool(out.get("dispatch_enabled"))}


def selfcheck(*, probe: bool = True) -> dict[str, Any]:
    registry = load_registry(REGISTRY_PATH)
    config = read_edge_config(EDGE_CONFIG_PATH)
    local = local_config_node(config)
    nodes = merge_nodes(registry_nodes(registry), [local] if local else [])
    now = time.time()
    registry_dispatch_enabled = bool(registry.get("dispatch_enabled", False))
    checked = [classify_node(node, now=now, probe=probe, registry_dispatch_enabled=registry_dispatch_enabled) for node in nodes]
    warnings: list[str] = []
    errors: list[str] = []

    if registry.get("load_error"):
        errors.append(f"registry load error: {registry['load_error']}")
    if not REGISTRY_PATH.exists():
        warnings.append(f"registry file missing: {REGISTRY_PATH}")
    if not checked:
        warnings.append("no edge nodes registered or configured")

    seen: set[str] = set()
    for node in checked:
        wid = str(node.get("worker_id") or "")
        if wid in seen:
            errors.append(f"duplicate worker_id: {wid}")
        seen.add(wid)
        for item in node.get("warnings") or []:
            warnings.append(f"{node.get('name') or wid}: {item}")
        for item in node.get("errors") or []:
            errors.append(f"{node.get('name') or wid}: {item}")

    if errors:
        status = "FAIL"
    elif warnings:
        status = "WARN"
    else:
        status = "PASS"
    return {
        "status": status,
        "schema": "edge_node_selfcheck_v1",
        "read_only": True,
        "dispatch_enabled": registry_dispatch_enabled,
        "registry_path": str(REGISTRY_PATH),
        "config_path": str(EDGE_CONFIG_PATH),
        "node_count": len(checked),
        "dispatch_eligible_count": sum(1 for node in checked if node.get("dispatch_eligible")),
        "nodes": checked,
        "warnings": warnings,
        "errors": errors,
        "timestamp": utc_now_iso(),
    }


def print_result(result: dict[str, Any], as_json: bool) -> int:
    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result.get("status", "UNKNOWN"))
        print(f"nodes: {result.get('node_count', 0)} dispatch_eligible: {result.get('dispatch_eligible_count', 0)}")
        for warning in result.get("warnings", []):
            print(f"WARN: {warning}")
        for error in result.get("errors", []):
            print(f"ERROR: {error}")
    return 0 if result.get("status") in {"OK", "PASS", "WARN"} else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hermes edge node registry/selfcheck (read-only)")
    sub = parser.add_subparsers(dest="cmd")
    sc = sub.add_parser("selfcheck")
    sc.add_argument("--json", action="store_true")
    sc.add_argument("--no-probe", action="store_true", help="Do not call local /health endpoints")
    rl = sub.add_parser("register-local", help="Register the configured local edge worker in the registry; does not enable dispatch")
    rl.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.cmd in {None, "selfcheck"}:
        return print_result(selfcheck(probe=not getattr(args, "no_probe", False)), getattr(args, "json", False))
    if args.cmd == "register-local":
        result = register_local()
        return print_result(result, getattr(args, "json", False))
    parser.error(f"unknown command: {args.cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
