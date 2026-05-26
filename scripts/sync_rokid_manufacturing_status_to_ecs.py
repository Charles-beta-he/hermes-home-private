#!/usr/bin/env python3
"""Refresh local X2D read-only status cache and copy it to the Rokid ECS bridge.

The ECS bridge cannot reach the LAN-only Bambu/X2D printer. This script keeps the
cloud bridge's cache fresh without copying printer credentials to the server.
It is silent on success and prints a compact error on failure.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

HOME = Path.home()
LOCAL_CACHE = Path(os.environ.get(
    "ROKID_MANUFACTURING_STATUS_CACHE",
    str(HOME / ".hermes/brains/rokid-glasses/manufacturing_status_cache.json"),
)).expanduser()
REMOTE = os.environ.get("ROKID_ECS_SSH_TARGET", "rokid-aliyun")
REMOTE_CACHE = os.environ.get(
    "ROKID_ECS_MANUFACTURING_STATUS_CACHE",
    "/opt/hermes-rokid-bridge/.hermes/brains/rokid-glasses/manufacturing_status_cache.json",
)
REFRESH_SCRIPT = Path(os.environ.get(
    "ROKID_MANUFACTURING_REFRESH_SCRIPT",
    str(HOME / ".hermes/scripts/update_rokid_manufacturing_status_cache.py"),
)).expanduser()
TIMEOUT = os.environ.get("ROKID_MANUFACTURING_STATUS_TIMEOUT", "8")


def run(cmd: list[str], *, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)


def compact_error(label: str, proc: subprocess.CompletedProcess[str] | None = None, exc: Exception | None = None) -> int:
    if proc is not None:
        msg = (proc.stderr or proc.stdout or f"exit={proc.returncode}").strip().splitlines()[:3]
        print(f"{label}: " + " | ".join(msg), file=sys.stderr)
    elif exc is not None:
        print(f"{label}: {type(exc).__name__}: {exc}", file=sys.stderr)
    else:
        print(label, file=sys.stderr)
    return 1


def main() -> int:
    if not REFRESH_SCRIPT.exists():
        return compact_error(f"missing refresh script: {REFRESH_SCRIPT}")

    try:
        proc = run([sys.executable, str(REFRESH_SCRIPT), "--timeout", TIMEOUT], timeout=int(float(TIMEOUT)) + 8)
    except Exception as exc:
        return compact_error("refresh_failed", exc=exc)
    if proc.returncode != 0:
        return compact_error("refresh_failed", proc=proc)

    try:
        data = json.loads(LOCAL_CACHE.read_text(encoding="utf-8"))
    except Exception as exc:
        return compact_error("cache_read_failed", exc=exc)
    if data.get("schema") != "hermes_rokid_manufacturing_status_cache_v1":
        return compact_error("cache_schema_invalid")

    remote_dir = str(Path(REMOTE_CACHE).parent)
    prep = run(["ssh", REMOTE, "mkdir", "-p", remote_dir], timeout=20)
    if prep.returncode != 0:
        return compact_error("remote_prepare_failed", proc=prep)

    scp = run(["scp", str(LOCAL_CACHE), f"{REMOTE}:{REMOTE_CACHE}"], timeout=30)
    if scp.returncode != 0:
        return compact_error("remote_copy_failed", proc=scp)

    chmod = run([
        "ssh",
        REMOTE,
        "chown hermes-rokid:hermes-rokid " + REMOTE_CACHE + " && chmod 644 " + REMOTE_CACHE,
    ], timeout=20)
    if chmod.returncode != 0:
        return compact_error("remote_chmod_failed", proc=chmod)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
