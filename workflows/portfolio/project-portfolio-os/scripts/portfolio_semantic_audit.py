#!/usr/bin/env python3
"""Portfolio semantic audit.

Local-only semantic/evidence verifier for project profiles. This complements
portfolio_doctor.py: doctor proves structural registry/profile/path alignment;
this script proves the declared audit dimensions are covered with current
readback, verdict, known gaps, and next action.
"""
from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HERMES_HOME = ROOT.parents[2]
REGISTRY = ROOT / "01-registry" / "portfolio-registry.json"
PROFILE_DIR = HERMES_HOME / "project-profiles"

HIGH_MATURITY_TOKENS = ("validated", "promoted", "production", "released", "complete", "done")
NEGATIVE_TOKENS = ("unverified", "missing", "needs-evidence", "not_validated", "not-started", "not_started")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def project_id(path: Path, payload: dict[str, Any]) -> str:
    return str(payload.get("id") or payload.get("project") or payload.get("project_id") or path.stem)


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def declared_evidence(profile: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for key in ("evidence", "portfolio_evidence", "verification_evidence"):
        value = profile.get(key)
        for item in as_list(value):
            if isinstance(item, str):
                out.append(item)
            elif isinstance(item, dict):
                path = item.get("path") or item.get("evidence") or item.get("file")
                if isinstance(path, str):
                    out.append(path)
    return out


def path_exists(path: str) -> bool:
    return path.startswith("/") and Path(path).exists()


def parse_date(value: Any) -> date | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def newest_mtime(paths: list[str]) -> str | None:
    mtimes: list[datetime] = []
    for item in paths:
        if path_exists(item):
            try:
                mtimes.append(datetime.fromtimestamp(Path(item).stat().st_mtime, tz=timezone.utc))
            except OSError:
                continue
    if not mtimes:
        return None
    return max(mtimes).isoformat()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on-warning", action="store_true")
    args = parser.parse_args()

    findings: list[dict[str, Any]] = []
    dimensions: list[dict[str, Any]] = []
    registry = load_json(REGISTRY)
    registry_entries = {str(p.get("id")): p for p in registry.get("projects", []) if isinstance(p, dict)}

    for path in sorted(PROFILE_DIR.glob("*.json")):
        try:
            profile = load_json(path)
        except Exception as exc:
            findings.append({"severity": "error", "project": path.stem, "check": "profile_json", "message": f"{type(exc).__name__}: {exc}", "path": str(path)})
            continue
        if not isinstance(profile, dict):
            findings.append({"severity": "error", "project": path.stem, "check": "profile_shape", "message": "profile must be an object", "path": str(path)})
            continue
        pid = project_id(path, profile)
        status = str(profile.get("status") or registry_entries.get(pid, {}).get("status") or "")
        components = profile.get("current_components")
        evidence = declared_evidence(profile)
        existing_evidence = [e for e in evidence if path_exists(e)]
        execution_policy = str(profile.get("execution_policy") or "")
        excluded = "excluded-unless-user-switches" in status or "excluded-unless-user-switches" in execution_policy
        raw_semantic = profile.get("audit_semantics")
        semantic: dict[str, Any] = raw_semantic if isinstance(raw_semantic, dict) else {}

        project_findings: list[dict[str, Any]] = []
        if not isinstance(components, dict) or not components:
            severity = "info" if excluded or semantic.get("intentionally_minimal_profile") else "warning"
            project_findings.append({"severity": severity, "check": "current_components", "message": "current_components is empty or missing"})
        if evidence:
            missing = [e for e in evidence if e.startswith("/") and not Path(e).exists()]
            if missing:
                project_findings.append({"severity": "warning", "check": "declared_evidence_exists", "message": f"{len(missing)} declared evidence paths missing", "missing": missing[:5]})
        high_claim = any(token in status.lower() for token in HIGH_MATURITY_TOKENS)
        negative_claim = any(token in status.lower() for token in NEGATIVE_TOKENS)
        if high_claim and not negative_claim and not existing_evidence:
            project_findings.append({"severity": "warning", "check": "maturity_claim_evidence", "message": "high-maturity status requires at least one existing declared evidence path"})
        if negative_claim and high_claim:
            project_findings.append({"severity": "warning", "check": "status_semantic_conflict", "message": "status mixes high-maturity and negative evidence tokens"})
        if excluded and not semantic.get("work_project_exemption"):
            project_findings.append({"severity": "warning", "check": "work_project_exemption", "message": "excluded work project should declare audit_semantics.work_project_exemption"})
        if excluded and semantic.get("work_project_exemption"):
            if not semantic.get("exemption_reason"):
                project_findings.append({"severity": "warning", "check": "exemption_reason", "message": "work-project exemption needs an explicit reason"})
            review_after = parse_date(semantic.get("exemption_review_after"))
            if review_after is None:
                project_findings.append({"severity": "warning", "check": "exemption_review_after", "message": "work-project exemption needs ISO review date"})
            elif review_after < date.today():
                project_findings.append({"severity": "warning", "check": "exemption_review_after", "message": f"work-project exemption review date is past: {review_after.isoformat()}"})
        freshness_days = semantic.get("evidence_freshness_days")
        if freshness_days is not None and (not isinstance(freshness_days, int) or freshness_days <= 0):
            project_findings.append({"severity": "warning", "check": "evidence_freshness_days", "message": "evidence_freshness_days must be a positive integer when declared"})

        for f in project_findings:
            item = {"project": pid, **f, "path": str(path)}
            findings.append(item)

        err = sum(1 for f in project_findings if f["severity"] == "error")
        warn = sum(1 for f in project_findings if f["severity"] == "warning")
        verdict = "fail" if err else "warn" if warn else "pass"
        gaps = [f"{f['severity']}:{f['check']}" for f in project_findings if f["severity"] in {"error", "warning"}]
        dimensions.append({
            "id": pid,
            "coverage_status": "covered_by_current_readback",
            "verdict": verdict,
            "evidence": [str(path), str(profile.get("progress_ledger") or ""), *existing_evidence],
            "evidence_freshness": {
                "policy_days": semantic.get("evidence_freshness_days"),
                "newest_declared_evidence_mtime": newest_mtime(existing_evidence),
                "note": "freshness is advisory unless a project-specific gate restores validated/promoted status",
            },
            "work_project_exemption": {
                "active": bool(excluded and semantic.get("work_project_exemption")),
                "review_after": semantic.get("exemption_review_after"),
            },
            "known_gaps": gaps or ["none"],
            "next_action": semantic.get("next_audit_action") or ("resolve warnings before portfolio PASS" if warn else "keep evidence current"),
        })

    errors = sum(1 for f in findings if f["severity"] == "error")
    warnings = sum(1 for f in findings if f["severity"] == "warning")
    covered = sum(1 for d in dimensions if d.get("evidence") and d.get("verdict") and d.get("known_gaps") and d.get("next_action"))
    ok = errors == 0 and (warnings == 0 or not args.fail_on_warning) and covered == len(dimensions)
    payload = {
        "schema": "portfolio_semantic_audit_v1",
        "definition": "100% coverage means every declared project dimension has current local readback, verdict, known gaps, and next action. It does not mean every project is healthy or production-ready.",
        "ok": ok,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "registry": str(REGISTRY),
        "profile_dir": str(PROFILE_DIR),
        "coverage_percent": round((covered / len(dimensions) * 100) if dimensions else 100, 2),
        "dimension_count": len(dimensions),
        "covered_dimension_count": covered,
        "counts": {"error": errors, "warning": warnings, "info": sum(1 for f in findings if f["severity"] == "info")},
        "findings": findings,
        "dimensions": dimensions,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
