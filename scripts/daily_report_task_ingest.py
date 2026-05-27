#!/usr/bin/env python3
"""Governed daily report -> taskpool ingestion bridge.

Consumes structured candidate sidecars emitted by daily report jobs and creates
explicitly-governed taskpool tasks via brain_task_orchestrator add.
Supports both Hermes-native PA reports and external browser-generated reports
(such as AIHOT / GitHub Trending) as long as they emit the governed sidecar
contract.
Fail-closed: missing governance metadata prevents creation.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
HERMES_HOME = SCRIPT_DIR.parent

REPORT_DIR = Path(os.environ.get("HERMES_PA_REPORT_DIR", str(HERMES_HOME / "notes" / "reports"))).expanduser()
STATE_PATH = Path(os.environ.get("HERMES_DAILY_REPORT_INGEST_STATE", str(HERMES_HOME / "state" / "daily_report_task_ingest_state.json"))).expanduser()
ORCH = Path(os.environ.get("HERMES_DAILY_REPORT_ORCH", str(SCRIPT_DIR / "brain_task_orchestrator.py"))).expanduser()

REQUIRED_FIELDS = {
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
ACTIVE_STATUSES = {"pending", "claimed", "running", "review", "blocked", "retry"}
CONTROL_PLANE_TARGETS = {
    "taskpool",
    "local-brain",
    "memory",
    "prompt",
    "prompts",
    "provider-quota",
    "provider-routing",
    "quota",
    "gateway",
    "browser-automation",
    "skill-graph",
    "skills",
    "hermes-agent",
    "control-plane",
}
SELF_STRENGTHENING_PREFIXES = (
    "control-plane",
    "self-strengthening",
    "evolution",
    "repo-intake",
    "daily-report:p1:external-signal-ingest",
)
MANUAL_DISPATCH_REQUESTS = Path(
    os.environ.get(
        "HERMES_DAILY_REPORT_MANUAL_REQUESTS",
        str(HERMES_HOME / "state" / "daily_report_manual_dispatch_requests.jsonl"),
    )
).expanduser()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {"seen_emissions": {}, "seen_dedupe_families": {}}
    try:
        data = load_json(STATE_PATH)
    except Exception:
        return {"seen_emissions": {}, "seen_dedupe_families": {}}
    if not isinstance(data, dict):
        return {"seen_emissions": {}, "seen_dedupe_families": {}}
    data.setdefault("seen_emissions", {})
    data.setdefault("seen_dedupe_families", {})
    return data


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def stable_dedupe_family(candidate: dict[str, Any]) -> str:
    """Return a cross-report duplicate key; report_id is intentionally excluded."""
    return str(candidate.get("dedupe_key") or candidate.get("title") or "").strip()


def is_multimodel_eligible(candidate: dict[str, Any]) -> bool:
    """Deterministic daily-report multimodel classifier.

    Daily/external sidecars are untrusted for expensive model spend: they may
    provide evidence, but only local structural rules may promote a candidate to
    a real multimodel contract.  Product/work candidates remain non-eligible by
    default even if the sidecar self-asserts requires_multimodel=true.
    """
    lane = str(candidate.get("lane") or "auto").strip().lower()
    priority = str(candidate.get("priority") or "").strip().upper()
    priority_layer = str(candidate.get("priority_layer") or "").strip().lower()
    architecture_target = str(candidate.get("architecture_target") or "").strip().lower()
    project = str(candidate.get("project") or "").strip().lower()
    concepts = csvify(candidate.get("concepts")).lower()
    title = str(candidate.get("title") or "").lower()
    structural_self_strengthening = (
        any(priority_layer.startswith(prefix) for prefix in SELF_STRENGTHENING_PREFIXES)
        or architecture_target in CONTROL_PLANE_TARGETS
        or project in {"hermes", "hermes-agent", "local-brain"}
        or "self-strengthening" in concepts
        or "skill-graph" in concepts
        or "任务池" in title
        or "taskpool" in title
    )
    if lane == "evolution":
        return structural_self_strengthening or priority in {"P0", "P1", "P2"}
    return priority in {"P0", "P1", "P2"} and structural_self_strengthening


def normalize_expected_participants(value: Any, *, eligible: bool) -> str:
    participants = [item for item in csvify(value).split(",") if item]
    if eligible and "claude-code" not in participants:
        participants.append("claude-code")
    # Preserve order while removing duplicates.
    deduped: list[str] = []
    for item in participants:
        if item not in deduped:
            deduped.append(item)
    return ",".join(deduped)


def normalize_multimodel_contract(candidate: dict[str, Any]) -> dict[str, Any]:
    eligible = is_multimodel_eligible(candidate)
    normalized = dict(candidate)
    if eligible:
        normalized["requires_multimodel"] = True
        normalized["expected_participants"] = normalize_expected_participants(candidate.get("expected_participants"), eligible=True)
        reason = str(candidate.get("multimodel_reason") or "").strip()
        normalized["multimodel_reason"] = reason or "daily-report-eligible-control-plane-or-self-strengthening-candidate; claude-code required in panel"
    else:
        normalized["requires_multimodel"] = False
        normalized["expected_participants"] = ""
        normalized["multimodel_reason"] = ""
    normalized["multimodel_eligible"] = eligible
    return normalized


def evidence_bundle_resolves(value: Any) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    # Local paths must exist.  Opaque report labels/URLs are allowed as provenance
    # but do not make an eligible task executable without a local bundle.
    if text.startswith(("http://", "https://", "url:")):
        return True
    if text.startswith("artifact:"):
        text = text[len("artifact:"):]
    path = Path(os.path.expanduser(text))
    return not path.is_absolute() or path.exists()


def record_manual_dispatch_request(candidate: dict[str, Any], reason: str, emission_key: str) -> None:
    MANUAL_DISPATCH_REQUESTS.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "kind": "daily_report_evidence_request",
        "emission_key": emission_key,
        "dedupe_key": candidate.get("dedupe_key", ""),
        "title": candidate.get("title", ""),
        "reason": reason,
        "manual_dispatch_gate": "tg:evidence_request",
        "evidence_bundle": candidate.get("evidence_bundle", ""),
    }
    with MANUAL_DISPATCH_REQUESTS.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False) + "\n")


def latest_sidecar() -> Path:
    candidates = sorted(REPORT_DIR.glob("pa-daily-*.tasks.json"))
    if not candidates:
        raise SystemExit(f"no daily report sidecar found under {REPORT_DIR}")
    return candidates[-1]


def csvify(value: Any) -> str:
    if isinstance(value, list):
        return ",".join(str(item).strip() for item in value if str(item).strip())
    return str(value or "").strip()


def normalize_candidate(report_payload: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    missing = sorted(field for field in REQUIRED_FIELDS if not candidate.get(field))
    if missing:
        raise ValueError(f"candidate missing required governance fields: {missing}")
    normalized = dict(candidate)
    normalized["report_id"] = candidate.get("report_id") or report_payload.get("report_id") or Path(report_payload.get("report_path", "report")).stem
    normalized["concepts"] = csvify(candidate.get("concepts"))
    normalized["dependency_order"] = csvify(candidate.get("dependency_order"))
    normalized["expected_participants"] = csvify(candidate.get("expected_participants"))
    normalized["acceptance_evidence"] = csvify(candidate.get("acceptance_evidence"))
    evidence_bundle = candidate.get("evidence_bundle")
    if isinstance(evidence_bundle, (dict, list)):
        normalized["evidence_bundle"] = json.dumps(evidence_bundle, ensure_ascii=False, sort_keys=True)
    else:
        normalized["evidence_bundle"] = csvify(evidence_bundle)
    return normalize_multimodel_contract(normalized)


def list_existing_active_titles() -> set[str]:
    env = os.environ.copy()
    cmd = [sys.executable, str(ORCH), "list", "--json"]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
    payload = json.loads(result.stdout)
    rows = payload.get("rows", [])
    return {
        str(row.get("title", "")).strip()
        for row in rows
        if str(row.get("status", "")).strip() in ACTIVE_STATUSES and str(row.get("title", "")).strip()
    }


def build_add_command(candidate: dict[str, Any]) -> list[str]:
    cmd = [
        sys.executable,
        str(ORCH),
        "add",
        candidate["title"],
        "--priority",
        candidate["priority"],
        "--project",
        candidate["project"],
        "--concepts",
        candidate["concepts"],
        "--priority-layer",
        candidate["priority_layer"],
        "--dependency-order",
        candidate["dependency_order"],
        "--multimodel-triage-result",
        candidate["multimodel_triage_result"],
        "--architecture-target",
        candidate.get("architecture_target", "") or "",
        "--capability-delta",
        candidate["capability_delta"],
        "--anti-drift-check",
        candidate["anti_drift_check"],
        "--acceptance-evidence",
        candidate["acceptance_evidence"],
        "--parallel-boundary",
        candidate["parallel_boundary"],
        "--objective",
        candidate["objective"],
        "--evidence-bundle",
        candidate["evidence_bundle"],
        "--truth-gate",
        candidate.get("truth_gate", "") or "",
        "--expected-participants",
        candidate.get("expected_participants", "") or "",
        "--multimodel-reason",
        candidate.get("multimodel_reason", "") or "",
        "--accept",
        candidate.get("accept", "Observable result is recorded in Proof Log."),
        "--json",
    ]
    if candidate.get("requires_multimodel"):
        cmd.append("--requires-multimodel")
    expires_days = candidate.get("expires_days")
    if expires_days is not None:
        cmd.extend(["--expires-days", str(expires_days)])
    lane = str(candidate.get("lane", "auto") or "auto")
    cmd.extend(["--lane", lane])
    return cmd


def create_task(candidate: dict[str, Any]) -> dict[str, Any]:
    result = subprocess.run(build_add_command(candidate), check=True, capture_output=True, text=True, env=os.environ.copy())
    return json.loads(result.stdout)


def process_payload(report_payload: dict[str, Any], write: bool) -> dict[str, Any]:
    state = load_state()
    existing_titles = list_existing_active_titles()
    report_id = str(report_payload.get("report_id") or Path(str(report_payload.get("report_path") or "report")).stem)
    actions: list[dict[str, Any]] = []

    for raw_candidate in report_payload.get("candidates", []):
        try:
            candidate = normalize_candidate(report_payload, raw_candidate)
        except Exception as exc:
            actions.append({"title": raw_candidate.get("title", ""), "status": "invalid", "reason": str(exc)})
            continue
        emission_key = f"{report_id}::{candidate['dedupe_key']}"
        dedupe_family = stable_dedupe_family(candidate)
        if emission_key in state["seen_emissions"]:
            actions.append({"title": candidate["title"], "status": "skipped", "reason": "already_emitted_for_report", "emission_key": emission_key})
            continue
        if dedupe_family and dedupe_family in state["seen_dedupe_families"]:
            actions.append({"title": candidate["title"], "status": "skipped", "reason": "repo_already_analyzed", "emission_key": emission_key, "dedupe_family": dedupe_family})
            continue
        if candidate["title"] in existing_titles:
            actions.append({"title": candidate["title"], "status": "skipped", "reason": "active_duplicate_title", "emission_key": emission_key})
            continue
        if candidate.get("multimodel_eligible") and not evidence_bundle_resolves(candidate.get("evidence_bundle")):
            reason = "eligible_multimodel_candidate_missing_local_evidence_bundle"
            if write:
                record_manual_dispatch_request(candidate, reason, emission_key)
                state["seen_emissions"][emission_key] = {"title": candidate["title"], "manual_dispatch_gate": "tg:evidence_request", "reason": reason}
            actions.append({"title": candidate["title"], "status": "blocked_evidence_request", "reason": reason, "emission_key": emission_key, "manual_dispatch_gate": "tg:evidence_request"})
            continue
        if not write:
            actions.append({"title": candidate["title"], "status": "dry_run", "emission_key": emission_key, "priority": candidate["priority"], "requires_multimodel": bool(candidate.get("requires_multimodel")), "expected_participants": csvify(candidate.get("expected_participants"))})
            continue
        created = create_task(candidate)
        state["seen_emissions"][emission_key] = {
            "title": candidate["title"],
            "created_task_id": created.get("id", ""),
            "created_task_path": created.get("created", ""),
        }
        if dedupe_family:
            state["seen_dedupe_families"][dedupe_family] = state["seen_emissions"][emission_key]
        actions.append({
            "title": candidate["title"],
            "status": "created",
            "emission_key": emission_key,
            "task_id": created.get("id", ""),
            "task_path": created.get("created", ""),
        })
    if write:
        save_state(state)
    return {
        "status": "OK",
        "write": write,
        "report_id": report_id,
        "proposal_count": len(report_payload.get("candidates", [])),
        "actions": actions,
        "created_count": sum(1 for item in actions if item.get("status") == "created"),
        "skipped_count": sum(1 for item in actions if item.get("status") == "skipped"),
        "invalid_count": sum(1 for item in actions if item.get("status") == "invalid"),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Governed daily report -> taskpool ingestion")
    parser.add_argument("--proposal-json", default="", help="Path to a *.tasks.json sidecar. Omit to use the latest Hermes-native pa-daily sidecar.")
    parser.add_argument("--write", action="store_true", help="Create tasks instead of dry-run preview.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON result.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    proposal_path = Path(args.proposal_json).expanduser() if args.proposal_json else latest_sidecar()
    payload = load_json(proposal_path)
    if payload.get("schema") != "daily_report_task_candidates_v1":
        raise SystemExit(f"unsupported proposal schema: {payload.get('schema')!r}")
    result = process_payload(payload, write=bool(args.write))
    result["proposal_path"] = str(proposal_path)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"daily_report_task_ingest: report={result['report_id']} write={result['write']} created={result['created_count']} skipped={result['skipped_count']} invalid={result['invalid_count']}")
        for item in result["actions"]:
            detail = item.get("reason") or item.get("task_id") or ""
            print(f"- {item['status']}: {item.get('title', '')} ({detail})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
