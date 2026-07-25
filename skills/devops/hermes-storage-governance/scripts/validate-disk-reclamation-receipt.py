#!/usr/bin/env python3
"""Read-only validator for exact-allowlist disk-reclamation receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat as stat_module
import sys
from pathlib import Path
from typing import Any

REQUIRED_KEYS = {
    "schema",
    "status",
    "authority",
    "allowlist_path",
    "allowlist_sha256",
    "declared_root",
    "deleted_count",
    "deleted",
    "estimated_allocated_bytes",
    "free_bytes_before",
    "free_bytes_after",
    "free_bytes_delta",
    "parent_directories_fsynced",
    "preserve_before",
    "preserve_after",
    "residual_targets",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _identity_matches(record: dict[str, Any]) -> bool:
    path = Path(record["path"])
    if not os.path.lexists(path):
        return False
    stat = path.lstat()
    fields = {
        "dev": stat.st_dev,
        "ino": stat.st_ino,
        "mtime_ns": stat.st_mtime_ns,
        "size": stat.st_size,
        "is_symlink": path.is_symlink(),
    }
    if any(record.get(key) != value for key, value in fields.items() if key in record):
        return False
    if "mode" in record:
        recorded_mode = record["mode"]
        if not isinstance(recorded_mode, int):
            return False
        actual_mode = stat_module.S_IMODE(stat.st_mode) if recorded_mode <= 0o7777 else stat.st_mode
        if recorded_mode != actual_mode:
            return False
    return "sha256" not in record or (path.is_file() and _sha256(path) == record["sha256"])


def validate_receipt(
    receipt_path: str | Path,
    *,
    expected_receipt_sha256: str | None = None,
    fresh: bool = False,
) -> dict[str, Any]:
    path = Path(receipt_path)
    errors: list[str] = []
    result: dict[str, Any] = {
        "schema": "hermes_disk_reclamation_validation_v1",
        "receipt_path": str(path),
        "receipt_sha256": None,
        "historical_receipt_valid": False,
        "fresh_target_absence": None,
        "fresh_preserve_parity": None,
        "current_capacity": None,
        "side_effects_performed": False,
        "errors": errors,
    }

    try:
        receipt_bytes = path.read_bytes()
        receipt = json.loads(receipt_bytes)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        errors.append(f"receipt_unreadable:{type(exc).__name__}")
        result["status"] = "fail"
        return result

    digest = hashlib.sha256(receipt_bytes).hexdigest()
    result["receipt_sha256"] = digest
    if expected_receipt_sha256 is not None and digest != expected_receipt_sha256:
        errors.append("receipt_sha256_mismatch")

    missing = sorted(REQUIRED_KEYS - set(receipt))
    if missing:
        errors.append("missing_required_keys:" + ",".join(missing))

    if receipt.get("schema") != "hermes_disk_reclamation_receipt_v1":
        errors.append("unsupported_receipt_schema")
    if receipt.get("status") != "completed_verified":
        errors.append("receipt_status_not_completed_verified")

    deleted = receipt.get("deleted") if isinstance(receipt.get("deleted"), list) else []
    deleted_paths = [item.get("path") for item in deleted if isinstance(item, dict)]
    if receipt.get("deleted_count") != len(deleted):
        errors.append("deleted_count_mismatch")
    if len(deleted_paths) != len(deleted) or len(set(deleted_paths)) != len(deleted_paths):
        errors.append("deleted_paths_invalid_or_duplicate")
    if receipt.get("residual_targets") != []:
        errors.append("residual_targets_not_empty")
    if receipt.get("preserve_before") != receipt.get("preserve_after"):
        errors.append("preserve_before_after_mismatch")

    fsynced = set(receipt.get("parent_directories_fsynced") or [])
    if any(str(Path(item).parent) not in fsynced for item in deleted_paths if isinstance(item, str)):
        errors.append("deleted_parent_not_fsynced")

    before = receipt.get("free_bytes_before")
    after = receipt.get("free_bytes_after")
    delta = receipt.get("free_bytes_delta")
    if not all(isinstance(value, int) for value in (before, after, delta)) or after - before != delta:
        errors.append("free_bytes_delta_mismatch")

    allocated_values = [item.get("allocated_bytes") for item in deleted if isinstance(item, dict)]
    allocated: list[int] = [value for value in allocated_values if isinstance(value, int)]
    if (
        len(allocated) != len(allocated_values)
        or any(value < 0 for value in allocated)
        or sum(allocated) != receipt.get("estimated_allocated_bytes")
    ):
        errors.append("estimated_allocated_bytes_mismatch")

    allowlist_path = Path(receipt.get("allowlist_path", ""))
    try:
        allowlist_bytes = allowlist_path.read_bytes()
        allowlist = json.loads(allowlist_bytes)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        errors.append(f"allowlist_unreadable:{type(exc).__name__}")
        allowlist = None
        allowlist_bytes = b""
    if allowlist is not None:
        if hashlib.sha256(allowlist_bytes).hexdigest() != receipt.get("allowlist_sha256"):
            errors.append("allowlist_sha256_mismatch")
        allow_deleted = allowlist.get("delete_exact") if isinstance(allowlist, dict) else None
        allow_pairs = [
            (item.get("path"), item.get("allocated_bytes"))
            for item in allow_deleted or []
            if isinstance(item, dict)
        ]
        receipt_pairs = [
            (item.get("path"), item.get("allocated_bytes"))
            for item in deleted
            if isinstance(item, dict)
        ]
        if allow_pairs != receipt_pairs:
            errors.append("allowlist_deleted_entries_mismatch")
        preserve_paths = [
            item.get("path") for item in receipt.get("preserve_before", []) if isinstance(item, dict)
        ]
        if allowlist.get("preserve") != preserve_paths:
            errors.append("allowlist_preserve_entries_mismatch")
        if allowlist.get("estimated_allocated_bytes") != receipt.get("estimated_allocated_bytes"):
            errors.append("allowlist_estimated_bytes_mismatch")

    result["historical_receipt_valid"] = not errors

    if fresh:
        existing = [item for item in deleted_paths if isinstance(item, str) and os.path.lexists(item)]
        result["fresh_target_absence"] = not existing
        result["fresh_existing_targets"] = existing
        if existing:
            errors.append("fresh_deleted_target_exists")

        preserve_after = receipt.get("preserve_after") or []
        drift = [
            item.get("path")
            for item in preserve_after
            if not isinstance(item, dict) or not _identity_matches(item)
        ]
        result["fresh_preserve_parity"] = not drift
        result["fresh_preserve_drift"] = drift
        if drift:
            errors.append("fresh_preserve_identity_mismatch")

        usage = shutil.disk_usage(path.parent)
        result["current_capacity"] = {
            "total_bytes": usage.total,
            "used_bytes": usage.used,
            "free_bytes": usage.free,
        }

    result["status"] = "pass" if not errors else "fail"
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--expected-sha256")
    parser.add_argument("--fresh", action="store_true")
    args = parser.parse_args(argv)
    result = validate_receipt(
        args.receipt,
        expected_receipt_sha256=args.expected_sha256,
        fresh=args.fresh,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
