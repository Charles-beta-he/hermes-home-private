#!/usr/bin/env python3
"""Product workflow workspace -> governed taskpool ingest bridge.

This is a thin, fail-closed adapter from the product workflow operating
system's workspace shape into the existing daily_report_task_ingest.py bridge.
It validates local workspace artifacts, normalizes relative evidence paths,
and delegates actual task creation to the canonical taskpool ingest script.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))).expanduser()
WORKFLOW_ROOT = HERMES_HOME / "workflows" / "product"
INGEST = HERMES_HOME / "scripts" / "daily_report_task_ingest.py"

REQUIRED_CANDIDATE_FIELDS = {
    "dedupe_key",
    "title",
    "priority",
    "project",
    "concepts",
    "priority_layer",
    "dependency_order",
    "multimodel_triage_result",
    "objective",
    "capability_delta",
    "anti_drift_check",
    "acceptance_evidence",
    "parallel_boundary",
    "evidence_bundle",
}
PLACEHOLDER_CHARS = ("<", ">")
VALID_WORKFLOW_STAGES = {"", "evidence", "execute", "review", "writeback", "human_gate", "done"}
VALID_COMPLETION_BOUNDARIES = {"", "document_only", "taskpool_candidate", "implementation_ready", "shipping_packet", "launched_observing"}
VALID_HARNESS_SURFACES = {"command", "ui", "api", "browser", "security", "performance", "metrics"}


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"failed to load JSON {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"JSON root must be object: {path}")
    return data


def resolve_workspace(args: argparse.Namespace) -> Path:
    if args.workspace:
        path = Path(args.workspace).expanduser()
    elif args.slug:
        path = WORKFLOW_ROOT / args.slug
    else:
        raise SystemExit("provide --workspace or --slug")
    path = path.resolve()
    if not path.exists() or not path.is_dir():
        raise SystemExit(f"workspace not found: {path}")
    return path


def has_placeholder(value: Any) -> bool:
    if isinstance(value, str):
        return any(ch in value for ch in PLACEHOLDER_CHARS)
    if isinstance(value, list):
        return any(has_placeholder(item) for item in value)
    if isinstance(value, dict):
        return any(has_placeholder(v) for v in value.values())
    return False


def csv_items(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [item.strip() for item in str(value or "").split(",") if item.strip()]


def boolify(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def normalize_candidate_optional_fields(candidate: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(candidate)
    for field in ("harness_surfaces", "required_artifacts"):
        if field in normalized:
            normalized[field] = csv_items(normalized.get(field))
    if "external_side_effects" in normalized:
        normalized["external_side_effects"] = boolify(normalized.get("external_side_effects"))
    return normalized


def normalize_evidence_bundle(value: Any, workspace: Path) -> Any:
    """Resolve relative local evidence refs against the workspace.

    Preserve URLs and structured values.  For comma/list strings, return a list
    if multiple refs exist; daily_report_task_ingest accepts lists and will
    serialize them deterministically.
    """
    if isinstance(value, (dict, list)) and not all(isinstance(x, str) for x in value if isinstance(value, list)):
        return value
    items = csv_items(value)
    normalized: list[str] = []
    for item in items:
        if item.startswith(("http://", "https://", "url:", "artifact:")):
            if item.startswith("artifact:"):
                raw = item[len("artifact:") :]
                p = Path(raw).expanduser()
                if not p.is_absolute():
                    p = workspace / raw
                normalized.append("artifact:" + str(p))
            else:
                normalized.append(item)
            continue
        p = Path(item).expanduser()
        if not p.is_absolute():
            p = workspace / item
        normalized.append(str(p))
    return normalized[0] if len(normalized) == 1 else normalized


def validate_candidate(candidate: dict[str, Any], index: int) -> list[str]:
    errors: list[str] = []
    missing = sorted(field for field in REQUIRED_CANDIDATE_FIELDS if not candidate.get(field))
    if missing:
        errors.append(f"candidate[{index}] missing required fields: {missing}")
    if has_placeholder(candidate):
        errors.append(f"candidate[{index}] contains template placeholders; edit it before ingest")
    priority = str(candidate.get("priority") or "").upper()
    if priority and priority not in {"P0", "P1", "P2", "P3"}:
        errors.append(f"candidate[{index}] invalid priority: {priority}")
    workflow_stage = str(candidate.get("workflow_stage") or "").strip()
    if workflow_stage not in VALID_WORKFLOW_STAGES:
        errors.append(f"candidate[{index}] invalid workflow_stage: {workflow_stage}")
    completion_boundary = str(candidate.get("completion_boundary") or "").strip()
    if completion_boundary not in VALID_COMPLETION_BOUNDARIES:
        errors.append(f"candidate[{index}] invalid completion_boundary: {completion_boundary}")
    harness_surfaces = set(csv_items(candidate.get("harness_surfaces")))
    invalid_surfaces = sorted(harness_surfaces - VALID_HARNESS_SURFACES)
    if invalid_surfaces:
        errors.append(f"candidate[{index}] invalid harness_surfaces: {invalid_surfaces}")
    return errors


def build_payload(workspace: Path) -> tuple[dict[str, Any], list[str]]:
    evidence_path = workspace / "evidence" / "evidence-bundle.json"
    candidates_path = workspace / "tasks" / "task-candidates.json"
    state_path = workspace / "workflow-state.yaml.md"
    intent_path = workspace / "00-intake" / "intent-card.md"

    required_paths = [evidence_path, candidates_path, state_path, intent_path]
    missing_paths = [str(p) for p in required_paths if not p.exists()]
    if missing_paths:
        raise SystemExit(f"workspace missing required artifacts: {missing_paths}")

    evidence = load_json(evidence_path)
    candidates_payload = load_json(candidates_path)
    if candidates_payload.get("schema") != "daily_report_task_candidates_v1":
        raise SystemExit(f"unsupported task candidate schema: {candidates_payload.get('schema')!r}")
    candidates = candidates_payload.get("candidates", [])
    if not isinstance(candidates, list):
        raise SystemExit("task candidate payload field 'candidates' must be a list")

    errors: list[str] = []
    normalized_candidates: list[dict[str, Any]] = []
    for idx, raw in enumerate(candidates):
        if not isinstance(raw, dict):
            errors.append(f"candidate[{idx}] must be object")
            continue
        candidate = normalize_candidate_optional_fields(raw)
        candidate["evidence_bundle"] = normalize_evidence_bundle(candidate.get("evidence_bundle"), workspace)
        errors.extend(validate_candidate(candidate, idx))
        normalized_candidates.append(candidate)

    report_id = str(candidates_payload.get("report_id") or candidates_payload.get("workflow_slug") or workspace.name)
    payload = {
        "schema": "daily_report_task_candidates_v1",
        "report_id": report_id,
        "report_path": str(workspace / "workflow-state.yaml.md"),
        "source": candidates_payload.get("source") or "product-workflow-operating-system",
        "workflow_slug": candidates_payload.get("workflow_slug") or workspace.name,
        "workspace_path": str(workspace),
        "evidence_bundle_path": str(evidence_path),
        "evidence_schema": evidence.get("schema"),
        "candidates": normalized_candidates,
    }
    return payload, errors


def run_ingest(proposal_path: Path, *, write: bool) -> dict[str, Any]:
    cmd = [sys.executable, str(INGEST), "--proposal-json", str(proposal_path), "--json"]
    if write:
        cmd.append("--write")
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest product workflow task candidates into the governed taskpool bridge")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--workspace", help="Path to a product workflow workspace")
    group.add_argument("--slug", help="Workspace slug under ~/.hermes/workflows/product")
    parser.add_argument("--write", action="store_true", help="Create tasks through the canonical ingest bridge")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument("--proposal-out", help="Override normalized proposal output path")
    parser.add_argument("--allow-empty", action="store_true", help="Return OK when there are no candidates")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workspace = resolve_workspace(args)
    payload, errors = build_payload(workspace)
    proposal_path = Path(args.proposal_out).expanduser() if args.proposal_out else workspace / "tasks" / ".product-workflow-ingest-proposal.json"

    if errors:
        result = {
            "status": "INVALID",
            "write": bool(args.write),
            "workspace": str(workspace),
            "proposal_path": str(proposal_path),
            "errors": errors,
            "proposal_count": len(payload.get("candidates", [])),
        }
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 2
        raise SystemExit("; ".join(errors))

    if not payload.get("candidates") and not args.allow_empty:
        result = {
            "status": "NO_CANDIDATES",
            "write": bool(args.write),
            "workspace": str(workspace),
            "proposal_path": str(proposal_path),
            "proposal_count": 0,
        }
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        print("product_workflow_taskpool_ingest: no candidates")
        return 0

    proposal_path.parent.mkdir(parents=True, exist_ok=True)
    proposal_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if not payload.get("candidates"):
        result = {
            "status": "OK",
            "write": bool(args.write),
            "workspace": str(workspace),
            "proposal_path": str(proposal_path),
            "proposal_count": 0,
            "created_count": 0,
            "skipped_count": 0,
            "invalid_count": 0,
            "actions": [],
        }
    else:
        result = run_ingest(proposal_path, write=bool(args.write))
        result["workspace"] = str(workspace)
        result["normalized_proposal_path"] = str(proposal_path)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"product_workflow_taskpool_ingest: status={result.get('status')} write={result.get('write')} "
            f"created={result.get('created_count', 0)} skipped={result.get('skipped_count', 0)} invalid={result.get('invalid_count', 0)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
