import copy
import hashlib
import json
from datetime import datetime, timezone

from .contracts import ContractError, validate_evidence_ledger_entry


def _canonical_hash(payload):
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(data.encode("utf-8")).hexdigest()


class EvidenceLedger:
    def __init__(self):
        self._entries = []

    def append(self, *, kind, subject_id, source, claims, evidence_refs, payload):
        if not evidence_refs:
            raise ContractError("evidence_refs must be non-empty")
        entry = {
            "entry_id": f"ev.{len(self._entries) + 1}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "kind": kind,
            "subject_id": subject_id,
            "source": source,
            "claims": copy.deepcopy(claims),
            "evidence_refs": list(evidence_refs),
            "payload": copy.deepcopy(payload),
            "checksum_or_hash": _canonical_hash(payload),
            "append_only": True,
        }
        validate_evidence_ledger_entry(entry)
        self._entries.append(entry)
        return copy.deepcopy(entry)

    def entries(self):
        return copy.deepcopy(self._entries)


def replay_world_state(entries):
    world_state = {"visible_parts": [], "completed_steps": []}
    for entry in entries:
        payload = entry.get("payload", {})
        derived = payload.get("derived_facts", {})
        for part in derived.get("visible_parts", []):
            if part not in world_state["visible_parts"]:
                world_state["visible_parts"].append(part)
        delta = payload.get("world_state_delta", {})
        for step in delta.get("completed_steps", []):
            if step not in world_state["completed_steps"]:
                world_state["completed_steps"].append(step)
    return world_state
