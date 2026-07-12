#!/usr/bin/env python3
"""Build and safely apply a rebuildable local-brain projection to Memory MCP."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
import time
import uuid
from pathlib import Path, PurePosixPath
from typing import Any

DEFAULT_VAULT = Path.home() / "Documents" / "brain"
CONFIGURED_MEMORY_FILE = Path.home() / ".hermes" / "mcp-memory.json"
CONCEPT_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,79}$")
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
STATUS_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
BRAIN_PREFIXES = ("brain-note:", "brain-concept:")


def frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return ""
    end = text.find("\n---", 4)
    return text[4:end] if end >= 0 else ""


def scalar(fm: str, key: str) -> str:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*([^\n]*)$", fm)
    return match.group(1).strip().strip("\"'") if match else ""


def concepts(fm: str) -> list[str]:
    match = re.search(r"(?m)^concepts:\s*([^\n]*)$", fm)
    if not match:
        return []
    tail, values = match.group(1).strip(), []
    if tail.startswith("[") and tail.endswith("]"):
        values = [item.strip().strip("\"'") for item in tail[1:-1].split(",")]
    elif not tail:
        for line in fm[match.end():].splitlines():
            item = re.match(r"^\s+-\s+(.+?)\s*$", line)
            if not item:
                if line.strip():
                    break
                continue
            values.append(item.group(1).strip().strip("\"'"))
    return list(dict.fromkeys(value for value in values if CONCEPT_RE.fullmatch(value)))[:12]


def build_projection(vault: Path, *, limit: int = 500) -> dict[str, Any]:
    vault = vault.expanduser().resolve()
    paths, entities, relations, concept_ids = sorted(vault.rglob("*.md")), [], [], set()
    selected, note_count = paths[: max(0, limit)], 0
    for path in selected:
        text = path.read_text(encoding="utf-8", errors="replace")
        fm, refs = frontmatter(text), concepts(frontmatter(text))
        if not refs:
            continue
        relative = path.relative_to(vault).as_posix()
        note_id, digest = f"brain-note:{relative}", hashlib.sha256(text.encode()).hexdigest()
        entities.append({"name": note_id, "entityType": "brain_note", "observations": [f"path:{relative}", f"sha256:{digest}", f"status:{scalar(fm, 'status') or 'unspecified'}"]})
        note_count += 1
        for ref in refs:
            concept_id = f"brain-concept:{ref}"
            if concept_id not in concept_ids:
                entities.append({"name": concept_id, "entityType": "brain_concept", "observations": [f"concept:{ref}"]})
                concept_ids.add(concept_id)
            relations.append({"from": note_id, "to": concept_id, "relationType": "has_concept"})
    return {"schema": "local_brain_mcp_projection_v1", "status": "PASS", "authority": "read_only_projection_no_mcp_write", "source_vault": str(vault), "truncated": len(paths) > len(selected), "counts": {"notes": note_count, "concepts": len(concept_ids), "relations": len(relations)}, "entities": entities, "relations": relations}


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _reject_symlink_path(path: Path) -> None:
    current = path.expanduser().absolute()
    while current != current.parent:
        if current.is_symlink():
            raise ValueError(f"symlink path component rejected: {current}")
        current = current.parent


def _validate_projection(projection: dict[str, Any]) -> None:
    if projection.get("schema") != "local_brain_mcp_projection_v1" or projection.get("status") != "PASS" or projection.get("authority") != "read_only_projection_no_mcp_write":
        raise ValueError("validated read-only local-brain projection required")
    entities, relations = projection.get("entities"), projection.get("relations")
    if not isinstance(entities, list) or not isinstance(relations, list):
        raise ValueError("projection graph lists required")
    names: set[str] = set()
    for item in entities:
        if not isinstance(item, dict) or set(item) != {"name", "entityType", "observations"} or not isinstance(item["observations"], list) or not all(isinstance(value, str) for value in item["observations"]):
            raise ValueError("invalid projection entity shape")
        name, kind, obs = item["name"], item["entityType"], item["observations"]
        if name in names:
            raise ValueError("duplicate projection entity")
        names.add(name)
        if kind == "brain_note":
            relative = name.removeprefix("brain-note:") if isinstance(name, str) else ""
            parts = PurePosixPath(relative).parts
            safe_path = bool(relative) and not relative.startswith("/") and "\\" not in relative and all(part not in {"", ".", ".."} for part in parts) and relative.endswith(".md")
            status = obs[2][7:] if len(obs) == 3 and isinstance(obs[2], str) and obs[2].startswith("status:") else ""
            valid = name == f"brain-note:{relative}" and safe_path and len(obs) == 3 and obs[0] == f"path:{relative}" and isinstance(obs[1], str) and obs[1].startswith("sha256:") and SHA_RE.fullmatch(obs[1][7:]) and STATUS_RE.fullmatch(status)
        elif kind == "brain_concept":
            ref = name.removeprefix("brain-concept:") if isinstance(name, str) else ""
            valid = name == f"brain-concept:{ref}" and CONCEPT_RE.fullmatch(ref) and obs == [f"concept:{ref}"]
        else:
            valid = False
        if not valid:
            raise ValueError("invalid or authority-bearing projection entity")
    for item in relations:
        if not isinstance(item, dict) or set(item) != {"from", "to", "relationType"} or item["relationType"] != "has_concept" or not str(item["from"]).startswith("brain-note:") or not str(item["to"]).startswith("brain-concept:") or item["from"] not in names or item["to"] not in names:
            raise ValueError("invalid projection relation")


def _load_records(data: bytes) -> list[dict[str, Any]]:
    if not data.strip():
        return []
    try:
        decoded = json.loads(data)
        if isinstance(decoded, dict) and decoded.get("type") in {"entity", "relation"}:
            records = [decoded]
        elif isinstance(decoded, dict):
            records = ([{"type": "entity", **item} for item in decoded.get("entities", [])] + [{"type": "relation", **item} for item in decoded.get("relations", [])])
        else:
            records = []
    except json.JSONDecodeError:
        try:
            records = [json.loads(line) for line in data.decode().splitlines() if line.strip()]
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("existing MCP memory is invalid JSONL") from exc
    if not all(isinstance(item, dict) and item.get("type") in {"entity", "relation"} for item in records):
        raise ValueError("existing MCP memory graph schema is invalid")
    return records


def _atomic_write(path: Path, data: bytes) -> None:
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data); handle.flush(); os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def apply_projection(projection: dict[str, Any], memory_file: Path, *, backup_dir: Path, expected_target: Path = CONFIGURED_MEMORY_FILE) -> dict[str, Any]:
    _validate_projection(projection)
    memory_file, expected_target = memory_file.expanduser().absolute(), expected_target.expanduser().absolute()
    _reject_symlink_path(memory_file)
    if memory_file != expected_target:
        raise ValueError("memory target does not match exact configured target")
    before = memory_file.read_bytes() if memory_file.exists() else b""
    records = _load_records(before)
    foreign = [item for item in records if not any(str(item.get(key, "")).startswith(BRAIN_PREFIXES) for key in ("name", "from", "to"))]
    projected = ([{"type": "entity", **item} for item in projection["entities"]] + [{"type": "relation", **item} for item in projection["relations"]])
    output = foreign + projected
    after = ("\n".join(json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")) for item in output) + ("\n" if output else "")).encode()
    before_hash, after_hash = _digest(before), _digest(after)
    counts = {"entities": sum(x["type"] == "entity" for x in output), "relations": sum(x["type"] == "relation" for x in output)}
    if memory_file.exists() and before_hash == after_hash:
        return {"schema": "local_brain_mcp_apply_receipt_v1", "status": "UNCHANGED", "authority": "local_mcp_store_write_only_no_task_authority", "target": str(memory_file), "before_sha256": before_hash, "after_sha256": after_hash, "backup_path": "", "rollback": {"action": "none", "guard_sha256": after_hash}, "readback_counts": counts}
    backup_dir = backup_dir.expanduser().absolute(); _reject_symlink_path(backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)
    unique = f"{time.time_ns()}-{uuid.uuid4().hex}"
    if memory_file.exists():
        backup = backup_dir / f"{memory_file.name}.{unique}.{before_hash[:12]}.bak"
        shutil.copy2(memory_file, backup)
        if _digest(backup.read_bytes()) != before_hash:
            raise RuntimeError("backup hash verification failed")
        rollback = {"action": "restore_backup_if_hash_matches", "backup_path": str(backup), "backup_sha256": before_hash, "guard_sha256": after_hash}
    else:
        backup = backup_dir / f"{memory_file.name}.{unique}.absent.json"
        backup.write_text(json.dumps({"target": str(memory_file), "state": "absent", "guard_sha256": after_hash}) + "\n", encoding="utf-8")
        marker_hash = _digest(backup.read_bytes())
        rollback = {"action": "delete_created_target_if_hash_matches", "backup_path": str(backup), "backup_sha256": marker_hash, "guard_sha256": after_hash}
    memory_file.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(memory_file, after)
    if _digest(memory_file.read_bytes()) != after_hash:
        raise RuntimeError("MCP memory readback hash mismatch")
    return {"schema": "local_brain_mcp_apply_receipt_v1", "status": "APPLIED", "authority": "local_mcp_store_write_only_no_task_authority", "target": str(memory_file), "before_sha256": before_hash, "after_sha256": after_hash, "backup_path": str(backup), "rollback": rollback, "readback_counts": counts}


def rollback_apply(receipt: dict[str, Any], *, expected_target: Path = CONFIGURED_MEMORY_FILE) -> dict[str, Any]:
    target = Path(receipt.get("target", "")).expanduser().absolute(); expected = expected_target.expanduser().absolute()
    _reject_symlink_path(target)
    if target != expected or _digest(target.read_bytes()) != receipt.get("after_sha256"):
        raise ValueError("rollback target or guard hash mismatch")
    rollback = receipt.get("rollback") or {}; backup = Path(rollback.get("backup_path", ""))
    if rollback.get("action") == "restore_backup_if_hash_matches":
        data = backup.read_bytes()
        if _digest(data) != rollback.get("backup_sha256"):
            raise ValueError("rollback backup hash mismatch")
        _atomic_write(target, data); status = "RESTORED"
    elif rollback.get("action") == "delete_created_target_if_hash_matches":
        if not backup.is_file() or _digest(backup.read_bytes()) != rollback.get("backup_sha256"):
            raise ValueError("absent-state rollback artifact missing or hash mismatch")
        target.unlink(); status = "DELETED_CREATED_TARGET"
    else:
        raise ValueError("receipt is not rollbackable")
    return {"schema": "local_brain_mcp_rollback_receipt_v1", "status": status, "target": str(target)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vault", type=Path, default=DEFAULT_VAULT)
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--memory-file", type=Path, default=CONFIGURED_MEMORY_FILE)
    parser.add_argument("--backup-dir", type=Path, default=Path.home() / ".hermes" / "backups" / "mcp-memory")
    args = parser.parse_args()
    result = build_projection(args.vault, limit=args.limit)
    if args.apply:
        applied = apply_projection(result, args.memory_file, backup_dir=args.backup_dir)
        result = {"projection": {key: result[key] for key in ("schema", "status", "counts", "truncated")}, "apply": applied}
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else json.dumps(result.get("counts") or result["apply"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
