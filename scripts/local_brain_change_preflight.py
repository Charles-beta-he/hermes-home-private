#!/usr/bin/env python3
"""local_brain_change_preflight.py — dry-run BrainConstraintGate.

This is the first executable slice of the local-brain auto-constraint layer.
It is deliberately local/read-only with respect to Hermes runtime, taskpool
lifecycle, cron, gateways, external adapters, publish/deploy, and destructive
operations. The only writes it performs are local brain index/WAL files under the
provided memory root while it reuses brainctl search/reindex.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Iterator, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import brainctl  # type: ignore  # local Hermes script

SCHEMA = "local_brain_change_preflight_v1"
ROUTE_SCHEMA = "route_review_record_v1"
BRAIN_SCHEMA = "local_brain_constraint_record_v1"

SURFACE_RULES = {
    "architecture": ["architecture", "架构", "control-plane", "控制面", "runtime", "hermes 自进化"],
    "code": [".py", ".ts", ".tsx", ".js", ".vue", "代码", "script", "scripts/"],
    "ui_visual": ["ui", "visual", "screenshot", "截图", "视觉", "页面", ".tsx", ".vue"],
    "retrieval": ["brain", "本地大脑", "retrieval", "search", "index", "检索", "索引", "vault"],
    "safety": ["permission", "authority", "secret", "credential", "安全", "授权", "凭证", "删除", "destructive"],
    "mlops": ["model", "模型", "quota", "provider", "route", "路由", "consult_models"],
    "taskpool": ["taskpool", "lifecycle", "mission", "任务池", "生命周期", "done transition"],
    "docs": [".md", "docs", "文档", "方案", "playbook"],
    "domain": ["research", "source", "事实", "调研", "证据源"],
}

SIDE_EFFECT_RULES = [
    ("credential_payment", ["credential", "password", "secret", "payment", "凭证", "密码", "支付"]),
    ("destructive", ["delete", "remove", "drop", "destroy", "destructive", "删除", "清理", "销毁"]),
    ("publish_deploy_push", ["push", "deploy", "publish", "release", "发布", "部署"]),
    ("external_dispatch", ["send", "telegram", "lark", "feishu", "gateway", "external", "外发", "发送"]),
    ("lifecycle_write", ["taskpool", "lifecycle", "mission", "cron", "done transition", "任务池", "生命周期"]),
    ("local_write", ["write", "commit", "patch", "file", "本地写入", "提交"]),
]

REQUIRED_EVIDENCE_BY_SURFACE = {
    "architecture": ["design_doc", "gate_readback"],
    "code": ["diff", "tests", "py_compile_or_build"],
    "ui_visual": ["screenshot", "browser_console"],
    "retrieval": ["search_output", "fixture_replay", "reindex_readback"],
    "safety": ["exact_target", "authority", "rollback", "readback"],
    "mlops": ["provider_status", "health_snapshot"],
    "taskpool": ["task_record", "proof_log", "lifecycle_readback"],
    "docs": ["file_readback"],
    "domain": ["source_packet", "timestamped_source"],
}


@contextlib.contextmanager
def brainctl_environment(vault: Path, memory_home: Path) -> Iterator[None]:
    old = {
        "HERMES_BRAIN_VAULT": os.environ.get("HERMES_BRAIN_VAULT"),
        "HERMES_MEMORY_HOME": os.environ.get("HERMES_MEMORY_HOME"),
        "HERMES_BRAIN_INDEX": os.environ.get("HERMES_BRAIN_INDEX"),
        "HERMES_BRAIN_WAL": os.environ.get("HERMES_BRAIN_WAL"),
    }
    os.environ["HERMES_BRAIN_VAULT"] = str(vault)
    os.environ["HERMES_MEMORY_HOME"] = str(memory_home)
    os.environ.pop("HERMES_BRAIN_INDEX", None)
    os.environ.pop("HERMES_BRAIN_WAL", None)
    try:
        yield
    finally:
        for key, value in old.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def stable_id(prefix: str, text: str) -> str:
    return f"{prefix}-{hashlib.sha256(text.encode('utf-8', errors='replace')).hexdigest()[:12]}"


def now_ts() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def default_vaults() -> list[Path]:
    env = os.environ.get("HERMES_BRAIN_PREFLIGHT_VAULTS")
    if env:
        return [Path(part).expanduser() for part in env.split(os.pathsep) if part.strip()]
    home = Path.home()
    return [home / "Documents" / "brain", home / ".hermes" / "notes" / "brain"]


def text_blob(summary: str, files: Sequence[str]) -> str:
    return (summary + "\n" + "\n".join(files)).lower()


DOC_SUFFIXES = {".md", ".markdown", ".txt", ".rst", ".adoc"}


def is_docs_only_change(files: Sequence[str]) -> bool:
    """Return true when every touched file is documentation/reference prose.

    Pre-commit summaries include file paths. A path such as
    ``skills/.../lark-task-reading/...`` names the domain being documented; it
    is not evidence that the change will dispatch to Lark. Keep domain nouns in
    documentation paths from escalating to live side-effect classes.
    """
    return bool(files) and all(Path(f).suffix.lower() in DOC_SUFFIXES for f in files)


def classify_surfaces(summary: str, files: Sequence[str]) -> list[str]:
    blob = text_blob(summary, files)
    surfaces = [name for name, markers in SURFACE_RULES.items() if any(marker.lower() in blob for marker in markers)]
    return surfaces or ["docs"]


def classify_side_effect(summary: str, files: Sequence[str]) -> str:
    summary_blob = summary.lower()
    files_blob = "\n".join(files).lower()
    if is_docs_only_change(files):
        # Documentation edits are local writes even when the documented domain is
        # Lark, gateway, deployment, credentials, or deletion policy. Escalate
        # only when the human summary itself explicitly describes a live action;
        # generated summaries contain file paths, so domain nouns like "lark" are
        # intentionally ignored here.
        if any(marker in summary_blob for marker in ["credential", "password", "secret", "payment", "凭证", "密码", "支付"]):
            return "credential_payment"
        if any(marker in summary_blob for marker in ["delete", "remove", "drop", "destroy", "destructive", "删除", "销毁"]):
            return "destructive"
        if any(marker in summary_blob for marker in ["push", "deploy", "publish", "release", "发布", "部署"]):
            return "publish_deploy_push"
        if any(marker in summary_blob for marker in ["send", "external_dispatch", "外发", "发送"]):
            return "external_dispatch"
        return "local_write"

    # Non-doc code/config paths can be side-effect surfaces, but avoid treating
    # domain nouns in filenames (for example "lark") as external dispatch unless
    # they appear with an actual sender/gateway/outbox surface or explicit action
    # intent in the summary.
    if any(marker in summary_blob for marker in ["credential", "password", "secret", "payment", "凭证", "密码", "支付"]):
        return "credential_payment"
    if any(marker in summary_blob for marker in ["delete", "remove", "drop", "destroy", "destructive", "删除", "清理", "销毁"]):
        return "destructive"
    if any(marker in summary_blob for marker in ["push", "deploy", "publish", "release", "发布", "部署"]):
        return "publish_deploy_push"
    if (
        any(marker in summary_blob for marker in ["send", "external_dispatch", "外发", "发送"])
        or any(marker in files_blob for marker in ["gateway/", "gateway_", "outbox", "sender", "platforms/"])
    ):
        return "external_dispatch"
    if any(marker in text_blob(summary, files) for marker in ["taskpool", "lifecycle", "mission", "cron", "done transition", "任务池", "生命周期"]):
        return "lifecycle_write"
    if any(marker in text_blob(summary, files) for marker in ["write", "commit", "patch", "file", "本地写入", "提交"]):
        return "local_write"
    return "read_only"


def classify_risk(summary: str, files: Sequence[str], surfaces: Sequence[str], side_effect_class: str) -> str:
    blob = text_blob(summary, files)
    if side_effect_class in {"credential_payment", "destructive", "publish_deploy_push", "external_dispatch"}:
        return "T3"
    if side_effect_class == "lifecycle_write" or any(marker in blob for marker in ["runtime", "hard gate", "canonical", "全局", "不可逆"]):
        return "T3"
    if is_docs_only_change(files) and (side_effect_class == "local_write" or "docs" in surfaces):
        return "T1"
    if {"taskpool", "architecture", "retrieval"} & set(surfaces) or len(files) > 1:
        return "T2"
    if side_effect_class == "local_write" or "docs" in surfaces:
        return "T1"
    return "T0"


def required_evidence_for(surfaces: Sequence[str], risk_tier: str, side_effect_class: str) -> list[str]:
    required: list[str] = []
    for surface in surfaces:
        required.extend(REQUIRED_EVIDENCE_BY_SURFACE.get(surface, []))
    if risk_tier in {"T2", "T3"}:
        required.extend(["deterministic_gate", "route_review_record"])
    if side_effect_class != "read_only":
        required.extend(["exact_target", "rollback", "post_action_readback"])
    # stable order, dedupe
    seen = set()
    out = []
    for item in required:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def evidence_coverage(required: Sequence[str], provided: Sequence[str]) -> tuple[float, list[str]]:
    if not required:
        return 1.0, []
    provided_blob = "\n".join(provided).lower()
    missing = [item for item in required if item.lower() not in provided_blob]
    return (len(required) - len(missing)) / len(required), missing


def derive_queries(summary: str, files: Sequence[str]) -> list[str]:
    """Build recall-oriented queries without requiring every summary word.

    brainctl search is intentionally conservative (AND semantics). A change
    summary often contains verbs such as “强化/完善/修改” that do not appear in
    canonical notes. The preflight gate therefore tries the full summary first,
    then stable nouns/surfaces and touched filenames.
    """
    queries = [summary]
    if "RouteReviewGate" in summary or "route" in summary.lower():
        queries.append("RouteReviewGate")
    if "本地大脑" in summary or "全量自动约束" in summary:
        queries.append("本地大脑全量自动约束层")
    if "BrainConstraint" in summary or "brain" in summary.lower():
        queries.append("BrainConstraintRecord")
    for file_path in files:
        stem = Path(file_path).stem.replace("_", " ").replace("-", " ")
        if stem:
            queries.append(stem)
    seen = set()
    out = []
    for query in queries:
        if query and query not in seen:
            seen.add(query)
            out.append(query)
    return out


def search_one_vault(queries: Sequence[str], vault: Path, memory_home: Path, limit: int) -> dict:
    if not vault.exists():
        return {"vault": str(vault), "exists": False, "hits": [], "error": "vault_missing"}
    scoped_memory = memory_home / hashlib.sha256(str(vault).encode()).hexdigest()[:12]
    try:
        hits_by_key: dict[tuple[str, str], dict] = {}
        with brainctl_environment(vault, scoped_memory):
            brainctl.reindex(json_mode=True)
            for query in queries:
                for raw_hit in brainctl.search(query, limit=limit, json_mode=True):
                    hit = dict(raw_hit)
                    key = (str(hit.get("path")), str(hit.get("content_hash")))
                    hit["vault"] = str(vault)
                    hit["matched_queries"] = [query]
                    prior = hits_by_key.get(key)
                    if prior is None or float(hit.get("score", 0.0)) > float(prior.get("score", 0.0)):
                        if prior is not None:
                            hit["matched_queries"] = sorted(set(prior.get("matched_queries", []) + [query]))
                        hits_by_key[key] = hit
                    else:
                        prior["matched_queries"] = sorted(set(prior.get("matched_queries", []) + [query]))
        hits = sorted(hits_by_key.values(), key=lambda h: (-float(h.get("score", 0.0)), str(h.get("path", ""))))[:limit]
        return {"vault": str(vault), "exists": True, "hits": hits, "error": None}
    except Exception as exc:  # fail closed at the caller, but preserve evidence
        return {"vault": str(vault), "exists": True, "hits": [], "error": f"{type(exc).__name__}: {exc}"}


def aggregate_hits(search_results: Sequence[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    accepted: list[dict] = []
    filtered: list[dict] = []
    quarantine: list[dict] = []
    injection_markers = ["绕过证明", "忽略门禁", "强制完成", "ignore gate", "bypass proof"]
    for result in search_results:
        for hit in result.get("hits", []):
            hay = f"{hit.get('path','')}\n{hit.get('heading','')}\n{hit.get('excerpt','')}".lower()
            if any(marker.lower() in hay for marker in injection_markers):
                item = dict(hit)
                item["selection_status"] = "quarantine"
                item.setdefault("filter_reasons", []).append("prompt_injection_or_bypass_marker")
                quarantine.append(item)
            elif hit.get("selection_status") == "filtered":
                filtered.append(hit)
            else:
                accepted.append(hit)
    accepted.sort(key=lambda h: (-float(h.get("score", 0.0)), str(h.get("path", ""))))
    filtered.sort(key=lambda h: (-float(h.get("score", 0.0)), str(h.get("path", ""))))
    quarantine.sort(key=lambda h: str(h.get("path", "")))
    return accepted, filtered, quarantine


def has_local_deterministic_precommit_certification(evidence: Sequence[str]) -> bool:
    blob = "\n".join(evidence).lower()
    common = (
        "deterministic_gate:pre-commit local deterministic checks completed" in blob
        and "tests:" in blob
        and "py_compile_or_build:" in blob
        and "post_action_readback:" in blob
    )
    taskpool_lifecycle = (
        "task_record:" in blob
        and "proof_log:" in blob
        and "lifecycle_readback:" in blob
    )
    local_runtime_or_architecture = (
        "design_doc:" in blob
        and "gate_readback:" in blob
        and "exact_target:" in blob
        and "rollback:" in blob
    )
    return common and (taskpool_lifecycle or local_runtime_or_architecture)


def build_route_review_record(summary: str, files: Sequence[str], evidence: Sequence[str]) -> dict:
    surfaces = classify_surfaces(summary, files)
    side_effect = classify_side_effect(summary, files)
    risk = classify_risk(summary, files, surfaces, side_effect)
    required = required_evidence_for(surfaces, risk, side_effect)
    coverage, missing = evidence_coverage(required, evidence)
    non_model_evidence = bool(evidence)
    if coverage >= 1.0 and non_model_evidence:
        truth_status = "grounded"
    elif evidence:
        truth_status = "needs_link_review"
    else:
        truth_status = "unsupported"

    if risk == "T0":
        mode, quorum, min_quorum = "no_model", 0, 0
    elif risk == "T1":
        mode, quorum, min_quorum = "single_specialist", 2, 1
    elif risk == "T2":
        mode, quorum, min_quorum = "fanout", 3, 2
    else:
        mode, quorum, min_quorum = "ratification", 5, 3

    local_deterministic_certified = (
        truth_status == "grounded"
        and coverage >= 1.0
        and risk in {"T2", "T3"}
        and has_local_deterministic_precommit_certification(evidence)
    )
    if local_deterministic_certified:
        status = "local_deterministic_certified"
        certified = True
        multi_model_certified = False
    elif truth_status == "grounded" and risk in {"T0", "T1"}:
        status = "pass"
        certified = risk == "T0"
        multi_model_certified = False
    elif truth_status == "grounded" and risk == "T2":
        status = "warn"
        certified = False
        multi_model_certified = False
    elif risk in {"T2", "T3"}:
        status = "degraded_not_certified"
        certified = False
        multi_model_certified = False
    else:
        status = "warn"
        certified = False
        multi_model_certified = False

    primary = "claude-architecture" if "architecture" in surfaces or "retrieval" in surfaces else "specialist"
    adversarial = [] if risk in {"T0", "T1"} else ["deepseek-or-gpt-adversarial"]
    return {
        "schema": ROUTE_SCHEMA,
        "review_id": stable_id("route-review", summary + "\n" + "\n".join(files)),
        "created_at": now_ts(),
        "subject": {
            "kind": "brain_constraint",
            "summary": summary,
            "target_files": list(files),
            "claim_ids": [],
        },
        "classification": {
            "surfaces": surfaces,
            "risk_tier": risk,
            "side_effect_class": side_effect,
            "reversibility": "reversible" if side_effect in {"read_only", "local_write"} else "unknown",
            "blast_radius": "local" if risk in {"T0", "T1"} else ("workflow" if risk == "T2" else "runtime"),
        },
        "evidence_state": {
            "required_evidence": required,
            "provided_evidence": list(evidence),
            "missing_evidence": missing,
            "evidence_coverage": coverage,
            "truth_status": truth_status,
            "non_model_evidence_present": non_model_evidence,
        },
        "routing": {
            "primary_specialist": primary,
            "adversarial_reviewers": adversarial,
            "optional_reviewers": [] if risk == "T0" else ["gpt-or-mimo-secondary"],
            "excluded_reviewers": [],
            "exclusion_reasons": [],
            "quorum_required": quorum,
            "min_quorum": min_quorum,
            "role_separation_required": risk in {"T2", "T3"},
            "producer_models": [],
        },
        "execution": {
            "mode": mode,
            "timeout_seconds": 180,
            "health_snapshot_ref": "not_probed_in_dry_run",
        },
        "votes": [],
        "verdict": {
            "status": status,
            "certified": certified,
            "multi_model_certified": multi_model_certified,
            "reasons": missing[:],
            "allowed_actions": ["local_dry_run", "evidence_request"],
            "forbidden_actions": ["external_dispatch", "lifecycle_write", "publish_deploy_push", "destructive", "credential_payment"],
            "next_required_gates": ["provide_missing_evidence"] if missing else [],
        },
    }


def build_brain_constraint_record(
    summary: str,
    queries: Sequence[str],
    files: Sequence[str],
    vaults: Sequence[Path],
    search_results: Sequence[dict],
    accepted: Sequence[dict],
    filtered: Sequence[dict],
    quarantine: Sequence[dict],
    route: dict,
) -> dict:
    risk = route["classification"]["risk_tier"]
    missing = route["evidence_state"]["missing_evidence"]
    reasons: list[str] = []
    status = "pass"
    if quarantine:
        reasons.append("quarantined_hits_present")
        status = "block"
    if not accepted:
        reasons.append("missing_current_canonical_knowledge")
        status = "block" if risk in {"T2", "T3"} else "warn"
    if missing and risk in {"T2", "T3"}:
        reasons.append("missing_required_evidence")
        status = "block"
    if route["verdict"]["status"] in {"degraded_not_certified", "not_certified"} and risk in {"T2", "T3"}:
        reasons.append(route["verdict"]["status"])
        status = "block"
    if not reasons and route["verdict"]["status"] == "warn":
        status = "warn"
    return {
        "schema": BRAIN_SCHEMA,
        "change": {
            "id": stable_id("change", summary + "\n" + "\n".join(files)),
            "summary": summary,
            "touched_files": list(files),
            "target_surface": route["classification"]["surfaces"],
            "risk_class": risk,
            "side_effect_class": route["classification"]["side_effect_class"],
        },
        "retrieval": {
            "vaults": [str(v) for v in vaults],
            "queries": list(queries),
            "result_count": sum(len(r.get("hits", [])) for r in search_results),
            "accepted_hits": list(accepted),
            "filtered_hits": list(filtered),
            "quarantine_hits": list(quarantine),
            "missing_expected_topics": [] if accepted else ["current_canonical_knowledge"],
            "vault_results": [
                {"vault": r.get("vault"), "exists": r.get("exists"), "error": r.get("error"), "hit_count": len(r.get("hits", []))}
                for r in search_results
            ],
        },
        "selected_knowledge": [
            {
                "path": h.get("path"),
                "heading": h.get("heading"),
                "vault": h.get("vault"),
                "source_class": h.get("source_class"),
                "selection_status": h.get("selection_status"),
                "filter_reasons": h.get("filter_reasons", []),
                "canonicality": "accepted" if h.get("selection_status") == "accepted" else "unknown",
                "evidence_refs": [h.get("content_hash")],
                "required_gate": "RouteReviewGate",
            }
            for h in accepted
        ],
        "impact": {
            "theory_point_ids": ["evidence-first", "ashby-variety"] if risk in {"T2", "T3"} else ["evidence-first"],
            "same_theory_targets": ["BrainConstraintGate", "RouteReviewGate"],
            "layer_impact_map": ["L0-trace", "L1-router", "L2-protocol", "L4-taskpool-brain", "L5-consult-models"],
            "impact_variance": "high" if risk == "T3" else ("medium" if risk == "T2" else "low"),
        },
        "routing": {
            "model_route": route["routing"],
            "route_review_ref": "embedded:route_review_record",
            "required_reviewers": [route["routing"]["primary_specialist"]] + route["routing"]["adversarial_reviewers"],
            "optional_reviewers": route["routing"]["optional_reviewers"],
            "quorum_policy": f"{route['routing']['min_quorum']}/{route['routing']['quorum_required']}",
            "degraded_policy": "block" if risk in {"T2", "T3"} else "advisory_only",
            "route_required_evidence": route["evidence_state"]["required_evidence"],
        },
        "verdict": {
            "status": status,
            "reasons": reasons,
            "allowed_actions": ["local_dry_run", "read_only_review"] if status != "block" else ["evidence_repair", "local_dry_run"],
            "forbidden_actions": ["external_dispatch", "lifecycle_write", "publish_deploy_push", "destructive", "credential_payment"],
            "required_next_gates": ["evidence_repair"] if status == "block" else [],
        },
        "evidence": {
            "commands": [],
            "files": list(files),
            "test_results": [],
            "receipts": [],
        },
    }


def high_risk_gate_status() -> dict:
    """Read high-risk gate enablement if available.

    This is read-only: it reports whether live side-effect classes are opened as
    fail-closed exact-target boundaries, but does not execute them.
    """
    try:
        import high_risk_gate_control  # type: ignore

        home = Path(os.environ.get("HERMES_HIGH_RISK_GATE_HOME", str(Path.home() / ".hermes"))).expanduser()
        return high_risk_gate_control.status(home)
    except Exception as exc:  # pragma: no cover - defensive runtime reporting
        return {"ok": False, "error": f"high_risk_gate_status_unavailable:{type(exc).__name__}:{exc}"}


def run_preflight(
    *,
    summary: str,
    files: Sequence[str] | None = None,
    vaults: Sequence[Path] | None = None,
    memory_root: Path | None = None,
    evidence: Sequence[str] | None = None,
    limit: int = 8,
) -> dict:
    files = list(files or [])
    vaults = list(vaults or default_vaults())
    evidence = list(evidence or [])
    cleanup_tmp = None
    if memory_root is None:
        cleanup_tmp = tempfile.TemporaryDirectory(prefix="hermes-brain-preflight-")
        memory_root = Path(cleanup_tmp.name)
    else:
        memory_root = Path(memory_root)
        memory_root.mkdir(parents=True, exist_ok=True)
    try:
        queries = derive_queries(summary, files)
        search_results = [search_one_vault(queries, Path(v), memory_root, limit) for v in vaults]
        accepted, filtered, quarantine = aggregate_hits(search_results)
        route = build_route_review_record(summary, files, evidence)
        brain = build_brain_constraint_record(summary, queries, files, vaults, search_results, accepted, filtered, quarantine, route)
        return {
            "schema": SCHEMA,
            "dry_run": True,
            "created_at": now_ts(),
            "summary": summary,
            "side_effects": {
                "external_dispatch": False,
                "lifecycle_write": False,
                "publish_deploy_push": False,
                "destructive": False,
                "credential_payment": False,
            },
            "side_effect_gate_status": high_risk_gate_status(),
            "brain_constraint_record": brain,
            "route_review_record": route,
        }
    finally:
        if cleanup_tmp is not None:
            cleanup_tmp.cleanup()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dry-run local brain BrainConstraintGate preflight")
    parser.add_argument("--summary", required=True, help="change summary / intent")
    parser.add_argument("--file", action="append", default=[], help="touched file path; repeatable")
    parser.add_argument("--vault", action="append", default=[], help="brain vault to search; repeatable")
    parser.add_argument("--memory-root", help="memory/index root for dry-run search state")
    parser.add_argument("--evidence", action="append", default=[], help="provided evidence ref; repeatable")
    parser.add_argument("--limit", type=int, default=8, help="per-vault search limit")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    vaults = [Path(v).expanduser() for v in args.vault] if args.vault else default_vaults()
    memory_root = Path(args.memory_root).expanduser() if args.memory_root else None
    result = run_preflight(
        summary=args.summary,
        files=args.file,
        vaults=vaults,
        memory_root=memory_root,
        evidence=args.evidence,
        limit=args.limit,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        verdict = result["brain_constraint_record"]["verdict"]
        print(f"BrainConstraintGate dry-run: {verdict['status']} reasons={','.join(verdict['reasons']) or 'none'}")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
