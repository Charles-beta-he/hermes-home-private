#!/usr/bin/env python3
"""Read-only UUMit public-surface probe for Hermes evidence gathering.

Scope:
- No credentials.
- No write/paid/UT endpoints.
- No MCP tool execution; only public SSE handshake.
- Outputs compact JSON suitable for taskpool evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

DEFAULT_TIMEOUT = 12
UA = "HermesUUMitReadonlyProbe/0.1 (+https://hermes-agent.nousresearch.com)"
API = "https://api.uumit.com"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def request(
    method: str,
    url: str,
    *,
    body: bytes | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    headers: dict[str, str] | None = None,
    max_bytes: int = 5_000_000,
) -> dict[str, Any]:
    req_headers = {"User-Agent": UA, **(headers or {})}
    req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
    started = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as resp:
            raw = resp.read(max_bytes)
            elapsed_ms = round((time.monotonic() - started) * 1000)
            content_type = resp.headers.get("content-type", "")
            text = raw.decode("utf-8", errors="replace")
            parsed = None
            if "json" in content_type or text[:1] in ("{", "["):
                try:
                    parsed = json.loads(text)
                except json.JSONDecodeError:
                    parsed = None
            return {
                "ok": True,
                "method": method,
                "url": url,
                "status": resp.status,
                "elapsed_ms": elapsed_ms,
                "content_type": content_type,
                "bytes_read": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "json": parsed,
                "text_preview": text[:1000] if parsed is None else None,
                "truncated_at_bytes": max_bytes if len(raw) == max_bytes else None,
            }
    except urllib.error.HTTPError as e:
        raw = e.read(64_000)
        text = raw.decode("utf-8", errors="replace")
        parsed = None
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            pass
        return {
            "ok": False,
            "method": method,
            "url": url,
            "status": e.code,
            "elapsed_ms": round((time.monotonic() - started) * 1000),
            "content_type": e.headers.get("content-type", ""),
            "bytes_read": len(raw),
            "json": parsed,
            "text_preview": text[:1000] if parsed is None else None,
        }
    except Exception as e:  # noqa: BLE001 - diagnostic tool must preserve failure shape
        return {
            "ok": False,
            "method": method,
            "url": url,
            "status": None,
            "elapsed_ms": round((time.monotonic() - started) * 1000),
            "error_type": type(e).__name__,
            "error": str(e),
        }


def sse_handshake(url: str, *, timeout: int = 8) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/event-stream"}, method="GET")
    started = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as resp:
            lines: list[str] = []
            for _ in range(6):
                line = resp.readline(4096)
                if not line:
                    break
                lines.append(line.decode("utf-8", errors="replace").rstrip("\r\n"))
                if len(lines) >= 2 and lines[-1] == "":
                    break
            return {
                "ok": True,
                "method": "GET",
                "url": url,
                "status": resp.status,
                "elapsed_ms": round((time.monotonic() - started) * 1000),
                "content_type": resp.headers.get("content-type", ""),
                "lines": lines,
                "text_preview": "\n".join(lines),
            }
    except Exception as e:  # noqa: BLE001
        return {
            "ok": False,
            "method": "GET",
            "url": url,
            "status": None,
            "elapsed_ms": round((time.monotonic() - started) * 1000),
            "error_type": type(e).__name__,
            "error": str(e),
        }


def summarize_openapi(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"available": False}
    paths = payload.get("paths") or {}
    tags: dict[str, int] = {}
    method_counts: dict[str, int] = {}
    sample_paths: list[str] = []
    for path, item in paths.items():
        if len(sample_paths) < 30:
            sample_paths.append(path)
        if not isinstance(item, dict):
            continue
        for method, operation in item.items():
            method_l = method.lower()
            if method_l not in {"get", "post", "put", "patch", "delete", "options", "head"}:
                continue
            method_counts[method_l.upper()] = method_counts.get(method_l.upper(), 0) + 1
            if isinstance(operation, dict):
                for tag in operation.get("tags") or []:
                    tags[str(tag)] = tags.get(str(tag), 0) + 1
    return {
        "available": True,
        "openapi": payload.get("openapi"),
        "info": payload.get("info"),
        "path_count": len(paths),
        "method_counts": method_counts,
        "schema_count": len(((payload.get("components") or {}).get("schemas") or {})),
        "top_tags": sorted(tags.items(), key=lambda kv: kv[1], reverse=True)[:20],
        "sample_paths": sample_paths,
    }


def summarize_agent_card(payload: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"available": False}
    skills = payload.get("skills") or payload.get("capabilities") or []
    return {
        "available": True,
        "name": payload.get("name"),
        "protocol": payload.get("protocol") or payload.get("protocolVersion"),
        "authentication_keys": sorted((payload.get("authentication") or {}).keys()) if isinstance(payload.get("authentication"), dict) else None,
        "capability_keys": sorted((payload.get("capabilities") or {}).keys()) if isinstance(payload.get("capabilities"), dict) else None,
        "skill_count": len(skills) if isinstance(skills, list) else None,
    }


def summarize_list(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"available": False}
    data = payload.get("data", payload)
    items = None
    if isinstance(data, dict):
        for key in ("items", "records", "list", "capabilities", "demands"):
            if isinstance(data.get(key), list):
                items = data[key]
                break
    elif isinstance(data, list):
        items = data
    sample = []
    for item in (items or [])[:3]:
        if isinstance(item, dict):
            sample.append({k: item.get(k) for k in ("id", "title", "name", "category", "price_ut", "status") if k in item})
    return {"available": True, "item_count_in_response": len(items or []), "sample": sample}


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe UUMit public surfaces without credentials or writes")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--include-sandbox-key", action="store_true", help="Also call the public temporary GET-only sandbox-key endpoint")
    args = parser.parse_args()

    probes: dict[str, dict[str, Any]] = {}
    probes["openapi"] = request("GET", f"{API}/api/v1/public/openapi.json", timeout=args.timeout)
    probes["agent_card"] = request("GET", f"{API}/.well-known/agent.json", timeout=args.timeout)
    probes["community_stats"] = request("GET", f"{API}/api/v1/public/community-stats", timeout=args.timeout)
    probes["capabilities"] = request("GET", f"{API}/api/v1/capabilities?page=1&page_size=3", timeout=args.timeout)
    probes["demands"] = request("GET", f"{API}/api/v1/demands?page=1&page_size=3", timeout=args.timeout)
    probes["mcp_sse_handshake"] = sse_handshake(f"{API}/mcp/sse", timeout=min(args.timeout, 8))
    probes["a2a_unauth_guard"] = request(
        "POST",
        f"{API}/a2a",
        body=json.dumps({"jsonrpc": "2.0", "method": "tasks/get", "params": {"id": "00000000-0000-0000-0000-000000000000"}, "id": "probe"}).encode("utf-8"),
        timeout=args.timeout,
        headers={"Content-Type": "application/json"},
    )
    if args.include_sandbox_key:
        # Public endpoint returns a temporary GET-only limited key. It is not used by this probe.
        probes["sandbox_key_public"] = request("POST", f"{API}/api/v1/public/playground/sandbox-key", body=b"{}", timeout=args.timeout, headers={"Content-Type": "application/json"})

    summary = {
        "generated_at": now_iso(),
        "scope": "read_only_public_no_credentials_no_write_no_ut_spend",
        "openapi": summarize_openapi(probes["openapi"].get("json")),
        "agent_card": summarize_agent_card(probes["agent_card"].get("json")),
        "community_stats": probes["community_stats"].get("json"),
        "capabilities": summarize_list(probes["capabilities"].get("json")),
        "demands": summarize_list(probes["demands"].get("json")),
        "mcp_sse_handshake": {
            "ok": probes["mcp_sse_handshake"].get("ok"),
            "status": probes["mcp_sse_handshake"].get("status"),
            "content_type": probes["mcp_sse_handshake"].get("content_type"),
            "preview": probes["mcp_sse_handshake"].get("text_preview"),
        },
        "a2a_unauth_guard": {
            "ok": probes["a2a_unauth_guard"].get("ok"),
            "status": probes["a2a_unauth_guard"].get("status"),
            "json": probes["a2a_unauth_guard"].get("json"),
        },
        "probes": probes,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
