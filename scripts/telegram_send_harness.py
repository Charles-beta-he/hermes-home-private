#!/usr/bin/env python3
"""Digest-bound Telegram send harness.

Default-on target-specific external side-effect gate for Telegram sends. It does
not talk to Telegram directly; Hermes still performs the send through the
messaging adapter/tool. This harness creates and authorizes a narrow send
intent, then validates/records the external receipt returned by the send tool.
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

try:
    from harness_event_ledger import append_event
except Exception:  # pragma: no cover
    import importlib.util as _importlib_util
    _ledger_path = Path(__file__).resolve().parent / "harness_event_ledger.py"
    _spec = _importlib_util.spec_from_file_location("harness_event_ledger", _ledger_path)
    if _spec and _spec.loader:
        _module = _importlib_util.module_from_spec(_spec)
        _spec.loader.exec_module(_module)
        append_event = _module.append_event
    else:
        append_event = None

HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))).expanduser()
RECEIPTS_DIR = HERMES_HOME / "state" / "telegram-send-receipts"
DEFAULT_TARGET_ALLOWLIST = "telegram:he cheng"
DISABLE_VALUES = {"0", "false", "off", "no", "disabled"}
ENABLE_VALUES = {"1", "true", "yes", "on"}
ELEVATED_ROLES = {"admin", "operator", "system"}
TARGET_RE = re.compile(r"^telegram:[^\n\r]{1,180}$")
MAX_MESSAGE_CHARS = 1200


def now() -> int:
    return int(time.time())


def utc_ts(ts: int | None = None) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts or now()))


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(obj: Any) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def content_digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def mode(default: str = "apply") -> str:
    raw = os.environ.get("HERMES_TELEGRAM_SEND_MODE") or default
    value = str(raw or "").strip().lower()
    if value in DISABLE_VALUES:
        return "off"
    if value in ENABLE_VALUES:
        return "apply"
    if value not in {"apply", "shadow", "off"}:
        return "apply"
    return value


def target_allowlist() -> set[str]:
    raw = os.environ.get("HERMES_TELEGRAM_SEND_TARGET_ALLOWLIST", DEFAULT_TARGET_ALLOWLIST)
    return {x.strip() for x in raw.split(",") if x.strip()}


def validate_target(target: str) -> str:
    target = str(target or "").strip()
    if not TARGET_RE.match(target):
        raise ValueError("invalid_telegram_target")
    return target


def build_send_intent(*, task_id: str, target: str, message: str, purpose: str, evidence: list[str] | None = None) -> dict[str, Any]:
    target = validate_target(target)
    evidence = [str(x) for x in (evidence or []) if str(x).strip()]
    if not message or len(message) > MAX_MESSAGE_CHARS:
        raise ValueError("message_length_invalid")
    if not purpose:
        raise ValueError("purpose_required")
    payload = {
        "channel": "telegram",
        "target": target,
        "message_digest": content_digest(message),
        "message_chars": len(message),
        "purpose": purpose,
        "task_id": task_id,
    }
    intent = {
        "schema": "hermes_telegram_send_intent_v1",
        "task_id": task_id,
        "channel": "telegram",
        "target": target,
        "message": message,
        "message_digest": payload["message_digest"],
        "message_chars": len(message),
        "purpose": purpose,
        "payload_digest": digest(payload),
        "evidence": evidence,
        "created_at": utc_ts(),
    }
    intent["intent_id"] = digest({"schema": intent["schema"], "payload_digest": intent["payload_digest"], "created_at": intent["created_at"]})
    return intent


def authorize_send(*, intent: dict[str, Any], actor_id: str, actor_role: str, approval_evidence: list[str] | None = None, mode_value: str | None = None) -> dict[str, Any]:
    mode_value = mode() if mode_value is None else str(mode_value or "apply").lower()
    approval_evidence = [str(x) for x in (approval_evidence or []) if str(x).strip()]
    auth = {
        "schema": "hermes_telegram_send_authorization_v1",
        "mode": mode_value,
        "intent_id": intent.get("intent_id"),
        "target": intent.get("target"),
        "message_digest": intent.get("message_digest"),
        "actor_id": actor_id,
        "actor_role": str(actor_role or "").lower(),
        "approved": False,
        "reasons": [],
        "authority": "telegram_target_allowlist_send_only_requires_external_receipt",
    }
    if mode_value == "off":
        auth["reasons"].append("disabled_by_env")
        return auth
    try:
        target = validate_target(str(intent.get("target") or ""))
    except ValueError as exc:
        auth["reasons"].append(str(exc))
        return auth
    if target not in target_allowlist():
        auth["reasons"].append("target_not_allowlisted")
    if str(actor_role or "").lower() not in ELEVATED_ROLES:
        auth["reasons"].append("actor_role_not_elevated")
    if not intent.get("evidence"):
        auth["reasons"].append("intent_evidence_required")
    if not approval_evidence:
        auth["reasons"].append("approval_evidence_required")
    expected_payload_digest = digest({
        "channel": "telegram",
        "target": target,
        "message_digest": intent.get("message_digest"),
        "message_chars": intent.get("message_chars"),
        "purpose": intent.get("purpose"),
        "task_id": intent.get("task_id"),
    })
    if expected_payload_digest != intent.get("payload_digest"):
        auth["reasons"].append("payload_digest_mismatch")
    if content_digest(str(intent.get("message") or "")) != intent.get("message_digest"):
        auth["reasons"].append("message_digest_mismatch")
    if not auth["reasons"]:
        auth["approved"] = mode_value == "apply"
        auth["status"] = "telegram_send_authorized" if mode_value == "apply" else "telegram_send_shadow_authorized_not_sent"
        auth["approval_evidence"] = approval_evidence
        auth["authorization_id"] = digest({"intent_id": intent.get("intent_id"), "target": target, "message_digest": intent.get("message_digest"), "actor_id": actor_id, "approval_evidence": approval_evidence})
        auth["reasons"].append("approved_digest_bound_telegram_send")
    else:
        auth["status"] = "telegram_send_denied"
    return auth


def receipt_path(receipt_id: str, *, base_dir: str | Path | None = None) -> Path:
    base = Path(base_dir).expanduser() if base_dir else RECEIPTS_DIR
    base = base.resolve()
    base.mkdir(parents=True, exist_ok=True)
    if not re.match(r"^[a-f0-9]{64}$", receipt_id):
        raise ValueError("invalid_receipt_id")
    return base / f"{receipt_id}.json"


def record_receipt(*, intent: dict[str, Any], authorization: dict[str, Any], send_result: dict[str, Any], receipt_evidence: list[str] | None = None, base_dir: str | Path | None = None) -> dict[str, Any]:
    receipt_evidence = [str(x) for x in (receipt_evidence or []) if str(x).strip()]
    result = {
        "schema": "hermes_telegram_send_receipt_v1",
        "intent_id": intent.get("intent_id"),
        "authorization_id": authorization.get("authorization_id"),
        "target": intent.get("target"),
        "message_digest": intent.get("message_digest"),
        "verified": False,
        "status": "telegram_receipt_denied",
        "reasons": [],
    }
    if not authorization.get("approved"):
        result["reasons"].append("authorization_not_approved")
    if not receipt_evidence:
        result["reasons"].append("receipt_evidence_required")
    if send_result.get("success") is not True:
        result["reasons"].append("send_result_not_success")
    if str(send_result.get("target") or intent.get("target")) != intent.get("target"):
        result["reasons"].append("target_mismatch")
    message_id = send_result.get("message_id") or send_result.get("id")
    if not message_id:
        result["reasons"].append("message_id_required")
    if not result["reasons"]:
        payload = {
            "intent_id": intent.get("intent_id"),
            "authorization_id": authorization.get("authorization_id"),
            "target": intent.get("target"),
            "message_digest": intent.get("message_digest"),
            "message_id": str(message_id),
            "receipt_evidence": receipt_evidence,
        }
        receipt_id = digest(payload)
        result.update({
            "status": "telegram_send_verified",
            "verified": True,
            "message_id": str(message_id),
            "receipt_id": receipt_id,
            "recorded_at": utc_ts(),
            "receipt_evidence": receipt_evidence,
        })
        path = receipt_path(receipt_id, base_dir=base_dir)
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        result["receipt_path"] = str(path)
        if append_event is not None:
            result["ledger_event"] = append_event(kind="telegram_send", payload={k: result.get(k) for k in ["status", "intent_id", "authorization_id", "target", "message_digest", "message_id", "receipt_id"]})
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Telegram send harness")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("mode")
    p = sub.add_parser("intent")
    p.add_argument("--task-id", required=True)
    p.add_argument("--target", required=True)
    p.add_argument("--message", required=True)
    p.add_argument("--purpose", required=True)
    p.add_argument("--evidence", action="append", default=[])
    p = sub.add_parser("authorize")
    p.add_argument("--intent-json", required=True)
    p.add_argument("--actor-id", required=True)
    p.add_argument("--actor-role", required=True)
    p.add_argument("--approval-evidence", action="append", default=[])
    p.add_argument("--mode", default=None)
    p = sub.add_parser("record")
    p.add_argument("--intent-json", required=True)
    p.add_argument("--authorization-json", required=True)
    p.add_argument("--send-result-json", required=True)
    p.add_argument("--receipt-evidence", action="append", default=[])
    p.add_argument("--base-dir", default=None)
    args = parser.parse_args(argv)
    if args.cmd == "mode":
        print(json.dumps({"mode": mode(), "target_allowlist": sorted(target_allowlist())}, ensure_ascii=False, indent=2))
    elif args.cmd == "intent":
        print(json.dumps(build_send_intent(task_id=args.task_id, target=args.target, message=args.message, purpose=args.purpose, evidence=args.evidence), ensure_ascii=False, indent=2))
    elif args.cmd == "authorize":
        print(json.dumps(authorize_send(intent=json.loads(args.intent_json), actor_id=args.actor_id, actor_role=args.actor_role, approval_evidence=args.approval_evidence, mode_value=args.mode), ensure_ascii=False, indent=2))
    elif args.cmd == "record":
        print(json.dumps(record_receipt(intent=json.loads(args.intent_json), authorization=json.loads(args.authorization_json), send_result=json.loads(args.send_result_json), receipt_evidence=args.receipt_evidence, base_dir=args.base_dir), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
