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
import unicodedata
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
INTERNAL_EVENT_TYPES = {"project.initialized", "claim.acquired", "claim.released", "claim.expired", "handoff.recorded", "evidence.recorded"}
SECRET_KEYS = {
    "password", "passwd", "secret", "api_key", "apikey", "access_key", "private_key",
    "credential", "credentials", "card_number", "authorization", "bearer_token",
    "auth_token", "access_token", "refresh_token", "token",
}
AUTHORITY_SMUGGLING_KEYS = {
    "mark_done", "external_write", "write_through", "write_through_enabled",
    "send_executed", "deploy", "push", "task_status", "lifecycle_target",
    "command", "commands",
}
EXPECTED_AUTHORITY_FLAGS = {
    "external_dispatch", "taskpool_lifecycle_write", "mission_lifecycle_write",
    "tmux_execution", "worker_execution", "deploy_push", "destructive_operations",
    "credential_entry",
}
EXTERNAL_AUTHORITY_SMUGGLING_KEYS = AUTHORITY_SMUGGLING_KEYS | EXPECTED_AUTHORITY_FLAGS | {
    "execute_commands", "status", "lifecycle_state", "completed_at", "approved",
}
SECRET_KEY_FRAGMENTS = {"secret", "token", "password", "passwd", "credential", "private_key", "api_key", "access_key"}
AUTHORITY_KEY_FRAGMENTS = {
    "external_dispatch", "external_write", "write_through", "taskpool_lifecycle",
    "mission_lifecycle", "tmux_execution", "worker_execution", "deploy_push",
    "destructive_operation", "credential_entry", "mark_done", "send_executed",
    "execute_command", "lifecycle_target", "task_status", "approved",
}
HANDOFF_ALLOWED_KEYS = {
    "handoff_id", "direction_id", "source_session_id", "claim_id", "objective",
    "verified_current_state", "completed", "changed_files", "decisions", "blockers",
    "next_safe_step", "forbidden_assumptions", "worktree", "closure_state", "recorded_at",
}
EXPECTED_STATE_DOMAINS = {
    "direction": DIRECTION_STATES,
    "task": TASK_STATES,
    "worker_runtime": RUNTIME_STATES,
    "chat_session": CHAT_STATES,
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


def normalize_scope(value: str) -> str:
    normalized = unicodedata.normalize("NFC", value.strip().replace("\\", "/"))
    if not normalized or normalized.startswith("/") or any(unicodedata.category(char).startswith("C") for char in normalized):
        raise ValueError(f"scope must be a non-empty project-relative pattern: {value!r}")
    raw_parts = normalized.split("/")
    if any(part == ".." for part in raw_parts):
        raise ValueError(f"scope cannot contain parent traversal: {value!r}")
    parts = [part for part in raw_parts if part not in {"", "."}]
    if not parts:
        raise ValueError(f"scope must identify a project-relative pattern: {value!r}")
    return "/".join(parts)


def validate_scope(value: str) -> None:
    normalize_scope(value)


def normalize_payload_key(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value).strip())
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", text)
    return re.sub(r"[^a-z0-9]+", "_", text.casefold()).strip("_")


def validate_safe_payload(
    value: Any,
    trail: tuple[str, ...] = (),
    reject_external_authority: bool = False,
) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = normalize_payload_key(key)
            canonical_closed_flag = bool(trail and trail[-1] == "authority" and normalized in EXPECTED_AUTHORITY_FLAGS and item is False)
            if not canonical_closed_flag and (normalized in SECRET_KEYS or any(fragment in normalized for fragment in SECRET_KEY_FRAGMENTS)):
                raise ValueError(f"secret-like field rejected: {'.'.join(trail + (str(key),))}")
            forbidden_authority = EXTERNAL_AUTHORITY_SMUGGLING_KEYS if reject_external_authority else AUTHORITY_SMUGGLING_KEYS
            if normalized in forbidden_authority or (
                reject_external_authority and any(fragment in normalized for fragment in AUTHORITY_KEY_FRAGMENTS)
            ):
                raise ValueError(f"authority-smuggling field rejected: {'.'.join(trail + (str(key),))}")
            validate_safe_payload(item, trail + (str(key),), reject_external_authority)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            validate_safe_payload(item, trail + (str(index),), reject_external_authority)


def validate_event_schema(event: dict[str, Any]) -> None:
    required = {"schema_version", "event_id", "event_type", "occurred_at", "actor", "payload"}
    if set(event) != required or event.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("event must contain the exact canonical field set and schema version")
    event_id = event.get("event_id")
    if not isinstance(event_id, str) or not event_id.startswith("evt-"):
        raise ValueError("event_id must be a non-empty canonical event id")
    event_type = event.get("event_type")
    if event_type not in PUBLIC_EVENT_TYPES | INTERNAL_EVENT_TYPES:
        raise ValueError(f"unsupported event_type: {event_type!r}")
    if not isinstance(event.get("actor"), str) or not event["actor"].strip():
        raise ValueError("event actor must be a non-empty string")
    occurred_at = event.get("occurred_at")
    if not isinstance(occurred_at, str):
        raise ValueError("event occurred_at must be a timestamp string")
    parse_time(occurred_at)
    if not isinstance(event.get("payload"), dict):
        raise ValueError("event payload must be an object")
    payload = event["payload"]
    validate_safe_payload(payload, reject_external_authority=True)
    if event_type == "project.initialized":
        if set(payload) != {"project_id", "display_name"}:
            raise ValueError("project.initialized payload schema is invalid")
        validate_id("event project id", payload.get("project_id"))
        if not isinstance(payload.get("display_name"), str) or not payload["display_name"].strip():
            raise ValueError("project.initialized display_name must be non-empty")
    elif event_type == "claim.acquired":
        if set(payload) != {"claim_id", "direction_id", "mode", "scope"}:
            raise ValueError("claim.acquired payload schema is invalid")
        validate_id("event claim id", payload.get("claim_id"))
        validate_id("event direction id", payload.get("direction_id"))
        if payload.get("mode") not in CLAIM_MODES:
            raise ValueError("claim.acquired mode is invalid")
        scopes = payload.get("scope")
        if not isinstance(scopes, list) or not scopes or any(not isinstance(scope, str) or normalize_scope(scope) != scope for scope in scopes):
            raise ValueError("claim.acquired scope is invalid")
    elif event_type in {"claim.released", "claim.expired"}:
        if set(payload) != {"claim_id"}:
            raise ValueError(f"{event_type} payload schema is invalid")
        validate_id("event claim id", payload.get("claim_id"))
    elif event_type == "handoff.recorded":
        if set(payload) != {"handoff_id", "direction_id", "source_session_id"}:
            raise ValueError("handoff.recorded payload schema is invalid")
        for field in ("handoff_id", "direction_id", "source_session_id"):
            validate_id(f"event {field}", payload.get(field))
    elif event_type == "evidence.recorded":
        if set(payload) != {"evidence_id", "kind", "claim_refs"}:
            raise ValueError("evidence.recorded payload schema is invalid")
        validate_id("event evidence id", payload.get("evidence_id"))
        if payload.get("kind") not in EVIDENCE_KINDS:
            raise ValueError("evidence.recorded kind is invalid")
        refs = payload.get("claim_refs")
        if not isinstance(refs, list) or any(not isinstance(ref, str) or not ref.strip() for ref in refs):
            raise ValueError("evidence.recorded claim_refs is invalid")
    elif event_type in PUBLIC_EVENT_TYPES:
        schemas = {
            "note.recorded": ("note",),
            "decision.recorded": ("decision",),
            "session.observed": ("session_id", "observation"),
            "runtime.observed": ("runtime_id", "observation"),
        }
        fields = schemas[event_type]
        if set(payload) != set(fields) or any(not isinstance(payload[field], str) or not payload[field].strip() for field in fields):
            raise ValueError(f"{event_type} payload schema is invalid")


def validate_event_history(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    ids: set[str] = set()
    if not path.exists():
        return events
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
            if not isinstance(event, dict):
                raise ValueError("event must be an object")
            validate_event_schema(event)
        except Exception as exc:
            raise ValueError(f"invalid event history at line {line_number}: {exc}") from exc
        if event["event_id"] in ids:
            raise ValueError(f"duplicate event id in history: {event['event_id']}")
        ids.add(event["event_id"])
        events.append(event)
    return events


def validate_evidence_record(record: dict[str, Any]) -> None:
    required = {"schema_version", "evidence_id", "kind", "path", "sha256", "summary", "claim_refs", "recorded_at"}
    if set(record) != required or record.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("evidence record must contain the exact canonical field set and schema version")
    evidence_id = record.get("evidence_id")
    if not isinstance(evidence_id, str):
        raise ValueError("evidence id must be a string")
    validate_id("evidence id", evidence_id)
    if record.get("kind") not in EVIDENCE_KINDS:
        raise ValueError("evidence kind is invalid")
    if not isinstance(record.get("path"), str) or not Path(record["path"]).is_absolute():
        raise ValueError("evidence path must be absolute")
    if not isinstance(record.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", record["sha256"]):
        raise ValueError("evidence sha256 is invalid")
    if not isinstance(record.get("summary"), str) or not record["summary"].strip():
        raise ValueError("evidence summary must be non-empty")
    refs = record.get("claim_refs")
    if not isinstance(refs, list) or any(not isinstance(ref, str) or not ref.strip() for ref in refs):
        raise ValueError("evidence claim_refs is invalid")
    if not isinstance(record.get("recorded_at"), str):
        raise ValueError("evidence recorded_at must be a timestamp string")
    parse_time(record["recorded_at"])
    validate_safe_payload(record)


def validate_evidence_index(records: list[Any]) -> set[str]:
    ids: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("evidence record must be object")
        validate_evidence_record(record)
        if record["evidence_id"] in ids:
            raise ValueError(f"duplicate evidence id: {record['evidence_id']}")
        artifact = Path(record["path"]).expanduser()
        if not artifact.is_file():
            raise ValueError(f"evidence artifact missing: {record['evidence_id']}")
        if sha256_file(artifact) != record["sha256"]:
            raise ValueError(f"evidence hash mismatch: {record['evidence_id']}")
        ids.add(record["evidence_id"])
    return ids


def validate_claim_schema(claim: dict[str, Any], project_id: str) -> None:
    required = {"schema_version", "claim_id", "project_id", "direction_id", "owner_type", "owner_session", "mode", "scope", "worktree", "status", "created_at", "expires_at"}
    allowed = required | {"released_at"}
    if not required.issubset(claim) or not set(claim).issubset(allowed) or claim.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("claim must contain the canonical field set and schema version")
    for field in ("claim_id", "direction_id", "owner_session"):
        value = claim.get(field)
        if not isinstance(value, str):
            raise ValueError(f"claim {field} must be a string")
        validate_id(f"claim {field}", value)
    if claim.get("project_id") != project_id or claim.get("owner_type") != "hermes-session":
        raise ValueError("claim project_id/owner_type does not match the canonical project")
    if claim.get("mode") not in CLAIM_MODES or claim.get("status") not in CLAIM_STATES:
        raise ValueError("claim mode/status is invalid")
    scopes = claim.get("scope")
    if not isinstance(scopes, list) or not scopes or any(not isinstance(scope, str) or normalize_scope(scope) != scope for scope in scopes):
        raise ValueError("claim scope must be a non-empty list of canonical strings")
    if not isinstance(claim.get("created_at"), str) or not isinstance(claim.get("expires_at"), str):
        raise ValueError("claim created_at/expires_at must be timestamp strings")
    created = parse_time(claim["created_at"])
    expires = parse_time(claim["expires_at"])
    if expires <= created:
        raise ValueError("claim expires_at must be after created_at")
    worktree = claim.get("worktree")
    if claim.get("mode") == "write" and (not isinstance(worktree, str) or not Path(worktree).is_absolute()):
        raise ValueError("write claim worktree must be an absolute path")
    if claim.get("mode") != "write" and worktree is not None and not isinstance(worktree, str):
        raise ValueError("claim worktree must be null or a string")
    if "released_at" in claim:
        if not isinstance(claim["released_at"], str):
            raise ValueError("claim released_at must be a timestamp string")
        released = parse_time(claim["released_at"])
        if released < created or released > expires:
            raise ValueError("claim released_at must be between created_at and expires_at")
    if claim.get("status") == "released" and "released_at" not in claim:
        raise ValueError("released claim requires released_at")
    if claim.get("status") != "released" and "released_at" in claim:
        raise ValueError("only released claims may contain released_at")


def validate_tmux_manifest(manifest: dict[str, Any], project: dict[str, Any]) -> None:
    if set(manifest) != {"schema_version", "project_id", "session_name", "execute_commands", "windows"}:
        raise ValueError("tmux manifest must contain the exact canonical field set")
    if manifest.get("schema_version") != SCHEMA_VERSION or manifest.get("project_id") != project.get("project_id"):
        raise ValueError("tmux manifest identity does not match the canonical project")
    if manifest.get("session_name") != project.get("tmux_session") or manifest.get("execute_commands") is not False:
        raise ValueError("tmux manifest session/execute policy is invalid")
    windows = manifest.get("windows")
    if not isinstance(windows, list) or not windows:
        raise ValueError("tmux manifest windows must be a non-empty list")
    names: set[str] = set()
    for window in windows:
        if not isinstance(window, dict) or set(window) != {"name", "direction_id", "claim_id", "workdir", "panes"}:
            raise ValueError("tmux window must contain the exact canonical field set")
        name = window.get("name")
        if not isinstance(name, str) or not SAFE_ID.fullmatch(name) or name in names:
            raise ValueError("tmux window name must be unique and safe")
        names.add(name)
        if not isinstance(window.get("workdir"), str) or not Path(window["workdir"]).is_absolute():
            raise ValueError("tmux window workdir must be an absolute path")
        direction_id, claim_id = window.get("direction_id"), window.get("claim_id")
        if (direction_id is None) != (claim_id is None):
            raise ValueError("tmux window direction_id and claim_id must both be null or strings")
        for label, value in (("direction_id", direction_id), ("claim_id", claim_id)):
            if value is not None:
                if not isinstance(value, str):
                    raise ValueError(f"tmux window {label} must be a string")
                validate_id(f"tmux window {label}", value)
        panes = window.get("panes")
        if not isinstance(panes, list) or not panes:
            raise ValueError("tmux window panes must be a non-empty list")
        for pane in panes:
            if not isinstance(pane, dict) or set(pane) != {"role"} or pane.get("role") not in {"control", "executor", "verify"}:
                raise ValueError("tmux pane must contain only a supported role")


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
    validate_event_schema(event)
    with p["event_lock"].open("a+", encoding="utf-8") as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        validate_event_history(p["events"])
        with p["events"].open("a", encoding="utf-8") as events_handle:
            events_handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
            events_handle.flush()
            os.fsync(events_handle.fileno())
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
    return event


def scope_static_prefix(value: str) -> tuple[str, bool]:
    clean = normalize_scope(value).casefold()
    wildcard = len(clean)
    for marker in ("*", "?", "["):
        pos = clean.find(marker)
        if pos >= 0:
            wildcard = min(wildcard, pos)
    return clean[:wildcard], wildcard < len(clean)


def scopes_overlap(left: str, right: str) -> bool:
    if left.strip() in {"*", "**", "**/*"} or right.strip() in {"*", "**", "**/*"}:
        return True
    a, a_glob = scope_static_prefix(left)
    b, b_glob = scope_static_prefix(right)
    if not a or not b:
        return True
    if not a_glob and not b_glob:
        return a == b
    return a.startswith(b) or b.startswith(a)


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
    p = paths(root)
    with exclusive_file_lock(p["state_lock"]):
        validate_event_history(p["events"])
        if p["evidence"].exists():
            validate_evidence_index(load_json(p["evidence"], list))
        if p["project"].is_file():
            existing_project = load_json(p["project"], dict)
            if existing_project.get("project_id") != project_id:
                raise ValueError(
                    f"project id mismatch: existing={existing_project.get('project_id')!r} requested={project_id!r}"
                )
        for dirname in ("00-spec", "01-directions", "02-ledger", "03-evidence/artifacts", "04-handoffs/sessions", "04-handoffs/workers", "05-runtime/receipts", "06-status"):
            (root / dirname).mkdir(parents=True, exist_ok=True)
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
    validate_safe_payload(payload, reject_external_authority=True)
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
    normalized_scopes = [normalize_scope(scope) for scope in args.scope]
    if not 1 <= args.ttl_minutes <= 1440:
        raise ValueError("ttl-minutes must be between 1 and 1440")
    with exclusive_file_lock(p["state_lock"]):
        validate_event_history(p["events"])
        claims = load_json(p["claims"], list)
        if any(not isinstance(item, dict) for item in claims):
            raise ValueError("active claims must contain only objects")
        for item in claims:
            validate_claim_schema(item, project["project_id"])
        if any(c.get("claim_id") == args.claim_id for c in claims if isinstance(c, dict)):
            raise ValueError(f"claim id already exists: {args.claim_id}")
        active = [c for c in claims if isinstance(c, dict) and claim_is_active(c)]
        for current in active:
            if args.mode == "write" and current.get("mode") == "write":
                if current.get("direction_id") == args.direction_id:
                    raise ValueError(f"active write claim already owns direction: {args.direction_id}")
                for left in normalized_scopes:
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
            "scope": normalized_scopes,
            "worktree": str(args.worktree.resolve()) if args.worktree else None,
            "status": "active",
            "created_at": created_at.isoformat().replace("+00:00", "Z"),
            "expires_at": (created_at + timedelta(minutes=args.ttl_minutes)).isoformat().replace("+00:00", "Z"),
        }
        validate_safe_payload(claim)
        validate_claim_schema(claim, project["project_id"])
        manifest = load_json(p["tmux"], dict)
        validate_tmux_manifest(manifest, project)
        windows = manifest["windows"]
        window = {
            "name": next_window_name(manifest, args.direction_id),
            "direction_id": args.direction_id,
            "claim_id": args.claim_id,
            "workdir": claim["worktree"] or str(args.root.resolve()),
            "panes": [{"role": "executor"}, {"role": "verify"}],
        }
        claims.append(claim)
        windows.append(window)
        atomic_write_json(p["claims"], claims)
        atomic_write_json(p["tmux"], manifest)
        event = append_event(args.root, "claim.acquired", {"claim_id": args.claim_id, "direction_id": args.direction_id, "mode": args.mode, "scope": normalized_scopes})
    return emit({"ok": True, "claim": claim, "tmux_window": window, "event_id": event["event_id"], "tmux_executed": False})


def cmd_claim_release(args: argparse.Namespace) -> int:
    project, p = require_project(args.root)
    with exclusive_file_lock(p["state_lock"]):
        validate_event_history(p["events"])
        claims = load_json(p["claims"], list)
        for claim in claims:
            if not isinstance(claim, dict):
                raise ValueError("active claims must contain only objects")
            validate_claim_schema(claim, project["project_id"])
        found = None
        for claim in claims:
            if isinstance(claim, dict) and claim.get("claim_id") == args.claim_id:
                found = claim
                break
        if found is None:
            raise ValueError(f"unknown claim: {args.claim_id}")
        if found.get("status") in {"released", "expired"}:
            return emit({"ok": True, "idempotent": True, "claim": found})
        if found.get("status") != "active":
            raise ValueError(f"claim cannot be released from state: {found.get('status')}")
        manifest = load_json(p["tmux"], dict)
        validate_tmux_manifest(manifest, project)
        windows = manifest["windows"]
        now = utc_now()
        if now > parse_time(found["expires_at"]):
            found["status"] = "expired"
            event_type = "claim.expired"
        else:
            found["status"] = "released"
            found["released_at"] = now.isoformat().replace("+00:00", "Z")
            event_type = "claim.released"
        validate_claim_schema(found, project["project_id"])
        manifest["windows"] = [w for w in windows if w.get("claim_id") != args.claim_id]
        atomic_write_json(p["claims"], claims)
        atomic_write_json(p["tmux"], manifest)
        event = append_event(args.root, event_type, {"claim_id": args.claim_id})
    return emit({"ok": True, "claim": found, "event_id": event["event_id"], "tmux_executed": False})


def require_nonempty_string(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"handoff {field} must be a non-empty string")
    return value


def validate_string_list(payload: dict[str, Any], field: str, required: bool = False, allow_empty: bool = True) -> None:
    if field not in payload and not required:
        return
    value = payload.get(field)
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"handoff {field} must be a list of non-empty strings")
    if not allow_empty and not value:
        raise ValueError(f"handoff {field} must not be empty")


def validate_handoff_schema(handoff: dict[str, Any]) -> None:
    required = {"handoff_id", "direction_id", "source_session_id", "objective", "verified_current_state", "next_safe_step", "closure_state"}
    missing = sorted(required - set(handoff))
    if missing:
        raise ValueError(f"handoff missing fields: {', '.join(missing)}")
    unknown = sorted(set(handoff) - HANDOFF_ALLOWED_KEYS)
    if unknown:
        raise ValueError(f"handoff contains unsupported fields: {', '.join(unknown)}")
    handoff_id = require_nonempty_string(handoff, "handoff_id")
    direction_id = require_nonempty_string(handoff, "direction_id")
    source_session_id = require_nonempty_string(handoff, "source_session_id")
    validate_id("handoff id", handoff_id)
    validate_id("direction id", direction_id)
    validate_id("source session id", source_session_id)
    require_nonempty_string(handoff, "objective")
    require_nonempty_string(handoff, "next_safe_step")
    validate_string_list(handoff, "verified_current_state", required=True, allow_empty=False)
    for field in ("changed_files", "decisions", "blockers", "forbidden_assumptions"):
        validate_string_list(handoff, field)
    closure_state = handoff["closure_state"]
    if not isinstance(closure_state, str) or closure_state not in CHAT_STATES - {"active"}:
        raise ValueError("handoff closure_state must be handoff-ready, archived, or stale")
    claim_id = handoff.get("claim_id")
    if claim_id is not None:
        if not isinstance(claim_id, str):
            raise ValueError("handoff claim_id must be a string or null")
        validate_id("claim id", claim_id)
    completed = handoff.get("completed", [])
    if not isinstance(completed, list):
        raise ValueError("handoff completed must be a list")
    for index, item in enumerate(completed):
        if not isinstance(item, dict) or set(item) != {"summary", "evidence_refs"}:
            raise ValueError(f"handoff completed[{index}] must contain only summary and evidence_refs")
        require_nonempty_string(item, "summary")
        validate_string_list(item, "evidence_refs", required=True, allow_empty=False)
    worktree = handoff.get("worktree")
    if worktree is not None:
        if not isinstance(worktree, dict) or set(worktree) != {"path", "branch"}:
            raise ValueError("handoff worktree must be null or contain only path and branch")
        worktree_path = require_nonempty_string(worktree, "path")
        if not Path(worktree_path).expanduser().is_absolute():
            raise ValueError("handoff worktree path must be absolute")
        require_nonempty_string(worktree, "branch")
    if "recorded_at" in handoff:
        parse_time(require_nonempty_string(handoff, "recorded_at"))


def cmd_handoff_add(args: argparse.Namespace) -> int:
    _, p = require_project(args.root)
    handoff = load_json(args.file, dict)
    validate_safe_payload(handoff, reject_external_authority=True)
    validate_handoff_schema(handoff)
    with exclusive_file_lock(p["state_lock"]):
        validate_event_history(p["events"])
        evidence_ids = validate_evidence_index(load_json(p["evidence"], list))
        for item in handoff.get("completed", []):
            unknown = sorted(set(item["evidence_refs"]) - evidence_ids)
            if unknown:
                raise ValueError(f"handoff completed references unknown evidence: {unknown}")
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
        validate_event_history(p["events"])
        evidence = load_json(p["evidence"], list)
        validate_evidence_index(evidence)
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
        validate_evidence_record(record)
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
        if (
            not isinstance(authority, dict)
            or set(authority) != EXPECTED_AUTHORITY_FLAGS
            or any(authority.get(flag) is not False for flag in EXPECTED_AUTHORITY_FLAGS)
        ):
            add_finding(findings, "error", "authority_closed", "all required project authority flags must be present and explicitly false", p["project"])
        domains = project.get("state_domains")
        domains_valid = isinstance(domains, dict) and set(domains) == set(EXPECTED_STATE_DOMAINS)
        if domains_valid:
            for name, expected_values in EXPECTED_STATE_DOMAINS.items():
                actual = domains.get(name)
                if not isinstance(actual, list) or set(actual) != expected_values or len(actual) != len(expected_values):
                    domains_valid = False
                    break
        if not domains_valid:
            add_finding(findings, "error", "state_domains", "state domains must be complete, distinct, and contain every allowed state", p["project"])
    except Exception as exc:
        add_finding(findings, "error", "project_json", f"{type(exc).__name__}: {exc}", p["project"])
        project = {}
    event_ids: set[str] = set()
    try:
        for line_number, line in enumerate(p["events"].read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            event = json.loads(line)
            try:
                validate_event_schema(event)
            except (ValueError, TypeError, AttributeError) as exc:
                add_finding(findings, "error", "event_schema", f"line {line_number}: {exc}", p["events"])
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
            try:
                validate_evidence_record(record)
            except (ValueError, TypeError, AttributeError) as exc:
                add_finding(findings, "error", "evidence_schema", str(exc), p["evidence"])
                continue
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
            try:
                validate_safe_payload(claim)
                validate_claim_schema(claim, str(project.get("project_id") or ""))
            except (ValueError, TypeError, AttributeError) as exc:
                add_finding(findings, "error", "claim_schema", str(exc), p["claims"])
                if claim.get("status") == "active":
                    try:
                        if parse_time(str(claim.get("expires_at"))) <= utc_now():
                            add_finding(findings, "error", "claim_expired", f"active claim expired: {claim.get('claim_id')}", p["claims"])
                    except Exception:
                        pass
                continue
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
        try:
            validate_tmux_manifest(manifest, project)
        except (ValueError, TypeError, AttributeError) as exc:
            add_finding(findings, "error", "tmux_schema", str(exc), p["tmux"])
        try:
            validate_safe_payload(manifest)
        except ValueError as exc:
            add_finding(findings, "error", "tmux_payload_safety", str(exc), p["tmux"])
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
                validate_safe_payload(handoff, reject_external_authority=True)
                validate_handoff_schema(handoff)
                for item in handoff.get("completed", []):
                    unknown = sorted(set(item["evidence_refs"]) - evidence_ids)
                    if unknown:
                        raise ValueError(f"handoff completed references unknown evidence: {unknown}")
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


def resolve_doctor_output(root: Path, requested: Path) -> Path:
    status_path = root.resolve() / "06-status"
    if status_path.is_symlink() or not status_path.is_dir():
        raise ValueError("06-status must be a real directory inside the project root")
    status_root = status_path.resolve()
    candidate = requested if requested.is_absolute() else status_root / requested
    target = candidate.resolve()
    if target == status_root or status_root not in target.parents:
        raise ValueError(f"doctor --out must stay inside {status_root}")
    return target


def cmd_doctor(args: argparse.Namespace) -> int:
    report = doctor(args.root, args.inspect_tmux)
    if args.out:
        atomic_write_json(resolve_doctor_output(args.root, args.out), report)
    return emit(report, 0 if report["ok"] else 1)


def tmux_plan(root: Path) -> dict[str, Any]:
    project, p = require_project(root)
    manifest = load_json(p["tmux"], dict)
    validate_tmux_manifest(manifest, project)
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
    project, p = require_project(root)
    manifest = load_json(p["tmux"], dict)
    validate_tmux_manifest(manifest, project)
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
    except (ValueError, TypeError, AttributeError, OSError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        return emit({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, 2)


if __name__ == "__main__":
    raise SystemExit(main())
