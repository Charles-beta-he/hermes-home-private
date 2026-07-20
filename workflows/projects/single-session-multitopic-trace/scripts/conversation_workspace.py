#!/usr/bin/env python3
"""Local-only Conversation Workspace OS control surface.

The CLI owns project-scoped SSOT artifacts only. It never starts tmux, executes
workers, mutates taskpool/Mission state, or performs external actions.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
DIRECTION_STATES = {"proposal", "contract-ready", "in-progress", "validated", "promoted", "released", "superseded"}
TASK_STATES = {"backlog", "ready", "claimed", "running", "review", "blocked", "done", "cancelled"}
RUNTIME_STATES = {"starting", "running", "stopping", "exited", "failed", "killed", "detached", "recovered"}
CHAT_STATES = {"active", "handoff-ready", "archived", "stale"}
CLAIM_MODES = {"write", "review", "read"}
CLAIM_STATES = {"active", "released", "expired", "cancelled"}
EVIDENCE_KINDS = {"command", "diff", "test", "browser", "api", "log", "human", "limitation", "file"}
PUBLIC_EVENT_TYPES = {"note.recorded", "decision.recorded", "session.observed", "runtime.observed"}
SECRET_KEYS = {
    "password", "passwd", "secret", "api_key", "apikey", "access_key", "private_key",
    "credential", "credentials", "card_number", "authorization", "bearer_token",
}
AUTHORITY_SMUGGLING_KEYS = {
    "mark_done", "external_write", "write_through", "write_through_enabled",
    "send_executed", "deploy", "push", "task_status", "lifecycle_target",
}
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().isoformat().replace("+00:00", "Z")


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def emit(payload: dict[str, Any], code: int = 0) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return code


def load_json(path: Path, expected: type | tuple[type, ...] | None = None) -> Any:
    data = json.loads(path.read_text(encoding="utf-8"))
    if expected is not None and not isinstance(data, expected):
        raise ValueError(f"{path} must contain {getattr(expected, '__name__', expected)}")
    return data


def atomic_write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
        dir_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


@contextmanager
def exclusive_file_lock(path: Path):
    """Serialize project-state read/check/write transactions across processes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def write_if_missing(path: Path, payload: Any) -> bool:
    if path.exists():
        return False
    atomic_write_json(path, payload)
    return True


def validate_id(label: str, value: str) -> None:
    if not SAFE_ID.fullmatch(value):
        raise ValueError(f"invalid {label}: {value!r}")


def validate_scope(value: str) -> None:
    normalized = value.strip().replace("\\", "/")
    if not normalized or normalized.startswith("/") or "\x00" in normalized:
        raise ValueError(f"scope must be a non-empty project-relative pattern: {value!r}")
    if any(part == ".." for part in normalized.split("/")):
        raise ValueError(f"scope cannot contain parent traversal: {value!r}")


def validate_safe_payload(value: Any, trail: tuple[str, ...] = ()) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).strip().lower()
            if normalized in SECRET_KEYS:
                raise ValueError(f"secret-like field rejected: {'.'.join(trail + (str(key),))}")
            if normalized in AUTHORITY_SMUGGLING_KEYS:
                raise ValueError(f"authority-smuggling field rejected: {'.'.join(trail + (str(key),))}")
            validate_safe_payload(item, trail + (str(key),))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            validate_safe_payload(item, trail + (str(index),))


def slug(value: str, limit: int = 40) -> str:
    result = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return (result or "lane")[:limit].rstrip("-")


def paths(root: Path) -> dict[str, Path]:
    return {
        "root": root,
        "project": root / "project.json",
        "events": root / "02-ledger" / "events.jsonl",
        "event_lock": root / "02-ledger" / ".events.lock",
        "state_lock": root / "05-runtime" / ".state.lock",
        "tasks": root / "02-ledger" / "tasks.json",
        "evidence": root / "03-evidence" / "evidence-index.json",
        "handoffs": root / "04-handoffs" / "sessions",
        "claims": root / "05-runtime" / "active-claims.json",
        "worktrees": root / "05-runtime" / "worktrees.json",
        "tmux": root / "05-runtime" / "tmux-manifest.json",
        "status": root / "06-status",
    }


def append_event(root: Path, event_type: str, payload: dict[str, Any], actor: str = "workspace-os-cli") -> dict[str, Any]:
    validate_safe_payload(payload)
    p = paths(root)
    p["events"].parent.mkdir(parents=True, exist_ok=True)
    event = {
        "schema_version": SCHEMA_VERSION,
        "event_id": f"evt-{utc_now().strftime('%Y%m%dT%H%M%S%fZ')}-{os.getpid()}",
        "event_type": event_type,
        "occurred_at": iso_now(),
        "actor": actor,
        "payload": payload,
    }
    with p["event_lock"].open("a+", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        with p["events"].open("a", encoding="utf-8") as events_handle:
            events_handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
            events_handle.flush()
            os.fsync(events_handle.fileno())
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
    return event


def scope_static_prefix(value: str) -> str:
    clean = value.strip().replace("\\", "/").lstrip("./")
    wildcard = len(clean)
    for marker in ("*", "?", "["):
        pos = clean.find(marker)
        if pos >= 0:
            wildcard = min(wildcard, pos)
    return clean[:wildcard].rstrip("/")


def scopes_overlap(left: str, right: str) -> bool:
    if left.strip() in {"*", "**", "**/*"} or right.strip() in {"*", "**", "**/*"}:
        return True
    a = scope_static_prefix(left)
    b = scope_static_prefix(right)
    if not a or not b:
        return True
    if a == b:
        return True
    return a.startswith(b + "/") or b.startswith(a + "/")


def claim_is_active(claim: dict[str, Any], now: datetime | None = None) -> bool:
    if claim.get("status") != "active":
        return False
    try:
        return parse_time(str(claim["expires_at"])) > (now or utc_now())
    except Exception:
        return False


def next_window_name(manifest: dict[str, Any], direction: str) -> str:
    existing = {str(w.get("name")) for w in manifest.get("windows", []) if isinstance(w, dict)}
    number = 10
    lane = slug(direction, 28)
    while f"{number:02d}-{lane}" in existing:
        number += 10
    return f"{number:02d}-{lane}"


def init_project(root: Path, project_id: str, display_name: str) -> dict[str, Any]:
    validate_id("project id", project_id)
    root.mkdir(parents=True, exist_ok=True)
    for dirname in ("00-spec", "01-directions", "02-ledger", "03-evidence/artifacts", "04-handoffs/sessions", "04-handoffs/workers", "05-runtime/receipts", "06-status"):
        (root / dirname).mkdir(parents=True, exist_ok=True)
    p = paths(root)
    created: list[str] = []
    project = {
        "schema_version": SCHEMA_VERSION,
        "project_id": project_id,
        "display_name": display_name,
        "ssot_root": str(root.resolve()),
        "tmux_session": f"hx-{slug(project_id, 48)}",
        "state_domains": {
            "direction": sorted(DIRECTION_STATES),
            "task": sorted(TASK_STATES),
            "worker_runtime": sorted(RUNTIME_STATES),
            "chat_session": sorted(CHAT_STATES),
        },
        "authority": {
            "external_dispatch": False,
            "taskpool_lifecycle_write": False,
            "mission_lifecycle_write": False,
            "tmux_execution": False,
            "worker_execution": False,
            "deploy_push": False,
            "destructive_operations": False,
            "credential_entry": False,
        },
    }
    defaults = {
        p["project"]: project,
        p["tasks"]: [],
        p["evidence"]: [],
        p["claims"]: [],
        p["worktrees"]: [],
        p["tmux"]: {
            "schema_version": SCHEMA_VERSION,
            "project_id": project_id,
            "session_name": project["tmux_session"],
            "execute_commands": False,
            "windows": [{
                "name": "00-control",
                "direction_id": None,
                "claim_id": None,
                "workdir": str(root.resolve()),
                "panes": [{"role": "control"}],
            }],
        },
    }
    for path, payload in defaults.items():
        if write_if_missing(path, payload):
            created.append(str(path))
    if not p["events"].exists():
        append_event(root, "project.initialized", {"project_id": project_id, "display_name": display_name})
        created.append(str(p["events"]))
    return {"ok": True, "root": str(root), "created": created, "preserved_existing": len(created) < len(defaults) + 1}


def require_project(root: Path) -> tuple[dict[str, Any], dict[str, Path]]:
    p = paths(root)
    if not p["project"].is_file():
        raise ValueError(f"project not initialized: {p['project']}")
    return load_json(p["project"], dict), p


def cmd_init(args: argparse.Namespace) -> int:
    return emit(init_project(args.root.resolve(), args.project_id, args.display_name or args.project_id))


def cmd_event_append(args: argparse.Namespace) -> int:
    require_project(args.root)
    payload = load_json(args.payload_file, dict)
    event = append_event(args.root, args.event_type, payload, actor=args.actor)
    return emit({"ok": True, "event": event})


def cmd_claim_acquire(args: argparse.Namespace) -> int:
    project, p = require_project(args.root)
    validate_id("claim id", args.claim_id)
    validate_id("direction id", args.direction_id)
    validate_id("owner session", args.owner_session)
    if args.mode == "write" and args.worktree is None:
        raise ValueError("write claim requires --worktree")
    if args.worktree is not None and not args.worktree.resolve().is_dir():
        raise ValueError(f"worktree does not exist: {args.worktree}")
    if not args.scope:
        raise ValueError("at least one --scope is required")
    for scope in args.scope:
        validate_scope(scope)
    if not 1 <= args.ttl_minutes <= 1440:
        raise ValueError("ttl-minutes must be between 1 and 1440")
    with exclusive_file_lock(p["state_lock"]):
        claims = load_json(p["claims"], list)
        if any(c.get("claim_id") == args.claim_id for c in claims if isinstance(c, dict)):
            raise ValueError(f"claim id already exists: {args.claim_id}")
        active = [c for c in claims if isinstance(c, dict) and claim_is_active(c)]
        for current in active:
            if args.mode == "write" and current.get("mode") == "write":
                if current.get("direction_id") == args.direction_id:
                    raise ValueError(f"active write claim already owns direction: {args.direction_id}")
                for left in args.scope:
                    for right in current.get("scope", []):
                        if scopes_overlap(left, str(right)):
                            raise ValueError(f"scope overlaps active claim {current.get('claim_id')}: {left!r} vs {right!r}")
        created_at = utc_now()
        claim = {
            "schema_version": SCHEMA_VERSION,
            "claim_id": args.claim_id,
            "project_id": project["project_id"],
            "direction_id": args.direction_id,
            "owner_type": "hermes-session",
            "owner_session": args.owner_session,
            "mode": args.mode,
            "scope": args.scope,
            "worktree": str(args.worktree.resolve()) if args.worktree else None,
            "status": "active",
            "created_at": created_at.isoformat().replace("+00:00", "Z"),
            "expires_at": (created_at + timedelta(minutes=args.ttl_minutes)).isoformat().replace("+00:00", "Z"),
        }
        validate_safe_payload(claim)
        claims.append(claim)
        atomic_write_json(p["claims"], claims)
        manifest = load_json(p["tmux"], dict)
        window = {
            "name": next_window_name(manifest, args.direction_id),
            "direction_id": args.direction_id,
            "claim_id": args.claim_id,
            "workdir": claim["worktree"] or str(args.root.resolve()),
            "panes": [{"role": "executor"}, {"role": "verify"}],
        }
        manifest.setdefault("windows", []).append(window)
        atomic_write_json(p["tmux"], manifest)
        event = append_event(args.root, "claim.acquired", {"claim_id": args.claim_id, "direction_id": args.direction_id, "mode": args.mode, "scope": args.scope})
    return emit({"ok": True, "claim": claim, "tmux_window": window, "event_id": event["event_id"], "tmux_executed": False})


def cmd_claim_release(args: argparse.Namespace) -> int:
    _, p = require_project(args.root)
    with exclusive_file_lock(p["state_lock"]):
        claims = load_json(p["claims"], list)
        found = None
        for claim in claims:
            if isinstance(claim, dict) and claim.get("claim_id") == args.claim_id:
                found = claim
                break
        if found is None:
            raise ValueError(f"unknown claim: {args.claim_id}")
        if found.get("status") == "released":
            return emit({"ok": True, "idempotent": True, "claim": found})
        if found.get("status") != "active":
            raise ValueError(f"claim cannot be released from state: {found.get('status')}")
        found["status"] = "released"
        found["released_at"] = iso_now()
        atomic_write_json(p["claims"], claims)
        manifest = load_json(p["tmux"], dict)
        manifest["windows"] = [w for w in manifest.get("windows", []) if not isinstance(w, dict) or w.get("claim_id") != args.claim_id]
        atomic_write_json(p["tmux"], manifest)
        event = append_event(args.root, "claim.released", {"claim_id": args.claim_id})
    return emit({"ok": True, "claim": found, "event_id": event["event_id"], "tmux_executed": False})


def cmd_handoff_add(args: argparse.Namespace) -> int:
    _, p = require_project(args.root)
    handoff = load_json(args.file, dict)
    validate_safe_payload(handoff)
    required = {"handoff_id", "direction_id", "source_session_id", "objective", "verified_current_state", "next_safe_step", "closure_state"}
    missing = sorted(required - set(handoff))
    if missing:
        raise ValueError(f"handoff missing fields: {', '.join(missing)}")
    validate_id("handoff id", str(handoff["handoff_id"]))
    validate_id("direction id", str(handoff["direction_id"]))
    if handoff["closure_state"] not in CHAT_STATES - {"active"}:
        raise ValueError("handoff closure_state must be handoff-ready, archived, or stale")
    with exclusive_file_lock(p["state_lock"]):
        destination = p["handoffs"] / f"{handoff['handoff_id']}.json"
        if destination.exists():
            existing = load_json(destination, dict)
            comparable_existing = {key: value for key, value in existing.items() if key != "recorded_at"}
            comparable_input = {key: value for key, value in handoff.items() if key != "recorded_at"}
            if comparable_existing == comparable_input:
                return emit({"ok": True, "idempotent": True, "path": str(destination)})
            raise ValueError(f"handoff id collision: {handoff['handoff_id']}")
        handoff["recorded_at"] = handoff.get("recorded_at") or iso_now()
        atomic_write_json(destination, handoff)
        event = append_event(args.root, "handoff.recorded", {"handoff_id": handoff["handoff_id"], "direction_id": handoff["direction_id"], "source_session_id": handoff["source_session_id"]})
    return emit({"ok": True, "path": str(destination), "event_id": event["event_id"]})


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def cmd_evidence_add(args: argparse.Namespace) -> int:
    _, p = require_project(args.root)
    validate_id("evidence id", args.evidence_id)
    target = args.path.resolve()
    if not target.is_file():
        raise ValueError(f"evidence file does not exist: {target}")
    with exclusive_file_lock(p["state_lock"]):
        evidence = load_json(p["evidence"], list)
        record = {
            "schema_version": SCHEMA_VERSION,
            "evidence_id": args.evidence_id,
            "kind": args.kind,
            "path": str(target),
            "sha256": sha256_file(target),
            "summary": args.summary,
            "claim_refs": args.claim_ref,
            "recorded_at": iso_now(),
        }
        validate_safe_payload(record)
        for current in evidence:
            if isinstance(current, dict) and current.get("evidence_id") == args.evidence_id:
                comparable = {k: v for k, v in current.items() if k != "recorded_at"}
                if comparable == {k: v for k, v in record.items() if k != "recorded_at"}:
                    return emit({"ok": True, "idempotent": True, "evidence": current})
                raise ValueError(f"evidence id collision: {args.evidence_id}")
        evidence.append(record)
        atomic_write_json(p["evidence"], evidence)
        event = append_event(args.root, "evidence.recorded", {"evidence_id": args.evidence_id, "kind": args.kind, "claim_refs": args.claim_ref})
    return emit({"ok": True, "evidence": record, "event_id": event["event_id"]})


def add_finding(findings: list[dict[str, Any]], severity: str, check: str, message: str, path: Path | None = None) -> None:
    item: dict[str, Any] = {"severity": severity, "check": check, "message": message}
    if path is not None:
        item["path"] = str(path)
    findings.append(item)


def inspect_tmux(session_name: str) -> tuple[set[str], str | None]:
    proc = subprocess.run(["tmux", "list-sessions", "-F", "#{session_name}"], text=True, capture_output=True, check=False, timeout=5)
    if proc.returncode != 0:
        message = (proc.stderr or proc.stdout).strip()
        if (
            "no server running" in message
            or "failed to connect" in message
            or "error connecting to" in message
        ):
            return set(), None
        return set(), message or f"tmux list-sessions exited {proc.returncode}"
    sessions = {line.strip() for line in proc.stdout.splitlines() if line.strip()}
    if session_name not in sessions:
        return set(), None
    windows = subprocess.run(["tmux", "list-windows", "-t", session_name, "-F", "#{window_name}"], text=True, capture_output=True, check=False, timeout=5)
    if windows.returncode != 0:
        return set(), (windows.stderr or windows.stdout).strip() or "tmux list-windows failed"
    return {line.strip() for line in windows.stdout.splitlines() if line.strip()}, None


def doctor(root: Path, inspect_runtime: bool) -> dict[str, Any]:
    p = paths(root)
    findings: list[dict[str, Any]] = []
    required = [p["project"], p["events"], p["tasks"], p["evidence"], p["claims"], p["worktrees"], p["tmux"]]
    for path in required:
        if not path.is_file():
            add_finding(findings, "error", "required_file", "required file missing", path)
    if any(f["severity"] == "error" for f in findings):
        return summarize_doctor(root, findings, inspect_runtime)
    try:
        project = load_json(p["project"], dict)
        validate_safe_payload(project)
        authority = project.get("authority")
        if not isinstance(authority, dict) or any(value is not False for value in authority.values()):
            add_finding(findings, "error", "authority_closed", "all project authority flags must be explicitly false", p["project"])
        domains = project.get("state_domains") or {}
        expected_domains = {"direction", "task", "worker_runtime", "chat_session"}
        if set(domains) != expected_domains:
            add_finding(findings, "error", "state_domains", "state domains are missing or collapsed", p["project"])
    except Exception as exc:
        add_finding(findings, "error", "project_json", f"{type(exc).__name__}: {exc}", p["project"])
        project = {}
    event_ids: set[str] = set()
    try:
        for line_number, line in enumerate(p["events"].read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            event = json.loads(line)
            validate_safe_payload(event)
            event_id = str(event.get("event_id") or "")
            if not event_id:
                add_finding(findings, "error", "event_id", f"line {line_number} missing event_id", p["events"])
            elif event_id in event_ids:
                add_finding(findings, "error", "event_id_unique", f"duplicate event_id {event_id}", p["events"])
            event_ids.add(event_id)
    except Exception as exc:
        add_finding(findings, "error", "events_jsonl", f"{type(exc).__name__}: {exc}", p["events"])
    evidence_ids: set[str] = set()
    try:
        evidence = load_json(p["evidence"], list)
        for record in evidence:
            if not isinstance(record, dict):
                add_finding(findings, "error", "evidence_shape", "evidence record must be object", p["evidence"])
                continue
            validate_safe_payload(record)
            eid = str(record.get("evidence_id") or "")
            if not eid or eid in evidence_ids:
                add_finding(findings, "error", "evidence_id_unique", f"missing or duplicate evidence id {eid!r}", p["evidence"])
            evidence_ids.add(eid)
            target = Path(str(record.get("path") or "")).expanduser()
            if not target.is_file():
                add_finding(findings, "error", "evidence_exists", f"evidence artifact missing for {eid}", target)
            elif record.get("sha256") != sha256_file(target):
                add_finding(findings, "error", "evidence_hash", f"evidence hash mismatch for {eid}", target)
    except Exception as exc:
        add_finding(findings, "error", "evidence_json", f"{type(exc).__name__}: {exc}", p["evidence"])
    try:
        tasks = load_json(p["tasks"], list)
        for task in tasks:
            if not isinstance(task, dict):
                add_finding(findings, "error", "task_shape", "task record must be object", p["tasks"])
                continue
            status = task.get("status")
            if status not in TASK_STATES:
                add_finding(findings, "error", "task_status", f"invalid task state {status!r}", p["tasks"])
            refs = task.get("evidence_refs") or []
            if status == "done" and not refs:
                add_finding(findings, "error", "done_requires_evidence", f"task {task.get('task_id')} is done without evidence", p["tasks"])
            for ref in refs:
                if ref not in evidence_ids:
                    add_finding(findings, "error", "task_evidence_ref", f"task {task.get('task_id')} references unknown evidence {ref}", p["tasks"])
    except Exception as exc:
        add_finding(findings, "error", "tasks_json", f"{type(exc).__name__}: {exc}", p["tasks"])
    active_claims: list[dict[str, Any]] = []
    try:
        claims = load_json(p["claims"], list)
        claim_ids: set[str] = set()
        for claim in claims:
            if not isinstance(claim, dict):
                add_finding(findings, "error", "claim_shape", "claim record must be object", p["claims"])
                continue
            validate_safe_payload(claim)
            cid = str(claim.get("claim_id") or "")
            if not cid or cid in claim_ids:
                add_finding(findings, "error", "claim_id_unique", f"missing or duplicate claim id {cid!r}", p["claims"])
            claim_ids.add(cid)
            if claim.get("mode") not in CLAIM_MODES or claim.get("status") not in CLAIM_STATES:
                add_finding(findings, "error", "claim_state", f"invalid claim mode/state for {cid}", p["claims"])
            if claim.get("status") == "active":
                try:
                    if parse_time(str(claim["expires_at"])) <= utc_now():
                        add_finding(findings, "error", "claim_expired", f"active claim expired: {cid}", p["claims"])
                    else:
                        active_claims.append(claim)
                except Exception:
                    add_finding(findings, "error", "claim_expiry", f"invalid expires_at for {cid}", p["claims"])
            if claim.get("mode") == "write":
                worktree = Path(str(claim.get("worktree") or "")).expanduser()
                if not worktree.is_dir():
                    add_finding(findings, "error", "claim_worktree", f"write claim worktree missing: {cid}", worktree)
        for index, left in enumerate(active_claims):
            if left.get("mode") != "write":
                continue
            for right in active_claims[index + 1:]:
                if right.get("mode") != "write":
                    continue
                if left.get("direction_id") == right.get("direction_id"):
                    add_finding(findings, "error", "direction_single_writer", f"active write claims share direction: {left.get('claim_id')} and {right.get('claim_id')}", p["claims"])
                if any(scopes_overlap(str(a), str(b)) for a in left.get("scope", []) for b in right.get("scope", [])):
                    add_finding(findings, "error", "scope_single_writer", f"active write claims overlap: {left.get('claim_id')} and {right.get('claim_id')}", p["claims"])
    except Exception as exc:
        add_finding(findings, "error", "claims_json", f"{type(exc).__name__}: {exc}", p["claims"])
    try:
        manifest = load_json(p["tmux"], dict)
        validate_safe_payload(manifest)
        if manifest.get("execute_commands") is not False:
            add_finding(findings, "error", "tmux_no_execute", "tmux manifest must set execute_commands=false", p["tmux"])
        windows = manifest.get("windows")
        if not isinstance(windows, list) or not windows:
            add_finding(findings, "error", "tmux_windows", "tmux manifest requires windows", p["tmux"])
            windows = []
        names: set[str] = set()
        active_claim_ids = {str(c.get("claim_id")) for c in active_claims}
        projected_claim_ids: set[str] = set()
        for window in windows:
            if not isinstance(window, dict):
                add_finding(findings, "error", "tmux_window_shape", "tmux window must be object", p["tmux"])
                continue
            if "command" in window:
                add_finding(findings, "error", "tmux_command_replay", "tmux manifest cannot contain command", p["tmux"])
            name = str(window.get("name") or "")
            if not name or name in names:
                add_finding(findings, "error", "tmux_window_unique", f"missing or duplicate window name {name!r}", p["tmux"])
            names.add(name)
            for pane in window.get("panes", []):
                if not isinstance(pane, dict) or "command" in pane:
                    add_finding(findings, "error", "tmux_pane_no_command", f"pane in {name} contains invalid shape or command", p["tmux"])
            if window.get("claim_id"):
                projected_claim_ids.add(str(window["claim_id"]))
        missing_projection = sorted(active_claim_ids - projected_claim_ids)
        if missing_projection:
            add_finding(findings, "warning", "tmux_claim_projection", f"active claims missing tmux windows: {missing_projection}", p["tmux"])
        if inspect_runtime:
            actual_windows, tmux_error = inspect_tmux(str(manifest.get("session_name") or ""))
            if tmux_error:
                add_finding(findings, "warning", "tmux_inspection", tmux_error, p["tmux"])
            elif active_claims and not actual_windows:
                add_finding(findings, "warning", "tmux_runtime_missing", "active claims exist but tmux session is absent; recovery is required", p["tmux"])
            elif actual_windows:
                missing_actual = sorted(names - actual_windows)
                if missing_actual:
                    add_finding(findings, "warning", "tmux_runtime_drift", f"manifest windows absent from tmux: {missing_actual}", p["tmux"])
    except Exception as exc:
        add_finding(findings, "error", "tmux_manifest", f"{type(exc).__name__}: {exc}", p["tmux"])
    if p["handoffs"].exists():
        for handoff_path in sorted(p["handoffs"].glob("*.json")):
            try:
                handoff = load_json(handoff_path, dict)
                validate_safe_payload(handoff)
                if handoff.get("closure_state") not in CHAT_STATES - {"active"}:
                    add_finding(findings, "error", "handoff_state", "invalid handoff closure state", handoff_path)
                if not handoff.get("next_safe_step"):
                    add_finding(findings, "error", "handoff_next_step", "handoff missing next_safe_step", handoff_path)
            except Exception as exc:
                add_finding(findings, "error", "handoff_json", f"{type(exc).__name__}: {exc}", handoff_path)
    return summarize_doctor(root, findings, inspect_runtime)


def summarize_doctor(root: Path, findings: list[dict[str, Any]], inspect_runtime: bool) -> dict[str, Any]:
    errors = sum(1 for finding in findings if finding["severity"] == "error")
    warnings = sum(1 for finding in findings if finding["severity"] == "warning")
    return {
        "schema": "conversation_workspace_doctor_v1",
        "ok": errors == 0,
        "root": str(root.resolve()),
        "checked_at": iso_now(),
        "runtime_inspected": inspect_runtime,
        "counts": {"error": errors, "warning": warnings},
        "findings": findings,
        "side_effects": {"tmux_executed": False, "worker_executed": False, "external": False, "lifecycle_write": False},
    }


def cmd_doctor(args: argparse.Namespace) -> int:
    report = doctor(args.root, args.inspect_tmux)
    if args.out:
        atomic_write_json(args.out, report)
    return emit(report, 0 if report["ok"] else 1)


def tmux_plan(root: Path) -> dict[str, Any]:
    _, p = require_project(root)
    manifest = load_json(p["tmux"], dict)
    if manifest.get("execute_commands") is not False:
        raise ValueError("tmux manifest is not plan-only")
    windows = manifest.get("windows")
    if not isinstance(windows, list) or not windows:
        raise ValueError("tmux manifest has no windows")
    session = str(manifest.get("session_name") or "")
    validate_id("tmux session", session)
    commands: list[list[str]] = []
    first = windows[0]
    first_workdir = Path(str(first.get("workdir") or root)).expanduser().resolve()
    commands.append(["tmux", "new-session", "-d", "-s", session, "-n", str(first["name"]), "-c", str(first_workdir)])
    for window in windows[1:]:
        workdir = Path(str(window.get("workdir") or root)).expanduser().resolve()
        commands.append(["tmux", "new-window", "-t", session, "-n", str(window["name"]), "-c", str(workdir)])
        panes = window.get("panes") or []
        for _ in panes[1:]:
            commands.append(["tmux", "split-window", "-t", f"{session}:{window['name']}", "-c", str(workdir)])
        if len(panes) > 1:
            commands.append(["tmux", "select-layout", "-t", f"{session}:{window['name']}", "tiled"])
    return {
        "schema": "tmux_plan_v1",
        "project_root": str(root.resolve()),
        "session_name": session,
        "commands": [{"argv": command, "display": shlex.join(command)} for command in commands],
        "executed": False,
        "replay_policy": "layout_only_no_worker_commands",
    }


def cmd_tmux_plan(args: argparse.Namespace) -> int:
    return emit(tmux_plan(args.root))


def tmux_reconcile(root: Path) -> dict[str, Any]:
    """Return a non-executing convergence plan from live tmux to the manifest."""
    full = tmux_plan(root)
    _, p = require_project(root)
    manifest = load_json(p["tmux"], dict)
    session = str(manifest["session_name"])
    actual_windows, inspection_error = inspect_tmux(session)
    desired_windows = {str(window["name"]) for window in manifest.get("windows", [])}
    if inspection_error:
        return {
            "schema": "tmux_reconcile_v1",
            "ok": False,
            "session_name": session,
            "inspection_error": inspection_error,
            "actual_windows": [],
            "desired_windows": sorted(desired_windows),
            "missing_windows": sorted(desired_windows),
            "extra_windows": [],
            "commands": [],
            "executed": False,
            "destructive_commands": False,
        }
    if not actual_windows:
        commands = full["commands"]
        state = "session-absent"
    else:
        commands = []
        state = "session-present"
        manifest_windows = {str(window["name"]): window for window in manifest.get("windows", [])}
        for name in sorted(desired_windows - actual_windows):
            window = manifest_windows[name]
            workdir = str(Path(str(window.get("workdir") or root)).expanduser().resolve())
            command = ["tmux", "new-window", "-t", session, "-n", name, "-c", workdir]
            commands.append({"argv": command, "display": shlex.join(command)})
            panes = window.get("panes") or []
            for _ in panes[1:]:
                split = ["tmux", "split-window", "-t", f"{session}:{name}", "-c", workdir]
                commands.append({"argv": split, "display": shlex.join(split)})
            if len(panes) > 1:
                layout = ["tmux", "select-layout", "-t", f"{session}:{name}", "tiled"]
                commands.append({"argv": layout, "display": shlex.join(layout)})
    return {
        "schema": "tmux_reconcile_v1",
        "ok": True,
        "state": state,
        "session_name": session,
        "actual_windows": sorted(actual_windows),
        "desired_windows": sorted(desired_windows),
        "missing_windows": sorted(desired_windows - actual_windows),
        "extra_windows": sorted(actual_windows - desired_windows),
        "commands": commands,
        "executed": False,
        "destructive_commands": False,
        "note": "extra windows are reported only; reconciliation never removes them",
    }


def cmd_tmux_reconcile(args: argparse.Namespace) -> int:
    result = tmux_reconcile(args.root)
    return emit(result, 0 if result["ok"] else 1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Hermes Conversation Workspace OS local control surface")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init")
    init.add_argument("--root", type=Path, required=True)
    init.add_argument("--project-id", required=True)
    init.add_argument("--display-name")
    init.set_defaults(func=cmd_init)

    event = sub.add_parser("event-append")
    event.add_argument("--root", type=Path, required=True)
    event.add_argument("--event-type", choices=sorted(PUBLIC_EVENT_TYPES), required=True)
    event.add_argument("--payload-file", type=Path, required=True)
    event.add_argument("--actor", default="human-orchestrator")
    event.set_defaults(func=cmd_event_append)

    acquire = sub.add_parser("claim-acquire")
    acquire.add_argument("--root", type=Path, required=True)
    acquire.add_argument("--claim-id", required=True)
    acquire.add_argument("--direction-id", required=True)
    acquire.add_argument("--owner-session", required=True)
    acquire.add_argument("--mode", choices=sorted(CLAIM_MODES), default="write")
    acquire.add_argument("--scope", action="append", default=[])
    acquire.add_argument("--worktree", type=Path)
    acquire.add_argument("--ttl-minutes", type=int, default=240)
    acquire.set_defaults(func=cmd_claim_acquire)

    release = sub.add_parser("claim-release")
    release.add_argument("--root", type=Path, required=True)
    release.add_argument("--claim-id", required=True)
    release.set_defaults(func=cmd_claim_release)

    handoff = sub.add_parser("handoff-add")
    handoff.add_argument("--root", type=Path, required=True)
    handoff.add_argument("--file", type=Path, required=True)
    handoff.set_defaults(func=cmd_handoff_add)

    evidence = sub.add_parser("evidence-add")
    evidence.add_argument("--root", type=Path, required=True)
    evidence.add_argument("--evidence-id", required=True)
    evidence.add_argument("--kind", choices=sorted(EVIDENCE_KINDS), required=True)
    evidence.add_argument("--path", type=Path, required=True)
    evidence.add_argument("--summary", required=True)
    evidence.add_argument("--claim-ref", action="append", default=[])
    evidence.set_defaults(func=cmd_evidence_add)

    doc = sub.add_parser("doctor")
    doc.add_argument("--root", type=Path, required=True)
    doc.add_argument("--inspect-tmux", action="store_true")
    doc.add_argument("--out", type=Path)
    doc.set_defaults(func=cmd_doctor)

    plan = sub.add_parser("tmux-plan")
    plan.add_argument("--root", type=Path, required=True)
    plan.set_defaults(func=cmd_tmux_plan)

    reconcile = sub.add_parser("tmux-reconcile")
    reconcile.add_argument("--root", type=Path, required=True)
    reconcile.set_defaults(func=cmd_tmux_reconcile)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if hasattr(args, "ttl_minutes") and not 1 <= args.ttl_minutes <= 1440:
        return emit({"ok": False, "error": "ttl-minutes must be between 1 and 1440"}, 2)
    try:
        return int(args.func(args))
    except (ValueError, OSError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        return emit({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, 2)


if __name__ == "__main__":
    raise SystemExit(main())
