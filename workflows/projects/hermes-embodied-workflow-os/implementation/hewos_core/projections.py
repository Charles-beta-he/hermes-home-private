from collections import Counter

from .ledger import replay_world_state


def capability_projection(manifest):
    return {
        "capability_id": manifest["capability_id"],
        "actor_id": manifest["actor_id"],
        "adapter_id": manifest["adapter_id"],
        "capability_type": manifest["capability_type"],
        "risk_class": manifest.get("risk_class", "none"),
        "dry_run_default": bool(manifest.get("dry_run_default", True)),
        "status": "simulated" if manifest.get("dry_run_default", True) else "available",
    }


def task_graph_projection(task_graph_id, title, *, nodes, edges):
    return {
        "task_graph_id": task_graph_id,
        "title": title,
        "nodes": [dict(node) for node in nodes],
        "edges": [dict(edge) for edge in edges],
        "world_state_ref": "replay:latest",
    }


def action_intent_projection(intent):
    risk_level = intent.get("risk_level", "none")
    required_gates = set(intent.get("required_gates", []))
    if risk_level in {"physical_action", "destructive", "payment_or_credential"}:
        status = "blocked"
    elif {"SafetyGate", "ExternalControlGate"}.issubset(required_gates):
        status = "dry_run_reviewable"
    else:
        status = "blocked"
    return {
        "intent_id": intent["intent_id"],
        "capability_id": intent["capability_id"],
        "risk_level": risk_level,
        "preview": intent.get("preview", ""),
        "required_gates": list(intent.get("required_gates", [])),
        "evidence_refs": list(intent.get("evidence_refs", [])),
        "status": status,
    }


def evidence_entry_projection(entry):
    return {
        "entry_id": entry["entry_id"],
        "timestamp": entry["timestamp"],
        "kind": entry["kind"],
        "subject_id": entry["subject_id"],
        "source": entry["source"],
        "claims": [dict(claim) for claim in entry.get("claims", [])],
        "evidence_refs": list(entry.get("evidence_refs", [])),
        "redaction_status": "checked",
    }


def build_dashboard_projection(capabilities, ledger_entries, pending_action_intents=None):
    pending_action_intents = list(pending_action_intents or [])
    risks = Counter(intent.get("risk_level", "none") for intent in pending_action_intents)
    projected_capabilities = [capability_projection(item) for item in capabilities]
    projected_entries = [evidence_entry_projection(item) for item in ledger_entries]
    return {
        "capability_count": len(projected_capabilities),
        "capabilities": projected_capabilities,
        "ledger_entry_count": len(projected_entries),
        "latest_evidence_entries": projected_entries[-10:],
        "pending_action_intents_by_risk": dict(risks),
        "world_state": replay_world_state(ledger_entries),
    }
