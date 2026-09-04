#!/usr/bin/env python3
"""Capability module pool, workflow graph planning, and synthesis ratchet.

Local-only helper for Workflow Kernel Loop Engineering. It validates capability
modules, keeps a JSON registry, compiles a seed into a module graph plan, records
usage-ledger events, and proposes composite module candidates from frequency plus
quality signals. It never invokes external actions, lifecycle writes, cron,
AgentOS, memory writes, publishing, deployment, deletion, or credentials.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REGISTRY_SCHEMA = "hermes_capability_module_registry_v1"
MODULE_SCHEMA = "hermes_capability_module_v1"
PLAN_SCHEMA = "hermes_workflow_module_plan_v1"
USAGE_SCHEMA = "hermes_capability_module_usage_event_v1"
SYNTHESIS_SCHEMA = "hermes_module_synthesis_candidate_v1"

MODULE_KINDS = {"atomic_module", "composite_module", "gate", "adapter", "presentation", "verifier"}
SIDE_EFFECTS = {"none", "local_write", "external_write", "lifecycle", "publish", "destructive"}
MATURITY = {"seed", "draft", "candidate", "validated", "common", "canonical", "deprecated", "archived", "revoked"}
NEED_ORDER = {
    "intent_normalization_kernel": 10,
    "landing_zone_kernel": 20,
    "authority_evidence_gate_kernel": 30,
    "lifecycle_promotion_cleanup_kernel": 40,
}
NEED_RULES = [
    ("intent_normalization_kernel", ("意图归一", "意图归一化", "workflowseed", "模糊需求", "intent normalization"), "workflow_seed"),
    ("landing_zone_kernel", ("落点", "落点判定", "landing zone", "memory污染", "skill膨胀", "沉淀到"), "landing_decision"),
    ("authority_evidence_gate_kernel", ("权限证据", "权限/证据", "证据门", "权限门", "evidence gate", "authority gate", "读回", "receipt"), "authority_decision"),
    ("lifecycle_promotion_cleanup_kernel", ("生命周期", "晋级", "清理", "promotion", "cleanup", "canonical", "finalizer"), "lifecycle_transition_decision"),
    ("source_evidence_collector", ("来源", "外链", "事实", "evidence source", "source evidence"), "evidence_refs"),
    ("business_analysis", ("商机", "商业", "竞品", "客群", "变现", "business", "competitor"), "business_analysis"),
    ("risk_modeler", ("风险", "合规", "安全", "risk"), "risk_report"),
    ("presentation_builder", ("美化", "输出", "呈现", "表格", "报告", "presentation"), "presentation_contract"),
    ("authority_gate", ("telegram", "发送", "外发", "关闭任务", "taskpool", "cron", "agentos", "发布", "部署", "删除"), "authority_decision"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_id(text: str, prefix: str = "cap") -> str:
    slug = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", text.strip().lower())[:40].strip("-") or "module"
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}-{slug}-{digest}"


def default_capability_module(
    module_id: str,
    responsibility: str,
    consumes: list[str] | None = None,
    produces: list[str] | None = None,
) -> dict[str, Any]:
    produces = produces or [module_id]
    consumes = consumes or ["seed"]
    return {
        "schema": MODULE_SCHEMA,
        "id": module_id,
        "title": module_id.replace("_", " ").title(),
        "version": 1,
        "kind": "atomic_module",
        "responsibility": responsibility,
        "contracts": {
            "consumes": consumes,
            "produces": produces,
            "input_contract": {"required": consumes, "optional": []},
            "output_contract": {"produces": produces, "evidence_required": True, "confidence_required": True},
            "presentation_contract": {"surfaces": ["cli", "markdown"], "style": "concise_evidence_first"},
        },
        "routing": {
            "applies_when": [responsibility],
            "does_not_apply_when": ["one-off simple answer", "keyword-only workflow request"],
            "positive_examples": [],
            "negative_examples": ["创建工作流：今天把这三个文件整理一下"],
            "neighbor_modules": [],
            "forbidden_triggers": ["the word workflow alone"],
        },
        "authority": {"side_effects": "none", "required_authority": [], "can_run_autonomously": True},
        "lifecycle": {"maturity": "candidate", "retention": "domain_reusable"},
        "metrics": {"usage_count": 0, "success_count": 0, "evidence_pass_rate": 0.0, "false_trigger_count": 0, "human_intervention_rate": 0.0},
        "promotion_policy": {
            "promote_when": ["successful_runs >= 2", "evidence_pass_rate >= 0.8", "negative_cases_pass"],
            "demote_when": ["false_trigger", "stale_evidence", "user_correction"],
            "cleanup_when": ["no_usage_for_ttl", "superseded_by_better_module"],
        },
    }


def validate_capability_module(module: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if module.get("schema") != MODULE_SCHEMA:
        issues.append("schema_mismatch")
    for key in ("id", "kind", "responsibility", "contracts", "routing", "authority", "lifecycle", "metrics"):
        if key not in module:
            issues.append(f"missing:{key}")
    if module.get("kind") not in MODULE_KINDS:
        issues.append("invalid_kind")
    contracts = module.get("contracts", {})
    if not contracts.get("consumes") or not contracts.get("produces"):
        issues.append("missing_stable_io")
    routing = module.get("routing", {})
    for key in ("applies_when", "does_not_apply_when", "negative_examples", "forbidden_triggers"):
        if not routing.get(key):
            issues.append(f"missing_routing:{key}")
    authority = module.get("authority", {})
    side_effects = authority.get("side_effects")
    if side_effects not in SIDE_EFFECTS:
        issues.append("invalid_side_effects")
    if side_effects in {"external_write", "lifecycle", "publish", "destructive"} and not authority.get("required_authority"):
        issues.append("external_side_effect_without_authority")
    lifecycle = module.get("lifecycle", {})
    if lifecycle.get("maturity") not in MATURITY:
        issues.append("invalid_maturity")
    return issues


def load_registry(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"schema": REGISTRY_SCHEMA, "modules": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("schema", REGISTRY_SCHEMA)
    data.setdefault("modules", [])
    return data


def save_registry(path: Path, registry: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def register_module(registry: dict[str, Any], module: dict[str, Any]) -> dict[str, Any]:
    issues = validate_capability_module(module)
    if issues:
        raise ValueError("invalid module: " + ",".join(issues))
    modules = [m for m in registry.get("modules", []) if m.get("id") != module["id"]]
    modules.append(module)
    registry["schema"] = REGISTRY_SCHEMA
    registry["modules"] = sorted(modules, key=lambda m: m["id"])
    return registry


def retrieve_modules(seed: str, registry: dict[str, Any], needs: list[str] | None = None) -> list[dict[str, Any]]:
    text = seed.lower()
    needs = needs or []
    scored: list[tuple[int, dict[str, Any]]] = []
    for module in registry.get("modules", []):
        score = 0
        haystack = " ".join(str(x) for x in module.get("routing", {}).get("applies_when", []) + module.get("contracts", {}).get("produces", []))
        for token in re.split(r"\W+", haystack.lower()):
            if token and token in text:
                score += 1
        for need in needs:
            if need in module.get("contracts", {}).get("produces", []) or need == module.get("id"):
                score += 4
        if score > 0:
            item = dict(module)
            item["match_score"] = score
            scored.append((score, item))
    return [m for _, m in sorted(scored, key=lambda p: (-p[0], p[1]["id"]))]


def infer_capability_needs(seed: str, registry: dict[str, Any] | None = None) -> list[str]:
    text = seed.lower()
    needs = []
    # Prefer data-defined module routing from the registry so new kernels/modules
    # can be added without editing this planner. Static NEED_RULES are fallback
    # compatibility, not the primary extension seam.
    if registry:
        for module in registry.get("modules", []):
            routing = module.get("routing", {})
            terms = routing.get("applies_when", []) + routing.get("positive_examples", [])
            if any(str(term).strip() and str(term).lower() in text for term in terms):
                needs.append(module.get("id"))
    for need, words, _produces in NEED_RULES:
        if any(w.lower() in text for w in words):
            needs.append(need)
    needs = [n for n in needs if n]
    if not needs:
        needs = ["intent_seed_capture", "output_contract_builder"]
    if "source_evidence_collector" in needs and "evidence_gate" not in needs and "authority_evidence_gate_kernel" not in needs:
        needs.append("evidence_gate")
    needs = list(dict.fromkeys(needs))
    return sorted(needs, key=lambda n: (NEED_ORDER.get(n, 100), n))


def plan_workflow_from_seed(seed: str, registry: dict[str, Any]) -> dict[str, Any]:
    needs = infer_capability_needs(seed, registry)
    nodes: list[dict[str, Any]] = []
    missing: list[str] = []
    selected_ids: list[str] = []
    for idx, need in enumerate(needs):
        matches = retrieve_modules(seed, registry, needs=[need])
        chosen = matches[0] if matches else None
        node_id = chosen["id"] if chosen else need
        if chosen:
            selected_ids.append(node_id)
        else:
            missing.append(need)
        nodes.append({"id": node_id, "need": need, "status": "matched" if chosen else "missing_candidate", "depends_on": [nodes[-1]["id"]] if nodes else []})
    external = any(n in {"authority_gate"} for n in needs) or any(w in seed.lower() for w in ("telegram", "发送", "外发", "关闭任务", "taskpool", "cron", "agentos", "发布", "部署", "删除"))
    return {
        "schema": PLAN_SCHEMA,
        "seed": seed,
        "capability_needs": needs,
        "selected_modules": selected_ids,
        "missing_capability_needs": missing,
        "graph": {"nodes": nodes, "edges": [{"from": n["depends_on"][0], "to": n["id"]} for n in nodes if n["depends_on"]]},
        "side_effects": {"external": bool(external), "cron": False, "taskpool": False, "agentos": False},
        "authority_boundary": "exact_authority_required" if external else "local_only",
    }


def usage_event(workflow_id: str, module_ids: list[str], outcome: str = "success", evidence_passed: bool = True, human_intervention: bool = False, false_trigger: bool = False) -> dict[str, Any]:
    return {
        "schema": USAGE_SCHEMA,
        "ts": utc_now(),
        "workflow_id": workflow_id,
        "module_ids": module_ids,
        "combo_key": hashlib.sha256("|".join(module_ids).encode()).hexdigest()[:12],
        "outcome": outcome,
        "evidence_passed": evidence_passed,
        "human_intervention": human_intervention,
        "false_trigger": false_trigger,
        "side_effects_enabled": False,
    }


def synthesize_module_candidates(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for ev in events:
        groups[tuple(ev.get("module_ids", []))].append(ev)
    candidates = []
    for combo, rows in groups.items():
        if len(combo) < 2 or len(rows) < 3:
            continue
        successes = sum(1 for r in rows if r.get("outcome") == "success")
        evidence_passed = sum(1 for r in rows if r.get("evidence_passed"))
        human_interventions = sum(1 for r in rows if r.get("human_intervention"))
        false_triggers = sum(1 for r in rows if r.get("false_trigger"))
        evidence_rate = evidence_passed / len(rows)
        if successes >= 2 and evidence_rate >= 0.8 and human_interventions == 0 and false_triggers == 0:
            title = " + ".join(combo)
            candidates.append({
                "schema": SYNTHESIS_SCHEMA,
                "id": stable_id(title, "modc"),
                "status": "candidate",
                "composed_from": list(combo),
                "reason": ["frequency_plus_quality", "same_module_combo_seen>=3", "evidence_pass_rate>=0.8", "human_intervention==0"],
                "metrics": {"run_count": len(rows), "success_count": successes, "evidence_pass_rate": evidence_rate, "false_trigger_count": false_triggers},
                "side_effects_enabled": False,
                "promotion_gate": ["negative_cases_pass", "neighbor_collision_count==0", "cleanup_policy_exists"],
            })
    return candidates


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    default_registry = Path.home() / ".hermes" / "workflows" / "module-pool" / "module_registry.json"
    default_ledger = Path.home() / ".hermes" / "workflows" / "module-pool" / "usage_ledger.jsonl"
    parser = argparse.ArgumentParser(description="Local capability module pool and synthesis ratchet")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_default = sub.add_parser("default-module")
    p_default.add_argument("--id", required=True)
    p_default.add_argument("--responsibility", required=True)
    p_validate = sub.add_parser("validate")
    p_validate.add_argument("--module", required=True)
    p_register = sub.add_parser("register")
    p_register.add_argument("--module", required=True)
    p_register.add_argument("--registry", default=str(default_registry))
    p_plan = sub.add_parser("plan")
    p_plan.add_argument("--seed", required=True)
    p_plan.add_argument("--registry", default=str(default_registry))
    p_record = sub.add_parser("record")
    p_record.add_argument("--workflow-id", required=True)
    p_record.add_argument("--modules", required=True, help="comma-separated module ids")
    p_record.add_argument("--outcome", default="success")
    p_record.add_argument("--evidence-passed", action="store_true")
    p_record.add_argument("--human-intervention", action="store_true")
    p_record.add_argument("--false-trigger", action="store_true")
    p_record.add_argument("--ledger", default=str(default_ledger))
    p_synth = sub.add_parser("synthesize")
    p_synth.add_argument("--ledger", default=str(default_ledger))
    args = parser.parse_args(argv)

    if args.cmd == "default-module":
        print(json.dumps(default_capability_module(args.id, args.responsibility), ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "validate":
        module = json.loads(Path(args.module).read_text(encoding="utf-8"))
        issues = validate_capability_module(module)
        print(json.dumps({"status": "PASS" if not issues else "FAIL", "issues": issues}, ensure_ascii=False, indent=2))
        return 0 if not issues else 1
    if args.cmd == "register":
        path = Path(args.registry)
        registry = load_registry(path)
        module = json.loads(Path(args.module).read_text(encoding="utf-8"))
        register_module(registry, module)
        save_registry(path, registry)
        print(json.dumps({"status": "ok", "registry": str(path), "module_count": len(registry["modules"])}, ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "plan":
        registry = load_registry(Path(args.registry))
        print(json.dumps(plan_workflow_from_seed(args.seed, registry), ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "record":
        row = usage_event(args.workflow_id, [m.strip() for m in args.modules.split(",") if m.strip()], args.outcome, args.evidence_passed, args.human_intervention, args.false_trigger)
        append_jsonl(Path(args.ledger), row)
        print(json.dumps({"status": "ok", "ledger": args.ledger, "event": row}, ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "synthesize":
        print(json.dumps({"schema": "hermes_module_synthesis_result_v1", "candidates": synthesize_module_candidates(read_jsonl(Path(args.ledger)))}, ensure_ascii=False, indent=2))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
