#!/usr/bin/env python3
"""Workflow assetization decision, validation, and scaffold CLI.

This is a local, fail-closed Workflow Kernel Loop Engineering helper. It does
not execute external actions, mutate taskpool/cron/AgentOS, send messages, or
write memory. It only classifies a seed, compiles a draft asset, validates an
asset, and optionally scaffolds a local workflow workspace.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "hermes_workflow_asset_v1"
MATURITY = {
    "seed",
    "draft",
    "candidate",
    "validated",
    "common",
    "canonical",
    "deprecated",
    "archived",
    "revoked",
}
RETENTION = {
    "session_only",
    "project_scoped",
    "domain_reusable",
    "global_reusable",
    "pinned",
    "cleanable",
    "quarantine",
}
SIDE_EFFECT_WORDS = (
    "telegram",
    "lark",
    "飞书",
    "发送",
    "发到",
    "外发",
    "关闭任务",
    "done",
    "cron",
    "agentos",
    "taskpool",
    "发布",
    "部署",
    "push",
    "删除",
)
EVIDENCE_WORDS = ("证据", "验证", "测试", "读回", "截图", "api", "日志", "来源", "evidence")
REUSE_WORDS = ("以后", "每次", "自动", "长期", "复用", "常用", "形成", "稳定", "一律", "默认")
COMPLEX_WORDS = (
    "竞品",
    "客群",
    "变现",
    "风险",
    "入池",
    "多模型",
    "生命周期",
    "治理",
    "工作流",
    "能力图",
    "门禁",
    "路由",
)
ONE_OFF_WORDS = ("今天", "这次", "临时", "一下", "这三个文件", "当前这个", "一次性")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_id(seed: str, prefix: str = "wfa") -> str:
    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", seed.strip().lower())[:32].strip("-")
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:10]
    if not slug:
        slug = "seed"
    return f"{prefix}-{slug}-{digest}"


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    lower = text.lower()
    return any(n.lower() in lower for n in needles)


def decide_assetization(seed: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    context = context or {}
    observed_repetition = int(context.get("observed_repetition", 0) or 0)
    explicit_one_off = context.get("task_scope") == "one_off" or _contains_any(seed, ONE_OFF_WORDS)

    score = 0
    reasons: list[str] = []
    warnings: list[str] = []

    if not explicit_one_off and (_contains_any(seed, REUSE_WORDS) or observed_repetition >= 2):
        score += 2
        reasons.append("reuse_value")
    if _contains_any(seed, COMPLEX_WORDS):
        score += 2
        reasons.append("multi_step_complexity")
    if _contains_any(seed, EVIDENCE_WORDS):
        score += 2
        reasons.append("evidence_gap")
    if observed_repetition >= 2:
        score += 1
        if "reuse_value" not in reasons:
            reasons.append("reuse_value")
    if _contains_any(seed, SIDE_EFFECT_WORDS):
        score += 2
        reasons.append("risk_surface")
        warnings.append("exact_authority_required")
    if "工作流" in seed:
        score += 1
        reasons.append("workflow_word_signal_only")
    if explicit_one_off:
        score -= 4
        reasons.append("one_off")

    side_effect_class = "external_or_lifecycle" if _contains_any(seed, SIDE_EFFECT_WORDS) else "local_read_write_only"
    stop_only_on = ["missing_evidence_after_attempt", "user_preference_conflict"]
    if side_effect_class == "external_or_lifecycle":
        stop_only_on.insert(0, "authority_boundary")
        stop_only_on.append("destructive_or_external_side_effect")

    if explicit_one_off:
        decision = "session_plan"
        landing = ["session_plan"]
    elif score >= 6:
        decision = "reusable_candidate"
        landing = ["workflow_workspace", "skill_reference_candidate"]
    elif score >= 4:
        decision = "project_scoped_candidate"
        landing = ["workflow_workspace"]
    elif score >= 2:
        decision = "output_template_fragment"
        landing = ["session_plan", "output_template_fragment"]
    else:
        decision = "no_asset"
        landing = ["no_write"]

    return {
        "schema": "hermes_workflow_asset_decision_v1",
        "id": stable_id(seed, "wfd"),
        "seed": seed,
        "score": max(score, 0),
        "decision": decision,
        "landing": landing,
        "reasons": reasons,
        "warnings": warnings,
        "side_effect_class": side_effect_class,
        "stop_only_on": stop_only_on,
        "created_at": utc_now(),
        "policy": {
            "keyword_trigger_sufficient": False,
            "model_consensus_is_proof": False,
            "external_side_effects_enabled": False,
            "memory_workflow_body_write_enabled": False,
        },
    }


def default_workflow_asset(title: str, seed: str) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "id": stable_id(seed),
        "title": title,
        "version": 1,
        "source": {"user_seed": seed, "source_refs": []},
        "classification": {
            "workflow_type": "hybrid",
            "scope": "domain",
            "maturity": "draft",
            "retention": "domain_reusable",
        },
        "intent_model": {
            "user_goal": seed,
            "success_criteria": ["safe local dry-run succeeds", "objective evidence is attached"],
            "non_goals": ["external dispatch without exact authority", "canonical promotion from a seed"],
            "assumptions": [],
            "ask_user_only_when": ["authority boundary", "durable preference conflict", "irreversible side effect"],
        },
        "routing": {
            "applies_when": ["repeated or long-term process pattern with evidence/governance need"],
            "does_not_apply_when": ["one-off task", "simple answer", "keyword-only workflow request with weak reuse"],
            "neighbor_workflows": [],
            "forbidden_triggers": ["the word workflow alone", "temporary task progress"],
            "examples_positive": [seed],
            "examples_negative": ["创建工作流：今天把这三个文件整理一下"],
        },
        "output_contract": {
            "allowed_formats": ["json", "markdown"],
            "default_format": "json",
            "ordering_rule": "risk and reuse value before convenience",
            "dedupe_rule": "merge same seed digest and same routing boundary",
            "overlap_rule": "prefer existing narrower workflow; avoid broad umbrella steal",
            "evidence_required": True,
            "confidence_required": True,
            "next_action_required": True,
        },
        "gates": [
            {
                "id": "assetization_decision_gate",
                "pass": "reuse/risk/evidence/governability score justifies candidate",
                "warn": "weak signal; keep as output fragment or project-scoped candidate",
                "fail": "one-off or no durable value; no asset write",
                "blocked": "retrieve context or evidence before promotion",
            },
            {
                "id": "authority_boundary_gate",
                "pass": "local reversible read/write only or exact authority present",
                "warn": "future automation mentioned but not authorized",
                "fail": "external/destructive/publish/credential boundary without authority",
                "blocked": "emit minimal authorization request; do not execute",
            },
        ],
        "model_routing": {
            "default_tier": "T1",
            "specialist_lanes": ["architecture", "verification"],
            "multimodel_required_when": ["canonical promotion", "global routing", "external side effect", "cron/taskpool/AgentOS enablement"],
        },
        "evidence": {"required_refs": [], "verification_commands": []},
        "lifecycle_policy": {
            "promote_when": ["route eval passes", "real or dry-run evidence attached", "negative/neighbor cases pass"],
            "demote_when": ["false trigger", "stale evidence", "user correction", "validation failure"],
            "cleanup_when": ["no usage", "superseded", "low evidence", "sprawl risk"],
            "protect_when": ["canonical with regression evidence", "pinned by user"],
            "superseded_by": None,
        },
        "loop_policy": {
            "self_advance": True,
            "max_autonomous_iterations": 3,
            "stop_only_on": ["authority_boundary", "missing_evidence_after_attempt", "destructive_or_external_side_effect", "user_preference_conflict"],
        },
    }


def compile_workflow_asset(decision: dict[str, Any]) -> dict[str, Any]:
    seed = decision["seed"]
    asset = default_workflow_asset("Workflow asset candidate", seed)
    if decision["decision"] == "project_scoped_candidate":
        asset["classification"]["scope"] = "project"
        asset["classification"]["retention"] = "project_scoped"
    elif decision["decision"] in {"session_plan", "no_asset"}:
        asset["classification"]["scope"] = "session"
        asset["classification"]["retention"] = "session_only"
    asset["source"]["decision"] = decision
    asset["loop_policy"]["stop_only_on"] = decision.get("stop_only_on", asset["loop_policy"]["stop_only_on"])
    if decision.get("side_effect_class") == "external_or_lifecycle":
        asset["model_routing"]["default_tier"] = "T3"
        asset["evidence"]["required_refs"].append("exact authority, rollback, and readback before side effects")
    return asset


def validate_workflow_asset(asset: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if asset.get("schema") != SCHEMA:
        issues.append("schema_mismatch")
    for path in ("id", "title", "version", "source", "classification", "routing", "output_contract", "gates", "lifecycle_policy", "loop_policy"):
        if path not in asset:
            issues.append(f"missing:{path}")
    classification = asset.get("classification", {})
    if classification.get("maturity") not in MATURITY:
        issues.append("invalid_maturity")
    if classification.get("retention") not in RETENTION:
        issues.append("invalid_retention")
    routing = asset.get("routing", {})
    for key in ("applies_when", "does_not_apply_when", "examples_positive", "examples_negative", "forbidden_triggers"):
        if not routing.get(key):
            issues.append(f"missing_routing:{key}")
    output = asset.get("output_contract", {})
    for key in ("ordering_rule", "dedupe_rule", "overlap_rule"):
        if not output.get(key):
            issues.append(f"missing_output_contract:{key}")
    if output.get("evidence_required") is not True:
        issues.append("evidence_not_required")
    if not asset.get("gates"):
        issues.append("missing_gates")
    lifecycle = asset.get("lifecycle_policy", {})
    for key in ("promote_when", "demote_when", "cleanup_when"):
        if not lifecycle.get(key):
            issues.append(f"missing_lifecycle:{key}")
    if classification.get("maturity") == "canonical":
        refs = asset.get("evidence", {}).get("required_refs", []) + asset.get("evidence", {}).get("verification_commands", [])
        joined = " ".join(str(r) for r in refs).lower()
        if "validated" not in joined and "regression" not in joined:
            issues.append("canonical_without_validation_evidence")
    return issues


def scaffold_workspace(asset: dict[str, Any], root: Path | None = None) -> dict[str, Any]:
    root = root or (Path.home() / ".hermes" / "workflows" / "assets")
    workdir = root / asset["id"]
    workdir.mkdir(parents=True, exist_ok=True)
    state = {
        "schema": "hermes_workflow_asset_state_v1",
        "asset_id": asset["id"],
        "maturity": asset["classification"]["maturity"],
        "retention": asset["classification"]["retention"],
        "status": "draft_scaffolded",
        "created_at": utc_now(),
        "external_side_effects_enabled": False,
        "cron_enabled": False,
        "taskpool_lifecycle_mutation_enabled": False,
        "agentos_runtime_mutation_enabled": False,
    }
    eval_cases = {
        "schema": "hermes_workflow_asset_eval_cases_v1",
        "asset_id": asset["id"],
        "positive": asset["routing"].get("examples_positive", []),
        "negative": asset["routing"].get("examples_negative", []),
        "neighbor": asset["routing"].get("neighbor_workflows", []),
        "forbidden": asset["routing"].get("forbidden_triggers", []),
    }
    (workdir / "workflow.json").write_text(json.dumps(asset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (workdir / "state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (workdir / "eval-cases.json").write_text(json.dumps(eval_cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    evidence = {"ts": utc_now(), "event": "scaffolded", "asset_id": asset["id"], "side_effects_enabled": False}
    with (workdir / "evidence.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(evidence, ensure_ascii=False, sort_keys=True) + "\n")
    return {
        "status": "ok",
        "workdir": str(workdir),
        "files": ["workflow.json", "state.json", "eval-cases.json", "evidence.jsonl"],
        "side_effects": {"external": False, "cron": False, "taskpool": False, "agentos": False},
    }


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Workflow asset decision/validator/scaffold helper")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_decide = sub.add_parser("decide")
    p_decide.add_argument("--seed", required=True)
    p_decide.add_argument("--observed-repetition", type=int, default=0)
    p_decide.add_argument("--task-scope", choices=["one_off", "unknown"], default="unknown")
    p_compile = sub.add_parser("compile")
    p_compile.add_argument("--seed", required=True)
    p_compile.add_argument("--observed-repetition", type=int, default=0)
    p_compile.add_argument("--task-scope", choices=["one_off", "unknown"], default="unknown")
    p_validate = sub.add_parser("validate")
    p_validate.add_argument("--asset", required=True)
    p_scaffold = sub.add_parser("scaffold")
    p_scaffold.add_argument("--seed", required=True)
    p_scaffold.add_argument("--observed-repetition", type=int, default=0)
    p_scaffold.add_argument("--task-scope", choices=["one_off", "unknown"], default="unknown")
    p_scaffold.add_argument("--root", default=str(Path.home() / ".hermes" / "workflows" / "assets"))
    args = parser.parse_args(argv)

    if args.cmd in {"decide", "compile", "scaffold"}:
        ctx = {"observed_repetition": args.observed_repetition}
        if args.task_scope == "one_off":
            ctx["task_scope"] = "one_off"
        decision = decide_assetization(args.seed, ctx)
        if args.cmd == "decide":
            print(json.dumps(decision, ensure_ascii=False, indent=2))
            return 0
        asset = compile_workflow_asset(decision)
        if args.cmd == "compile":
            print(json.dumps(asset, ensure_ascii=False, indent=2))
            return 0
        receipt = scaffold_workspace(asset, Path(args.root))
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "validate":
        asset = _load_json(Path(args.asset))
        issues = validate_workflow_asset(asset)
        result = {"status": "PASS" if not issues else "FAIL", "issues": issues}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if not issues else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
