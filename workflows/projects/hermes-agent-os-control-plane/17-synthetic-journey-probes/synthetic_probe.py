#!/usr/bin/env python3
"""Default-off, local-read-only synthetic journey probe runner.

The runner intentionally supports one adapter only: bounded JSON readback plus
exact assertions. It never invokes commands, models, networks, schedulers, or
lifecycle APIs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
PROBE_SCHEMA = "hermes_synthetic_probe_v1"
RECEIPT_SCHEMA = "hermes_synthetic_probe_receipt_v1"
MAX_TARGET_BYTES = 1_048_576
MAX_PROBE_BYTES = 262_144
ALLOWED_OUTPUT_DIRS = (HERE / "evidence", HERE / "runtime")
TOP_LEVEL_KEYS = {"schema", "probe_id", "enabled", "mode", "steps"}
STEP_KEYS = {"id", "adapter", "target", "assertions"}
NEGATIVE_ASSERTIONS = {
    "no_external_dispatch": True,
    "no_lifecycle_write": True,
    "no_scheduler_or_worker_write": True,
    "no_model_call": True,
    "no_memory_or_learning_ingestion": True,
    "no_arbitrary_command_execution": True,
    "no_secret_export": True,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _valid_identifier(value: Any, *, minimum: int, maximum: int) -> bool:
    if not isinstance(value, str) or not minimum <= len(value) <= maximum:
        return False
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789._-")
    return value[0] in set("abcdefghijklmnopqrstuvwxyz0123456789") and all(char in allowed for char in value)


def validate_probe(probe: Any) -> list[str]:
    if not isinstance(probe, dict):
        return ["probe_must_be_object"]
    issues: list[str] = []
    unknown = sorted(set(probe) - TOP_LEVEL_KEYS)
    if unknown:
        issues.extend(f"unknown_probe_field:{key}" for key in unknown)
    missing = sorted(TOP_LEVEL_KEYS - set(probe))
    if missing:
        issues.extend(f"missing_probe_field:{key}" for key in missing)
    if probe.get("schema") != PROBE_SCHEMA:
        issues.append("invalid_probe_schema")
    if not _valid_identifier(probe.get("probe_id"), minimum=3, maximum=80):
        issues.append("invalid_probe_id")
    if probe.get("enabled") is not False:
        issues.append("probe_must_be_default_off")
    if probe.get("mode") != "local_read_only":
        issues.append("invalid_probe_mode")
    steps = probe.get("steps")
    if not isinstance(steps, list) or isinstance(steps, bool) or not 1 <= len(steps) <= 16:
        issues.append("invalid_steps")
        return sorted(set(issues))
    seen_ids: set[str] = set()
    for index, step in enumerate(steps):
        prefix = f"step[{index}]"
        if not isinstance(step, dict):
            issues.append(f"{prefix}:must_be_object")
            continue
        unknown_step = sorted(set(step) - STEP_KEYS)
        issues.extend(f"{prefix}:unknown_field:{key}" for key in unknown_step)
        missing_step = sorted(STEP_KEYS - set(step))
        issues.extend(f"{prefix}:missing_field:{key}" for key in missing_step)
        step_id = step.get("id")
        if not _valid_identifier(step_id, minimum=2, maximum=64):
            issues.append(f"{prefix}:invalid_id")
        else:
            valid_step_id = str(step_id)
            if valid_step_id in seen_ids:
                issues.append(f"{prefix}:duplicate_id")
            else:
                seen_ids.add(valid_step_id)
        adapter = step.get("adapter")
        if adapter != "json_readback":
            issues.append(f"unsupported_adapter:{adapter}")
        target = step.get("target")
        if not isinstance(target, str) or not target or len(target) > 240 or "\x00" in target:
            issues.append(f"{prefix}:invalid_target")
        assertions = step.get("assertions")
        if not isinstance(assertions, dict) or not 1 <= len(assertions) <= 32:
            issues.append(f"{prefix}:invalid_assertions")
        elif any(not isinstance(path, str) or not path or len(path) > 160 for path in assertions):
            issues.append(f"{prefix}:invalid_assertion_path")
        else:
            try:
                json.dumps(assertions, ensure_ascii=False, allow_nan=False)
            except (TypeError, ValueError):
                issues.append(f"{prefix}:assertions_not_json")
    return sorted(set(issues))


def _relative_parts(target: str) -> tuple[list[str] | None, str | None]:
    candidate = Path(target)
    if candidate.is_absolute():
        return None, "target_must_be_relative"
    parts = list(candidate.parts)
    if not parts or any(part in {"", ".", ".."} for part in parts):
        return None, "target_outside_project_root"
    return parts, None


def _read_bounded_regular_json(project_root: Path, target: str) -> tuple[Any | None, bytes | None, str | None]:
    parts, issue = _relative_parts(target)
    if issue or parts is None:
        return None, None, issue
    root = project_root.expanduser().resolve(strict=True)
    current = root
    for part in parts:
        current = current / part
        if current.is_symlink():
            return None, None, "target_symlink_forbidden"
    root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    fd = root_fd
    try:
        for component in parts[:-1]:
            next_fd = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            if fd != root_fd:
                os.close(fd)
            fd = next_fd
        file_fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
        try:
            before = os.fstat(file_fd)
            if not stat.S_ISREG(before.st_mode):
                return None, None, "target_not_regular_file"
            if before.st_size > MAX_TARGET_BYTES:
                return None, None, "target_too_large"
            chunks: list[bytes] = []
            total = 0
            while True:
                chunk = os.read(file_fd, min(65_536, MAX_TARGET_BYTES + 1 - total))
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
                if total > MAX_TARGET_BYTES:
                    return None, None, "target_too_large"
            after = os.fstat(file_fd)
            fingerprint_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
            fingerprint_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
            if fingerprint_before != fingerprint_after:
                return None, None, "target_changed_while_reading"
            raw = b"".join(chunks)
        finally:
            os.close(file_fd)
    except FileNotFoundError:
        return None, None, "target_not_found"
    except NotADirectoryError:
        return None, None, "target_parent_not_directory"
    except OSError:
        return None, None, "target_read_error"
    finally:
        if fd != root_fd:
            os.close(fd)
        os.close(root_fd)
    try:
        return json.loads(raw.decode("utf-8")), raw, None
    except UnicodeDecodeError:
        return None, raw, "target_not_utf8"
    except json.JSONDecodeError:
        return None, raw, "target_not_json"


def _json_path(value: Any, path: str) -> tuple[Any, bool]:
    current = value
    for segment in path.split("."):
        if isinstance(current, dict) and segment in current:
            current = current[segment]
        elif isinstance(current, list) and segment.isdigit() and int(segment) < len(current):
            current = current[int(segment)]
        else:
            return None, False
    return current, True


def _base_receipt(probe: Any, *, execute: bool) -> dict[str, Any]:
    return {
        "schema": RECEIPT_SCHEMA,
        "probe_id": probe.get("probe_id") if isinstance(probe, dict) else None,
        "probe_contract_sha256": canonical_sha256(probe),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "synthetic": True,
        "exclude_from_learning": True,
        "exclude_from_user_analytics": True,
        "mode": "local_read_only",
        "would_execute": execute,
        "executed": False,
        "ok": False,
        "status": "invalid",
        "started_at": utc_now(),
        "completed_at": None,
        "steps": [],
        "findings": [],
        "side_effects_observed": ["local_read"],
        "journey_target_read_attempts": 0,
        "journey_target_reads_succeeded": 0,
        "negative_assertions": dict(NEGATIVE_ASSERTIONS),
        "negative_assertion_basis": "closed_adapter_set_plus_static_source_test",
        "global_certification_claimed": False,
    }


def evaluate_probe(probe: Any, *, project_root: Path, execute: bool = False) -> dict[str, Any]:
    receipt = _base_receipt(probe, execute=execute)
    issues = validate_probe(probe)
    if issues:
        receipt["findings"] = issues
        receipt["completed_at"] = utc_now()
        return receipt
    if not execute:
        receipt.update({"ok": True, "status": "validated", "would_execute": False, "completed_at": utc_now()})
        return receipt

    receipt["executed"] = True
    findings: list[str] = []
    step_receipts: list[dict[str, Any]] = []
    for step in probe["steps"]:
        value, raw, issue = _read_bounded_regular_json(project_root, step["target"])
        step_findings: list[str] = []
        assertions: list[dict[str, Any]] = []
        if issue:
            step_findings.append(issue)
        else:
            for path, expected in step["assertions"].items():
                actual, found = _json_path(value, path)
                passed = found and actual == expected and type(actual) is type(expected)
                assertions.append({"path": path, "passed": passed})
                if not found:
                    step_findings.append(f"assertion_path_missing:{path}")
                elif not passed:
                    step_findings.append(f"assertion_mismatch:{path}")
        findings.extend(step_findings)
        step_receipts.append({
            "id": step["id"],
            "adapter": "json_readback",
            "target": step["target"],
            "target_sha256": hashlib.sha256(raw).hexdigest() if raw is not None else None,
            "assertions": assertions,
            "status": "pass" if not step_findings else "fail",
            "findings": step_findings,
        })
    receipt["steps"] = step_receipts
    receipt["journey_target_read_attempts"] = len(probe["steps"])
    receipt["journey_target_reads_succeeded"] = sum(1 for step in step_receipts if step["target_sha256"] is not None)
    receipt["findings"] = sorted(set(findings))
    receipt["ok"] = not findings
    receipt["status"] = "pass" if receipt["ok"] else "fail"
    receipt["completed_at"] = utc_now()
    return receipt


def _read_probe(path: Path) -> Any:
    if path.is_symlink():
        raise ValueError("probe_symlink_forbidden")
    raw = path.read_bytes()
    if len(raw) > MAX_PROBE_BYTES:
        raise ValueError("probe_too_large")
    return json.loads(raw.decode("utf-8"))


def _write_scoped_atomic(path: Path, payload: dict[str, Any]) -> None:
    absolute = path.expanduser().resolve(strict=False)
    allowed_roots = [root.resolve(strict=False) for root in ALLOWED_OUTPUT_DIRS]
    if not any(absolute.is_relative_to(root) for root in allowed_roots):
        raise ValueError("output_outside_allowed_receipt_dirs")
    if absolute.name in {"", ".", ".."}:
        raise ValueError("invalid_output_filename")
    absolute.parent.mkdir(parents=True, exist_ok=True)
    if absolute.is_symlink():
        raise ValueError("output_symlink_forbidden")
    fd, temp_name = tempfile.mkstemp(prefix=f".{absolute.name}.", suffix=".tmp", dir=absolute.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, absolute)
    finally:
        Path(temp_name).unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", required=True, type=Path)
    parser.add_argument("--run", action="store_true", help="explicitly execute local readback; default validates only")
    parser.add_argument("--out", type=Path, help="optional receipt path below evidence/ or runtime/")
    args = parser.parse_args()
    try:
        probe = _read_probe(args.probe)
        receipt = evaluate_probe(probe, project_root=PROJECT_ROOT, execute=args.run)
        if args.out is not None:
            _write_scoped_atomic(args.out, receipt)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"ok": False, "status": "invalid", "finding": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if receipt["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
