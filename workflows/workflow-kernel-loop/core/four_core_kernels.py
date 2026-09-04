#!/usr/bin/env python3
"""Four decoupled workflow-kernel contracts.

Local-only core module. It performs pure JSON transformations for:
1. intent normalization
2. landing-zone classification
3. authority/evidence gating
4. lifecycle promotion/cleanup

It intentionally does not import Hermes runtime helpers, mutate memory, schedule cron,
write taskpool/AgentOS state, dispatch externally, publish/deploy/push, delete
resources, or enter credentials. File writes are only done by the optional CLI when
--out is supplied by the caller.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_PREFIX = "hermes_four_core_kernel"
SIDE_EFFECT_CLASSES = {
    "none",
    "read_only",
    "local_write",
    "external_read",
    "external_write",
    "scheduler_cron",
    "taskpool_lifecycle",
    "publish_deploy_push",
    "destructive",
    "credential_payment_secret",
}
AUTHORIZED_AUTONOMOUS = {"none", "read_only", "local_write"}
MATURITY_ORDER = ["seed", "draft", "candidate", "validated", "common", "canonical"]
TERMINAL_OR_NEGATIVE = {"deprecated", "quarantined", "archived", "revoked"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_id(text: str, prefix: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", text.strip().lower())[:36].strip("-") or "item"
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{slug}-{digest}"


def contains_any(text: str, words: list[str]) -> bool:
    lower = text.lower()
    return any(w.lower() in lower for w in words)


def normalize_intent(user_request: str, source_refs: list[str] | None = None, active_context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Normalize prose into a candidate WorkflowSeed; no persistence or execution."""
    source_refs = source_refs or []
    active_context = active_context or {}
    risk_words = ["发送", "外发", "cron", "taskpool", "agentos", "发布", "部署", "删除", "push", "sudo", "credential", "secret"]
    reuse_words = ["长期", "复用", "每次", "以后", "固化", "workflow", "工作流", "模块", "内核"]
    one_off_words = ["今天", "这次", "临时", "一下", "一次性"]
    expected = "reusable_kernel_candidate" if contains_any(user_request, reuse_words) else "session_answer_or_plan"
    risk_level = "high" if contains_any(user_request, risk_words) else ("medium" if contains_any(user_request, reuse_words) else "low")
    non_goals = [
        "do not treat original prose as execution authority",
        "do not persist to memory/skill/project state from normalization",
        "do not create cron/taskpool/AgentOS/external effects",
    ]
    if contains_any(user_request, one_off_words):
        non_goals.append("do not create reusable assets for explicit one-off work")
    return {
        "schema": f"{SCHEMA_PREFIX}_workflow_seed_v1",
        "id": stable_id(user_request, "seed"),
        "source": {"user_request": user_request, "source_refs": source_refs},
        "goal": user_request.strip(),
        "non_goals": non_goals,
        "active_context_keys": sorted(active_context.keys()),
        "authority_boundary": "exact_authority_required" if risk_level == "high" else "local_only",
        "risk_level": risk_level,
        "expected_artifact": expected,
        "ask_user_only_when": ["authority boundary", "durable preference conflict", "irreversible side effect"],
        "normalization_warnings": [],
    }


def classify_landing_zone(workflow_seed: dict[str, Any], candidate_claims: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Classify durable placement without writing to the destination."""
    candidate_claims = candidate_claims or []
    text = workflow_seed.get("goal", "")
    decisions = []
    for claim in candidate_claims or [{"claim": text, "scope": "inferred"}]:
        claim_text = str(claim.get("claim", ""))
        if contains_any(claim_text, ["流程", "步骤", "坑", "验证清单", "workflow", "工作流", "模块", "内核"]):
            target = "skill_or_workflow_candidate"
            forbidden = ["global_memory_body", "cron_without_authority", "taskpool_without_authority"]
        elif contains_any(claim_text, ["PR", "commit", "issue", "已完成", "已修复", "进度"]):
            target = "session_or_project_progress_only"
            forbidden = ["global_memory", "global_skill"]
        elif contains_any(claim_text, ["用户偏好", "偏好", "总是", "不喜欢"]):
            target = "user_memory_candidate"
            forbidden = ["workflow_body", "task_progress"]
        elif contains_any(claim_text, ["项目", "repo", "SSOT", "ADR"]):
            target = "project_scoped_ssot_or_adr_candidate"
            forbidden = ["global_memory_unscoped"]
        else:
            target = "session_plan_or_no_write"
            forbidden = ["durable_global_write"]
        decisions.append({
            "claim": claim_text,
            "target": target,
            "scope": claim.get("scope", "unscoped"),
            "reason": "landing_policy_classification",
            "forbidden_targets": forbidden,
            "evidence_required": ["source_ref", "scope", "fresh_readback_before_claim"],
        })
    return {
        "schema": f"{SCHEMA_PREFIX}_landing_decision_v1",
        "seed_id": workflow_seed.get("id"),
        "decisions": decisions,
        "forbidden_global_effects": ["memory_pollution", "skill_bloat", "workflow_keyword_auto_create"],
    }


def authority_evidence_gate(proposed_action: str, target: str, side_effect_class: str, authority_context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Fail-closed authority decision plus evidence/readback contract."""
    authority_context = authority_context or {}
    if side_effect_class not in SIDE_EFFECT_CLASSES:
        status = "blocked"
        reason = "unknown_side_effect_class"
    elif side_effect_class in AUTHORIZED_AUTONOMOUS:
        status = "allowed"
        reason = "within_local_autonomous_boundary"
    elif authority_context.get("exact_authority_grant") and authority_context.get("exact_target") == target:
        status = "allowed_with_exact_authority"
        reason = "exact_authority_bound_to_target"
    else:
        status = "needs_exact_authority"
        reason = "side_effect_boundary_closed"
    receipt_required = side_effect_class not in {"none", "read_only"}
    return {
        "schema": f"{SCHEMA_PREFIX}_authority_evidence_decision_v1",
        "proposed_action": proposed_action,
        "target": target,
        "side_effect_class": side_effect_class,
        "status": status,
        "reason": reason,
        "required_receipt": receipt_required,
        "required_readback": True,
        "evidence_contract": {
            "command_or_api_exit_is_not_enough": True,
            "fresh_current_task_evidence_required": True,
            "negative_requirements_need_negative_evidence": True,
            "old_summary_is_not_evidence": True,
        },
        "prohibited_without_exact_authority": sorted(SIDE_EFFECT_CLASSES - AUTHORIZED_AUTONOMOUS),
    }


def lifecycle_transition(module_identity: str, current_maturity: str, evidence_ledger: list[dict[str, Any]] | None = None, route_eval_result: dict[str, Any] | None = None) -> dict[str, Any]:
    """Decide promotion/demotion/cleanup from evidence; never mutates registry."""
    evidence_ledger = evidence_ledger or []
    route_eval_result = route_eval_result or {}
    pass_count = sum(1 for e in evidence_ledger if e.get("status") in {"PASS", "pass", "success"})
    false_trigger_count = int(route_eval_result.get("false_trigger_count", 0) or 0)
    neighbor_collision_count = int(route_eval_result.get("neighbor_collision_count", 0) or 0)
    cleanup_policy_exists = bool(route_eval_result.get("cleanup_policy_exists"))
    negative_cases_pass = bool(route_eval_result.get("negative_cases_pass"))
    if current_maturity in TERMINAL_OR_NEGATIVE:
        action = "keep_terminal"
        next_maturity = current_maturity
        missing = []
    elif false_trigger_count or neighbor_collision_count:
        action = "quarantine"
        next_maturity = "quarantined"
        missing = []
    elif pass_count >= 3 and cleanup_policy_exists and negative_cases_pass:
        idx = MATURITY_ORDER.index(current_maturity) if current_maturity in MATURITY_ORDER else 0
        next_maturity = MATURITY_ORDER[min(idx + 1, MATURITY_ORDER.index("validated"))]
        action = "promote_one_step" if next_maturity != current_maturity else "keep"
        missing = []
    else:
        action = "keep_candidate_or_draft"
        next_maturity = current_maturity
        missing = []
        if pass_count < 3:
            missing.append(">=3_pass_evidence_events")
        if not cleanup_policy_exists:
            missing.append("cleanup_policy")
        if not negative_cases_pass:
            missing.append("negative_cases_pass")
    return {
        "schema": f"{SCHEMA_PREFIX}_lifecycle_transition_v1",
        "module_identity": module_identity,
        "current_maturity": current_maturity,
        "action": action,
        "next_maturity": next_maturity,
        "missing_evidence": missing,
        "finalizers_required": ["reference_scan", "absorbed_into_or_superseded_by_when_removed", "receipt_archive"],
        "canonical_guard": "never_promote_to_canonical_from_one_local_success",
    }


def run_four_core_pipeline(user_request: str, side_effect_class: str = "local_write") -> dict[str, Any]:
    seed = normalize_intent(user_request)
    landing = classify_landing_zone(seed)
    auth = authority_evidence_gate("materialize_local_candidate", "workflow-kernel-loop", side_effect_class, {})
    lifecycle = lifecycle_transition(
        "four_core_kernel_candidate",
        "candidate",
        evidence_ledger=[{"status": "PASS"}, {"status": "PASS"}, {"status": "PASS"}],
        route_eval_result={"false_trigger_count": 0, "neighbor_collision_count": 0, "cleanup_policy_exists": True, "negative_cases_pass": True},
    )
    return {
        "schema": f"{SCHEMA_PREFIX}_pipeline_receipt_v1",
        "status": "ok" if auth["status"] == "allowed" else "blocked_or_waiting_authority",
        "created_at": utc_now(),
        "seed": seed,
        "landing": landing,
        "authority_evidence": auth,
        "lifecycle": lifecycle,
        "side_effect_boundary": "local_transform_only; optional CLI --out local write only",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the decoupled four-core kernel pipeline")
    parser.add_argument("--seed", required=True)
    parser.add_argument("--side-effect-class", default="local_write", choices=sorted(SIDE_EFFECT_CLASSES))
    parser.add_argument("--out")
    args = parser.parse_args(argv)
    receipt = run_four_core_pipeline(args.seed, args.side_effect_class)
    text = json.dumps(receipt, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if receipt["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
