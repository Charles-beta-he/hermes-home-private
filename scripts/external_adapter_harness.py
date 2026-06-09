#!/usr/bin/env python3
"""Digest-bound external adapter local-file write-through harness.

This is the first default-on external side-effect executor for Hermes self-
architecture experiments. It intentionally writes only a JSON fixture file under
an allowlisted harness directory. It does not send network requests, mutate
Kanban/Taskpool, install skills, write memory, or deploy.
"""
from __future__ import annotations

import argparse
import json
import os
import hashlib
import time
from pathlib import Path
from typing import Any

HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))).expanduser()
HARNESS_DIR = HERMES_HOME / "state" / "external-adapter-harness"
ELEVATED_ROLES = {"admin", "operator", "system"}
DISABLE_VALUES = {"0", "false", "off", "no", "disabled"}
ENABLE_VALUES = {"1", "true", "yes", "on"}


def utc_ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def harness_mode(default: str = "apply") -> str:
    raw = os.environ.get("HERMES_EXTERNAL_ADAPTER_HARNESS_MODE") or os.environ.get("HERMES_EXTERNAL_ADAPTER_HARNESS") or default
    mode = str(raw or "").strip().lower()
    if mode in DISABLE_VALUES:
        return "off"
    if mode in ENABLE_VALUES:
        return "apply"
    if mode not in {"off", "shadow", "apply"}:
        return "apply"
    return mode


def _reject_symlink_chain(path: Path, *, stop_at: Path) -> None:
    cur = path
    candidates = []
    while True:
        candidates.append(cur)
        if cur == stop_at or cur.parent == cur:
            break
        cur = cur.parent
    for item in candidates:
        if item.exists() and item.is_symlink():
            raise ValueError(f"symlink_rejected:{item}")


def safe_state_path(adapter_state_path: str | Path, *, base_dir: str | Path | None = None) -> Path:
    base = Path(base_dir).expanduser() if base_dir else HARNESS_DIR
    base = base.resolve()
    raw = Path(adapter_state_path).expanduser()
    path = raw if raw.is_absolute() else base / raw
    if path.suffix != ".json":
        raise ValueError("adapter_state_path_must_be_json")
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)
    resolved_parent = parent.resolve()
    if not (resolved_parent == base or base in resolved_parent.parents):
        raise ValueError("adapter_state_path_outside_harness_dir")
    _reject_symlink_chain(resolved_parent, stop_at=base)
    if path.exists() and path.is_symlink():
        raise ValueError(f"symlink_rejected:{path}")
    return resolved_parent / path.name


def read_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"status": "missing"}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("adapter_state_not_json_object")
    return data


def write_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_write_intent(
    *,
    task_id: str,
    adapter_state_path: str | Path,
    target_status: str = "done",
    canonical_done_authorization_id: str,
    evidence: list[str] | None = None,
    base_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Create a digest-bound local-file adapter write intent."""
    if target_status != "done":
        raise ValueError("only_target_status_done_supported")
    if not canonical_done_authorization_id:
        raise ValueError("canonical_done_authorization_id_required")
    evidence = [str(x) for x in (evidence or []) if str(x).strip()]
    if not evidence:
        raise ValueError("non_empty_evidence_required")
    state_path = safe_state_path(adapter_state_path, base_dir=base_dir)
    harness_base_dir = str((Path(base_dir).expanduser() if base_dir else HARNESS_DIR).resolve())
    mutation_payload = {
        "adapter": "local_file",
        "operation": "set_status",
        "target_status": target_status,
        "task_id": task_id,
        "adapter_state_path": str(state_path),
        "harness_base_dir": harness_base_dir,
        "canonical_done_authorization_id": canonical_done_authorization_id,
    }
    mutation_digest = digest(mutation_payload)
    intent_basis = {"schema": "hermes_external_adapter_write_intent_v1", "mutation_digest": mutation_digest}
    return {
        "schema": "hermes_external_adapter_write_intent_v1",
        "adapter": "local_file",
        "operation": "set_status",
        "task_id": task_id,
        "target_status": target_status,
        "adapter_state_path": str(state_path),
        "harness_base_dir": harness_base_dir,
        "canonical_done_authorization_id": canonical_done_authorization_id,
        "evidence": evidence,
        "mutation_payload": mutation_payload,
        "mutation_digest": mutation_digest,
        "intent_id": digest(intent_basis),
        "created_at": utc_ts(),
    }


def authorize_write(
    intent: dict[str, Any],
    *,
    actor_id: str,
    actor_role: str,
    approval_decision: str = "approved",
    ttl_seconds: int = 900,
    evidence: list[str] | None = None,
) -> dict[str, Any]:
    role = str(actor_role or "").strip().lower()
    approval_decision = str(approval_decision or "").strip().lower()
    evidence = [str(x) for x in (evidence or []) if str(x).strip()]
    auth: dict[str, Any] = {
        "schema": "hermes_external_adapter_write_authorization_v1",
        "intent_id": intent.get("intent_id"),
        "adapter": intent.get("adapter"),
        "target_status": intent.get("target_status"),
        "mutation_digest": intent.get("mutation_digest"),
        "actor_id": actor_id,
        "actor_role": role,
        "approval_decision": approval_decision,
        "ttl_seconds": ttl_seconds,
        "issued_at": utc_ts(),
        "authorized": False,
        "reasons": [],
        "authority": "local_file_adapter_only_no_network_no_skill_no_memory_no_sql",
    }
    if intent.get("schema") != "hermes_external_adapter_write_intent_v1":
        auth["reasons"].append("invalid_intent_schema")
    if intent.get("adapter") != "local_file":
        auth["reasons"].append("adapter_not_allowlisted")
    if intent.get("target_status") != "done":
        auth["reasons"].append("target_status_not_done")
    if digest(intent.get("mutation_payload")) != intent.get("mutation_digest"):
        auth["reasons"].append("mutation_digest_mismatch")
    if approval_decision != "approved":
        auth["reasons"].append("approval_not_approved")
    if role not in ELEVATED_ROLES:
        auth["reasons"].append("actor_role_not_elevated")
    if not evidence:
        auth["reasons"].append("authorization_evidence_required")
    if not intent.get("canonical_done_authorization_id"):
        auth["reasons"].append("canonical_done_authorization_missing")
    if not auth["reasons"]:
        auth_basis = {
            "intent_id": intent.get("intent_id"),
            "mutation_digest": intent.get("mutation_digest"),
            "adapter_state_path": intent.get("adapter_state_path"),
            "target_status": intent.get("target_status"),
            "actor_id": actor_id,
            "actor_role": role,
        }
        auth["authorization_id"] = digest(auth_basis)
        auth["authorized"] = True
        auth["evidence"] = evidence
        auth["reasons"].append("approved_digest_bound_local_file_write")
    return auth


def execute_write(intent: dict[str, Any], authorization: dict[str, Any], *, mode: str | None = None) -> dict[str, Any]:
    mode = harness_mode() if mode is None else str(mode or "apply").lower()
    result: dict[str, Any] = {
        "schema": "hermes_external_adapter_local_file_write_v1",
        "mode": mode,
        "intent_id": intent.get("intent_id"),
        "authorization_id": authorization.get("authorization_id"),
        "adapter": intent.get("adapter"),
        "write_executed": False,
        "readback_verified": False,
        "status": "skipped",
        "authority": "local_file_adapter_only_no_network_no_skill_no_memory_no_sql",
    }
    if mode == "off":
        result["reason"] = "disabled_by_env"
        return result
    if not authorization.get("authorized"):
        result["reason"] = "authorization_not_approved"
        return result
    if authorization.get("intent_id") != intent.get("intent_id") or authorization.get("mutation_digest") != intent.get("mutation_digest"):
        result["reason"] = "authorization_intent_digest_mismatch"
        return result
    if mode == "shadow":
        result["status"] = "shadow_authorized_not_executed"
        return result
    adapter_state_path = intent.get("adapter_state_path")
    if not adapter_state_path:
        result["reason"] = "adapter_state_path_required"
        return result
    path = safe_state_path(str(adapter_state_path), base_dir=intent.get("harness_base_dir") or None)
    before = read_state(path)
    request_digest = digest({
        "intent_id": intent.get("intent_id"),
        "authorization_id": authorization.get("authorization_id"),
        "mutation_digest": intent.get("mutation_digest"),
    })
    if before.get("last_request_digest") == request_digest and before.get("status") == intent.get("target_status"):
        result.update({
            "status": "already_applied",
            "write_executed": False,
            "readback_verified": True,
            "request_digest": request_digest,
            "adapter_state_path": str(path),
            "harness_base_dir": str(Path(intent.get("harness_base_dir") or HARNESS_DIR).expanduser().resolve()),
            "rollback_snapshot": before.get("rollback_snapshot", {}),
        })
        return result
    rollback_snapshot = {
        "previous_status": before.get("status", "missing"),
        "previous_state": before,
        "adapter_state_path": str(path),
        "request_digest": request_digest,
    }
    after = dict(before)
    after.update({
        "status": intent.get("target_status"),
        "task_id": intent.get("task_id"),
        "updated_at": utc_ts(),
        "last_request_digest": request_digest,
        "intent_id": intent.get("intent_id"),
        "authorization_id": authorization.get("authorization_id"),
        "mutation_digest": intent.get("mutation_digest"),
        "rollback_snapshot": rollback_snapshot,
    })
    write_state(path, after)
    readback = read_state(path)
    verified = readback.get("status") == intent.get("target_status") and readback.get("last_request_digest") == request_digest
    result.update({
        "status": "external_adapter_write_verified" if verified else "external_adapter_readback_mismatch",
        "write_executed": True,
        "readback_verified": verified,
        "request_digest": request_digest,
        "adapter_state_path": str(path),
        "harness_base_dir": str(Path(intent.get("harness_base_dir") or HARNESS_DIR).expanduser().resolve()),
        "previous_status": rollback_snapshot["previous_status"],
        "readback_status": readback.get("status"),
        "rollback_snapshot": rollback_snapshot,
    })
    return result


def rollback_write(execution: dict[str, Any], *, expected_request_digest: str, evidence: list[str] | None = None) -> dict[str, Any]:
    evidence = [str(x) for x in (evidence or []) if str(x).strip()]
    result: dict[str, Any] = {
        "schema": "hermes_external_adapter_local_file_rollback_v1",
        "request_digest": execution.get("request_digest"),
        "rollback_executed": False,
        "readback_verified": False,
        "status": "skipped",
    }
    if not evidence:
        result["reason"] = "rollback_evidence_required"
        return result
    if execution.get("request_digest") != expected_request_digest:
        result["reason"] = "request_digest_mismatch"
        return result
    if execution.get("status") not in {"external_adapter_write_verified", "already_applied"}:
        result["reason"] = "write_not_verified"
        return result
    snapshot = execution.get("rollback_snapshot") or {}
    rollback_path_value = snapshot.get("adapter_state_path") or execution.get("adapter_state_path")
    if not rollback_path_value:
        result["reason"] = "adapter_state_path_required"
        return result
    path = safe_state_path(str(rollback_path_value), base_dir=execution.get("harness_base_dir") or None)
    current = read_state(path)
    if current.get("last_request_digest") != expected_request_digest:
        result["reason"] = "current_state_drift"
        return result
    previous = snapshot.get("previous_state") or {"status": snapshot.get("previous_status", "missing")}
    if snapshot.get("previous_status") == "missing":
        if path.exists():
            path.unlink()
        readback = {"status": "missing"}
    else:
        restored = dict(previous)
        restored["rollback_of_request_digest"] = expected_request_digest
        restored["rolled_back_at"] = utc_ts()
        write_state(path, restored)
        readback = read_state(path)
    verified = readback.get("status") == snapshot.get("previous_status", "missing")
    result.update({
        "status": "external_adapter_rollback_verified" if verified else "external_adapter_rollback_mismatch",
        "rollback_executed": True,
        "readback_verified": verified,
        "adapter_state_path": str(path),
        "readback_status": readback.get("status"),
    })
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Digest-bound local-file external adapter harness")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("mode")
    p = sub.add_parser("intent")
    p.add_argument("--task-id", required=True)
    p.add_argument("--adapter-state-path", required=True)
    p.add_argument("--canonical-done-authorization-id", required=True)
    p.add_argument("--evidence", action="append", default=[])
    p = sub.add_parser("authorize")
    p.add_argument("--intent-json", required=True)
    p.add_argument("--actor-id", required=True)
    p.add_argument("--actor-role", required=True)
    p.add_argument("--evidence", action="append", default=[])
    p = sub.add_parser("execute")
    p.add_argument("--intent-json", required=True)
    p.add_argument("--authorization-json", required=True)
    p.add_argument("--mode", default=None)
    p = sub.add_parser("rollback")
    p.add_argument("--execution-json", required=True)
    p.add_argument("--expected-request-digest", required=True)
    p.add_argument("--evidence", action="append", default=[])
    args = parser.parse_args(argv)
    if args.cmd == "mode":
        print(json.dumps({"mode": harness_mode()}, ensure_ascii=False, indent=2))
    elif args.cmd == "intent":
        print(json.dumps(build_write_intent(task_id=args.task_id, adapter_state_path=args.adapter_state_path, canonical_done_authorization_id=args.canonical_done_authorization_id, evidence=args.evidence), ensure_ascii=False, indent=2))
    elif args.cmd == "authorize":
        print(json.dumps(authorize_write(json.loads(args.intent_json), actor_id=args.actor_id, actor_role=args.actor_role, evidence=args.evidence), ensure_ascii=False, indent=2))
    elif args.cmd == "execute":
        print(json.dumps(execute_write(json.loads(args.intent_json), json.loads(args.authorization_json), mode=args.mode), ensure_ascii=False, indent=2))
    elif args.cmd == "rollback":
        print(json.dumps(rollback_write(json.loads(args.execution_json), expected_request_digest=args.expected_request_digest, evidence=args.evidence), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
