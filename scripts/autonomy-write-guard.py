#!/usr/bin/env python3
"""Write-surface guard for Hermes autonomy-capable integrations.

This reusable fail-closed wrapper is intentionally about *authority* only. It
never completes task lifecycle state; callers must still pass their own
proof/lifecycle gates (for taskpool: running -> review -> done).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

HOME = Path.home()
HERMES_HOME = Path(os.environ.get("HERMES_HOME", HOME / ".hermes")).expanduser()
SCRIPTS = HERMES_HOME / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import permission_taxonomy as taxonomy  # noqa: E402

DEFAULT_ALLOWLIST = Path(
    os.environ.get("HERMES_AUTONOMY_WRITE_ALLOWLIST", str(HERMES_HOME / "config" / "autonomy-write-allowlist.json"))
).expanduser()
WRITE_SURFACES = taxonomy.WRITE_SURFACES
READONLY_MODES = taxonomy.READONLY_OPERATIONS
WRITE_MODES = {"budget-handoff", "autonomous-execution", "yolo-execution"}
CONTROL_PLANE_OPERATIONS = taxonomy.CONTROL_PLANE_OPERATIONS


def load_allowlist(path: Path) -> set[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return set()
    if isinstance(data, list):
        return {str(x).strip() for x in data if str(x).strip()}
    if isinstance(data, dict):
        values = data.get("allow") or data.get("surfaces") or []
        if isinstance(values, list):
            return {str(x).strip() for x in values if str(x).strip()}
    return set()


def run_precondition(mode: str) -> dict[str, Any]:
    cmd = [sys.executable, str(SCRIPTS / "autonomy-precondition.py"), "--mode", mode]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
    try:
        data = json.loads(proc.stdout or "{}")
    except Exception:
        data = {"parse_error": (proc.stdout or "")[-1000:]}
    return {"ok": proc.returncode == 0 and bool(data.get("ok")), "returncode": proc.returncode, "data": data, "stderr": (proc.stderr or "")[-1000:]}


def evaluate(surface: str, operation: str, mode: str, allowlist_path: Path) -> dict[str, Any]:
    allowlist = load_allowlist(allowlist_path)
    operation = str(operation or "write").strip()
    mode = taxonomy.normalize_authority(mode)
    checks: list[dict[str, Any]] = []

    def add(name: str, ok: bool, **extra: Any) -> None:
        checks.append({"name": name, "ok": bool(ok), **extra})

    authority_decision = taxonomy.evaluate_authority(surface, operation, mode, allowlist)
    for c in authority_decision.get("checks", []):
        # Preserve legacy check names while adding shared taxonomy coverage.
        checks.append(c)

    unknown_allow = taxonomy.unknown_allowlisted_surfaces(allowlist)
    if unknown_allow:
        # Fail closed even if the requested surface itself is known. This catches
        # drift where config grants authority to a surface not represented in the
        # audited taxonomy.
        add("allowlist_taxonomy_closed", False, unknown_allowlisted_surfaces=unknown_allow)

    if operation in taxonomy.LIFECYCLE_GATED_OPERATIONS:
        failed = [c["name"] for c in checks if not c.get("ok")]
        return {
            "schema_version": 1,
            "surface": surface,
            "operation": operation,
            "mode": mode,
            "authority_tier": mode,
            "status": "PASS" if not failed else "FAIL_CLOSED",
            "ok": not failed,
            "failed_required_checks": failed,
            "checks": checks,
            "policy": "task completion is lifecycle/proof gated; --yolo may never satisfy review->done",
            "authority": taxonomy.describe_authority(mode),
        }

    if operation in taxonomy.READONLY_OPERATIONS:
        pre = run_precondition("dispatch-hint")
        add("dispatch_hint_precondition", pre["ok"], precondition=pre)
        failed = [c["name"] for c in checks if not c.get("ok")]
        return {
            "schema_version": 1,
            "surface": surface,
            "operation": operation,
            "mode": mode,
            "authority_tier": mode,
            "status": "PASS" if not failed else "FAIL_CLOSED",
            "ok": not failed,
            "failed_required_checks": failed,
            "checks": checks,
            "policy": "read/dry-run surfaces may pass with dispatch-hint only; no external write authorized",
            "authority": taxonomy.describe_authority(mode),
        }

    if operation in CONTROL_PLANE_OPERATIONS:
        control_plane_mode_ok = mode == "dispatch-hint"
        add("control_plane_mode_is_dispatch_hint", control_plane_mode_ok, allowed_modes=["dispatch-hint"])
        pre = run_precondition("dispatch-hint")
        add("dispatch_hint_precondition", pre["ok"], precondition=pre)
        failed = [c["name"] for c in checks if not c.get("ok")]
        return {
            "schema_version": 1,
            "surface": surface,
            "operation": operation,
            "mode": mode,
            "authority_tier": mode,
            "status": "PASS" if not failed else "FAIL_CLOSED",
            "ok": not failed,
            "failed_required_checks": failed,
            "checks": checks,
            "policy": "bounded control-plane handoffs may mutate local task state only after surface allowlist and dispatch-hint precondition PASS; no task execution or external write authorized",
            "authority": taxonomy.describe_authority(mode),
        }

    requested_mode_ok = mode in WRITE_MODES
    add("write_mode_is_explicit", requested_mode_ok, allowed_modes=sorted(WRITE_MODES))
    pre_mode = mode if mode in WRITE_MODES else "budget-handoff"
    pre = run_precondition(pre_mode)
    add("autonomy_precondition", pre["ok"], precondition=pre)
    failed = [c["name"] for c in checks if not c.get("ok")]
    return {
        "schema_version": 1,
        "surface": surface,
        "operation": operation,
        "mode": mode,
        "authority_tier": mode,
        "status": "PASS" if not failed else "FAIL_CLOSED",
        "ok": not failed,
        "failed_required_checks": failed,
        "checks": checks,
        "policy": "side-effecting writes require known surface, explicit allowlist, explicit mode, and autonomy-precondition PASS; --yolo only bypasses command approval prompts",
        "authority": taxonomy.describe_authority(mode),
    }


def guard_or_raise(surface: str, operation: str, mode: str, allowlist_path: Path | None = None) -> dict[str, Any]:
    """Reusable caller-side guard.

    Side-effecting integrations should call this immediately before performing
    writes. It returns the full evidence object on PASS and raises
    PermissionError with the same evidence JSON on FAIL_CLOSED.
    """
    result = evaluate(surface, operation, mode, allowlist_path or DEFAULT_ALLOWLIST)
    if not result.get("ok"):
        raise PermissionError(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fail-closed guard before Hermes write-capable surfaces")
    parser.add_argument("--surface", required=True)
    parser.add_argument("--operation", default="write")
    parser.add_argument("--mode", choices=taxonomy.AUTHORITY_TIERS, default="dispatch-hint")
    parser.add_argument("--allowlist", default=str(DEFAULT_ALLOWLIST))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--gate", action="store_true")
    args = parser.parse_args(argv)
    result = evaluate(args.surface, args.operation, args.mode, Path(args.allowlist).expanduser())
    if args.json or args.gate:
        print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(f"autonomy_write_guard: {result['status']} failed={result['failed_required_checks']}")
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
