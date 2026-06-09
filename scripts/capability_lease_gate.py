#!/usr/bin/env python3
"""Digest-bound capability lease gate for dangerous Hermes capabilities.

Default-on policy gate for capabilities such as run_command. It issues scoped,
TTL-bound leases and validates requests against capability/scope/danger/evidence
without executing the capability itself.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Any

HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))).expanduser()
LEASE_DIR = HERMES_HOME / "state" / "capability-leases"
DISABLE_VALUES = {"0", "false", "off", "no", "disabled"}
ENABLE_VALUES = {"1", "true", "yes", "on"}
ELEVATED_ROLES = {"admin", "operator", "system"}
ALLOWED_CAPABILITIES = {"run_command", "computer_use", "browser_action", "external_send", "deploy"}
DANGER_LEVELS = {"low", "moderate", "high", "critical"}
DEFAULT_MAX_DANGER = "moderate"
DANGER_RANK = {"low": 0, "moderate": 1, "high": 2, "critical": 3}
SCOPE_RE = re.compile(r"^[a-zA-Z0-9_./:@+-]{1,240}$")


def now() -> int:
    return int(time.time())


def utc_ts(ts: int | None = None) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts or now()))


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def gate_mode(default: str = "apply") -> str:
    raw = os.environ.get("HERMES_CAPABILITY_LEASE_MODE") or os.environ.get("HERMES_CAPABILITY_LEASE") or default
    mode = str(raw or "").strip().lower()
    if mode in DISABLE_VALUES:
        return "off"
    if mode in ENABLE_VALUES:
        return "apply"
    if mode not in {"off", "shadow", "apply"}:
        return "apply"
    return mode


def validate_scope(scope: str) -> str:
    scope = str(scope or "").strip()
    if not scope or ".." in scope or not SCOPE_RE.match(scope):
        raise ValueError("invalid_scope")
    return scope


def lease_path(lease_id: str, *, base_dir: str | Path | None = None) -> Path:
    base = Path(base_dir).expanduser() if base_dir else LEASE_DIR
    base = base.resolve()
    base.mkdir(parents=True, exist_ok=True)
    if not re.match(r"^[a-f0-9]{64}$", lease_id):
        raise ValueError("invalid_lease_id")
    return base / f"{lease_id}.json"


def issue_lease(
    *,
    actor_id: str,
    actor_role: str,
    task_id: str,
    capability: str,
    scope: str,
    max_danger: str = DEFAULT_MAX_DANGER,
    ttl_seconds: int = 900,
    evidence: list[str] | None = None,
    base_dir: str | Path | None = None,
) -> dict[str, Any]:
    role = str(actor_role or "").strip().lower()
    capability = str(capability or "").strip()
    max_danger = str(max_danger or DEFAULT_MAX_DANGER).strip().lower()
    scope = validate_scope(scope)
    evidence = [str(x) for x in (evidence or []) if str(x).strip()]
    lease = {
        "schema": "hermes_capability_lease_v1",
        "actor_id": actor_id,
        "actor_role": role,
        "task_id": task_id,
        "capability": capability,
        "scope": scope,
        "max_danger": max_danger,
        "ttl_seconds": ttl_seconds,
        "issued_at_epoch": now(),
        "expires_at_epoch": now() + int(ttl_seconds),
        "authorized": False,
        "reasons": [],
        "authority": "scoped_capability_lease_only_no_execution",
    }
    if role not in ELEVATED_ROLES:
        lease["reasons"].append("actor_role_not_elevated")
    if capability not in ALLOWED_CAPABILITIES:
        lease["reasons"].append("capability_not_allowlisted")
    if max_danger not in DANGER_LEVELS:
        lease["reasons"].append("max_danger_invalid")
    if ttl_seconds <= 0 or ttl_seconds > 3600:
        lease["reasons"].append("ttl_out_of_range")
    if not evidence:
        lease["reasons"].append("evidence_required")
    if not lease["reasons"]:
        lease["lease_id"] = digest({k: lease[k] for k in ["actor_id", "actor_role", "task_id", "capability", "scope", "max_danger", "issued_at_epoch", "expires_at_epoch"]})
        lease["authorized"] = True
        lease["evidence"] = evidence
        lease["issued_at"] = utc_ts(lease["issued_at_epoch"])
        lease["expires_at"] = utc_ts(lease["expires_at_epoch"])
        path = lease_path(lease["lease_id"], base_dir=base_dir)
        lease["lease_path"] = str(path)
        path.write_text(json.dumps(lease, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        lease["reasons"].append("approved_scoped_capability_lease")
    return lease


def load_lease(lease_id: str, *, base_dir: str | Path | None = None) -> dict[str, Any]:
    path = lease_path(lease_id, base_dir=base_dir)
    if not path.exists():
        raise ValueError("lease_not_found")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("lease_id") != lease_id:
        raise ValueError("lease_id_mismatch")
    return data


def validate_request(
    *,
    lease_id: str,
    capability: str,
    scope: str,
    danger: str,
    request_payload: dict[str, Any],
    evidence: list[str] | None = None,
    base_dir: str | Path | None = None,
    mode: str | None = None,
) -> dict[str, Any]:
    mode = gate_mode() if mode is None else str(mode or "apply").lower()
    evidence = [str(x) for x in (evidence or []) if str(x).strip()]
    result = {
        "schema": "hermes_capability_lease_validation_v1",
        "mode": mode,
        "lease_id": lease_id,
        "capability": capability,
        "scope": scope,
        "danger": danger,
        "allowed": False,
        "status": "denied",
        "reasons": [],
        "authority": "validation_only_no_execution",
    }
    if mode == "off":
        result["status"] = "skipped_disabled_by_env"
        result["reasons"].append("disabled_by_env")
        return result
    try:
        lease = load_lease(lease_id, base_dir=base_dir)
    except Exception as exc:
        result["reasons"].append(str(exc))
        return result
    danger = str(danger or "").strip().lower()
    try:
        scope = validate_scope(scope)
    except ValueError as exc:
        result["reasons"].append(str(exc))
        return result
    if not lease.get("authorized"):
        result["reasons"].append("lease_not_authorized")
    if now() > int(lease.get("expires_at_epoch", 0)):
        result["reasons"].append("lease_expired")
    if capability != lease.get("capability"):
        result["reasons"].append("capability_mismatch")
    if scope != lease.get("scope"):
        result["reasons"].append("scope_mismatch")
    if danger not in DANGER_LEVELS:
        result["reasons"].append("danger_invalid")
    elif DANGER_RANK[danger] > DANGER_RANK.get(str(lease.get("max_danger")), -1):
        result["reasons"].append("danger_exceeds_lease")
    if not evidence:
        result["reasons"].append("request_evidence_required")
    request_digest = digest({"lease_id": lease_id, "capability": capability, "scope": scope, "danger": danger, "payload": request_payload})
    result["request_digest"] = request_digest
    if not result["reasons"]:
        result["allowed"] = mode == "apply"
        result["status"] = "allowed" if mode == "apply" else "shadow_allowed_not_executed"
        result["reasons"].append("validated_by_scoped_capability_lease")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capability lease gate")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("mode")
    p = sub.add_parser("issue")
    p.add_argument("--actor-id", required=True)
    p.add_argument("--actor-role", required=True)
    p.add_argument("--task-id", required=True)
    p.add_argument("--capability", required=True)
    p.add_argument("--scope", required=True)
    p.add_argument("--max-danger", default=DEFAULT_MAX_DANGER)
    p.add_argument("--ttl-seconds", type=int, default=900)
    p.add_argument("--base-dir", default=None)
    p.add_argument("--evidence", action="append", default=[])
    p = sub.add_parser("validate")
    p.add_argument("--lease-id", required=True)
    p.add_argument("--capability", required=True)
    p.add_argument("--scope", required=True)
    p.add_argument("--danger", required=True)
    p.add_argument("--payload-json", default="{}")
    p.add_argument("--base-dir", default=None)
    p.add_argument("--mode", default=None)
    p.add_argument("--evidence", action="append", default=[])
    args = parser.parse_args(argv)
    if args.cmd == "mode":
        print(json.dumps({"mode": gate_mode()}, ensure_ascii=False, indent=2))
    elif args.cmd == "issue":
        print(json.dumps(issue_lease(actor_id=args.actor_id, actor_role=args.actor_role, task_id=args.task_id, capability=args.capability, scope=args.scope, max_danger=args.max_danger, ttl_seconds=args.ttl_seconds, evidence=args.evidence, base_dir=args.base_dir), ensure_ascii=False, indent=2))
    elif args.cmd == "validate":
        print(json.dumps(validate_request(lease_id=args.lease_id, capability=args.capability, scope=args.scope, danger=args.danger, request_payload=json.loads(args.payload_json), evidence=args.evidence, base_dir=args.base_dir, mode=args.mode), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
