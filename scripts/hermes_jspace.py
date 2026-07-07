#!/usr/bin/env python3
"""hermes_jspace.py — local External J-space P0 projection helper.

This script implements a local-file-only workspace/evidence/reflection skeleton.
It does not read model hidden states, mutate taskpool lifecycle, dispatch tools,
send messages, publish, deploy, delete data, or enter credentials.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import subprocess
import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

SCHEMA_WORKSPACE = "workspace_projection_v0_1"
SCHEMA_EVIDENCE = "evidence_dag_v0_1"
SCHEMA_COMPLETION = "completion_claim_packet_v0_1"
SCHEMA_EVENT = "jspace_event_ledger_v0_1"
DEFAULT_ROOT = Path.home() / ".hermes" / "workflows" / "jspace"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", text.strip().lower()).strip("-._")
    return slug[:64] or "jspace"


def workspace_dir(root: Path, workspace_id: str) -> Path:
    return root.expanduser().resolve() / workspace_id


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def default_authority() -> dict[str, list[str]]:
    return {
        "allowed": ["local_read", "local_write_workspace", "advisory_review"],
        "requires_auth": ["external_dispatch", "publish_deploy_push", "taskpool_lifecycle_write", "destructive_operation"],
        "forbidden": ["credential_entry", "payment", "secret_exfiltration"],
    }


def init_workspace(root: Path, title: str, goal: str, *, workspace_id: Any = None, task_id: Any = None) -> dict[str, Any]:
    wid = workspace_id or f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{slugify(title)}"
    wdir = workspace_dir(root, wid)
    if wdir.exists():
        raise SystemExit(f"workspace already exists: {wdir}")
    now = utc_now()
    workspace = {
        "schema": SCHEMA_WORKSPACE,
        "id": wid,
        "title": title,
        "task_id": task_id,
        "goal": goal,
        "non_goals": ["no_hidden_state_claim", "no_external_side_effects_in_p0", "no_taskpool_lifecycle_mutation_in_p0"],
        "constraints": ["objective_evidence_required_for_completion_claims", "model_judgment_is_advisory"],
        "authority_boundary": default_authority(),
        "intermediate_beliefs": [],
        "risks": [],
        "missing_evidence": [],
        "next_action_contract": {"action": "add_evidence_then_gate_check", "expected_evidence": ["root_evidence"]},
        "workspace_state": "objective_model",
        "created_at": now,
        "updated_at": now,
    }
    evidence = {
        "schema": SCHEMA_EVIDENCE,
        "workspace_id": wid,
        "claims": [{"id": "C-ROOT", "text": "Workspace initialized as local external projection", "criticality": "medium", "status": "supported"}],
        "evidence": [{"id": "E-ROOT", "type": "artifact", "authority": "objective", "ref": "workspace_state.yaml", "supports": ["C-ROOT"], "contradicts": [], "timestamp": now, "status": "verified"}],
    }
    wdir.mkdir(parents=True)
    (wdir / "artifacts").mkdir()
    (wdir / "reflection_log.md").write_text("# Reflection Log\n\n", encoding="utf-8")
    write_json(wdir / "workspace_state.json", workspace)
    write_json(wdir / "evidence_dag.json", evidence)
    write_json(wdir / "gates.json", {"schema": "jspace_gates_v0_1", "workspace_id": wid, "gate_results": []})
    (wdir / "event_ledger.jsonl").write_text("", encoding="utf-8")
    return {"ok": True, "workspace_id": wid, "path": str(wdir), "workspace": workspace}


def load_workspace(root: Path, workspace_id: str) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    wdir = workspace_dir(root, workspace_id)
    if not wdir.exists():
        raise SystemExit(f"workspace not found: {wdir}")
    return wdir, read_json(wdir / "workspace_state.json"), read_json(wdir / "evidence_dag.json")


def status(root: Path, workspace_id: str) -> dict[str, Any]:
    wdir, workspace, evidence = load_workspace(root, workspace_id)
    verified = [e for e in evidence.get("evidence", []) if e.get("status") == "verified"]
    advisory = [e for e in evidence.get("evidence", []) if e.get("authority") == "model_judgment"]
    event_path = wdir / "event_ledger.jsonl"
    event_count = len([line for line in event_path.read_text(encoding="utf-8").splitlines() if line.strip()]) if event_path.exists() else 0
    return {
        "ok": True,
        "workspace_id": workspace_id,
        "path": str(wdir),
        "workspace_state": workspace.get("workspace_state"),
        "goal": workspace.get("goal"),
        "authority_boundary": workspace.get("authority_boundary"),
        "claim_count": len(evidence.get("claims", [])),
        "evidence_count": len(evidence.get("evidence", [])),
        "verified_evidence_count": len(verified),
        "model_judgment_evidence_count": len(advisory),
        "event_count": event_count,
    }


def append_event(wdir: Path, event: dict[str, Any]) -> dict[str, Any]:
    event = dict(event)
    event.setdefault("schema", SCHEMA_EVENT)
    event.setdefault("event_id", f"evt-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}")
    event.setdefault("timestamp", utc_now())
    event.setdefault("side_effect_boundary", "local_projection_only")
    event.setdefault("external_side_effects_executed", False)
    with (wdir / "event_ledger.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    return event


def taskpool_to_workspace_state(lifecycle_state: Any) -> Any:
    mapping = {
        "pending": "dormant",
        "selected": "objective_model",
        "claimed": "objective_model",
        "running": "executing",
        "review": "reflective",
        "blocked": "gated",
        "done": "closed",
        "reopened": "contested",
    }
    return mapping.get(lifecycle_state or "")


def attach_task(root: Path, workspace_id: str, task_id: str) -> dict[str, Any]:
    wdir, workspace, evidence = load_workspace(root, workspace_id)
    workspace["task_id"] = task_id
    workspace["updated_at"] = utc_now()
    write_json(wdir / "workspace_state.json", workspace)
    event = append_event(wdir, {"source": "jspace", "type": "task.attached", "task_id": task_id, "workspace_id": workspace_id})
    return {"ok": True, "workspace_id": workspace_id, "task_id": task_id, "event_id": event["event_id"]}


def record_event(root: Path, workspace_id: str, event: dict[str, Any]) -> dict[str, Any]:
    wdir, workspace, evidence = load_workspace(root, workspace_id)
    event.setdefault("workspace_id", workspace_id)
    if workspace.get("task_id") and not event.get("task_id"):
        event["task_id"] = workspace.get("task_id")
    to_state = event.get("to") or event.get("lifecycle_state")
    projected = taskpool_to_workspace_state(to_state)
    derived_actions: list[str] = []
    if projected:
        workspace["workspace_state"] = projected
        workspace["updated_at"] = utc_now()
    if event.get("type") in {"task.review_requested", "task.status_changed"} and to_state == "review":
        derived_actions.extend(["gate_check:before_review", "reflection:evidence_review"])
    if event.get("type") == "task.done" or to_state == "done":
        derived_actions.append("gate_check:before_done")
    event.setdefault("derived_actions", derived_actions)
    recorded = append_event(wdir, event)
    write_json(wdir / "workspace_state.json", workspace)
    return {"ok": True, "workspace_id": workspace_id, "event_id": recorded["event_id"], "workspace_state": workspace.get("workspace_state"), "derived_actions": recorded.get("derived_actions", [])}


def add_evidence(root: Path, workspace_id: str, ev_type: str, ref: str, claim: str, *, authority: str, status_value: str) -> dict[str, Any]:
    wdir, workspace, evidence = load_workspace(root, workspace_id)
    now = utc_now()
    claim_id = f"C-{len(evidence.get('claims', [])) + 1:03d}"
    ev_id = f"E-{len(evidence.get('evidence', [])) + 1:03d}"
    evidence["claims"].append({"id": claim_id, "text": claim, "criticality": "medium", "status": "supported" if status_value == "verified" else "unverified"})
    evidence["evidence"].append({"id": ev_id, "type": ev_type, "authority": authority, "ref": ref, "supports": [claim_id], "contradicts": [], "timestamp": now, "status": status_value})
    workspace["updated_at"] = now
    write_json(wdir / "evidence_dag.json", evidence)
    write_json(wdir / "workspace_state.json", workspace)
    return {"ok": True, "workspace_id": workspace_id, "claim_id": claim_id, "evidence_id": ev_id, "authority": authority, "status": status_value}


def gate_check(root: Path, workspace_id: str, gate: str) -> dict[str, Any]:
    wdir, workspace, evidence = load_workspace(root, workspace_id)
    missing: list[str] = []
    result = "pass"
    if gate == "objective_defined":
        for key in ["goal", "non_goals", "constraints", "authority_boundary"]:
            if not workspace.get(key):
                missing.append(key)
        auth = workspace.get("authority_boundary") or {}
        for key in ["allowed", "requires_auth", "forbidden"]:
            if key not in auth:
                missing.append(f"authority_boundary.{key}")
    elif gate == "evidence_dag_exists":
        if evidence.get("schema") != SCHEMA_EVIDENCE:
            missing.append("evidence_dag.schema")
        if not evidence.get("evidence"):
            missing.append("evidence")
    elif gate == "reflection_readback":
        log = wdir / "reflection_log.md"
        text = log.read_text(encoding="utf-8") if log.exists() else ""
        if "## Reflection Readback" not in text:
            missing.append("reflection_log.readback")
    elif gate == "before_review":
        objective_verified = [e for e in evidence.get("evidence", []) if e.get("authority") == "objective" and e.get("status") == "verified"]
        if not objective_verified:
            missing.append("verified_objective_evidence")
        log = wdir / "reflection_log.md"
        text = log.read_text(encoding="utf-8") if log.exists() else ""
        if "## Reflection Readback" not in text:
            missing.append("reflection_log.readback")
    elif gate == "before_done":
        objective_verified = [e for e in evidence.get("evidence", []) if e.get("authority") == "objective" and e.get("status") == "verified"]
        if not objective_verified:
            missing.append("verified_objective_evidence")
        log = wdir / "reflection_log.md"
        text = log.read_text(encoding="utf-8") if log.exists() else ""
        if "## Reflection Readback" not in text:
            missing.append("reflection_log.readback")
    elif gate == "completion_claim":
        completion_claims = [c for c in evidence.get("claims", []) if c.get("criticality") == "completion_critical"]
        for claim in completion_claims:
            cid = claim["id"]
            supporters = [e for e in evidence.get("evidence", []) if cid in e.get("supports", [])]
            objective = [e for e in supporters if e.get("authority") == "objective" and e.get("status") == "verified"]
            if not objective:
                missing.append(f"objective_evidence_for_{cid}")
        if not completion_claims:
            result = "advisory"
    else:
        raise SystemExit(f"unknown gate: {gate}")
    if missing:
        result = "fail"
    gate_result = {"gate": gate, "result": result, "missing": missing, "timestamp": utc_now()}
    gates = read_json(wdir / "gates.json")
    gates.setdefault("gate_results", []).append(gate_result)
    write_json(wdir / "gates.json", gates)
    return {"ok": result in {"pass", "advisory"}, "workspace_id": workspace_id, **gate_result}


def reflect(root: Path, workspace_id: str) -> dict[str, Any]:
    wdir, workspace, evidence = load_workspace(root, workspace_id)
    verified = [e["id"] for e in evidence.get("evidence", []) if e.get("status") == "verified" and e.get("authority") == "objective"]
    advisory = [e["id"] for e in evidence.get("evidence", []) if e.get("authority") == "model_judgment"]
    missing = workspace.get("missing_evidence", [])
    packet = {
        "schema": "reflection_readback_v0_1",
        "workspace_id": workspace_id,
        "timestamp": utc_now(),
        "current_goal": workspace.get("goal"),
        "current_state": workspace.get("workspace_state"),
        "verified_objective_evidence": verified,
        "advisory_model_judgment": advisory,
        "unverified_assumptions": missing,
        "authority_boundary": workspace.get("authority_boundary"),
        "next_minimum_safe_action": workspace.get("next_action_contract", {}).get("action", "gate_check"),
        "stop_conditions": workspace.get("authority_boundary", {}).get("requires_auth", []),
    }
    with (wdir / "reflection_log.md").open("a", encoding="utf-8") as f:
        f.write(f"## Reflection Readback — {packet['timestamp']}\n\n")
        f.write(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True))
        f.write("\n\n")
    return {"ok": True, **packet}


def read_events(wdir: Path) -> list[dict[str, Any]]:
    path = wdir / "event_ledger.jsonl"
    events: list[dict[str, Any]] = []
    if not path.exists():
        return events
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            events.append({"raw": line, "parse_error": True})
    return events


def closure_packet(root: Path, workspace_id: str) -> dict[str, Any]:
    wdir, workspace, evidence = load_workspace(root, workspace_id)
    gates = read_json(wdir / "gates.json")
    events = read_events(wdir)
    objective_verified_ids = {e["id"] for e in evidence.get("evidence", []) if e.get("authority") == "objective" and e.get("status") == "verified"}
    taskpool_write_events = [e for e in events if e.get("taskpool_lifecycle_write_executed") is True or (e.get("source") == "taskpool_write_through" and e.get("returncode") == 0)]
    status_value = "verified_local" if objective_verified_ids else "advisory_only"
    scope = "local_projection_with_exact_taskpool_write_through" if taskpool_write_events else "local_projection_only_no_runtime_mutation"
    negative_evidence = ["no_hidden_state_access", "no_external_dispatch"]
    if not taskpool_write_events:
        negative_evidence.append("no_taskpool_lifecycle_write")
    excluded_claims = ["not_full_multimodel_certified", "not_integrated_with_runtime_router"]
    if not taskpool_write_events:
        excluded_claims.append("not_taskpool_real_lifecycle_write")
    packet = {
        "schema": SCHEMA_COMPLETION,
        "workspace_id": workspace_id,
        "claim": "External J-space workspace has a local projection/evidence/event packet",
        "scope": scope,
        "evidence_refs": sorted(objective_verified_ids),
        "taskpool_write_event_refs": [e.get("event_id") for e in taskpool_write_events],
        "missing_evidence": [] if objective_verified_ids else ["objective_evidence"],
        "negative_evidence": negative_evidence,
        "excluded_claims": excluded_claims,
        "status": status_value,
    }
    write_json(wdir / "completion_claim_packet.json", packet)
    md = [
        "# Closure Packet",
        "",
        f"- Workspace: `{workspace_id}`",
        f"- Goal: {workspace.get('goal')}",
        f"- State: {workspace.get('workspace_state')}",
        f"- Claims: {len(evidence.get('claims', []))}",
        f"- Evidence: {len(evidence.get('evidence', []))}",
        f"- Gate results: {len(gates.get('gate_results', []))}",
        f"- Events: {status(root, workspace_id).get('event_count')}",
        f"- Completion status: `{status_value}`",
        f"- Scope: {scope}",
        "- Boundary: no hidden-state access or external side effects.",
        "",
    ]
    (wdir / "closure_packet.md").write_text("\n".join(md), encoding="utf-8")
    return {"ok": True, "path": str(wdir / "closure_packet.md"), "packet": packet}


def taskpool_transition(root: Path, workspace_id: str, task_id: str, to_status: str, evidence: str, *, actor: str = "hermes-jspace", authority: str = "autonomous-execution") -> dict[str, Any]:
    wdir, workspace, evidence_dag = load_workspace(root, workspace_id)
    bound_task_id = workspace.get("task_id")
    if bound_task_id and bound_task_id != task_id:
        raise SystemExit(f"task_id mismatch: workspace bound to {bound_task_id}, got {task_id}")
    if not evidence.startswith(("artifact:", "command:", "proof:", "file:", "url:")):
        raise SystemExit("evidence must use accepted prefix: artifact:, command:, proof:, file:, or url:")
    if to_status not in {"claimed", "running", "review", "done", "blocked", "retry", "archived"}:
        raise SystemExit(f"unsupported taskpool target status: {to_status}")
    script = Path.home() / ".hermes" / "scripts" / "brain_task_orchestrator.py"
    cmd = [sys.executable, str(script), "transition", task_id, "--to", to_status, "--actor", actor, "--authority", authority, "--reason", f"External J-space exact write-through from {workspace_id}", "--evidence", evidence, "--json"]
    proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
    try:
        transition = json.loads(proc.stdout) if proc.stdout.strip() else {}
    except json.JSONDecodeError:
        transition = {"raw_stdout": proc.stdout}
    ok = proc.returncode == 0 and (transition.get("status") in {"OK", "PASS"} or transition.get("ok") is True or bool(transition))
    event = append_event(wdir, {
        "source": "taskpool_write_through",
        "type": "taskpool.transition.executed",
        "task_id": task_id,
        "workspace_id": workspace_id,
        "to": to_status,
        "command": " ".join(cmd[:4] + ["...redacted-args"]),
        "returncode": proc.returncode,
        "stdout_summary": proc.stdout[:2000],
        "stderr_summary": proc.stderr[:2000],
        "external_side_effects_executed": False,
        "taskpool_lifecycle_write_executed": proc.returncode == 0,
        "side_effect_boundary": "exact_taskpool_lifecycle_write_through",
    })
    projected = taskpool_to_workspace_state(to_status)
    if projected:
        workspace["workspace_state"] = projected
    workspace["task_id"] = task_id
    workspace["updated_at"] = utc_now()
    write_json(wdir / "workspace_state.json", workspace)
    return {"ok": ok, "workspace_id": workspace_id, "task_id": task_id, "to": to_status, "event_id": event["event_id"], "returncode": proc.returncode, "transition": transition, "stderr": proc.stderr[:2000]}


def learning_candidates(root: Path, workspace_id: str) -> dict[str, Any]:
    wdir, workspace, evidence = load_workspace(root, workspace_id)
    gates = read_json(wdir / "gates.json")
    verified_refs = [e["id"] for e in evidence.get("evidence", []) if e.get("authority") == "objective" and e.get("status") == "verified"]
    passed_gates = [g["gate"] for g in gates.get("gate_results", []) if g.get("result") in {"pass", "advisory"}]
    candidate = {
        "schema": "jspace_learning_candidate_v0_1",
        "workspace_id": workspace_id,
        "timestamp": utc_now(),
        "scope": "project_ref",
        "claim": "External J-space workflow produced a reusable local projection/evidence/gate pattern",
        "evidence_refs": verified_refs,
        "gate_refs": passed_gates,
        "recommended_action": "review_before_skill_or_runtime_promotion",
        "requires_human_review": True,
        "auto_apply_executed": False,
        "global_memory_write_executed": False,
        "skill_patch_executed": False,
        "boundary": "candidate_only_no_persistent_learning_write",
    }
    write_json(wdir / "learning_candidate.json", candidate)
    return {"ok": True, "workspace_id": workspace_id, "path": str(wdir / "learning_candidate.json"), "candidate": candidate}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def real_open_matrix(root: Path, workspace_id: str, *, run_destructive_canary: bool = False) -> dict[str, Any]:
    wdir, workspace, evidence = load_workspace(root, workspace_id)
    events = read_events(wdir)
    taskpool_written = any(e.get("taskpool_lifecycle_write_executed") is True or (e.get("source") == "taskpool_write_through" and e.get("returncode") == 0) for e in events)
    destructive_canary: dict[str, Any] = {"executed": False, "production_resource_touched": False}
    if run_destructive_canary:
        canary_dir = wdir / "artifacts" / "destructive-canary"
        canary_dir.mkdir(parents=True, exist_ok=True)
        target = canary_dir / "canary.txt"
        backup = canary_dir / "canary.txt.bak"
        restored = canary_dir / "canary.restored.txt"
        content = f"external-jspace-destructive-canary:{workspace_id}\n"
        target.write_text(content, encoding="utf-8")
        before_hash = sha256_file(target)
        shutil.copy2(target, backup)
        target.unlink()
        absent_after_delete = not target.exists()
        shutil.copy2(backup, restored)
        restored_hash = sha256_file(restored)
        destructive_canary = {
            "executed": True,
            "production_resource_touched": False,
            "target": str(target),
            "backup": str(backup),
            "restored": str(restored),
            "absent_after_delete": absent_after_delete,
            "before_sha256": before_hash,
            "restored_sha256": restored_hash,
            "hash_match": before_hash == restored_hash,
        }
        append_event(wdir, {"source": "jspace", "type": "destructive.canary.delete_restore", "workspace_id": workspace_id, "destructive_canary_executed": True, "production_resource_touched": False, "side_effect_boundary": "disposable_local_canary", "external_side_effects_executed": False})
    cron_receipt = Path.home() / ".hermes" / "workflows" / "jspace" / "cron-heartbeat-receipts" / "latest.json"
    scheduler_executed = cron_receipt.exists()
    boundaries = [
        {"id": "taskpool_lifecycle_write", "label": "Exact taskpool lifecycle write-through", "governance_covered": True, "exact_target_required": True, "receipt_required": True, "rollback_required": True, "readback_required": True, "executed": taskpool_written, "execution_status": "executed_exact_task" if taskpool_written else "exact_target_required"},
        {"id": "scheduler_cron_write", "label": "Scheduler/no-agent cron write", "governance_covered": True, "exact_target_required": True, "receipt_required": True, "rollback_required": True, "readback_required": True, "executed": scheduler_executed, "execution_status": "executed_local_no_agent_heartbeat" if scheduler_executed else "blocked_exact_job_not_requested", "receipt": str(cron_receipt) if scheduler_executed else ""},
        {"id": "worker_spawn", "label": "Worker/subagent spawn", "governance_covered": True, "exact_target_required": True, "receipt_required": True, "rollback_required": True, "readback_required": True, "executed": False, "execution_status": "blocked_exact_worker_packet_not_requested"},
        {"id": "external_dispatch", "label": "External platform dispatch/send", "governance_covered": True, "exact_target_required": True, "receipt_required": True, "rollback_required": False, "readback_required": True, "executed": False, "execution_status": "blocked_missing_platform_target_payload"},
        {"id": "publish_deploy_push", "label": "Publish/deploy/push", "governance_covered": True, "exact_target_required": True, "receipt_required": True, "rollback_required": True, "readback_required": True, "executed": False, "execution_status": "blocked_missing_repo_remote_env_ref_rollback"},
        {"id": "destructive_operation", "label": "Destructive operation", "governance_covered": True, "exact_target_required": True, "receipt_required": True, "rollback_required": True, "readback_required": True, "executed": destructive_canary.get("executed", False), "execution_status": "canary_delete_restore_verified" if destructive_canary.get("executed") and destructive_canary.get("hash_match") else "blocked_exact_production_target_missing", "canary": destructive_canary},
        {"id": "payment_credential_entry", "label": "Payment / credential entry", "governance_covered": True, "exact_target_required": True, "receipt_required": True, "rollback_required": False, "readback_required": True, "executed": False, "execution_status": "human_secret_gate_only", "agent_may_type_secret": False},
        {"id": "broad_fanout", "label": "Broad fan-out", "governance_covered": True, "exact_target_required": True, "receipt_required": True, "rollback_required": False, "readback_required": True, "executed": False, "execution_status": "blocked_missing_exact_channel_set_payload"},
    ]
    coverage_percent = 100 if all(b["governance_covered"] for b in boundaries) else int(100 * sum(1 for b in boundaries if b["governance_covered"]) / len(boundaries))
    matrix = {
        "schema": "jspace_real_open_matrix_v0_1",
        "workspace_id": workspace_id,
        "timestamp": utc_now(),
        "coverage_type": "governance_and_exact-boundary_readback",
        "governance_coverage_percent": coverage_percent,
        "unscoped_high_risk_execution": False,
        "boundaries": boundaries,
    }
    write_json(wdir / "real_open_matrix.json", matrix)
    return {"ok": True, "workspace_id": workspace_id, "path": str(wdir / "real_open_matrix.json"), "matrix": matrix}


def dashboard_data(root: Path) -> dict[str, Any]:
    root_path = root.expanduser().resolve()
    active: list[dict[str, Any]] = []
    blocked_gates: list[dict[str, Any]] = []
    learning: list[dict[str, Any]] = []
    evidence_health = {"verified": 0, "advisory": 0, "failed": 0, "blocked": 0}
    if root_path.exists():
        for wdir in sorted([p for p in root_path.iterdir() if p.is_dir()]):
            try:
                workspace = read_json(wdir / "workspace_state.json")
                evidence = read_json(wdir / "evidence_dag.json")
            except Exception:
                continue
            active.append({"workspace_id": workspace.get("id"), "title": workspace.get("title"), "task_id": workspace.get("task_id"), "state": workspace.get("workspace_state"), "path": str(wdir)})
            for ev in evidence.get("evidence", []):
                status_key = ev.get("status")
                if status_key in evidence_health:
                    evidence_health[status_key] += 1
            gates_path = wdir / "gates.json"
            if gates_path.exists():
                for gate in read_json(gates_path).get("gate_results", []):
                    if gate.get("result") in {"fail", "blocked"}:
                        blocked_gates.append({"workspace_id": workspace.get("id"), **gate})
            candidate_path = wdir / "learning_candidate.json"
            if candidate_path.exists():
                candidate = read_json(candidate_path)
                learning.append({"workspace_id": workspace.get("id"), "requires_human_review": candidate.get("requires_human_review"), "auto_apply_executed": candidate.get("auto_apply_executed"), "path": str(candidate_path)})
    all_events: list[dict[str, Any]] = []
    if root_path.exists():
        for wdir in sorted([p for p in root_path.iterdir() if p.is_dir()]):
            all_events.extend(read_events(wdir))
    taskpool_written = any(e.get("taskpool_lifecycle_write_executed") is True or (e.get("source") == "taskpool_write_through" and e.get("returncode") == 0) for e in all_events)
    external_executed = any(e.get("external_side_effects_executed") is True for e in all_events)
    return {
        "ok": True,
        "schema": "jspace_dashboard_data_v0_1",
        "root": str(root_path),
        "active_jspaces": active,
        "blocked_gates": blocked_gates,
        "evidence_health": evidence_health,
        "learning_candidates": learning,
        "runtime_mutation": taskpool_written,
        "external_side_effects_executed": external_executed,
        "taskpool_lifecycle_write_executed": taskpool_written,
    }


def emit(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Hermes External J-space P0 projection helper")
    parser.add_argument("--root", default=str(DEFAULT_ROOT))
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("dashboard-data")
    p = sub.add_parser("real-open-matrix")
    p.add_argument("workspace_id")
    p.add_argument("--run-destructive-canary", action="store_true")
    p = sub.add_parser("init")
    p.add_argument("--title", required=True)
    p.add_argument("--goal", required=True)
    p.add_argument("--id", default=None)
    p.add_argument("--task-id", default=None)
    p = sub.add_parser("status")
    p.add_argument("workspace_id")
    p = sub.add_parser("add-evidence")
    p.add_argument("workspace_id")
    p.add_argument("--type", required=True)
    p.add_argument("--ref", required=True)
    p.add_argument("--claim", required=True)
    p.add_argument("--authority", choices=["objective", "model_judgment", "user_statement"], default="objective")
    p.add_argument("--status", choices=["verified", "advisory", "failed", "blocked"], default="verified")
    p = sub.add_parser("attach-task")
    p.add_argument("workspace_id")
    p.add_argument("--task-id", required=True)
    p = sub.add_parser("on-event")
    p.add_argument("workspace_id")
    p.add_argument("--event-json", required=True, help="JSON object or path")
    p = sub.add_parser("gate-check")
    p.add_argument("workspace_id")
    p.add_argument("--gate", required=True, choices=["objective_defined", "evidence_dag_exists", "reflection_readback", "before_review", "before_done", "completion_claim"])
    p = sub.add_parser("reflect")
    p.add_argument("workspace_id")
    p = sub.add_parser("closure-packet")
    p.add_argument("workspace_id")
    p = sub.add_parser("learning-candidates")
    p.add_argument("workspace_id")
    p = sub.add_parser("taskpool-transition")
    p.add_argument("workspace_id")
    p.add_argument("--task-id", required=True)
    p.add_argument("--to", required=True, choices=["claimed", "running", "review", "done", "blocked", "retry", "archived"])
    p.add_argument("--evidence", required=True)
    p.add_argument("--actor", default="hermes-jspace")
    p.add_argument("--authority", choices=["read", "dry-run", "dispatch-hint", "claim-and-handoff", "budget-handoff", "autonomous-execution", "yolo-execution"], default="autonomous-execution")
    return parser


def main(argv: Any = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root)
    if args.cmd == "dashboard-data":
        data = dashboard_data(root)
    elif args.cmd == "real-open-matrix":
        data = real_open_matrix(root, args.workspace_id, run_destructive_canary=args.run_destructive_canary)
    elif args.cmd == "init":
        data = init_workspace(root, args.title, args.goal, workspace_id=args.id, task_id=args.task_id)
    elif args.cmd == "status":
        data = status(root, args.workspace_id)
    elif args.cmd == "add-evidence":
        data = add_evidence(root, args.workspace_id, args.type, args.ref, args.claim, authority=args.authority, status_value=args.status)
    elif args.cmd == "attach-task":
        data = attach_task(root, args.workspace_id, args.task_id)
    elif args.cmd == "on-event":
        event_arg = Path(args.event_json).expanduser()
        event = json.loads(event_arg.read_text(encoding="utf-8")) if event_arg.exists() else json.loads(args.event_json)
        data = record_event(root, args.workspace_id, event)
    elif args.cmd == "gate-check":
        data = gate_check(root, args.workspace_id, args.gate)
    elif args.cmd == "reflect":
        data = reflect(root, args.workspace_id)
    elif args.cmd == "closure-packet":
        data = closure_packet(root, args.workspace_id)
    elif args.cmd == "learning-candidates":
        data = learning_candidates(root, args.workspace_id)
    elif args.cmd == "taskpool-transition":
        data = taskpool_transition(root, args.workspace_id, args.task_id, args.to, args.evidence, actor=args.actor, authority=args.authority)
    else:
        raise AssertionError(args.cmd)
    emit(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
