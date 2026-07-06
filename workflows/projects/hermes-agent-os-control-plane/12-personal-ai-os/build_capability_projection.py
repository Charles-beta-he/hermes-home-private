#!/usr/bin/env python3
"""Build a read-only Personal AI OS CapabilityNode projection.

Sources are local skills, the project profile, and Personal AI OS packet scripts.
This is advisory/projection only: it does not execute projected capabilities.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from datetime import datetime, timezone

HOME = Path.home()
PACKET = HOME / ".hermes" / "workflows" / "projects" / "hermes-agent-os-control-plane" / "12-personal-ai-os"
SKILLS = HOME / ".hermes" / "skills"
PROFILE = HOME / ".hermes" / "project-profiles" / "hermes-agent-os-control-plane.json"
OUT = PACKET / "10-capability-projection.json"


def safe_id(text: str) -> str:
    return re.sub(r"[^a-z0-9_.-]+", "-", text.lower()).strip("-")[:120]


def first_frontmatter_value(text: str, key: str) -> str | None:
    m = re.search(rf"^{re.escape(key)}:\s*(.+)$", text, re.MULTILINE)
    if not m:
        return None
    return m.group(1).strip().strip('"\'')


def classify_skill(path: Path, text: str) -> dict:
    rel = path.relative_to(SKILLS)
    name = first_frontmatter_value(text, "name") or rel.parts[0]
    desc = first_frontmatter_value(text, "description") or "local skill capability"
    joined = f"{name} {desc} {rel}".lower()
    side = "S0"
    auto = "L1"
    perms = ["local_read"]
    verify = "skill_view/readback"
    rollback = "not_applicable_read_only"
    sensitivity = "D2"
    if any(k in joined for k in ["github", "send", "gateway", "telegram", "external", "publish", "deploy", "push"]):
        side, auto, perms = "S5", "L6", ["exact_external_authority", "receipt_readback"]
        rollback = "adapter_specific_or_compensation"
    elif any(k in joined for k in ["terminal", "devops", "code", "software", "git", "file", "patch"]):
        side, auto, perms = "S2", "L2", ["local_reversible_write_or_command_authority"]
        rollback = "git_diff_revert_or_file_backup"
    elif any(k in joined for k in ["cron", "taskpool", "mission", "agent", "workflow"]):
        side, auto, perms = "S3", "L3", ["local_runtime_governance_authority"]
        rollback = "disable_job_or_revert_state"
    if any(k in joined for k in ["payment", "credential", "secret", "password", "wallet"]):
        side, auto, perms, sensitivity = "S7", "L8", ["sealed_secret_or_external_authority_boundary"], "D5"
        rollback = "do_not_execute_without_external_safe_channel"
    return {
        "id": "skill." + safe_id(str(rel.with_suffix(""))),
        "source": "skill",
        "source_path": str(path),
        "name": name,
        "description": desc[:300],
        "goal_patterns": [name, desc[:120]],
        "required_tools": ["skill_view"],
        "required_permissions": perms,
        "side_effect_level": side,
        "data_sensitivity": sensitivity,
        "verification_method": verify,
        "rollback_method": rollback,
        "automation_level": auto,
        "model_preferences": ["router", "architect"],
        "would_execute": False,
    }


def main() -> int:
    nodes = []
    findings = []
    if SKILLS.exists():
        for path in SKILLS.rglob("SKILL.md"):
            if "/profiles/" in str(path):
                continue
            try:
                nodes.append(classify_skill(path, path.read_text(encoding="utf-8", errors="ignore")))
            except Exception as exc:  # noqa: BLE001
                findings.append({"severity": "warn", "code": "skill_projection_failed", "path": str(path), "error": str(exc)})

    if PROFILE.exists():
        profile = json.loads(PROFILE.read_text())
        nodes.append({
            "id": "profile.hermes-agent-os-control-plane",
            "source": "project_profile",
            "source_path": str(PROFILE),
            "name": profile.get("name", "Hermes Agent OS Control Plane"),
            "description": "Project profile for Personal AI OS / Web4.0 Agent OS upgrade",
            "goal_patterns": ["personal AI OS", "Web4.0 Agent OS", "Agent OS control plane"],
            "required_tools": ["read_file", "personal_ai_os_control"],
            "required_permissions": ["local_read", "local_reversible_write_for_project_artifacts"],
            "side_effect_level": "S2",
            "data_sensitivity": "D2",
            "verification_method": "profile JSON readback + doctor",
            "rollback_method": "git revert scoped packet/profile commit",
            "automation_level": "L2",
            "model_preferences": ["architect", "arbiter", "safety_reviewer"],
            "would_execute": False,
        })

    for script in ["personal_ai_os_doctor.py", "personal_ai_os_control.py", "build_capability_projection.py"]:
        nodes.append({
            "id": "local_script." + script.replace(".py", ""),
            "source": "local_packet_script",
            "source_path": str(PACKET / script),
            "name": script,
            "description": "Read-only/local projection support script",
            "goal_patterns": ["validate packet", "read-only projection", "doctor", "status"],
            "required_tools": ["terminal", "python"],
            "required_permissions": ["local_read", "local_artifact_write_for_reports"],
            "side_effect_level": "S1",
            "data_sensitivity": "D2",
            "verification_method": "py_compile + command readback",
            "rollback_method": "delete generated report or git revert",
            "automation_level": "L2",
            "model_preferences": ["implementer", "reviewer"],
            "would_execute": False,
        })

    required = {"id", "name", "goal_patterns", "required_tools", "required_permissions", "side_effect_level", "verification_method", "rollback_method", "automation_level"}
    for node in nodes:
        missing = sorted(k for k in required if k not in node or node[k] in (None, "", []))
        if missing:
            findings.append({"severity": "fail", "code": "capability_node_missing_required", "id": node.get("id"), "missing": missing})

    payload = {
        "ok": not any(f["severity"] == "fail" for f in findings),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "read_only_capability_graph_projection_v0",
        "node_count": len(nodes),
        "source_counts": {src: sum(1 for n in nodes if n["source"] == src) for src in sorted({n["source"] for n in nodes})},
        "runtime_mutation": False,
        "tool_invocation_from_projection": False,
        "external_side_effects_executed": False,
        "projected_nodes_would_execute": False,
        "findings": findings,
        "nodes": nodes,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: payload[k] for k in ["ok", "mode", "node_count", "source_counts", "runtime_mutation", "external_side_effects_executed", "projected_nodes_would_execute", "findings"]}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
