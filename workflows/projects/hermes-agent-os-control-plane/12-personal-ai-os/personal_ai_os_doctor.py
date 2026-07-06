#!/usr/bin/env python3
"""Read-only doctor for the Personal AI OS / Web4.0 Agent OS SSOT packet.

This script performs local validation only. It does not mutate runtime state,
scheduler, taskpool, gateway, external services, credentials, or devices.
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path.home() / ".hermes" / "workflows" / "projects" / "hermes-agent-os-control-plane"
PACKET = ROOT / "12-personal-ai-os"
PROFILE = Path.home() / ".hermes" / "project-profiles" / "hermes-agent-os-control-plane.json"

REQUIRED_FILES = [
    "00-index.md",
    "01-objective-model.md",
    "02-web4-gap-to-local-workstreams.md",
    "03-domain-model-v0.json",
    "04-multimodel-governance.md",
    "05-implementation-roadmap.md",
    "06-non-human-interface-boundary.md",
    "07-backlog.json",
    "08-progress-ledger.md",
    "personal_ai_os_control.py",
    "build_capability_projection.py",
    "10-capability-projection.json",
    "build_authority_ledger_projection.py",
    "11-authority-ledger-projection.jsonl",
    "11-authority-ledger-report.json",
    "build_data_vault_projection.py",
    "12-data-vault-projection.json",
    "build_mission_runtime_state.py",
    "13-mission-runtime-state.json",
    "build_model_review_projection.py",
    "14-model-review-projection.json",
    "15-ux-shell-projection.md",
    "16-device-agent-proposal-projection.json",
]

REQUIRED_DOMAIN_ENTITIES = [
    "UserGoal",
    "CapabilityNode",
    "AuthorityRecord",
    "DataVaultItem",
    "MissionRuntimeState",
    "EvidenceNode",
    "ServiceContract",
    "AgentProposal",
    "DeviceNode",
    "ModelReview",
    "AuthorityBoundary",
]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    findings = []
    file_status = {}

    for name in REQUIRED_FILES:
        path = PACKET / name
        ok = path.exists() and path.stat().st_size > 0
        file_status[name] = {"exists": path.exists(), "non_empty": ok, "bytes": path.stat().st_size if path.exists() else 0}
        if not ok:
            findings.append({"severity": "fail", "code": "missing_or_empty_file", "file": name})

    domain = None
    backlog = None
    profile = None
    try:
        domain = load_json(PACKET / "03-domain-model-v0.json")
    except Exception as exc:  # noqa: BLE001 - diagnostic script
        findings.append({"severity": "fail", "code": "domain_json_invalid", "error": str(exc)})

    try:
        backlog = load_json(PACKET / "07-backlog.json")
    except Exception as exc:  # noqa: BLE001
        findings.append({"severity": "fail", "code": "backlog_json_invalid", "error": str(exc)})

    try:
        profile = load_json(PROFILE)
    except Exception as exc:  # noqa: BLE001
        findings.append({"severity": "fail", "code": "profile_json_invalid", "error": str(exc)})

    if domain:
        entities = domain.get("entities", {})
        for entity in REQUIRED_DOMAIN_ENTITIES:
            if entity not in entities:
                findings.append({"severity": "fail", "code": "missing_domain_entity", "entity": entity})
        levels = domain.get("automation_levels", {})
        if set(levels) != {f"L{i}" for i in range(9)}:
            findings.append({"severity": "fail", "code": "automation_levels_incomplete", "levels": sorted(levels)})

    if backlog:
        items = backlog.get("items", [])
        if len(items) < 9:
            findings.append({"severity": "fail", "code": "backlog_too_small", "count": len(items)})
        if not any(i.get("phase") == "external_dependency" for i in items):
            findings.append({"severity": "fail", "code": "missing_external_dependency_boundary"})
        if backlog.get("policy", {}).get("no_generic_human_intervention_stop") is not True:
            findings.append({"severity": "fail", "code": "non_human_policy_not_enabled"})

    if profile:
        if profile.get("personal_ai_os_packet") != str(PACKET) + "/":
            findings.append({"severity": "fail", "code": "profile_packet_pointer_mismatch", "value": profile.get("personal_ai_os_packet")})
        if profile.get("target_architecture") != "personal_ai_os_web4_agent_os":
            findings.append({"severity": "fail", "code": "profile_target_architecture_mismatch"})

    report = {
        "ok": not any(f["severity"] == "fail" for f in findings),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "read_only_personal_ai_os_packet_doctor",
        "packet": str(PACKET),
        "profile": str(PROFILE),
        "file_status": file_status,
        "domain_entity_count": len(domain.get("entities", {})) if domain else 0,
        "backlog_count": len(backlog.get("items", [])) if backlog else 0,
        "runtime_mutation": False,
        "external_side_effects_executed": False,
        "generic_human_intervention_interface": False,
        "findings": findings,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
