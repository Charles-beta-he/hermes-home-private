#!/usr/bin/env python3
"""Validate Hermes project scaffold matrix JSON specs.

Stdlib-only v0 validator. It intentionally lives outside Hermes core so the
matrix can stabilize through docs/fixtures before becoming a CLI feature.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

TASK_RUNNERS = {"vite", "turborepo", "nx", "pnpm", "npm", "bun"}
MUTUALLY_EXCLUSIVE_TASK_RUNNERS = {"vite", "turborepo", "nx"}
WORKERS_COMPATIBLE_BACKENDS = {"hono", "none"}
KNOWN_SURFACES = {
    "web_frontend",
    "mobile_pwa",
    "backend_api",
    "cloudflare_pages",
    "cloudflare_workers",
    "mcp",
    "skills",
    "browser_harness",
    "evidence_proof_gate",
}


def err(rule_id: str, message: str, path: str) -> Dict[str, str]:
    return {"rule_id": rule_id, "message": message, "path": path}


def warn(rule_id: str, message: str, path: str) -> Dict[str, str]:
    return {"rule_id": rule_id, "message": message, "path": path}


def as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def load_spec(path: str | None) -> Dict[str, Any]:
    if path in (None, "-"):
        return json.load(sys.stdin)
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def validate(spec: Dict[str, Any]) -> Dict[str, Any]:
    errors: List[Dict[str, str]] = []
    warnings: List[Dict[str, str]] = []

    if not isinstance(spec, dict):
        return {
            "valid": False,
            "errors": [err("schema.root_object", "spec must be a JSON object", "$")],
            "warnings": [],
            "proof_plan": [],
        }

    project_name = spec.get("project_name")
    if not isinstance(project_name, str) or not project_name.strip():
        errors.append(err("schema.project_name.required", "project_name must be a non-empty string", "$.project_name"))

    surfaces = as_list(spec.get("surfaces"))
    if not surfaces:
        errors.append(err("schema.surfaces.required", "surfaces must list at least one scaffold capability", "$.surfaces"))
    unknown_surfaces = sorted(str(s) for s in surfaces if s not in KNOWN_SURFACES)
    if unknown_surfaces:
        warnings.append(warn("schema.surfaces.unknown", "unknown surfaces are advisory in v0: " + ", ".join(unknown_surfaces), "$.surfaces"))

    frontend = spec.get("frontend") or {}
    backend = spec.get("backend") or {}
    cloudflare = spec.get("cloudflare") or {}
    addons = set(str(a) for a in as_list(spec.get("addons")))

    if "web_frontend" in surfaces and not frontend:
        errors.append(err("surface.web_frontend.frontend_required", "web_frontend surface requires a frontend object", "$.frontend"))
    if "mobile_pwa" in surfaces:
        if not frontend:
            errors.append(err("surface.mobile_pwa.frontend_required", "mobile_pwa surface requires a frontend object", "$.frontend"))
        elif frontend.get("pwa") is not True:
            errors.append(err("surface.mobile_pwa.pwa_required", "mobile_pwa surface requires frontend.pwa=true", "$.frontend.pwa"))
    if "backend_api" in surfaces and not backend:
        errors.append(err("surface.backend_api.backend_required", "backend_api surface requires a backend object", "$.backend"))

    task_runners = [str(x) for x in as_list(frontend.get("task_runner"))]
    unknown_runners = sorted(set(task_runners) - TASK_RUNNERS)
    if unknown_runners:
        warnings.append(warn("frontend.task_runner.unknown", "unknown task runner(s): " + ", ".join(unknown_runners), "$.frontend.task_runner"))
    exclusive = sorted(set(task_runners) & MUTUALLY_EXCLUSIVE_TASK_RUNNERS)
    if len(exclusive) > 1:
        errors.append(err(
            "frontend.task_runner.mutual_exclusion",
            "choose at most one orchestration/build task runner from: " + ", ".join(sorted(MUTUALLY_EXCLUSIVE_TASK_RUNNERS)),
            "$.frontend.task_runner",
        ))

    workers_enabled = bool(cloudflare.get("workers")) or backend.get("runtime") == "workers" or "cloudflare_workers" in surfaces
    pages_enabled = bool(cloudflare.get("pages")) or "cloudflare_pages" in surfaces
    if workers_enabled:
        framework = str(backend.get("framework", "none"))
        if framework not in WORKERS_COMPATIBLE_BACKENDS:
            errors.append(err(
                "cloudflare.workers.backend_runtime",
                "Cloudflare Workers runtime v0 supports only Hono/no custom backend; got framework=" + framework,
                "$.backend.framework",
            ))
        if backend and backend.get("runtime") not in ("workers", "workerd", None):
            errors.append(err(
                "cloudflare.workers.runtime",
                "cloudflare.workers requires backend.runtime='workers' or 'workerd' when backend is present",
                "$.backend.runtime",
            ))
    if pages_enabled and not frontend:
        errors.append(err("cloudflare.pages.frontend_required", "Cloudflare Pages requires a frontend surface/object", "$.frontend"))

    if "mcp" in addons:
        mcp = spec.get("mcp") or {}
        if not as_list(mcp.get("servers")):
            errors.append(err("addon.mcp.servers_required", "mcp addon requires mcp.servers with at least one server id", "$.mcp.servers"))
    if "skills" in addons:
        skills = spec.get("skills") or {}
        if not as_list(skills.get("names")):
            errors.append(err("addon.skills.names_required", "skills addon requires skills.names with at least one skill", "$.skills.names"))
    if "browser_harness" in addons:
        harness = spec.get("browser_harness") or {}
        viewports = set(str(v) for v in as_list(harness.get("viewports")))
        if not viewports:
            errors.append(err("addon.browser_harness.viewports_required", "browser_harness addon requires browser_harness.viewports", "$.browser_harness.viewports"))
        elif not ({"desktop_1280", "mobile_375"} & viewports):
            warnings.append(warn("addon.browser_harness.viewport_coverage", "include desktop_1280 and/or mobile_375 for Hermes browser proof parity", "$.browser_harness.viewports"))

    proof_gate = spec.get("proof_gate") or {}
    if proof_gate.get("required") is not True:
        errors.append(err("proof_gate.required", "proof_gate.required must be true; scaffold completion needs evidence", "$.proof_gate.required"))
    commands = [str(c) for c in as_list(proof_gate.get("commands")) if str(c).strip()]
    evidence = [str(e) for e in as_list(proof_gate.get("evidence")) if str(e).strip()]
    if not commands:
        errors.append(err("proof_gate.commands.required", "proof_gate.commands must include at least one verification command", "$.proof_gate.commands"))
    if not evidence:
        errors.append(err("proof_gate.evidence.required", "proof_gate.evidence must include at least one evidence artifact", "$.proof_gate.evidence"))
    if "validator_json" not in evidence:
        warnings.append(warn("proof_gate.validator_json.recommended", "include validator_json so downstream taskpool/kanban can consume structured proof", "$.proof_gate.evidence"))
    if workers_enabled and "workers_smoke" not in evidence:
        warnings.append(warn("proof_gate.workers_smoke.recommended", "Cloudflare Workers stacks should include workers_smoke evidence before write/merge", "$.proof_gate.evidence"))
    if pages_enabled and "browser_smoke" not in evidence:
        warnings.append(warn("proof_gate.browser_smoke.recommended", "Cloudflare Pages/web stacks should include browser_smoke evidence", "$.proof_gate.evidence"))

    proof_plan = build_proof_plan(spec, commands, evidence, workers_enabled, pages_enabled)
    return {"valid": not errors, "errors": errors, "warnings": warnings, "proof_plan": proof_plan}


def build_proof_plan(spec: Dict[str, Any], commands: List[str], evidence: List[str], workers_enabled: bool, pages_enabled: bool) -> List[Dict[str, Any]]:
    plan: List[Dict[str, Any]] = [
        {"tier": 0, "name": "schema_and_matrix_validation", "required": True, "evidence": ["validator_json"]},
        {"tier": 0, "name": "dry_run_manifest_review", "required": True, "evidence": ["file_manifest", "reproducible_spec"]},
    ]
    if commands:
        plan.append({"tier": 1, "name": "declared_verification_commands", "required": True, "commands": commands})
    if pages_enabled or spec.get("frontend"):
        plan.append({"tier": 1, "name": "browser_harness_smoke", "required": pages_enabled, "evidence": ["browser_smoke"]})
    if workers_enabled:
        plan.append({"tier": 1, "name": "cloudflare_workers_smoke", "required": True, "evidence": ["workers_smoke"]})
    if spec.get("proof_gate", {}).get("review_required", True):
        plan.append({"tier": 2, "name": "human_review_gate", "required": True, "evidence": ["review_comment_or_approval"]})
    if evidence:
        plan.append({"tier": 2, "name": "evidence_bundle", "required": True, "evidence": sorted(set(evidence))})
    return plan


def check_fixtures(root: Path) -> Tuple[bool, List[Dict[str, Any]]]:
    results: List[Dict[str, Any]] = []
    ok = True
    for expected_valid, subdir in ((True, "valid"), (False, "invalid")):
        for path in sorted((root / subdir).glob("*.json")):
            result = validate(json.loads(path.read_text(encoding="utf-8")))
            passed = result["valid"] is expected_valid
            ok = ok and passed
            results.append({
                "fixture": str(path),
                "expected_valid": expected_valid,
                "actual_valid": result["valid"],
                "passed": passed,
                "errors": result["errors"],
                "warnings": result["warnings"],
            })
    return ok, results


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a Hermes project scaffold matrix JSON spec.")
    parser.add_argument("spec", nargs="?", help="JSON spec path, or '-' / omitted for stdin")
    parser.add_argument("--check-fixtures", metavar="DIR", help="Validate fixtures under DIR/{valid,invalid}/*.json")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.check_fixtures:
        ok, results = check_fixtures(Path(args.check_fixtures))
        output = {"valid": ok, "errors": [] if ok else [err("fixtures.failed", "one or more fixtures did not match expected validity", args.check_fixtures)], "warnings": [], "proof_plan": [], "fixtures": results}
        print(json.dumps(output, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
        return 0 if ok else 1

    try:
        result = validate(load_spec(args.spec))
    except (OSError, json.JSONDecodeError) as exc:
        result = {"valid": False, "errors": [err("input.read_or_parse_failed", str(exc), args.spec or "-")], "warnings": [], "proof_plan": []}
    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
