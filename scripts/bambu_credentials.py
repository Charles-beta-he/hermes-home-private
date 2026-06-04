#!/usr/bin/env python3
"""Bambu credential helper for Hermes.

Stores/retrieves the LAN access code from macOS Keychain, never plaintext brain files.
The module function returns the code to the caller process; CLI never prints the secret.
"""
from __future__ import annotations

import argparse
import getpass
import os
import subprocess
import sys
from dataclasses import dataclass

SERVICE = os.environ.get("HERMES_BAMBU_KEYCHAIN_SERVICE", "hermes-bambu-x2d")
ACCOUNT = os.environ.get("HERMES_BAMBU_KEYCHAIN_ACCOUNT", "lan-access-code")
ENV_KEY = "BAMBU_ACCESS_CODE"


@dataclass
class CredentialResult:
    code: str | None
    source: str


def _valid_shape(code: str) -> bool:
    return len(code) == 8 and code.isalnum()


def _security(*args: str, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["security", *args],
        input=input_text,
        capture_output=True,
        text=True,
        timeout=20,
    )


def get_keychain_code() -> str | None:
    proc = _security("find-generic-password", "-s", SERVICE, "-a", ACCOUNT, "-w")
    if proc.returncode != 0:
        return None
    code = proc.stdout.strip()
    if not code:
        return None
    if not _valid_shape(code):
        raise RuntimeError("Keychain Bambu access code exists but has invalid shape; expected 8 alphanumeric characters")
    return code


def resolve_access_code(*, allow_env: bool = True, allow_keychain: bool = True) -> CredentialResult:
    if allow_env:
        code = (os.environ.get(ENV_KEY) or "").strip()
        if code:
            if not _valid_shape(code):
                raise RuntimeError("BAMBU_ACCESS_CODE has invalid shape; expected 8 alphanumeric characters")
            return CredentialResult(code=code, source=f"env:{ENV_KEY}")
    if allow_keychain:
        code = get_keychain_code()
        if code:
            return CredentialResult(code=code, source=f"keychain:{SERVICE}/{ACCOUNT}")
    return CredentialResult(code=None, source="missing")


def store_keychain_code(code: str) -> None:
    code = code.strip()
    if not _valid_shape(code):
        raise SystemExit("Invalid access code shape; expected exactly 8 alphanumeric characters")
    # -U updates existing item in-place. Password is supplied as an argument; macOS
    # security does not echo it, but avoid running this from shell history with the
    # code inline. The CLI below prompts hidden and passes it directly.
    proc = _security("add-generic-password", "-U", "-s", SERVICE, "-a", ACCOUNT, "-w", code)
    if proc.returncode != 0:
        raise SystemExit(proc.stderr.strip() or "security add-generic-password failed")


def delete_keychain_code() -> bool:
    proc = _security("delete-generic-password", "-s", SERVICE, "-a", ACCOUNT)
    if proc.returncode == 0:
        return True
    if "could not be found" in proc.stderr.lower() or "specified item could not be found" in proc.stderr.lower():
        return False
    raise SystemExit(proc.stderr.strip() or "security delete-generic-password failed")


def cmd_set(args: argparse.Namespace) -> int:
    code = getpass.getpass("Bambu access code (hidden; stored in macOS Keychain): ").strip()
    store_keychain_code(code)
    print(f"stored: keychain:{SERVICE}/{ACCOUNT}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    try:
        res = resolve_access_code(allow_env=True, allow_keychain=True)
    except Exception as exc:
        print(f"status: invalid ({exc})")
        return 2
    if res.code:
        print(f"available: {res.source}")
        return 0
    print("missing: set with `python3 ~/.hermes/scripts/bambu_credentials.py set`")
    return 1


def cmd_delete(args: argparse.Namespace) -> int:
    removed = delete_keychain_code()
    print("deleted" if removed else "not_found")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage Bambu LAN access code in macOS Keychain without printing it")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("set")
    p.set_defaults(func=cmd_set)
    p = sub.add_parser("status")
    p.set_defaults(func=cmd_status)
    p = sub.add_parser("delete")
    p.set_defaults(func=cmd_delete)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
