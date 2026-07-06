#!/usr/bin/env python3
"""Build Multi-model RouteReview/EvidencePacket projection for Personal AI OS.

Projection only: no live model fanout, no provider calls, no external side effects.
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone

HOME = Path.home()
PACKET = HOME / ".hermes" / "workflows" / "projects" / "hermes-agent-os-control-plane" / "12-personal-ai-os"
OUT = PACKET / "14-model-review-projection.json"


def main() -> int:
    evidence_refs = [
        "09-doctor-report.json",
        "10-capability-projection.json",
        "11-authority-ledger-report.json",
        "12-data-vault-projection.json",
        "13-mission-runtime-state.json",
    ]
    missing = [p for p in evidence_refs if not (PACKET / p).exists()]
    route_review = {
        "schema": "RouteReview.v0",
        "id": "route_review.personal_ai_os_p6",
        "objective": "Certify local Personal AI OS projection progress and select next safe automation slice",
        "risk_tier": "T3_architecture_governance_projection",
        "expected_side_effects": "local_projection_files_only",
        "data_sensitivity": "D2_project_artifacts",
        "model_roles": ["architect", "safety_adversarial_reviewer", "arbiter", "t0_router"],
        "certification_required": True,
        "automation_ceiling": "L3_local_scheduled_or_long_running",
        "execution_allowed": False,
        "external_dispatch_allowed": False,
    }
    evidence_packet = {
        "schema": "EvidencePacket.v0",
        "id": "evidence_packet.personal_ai_os_p6",
        "goal": "Personal AI OS / Web4.0 Agent OS local safe slice advancement",
        "success_criteria": [
            "P0-P5 projections exist and validate",
            "No secret/payment/external side effect executed",
            "No generic human-intervention interface used as stop condition",
            "Next slice remains local and reversible",
        ],
        "constraints": [
            "no agent-typed secrets",
            "no payments/legal signatures",
            "no unbounded external fanout",
            "external ecosystem gaps become AuthorityBoundary/ExternalDependency records",
        ],
        "evidence_refs": [str(PACKET / p) for p in evidence_refs],
        "claim_ids": [
            "C-001: packet doctor passes",
            "C-002: capability projection is read-only",
            "C-003: authority ledger records local grants and forbids secret/payment/external actions",
            "C-004: data vault exports no raw secrets or WIP global memory",
            "C-005: mission state encodes evidence DAG and non-human boundary policy",
        ],
    }
    model_review = {
        "schema": "ModelReview.v0",
        "id": "model_review.personal_ai_os_p6_projection",
        "route_review": route_review,
        "evidence_packet": evidence_packet,
        "verdict": "local_projection_ready_for_future_multimodel_certification",
        "degraded": False,
        "live_model_fanout_executed": False,
        "dissent": [],
        "automation_ceiling": "L3",
    }
    findings = []
    if missing:
        findings.append({"severity": "fail", "code": "missing_evidence_refs", "missing": missing})
    payload = {
        "ok": not findings,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "multimodel_governance_projection_v0",
        "route_review": route_review,
        "evidence_packet": evidence_packet,
        "model_review": model_review,
        "runtime_mutation": False,
        "external_side_effects_executed": False,
        "live_model_fanout_executed": False,
        "findings": findings,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: payload[k] for k in ["ok", "mode", "runtime_mutation", "external_side_effects_executed", "live_model_fanout_executed", "findings"]}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
