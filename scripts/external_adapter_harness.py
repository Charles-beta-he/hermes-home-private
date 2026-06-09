#!/usr/bin/env python3
"""Digest-bound external adapter write-through harness.

Default-on external adapter executor for Hermes self-architecture experiments.
It supports three allowlisted local adapters: local_file fixtures, taskpool
markdown note closeout, and Kanban SQLite status closeout. It does not send
network requests, install skills, write memory, deploy, or run shell commands.
"""
from __future__ import annotations

import argparse
import json
import os
import hashlib
import sqlite3
import time
from pathlib import Path
from typing import Any

try:
    from harness_event_ledger import append_event
except Exception:  # pragma: no cover - ledger is best-effort for standalone imports
    append_event = None

HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))).expanduser()
HARNESS_DIR = HERMES_HOME / "state" / "external-adapter-harness"
ELEVATED_ROLES = {"admin", "operator", "system"}
DISABLE_VALUES = {"0", "false", "off", "no", "disabled"}
ENABLE_VALUES = {"1", "true", "yes", "on"}
ALLOWED_ADAPTERS = {"local_file", "taskpool_note", "kanban_db"}
ADAPTER_AUTHORITY = "allowlisted_local_adapters_only_no_network_no_skill_no_memory_no_shell"


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


def safe_target_path(target_path: str | Path, *, base_dir: str | Path | None, suffixes: set[str]) -> Path:
    if base_dir is None:
        raise ValueError("base_dir_required_for_real_adapter")
    base = Path(base_dir).expanduser().resolve()
    raw = Path(target_path).expanduser()
    path = raw if raw.is_absolute() else base / raw
    if path.suffix not in suffixes:
        raise ValueError("target_path_suffix_not_allowlisted")
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)
    resolved_parent = parent.resolve()
    if not (resolved_parent == base or base in resolved_parent.parents):
        raise ValueError("target_path_outside_base_dir")
    _reject_symlink_chain(resolved_parent, stop_at=base)
    if path.exists() and path.is_symlink():
        raise ValueError(f"symlink_rejected:{path}")
    return resolved_parent / path.name


def read_taskpool_note(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ValueError("taskpool_note_missing")
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("taskpool_frontmatter_missing")
    end = text.find("\n---", 4)
    if end < 0:
        raise ValueError("taskpool_frontmatter_unclosed")
    frontmatter = text[4:end]
    body = text[end + 4:]
    status = ""
    for line in frontmatter.splitlines():
        if line.strip().startswith("status:"):
            status = line.split(":", 1)[1].strip().strip('"\'')
            break
    if not status:
        raise ValueError("taskpool_status_missing")
    return {"status": status, "frontmatter": frontmatter, "body": body, "text": text}


def write_taskpool_note_status(path: Path, state: dict[str, Any], *, target_status: str, audit_payload: dict[str, Any]) -> None:
    lines = state["frontmatter"].splitlines()
    updated = []
    replaced = False
    for line in lines:
        if line.strip().startswith("status:"):
            updated.append(f"status: {target_status}")
            replaced = True
        else:
            updated.append(line)
    if not replaced:
        raise ValueError("taskpool_status_missing")
    body = state["body"]
    suffix = "\n" if body.endswith("\n") else "\n\n"
    audit = f"<!-- hermes_external_adapter_taskpool_write: {canonical_json(audit_payload)} -->\n"
    path.write_text("---\n" + "\n".join(updated) + "\n---" + body + suffix + audit, encoding="utf-8")


def read_kanban_status(db_path: Path, task_id: str) -> dict[str, Any]:
    if not db_path.exists():
        raise ValueError("kanban_db_missing")
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        table = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'").fetchone()
        if not table:
            raise ValueError("kanban_tasks_table_missing")
        row = conn.execute("SELECT id, status FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            raise ValueError("kanban_task_missing")
        return {"status": row["status"], "task_id": row["id"]}


def write_kanban_status(db_path: Path, task_id: str, target_status: str) -> None:
    with sqlite3.connect(str(db_path)) as conn:
        cur = conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (target_status, task_id))
        if cur.rowcount != 1:
            raise ValueError("kanban_update_rowcount_mismatch")
        conn.commit()


def adapter_path(intent: dict[str, Any]) -> Path:
    adapter = intent.get("adapter")
    path_value = intent.get("adapter_state_path")
    if not path_value:
        raise ValueError("adapter_state_path_required")
    if adapter == "local_file":
        return safe_state_path(str(path_value), base_dir=intent.get("harness_base_dir") or None)
    if adapter == "taskpool_note":
        return safe_target_path(str(path_value), base_dir=intent.get("harness_base_dir"), suffixes={".md"})
    if adapter == "kanban_db":
        return safe_target_path(str(path_value), base_dir=intent.get("harness_base_dir"), suffixes={".db", ".sqlite", ".sqlite3"})
    raise ValueError("adapter_not_allowlisted")


def read_adapter_state(intent: dict[str, Any], path: Path) -> dict[str, Any]:
    adapter = intent.get("adapter")
    if adapter == "local_file":
        return read_state(path)
    if adapter == "taskpool_note":
        state = read_taskpool_note(path)
        return {"status": state["status"], "previous_state": state}
    if adapter == "kanban_db":
        return read_kanban_status(path, str(intent.get("task_id")))
    raise ValueError("adapter_not_allowlisted")


def write_adapter_state(intent: dict[str, Any], path: Path, *, request_digest: str, authorization_id: str) -> None:
    adapter = intent.get("adapter")
    if adapter == "local_file":
        before = read_state(path)
        rollback_snapshot = {
            "previous_status": before.get("status", "missing"),
            "previous_state": before,
            "adapter_state_path": str(path),
            "adapter": adapter,
            "request_digest": request_digest,
        }
        after = dict(before)
        after.update({"status": intent.get("target_status"), "task_id": intent.get("task_id"), "updated_at": utc_ts(), "last_request_digest": request_digest, "intent_id": intent.get("intent_id"), "authorization_id": authorization_id, "mutation_digest": intent.get("mutation_digest"), "rollback_snapshot": rollback_snapshot})
        write_state(path, after)
        return
    if adapter == "taskpool_note":
        state = read_taskpool_note(path)
        write_taskpool_note_status(path, state, target_status=str(intent.get("target_status")), audit_payload={"request_digest": request_digest, "intent_id": intent.get("intent_id"), "authorization_id": authorization_id})
        return
    if adapter == "kanban_db":
        write_kanban_status(path, str(intent.get("task_id")), str(intent.get("target_status")))
        return
    raise ValueError("adapter_not_allowlisted")


def build_write_intent(
    *,
    task_id: str,
    adapter_state_path: str | Path,
    adapter: str = "local_file",
    target_status: str = "done",
    canonical_done_authorization_id: str,
    evidence: list[str] | None = None,
    base_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Create a digest-bound local-file adapter write intent."""
    adapter = str(adapter or "local_file").strip()
    if adapter not in ALLOWED_ADAPTERS:
        raise ValueError("adapter_not_allowlisted")
    if target_status != "done":
        raise ValueError("only_target_status_done_supported")
    if not canonical_done_authorization_id:
        raise ValueError("canonical_done_authorization_id_required")
    evidence = [str(x) for x in (evidence or []) if str(x).strip()]
    if not evidence:
        raise ValueError("non_empty_evidence_required")
    harness_base_dir = str((Path(base_dir).expanduser() if base_dir else HARNESS_DIR).resolve())
    if adapter == "local_file":
        state_path = safe_state_path(adapter_state_path, base_dir=base_dir)
    elif adapter == "taskpool_note":
        state_path = safe_target_path(adapter_state_path, base_dir=base_dir, suffixes={".md"})
    else:
        state_path = safe_target_path(adapter_state_path, base_dir=base_dir, suffixes={".db", ".sqlite", ".sqlite3"})
    mutation_payload = {
        "adapter": adapter,
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
        "adapter": adapter,
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
        "authority": ADAPTER_AUTHORITY,
    }
    if intent.get("schema") != "hermes_external_adapter_write_intent_v1":
        auth["reasons"].append("invalid_intent_schema")
    if intent.get("adapter") not in ALLOWED_ADAPTERS:
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
        auth["reasons"].append("approved_digest_bound_allowlisted_adapter_write")
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
        "authority": ADAPTER_AUTHORITY,
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
    try:
        path = adapter_path(intent)
        before = read_adapter_state(intent, path)
    except Exception as exc:
        result["reason"] = str(exc)
        return result
    request_digest = digest({
        "intent_id": intent.get("intent_id"),
        "authorization_id": authorization.get("authorization_id"),
        "mutation_digest": intent.get("mutation_digest"),
    })
    if before.get("status") == intent.get("target_status") and (intent.get("adapter") != "local_file" or before.get("last_request_digest") == request_digest):
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
        "previous_state": before.get("previous_state", before),
        "adapter_state_path": str(path),
        "adapter": intent.get("adapter"),
        "task_id": intent.get("task_id"),
        "target_status": intent.get("target_status"),
        "request_digest": request_digest,
    }
    write_adapter_state(intent, path, request_digest=request_digest, authorization_id=str(authorization.get("authorization_id")))
    readback = read_adapter_state(intent, path)
    if intent.get("adapter") == "local_file":
        # Preserve local-file rollback snapshot inside the fixture state.
        local = read_state(path)
        rollback_snapshot = local.get("rollback_snapshot", rollback_snapshot)
    verified = readback.get("status") == intent.get("target_status")
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
    if append_event is not None:
        result["ledger_event"] = append_event(kind="external_adapter_write", payload={k: result.get(k) for k in ["status", "adapter", "intent_id", "authorization_id", "request_digest", "readback_verified", "adapter_state_path"]})
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
    adapter = snapshot.get("adapter") or execution.get("adapter") or "local_file"
    fake_intent = {"adapter": adapter, "adapter_state_path": rollback_path_value, "harness_base_dir": execution.get("harness_base_dir"), "task_id": snapshot.get("task_id")}
    path = adapter_path(fake_intent)
    if adapter == "local_file":
        current = read_state(path)
        if current.get("last_request_digest") != expected_request_digest:
            result["reason"] = "current_state_drift"
            return result
    else:
        current = read_adapter_state(fake_intent, path)
        if current.get("status") != snapshot.get("target_status"):
            result["reason"] = "current_state_drift"
            return result
    previous = snapshot.get("previous_state") or {"status": snapshot.get("previous_status", "missing")}
    if adapter == "local_file":
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
    elif adapter == "taskpool_note":
        if snapshot.get("previous_status") == "missing":
            result["reason"] = "cannot_restore_missing_taskpool_note"
            return result
        write_taskpool_note_status(path, previous, target_status=str(snapshot.get("previous_status")), audit_payload={"rollback_of_request_digest": expected_request_digest})
        readback = {"status": read_taskpool_note(path)["status"]}
    elif adapter == "kanban_db":
        if snapshot.get("previous_status") == "missing":
            result["reason"] = "cannot_restore_missing_kanban_task"
            return result
        write_kanban_status(path, str(snapshot.get("task_id")), str(snapshot.get("previous_status")))
        readback = read_kanban_status(path, str(snapshot.get("task_id")))
    else:
        result["reason"] = "adapter_not_allowlisted"
        return result
    verified = readback.get("status") == snapshot.get("previous_status", "missing")
    result.update({
        "status": "external_adapter_rollback_verified" if verified else "external_adapter_rollback_mismatch",
        "rollback_executed": True,
        "readback_verified": verified,
        "adapter_state_path": str(path),
        "readback_status": readback.get("status"),
    })
    if append_event is not None:
        result["ledger_event"] = append_event(kind="external_adapter_rollback", payload={k: result.get(k) for k in ["status", "request_digest", "rollback_executed", "readback_verified", "adapter_state_path"]})
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Digest-bound local-file external adapter harness")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("mode")
    p = sub.add_parser("intent")
    p.add_argument("--task-id", required=True)
    p.add_argument("--adapter", default="local_file", choices=sorted(ALLOWED_ADAPTERS))
    p.add_argument("--adapter-state-path", required=True)
    p.add_argument("--base-dir", default=None)
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
        print(json.dumps(build_write_intent(task_id=args.task_id, adapter=args.adapter, adapter_state_path=args.adapter_state_path, canonical_done_authorization_id=args.canonical_done_authorization_id, evidence=args.evidence, base_dir=args.base_dir), ensure_ascii=False, indent=2))
    elif args.cmd == "authorize":
        print(json.dumps(authorize_write(json.loads(args.intent_json), actor_id=args.actor_id, actor_role=args.actor_role, evidence=args.evidence), ensure_ascii=False, indent=2))
    elif args.cmd == "execute":
        print(json.dumps(execute_write(json.loads(args.intent_json), json.loads(args.authorization_json), mode=args.mode), ensure_ascii=False, indent=2))
    elif args.cmd == "rollback":
        print(json.dumps(rollback_write(json.loads(args.execution_json), expected_request_digest=args.expected_request_digest, evidence=args.evidence), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
