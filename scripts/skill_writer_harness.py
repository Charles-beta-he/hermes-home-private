#!/usr/bin/env python3
"""Digest-bound canonical skill writer.

Default-on, narrow skill writer for Hermes self-architecture work. It can create
new skills only under an allowlisted category directory and can roll back the
exact created skill by request digest. It never edits existing skills, memory,
cron, provider config, plugins, or external systems.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import time
from pathlib import Path
from typing import Any

HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))).expanduser()
SKILLS_BASE = HERMES_HOME / "skills"
DEFAULT_CATEGORY = "agent-generated"
DISABLE_VALUES = {"0", "false", "off", "no", "disabled"}
ENABLE_VALUES = {"1", "true", "yes", "on"}
ELEVATED_ROLES = {"admin", "operator", "system"}
AUTHORITY = "create_new_skill_only_no_overwrite_no_memory_no_cron_no_provider_no_plugin"
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,62}[a-z0-9]$")
CATEGORY_RE = re.compile(r"^[a-z0-9][a-z0-9_/-]{0,96}[a-z0-9]$")


def utc_ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def writer_mode(default: str = "apply") -> str:
    raw = os.environ.get("HERMES_SKILL_WRITER_MODE") or os.environ.get("HERMES_CANONICAL_SKILL_WRITER") or default
    mode = str(raw or "").strip().lower()
    if mode in DISABLE_VALUES:
        return "off"
    if mode in ENABLE_VALUES:
        return "apply"
    if mode not in {"off", "shadow", "apply"}:
        return "apply"
    return mode


def validate_name(name: str) -> str:
    name = str(name or "").strip().lower()
    if not NAME_RE.match(name):
        raise ValueError("invalid_skill_name")
    return name


def validate_category(category: str | None) -> str:
    category = str(category or DEFAULT_CATEGORY).strip().lower().strip("/")
    if ".." in category or category.startswith("/") or not CATEGORY_RE.match(category):
        raise ValueError("invalid_skill_category")
    return category


def validate_content(content: str) -> str:
    content = str(content or "")
    if len(content) < 80:
        raise ValueError("skill_content_too_short")
    if not content.startswith("---\n"):
        raise ValueError("skill_frontmatter_missing")
    end = content.find("\n---", 4)
    if end < 0:
        raise ValueError("skill_frontmatter_unclosed")
    frontmatter = content[4:end]
    required = ["name:", "description:"]
    missing = [key for key in required if key not in frontmatter]
    if missing:
        raise ValueError("skill_frontmatter_missing_required_fields:" + ",".join(missing))
    if "```" not in content and "##" not in content:
        raise ValueError("skill_body_too_sparse")
    return content


def skill_dir(name: str, category: str, *, base_dir: str | Path | None = None) -> Path:
    base = Path(base_dir).expanduser() if base_dir else SKILLS_BASE
    base = base.resolve()
    path = (base / category / name).resolve()
    if not (path == base or base in path.parents):
        raise ValueError("skill_path_outside_base")
    for p in [path, *path.parents]:
        if p == base.parent or p.parent == p:
            break
        if p.exists() and p.is_symlink():
            raise ValueError("symlink_rejected")
    return path


def build_intent(*, name: str, content: str, category: str | None = None, evidence: list[str] | None = None, base_dir: str | Path | None = None) -> dict[str, Any]:
    name = validate_name(name)
    category = validate_category(category)
    content = validate_content(content)
    evidence = [str(x) for x in (evidence or []) if str(x).strip()]
    if not evidence:
        raise ValueError("non_empty_evidence_required")
    path = skill_dir(name, category, base_dir=base_dir)
    payload = {
        "operation": "create_skill",
        "name": name,
        "category": category,
        "skill_dir": str(path),
        "skill_file": str(path / "SKILL.md"),
        "content_digest": hashlib.sha256(content.encode("utf-8")).hexdigest(),
    }
    return {
        "schema": "hermes_skill_write_intent_v1",
        "operation": "create_skill",
        "name": name,
        "category": category,
        "skill_dir": str(path),
        "skill_file": str(path / "SKILL.md"),
        "content": content,
        "content_digest": payload["content_digest"],
        "payload": payload,
        "payload_digest": digest(payload),
        "intent_id": digest({"schema": "hermes_skill_write_intent_v1", "payload_digest": digest(payload)}),
        "evidence": evidence,
        "base_dir": str((Path(base_dir).expanduser() if base_dir else SKILLS_BASE).resolve()),
        "created_at": utc_ts(),
    }


def authorize(intent: dict[str, Any], *, actor_id: str, actor_role: str, evidence: list[str] | None = None, approval_decision: str = "approved") -> dict[str, Any]:
    role = str(actor_role or "").strip().lower()
    evidence = [str(x) for x in (evidence or []) if str(x).strip()]
    auth = {
        "schema": "hermes_skill_write_authorization_v1",
        "intent_id": intent.get("intent_id"),
        "payload_digest": intent.get("payload_digest"),
        "actor_id": actor_id,
        "actor_role": role,
        "approval_decision": approval_decision,
        "authorized": False,
        "reasons": [],
        "authority": AUTHORITY,
        "issued_at": utc_ts(),
    }
    if intent.get("schema") != "hermes_skill_write_intent_v1":
        auth["reasons"].append("invalid_intent_schema")
    if intent.get("operation") != "create_skill":
        auth["reasons"].append("operation_not_allowlisted")
    if digest(intent.get("payload")) != intent.get("payload_digest"):
        auth["reasons"].append("payload_digest_mismatch")
    if hashlib.sha256(str(intent.get("content", "")).encode("utf-8")).hexdigest() != intent.get("content_digest"):
        auth["reasons"].append("content_digest_mismatch")
    if approval_decision != "approved":
        auth["reasons"].append("approval_not_approved")
    if role not in ELEVATED_ROLES:
        auth["reasons"].append("actor_role_not_elevated")
    if not evidence:
        auth["reasons"].append("authorization_evidence_required")
    if not auth["reasons"]:
        auth["authorization_id"] = digest({"intent_id": intent.get("intent_id"), "payload_digest": intent.get("payload_digest"), "actor_id": actor_id, "actor_role": role})
        auth["authorized"] = True
        auth["evidence"] = evidence
        auth["reasons"].append("approved_digest_bound_new_skill_create")
    return auth


def execute(intent: dict[str, Any], authorization: dict[str, Any], *, mode: str | None = None) -> dict[str, Any]:
    mode = writer_mode() if mode is None else str(mode or "apply").lower()
    result = {"schema": "hermes_skill_write_execution_v1", "mode": mode, "intent_id": intent.get("intent_id"), "authorization_id": authorization.get("authorization_id"), "write_executed": False, "readback_verified": False, "status": "skipped", "authority": AUTHORITY}
    if mode == "off":
        result["reason"] = "disabled_by_env"
        return result
    if not authorization.get("authorized"):
        result["reason"] = "authorization_not_approved"
        return result
    if authorization.get("intent_id") != intent.get("intent_id") or authorization.get("payload_digest") != intent.get("payload_digest"):
        result["reason"] = "authorization_intent_digest_mismatch"
        return result
    if mode == "shadow":
        result["status"] = "shadow_authorized_not_executed"
        return result
    path = Path(str(intent.get("skill_file"))).resolve()
    directory = Path(str(intent.get("skill_dir"))).resolve()
    base = Path(str(intent.get("base_dir") or SKILLS_BASE)).resolve()
    if not (directory == base or base in directory.parents):
        result["reason"] = "skill_path_outside_base"
        return result
    if directory.exists():
        result["reason"] = "skill_already_exists_no_overwrite"
        return result
    request_digest = digest({"intent_id": intent.get("intent_id"), "authorization_id": authorization.get("authorization_id"), "payload_digest": intent.get("payload_digest")})
    directory.mkdir(parents=True, exist_ok=False)
    path.write_text(str(intent.get("content")), encoding="utf-8")
    marker = directory / ".hermes-skill-write.json"
    marker.write_text(json.dumps({"request_digest": request_digest, "intent_id": intent.get("intent_id"), "authorization_id": authorization.get("authorization_id"), "created_at": utc_ts()}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    readback = path.read_text(encoding="utf-8")
    verified = hashlib.sha256(readback.encode("utf-8")).hexdigest() == intent.get("content_digest")
    result.update({"status": "skill_write_verified" if verified else "skill_write_readback_mismatch", "write_executed": True, "readback_verified": verified, "request_digest": request_digest, "skill_dir": str(directory), "skill_file": str(path), "readback_digest": hashlib.sha256(readback.encode("utf-8")).hexdigest()})
    return result


def rollback(execution: dict[str, Any], *, expected_request_digest: str, evidence: list[str] | None = None) -> dict[str, Any]:
    evidence = [str(x) for x in (evidence or []) if str(x).strip()]
    result = {"schema": "hermes_skill_write_rollback_v1", "request_digest": execution.get("request_digest"), "rollback_executed": False, "readback_verified": False, "status": "skipped"}
    if not evidence:
        result["reason"] = "rollback_evidence_required"
        return result
    if execution.get("request_digest") != expected_request_digest:
        result["reason"] = "request_digest_mismatch"
        return result
    if execution.get("status") != "skill_write_verified":
        result["reason"] = "write_not_verified"
        return result
    directory = Path(str(execution.get("skill_dir"))).resolve()
    marker = directory / ".hermes-skill-write.json"
    if not marker.exists():
        result["reason"] = "rollback_marker_missing"
        return result
    marker_data = json.loads(marker.read_text(encoding="utf-8"))
    if marker_data.get("request_digest") != expected_request_digest:
        result["reason"] = "rollback_marker_digest_mismatch"
        return result
    shutil.rmtree(directory)
    verified = not directory.exists()
    result.update({"status": "skill_write_rollback_verified" if verified else "skill_write_rollback_mismatch", "rollback_executed": True, "readback_verified": verified, "skill_dir": str(directory)})
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Digest-bound canonical skill writer")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("mode")
    p = sub.add_parser("intent")
    p.add_argument("--name", required=True)
    p.add_argument("--content-file", required=True)
    p.add_argument("--category", default=DEFAULT_CATEGORY)
    p.add_argument("--base-dir", default=None)
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
        print(json.dumps({"mode": writer_mode()}, ensure_ascii=False, indent=2))
    elif args.cmd == "intent":
        content = Path(args.content_file).read_text(encoding="utf-8")
        print(json.dumps(build_intent(name=args.name, content=content, category=args.category, base_dir=args.base_dir, evidence=args.evidence), ensure_ascii=False, indent=2))
    elif args.cmd == "authorize":
        print(json.dumps(authorize(json.loads(args.intent_json), actor_id=args.actor_id, actor_role=args.actor_role, evidence=args.evidence), ensure_ascii=False, indent=2))
    elif args.cmd == "execute":
        print(json.dumps(execute(json.loads(args.intent_json), json.loads(args.authorization_json), mode=args.mode), ensure_ascii=False, indent=2))
    elif args.cmd == "rollback":
        print(json.dumps(rollback(json.loads(args.execution_json), expected_request_digest=args.expected_request_digest, evidence=args.evidence), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
