import hashlib
import json
from pathlib import Path


class OrderedBoundaryError(ValueError):
    pass


def _require(condition, message):
    if not condition:
        raise OrderedBoundaryError(message)


def digest_payload(payload):
    text = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_jsonl(path):
    path = Path(path)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def append_external_outbox_dry_run(path, *, platform, target, payload_hash, allowlist, idempotency_key):
    exact = f"{platform}:{target}"
    _require(exact in set(allowlist or []), "target_not_allowlisted")
    _require(str(payload_hash).startswith("sha256:"), "payload_hash_required")
    _require(bool(idempotency_key), "idempotency_key_required")
    rows = read_jsonl(path)
    outbox_id = "outbox:" + digest_payload({"platform": platform, "target": target, "payload_hash": payload_hash, "idempotency_key": idempotency_key}).split(":", 1)[1][:16]
    for row in rows:
        if row.get("outbox_id") == outbox_id:
            replay = dict(row)
            replay["idempotent_replay"] = True
            return replay
    row = {
        "schema": "hewos_external_outbox_dry_run_v1",
        "outbox_id": outbox_id,
        "platform": platform,
        "target": target,
        "payload_hash": payload_hash,
        "allowlist_ref": sorted(allowlist),
        "status": "dry_run_recorded",
        "send_executed": False,
        "token_read_allowed": False,
        "stores_secrets": False,
        "idempotency_key": idempotency_key,
        "idempotent_replay": False,
    }
    rows.append(row)
    _write_jsonl(path, rows)
    return dict(row)


def deploy_push_preflight_record(*, repo, remote, branch, dry_run_exit_code, dry_run_output, rollback_plan):
    status = "dry_run_pass_no_push" if dry_run_exit_code == 0 else "blocked_preflight"
    return {
        "schema": "hewos_deploy_push_preflight_v1",
        "repo": repo,
        "remote": remote,
        "branch": branch,
        "dry_run_exit_code": dry_run_exit_code,
        "status": status,
        "push_executed": False,
        "deploy_executed": False,
        "rollback_plan": rollback_plan,
        "readback": dry_run_output,
    }


def hardware_safety_gate(*, device_id, telemetry, safety_gate, external_control_gate, onsite_gate, physical_risk):
    reasons = []
    if not device_id:
        reasons.append("missing_device_id")
    if not telemetry or not telemetry.get("fresh"):
        reasons.append("telemetry_not_fresh")
    if not safety_gate:
        reasons.append("safety_gate_required")
    if not external_control_gate:
        reasons.append("external_control_gate_required")
    if physical_risk and not onsite_gate:
        reasons.append("onsite_gate_required")
    return {
        "schema": "hewos_hardware_safety_gate_v1",
        "device_id": device_id,
        "telemetry": dict(telemetry or {}),
        "safety_gate": bool(safety_gate),
        "external_control_gate": bool(external_control_gate),
        "onsite_gate": bool(onsite_gate),
        "physical_risk": bool(physical_risk),
        "decision": "blocked" if reasons else "dry_run_pass_no_execution",
        "reasons": sorted(reasons),
        "execution_enabled": False,
        "hardware_touched": False,
    }


def auth_human_secret_gate(*, provider, actor, requested_scope):
    return {
        "schema": "hewos_auth_human_secret_gate_v1",
        "provider": provider,
        "actor": actor,
        "requested_scope": requested_scope,
        "decision": "human_secret_entry_only",
        "agent_may_type_secret": False,
        "token_read_allowed": False,
        "stores_secrets": False,
        "auth_executed": False,
        "readback": "non-secret gate record only",
    }
