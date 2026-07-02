import json
from pathlib import Path


class SimulationLedgerError(ValueError):
    pass


def _require(condition, message):
    if not condition:
        raise SimulationLedgerError(message)


def read_simulation_ledger(path):
    path = Path(path)
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _write_rows(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in rows)
    path.write_text(text, encoding="utf-8")


def append_simulation_receipt(path, decision):
    _require(decision.get("decision") == "authorized_intent_only", "only authorized intent decisions can be recorded")
    _require(decision.get("execution_enabled") is False, "simulation ledger cannot record live execution-enabled decisions")
    _require(decision.get("intent_digest"), "intent_digest required")
    receipt_id = "simreceipt:" + decision["intent_digest"].split(":", 1)[1][:16]
    rows = read_simulation_ledger(path)
    for row in rows:
        if row.get("receipt_id") == receipt_id:
            replay = dict(row)
            replay["idempotent_replay"] = True
            return replay
    row = {
        "schema": "hewos_simulation_ledger_receipt_v1",
        "receipt_id": receipt_id,
        "boundary_id": decision["boundary_id"],
        "intent_digest": decision["intent_digest"],
        "exact_target": decision["exact_target"],
        "payload_hash": decision["payload_hash"],
        "execution_enabled": False,
        "write_class": "simulation_only_local_ledger",
        "readback_plan": decision["readback_plan"],
        "rollback_plan": decision["rollback_plan"],
        "evidence_refs": list(decision.get("evidence_refs") or []),
        "idempotency_key": decision["idempotency_key"],
        "idempotent_replay": False,
    }
    rows.append(row)
    _write_rows(path, rows)
    return dict(row)


def rollback_simulation_receipt(path, receipt_id):
    rows = read_simulation_ledger(path)
    kept = [row for row in rows if row.get("receipt_id") != receipt_id]
    rolled = len(kept) != len(rows)
    _write_rows(path, kept)
    return {
        "schema": "hewos_simulation_ledger_rollback_v1",
        "receipt_id": receipt_id,
        "rolled_back": rolled,
        "remaining": len(kept),
    }
