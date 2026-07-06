#!/usr/bin/env python3
"""Read-only local control surface for Personal AI OS packet.

Commands:
  status   summarize project/profile/packet state
  doctor   validate packet consistency
  schema   print domain model schema
  backlog  print backlog items, optionally filtered by status/phase

No runtime routing, tool invocation, scheduler mutation, taskpool lifecycle write,
external dispatch, device actuation, payment, credential entry, or destructive
operation is performed by this script.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path.home() / ".hermes" / "workflows" / "projects" / "hermes-agent-os-control-plane"
PACKET = ROOT / "12-personal-ai-os"
PROFILE = Path.home() / ".hermes" / "project-profiles" / "hermes-agent-os-control-plane.json"
DOCTOR = PACKET / "personal_ai_os_doctor.py"
DOMAIN = PACKET / "03-domain-model-v0.json"
BACKLOG = PACKET / "07-backlog.json"
CAPABILITY = PACKET / "10-capability-projection.json"
AUTHORITY_REPORT = PACKET / "11-authority-ledger-report.json"
AUTHORITY_LEDGER = PACKET / "11-authority-ledger-projection.jsonl"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def emit(obj) -> int:
    print(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def run_doctor_json():
    completed = subprocess.run([sys.executable, str(DOCTOR)], check=False, text=True, capture_output=True)
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        payload = {"ok": False, "findings": [{"severity": "fail", "code": "doctor_output_invalid", "stderr": completed.stderr}]}
    payload["doctor_exit_code"] = completed.returncode
    return payload


def cmd_status(args) -> int:
    profile = load_json(PROFILE)
    domain = load_json(DOMAIN)
    backlog = load_json(BACKLOG)
    capability = load_json(CAPABILITY) if CAPABILITY.exists() else None
    authority = load_json(AUTHORITY_REPORT) if AUTHORITY_REPORT.exists() else None
    doctor = run_doctor_json() if args.with_doctor else None
    items = backlog.get("items", [])
    by_status = {}
    by_phase = {}
    for item in items:
        by_status[item.get("status", "unknown")] = by_status.get(item.get("status", "unknown"), 0) + 1
        by_phase[item.get("phase", "unknown")] = by_phase.get(item.get("phase", "unknown"), 0) + 1
    return emit({
        "ok": True if doctor is None else bool(doctor.get("ok")),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "read_only_personal_ai_os_status",
        "profile_status": profile.get("status"),
        "ssot": profile.get("ssot"),
        "packet": str(PACKET),
        "target_architecture": profile.get("target_architecture"),
        "domain_entity_count": len(domain.get("entities", {})),
        "automation_levels": sorted(domain.get("automation_levels", {}).keys()),
        "backlog_count": len(items),
        "capability_projection": None if capability is None else {
            "ok": capability.get("ok"),
            "node_count": capability.get("node_count"),
            "source_counts": capability.get("source_counts"),
            "runtime_mutation": capability.get("runtime_mutation"),
            "external_side_effects_executed": capability.get("external_side_effects_executed"),
            "projected_nodes_would_execute": capability.get("projected_nodes_would_execute"),
        },
        "authority_ledger": None if authority is None else {
            "ok": authority.get("ok"),
            "record_count": authority.get("record_count"),
            "runtime_mutation": authority.get("runtime_mutation"),
            "external_side_effects_executed": authority.get("external_side_effects_executed"),
            "payment_or_credential_action_executed": authority.get("payment_or_credential_action_executed"),
            "agent_typed_secret": authority.get("agent_typed_secret"),
        },
        "backlog_by_status": by_status,
        "backlog_by_phase": by_phase,
        "next_ready_item": next((i for i in items if i.get("status") in {"ready_next", "in_progress"}), None),
        "runtime_mutation": False,
        "tool_invocation_from_personal_os": False,
        "scheduler_mutation": False,
        "taskpool_lifecycle_write": False,
        "external_side_effects_executed": False,
        "generic_human_intervention_interface": False,
        "doctor": doctor,
    })


def cmd_doctor(args) -> int:
    payload = run_doctor_json()
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if payload.get("ok") else 1


def cmd_schema(args) -> int:
    domain = load_json(DOMAIN)
    if args.entity:
        entities = domain.get("entities", {})
        if args.entity not in entities:
            return emit({"ok": False, "error": "unknown_entity", "entity": args.entity, "available": sorted(entities)}) or 1
        return emit({"ok": True, "entity": args.entity, "schema": entities[args.entity], "runtime_mutation": False})
    return emit({"ok": True, "schema_version": domain.get("schema_version"), "automation_levels": domain.get("automation_levels"), "entities": domain.get("entities"), "runtime_mutation": False})


def cmd_backlog(args) -> int:
    backlog = load_json(BACKLOG)
    items = backlog.get("items", [])
    if args.status:
        items = [i for i in items if i.get("status") == args.status]
    if args.phase:
        items = [i for i in items if i.get("phase") == args.phase]
    return emit({"ok": True, "count": len(items), "items": items, "runtime_mutation": False, "external_side_effects_executed": False})


def cmd_capabilities(args) -> int:
    projection = load_json(CAPABILITY)
    nodes = projection.get("nodes", [])
    if args.source:
        nodes = [n for n in nodes if n.get("source") == args.source]
    if args.automation_level:
        nodes = [n for n in nodes if n.get("automation_level") == args.automation_level]
    if args.limit is not None:
        nodes = nodes[: args.limit]
    return emit({
        "ok": bool(projection.get("ok")),
        "mode": "read_only_capability_projection_readback",
        "total_node_count": projection.get("node_count"),
        "returned_count": len(nodes),
        "source_counts": projection.get("source_counts"),
        "runtime_mutation": False,
        "tool_invocation_from_projection": False,
        "external_side_effects_executed": False,
        "projected_nodes_would_execute": False,
        "nodes": nodes,
    })


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only Personal AI OS local control surface")
    sub = parser.add_subparsers(dest="command", required=True)

    p_status = sub.add_parser("status")
    p_status.add_argument("--with-doctor", action="store_true")
    p_status.set_defaults(func=cmd_status)

    p_doctor = sub.add_parser("doctor")
    p_doctor.set_defaults(func=cmd_doctor)

    p_schema = sub.add_parser("schema")
    p_schema.add_argument("--entity")
    p_schema.set_defaults(func=cmd_schema)

    p_backlog = sub.add_parser("backlog")
    p_backlog.add_argument("--status")
    p_backlog.add_argument("--phase")
    p_backlog.set_defaults(func=cmd_backlog)

    p_cap = sub.add_parser("capabilities")
    p_cap.add_argument("--source")
    p_cap.add_argument("--automation-level")
    p_cap.add_argument("--limit", type=int)
    p_cap.set_defaults(func=cmd_capabilities)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
