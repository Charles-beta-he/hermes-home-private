#!/usr/bin/env python3
"""Governed high-risk side-effect gate control plane.

This opens Hermes high-risk capability gates in a local, auditable, fail-closed
form. It does not execute live external dispatch, publish/deploy/push,
destructive production operations, or credential/payment entry without an exact
per-action target, rollback/readback, and evidence packet.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

GATE_NAMES = [
    "runtime_hard_gate",
    "taskpool_lifecycle_write_through",
    "cron_worker_auto_status_write",
    "external_dispatch",
    "publish_deploy_push",
    "destructive",
    "credential_payment",
]

GATE_MODES = {
    "runtime_hard_gate": "enforcing",
    "taskpool_lifecycle_write_through": "exact_local_target_required",
    "cron_worker_auto_status_write": "local_heartbeat_write_enabled",
    "external_dispatch": "exact_allowlist_required",
    "publish_deploy_push": "exact_target_required",
    "destructive": "exact_target_and_backup_required",
    "credential_payment": "human_secret_entry_required",
}

FORBIDDEN_LIVE_UNTIL_EXACT = {
    "external_dispatch",
    "publish_deploy_push",
    "destructive",
    "credential_payment",
}

ALLOWED_LIFECYCLE_STATUSES = {"pending", "retry", "blocked", "review", "done", "cancelled", "claimed", "running"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def state_dir(home: Path) -> Path:
    return home / "state" / "side-effect-gates"


def state_path(home: Path) -> Path:
    return state_dir(home) / "enablement.json"


def receipts_path(home: Path) -> Path:
    return state_dir(home) / "receipts.jsonl"


def taskpool_ledger_path(home: Path) -> Path:
    return state_dir(home) / "taskpool-lifecycle-write-through.jsonl"


def heartbeat_path(home: Path) -> Path:
    return state_dir(home) / "cron-worker-heartbeat.jsonl"


def safe_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)


def digest_obj(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def ensure(home: Path) -> None:
    state_dir(home).mkdir(parents=True, exist_ok=True)


def append_receipt(home: Path, receipt: dict[str, Any]) -> dict[str, Any]:
    ensure(home)
    receipt = dict(receipt)
    receipt.setdefault("created_at", utc_now())
    receipt.setdefault("schema", "high_risk_gate_receipt_v1")
    receipt.setdefault("request_digest", digest_obj({k: v for k, v in receipt.items() if k != "created_at"}))
    with receipts_path(home).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(receipt, ensure_ascii=False, sort_keys=True) + "\n")
    return receipt


def _gate_record(name: str) -> dict[str, Any]:
    return {
        "enabled": True,
        "mode": GATE_MODES[name],
        "live_execution": False if name in FORBIDDEN_LIVE_UNTIL_EXACT else True,
        "requires_exact_target": name != "runtime_hard_gate",
        "requires_rollback": name in {"taskpool_lifecycle_write_through", "publish_deploy_push", "destructive"},
        "requires_post_action_readback": True,
        "stores_secrets": False,
        "token_read_allowed": False,
    }


def enable_all(home: Path, *, actor: str, evidence_refs: Sequence[str]) -> dict[str, Any]:
    ensure(home)
    gates = {name: _gate_record(name) for name in GATE_NAMES}
    record = {
        "schema": "high_risk_gate_enablement_v1",
        "enabled_at": utc_now(),
        "actor": actor,
        "authority_grant": "user_latest_message_enable_high_risk_boundaries",
        "enabled_all_requested_gates": True,
        "gates": gates,
        "global_invariants": {
            "fail_closed_without_exact_target": True,
            "external_send_requires_allowlist": True,
            "publish_deploy_push_requires_exact_target_and_rollback": True,
            "destructive_requires_exact_target_backup_and_readback": True,
            "credential_payment_requires_human_entry_never_agent_typed_secret": True,
            "no_secret_persistence": True,
        },
        "evidence_refs": list(evidence_refs),
        "rollback": {
            "disable_file": str(state_path(home)),
            "method": "set enabled=false per gate or git revert scoped commit; receipts are append-only audit",
        },
    }
    state_path(home).write_text(safe_json(record) + "\n", encoding="utf-8")
    receipt = append_receipt(
        home,
        {
            "event": "enable_all_high_risk_gates",
            "actor": actor,
            "gates": GATE_NAMES,
            "state_path": str(state_path(home)),
            "readback_enabled_all": True,
            "evidence_refs": list(evidence_refs),
            "executed": True,
            "live_external_side_effect_executed": False,
        },
    )
    out = dict(record)
    out.update({"ok": True, "state_path": str(state_path(home)), "receipt": receipt})
    return out


def load_state(home: Path) -> dict[str, Any]:
    p = state_path(home)
    if not p.exists():
        return {
            "schema": "high_risk_gate_enablement_v1",
            "enabled_all_requested_gates": False,
            "gates": {},
            "state_path": str(p),
        }
    return json.loads(p.read_text(encoding="utf-8"))


def status(home: Path) -> dict[str, Any]:
    state = load_state(home)
    gates = state.get("gates", {}) if isinstance(state, dict) else {}
    missing = [name for name in GATE_NAMES if not gates.get(name, {}).get("enabled")]
    return {
        "ok": not missing,
        "state_path": str(state_path(home)),
        "receipts_path": str(receipts_path(home)),
        "enabled_all_requested_gates": not missing,
        "missing_enabled_gates": missing,
        "gates": gates,
    }


def authorize_action(
    home: Path,
    *,
    gate: str,
    target: str,
    payload_hash: str,
    rollback: str,
    readback: str,
    evidence_refs: Sequence[str],
    actor: str = "operator",
    execute: bool = False,
) -> dict[str, Any]:
    state = load_state(home)
    gates = state.get("gates", {}) if isinstance(state, dict) else {}
    blocked: list[str] = []
    if gate not in GATE_NAMES:
        blocked.append("unknown_gate")
    elif not gates.get(gate, {}).get("enabled"):
        blocked.append("gate_not_enabled")
    if not target:
        blocked.append("missing_exact_target")
    if not payload_hash:
        blocked.append("missing_payload_hash")
    if gates.get(gate, {}).get("requires_rollback") and not rollback:
        blocked.append("missing_rollback")
    if not readback:
        blocked.append("missing_post_action_readback")
    if not evidence_refs:
        blocked.append("missing_evidence_refs")
    if gate == "credential_payment":
        # Hermes must not type or persist secrets/payments. Human gate only.
        blocked.append("credential_payment_human_gate_required")
    allowed = not blocked
    receipt = append_receipt(
        home,
        {
            "event": "authorize_action",
            "gate": gate,
            "actor": actor,
            "target": target,
            "payload_hash": payload_hash,
            "rollback": rollback,
            "readback": readback,
            "evidence_refs": list(evidence_refs),
            "allowed": allowed,
            "blocked_reasons": blocked,
            "executed": False if gate in FORBIDDEN_LIVE_UNTIL_EXACT else bool(execute and allowed),
        },
    )
    return {"ok": allowed, "allowed": allowed, "blocked_reasons": blocked, "executed": receipt["executed"], "receipt": receipt}


def destructive_canary(home: Path, *, actor: str) -> dict[str, Any]:
    state = load_state(home)
    if not state.get("gates", {}).get("destructive", {}).get("enabled"):
        return {"ok": False, "gate": "destructive", "blocked_reasons": ["gate_not_enabled"]}
    canary_dir = state_dir(home) / "canary"
    canary_dir.mkdir(parents=True, exist_ok=True)
    target = canary_dir / "delete-me.txt"
    backup = canary_dir / "delete-me.txt.backup"
    target.write_text("local destructive canary\n", encoding="utf-8")
    shutil.copy2(target, backup)
    before_hash = hashlib.sha256(target.read_bytes()).hexdigest()
    target.unlink()
    readback = {"deleted": not target.exists(), "backup_exists": backup.exists(), "backup_hash": hashlib.sha256(backup.read_bytes()).hexdigest()}
    receipt = append_receipt(
        home,
        {
            "event": "destructive_canary",
            "gate": "destructive",
            "actor": actor,
            "target_path": str(target),
            "backup_path": str(backup),
            "before_hash": before_hash,
            "readback": readback,
            "executed": True,
            "scope": "local_disposable_canary_only",
        },
    )
    return {"ok": readback["deleted"] and readback["backup_exists"], "gate": "destructive", "target_path": str(target), "backup_path": str(backup), "readback": readback, "receipt": receipt}


def taskpool_lifecycle_write(
    home: Path,
    *,
    task_id: str,
    status_value: str,
    evidence_refs: Sequence[str],
    actor: str,
) -> dict[str, Any]:
    state = load_state(home)
    blocked: list[str] = []
    if not state.get("gates", {}).get("taskpool_lifecycle_write_through", {}).get("enabled"):
        blocked.append("gate_not_enabled")
    if not task_id:
        blocked.append("missing_task_id")
    if status_value not in ALLOWED_LIFECYCLE_STATUSES:
        blocked.append("invalid_status")
    if not evidence_refs:
        blocked.append("missing_evidence_refs")
    if blocked:
        receipt = append_receipt(home, {"event": "taskpool_lifecycle_write_blocked", "task_id": task_id, "status": status_value, "blocked_reasons": blocked, "executed": False})
        return {"ok": False, "blocked_reasons": blocked, "receipt": receipt}
    ensure(home)
    row = {
        "schema": "taskpool_lifecycle_write_through_v1",
        "created_at": utc_now(),
        "actor": actor,
        "task_id": task_id,
        "status": status_value,
        "evidence_refs": list(evidence_refs),
        "write_executed": True,
        "adapter": "local_ledger",
        "readback": {"task_id": task_id, "status": status_value},
    }
    row["request_digest"] = digest_obj({k: v for k, v in row.items() if k not in {"created_at"}})
    with taskpool_ledger_path(home).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    receipt = append_receipt(home, {"event": "taskpool_lifecycle_write_through", "task_id": task_id, "status": status_value, "ledger_path": str(taskpool_ledger_path(home)), "executed": True, "readback": row["readback"]})
    return {"ok": True, "ledger_path": str(taskpool_ledger_path(home)), "row": row, "receipt": receipt}


def heartbeat(home: Path, *, actor: str = "cron-worker") -> dict[str, Any]:
    state = load_state(home)
    if not state.get("gates", {}).get("cron_worker_auto_status_write", {}).get("enabled"):
        return {"ok": False, "blocked_reasons": ["gate_not_enabled"]}
    row = {
        "schema": "cron_worker_auto_status_write_v1",
        "created_at": utc_now(),
        "actor": actor,
        "status": "alive",
        "write_executed": True,
        "target": "local_side_effect_gate_heartbeat",
    }
    row["request_digest"] = digest_obj(row)
    ensure(home)
    with heartbeat_path(home).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return {"ok": True, "heartbeat_path": str(heartbeat_path(home)), "row": row}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", default=str(Path.home() / ".hermes"))
    parser.add_argument("--actor", default="operator")
    parser.add_argument("--evidence", action="append", default=[])
    parser.add_argument("--json", action="store_true")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("enable-all")
    sub.add_parser("status")
    sub.add_parser("destructive-canary")
    sub.add_parser("heartbeat")
    p_auth = sub.add_parser("authorize")
    p_auth.add_argument("--gate", required=True)
    p_auth.add_argument("--target", default="")
    p_auth.add_argument("--payload-hash", default="")
    p_auth.add_argument("--rollback", default="")
    p_auth.add_argument("--readback", default="")
    p_life = sub.add_parser("lifecycle-write")
    p_life.add_argument("--task-id", required=True)
    p_life.add_argument("--status", required=True)
    args = parser.parse_args(argv)
    home = Path(args.home).expanduser()
    evidence = list(args.evidence or []) or ["command:high_risk_gate_control"]
    if args.cmd == "enable-all":
        result = enable_all(home, actor=args.actor, evidence_refs=evidence)
    elif args.cmd == "status":
        result = status(home)
    elif args.cmd == "destructive-canary":
        result = destructive_canary(home, actor=args.actor)
    elif args.cmd == "heartbeat":
        result = heartbeat(home, actor=args.actor)
    elif args.cmd == "authorize":
        result = authorize_action(home, gate=args.gate, target=args.target, payload_hash=args.payload_hash, rollback=args.rollback, readback=args.readback, evidence_refs=evidence, actor=args.actor)
    elif args.cmd == "lifecycle-write":
        result = taskpool_lifecycle_write(home, task_id=args.task_id, status_value=args.status, evidence_refs=evidence, actor=args.actor)
    else:  # pragma: no cover
        raise AssertionError(args.cmd)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(result)
    return 0 if result.get("ok", False) else 2


if __name__ == "__main__":
    raise SystemExit(main())
