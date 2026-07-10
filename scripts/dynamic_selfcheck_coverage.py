#!/usr/bin/env python3
"""Dynamic Hermes self-check coverage discovery/planning/proposal.

Local-first and proposal-first by design:
- reads local Hermes state only;
- writes registry/plan/proposal artifacts under ~/.hermes/state/selfcheck;
- never sends external messages, closes issues, pushes, deletes, or enters secrets;
- only labels read-only/local/no-agent proposals as auto-promotable.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SCHEMA = "hermes_dynamic_selfcheck_coverage_v1"
PLAN_SCHEMA = "hermes_dynamic_selfcheck_plan_v1"
PROPOSAL_SCHEMA = "hermes_dynamic_selfcheck_proposals_v1"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def hermes_root(home: Path | None = None) -> Path:
    return (home or Path.home()) / ".hermes"


def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default
    except json.JSONDecodeError as exc:
        return {"_error": f"json_decode_error:{exc}", "_path": str(path)}


def safe_rel(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except Exception:
        return str(path)


def classify_delivery(deliver: Any) -> str:
    if not deliver:
        return "local"
    text = str(deliver)
    if text == "local":
        return "local"
    if text.startswith("telegram"):
        return "telegram"
    if text.startswith("discord"):
        return "discord"
    if text.startswith("slack"):
        return "slack"
    if text in {"origin", "all"}:
        return text
    return text.split(":", 1)[0]


def git_snapshot(repo: Path) -> dict[str, Any]:
    if not (repo / ".git").exists():
        return {"present": False, "path": str(repo)}
    def run(args: list[str]) -> str:
        try:
            return subprocess.check_output(["git", "-C", str(repo), *args], text=True, stderr=subprocess.DEVNULL, timeout=10).strip()
        except Exception:
            return ""
    return {
        "present": True,
        "path": str(repo),
        "branch": run(["branch", "--show-current"]),
        "head": run(["rev-parse", "--short", "HEAD"]),
        "status_short": run(["status", "--short"]),
        "remote": run(["remote", "-v"]),
    }


def discover_user_system_profile(home: Path | None = None) -> dict[str, Any]:
    home = Path(home or Path.home())
    root = hermes_root(home)
    cron_path = root / "cron" / "jobs.json"
    cron_data = read_json(cron_path, {"jobs": []})
    jobs = cron_data.get("jobs", []) if isinstance(cron_data, dict) else []
    enabled_jobs = [j for j in jobs if j.get("enabled", True)]
    delivery_error_jobs = [j for j in enabled_jobs if j.get("last_delivery_error") or (j.get("last_status") == "error" and classify_delivery(j.get("deliver")) != "local")]
    cron_error_jobs = [j for j in enabled_jobs if j.get("last_status") == "error" or j.get("last_error") or j.get("last_delivery_error")]

    systems: list[dict[str, Any]] = []
    systems.append({
        "system_id": "hermes-core",
        "kind": "core",
        "detected_from": [str(root), str(root / "hermes-agent")],
        "enabled": True,
        "evidence": {"repo": git_snapshot(root / "hermes-agent")},
    })
    systems.append({
        "system_id": "cron",
        "kind": "scheduler",
        "detected_from": [str(cron_path)],
        "enabled": bool(jobs),
        "evidence": {"job_count": len(jobs), "enabled_count": len(enabled_jobs), "error_count": len(cron_error_jobs)},
    })

    deliveries = sorted({classify_delivery(j.get("deliver")) for j in enabled_jobs}) or ["local"]
    for delivery in deliveries:
        related = [j for j in enabled_jobs if classify_delivery(j.get("deliver")) == delivery]
        systems.append({
            "system_id": f"delivery:{delivery}",
            "kind": "delivery",
            "detected_from": [str(cron_path)],
            "enabled": True,
            "evidence": {
                "jobs": [j.get("id") for j in related],
                "job_count": len(related),
                "delivery_error_jobs": [j.get("id") for j in related if j.get("last_delivery_error") or j.get("last_status") == "error"],
            },
        })

    profile_dir = root / "project-profiles"
    for profile in sorted(profile_dir.glob("*.json")) if profile_dir.exists() else []:
        profile_evidence: dict[str, Any] = {"path": str(profile)}
        if profile.stem == "lark":
            lark_flow = root / "scripts" / "lark_task_flow.py"
            lark_flow_text = lark_flow.read_text(encoding="utf-8", errors="ignore") if lark_flow.exists() else ""
            profile_evidence.update({
                "reader_script": str(lark_flow),
                "reader_script_exists": lark_flow.exists(),
                "health_check_supported": "--health-check" in lark_flow_text,
                "health_check_command": f"python3 {lark_flow} --health-check",
            })
        systems.append({
            "system_id": f"profile:{profile.stem}",
            "kind": "project_profile",
            "detected_from": [str(profile)],
            "enabled": True,
            "evidence": profile_evidence,
        })

    scripts_dir = root / "scripts"
    if scripts_dir.exists():
        key_scripts = []
        for name in ["post-update-check.py", "brain_task_orchestrator.py", "health-check.py", "github_issue_monitor.py", "lark_task_flow.py"]:
            if (scripts_dir / name).exists():
                key_scripts.append(name)
        systems.append({
            "system_id": "scripts:selfcheck",
            "kind": "script_pool",
            "detected_from": [str(scripts_dir)],
            "enabled": True,
            "evidence": {"key_scripts": key_scripts},
        })

    experience_home = root / "experience-ratchet"
    if experience_home.exists() or (scripts_dir / "experience-ratchet-maze.py").exists() or (scripts_dir / "experience_ratchet_watchdog.py").exists():
        atoms_dir = experience_home / "atoms"
        proposals_dir = experience_home / "proposals"
        atoms = []
        for atom_path in sorted(atoms_dir.glob("*.json")) if atoms_dir.exists() else []:
            atom = read_json(atom_path, {})
            if isinstance(atom, dict):
                atoms.append(atom)
        enabled_watchdog_jobs = []
        for job in enabled_jobs:
            haystack = " ".join(str(job.get(k) or "") for k in ["name", "script", "prompt"]).lower()
            if "experience_ratchet_watchdog" in haystack or "experience-ratchet" in haystack:
                enabled_watchdog_jobs.append(job.get("id") or job.get("name"))
        staging_dir = root / "evidence" / "skill-evolution-candidates"
        staged_keys = set()
        if staging_dir.exists():
            for staged_path in list(staging_dir.glob("*.json")) + list(staging_dir.glob("*.md")):
                try:
                    staged_text = staged_path.read_text(encoding="utf-8", errors="ignore").lower()
                except Exception:
                    continue
                staged_keys.update(re.findall(r"[a-z0-9][a-z0-9._-]+-[0-9a-f]{12}", staged_text))
                if staged_path.suffix == ".json":
                    payload = read_json(staged_path, {})
                    if isinstance(payload, dict) and payload.get("title"):
                        staged_keys.add(str(payload.get("title")).strip().lower())
        unstaged_skill_candidates = []
        for atom in atoms:
            if atom.get("status") not in {"validated", "promoted_candidate"}:
                continue
            if (atom.get("classification") or {}).get("target_landing_zone") != "skill":
                continue
            atom_id = str(atom.get("atom_id") or "").lower()
            title = str(atom.get("title") or "").strip().lower()
            if atom_id not in staged_keys and title not in staged_keys:
                unstaged_skill_candidates.append(atom.get("atom_id") or title)
        systems.append({
            "system_id": "experience-ratchet",
            "kind": "experience_overlay",
            "detected_from": [str(experience_home), str(scripts_dir / "experience-ratchet-maze.py"), str(scripts_dir / "experience_ratchet_watchdog.py")],
            "enabled": experience_home.exists(),
            "evidence": {
                "home_exists": experience_home.exists(),
                "cli_exists": (scripts_dir / "experience-ratchet-maze.py").exists(),
                "watchdog_script_exists": (scripts_dir / "experience_ratchet_watchdog.py").exists(),
                "watchdog_job_ids": enabled_watchdog_jobs,
                "atom_count": len(atoms),
                "proposal_count": len(list(proposals_dir.glob("*.json"))) if proposals_dir.exists() else 0,
                "promoted_candidate_count": sum(1 for atom in atoms if atom.get("status") == "promoted_candidate"),
                "unstaged_skill_candidate_count": len(unstaged_skill_candidates),
                "unstaged_skill_candidate_ids": unstaged_skill_candidates[:20],
            },
        })

    providers = []
    config = read_json(root / "config.json", {})
    # config.yaml parsing deliberately avoided to keep stdlib-only and non-fragile.
    for env_name in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "OPENROUTER_API_KEY", "XAI_API_KEY"]:
        if os.environ.get(env_name):
            providers.append(env_name.replace("_API_KEY", "").lower())
    systems.append({
        "system_id": "model-providers",
        "kind": "provider_health",
        "detected_from": ["environment", str(root / "config.yaml"), str(root / "config.json")],
        "enabled": True,
        "evidence": {"env_provider_markers": providers, "json_config_seen": bool(config)},
    })

    return {
        "schema": "hermes_user_system_profile_v1",
        "generated_at": utc_now(),
        "home": str(home),
        "systems": systems,
        "summary": {
            "systems": len(systems),
            "cron_jobs": len(jobs),
            "enabled_cron_jobs": len(enabled_jobs),
            "cron_error_jobs": len(cron_error_jobs),
            "delivery_error_jobs": len(delivery_error_jobs),
            "project_profiles": len([s for s in systems if s["kind"] == "project_profile"]),
        },
    }


def current_checks_for(system: dict[str, Any]) -> list[str]:
    sid = system["system_id"]
    evidence = system.get("evidence", {})
    if sid == "hermes-core":
        return ["hermes_doctor", "post_update_check", "dirty_worktree_awareness"]
    if sid == "cron":
        return ["cron_list_readback", "cron_error_cluster_watch"]
    if sid.startswith("delivery:"):
        checks = ["delivery_job_config_readback", "delivery_failure_watch"]
        if sid == "delivery:local":
            checks.append("cron_output_readback")
        return checks
    if sid == "scripts:selfcheck":
        return ["script_presence_scan"]
    if sid == "model-providers":
        return ["provider_static_readiness", "provider_health_watch"]
    if system.get("kind") == "project_profile":
        checks = ["project_profile_json_readback"]
        if sid == "profile:lark" and evidence.get("health_check_supported"):
            checks.append("lark_auth_and_reader_watch")
        return checks
    if sid == "experience-ratchet":
        checks = ["experience_ratchet_cli_present"] if evidence.get("cli_exists") else []
        if evidence.get("watchdog_script_exists"):
            checks.append("experience_ratchet_watchdog_script_present")
        if evidence.get("watchdog_job_ids"):
            checks.append("experience_ratchet_watchdog_cron")
        return checks or ["system_detection_evidence_readback"]
    if system.get("detected_from"):
        return ["system_detection_evidence_readback"]
    return ["system_registration_readback"]


def missing_checks_for(system: dict[str, Any]) -> list[str]:
    sid = system["system_id"]
    evidence = system.get("evidence", {})
    missing: list[str] = []
    if sid == "profile:lark" and not evidence.get("health_check_supported"):
        missing.append("lark_auth_and_reader_watch")
    if sid == "experience-ratchet":
        if not evidence.get("home_exists") or not evidence.get("cli_exists"):
            missing.append("experience_ratchet_store_or_cli_missing")
        if not evidence.get("watchdog_script_exists"):
            missing.append("experience_ratchet_watchdog_script_missing")
        if not evidence.get("watchdog_job_ids"):
            missing.append("experience_ratchet_watchdog_cron_missing")
        if int(evidence.get("unstaged_skill_candidate_count") or 0) > 0:
            missing.append("experience_ratchet_skill_candidate_staging_watch")
    return missing


def operational_findings_for(system: dict[str, Any], snapshots: dict[str, Any] | None = None) -> list[str]:
    sid = system["system_id"]
    evidence = system.get("evidence", {})
    snapshots = snapshots or {}
    findings: list[str] = []
    if sid == "hermes-core" and (evidence.get("repo") or {}).get("status_short"):
        findings.append("dirty_worktree_observed")
    if sid == "cron" and int(evidence.get("error_count") or 0) > 0:
        findings.append("cron_errors_observed")
    if sid.startswith("delivery:") and evidence.get("delivery_error_jobs"):
        findings.append("delivery_errors_observed")
    if sid == "model-providers":
        provider = snapshots.get("provider_health") or {}
        if provider and not (provider.get("summary") or {}).get("ok"):
            findings.append("provider_runtime_not_verified_or_degraded")
    if sid == "profile:lark":
        lark = snapshots.get("lark_health") or {}
        if lark and not (lark.get("summary") or {}).get("ok"):
            findings.append("lark_auth_or_reader_degraded")
    return findings


def risk_for(system: dict[str, Any], missing: list[str]) -> str:
    sid = system["system_id"]
    if sid.startswith("delivery:") and sid != "delivery:local" and "delivery_failure_watch" in missing:
        return "high"
    if sid in {"model-providers", "cron"} and missing:
        return "medium"
    if sid == "experience-ratchet" and any(item in missing for item in {"experience_ratchet_store_or_cli_missing", "experience_ratchet_promoted_candidate_backlog", "experience_ratchet_skill_candidate_staging_watch"}):
        return "medium"
    if sid == "experience-ratchet" and missing:
        return "low"
    if sid.startswith("profile:lark") and missing:
        return "medium"
    return "low"


def build_coverage_registry(profile: dict[str, Any], snapshots: dict[str, Any] | None = None) -> dict[str, Any]:
    systems = []
    for system in profile.get("systems", []):
        current = current_checks_for(system)
        missing = missing_checks_for(system)
        operational_findings = operational_findings_for(system, snapshots)
        coverage_state = "gap" if missing else "covered"
        systems.append({
            "system_id": system["system_id"],
            "kind": system.get("kind"),
            "enabled": system.get("enabled", True),
            "coverage_state": coverage_state,
            "classification_reason": "explicit_missing_checks" if missing else "current_checks_attached",
            "detected_from": system.get("detected_from", []),
            "risk_level": risk_for(system, missing),
            "current_checks": current,
            "missing_checks": missing,
            "operational_state": "warning" if operational_findings else "healthy_or_not_observed_degraded",
            "operational_findings": operational_findings,
            "stale_checks": [],
            "evidence_refs": system.get("detected_from", []),
            "last_observed_at": profile.get("generated_at"),
            "proposals": [],
        })
    return {
        "schema": SCHEMA,
        "generated_at": utc_now(),
        "profile_generated_at": profile.get("generated_at"),
        "systems": systems,
        "summary": {
            "systems": len(systems),
            "classified_systems": sum(1 for s in systems if s["coverage_state"] in {"covered", "gap", "not_applicable"}),
            "unclassified_systems": sum(1 for s in systems if s["coverage_state"] not in {"covered", "gap", "not_applicable"}),
            "classification_coverage_percent": round(100.0 * sum(1 for s in systems if s["coverage_state"] in {"covered", "gap", "not_applicable"}) / len(systems), 1) if systems else 100.0,
            "check_attachment_percent": round(100.0 * sum(1 for s in systems if s["current_checks"]) / len(systems), 1) if systems else 100.0,
            "engineering_gap_systems": sum(1 for s in systems if s["coverage_state"] == "gap"),
            "operational_gap_systems": sum(1 for s in systems if s["operational_findings"]),
            "operational_findings": sum(len(s["operational_findings"]) for s in systems),
            "missing_checks": sum(len(s["missing_checks"]) for s in systems),
            "high_risk_systems": sum(1 for s in systems if s["risk_level"] == "high"),
            "score_semantics": "classification coverage is separate from operational health",
        },
    }


def add_check(checks: list[dict[str, Any]], check_id: str, reason: str, command: str, side_effects: str = "local_read") -> None:
    if any(c["check_id"] == check_id for c in checks):
        return
    checks.append({
        "check_id": check_id,
        "reason": reason,
        "command": command,
        "side_effects": side_effects,
        "required_evidence": ["exit_code", "stdout_or_artifact_readback"],
    })


def plan_from_events(events: Iterable[dict[str, Any]]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    normalized = list(events)
    for event in normalized:
        path = str(event.get("path", ""))
        kind = event.get("kind")
        if kind == "changed_file":
            if "doctor.py" in path:
                add_check(checks, "doctor_cli_smoke", f"doctor surface changed: {path}", "hermes doctor")
                add_check(checks, "doctor_fix_smoke", f"doctor fix path changed: {path}", "hermes doctor --fix", "local_write")
                add_check(checks, "post_update_check", f"post-update guard for: {path}", "python3 ~/.hermes/scripts/post-update-check.py --fix", "local_write")
            if "adapter" in path or "provider" in path or "openai" in path or "anthropic" in path:
                add_check(checks, "provider_runtime_smoke", f"provider surface changed: {path}", "python3 ~/.hermes/scripts/consult_models.py selfcheck")
                add_check(checks, "provider_route_eligibility", f"provider routing changed: {path}", "python3 ~/.hermes/scripts/consult_models.py status")
            if "prompt" in path or "system_prompt" in path:
                add_check(checks, "prompt_cache_and_role_smoke", f"prompt surface changed: {path}", "python -m pytest tests/agent/test_system_prompt_restore.py -q")
            if "cron" in path or "gateway" in path:
                add_check(checks, "delivery_readback_scan", f"scheduler/delivery surface changed: {path}", "python3 ~/.hermes/scripts/dynamic_selfcheck_coverage.py run")
            if "taskpool" in path or "kanban" in path:
                add_check(checks, "taskpool_boundary_selfcheck", f"taskpool surface changed: {path}", "python3 ~/.hermes/scripts/brain_task_orchestrator.py selfcheck --json")
        elif kind in {"cron_failure", "delivery_failure"}:
            add_check(checks, "cron_error_cluster_watch", "cron/delivery failure event", "python3 ~/.hermes/scripts/dynamic_selfcheck_coverage.py run")
    return {
        "schema": PLAN_SCHEMA,
        "generated_at": utc_now(),
        "events": normalized,
        "checks": checks,
        "summary": {"events": len(normalized), "checks": len(checks)},
    }


def generate_proposals(registry: dict[str, Any]) -> list[dict[str, Any]]:
    proposals: list[dict[str, Any]] = []
    missing_all = {m for s in registry.get("systems", []) for m in s.get("missing_checks", [])}
    findings_all = {m for s in registry.get("systems", []) for m in s.get("operational_findings", [])}
    if "delivery_failure_watch" in missing_all or "delivery_errors_observed" in findings_all:
        proposals.append({
            "id": "proposal.delivery_failure_watch",
            "reason": "External delivery jobs have recent delivery errors; monitor locally and emit actionable repair packets only on failure.",
            "target_system": "delivery:*",
            "workflow_type": "no_agent_cron",
            "schedule": "every 30m",
            "script": "dynamic_selfcheck_coverage.py run --quiet-success",
            "deliver": "local",
            "no_agent": True,
            "success_behavior": "silent",
            "failure_behavior": "print actionable local alert with evidence path; do not resend externally",
            "side_effects": "local_read",
            "promotion": {
                "auto_promotable": True,
                "authority_required": "none_for_local_read_monitor",
                "forbidden_without_authority": ["external_send", "github_comment_or_close", "push", "deploy", "delete", "credential_entry"],
            },
            "rollback": "hermes cron remove <job_id>",
        })
    if "provider_health_watch" in missing_all or "provider_runtime_not_verified_or_degraded" in findings_all:
        proposals.append({
            "id": "proposal.provider_health_watch",
            "reason": "Model/provider health gates affect multi-model certification and autonomous promotion safety.",
            "target_system": "model-providers",
            "workflow_type": "no_agent_cron",
            "schedule": "every 4h",
            "script": "consult_models.py selfcheck && consult_models.py status",
            "deliver": "local",
            "no_agent": True,
            "success_behavior": "silent",
            "failure_behavior": "print degraded model availability and fail-closed boundary",
            "side_effects": "local_read",
            "promotion": {"auto_promotable": True, "authority_required": "none_for_local_read_monitor", "forbidden_without_authority": ["model_certification_claim"]},
            "rollback": "hermes cron remove <job_id>",
        })
    if "lark_auth_and_reader_watch" in missing_all or "lark_auth_or_reader_degraded" in findings_all:
        proposals.append({
            "id": "proposal.lark_auth_and_reader_watch",
            "reason": "Lark profile exists; auth/reader health should be covered without sending messages.",
            "target_system": "profile:lark",
            "workflow_type": "no_agent_cron",
            "schedule": "every 2h",
            "script": "lark_task_flow.py --health-check",
            "deliver": "local",
            "no_agent": True,
            "success_behavior": "silent",
            "failure_behavior": "print local auth/reader boundary only",
            "side_effects": "local_read",
            "promotion": {"auto_promotable": False, "authority_required": "exact_command_verified_first", "forbidden_without_authority": ["lark_send", "token_write"]},
            "rollback": "hermes cron remove <job_id>",
        })
    if any(item in missing_all for item in {"experience_ratchet_watchdog_script_missing", "experience_ratchet_watchdog_cron_missing", "experience_ratchet_promoted_candidate_backlog", "experience_ratchet_skill_candidate_staging_watch"}):
        proposals.append({
            "id": "proposal.experience_ratchet_watchdog",
            "reason": "Experience Ratchet is the dev-brain overlay for cross-project lessons; it needs local validation/backlog coverage before experience can safely promote into skills or profiles.",
            "target_system": "experience-ratchet",
            "workflow_type": "no_agent_cron",
            "schedule": "every 6h",
            "script": "experience_ratchet_watchdog.py --quiet-success --require-cron",
            "deliver": "local",
            "no_agent": True,
            "success_behavior": "silent",
            "failure_behavior": "print local JSON with validate/backlog/staging evidence; do not mutate skills/memory/profiles/taskpool",
            "side_effects": "local_read",
            "promotion": {
                "auto_promotable": True,
                "authority_required": "none_for_local_read_monitor",
                "forbidden_without_authority": ["direct_skill_edit", "direct_memory_write", "direct_profile_edit", "direct_taskpool_add", "external_send", "push", "deploy", "delete", "credential_entry"],
            },
            "rollback": "hermes cron remove <job_id>",
        })
    return proposals


def error_text(job: dict[str, Any]) -> str:
    return " ".join(str(job.get(k) or "") for k in ["last_delivery_error", "last_error", "name", "script", "deliver"]).lower()


def classify_cron_error(job: dict[str, Any]) -> str:
    text = error_text(job)
    delivery = classify_delivery(job.get("deliver"))
    if job.get("last_delivery_error") or "proxyerror" in text or "telegram" in text or "send_path" in text:
        return "delivery_proxy" if delivery != "local" or "telegram" in text else "delivery_local"
    if any(token in text for token in ["quota", "rate limit", "429", "model", "planner", "consult_models", "xiaomi", "openai", "claude", "mimo", "connection error"]):
        return "model_provider_or_quota"
    if any(token in text for token in ["permission", "not found", "no such file", "traceback", "syntaxerror", "modulenotfound"]):
        return "script_runtime"
    if any(token in text for token in ["disk", "storage", "cleanup", "snapshot", "state.db"]):
        return "storage_or_cleanup"
    return "other_cron_error"


def cluster_cron_errors(jobs: list[dict[str, Any]]) -> dict[str, Any]:
    clusters: dict[str, dict[str, Any]] = {}
    error_jobs = [j for j in jobs if j.get("enabled", True) and (j.get("last_status") == "error" or j.get("last_error") or j.get("last_delivery_error"))]
    for job in error_jobs:
        cid = classify_cron_error(job)
        cluster = clusters.setdefault(cid, {
            "cluster_id": cid,
            "side_effects": "local_read",
            "jobs": [],
            "evidence_refs": [],
            "next_local_actions": [],
        })
        cluster["jobs"].append({
            "id": job.get("id") or job.get("job_id"),
            "name": job.get("name"),
            "script": job.get("script"),
            "deliver": classify_delivery(job.get("deliver")),
            "last_status": job.get("last_status"),
            "last_error_excerpt": (job.get("last_delivery_error") or job.get("last_error") or "")[:240],
        })
    action_map = {
        "delivery_proxy": ["inspect gateway/proxy status", "read failed cron output artifact", "prepare resend packet only after exact external-send authority"],
        "model_provider_or_quota": ["run consult_models status/selfcheck", "mark model-quorum automation fail-closed when below quorum", "keep deterministic local checks running"],
        "script_runtime": ["run script directly in local shell", "capture traceback", "patch with targeted test before changing production script"],
        "storage_or_cleanup": ["measure storage/log sizes", "prefer dry-run cleanup", "require rollback/backup before destructive cleanup"],
        "delivery_local": ["inspect local cron output path", "verify deliver=local receipt"],
        "other_cron_error": ["read cron output artifact", "classify manually into a stable cluster if repeated"],
    }
    for cid, cluster in clusters.items():
        cluster["count"] = len(cluster["jobs"])
        cluster["next_local_actions"] = action_map.get(cid, action_map["other_cron_error"])
        cluster["evidence_refs"] = [j["id"] for j in cluster["jobs"] if j.get("id")]
    ordered = sorted(clusters.values(), key=lambda c: (-c["count"], c["cluster_id"]))
    return {
        "schema": "hermes_cron_error_clusters_v1",
        "generated_at": utc_now(),
        "clusters": ordered,
        "summary": {"error_jobs": len(error_jobs), "clusters": len(ordered)},
    }


def run_command(cmd: list[str], timeout: int = 45) -> dict[str, Any]:
    try:
        proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
        return {"cmd": cmd, "exit_code": proc.returncode, "output": proc.stdout[-4000:]}
    except FileNotFoundError as exc:
        return {"cmd": cmd, "exit_code": 127, "output": str(exc)}
    except subprocess.TimeoutExpired as exc:
        raw = exc.stdout or ""
        output = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else str(raw)
        return {"cmd": cmd, "exit_code": 124, "output": (output + "\nTIMEOUT")[-4000:]}


def build_lark_health_snapshot(home: Path | None = None, runner: Any | None = None) -> dict[str, Any]:
    home = Path(home or Path.home())
    root = hermes_root(home)
    profile = root / "project-profiles" / "lark.json"
    script = root / "scripts" / "lark_task_flow.py"
    if not profile.exists():
        return {
            "schema": "hermes_lark_health_snapshot_v1",
            "generated_at": utc_now(),
            "status": "not_applicable",
            "side_effects": "local_read",
            "summary": {"ok": True, "configured": False},
        }
    if not script.exists():
        return {
            "schema": "hermes_lark_health_snapshot_v1",
            "generated_at": utc_now(),
            "status": "reader_missing",
            "side_effects": "local_read",
            "summary": {"ok": False, "configured": True},
        }
    command_runner = runner or (lambda cmd: run_command(cmd, timeout=45))
    result = command_runner([sys.executable, str(script), "--health-check"])
    try:
        payload = json.loads(str(result.get("output") or "{}"))
    except json.JSONDecodeError:
        payload = {}
    ok = result.get("exit_code") == 0 and payload.get("ok") is True and payload.get("stage") == "auth"
    auth_payload = payload.get("auth")
    auth: dict[str, Any] = auth_payload if isinstance(auth_payload, dict) else {}
    return {
        "schema": "hermes_lark_health_snapshot_v1",
        "generated_at": utc_now(),
        "status": "ready" if ok else "degraded",
        "side_effects": "local_read",
        "may_open_browser": False,
        "may_read_tasks": False,
        "may_write_lark": False,
        "command": f"{sys.executable} {script} --health-check",
        "exit_code": result.get("exit_code"),
        "stage": payload.get("stage"),
        "auth_action": auth.get("action"),
        "summary": {"ok": ok, "configured": True},
    }


def discover_recent_provider_runtime_evidence(home: Path | None = None, freshness_seconds: int = 3600, min_quorum: int = 2) -> dict[str, Any] | None:
    home = Path(home or Path.home())
    candidates = sorted(home.glob(".hermes/tick-*/final/certification_manifest.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    now = datetime.now(timezone.utc)
    for manifest_path in candidates:
        manifest = read_json(manifest_path, {})
        if not isinstance(manifest, dict):
            continue
        generated_raw = str(manifest.get("generated_at") or "")
        try:
            generated = datetime.fromisoformat(generated_raw.replace("Z", "+00:00"))
        except ValueError:
            continue
        age_seconds = max(0.0, (now - generated).total_seconds())
        if age_seconds > freshness_seconds:
            continue
        gates_payload = manifest.get("gates")
        gates: dict[str, Any] = gates_payload if isinstance(gates_payload, dict) else {}
        actual_calls = int(gates.get("planner_count") or 0)
        successful_calls = int(gates.get("success_count") or 0)
        artifacts_payload = manifest.get("artifacts")
        artifacts: dict[str, Any] = artifacts_payload if isinstance(artifacts_payload, dict) else {}
        plans_payload = artifacts.get("plans")
        plans: dict[str, Any] = plans_payload if isinstance(plans_payload, dict) else {}
        plan_files = [Path(item.get("path", "")) for item in plans.get("files", []) if isinstance(item, dict)]
        tick_dir = manifest_path.parents[1]
        refs = [str(manifest_path)] + [str(tick_dir / path) for path in plan_files if path and (tick_dir / path).exists()]
        if actual_calls >= min_quorum and successful_calls >= min_quorum and len(refs) >= min_quorum + 1:
            return {
                "status": "PASS",
                "actual_calls": actual_calls,
                "successful_calls": successful_calls,
                "min_quorum": min_quorum,
                "evidence_refs": refs,
                "observed_at": generated_raw,
                "freshness_seconds": freshness_seconds,
                "age_seconds": round(age_seconds, 1),
                "global_certification_status": manifest.get("status"),
            }
    return None


def build_provider_health_snapshot(
    home: Path | None = None,
    runner: Any | None = None,
    runtime_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    home = Path(home or Path.home())
    command_runner = runner or (lambda cmd: run_command(cmd, timeout=45))
    script = hermes_root(home) / "scripts" / "consult_models.py"
    commands: list[dict[str, Any]] = []
    if script.exists() or runner is not None:
        for args in [["python3", str(script), "selfcheck"], ["python3", str(script), "status"]]:
            result = command_runner(args)
            if "cmd" not in result:
                result = {"cmd": args, **result}
            commands.append(result)
    else:
        commands.append({"cmd": ["python3", str(script), "selfcheck"], "exit_code": 127, "output": "consult_models.py not found"})

    static_ready = bool(commands) and all(c.get("exit_code") == 0 for c in commands)
    combined = "\n".join(str(c.get("output", "")) for c in commands).lower()
    degraded_markers = ["no planners", "below min_quorum", "quota", "unhealthy", "timeout", "rate limit", "429", "fail_closed"]
    static_degraded = (not static_ready) or any(marker in combined for marker in degraded_markers)

    supplied = runtime_evidence or {}
    actual_calls = int(supplied.get("actual_calls") or 0)
    successful_calls = int(supplied.get("successful_calls") or 0)
    min_quorum = int(supplied.get("min_quorum") or 1)
    runtime_verified = (
        str(supplied.get("status", "")).upper() == "PASS"
        and actual_calls > 0
        and successful_calls >= min_quorum
        and min_quorum > 0
        and bool(supplied.get("evidence_refs"))
    )
    runtime = {
        "status": "verified" if runtime_verified else ("degraded" if supplied else "not_verified"),
        "actual_calls": actual_calls,
        "successful_calls": successful_calls,
        "min_quorum": min_quorum,
        "evidence_refs": list(supplied.get("evidence_refs") or []),
        "source_status": supplied.get("status", "absent"),
    }
    degraded = static_degraded or not runtime_verified
    ok = static_ready and runtime_verified and not static_degraded
    return {
        "schema": "hermes_provider_health_snapshot_v2",
        "generated_at": utc_now(),
        "side_effects": "local_read",
        "commands": commands,
        "readiness": {"status": "ready" if static_ready and not static_degraded else "degraded", "static_only": True},
        "runtime": runtime,
        "certification_status": "runtime_quorum_verified_not_global_certification" if ok else "not_certified",
        "routing_safety": "deterministic_checks_may_continue_model_certification_still_requires_quorum" if ok else "fail_closed_for_model_quorum_automation",
        "summary": {"commands": len(commands), "static_ready": static_ready and not static_degraded, "runtime_verified": runtime_verified, "ok": ok, "degraded": degraded},
    }


def generate_repair_packets(registry: dict[str, Any], cron_clusters: dict[str, Any]) -> dict[str, Any]:
    packets: list[dict[str, Any]] = []
    cluster_ids = {c.get("cluster_id") for c in cron_clusters.get("clusters", [])}
    if "delivery_proxy" in cluster_ids:
        packets.append({
            "packet_id": "repair.delivery_proxy",
            "deliver": "local",
            "may_send_external": False,
            "side_effects": "local_read",
            "reason": "External delivery failure cluster detected; prepare local repair evidence without sending.",
            "requires_authority_for": ["external_send", "resend", "gateway_restart_if_disruptive"],
            "next_local_actions": [
                "read affected cron output artifact",
                "check gateway/proxy process and recent errors",
                "prepare exact resend target/payload/readback packet if user later authorizes external send",
            ],
            "evidence_refs": [c for c in cron_clusters.get("clusters", []) if c.get("cluster_id") == "delivery_proxy"],
        })
    if "model_provider_or_quota" in cluster_ids or any("provider_health_watch" in s.get("missing_checks", []) for s in registry.get("systems", [])):
        packets.append({
            "packet_id": "repair.model_provider_health",
            "deliver": "local",
            "may_send_external": False,
            "side_effects": "local_read",
            "reason": "Model/provider or quota cluster affects multi-model certification; keep automation fail-closed for model quorum claims.",
            "requires_authority_for": ["credential_entry", "provider_config_change", "model_certification_claim"],
            "next_local_actions": ["run provider health snapshot", "route deterministic checks around model quorum", "only re-enable certification after quorum evidence"],
            "evidence_refs": [c for c in cron_clusters.get("clusters", []) if c.get("cluster_id") == "model_provider_or_quota"],
        })
    return {
        "schema": "hermes_local_repair_packets_v1",
        "generated_at": utc_now(),
        "packets": packets,
        "summary": {"packets": len(packets)},
    }


def lifecycle_policy(risk_level: str) -> dict[str, Any]:
    if risk_level == "high":
        return {"severity": "high", "review_sla_hours": 24, "resolved_retention_runs": 5, "stale_after_runs": 3}
    if risk_level == "medium":
        return {"severity": "medium", "review_sla_hours": 72, "resolved_retention_runs": 4, "stale_after_runs": 5}
    return {"severity": "low", "review_sla_hours": 168, "resolved_retention_runs": 2, "stale_after_runs": 8}


def active_lifecycle_items_from_registry(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    active: dict[str, dict[str, Any]] = {}
    for system in registry.get("systems", []):
        system_id = system.get("system_id")
        for check_id in system.get("missing_checks", []):
            key = f"{system_id}::{check_id}"
            active[key] = {
                "key": key,
                "system_id": system_id,
                "check_id": check_id,
                "issue_type": "engineering_gap",
                "risk_level": system.get("risk_level", "low"),
                "kind": system.get("kind"),
                "evidence_refs": system.get("evidence_refs", []),
            }
        for finding_id in system.get("operational_findings", []):
            key = f"{system_id}::operational::{finding_id}"
            risk = "high" if finding_id == "delivery_errors_observed" else "medium" if finding_id in {"cron_errors_observed", "provider_runtime_not_verified_or_degraded", "lark_auth_or_reader_degraded"} else "low"
            active[key] = {
                "key": key,
                "system_id": system_id,
                "check_id": finding_id,
                "issue_type": "operational_finding",
                "risk_level": risk,
                "kind": system.get("kind"),
                "evidence_refs": system.get("evidence_refs", []),
            }
    return active


def update_coverage_lifecycle(registry: dict[str, Any], previous: dict[str, Any] | None = None, now: str | None = None) -> dict[str, Any]:
    now = now or utc_now()
    previous_items = (previous or {}).get("items", {}) if isinstance(previous, dict) else {}
    active = active_lifecycle_items_from_registry(registry)
    items: dict[str, dict[str, Any]] = {}
    retired: list[dict[str, Any]] = []

    for key, current in active.items():
        old = previous_items.get(key, {}) if isinstance(previous_items, dict) else {}
        item = {
            "key": key,
            "system_id": current["system_id"],
            "check_id": current["check_id"],
            "issue_type": current.get("issue_type", "engineering_gap"),
            "kind": current.get("kind"),
            "status": "active",
            "risk_level": current.get("risk_level", "low"),
            "first_seen_at": old.get("first_seen_at") or now,
            "last_seen_at": now,
            "resolved_at": None,
            "seen_count": int(old.get("seen_count", 0)) + 1,
            "absent_count": 0,
            "evidence_refs": current.get("evidence_refs", []),
            "retention_policy": lifecycle_policy(current.get("risk_level", "low")),
            "allowed_next_states": ["active", "resolved", "stale", "retired"],
            "side_effects": "local_write_artifact_only",
        }
        if old.get("status") == "resolved":
            item["reopened_at"] = now
        items[key] = item

    for key, old in previous_items.items() if isinstance(previous_items, dict) else []:
        if key in active:
            continue
        old_policy = old.get("retention_policy") or lifecycle_policy(old.get("risk_level", "low"))
        absent_count = int(old.get("absent_count", 0)) + 1
        if old.get("status") == "resolved" and absent_count > int(old_policy.get("resolved_retention_runs", 2)):
            retired.append({"key": key, "retired_at": now, "reason": "resolved_retention_elapsed", "previous_status": old.get("status")})
            continue
        item = dict(old)
        item["status"] = "resolved"
        item["resolved_at"] = old.get("resolved_at") or now
        item["absent_count"] = absent_count
        item["last_absent_at"] = now
        item["retention_policy"] = old_policy
        item["allowed_next_states"] = ["resolved", "active", "retired"]
        items[key] = item

    return {
        "schema": "hermes_coverage_lifecycle_v1",
        "generated_at": now,
        "items": items,
        "retired": retired,
        "summary": {
            "active": sum(1 for i in items.values() if i.get("status") == "active"),
            "resolved": sum(1 for i in items.values() if i.get("status") == "resolved"),
            "retired": len(retired),
            "total": len(items),
        },
    }


def latest_output_excerpt(home: Path, job_id: str, limit: int = 1200) -> dict[str, Any]:
    output_dir = hermes_root(home) / "cron" / "output" / job_id
    if not output_dir.exists():
        return {"output_dir": str(output_dir), "latest_output_path": None, "latest_output_excerpt": ""}
    files = sorted([p for p in output_dir.glob("*") if p.is_file()], key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return {"output_dir": str(output_dir), "latest_output_path": None, "latest_output_excerpt": ""}
    latest = files[0]
    text = latest.read_text(encoding="utf-8", errors="replace")
    return {"output_dir": str(output_dir), "latest_output_path": str(latest), "latest_output_excerpt": text[-limit:]}


def build_delivery_proxy_diagnostics(home: Path | None, cron_clusters: dict[str, Any], runner: Any | None = None) -> dict[str, Any]:
    home = Path(home or Path.home())
    command_runner = runner or (lambda cmd: run_command(cmd, timeout=20))
    delivery_clusters = [c for c in cron_clusters.get("clusters", []) if c.get("cluster_id") == "delivery_proxy"]
    jobs = [j for c in delivery_clusters for j in c.get("jobs", [])]
    diagnosed = []
    for job in jobs:
        job_id = str(job.get("id") or "")
        if not job_id:
            continue
        diagnosed.append({**job, **latest_output_excerpt(home, job_id)})
    commands = [
        command_runner(["bash", "-lc", "ps aux | egrep 'hermes_cli.main gateway|gateway run|telegram' | egrep -v 'egrep' | head -20"]),
        command_runner(["bash", "-lc", "env | egrep -i '^(http_proxy|https_proxy|all_proxy|no_proxy|NO_PROXY)=' || true"]),
    ]
    normalized_commands = []
    for cmd, result in zip(["gateway_process_scan", "proxy_env_scan"], commands):
        normalized_commands.append({"name": cmd, "exit_code": result.get("exit_code"), "output": str(result.get("output", ""))[-1600:]})
    return {
        "schema": "hermes_delivery_proxy_diagnostics_v1",
        "generated_at": utc_now(),
        "deliver": "local",
        "may_send_external": False,
        "side_effects": "local_read",
        "jobs": diagnosed,
        "commands": normalized_commands,
        "summary": {"diagnosed_jobs": len(diagnosed), "commands": len(normalized_commands)},
        "requires_authority_for": ["external_send", "resend", "disruptive_gateway_restart", "proxy_config_write"],
    }


def write_json(path: Path, data: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(path)


def default_events_from_git(home: Path) -> list[dict[str, Any]]:
    repo = hermes_root(home) / "hermes-agent"
    if not (repo / ".git").exists():
        return []
    try:
        out = subprocess.check_output(["git", "-C", str(repo), "diff", "--name-only"], text=True, timeout=10)
    except Exception:
        return []
    return [{"kind": "changed_file", "path": line.strip()} for line in out.splitlines() if line.strip()]


def run_once(home: Path | None = None, output_dir: Path | None = None, events: list[dict[str, Any]] | None = None, quiet_success: bool = False) -> dict[str, Any]:
    home = Path(home or Path.home())
    root = hermes_root(home)
    output_dir = Path(output_dir or (root / "state" / "selfcheck"))
    profile = discover_user_system_profile(home)
    provider_runtime_evidence = discover_recent_provider_runtime_evidence(home)
    provider_health = build_provider_health_snapshot(home, runtime_evidence=provider_runtime_evidence)
    lark_health = build_lark_health_snapshot(home)
    registry = build_coverage_registry(profile, snapshots={"provider_health": provider_health, "lark_health": lark_health})
    if events is None:
        events = default_events_from_git(home)
    plan = plan_from_events(events)
    proposals = generate_proposals(registry)
    cron_data = read_json(root / "cron" / "jobs.json", {"jobs": []})
    jobs = cron_data.get("jobs", []) if isinstance(cron_data, dict) else []
    cron_clusters = cluster_cron_errors(jobs)
    repair_packets = generate_repair_packets(registry, cron_clusters)
    delivery_diagnostics = build_delivery_proxy_diagnostics(home, cron_clusters)
    previous_lifecycle = read_json(output_dir / "coverage_lifecycle.json", {})
    lifecycle = update_coverage_lifecycle(registry, previous=previous_lifecycle if isinstance(previous_lifecycle, dict) else None)
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    result = {
        "schema": "hermes_dynamic_selfcheck_run_v1",
        "generated_at": utc_now(),
        "profile_path": write_json(output_dir / "user_system_profile.json", profile),
        "registry_path": write_json(output_dir / "coverage_registry.json", registry),
        "plan_path": write_json(output_dir / f"coverage_plan_{ts}.json", plan),
        "proposals_path": write_json(output_dir / "coverage_proposals.json", {"schema": PROPOSAL_SCHEMA, "generated_at": utc_now(), "proposals": proposals}),
        "cron_error_clusters_path": write_json(output_dir / "cron_error_clusters.json", cron_clusters),
        "provider_health_path": write_json(output_dir / "provider_health_snapshot.json", provider_health),
        "lark_health_path": write_json(output_dir / "lark_health_snapshot.json", lark_health),
        "repair_packets_path": write_json(output_dir / "repair_packets.json", repair_packets),
        "delivery_proxy_diagnostics_path": write_json(output_dir / "delivery_proxy_diagnostics.json", delivery_diagnostics),
        "coverage_lifecycle_path": write_json(output_dir / "coverage_lifecycle.json", lifecycle),
        "summary": {
            "systems": registry["summary"]["systems"],
            "missing_checks": registry["summary"]["missing_checks"],
            "high_risk_systems": registry["summary"]["high_risk_systems"],
            "plan_checks": plan["summary"]["checks"],
            "proposals": len(proposals),
            "cron_error_clusters": cron_clusters["summary"]["clusters"],
            "repair_packets": repair_packets["summary"]["packets"],
            "provider_health_degraded": provider_health["summary"]["degraded"],
            "lark_health_degraded": not lark_health["summary"]["ok"],
            "operational_findings": registry["summary"]["operational_findings"],
            "delivery_diagnostics_jobs": delivery_diagnostics["summary"]["diagnosed_jobs"],
            "lifecycle_active": lifecycle["summary"]["active"],
            "lifecycle_resolved": lifecycle["summary"]["resolved"],
            "lifecycle_retired": lifecycle["summary"]["retired"],
        },
    }
    write_json(output_dir / "last_run.json", result)
    if quiet_success and not (result["summary"]["missing_checks"] or result["summary"]["high_risk_systems"] or result["summary"]["cron_error_clusters"] or result["summary"]["provider_health_degraded"] or result["summary"]["lark_health_degraded"]):
        return result
    return result


def parse_event(values: list[str]) -> list[dict[str, Any]]:
    events = []
    for value in values:
        if ":" in value:
            kind, path = value.split(":", 1)
            events.append({"kind": kind, "path": path})
        else:
            events.append({"kind": "changed_file", "path": value})
    return events


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Hermes dynamic self-check coverage artifacts.")
    sub = parser.add_subparsers(dest="cmd")
    run_p = sub.add_parser("run")
    run_p.add_argument("--home", type=Path, default=Path.home())
    run_p.add_argument("--output-dir", type=Path, default=None)
    run_p.add_argument("--event", action="append", default=[], help="kind:path, defaults to changed_file:path")
    run_p.add_argument("--quiet-success", action="store_true")
    args = parser.parse_args(argv)
    if args.cmd in {None, "run"}:
        events = parse_event(args.event) if args.event else None
        result = run_once(home=args.home, output_dir=args.output_dir, events=events, quiet_success=args.quiet_success)
        if not args.quiet_success or result["summary"]["missing_checks"] or result["summary"]["high_risk_systems"]:
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
