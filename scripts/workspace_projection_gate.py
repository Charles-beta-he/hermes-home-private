#!/usr/bin/env python3
"""Validate external WorkspaceProjection packets.

This is a local, read-only gate inspired by Anthropic J-space/global-workspace
research. It validates external projection/evidence/claim packets; it does not
inspect model hidden states and grants no runtime/external authority.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

ALLOWED_COMPLETION_STATUSES = {"verified_local", "advisory_only", "blocked_missing_evidence"}
OBJECTIVE_EVIDENCE = {"objective", "user_statement"}
MODEL_ONLY = {"model_judgment", "model_consensus", "reflection_text"}
REQUIRED_NEGATIVE_EVIDENCE = {
    "no_hidden_state_access",
    "no_external_dispatch",
    "no_taskpool_lifecycle_write",
}
DANGEROUS_ALLOWED = {
    "external_dispatch",
    "publish_deploy_push",
    "destructive_operation",
    "payment",
    "secret_entry",
    "credential_entry",
    "taskpool_lifecycle_write",
}


def load_packet(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _ids(items: List[Dict[str, Any]]) -> set[str]:
    return {str(x.get("id")) for x in items if x.get("id")}


def validate(packet: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []

    if packet.get("schema") != "workspace_projection_packet_v1":
        errors.append("schema must be workspace_projection_packet_v1")

    source = packet.get("source_boundary") or {}
    if source.get("hidden_state_access") is not False:
        errors.append("source_boundary.hidden_state_access must be false for this external projection gate")
    if source.get("model_judgment_is_objective_evidence") is not False:
        errors.append("model_judgment_is_objective_evidence must be false")

    workspace = packet.get("workspace_projection") or {}
    for field in ["goal", "authority_boundary", "workspace_state", "next_action_contract"]:
        if field not in workspace:
            errors.append(f"workspace_projection missing {field}")

    authority = workspace.get("authority_boundary") or {}
    allowed = set(authority.get("allowed") or [])
    opened = sorted(allowed & DANGEROUS_ALLOWED)
    if opened:
        errors.append(f"dangerous authority listed as allowed: {opened}")

    dag = packet.get("evidence_dag") or {}
    claims = dag.get("claims") or []
    evidence = dag.get("evidence") or []
    claim_ids = _ids(claims)
    evidence_ids = _ids(evidence)
    if not claims:
        errors.append("evidence_dag.claims is empty")
    if not evidence:
        errors.append("evidence_dag.evidence is empty")

    evidence_by_id = {str(e.get("id")): e for e in evidence if e.get("id")}
    for e in evidence:
        auth = e.get("authority")
        if auth in MODEL_ONLY and e.get("status") == "verified":
            errors.append(f"model-only evidence cannot be verified objective evidence: {e.get('id')}")
        for c in e.get("supports") or []:
            if c not in claim_ids:
                errors.append(f"evidence {e.get('id')} supports unknown claim {c}")

    for c in claims:
        cid = c.get("id")
        if c.get("criticality") == "completion_critical" and c.get("status") == "verified":
            supporting = [e for e in evidence if cid in (e.get("supports") or [])]
            if not supporting:
                errors.append(f"verified completion-critical claim has no supporting evidence: {cid}")
            elif not any(e.get("authority") in OBJECTIVE_EVIDENCE and e.get("status") == "verified" for e in supporting):
                errors.append(f"completion-critical claim lacks objective verified evidence: {cid}")

    completion = packet.get("completion_claim_packet") or {}
    status = completion.get("status")
    if status not in ALLOWED_COMPLETION_STATUSES:
        errors.append(f"completion_claim_packet.status must be one of {sorted(ALLOWED_COMPLETION_STATUSES)}")
    neg = set(completion.get("negative_evidence") or [])
    missing_neg = sorted(REQUIRED_NEGATIVE_EVIDENCE - neg)
    if missing_neg:
        errors.append(f"completion packet missing negative evidence: {missing_neg}")
    for ref in completion.get("evidence_refs") or []:
        if ref not in evidence_ids:
            errors.append(f"completion evidence ref not found in evidence_dag: {ref}")
    if status == "verified_local" and completion.get("missing_evidence"):
        errors.append("verified_local completion cannot have missing_evidence")
    if status == "verified_local":
        for ref in completion.get("evidence_refs") or []:
            e = evidence_by_id.get(ref, {})
            if e.get("authority") in MODEL_ONLY:
                errors.append(f"verified_local completion uses model-only evidence: {ref}")

    if not completion.get("excluded_claims"):
        warnings.append("completion_claim_packet.excluded_claims is empty; consider recording what is not proven")

    result_status = "PASS" if not errors else "FAIL"
    return {
        "status": result_status,
        "schema": "workspace_projection_gate_v1",
        "errors": errors,
        "warnings": warnings,
        "claim_count": len(claims),
        "evidence_count": len(evidence),
        "policy": "local external projection only; no hidden-state access; no lifecycle/external authority granted",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a WorkspaceProjection packet")
    parser.add_argument("path")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    path = Path(args.path).expanduser()
    if not path.exists():
        print(json.dumps({"status": "ERROR", "error": f"not found: {path}"}, ensure_ascii=False, indent=2))
        return 2
    try:
        result = validate(load_packet(path))
    except Exception as exc:
        result = {"status": "ERROR", "error": repr(exc), "schema": "workspace_projection_gate_v1"}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
