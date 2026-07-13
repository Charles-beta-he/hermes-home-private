#!/usr/bin/env python3
"""Run Meituan Travel ht-ai with a token read from macOS Keychain.

The token is never printed or persisted by this adapter. It is injected only into
ht-ai's child-process environment.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

SERVICE = "hermes.meituan.ht-ai"
PACKAGE = "@meituan-travel/ht-ai@0.0.6"
CHANNEL = "meituan-developer"
MANAGED_BINARY = Path.home() / ".hermes" / "modules" / "meituan-travel" / "node_modules" / ".bin" / "ht-ai"
DEFAULT_TIMEOUT_SECONDS = 150


def resolve_adapter_command() -> list[str]:
    if MANAGED_BINARY.exists():
        return [str(MANAGED_BINARY)]
    npx = shutil.which("npx")
    if npx:
        return [npx, "--yes", PACKAGE]
    return []


def keychain_account() -> str:
    return os.environ.get("MEITUAN_KEYCHAIN_ACCOUNT") or os.environ.get("USER") or os.getlogin()


def read_token(account: str) -> str:
    proc = subprocess.run(
        ["/usr/bin/security", "find-generic-password", "-a", account, "-s", SERVICE, "-w"],
        text=True,
        capture_output=True,
        check=False,
    )
    token = proc.stdout.strip()
    if proc.returncode != 0 or not token:
        raise RuntimeError("credential_missing")
    return token


def check_status() -> int:
    account = keychain_account()
    adapter_command = resolve_adapter_command()
    try:
        read_token(account)
        credential_present = True
    except RuntimeError:
        credential_present = False
    print(json.dumps({
        "ok": bool(adapter_command and credential_present),
        "adapter": "meituan_keychain_ht_ai",
        "service": SERVICE,
        "account": account,
        "credential_present": credential_present,
        "adapter_command": adapter_command,
        "managed_binary": str(MANAGED_BINARY),
        "managed_binary_present": MANAGED_BINARY.exists(),
        "package": PACKAGE,
        "channel": CHANNEL,
        "external_query_executed": False,
    }, ensure_ascii=False))
    return 0 if adapter_command and credential_present else 3


def run_query(query: str, city: str | None, origin_query: str | None, timeout: int) -> int:
    account = keychain_account()
    try:
        token = read_token(account)
    except RuntimeError:
        print(json.dumps({
            "ok": False,
            "error": "credential_missing",
            "service": SERVICE,
            "account": account,
        }, ensure_ascii=False), file=sys.stderr)
        return 3

    adapter_command = resolve_adapter_command()
    if not adapter_command:
        print(json.dumps({"ok": False, "error": "adapter_unavailable", "missing": "managed binary or npx"}), file=sys.stderr)
        return 127

    cmd = [
        *adapter_command, "query",
        "--query", query,
        "--origin-query", origin_query or query,
        "--channel", CHANNEL,
    ]
    if city:
        cmd.extend(["--city", city])

    env = os.environ.copy()
    env["MEITUAN_HT_TOKEN"] = token
    try:
        proc = subprocess.run(cmd, env=env, timeout=timeout, check=False)
        return proc.returncode
    except subprocess.TimeoutExpired:
        print(json.dumps({"ok": False, "error": "provider_query_timeout", "timeout_seconds": timeout}), file=sys.stderr)
        return 124
    finally:
        env.pop("MEITUAN_HT_TOKEN", None)
        token = ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Keychain-backed Meituan Travel ht-ai adapter")
    parser.add_argument("--check", action="store_true", help="Check local readiness without making an external query")
    parser.add_argument("--query", help="Natural-language travel query")
    parser.add_argument("--city", help="City name")
    parser.add_argument("--origin-query", help="Original user query for provider telemetry")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    args = parser.parse_args()

    if args.check:
        return check_status()
    if not args.query:
        parser.error("--query is required unless --check is used")
    return run_query(args.query, args.city, args.origin_query, args.timeout)


if __name__ == "__main__":
    raise SystemExit(main())
