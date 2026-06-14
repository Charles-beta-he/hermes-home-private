#!/usr/bin/env python3
"""Agent/Web3 internal security self-check evaluator.

This is a local, no-network evaluator for ERC-8126-inspired internal self-check
reports. It does not claim ERC-8126 certification, does not scan targets, and
does not perform external side effects. It validates a JSON report shape and
computes a final risk level from hard kill-switch findings plus per-dimension
0-100 scores.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

DIMENSIONS = [
    "identity",
    "web_api",
    "contract_wallet",
    "code_supply_chain",
    "agent_permissions",
    "data_privacy",
    "media_authenticity",
    "ops_incident_response",
]

KILL_SWITCH_IDS = {
    "secret_leak",
    "unauthorized_asset_transfer_path",
    "undisclosed_asset_seizure_authority",
    "rce_or_unauth_admin_or_sensitive_data_exposure",
    "audit_target_mismatch",
    "ungated_high_risk_agent_action",
}

RISK_ORDER = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}


def score_to_risk(score: int) -> str:
    if score <= 20:
        return "Low"
    if score <= 40:
        return "Medium"
    if score <= 70:
        return "High"
    return "Critical"


def max_risk(*risks: str) -> str:
    return max(risks, key=lambda r: RISK_ORDER[r])


def _err(errors: List[str], msg: str) -> None:
    errors.append(msg)


def validate_report(report: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    if report.get("schema") != "agent_web3_security_selfcheck_v0_1":
        _err(errors, "schema must be agent_web3_security_selfcheck_v0_1")

    meta = report.get("metadata")
    if not isinstance(meta, dict):
        _err(errors, "metadata object is required")
    else:
        for key in ["project", "scope", "internal_only"]:
            if key not in meta:
                _err(errors, f"metadata.{key} is required")
        if meta.get("internal_only") is not True:
            _err(errors, "metadata.internal_only must be true; this tool is not an external certification")
        if meta.get("claims_external_certification"):
            _err(errors, "external certification/self-attestation claim is forbidden")

    dims = report.get("dimensions")
    if not isinstance(dims, dict):
        _err(errors, "dimensions object is required")
    else:
        for dim in DIMENSIONS:
            item = dims.get(dim)
            if not isinstance(item, dict):
                _err(errors, f"dimensions.{dim} object is required")
                continue
            score = item.get("score")
            if not isinstance(score, int) or score < 0 or score > 100:
                _err(errors, f"dimensions.{dim}.score must be integer 0..100")
            evidence = item.get("evidence")
            if not isinstance(evidence, list) or not evidence:
                _err(errors, f"dimensions.{dim}.evidence must be a non-empty list")
            status = item.get("status")
            if status not in {"pass", "warn", "fail", "not_applicable"}:
                _err(errors, f"dimensions.{dim}.status must be pass|warn|fail|not_applicable")
            if item.get("assumptions") and not isinstance(item.get("assumptions"), list):
                _err(errors, f"dimensions.{dim}.assumptions must be a list when present")

    kill = report.get("kill_switch_findings", [])
    if not isinstance(kill, list):
        _err(errors, "kill_switch_findings must be a list")
    else:
        for idx, finding in enumerate(kill):
            if not isinstance(finding, dict):
                _err(errors, f"kill_switch_findings[{idx}] must be object")
                continue
            fid = finding.get("id")
            if fid not in KILL_SWITCH_IDS:
                _err(errors, f"kill_switch_findings[{idx}].id is unknown: {fid!r}")
            if finding.get("severity") not in {"High", "Critical"}:
                _err(errors, f"kill_switch_findings[{idx}].severity must be High or Critical")
            if not finding.get("evidence"):
                _err(errors, f"kill_switch_findings[{idx}].evidence is required")

    if not report.get("report_template_filled"):
        warnings.append("report_template_filled is missing/false; report may be incomplete for human review")

    return errors, warnings


def evaluate(report: Dict[str, Any]) -> Dict[str, Any]:
    errors, warnings = validate_report(report)
    if errors:
        return {"status": "INVALID", "errors": errors, "warnings": warnings}

    dims = report["dimensions"]
    per_dimension = {}
    final_risk = "Low"
    for dim in DIMENSIONS:
        score = dims[dim]["score"]
        risk = score_to_risk(score)
        if dims[dim].get("status") == "fail":
            risk = max_risk(risk, "High")
        per_dimension[dim] = {
            "score": score,
            "risk": risk,
            "status": dims[dim]["status"],
            "evidence_count": len(dims[dim].get("evidence", [])),
        }
        final_risk = max_risk(final_risk, risk)

    kill_findings = report.get("kill_switch_findings", [])
    for finding in kill_findings:
        final_risk = max_risk(final_risk, finding["severity"])

    return {
        "status": "PASS",
        "final_risk": final_risk,
        "risk_model": "kill-switch-max-plus-per-dimension; no average final risk",
        "external_certification": False,
        "kill_switch_count": len(kill_findings),
        "per_dimension": per_dimension,
        "warnings": warnings,
    }


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("report", help="Path to self-check report JSON")
    ap.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = ap.parse_args(argv)

    try:
        data = json.loads(Path(args.report).read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - CLI guard
        print(json.dumps({"status": "INVALID", "errors": [f"cannot read/parse report: {exc}"]}, ensure_ascii=False))
        return 2

    result = evaluate(data)
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
