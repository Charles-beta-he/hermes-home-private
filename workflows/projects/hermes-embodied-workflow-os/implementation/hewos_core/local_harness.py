import json
from pathlib import Path


class LocalHarnessError(ValueError):
    pass


def _require(condition, message):
    if not condition:
        raise LocalHarnessError(message)


def _receipt_path(root):
    return Path(root) / "receipts.jsonl"


def read_harness_receipts(root):
    path = _receipt_path(root)
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _write_receipts(root, rows):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    path = _receipt_path(root)
    path.write_text("".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def execute_local_harness(root, decision):
    _require(decision.get("decision") == "authorized_intent_only", "harness requires authorized_intent_only decision")
    _require(decision.get("execution_enabled") is False, "harness cannot consume live execution-enabled decisions")
    exact_target = decision.get("exact_target") or ""
    _require(exact_target.startswith("local-harness:"), "harness target must be local-harness scoped")
    _require(decision.get("intent_digest"), "intent_digest required")
    receipt_id = "harness:" + decision["intent_digest"].split(":", 1)[1][:16]
    rows = read_harness_receipts(root)
    for row in rows:
        if row.get("receipt_id") == receipt_id:
            replay = dict(row)
            replay["idempotent_replay"] = True
            return replay
    row = {
        "schema": "hewos_local_harness_receipt_v1",
        "receipt_id": receipt_id,
        "boundary_id": decision["boundary_id"],
        "intent_digest": decision["intent_digest"],
        "exact_target": exact_target,
        "payload_hash": decision["payload_hash"],
        "write_class": "local_disposable_harness",
        "live_adapter_touched": False,
        "execution_enabled": False,
        "token_read_allowed": False,
        "stores_secrets": False,
        "evidence_refs": list(decision.get("evidence_refs") or []),
        "readback": {
            "receipt_file": str(_receipt_path(root)),
            "boundary_id": decision["boundary_id"],
            "verified": True,
        },
        "rollback_plan": f"remove exact receipt_id {receipt_id} from {_receipt_path(root)}",
        "idempotency_key": decision["idempotency_key"],
        "idempotent_replay": False,
    }
    rows.append(row)
    _write_receipts(root, rows)
    return dict(row)


def rollback_harness_receipt(root, receipt_id):
    rows = read_harness_receipts(root)
    kept = [row for row in rows if row.get("receipt_id") != receipt_id]
    rolled = len(kept) != len(rows)
    _write_receipts(root, kept)
    return {
        "schema": "hewos_local_harness_rollback_v1",
        "receipt_id": receipt_id,
        "rolled_back": rolled,
        "remaining": len(kept),
    }
