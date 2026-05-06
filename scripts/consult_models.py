#!/usr/bin/env python3
"""
consult_models.py — 多脑 fan-out 编排器 v3 (替代 consult-models.sh)

Phase 0 shadow → Phase 3 steady: 读取 quorum.yaml, 选择 planner, fan-out 调用,
运行 consensus, emit protocol 消息, 清理工作目录。

用法:
  python3 consult_models.py run <state.json> [--tier T2] [--shadow]
  python3 consult_models.py run <state.json> --quorum 2 --tier T1
  python3 consult_models.py status  # 读取 quorum.yaml 当前配置

与 v2(shell) 的区别:
  - 读取 quorum.yaml (不再硬编码)
  - L2 agent_protocol emit (全链路可追踪)
  - TICK_DIR 自动清理 (除非 --keep)
  - 每 planner 有 timeout (默认 120s)
  - Python 原生错误处理 (无 2>/dev/null)
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import Any, List, Dict, Optional, Tuple

try:
    import yaml
except ImportError:  # PyYAML is optional for import-time safety in tests/tools.
    yaml = None

# ── 路径 ──
HERMES_HOME = os.path.expanduser(os.environ.get("HERMES_HOME", "~/.hermes"))
SCRIPTS_DIR = os.path.join(HERMES_HOME, "scripts")
CONFIG_DIR = os.path.join(HERMES_HOME, "config")
LOG_DIR = os.path.join(HERMES_HOME, "logs")

# ── L2 协议导入 ──
sys.path.insert(0, SCRIPTS_DIR)
from agent_protocol import (
    wrap as protocol_wrap,
    emit as protocol_emit,
    ProtocolError,
)

# ── SPL encoding (optional, for token savings) ──
try:
    sys.path.insert(0, os.path.join(HERMES_HOME, "hermes-agent"))
    from agent.spl import SPLEncoder, SPLTier, spl_prompt_for_model
    _spl_encoder = SPLEncoder()
    _spl_available = True
except ImportError:
    _spl_available = False

DEFAULT_TIMEOUT = 120  # per-planner timeout (seconds)
TICK_CLEANUP_AGE = 86400  # 24h — 清理旧 TICK_DIR
SUPPORTED_HERMES_PROVIDERS = {
    "openai-codex", "anthropic", "xiaomi", "openrouter", "gemini", "xai",
    "ollama-cloud", "huggingface", "zai", "kimi-coding", "kimi-coding-cn",
    "stepfun", "minimax", "minimax-cn", "kilocode", "arcee", "nvidia",
}

try:
    import model_quota
except Exception:  # quota must be best-effort, never break legacy fan-out import
    model_quota = None


def load_quorum() -> dict:
    """读取 quorum.yaml"""
    path = os.path.join(CONFIG_DIR, "quorum.yaml")
    if yaml is None:
        print("[consult_models] PyYAML unavailable; quorum.yaml skipped", file=sys.stderr)
        return {}
    try:
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except (yaml.YAMLError, FileNotFoundError, OSError) as e:
        print(f"[consult_models] quorum.yaml load failed: {e}", file=sys.stderr)
        return {}


def load_config() -> dict:
    """读取 config.yaml"""
    path = os.path.join(HERMES_HOME, "config.yaml")
    if yaml is None:
        return {}
    try:
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except (yaml.YAMLError, FileNotFoundError, OSError):
        return {}


def get_tier_planners(quorum: dict, tier: str, skip_claude: bool = False) -> Tuple[List[str], int, int]:
    """
    从 quorum.yaml 读取 tier 配置。

    返回 (planner_list, quorum_count, min_quorum)
    """
    tiers = quorum.get("tiers", {})
    tier_cfg = tiers.get(tier, {})
    planners = tier_cfg.get("planners", [])

    # Claude budget guard
    if skip_claude or _claude_excluded(quorum):
        planners = [m for m in planners if "claude" not in m.lower()]

    q = tier_cfg.get("quorum", 3)
    mq = tier_cfg.get("min_quorum", 2)

    return planners, q, mq


def _claude_excluded(quorum: dict) -> bool:
    """检查 Claude budget 是否排除"""
    budget_guard = quorum.get("claude_budget_guard", {})
    if budget_guard.get("exclude_below_5_usd"):
        # 简单检查: 如果 budget tracker 说不能使用
        try:
            r = subprocess.run(
                [sys.executable, os.path.join(SCRIPTS_DIR, "claude-budget-tracker.py"),
                 "can-use"],
                capture_output=True, text=True, timeout=10,
            )
            return r.returncode != 0
        except Exception:
            return True  # 无法确认 → 保守排除
    return False


def cleanup_old_ticks():
    """清理超过 TICK_CLEANUP_AGE 的旧 TICK_DIR"""
    import shutil
    now = time.time()
    for entry in os.listdir(HERMES_HOME):
        path = os.path.join(HERMES_HOME, entry)
        if entry.startswith("tick-") and os.path.isdir(path):
            try:
                mtime = os.path.getmtime(path)
                if now - mtime > TICK_CLEANUP_AGE:
                    shutil.rmtree(path)
                    print(f"[consult_models] Cleaned old tick: {entry}", file=sys.stderr)
            except OSError:
                pass


def compute_state_hash(state_file: str) -> str:
    """计算 state.json 的 SHA256"""
    with open(state_file, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


MAX_PLANNER_STATE_CHARS = int(os.environ.get("HERMES_MULTI_BRAIN_MAX_STATE_CHARS", "24000"))
CRITICAL_STATE_FIELDS = [
    "schema", "question", "constraints", "acceptance_criteria", "non_goals",
    "risk_level", "budget", "claims", "evidence", "evidence_bundle", "truth_gate",
    "state_owner", "implementation_target",
]


def _planner_state_payload(state: dict) -> Tuple[str, bool]:
    """Return planner-visible state without silently dropping truth-critical fields.

    Historical prompts sliced state_json at 8k chars. That can remove claims/evidence
    after the truth gate attaches them. If the state is too large, compact to critical
    fields and mark the payload as truncated so reviewers can request missing context.
    """
    raw = json.dumps(state, indent=2, ensure_ascii=False)
    if len(raw) <= MAX_PLANNER_STATE_CHARS:
        return raw, False
    compact = {k: state.get(k) for k in CRITICAL_STATE_FIELDS if k in state}
    compact["state_truncated"] = True
    compact["omitted_fields"] = [k for k in state.keys() if k not in compact]
    compact["truncation_policy"] = (
        "Original state exceeded planner prompt budget; orchestrator preserved "
        "claims/evidence/evidence_bundle/truth_gate and omitted non-critical fields."
    )
    return json.dumps(compact, indent=2, ensure_ascii=False), True


def build_planner_prompt(state: dict, state_hash: str, model: str, tier: str) -> str:
    """构建 planner 提示词 (同 consult-models.sh v2 格式)"""
    state_json, state_truncated = _planner_state_payload(state)
    truncation_notice = ""
    if state_truncated:
        truncation_notice = (
            "\nSTATE_TRUNCATION_NOTICE: non-critical fields were omitted, but "
            "claims/evidence/evidence_bundle/truth_gate were preserved. Request evidence "
            "instead of certifying any omitted fact.\n"
        )
    return f"""You are a Hermes Agent architecture planner.

Read the state below and produce a structured improvement plan.

STATE (sha256: {state_hash}):{truncation_notice}
{state_json}

Output ONLY valid JSON matching this schema:
{{
  "meta": {{"planner_model": "{model}", "planner_role": "architect", "state_hash": "{state_hash}", "tier_target": "{tier}", "confidence": 0.0-1.0}},
  "diagnosis": {{"root_cause_class": "regression|router_skew|verifier_gap|kill_switch_oscillation|consensus_drift|pricing_overrun|schema_mismatch|no_action", "evidence_field_ids": ["field1"], "summary": "..."}},
  "patches": [{{"id": "unique", "target_file": "path", "op": "tune_threshold|swap_model|add_verifier|modify_router_weight|raise_tier|lower_tier|noop", "rationale": "...", "risk": "low|med|high", "blast_radius": "single_tier|router|all_tiers|kill_switch", "depends_on": []}}],
  "verification": {{"expected_metric_delta": {{"main_pass_rate": 0.0}}, "guard_metrics": ["main_pass_rate"], "tier_eval_plan": "T0_only|T0_T1|T1_T2|full_T0_T3"}},
  "evidence_requests": [{{"claim_id": "C-001", "tool_needed": "terminal|file|web", "command": "read-only command/query", "why": "missing evidence needed before truth certification"}}],
  "rollback_signal": {{"auto_rollback_if": "main_pass_rate < pre - 0.05", "kill_switch_inc": false}}
}}

Rules:
- Multi-model agreement is not truth verification.
- Cite evidence_bundle.grounding when relying on factual claims.
- If evidence is missing, add evidence_requests instead of asserting you verified it.

Keep patches ≤ 5. Be concrete. Confidence must be honest."""


def model_provider(config: dict, model: str) -> str:
    """Resolve provider for a model from pricing config."""
    return (
        config.get("pricing", {})
        .get("models", {})
        .get(model, {})
        .get("provider", "")
    )


def _provider_map_for_models(models: List[str], config: dict) -> Dict[str, str]:
    providers: Dict[str, str] = {}
    for model in models:
        provider = model_provider(config, model)
        if not provider and model_quota:
            provider = model_quota.provider_for_model(model, config)
        providers[model] = provider or "unknown"
    return providers


def filter_planners_by_quota(
    planners: List[str],
    config: dict,
    quota_snapshot: Optional[dict] = None,
) -> Tuple[List[str], List[dict], dict]:
    """Filter exhausted planners while preserving exact/estimated quota provenance.

    Unknown/unobservable quota is allowed but attached to state/output. Only explicit
    `status=exhausted` is a hard gate.
    """
    if not model_quota:
        return planners, [], {}
    providers = _provider_map_for_models(planners, config)
    snapshots = quota_snapshot or model_quota.snapshot_models(planners, config=config)
    # Ensure every selected planner has an attached snapshot, even when the caller
    # supplied a partial test/fixture snapshot.
    attached = dict(snapshots)
    for model in planners:
        provider = providers.get(model, "unknown")
        key = model_quota.quota_key(provider, model)
        default = model_quota.default_snapshot(model, provider)
        supplied = attached.get(key) or attached.get(model) or {}
        merged = dict(default)
        merged.update(supplied)
        attached[key] = merged
    allowed, skipped = model_quota.gate_models(planners, attached, providers=providers)
    return allowed, skipped, attached


def select_planners_for_fanout(
    planners: List[str],
    q_count: int,
    config: dict,
    quota_snapshot: Optional[dict] = None,
) -> Tuple[List[str], List[dict], dict]:
    """Apply quota gate before quorum trimming.

    If the first N planners are exhausted, later healthy planners should still be
    eligible to satisfy quorum. This preserves the configured preference order while
    preventing head-of-list exhaustion from masquerading as a multi-model outage.
    """
    allowed, skipped, attached = filter_planners_by_quota(
        planners, config=config, quota_snapshot=quota_snapshot
    )
    return allowed[:q_count], skipped, attached


def build_state(
    question: str,
    context: Optional[dict] = None,
    constraints: Optional[List[str]] = None,
    acceptance_criteria: Optional[List[str]] = None,
    implementation_target: Optional[dict] = None,
    non_goals: Optional[List[str]] = None,
    risk_level: str = "medium",
    budget: Optional[dict] = None,
    claims: Optional[List[Any]] = None,
    evidence: Optional[List[dict]] = None,
) -> dict:
    """Build the orchestrator-owned state.json facts/bounds for true multi-model discussion.

    This is deliberately not a candidate solution. Candidate plans are produced later by
    independent models from this shared state. `claims` and `evidence` are the optional
    truth-provenance contract: models may critique it or request more evidence, but they
    must not treat unsupported claims as tool-verified facts.
    """
    return {
        "schema": "multi_model_state_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "question": question,
        "context": context or {},
        "constraints": constraints or [],
        "acceptance_criteria": acceptance_criteria or [],
        "non_goals": non_goals or [],
        "risk_level": risk_level,
        "budget": budget or {},
        "claims": claims or [],
        "evidence": evidence or [],
        "implementation_target": implementation_target or {
            "files": [],
            "verify_commands": [],
            "forbidden_changes": [],
        },
        "is_candidate_solution": False,
        "state_owner": "main_orchestrator",
    }


EVIDENCE_BUNDLE_SCHEMA_VERSION = 1
TRUTH_GATE_SCHEMA_VERSION = 1


def _normalize_claims(raw_claims: List[Any]) -> List[dict]:
    claims: List[dict] = []
    for i, raw in enumerate(raw_claims or [], start=1):
        if isinstance(raw, str):
            claim = {"id": f"C-{i:03d}", "text": raw, "severity": 3}
        elif isinstance(raw, dict):
            claim = dict(raw)
            claim.setdefault("id", f"C-{i:03d}")
            claim.setdefault("text", claim.get("claim") or claim.get("summary") or "")
            claim.setdefault("severity", 3)
        else:
            claim = {"id": f"C-{i:03d}", "text": str(raw), "severity": 3}
        claim["id"] = str(claim.get("id") or f"C-{i:03d}")
        claim["text"] = str(claim.get("text") or "").strip()
        try:
            claim["severity"] = int(claim.get("severity", 3) or 3)
        except (TypeError, ValueError):
            claim["severity"] = 3
        claims.append(claim)
    return claims


def _normalize_evidence(raw_evidence: List[dict]) -> List[dict]:
    evidence: List[dict] = []
    for i, raw in enumerate(raw_evidence or [], start=1):
        if not isinstance(raw, dict):
            raw = {"summary": str(raw)}
        item = dict(raw)
        item.setdefault("id", f"E-{i:03d}")
        item.setdefault("type", "note")
        item.setdefault("summary", item.get("content") or item.get("stdout") or "")
        item.setdefault("supports", item.get("claim_ids", []))
        item.setdefault("contradicts", [])
        if isinstance(item.get("supports"), str):
            item["supports"] = [item["supports"]]
        if isinstance(item.get("contradicts"), str):
            item["contradicts"] = [item["contradicts"]]
        item["id"] = str(item.get("id") or f"E-{i:03d}")
        item["supports"] = [str(x) for x in (item.get("supports") or [])]
        item["contradicts"] = [str(x) for x in (item.get("contradicts") or [])]
        # A failed command may still be evidence, but it must not support a claim.
        if item.get("type") == "command" and item.get("exit_code") not in (None, 0):
            item["supports"] = []
            item.setdefault("validity", "command_failed")
        evidence.append(item)
    return evidence


def build_evidence_bundle(state: dict) -> dict:
    """Build a grounded evidence bundle from orchestrator-collected claims/evidence.

    This separates multi-model agreement from factual verification. Models can only
    certify factual claims that have explicit supporting evidence IDs. Missing evidence
    remains visible as `unsupported` and can generate evidence_requests.
    """
    context = state.get("context", {}) if isinstance(state, dict) else {}
    raw_claims = state.get("claims") or (context.get("claims") if isinstance(context, dict) else []) or []
    raw_evidence = state.get("evidence") or (context.get("evidence") if isinstance(context, dict) else []) or []
    claims = _normalize_claims(raw_claims)
    evidence = _normalize_evidence(raw_evidence)

    grounding: Dict[str, dict] = {}
    for claim in claims:
        cid = claim["id"]
        supporting = [e["id"] for e in evidence if cid in (e.get("supports") or [])]
        contradicting = [e["id"] for e in evidence if cid in (e.get("contradicts") or [])]
        if contradicting:
            truth_status = "contradicted_by_evidence"
        elif supporting:
            truth_status = "verified_by_evidence"
        else:
            truth_status = "unsupported"
        grounding[cid] = {
            "claim_id": cid,
            "claim_text": claim.get("text", ""),
            "severity": claim.get("severity", 3),
            "truth_status": truth_status,
            "supporting_evidence_ids": supporting,
            "contradicting_evidence_ids": contradicting,
        }

    verified_count = sum(1 for g in grounding.values() if g["truth_status"] == "verified_by_evidence")
    coverage = (verified_count / len(claims)) if claims else 1.0
    return {
        "schema_version": EVIDENCE_BUNDLE_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "claims": claims,
        "evidence": evidence,
        "grounding": grounding,
        "evidence_coverage": coverage,
        "verified_claim_count": verified_count,
        "claim_count": len(claims),
    }


def evaluate_truth_gate(evidence_bundle: Optional[dict]) -> dict:
    """Fail-closed truth gate for multi-brain certification artifacts."""
    bundle = evidence_bundle or build_evidence_bundle({})
    grounding = bundle.get("grounding", {}) if isinstance(bundle, dict) else {}
    unsupported = [cid for cid, g in grounding.items() if g.get("truth_status") == "unsupported"]
    contradicted = [cid for cid, g in grounding.items() if g.get("truth_status") == "contradicted_by_evidence"]
    unsupported_high = [cid for cid, g in grounding.items() if g.get("truth_status") == "unsupported" and int(g.get("severity", 3) or 3) >= 3]
    contradicted_high = [cid for cid, g in grounding.items() if g.get("truth_status") == "contradicted_by_evidence" and int(g.get("severity", 3) or 3) >= 3]
    claim_count = int(bundle.get("claim_count", len(grounding)) or 0) if isinstance(bundle, dict) else 0
    verified_count = int(bundle.get("verified_claim_count", 0) or 0) if isinstance(bundle, dict) else 0

    if claim_count == 0:
        truth_status = "no_claims"
    elif contradicted:
        truth_status = "contradicted"
    elif unsupported and verified_count > 0:
        truth_status = "partially_grounded"
    elif unsupported:
        truth_status = "unsupported"
    else:
        truth_status = "grounded"

    reasons = []
    if unsupported:
        reasons.append(f"unsupported factual claims: {unsupported}")
    if contradicted:
        reasons.append(f"contradicted factual claims: {contradicted}")
    can_certify_truth = not unsupported and not contradicted
    return {
        "schema_version": TRUTH_GATE_SCHEMA_VERSION,
        "truth_status": truth_status,
        "can_certify_truth": can_certify_truth,
        "claim_count": claim_count,
        "verified_claim_count": verified_count,
        "evidence_coverage": bundle.get("evidence_coverage", 1.0) if isinstance(bundle, dict) else 1.0,
        "unsupported_claim_ids": unsupported,
        "unsupported_high_severity_claim_ids": unsupported_high,
        "contradicted_claim_ids": contradicted,
        "contradicted_high_severity_claim_ids": contradicted_high,
        "reasons": reasons,
    }


def collect_evidence_requests(outputs: List[dict]) -> List[dict]:
    """Collect structured evidence requests from planner/discussion outputs.

    Peer models do not get to claim they used tools in the text-only multi-brain path.
    They can instead ask the main orchestrator for read-only evidence to acquire.
    """
    requests: List[dict] = []
    seen = set()
    for output in outputs or []:
        if not isinstance(output, dict):
            continue
        model = _plan_model(output, "unknown")
        raw_requests = []
        raw_requests.extend(output.get("evidence_requests") or [])
        diagnosis = output.get("diagnosis") or {}
        if isinstance(diagnosis, dict):
            raw_requests.extend(diagnosis.get("evidence_requests") or [])
        for i, raw in enumerate(raw_requests, start=1):
            if not isinstance(raw, dict):
                continue
            command = str(raw.get("command") or raw.get("query") or "").strip()
            claim_id = str(raw.get("claim_id") or "").strip()
            claim = str(raw.get("claim") or "").strip()
            tool_needed = str(raw.get("tool_needed") or raw.get("tool") or "unknown").strip()
            why = str(raw.get("why") or raw.get("reason") or "").strip()
            key = (model, claim_id, claim, tool_needed, command, why)
            if key in seen:
                continue
            seen.add(key)
            requests.append({
                "id": f"ER-{len(requests) + 1:03d}",
                "requested_by": model,
                "claim_id": claim_id,
                "claim": claim,
                "tool_needed": tool_needed,
                "command": command,
                "why": why,
                "status": "requested",
                "safety": "read_only_or_orchestrator_approved",
            })
    return requests


def _plan_model(plan: dict, fallback: str = "unknown") -> str:
    meta = plan.get("meta", {}) if isinstance(plan, dict) else {}
    return meta.get("planner_model") or meta.get("model") or fallback


def _patch_signature(patch: dict) -> str:
    """Stable signature for comparing plan patches across models."""
    if patch.get("id"):
        return str(patch.get("id"))
    body = "|".join(str(patch.get(k, "")) for k in ("target_file", "op", "rationale"))
    return hashlib.sha1(body.encode("utf-8")).hexdigest()[:12]


def build_issue_ledger(plans: List[dict]) -> List[dict]:
    """Build explicit unresolved issues from disagreement between model plans.

    The first version focuses on concrete implementation disagreements: different
    patch signatures/ops aimed at the same target file, and missing patches that only
    one model proposed. This gives Phase 3 a bounded issue ledger to debate.
    """
    by_target: Dict[str, List[Tuple[str, dict, str]]] = {}
    all_models = [_plan_model(p, f"model_{i}") for i, p in enumerate(plans)]
    for i, plan in enumerate(plans):
        model = _plan_model(plan, f"model_{i}")
        for patch in plan.get("patches", []) or []:
            target = patch.get("target_file") or patch.get("file") or "<unknown>"
            by_target.setdefault(target, []).append((model, patch, _patch_signature(patch)))

    issues = []
    next_id = 1
    for target, entries in sorted(by_target.items()):
        sigs = {sig for _, _, sig in entries}
        models_present = {model for model, _, _ in entries}
        ops = {str(patch.get("op", "")) for _, patch, _ in entries}
        if len(sigs) > 1 or (len(models_present) < len(all_models) and len(entries) == 1):
            severity = 4 if len(ops) > 1 else 3
            issues.append({
                "id": f"I-{next_id:03d}",
                "status": "unresolved",
                "severity": severity,
                "target_file": target,
                "models": sorted(models_present),
                "missing_models": sorted(set(all_models) - models_present),
                "claim": f"Models disagree on patches for {target}",
                "evidence": [
                    {"model": model, "patch_id": sig, "op": patch.get("op"), "rationale": patch.get("rationale", "")}
                    for model, patch, sig in entries
                ],
                "resolution": "",
            })
            next_id += 1

    return issues


FANOUT_CERTIFICATION_SCHEMA_VERSION = 1
FANOUT_CERTIFICATION_REQUIRED_FIELDS = (
    "schema_version",
    "status",
    "certified",
    "multi_model_certified",
    "certification_scope",
    "below_min_quorum",
    "success_count",
    "fail_count",
    "planner_count",
    "min_quorum",
    "reason",
)
FANOUT_CERTIFICATION_STATUSES = {
    "all_failed",
    "degraded_not_certified",
    "single_model_quorum_met",
    "fanout_quorum_met",
}


def fanout_certification_status(success_count: int, planner_count: int, min_quorum: int, fail_count: int = 0) -> dict:
    """Return auditable certification status for planner fan-out quorum.

    Multi-model outputs below min_quorum may still be useful as degraded planning
    signals, but they must not be represented as certified multi-model results.
    T0/single-planner fan-out can satisfy its own quick-plan threshold while still
    being explicitly marked as non-multi-model certification.
    """
    success_count = max(0, int(success_count))
    planner_count = max(0, int(planner_count))
    min_quorum = max(1, int(min_quorum or 1))
    fail_count = max(0, int(fail_count))

    below_min = success_count < min_quorum
    all_failed = planner_count > 0 and success_count == 0
    single_planner = planner_count == 1

    if all_failed:
        status = "all_failed"
        certified = False
        reason = "all planners failed"
    elif below_min:
        status = "degraded_not_certified"
        certified = False
        reason = f"planner fan-out below min_quorum: {success_count}/{min_quorum}"
    elif single_planner:
        status = "single_model_quorum_met"
        certified = True
        reason = "single planner quorum met; not multi-model certified"
    else:
        status = "fanout_quorum_met"
        certified = True
        reason = f"planner fan-out met min_quorum: {success_count}/{min_quorum}"

    multi_model_certified = bool(certified and success_count >= 2 and planner_count >= 2)
    certification_scope = "multi_model" if multi_model_certified else "single_model"

    return {
        "schema_version": FANOUT_CERTIFICATION_SCHEMA_VERSION,
        "status": status,
        "certified": certified,
        "multi_model_certified": multi_model_certified,
        "certification_scope": certification_scope,
        "below_min_quorum": below_min,
        "success_count": success_count,
        "fail_count": fail_count,
        "planner_count": planner_count,
        "min_quorum": min_quorum,
        "reason": reason,
    }


def validate_fanout_certification_status(status: dict) -> Tuple[bool, List[str]]:
    """Validate fanout_certification before writing merged/discussion artifacts.

    This intentionally uses stdlib-only semantic checks instead of requiring the
    external jsonschema package inside operational scripts.
    """
    errors: List[str] = []
    if not isinstance(status, dict):
        return False, ["fanout_certification must be an object"]
    for field in FANOUT_CERTIFICATION_REQUIRED_FIELDS:
        if field not in status:
            errors.append(f"missing field: {field}")
    if errors:
        return False, errors

    if status.get("schema_version") != FANOUT_CERTIFICATION_SCHEMA_VERSION:
        errors.append(f"schema_version must be {FANOUT_CERTIFICATION_SCHEMA_VERSION}")
    if status.get("status") not in FANOUT_CERTIFICATION_STATUSES:
        errors.append(f"invalid status: {status.get('status')}")
    for field in ("certified", "multi_model_certified", "below_min_quorum"):
        if not isinstance(status.get(field), bool):
            errors.append(f"{field} must be boolean")
    for field in ("success_count", "fail_count", "planner_count", "min_quorum"):
        if not isinstance(status.get(field), int) or status.get(field) < 0:
            errors.append(f"{field} must be non-negative integer")
    if status.get("min_quorum", 0) < 1:
        errors.append("min_quorum must be >= 1")
    if status.get("certification_scope") not in {"single_model", "multi_model"}:
        errors.append("certification_scope must be single_model or multi_model")
    if status.get("multi_model_certified") and status.get("certification_scope") != "multi_model":
        errors.append("multi_model_certified requires certification_scope=multi_model")
    if status.get("multi_model_certified") and status.get("success_count", 0) < 2:
        errors.append("multi_model_certified requires success_count >= 2")
    if status.get("status") == "degraded_not_certified" and status.get("certified"):
        errors.append("degraded_not_certified cannot be certified")
    if status.get("status") == "all_failed" and status.get("success_count") != 0:
        errors.append("all_failed requires success_count=0")
    if not str(status.get("reason", "")).strip():
        errors.append("reason must be non-empty")
    return not errors, errors


def quota_observability_summary(quota_snapshot: dict) -> dict:
    """Summarize quota confidence without treating unknown/unobservable as healthy.

    Exhausted quotas are gated elsewhere. This summary is for artifact visibility:
    exact/estimated are higher confidence; unknown/unobservable require explicit
    degraded-confidence handling by humans or cron wrappers.
    """
    summary = {
        "schema_version": 1,
        "exact_count": 0,
        "estimated_count": 0,
        "unknown_count": 0,
        "unobservable_count": 0,
        "exhausted_count": 0,
        "has_low_confidence_quota": False,
        "low_confidence_models": [],
    }
    for snap in (quota_snapshot or {}).values():
        if not isinstance(snap, dict):
            continue
        model = snap.get("model") or snap.get("name") or "unknown"
        status = str(snap.get("status") or "unknown").lower()
        observability = str(snap.get("observability") or snap.get("quota_type") or status or "unknown").lower()
        if status == "exhausted":
            summary["exhausted_count"] += 1
        if observability == "exact":
            summary["exact_count"] += 1
        elif observability == "estimated":
            summary["estimated_count"] += 1
        elif observability == "unobservable" or status == "unobservable":
            summary["unobservable_count"] += 1
            summary["low_confidence_models"].append(model)
        else:
            summary["unknown_count"] += 1
            summary["low_confidence_models"].append(model)
    summary["low_confidence_models"] = sorted(set(summary["low_confidence_models"]))
    summary["has_low_confidence_quota"] = bool(summary["low_confidence_models"])
    return summary


def evaluate_ratification(
    votes: List[dict],
    agreement_matrix: dict,
    issue_ledger: List[dict],
    revised_this_round: bool,
    novel_redteam_blocker: bool,
    min_agreement: float = 0.85,
    truth_gate: Optional[dict] = None,
) -> dict:
    """Evaluate true multi-model stop condition.

    Multi-model approval is not factual verification. If an evidence/truth gate is
    supplied, unsupported or contradicted high-severity claims fail closed even when
    every reviewer votes approve.
    """
    reasons: List[str] = []
    n = len(votes)
    approvals = sum(1 for v in votes if str(v.get("vote", "")).lower() == "approve")
    rejects = [v for v in votes if str(v.get("vote", "")).lower() == "reject"]
    unsigned = [v for v in votes if not v.get("best_within_constraints")]
    blockers = [i for i in issue_ledger if i.get("status") == "unresolved" and int(i.get("severity", 0)) >= 3]

    if approvals < max(1, n - 1):
        reasons.append(f"approval_count {approvals}/{n} below N-1")
    if rejects:
        reasons.append(f"reject votes present: {[v.get('model') for v in rejects]}")
    if unsigned:
        reasons.append(f"missing best_within_constraints signatures: {[v.get('model') for v in unsigned]}")
    for axis in ("framing", "approach", "implementation_order"):
        if float(agreement_matrix.get(axis, 0.0)) < min_agreement:
            reasons.append(f"agreement.{axis} below {min_agreement}")
    if revised_this_round:
        reasons.append("revision occurred this round")
    if novel_redteam_blocker:
        reasons.append("novel severity>=3 red-team blocker")
    if blockers:
        reasons.append(f"unresolved blockers: {[i.get('id') for i in blockers]}")
    if truth_gate:
        unsupported_high = truth_gate.get("unsupported_high_severity_claim_ids") or []
        contradicted_high = truth_gate.get("contradicted_high_severity_claim_ids") or []
        if unsupported_high:
            reasons.append(f"unsupported high-severity factual claims: {unsupported_high}")
        if contradicted_high:
            reasons.append(f"contradicted high-severity factual claims: {contradicted_high}")
        if not truth_gate.get("can_certify_truth", True) and not (unsupported_high or contradicted_high):
            reasons.append("truth gate not certified: " + "; ".join(truth_gate.get("reasons", [])))

    minor_risks = [i for i in issue_ledger if i.get("status") == "unresolved" and int(i.get("severity", 0)) <= 2]
    if reasons:
        status = "not_certified"
    elif minor_risks:
        status = "certified_with_minor_risks"
    else:
        status = "certified"
    return {
        "status": status,
        "approval_count": approvals,
        "reject_count": len(rejects),
        "reasons": reasons,
    }


def _agreement_from_issues(issue_ledger: List[dict]) -> dict:
    unresolved = [i for i in issue_ledger if i.get("status") == "unresolved"]
    blockers = [i for i in unresolved if int(i.get("severity", 0)) >= 3]
    if not unresolved:
        score = 0.95
    elif not blockers:
        score = 0.87
    else:
        score = 0.65
    return {"framing": score, "approach": score, "implementation_order": score}


def _offline_votes(models: List[str], issue_ledger: List[dict]) -> List[dict]:
    blockers = [i for i in issue_ledger if i.get("status") == "unresolved" and int(i.get("severity", 0)) >= 3]
    vote = "reject" if blockers else "approve"
    return [
        {
            "model": model,
            "vote": vote,
            "best_within_constraints": not blockers,
            "reasoning": "offline deterministic ratification; blockers present" if blockers else "offline deterministic ratification; no unresolved blockers",
        }
        for model in models
    ]


def run_discussion_rounds(
    plans: List[dict],
    current_best: dict,
    models: Optional[List[str]] = None,
    max_rounds: int = 5,
    offline: bool = False,
    call_model_fn=None,
    evidence_bundle: Optional[dict] = None,
) -> dict:
    """Run Phase 3-6 discussion/ratification loop.

    Offline mode is deterministic and used for tests/dry-runs. Online mode currently
    performs ratification prompts through call_model_fn when supplied; if no callable is
    supplied, it safely falls back to offline behavior rather than pretending certification.
    """
    models = models or [_plan_model(p, f"model_{i}") for i, p in enumerate(plans)]
    issue_ledger = build_issue_ledger(plans)
    evidence_bundle = evidence_bundle or build_evidence_bundle({})
    truth_gate = evaluate_truth_gate(evidence_bundle)
    evidence_requests = collect_evidence_requests(plans)
    rounds_used = 0
    transcript: List[dict] = []
    revised_this_round = False
    novel_redteam_blocker = False

    for round_no in range(1, max(1, max_rounds) + 1):
        rounds_used = round_no
        unresolved = [i for i in issue_ledger if i.get("status") == "unresolved"]
        if offline or call_model_fn is None:
            # Deterministic dry-run: no blockers means every model can certify; blockers
            # remain unresolved and correctly prevent false certification.
            votes = _offline_votes(models, issue_ledger)
        else:
            votes = []
            new_critiques = []
            prompt_context = {
                "phase": "cross_critique_rebuttal_ratification",
                "current_best": current_best,
                "unresolved_issues": unresolved,
                "evidence_bundle": evidence_bundle,
                "truth_gate": truth_gate,
                "instructions": [
                    "Challenge unresolved issues with specific evidence/correction/experiment.",
                    "Do not claim tool-verified truth unless a claim is backed by evidence_bundle.grounding.",
                    "If required evidence is missing, output evidence_requests instead of asserting the fact.",
                    "If your prior position is challenged, rebut or concede in reasoning.",
                    "Vote approve only if this is best_within_constraints and no blocker remains.",
                ],
                "required_output": {
                    "critiques": [{"target_model": "...", "severity": 1, "claim": "...", "evidence": "...", "correction": "...", "novel": True}],
                    "evidence_requests": [{"claim_id": "C-001", "tool_needed": "terminal|file|web", "command": "read-only command/query", "why": "what this would verify"}],
                    "vote": "approve|amend|reject",
                    "best_within_constraints": True,
                    "reasoning": "...",
                },
            }
            for model in models:
                try:
                    raw = call_model_fn(model, json.dumps(prompt_context, ensure_ascii=False))
                    parsed = extract_plan_json(raw)
                except Exception as e:
                    parsed = {"vote": "amend", "best_within_constraints": False, "reasoning": f"discussion call failed/unparseable: {str(e)[:160]}", "critiques": []}
                for critique in parsed.get("critiques", []) or []:
                    if not isinstance(critique, dict) or not critique.get("novel", True):
                        continue
                    severity = int(critique.get("severity", 3) or 3)
                    if severity >= 3:
                        new_critiques.append({
                            "id": f"I-{len(issue_ledger) + len(new_critiques) + 1:03d}",
                            "status": "unresolved",
                            "severity": severity,
                            "models": [model],
                            "target_model": critique.get("target_model", "unknown"),
                            "claim": critique.get("claim", "model critique"),
                            "evidence": critique.get("evidence", ""),
                            "resolution": critique.get("correction", ""),
                        })
                for req in collect_evidence_requests([{**parsed, "meta": {"planner_model": model}}]):
                    key = (req.get("requested_by"), req.get("claim_id"), req.get("claim"), req.get("tool_needed"), req.get("command"), req.get("why"))
                    existing = {(r.get("requested_by"), r.get("claim_id"), r.get("claim"), r.get("tool_needed"), r.get("command"), r.get("why")) for r in evidence_requests}
                    if key not in existing:
                        evidence_requests.append(req)
                votes.append({"model": model, "vote": parsed.get("vote", "amend"), "best_within_constraints": bool(parsed.get("best_within_constraints")), "reasoning": parsed.get("reasoning", "")})
            if new_critiques:
                issue_ledger.extend(new_critiques)
                novel_redteam_blocker = True

        agreement = _agreement_from_issues(issue_ledger)
        status = evaluate_ratification(votes, agreement, issue_ledger, revised_this_round, novel_redteam_blocker, truth_gate=truth_gate)
        transcript.append({
            "round": round_no,
            "unresolved_issue_ids": [i.get("id") for i in unresolved],
            "votes": votes,
            "status": status,
        })
        if status["status"] in ("certified", "certified_with_minor_risks"):
            break
        # If there are blockers and no online model callable to resolve them, more
        # deterministic rounds cannot change the result. Stop honestly.
        if offline or call_model_fn is None:
            break

    final_status = transcript[-1]["status"] if transcript else {"status": "not_certified", "reasons": ["no rounds executed"]}
    return {
        "status": final_status["status"],
        "models_consulted": models,
        "rounds_used": rounds_used,
        "agreement_matrix": _agreement_from_issues(issue_ledger),
        "final_design": current_best,
        "issue_ledger": issue_ledger,
        "ratification_votes": transcript[-1]["votes"] if transcript else [],
        "discussion_transcript": transcript,
        "remaining_risks": [i for i in issue_ledger if i.get("status") != "resolved"],
        "truth_assessment": truth_gate,
        "evidence_bundle": evidence_bundle,
        "evidence_requests": evidence_requests,
        "provenance": [f"{_plan_model(plan, f'model_{i}')} contributed seed proposal" for i, plan in enumerate(plans)],
        "reasons": final_status.get("reasons", []),
    }


def _load_env_file(path: Optional[str] = None) -> dict:
    """Load simple KEY=VALUE lines without overriding process env."""
    path = path or os.path.join(HERMES_HOME, ".env")
    data = {}
    try:
        with open(os.path.expanduser(path)) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                data[key.strip()] = value.strip().strip('"').strip("'")
    except OSError:
        pass
    return data


def call_deepseek_api(prompt: str, model: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    """Direct DeepSeek adapter used because Hermes CLI may not expose --provider deepseek."""
    import urllib.error
    import urllib.request

    env_file = _load_env_file()
    key = os.environ.get("DEEPSEEK_API_KEY") or env_file.get("DEEPSEEK_API_KEY")
    if not key:
        raise RuntimeError("DEEPSEEK_API_KEY missing")
    api_model = os.environ.get("DEEPSEEK_MODEL") or ("deepseek-reasoner" if "reasoner" in model else "deepseek-chat")
    payload = json.dumps({
        "model": api_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 1800,
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            if model_quota:
                model_quota.record_call(model=model, provider="deepseek", ok=True, headers=dict(resp.headers), usage={})
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:500]
        if model_quota:
            model_quota.record_call(model=model, provider="deepseek", ok=False, headers=dict(e.headers or {}), error=detail)
        raise RuntimeError(f"DeepSeek API HTTP {e.code}: {detail}") from e
    data = json.loads(body)
    return data["choices"][0]["message"]["content"]


def call_discussion_model(model: str, prompt: str, config: dict, timeout: int = DEFAULT_TIMEOUT) -> str:
    """Call a model for discussion/challenge/ratification text output."""
    provider = model_provider(config, model)
    if provider == "deepseek":
        return call_deepseek_api(prompt, model, timeout=timeout)
    hermes_bin = shutil.which("hermes") or "hermes"
    cmd = [hermes_bin, "chat", "-q", prompt, "--model", model, "--quiet", "--max-turns", "1", "--source", "multi-brain-discussion", "--ignore-rules"]
    if "claude" in model.lower():
        cmd += ["--provider", "anthropic"]
    elif provider in SUPPORTED_HERMES_PROVIDERS:
        cmd += ["--provider", provider]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        if model_quota:
            model_quota.record_call(model=model, provider=provider or model_quota.provider_for_model(model, config), ok=False, headers={}, error=(r.stderr or r.stdout)[:500])
        raise RuntimeError((r.stderr or r.stdout)[:500])
    if model_quota:
        model_quota.record_call(model=model, provider=provider or model_quota.provider_for_model(model, config), ok=True, headers={}, usage={})
    return r.stdout


def extract_plan_json(raw: str) -> dict:
    """Extract plan JSON from Claude wrapper, fenced JSON, or raw model output."""
    text = (raw or "").strip()
    if not text:
        raise json.JSONDecodeError("empty output", text, 0)

    try:
        outer = json.loads(text)
        if isinstance(outer, dict) and isinstance(outer.get("result"), str):
            text = outer["result"].strip()
        elif isinstance(outer, dict) and "meta" in outer and "diagnosis" in outer:
            return outer
    except json.JSONDecodeError:
        pass

    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))

    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return json.loads(text[start:end + 1])
    return json.loads(text)


def normalize_plan(plan: dict, model: str, state_hash: str, tier: str,
                   chain_id: str, provider: str, adapter: str,
                   latency_ms: int) -> dict:
    """Fill required fields so downstream consensus can compare plans safely."""
    if not isinstance(plan, dict):
        raise ValueError("plan is not a JSON object")
    plan.setdefault("meta", {})
    plan["meta"].update({
        "planner_model": model,
        "planner_role": plan["meta"].get("planner_role", "architect"),
        "state_hash": state_hash,
        "tier_target": tier,
        "chain_id": chain_id,
        "provider": provider or "unknown",
        "adapter": adapter,
        "latency_ms": latency_ms,
    })
    plan["meta"]["confidence"] = float(plan["meta"].get("confidence", 0.5))
    plan.setdefault("diagnosis", {"root_cause_class": "no_action", "evidence_field_ids": [], "summary": ""})
    plan.setdefault("patches", [])
    for p in plan["patches"]:
        if not p.get("id"):
            body = "|".join([p.get("target_file", ""), p.get("op", ""), p.get("rationale", "")])
            p["id"] = hashlib.sha1(body.encode()).hexdigest()[:12]
    plan.setdefault("verification", {"expected_metric_delta": {"main_pass_rate": 0.0}, "guard_metrics": ["main_pass_rate"], "tier_eval_plan": "T0_only"})
    plan.setdefault("evidence_requests", [])
    plan.setdefault("rollback_signal", {"auto_rollback_if": "main_pass_rate < pre - 0.05", "kill_switch_inc": False})
    return plan


def call_planner_model(model: str, prompt: str, state_hash: str, tier: str,
                       chain_id: str, config: dict, timeout: int) -> Tuple[dict, dict]:
    """Actually invoke the requested planner model via its best available adapter."""
    hermes_bin = shutil.which("hermes") or "hermes"
    provider = model_provider(config, model)
    if os.environ.get("HERMES_MULTI_BRAIN_OFFLINE") == "1":
        plan = generate_shadow_plan(model, state_hash, tier, chain_id)
        plan["diagnosis"]["summary"] = f"Offline adapter dry-run for {model}"
        return plan, {"ok": True, "adapter": "offline", "provider": provider, "latency_ms": 0}

    # SPL can save tokens, but it must never drop the orchestrator-owned state/evidence.
    # Keep natural prompts by default until the SPL encoder supports full state payloads.
    if _spl_available and os.environ.get("HERMES_MULTI_BRAIN_USE_SPL") == "1":
        try:
            tier_enum = SPLTier[tier] if isinstance(tier, str) else tier
            spl_msg = _spl_encoder.encode_planner_call(
                model=model, state={},
                tier=tier_enum, state_hash=state_hash,
            )
            prompt = json.dumps(spl_msg, ensure_ascii=False)
        except Exception:
            pass  # fall back to original prompt

    adapter = ""
    cmd = []
    if provider == "deepseek":
        adapter = "deepseek-api"
        start = time.time()
        try:
            raw = call_deepseek_api(prompt, model, timeout=timeout)
            latency_ms = int((time.time() - start) * 1000)
            parsed = extract_plan_json(raw)
            plan = normalize_plan(parsed, model, state_hash, tier, chain_id, provider, adapter, latency_ms)
            return plan, {"ok": True, "adapter": adapter, "provider": provider, "latency_ms": latency_ms}
        except Exception as e:
            latency_ms = int((time.time() - start) * 1000)
            plan = generate_shadow_plan(model, state_hash, tier, chain_id)
            plan["meta"]["confidence"] = 0.2
            plan["diagnosis"]["summary"] = f"{model} direct DeepSeek adapter failed: {str(e)[:240]}"
            return plan, {"ok": False, "adapter": adapter, "provider": provider, "error": str(e)[:500], "latency_ms": latency_ms}
    if "claude" in model.lower():
        adapter = "hermes-chat"
        cmd = [hermes_bin, "chat", "-q", prompt, "--model", model,
               "--provider", "anthropic", "--quiet", "--max-turns", "1",
               "--source", "multi-brain", "--ignore-rules"]
    elif shutil.which("hermes"):
        adapter = "hermes-chat"
        cmd = [hermes_bin, "chat", "-q", prompt, "--model", model, "--quiet", "--max-turns", "1", "--source", "multi-brain", "--ignore-rules"]
        if provider in SUPPORTED_HERMES_PROVIDERS:
            cmd += ["--provider", provider]

    if not cmd:
        plan = generate_shadow_plan(model, state_hash, tier, chain_id)
        plan["meta"]["confidence"] = 0.2
        plan["diagnosis"]["summary"] = f"No adapter available for {model}"
        return plan, {"ok": False, "adapter": "none", "provider": provider, "error": "no_adapter"}

    start = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        latency_ms = int((time.time() - start) * 1000)
        if r.returncode != 0:
            if model_quota:
                model_quota.record_call(model=model, provider=provider or model_quota.provider_for_model(model, config), ok=False, headers={}, error=(r.stderr or r.stdout)[:500])
            plan = generate_shadow_plan(model, state_hash, tier, chain_id)
            plan["meta"]["confidence"] = 0.2
            plan["diagnosis"]["summary"] = f"{model} adapter {adapter} failed: {r.stderr[:240]}"
            return plan, {"ok": False, "adapter": adapter, "provider": provider, "exit_code": r.returncode, "latency_ms": latency_ms, "stderr": r.stderr[:500]}
        if model_quota:
            model_quota.record_call(model=model, provider=provider or model_quota.provider_for_model(model, config), ok=True, headers={}, usage={})
        parsed = extract_plan_json(r.stdout)
        plan = normalize_plan(parsed, model, state_hash, tier, chain_id, provider, adapter, latency_ms)
        return plan, {"ok": True, "adapter": adapter, "provider": provider, "latency_ms": latency_ms}
    except subprocess.TimeoutExpired:
        if model_quota:
            model_quota.record_call(model=model, provider=provider or model_quota.provider_for_model(model, config), ok=False, headers={}, error=f"timeout after {timeout}s")
        plan = generate_shadow_plan(model, state_hash, tier, chain_id)
        plan["meta"]["confidence"] = 0.2
        plan["diagnosis"]["summary"] = f"{model} timed out after {timeout}s via adapter"
        return plan, {"ok": False, "adapter": adapter, "provider": provider, "timeout_s": timeout}
    except (json.JSONDecodeError, ValueError, OSError) as e:
        if model_quota:
            model_quota.record_call(model=model, provider=provider or model_quota.provider_for_model(model, config), ok=False, headers={}, error=str(e)[:500])
        plan = generate_shadow_plan(model, state_hash, tier, chain_id)
        plan["meta"]["confidence"] = 0.2
        plan["diagnosis"]["summary"] = f"{model} output parse/invoke failed: {e}"
        return plan, {"ok": False, "adapter": adapter, "provider": provider, "error": str(e)[:500]}


def generate_shadow_plan(model: str, state_hash: str, tier: str, chain_id: str) -> dict:
    """生成 Phase 0 shadow 计划模板"""
    return {
        "meta": {
            "planner_model": model,
            "planner_role": "architect",
            "state_hash": state_hash,
            "tier_target": tier,
            "confidence": 0.8,
            "cost_usd": 0.01,
            "latency_ms": 5000,
            "chain_id": chain_id,
        },
        "diagnosis": {
            "root_cause_class": "no_action",
            "evidence_field_ids": [],
            "summary": f"Phase 0 shadow plan by {model} — no changes proposed"
        },
        "patches": [],
        "verification": {
            "expected_metric_delta": {"main_pass_rate": 0.0},
            "guard_metrics": ["main_pass_rate"],
            "tier_eval_plan": "T0_only"
        },
        "evidence_requests": [],
        "rollback_signal": {
            "auto_rollback_if": "main_pass_rate < pre - 0.10",
            "kill_switch_inc": False
        }
    }


def emit_phase_event(phase: str, chain_id: str, task_id: str,
                     verdict: str, summary: str,
                     extensions: Optional[dict] = None):
    """发射 L2 协议事件"""
    try:
        msg = protocol_wrap(
            agent_id="consult-models",
            task_id=task_id,
            verdict=verdict,
            summary=summary,
            chain_id=chain_id,
            verification_pattern="multi_brain",
            extensions=extensions,
        )
        protocol_emit(msg)
        return msg
    except ProtocolError as e:
        print(f"[consult_models] Protocol emit failed: {e}", file=sys.stderr)
        return None


def run_fanout(
    state_file: str,
    tier: str = "T2",
    quorum_override: Optional[int] = None,
    shadow: bool = False,
    keep_ticks: bool = False,
    timeout: int = DEFAULT_TIMEOUT,
    discussion: bool = False,
    max_rounds: int = 5,
) -> dict:
    """
    运行多脑 fan-out。

    Returns:
        {"merged_plan": dict, "chain_id": str, "tick_dir": str, "models_used": [...]}
    """
    cleanup_old_ticks()

    # ── 1. 加载配置 ──
    quorum = load_quorum()
    config = load_config()
    skip_claude = os.environ.get("SKIP_CLAUDE", "0") == "1"

    planners, q_count, min_q = get_tier_planners(quorum, tier, skip_claude)
    if quorum_override:
        q_count = quorum_override

    # 先做额度硬门控，再截取 quorum 数量。unknown/unobservable 允许，exhausted 跳过；
    # later healthy planners can backfill exhausted preferred planners.
    planners, skipped_due_to_quota, quota_snapshot = select_planners_for_fanout(
        planners, q_count, config=config
    )
    quota_confidence = quota_observability_summary(quota_snapshot)
    if not planners:
        print("[consult_models] No planners available after quota gate", file=sys.stderr)
        return {
            "error": "no_planners_after_quota_gate",
            "tier": tier,
            "skipped_due_to_quota": skipped_due_to_quota,
            "quota_snapshot": quota_snapshot,
            "quota_confidence": quota_confidence,
        }

    print(f"[consult_models] Tier={tier} Quorum={q_count} Min={min_q} "
          f"Planners={planners} Shadow={shadow} QuotaSkipped={len(skipped_due_to_quota)}", file=sys.stderr)

    # ── 2. 计算 state_hash ──
    state_hash = compute_state_hash(state_file)
    chain_id = str(uuid.uuid4())

    # ── 3. 创建 TICK_DIR ──
    tick_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    tick_dir = os.path.join(HERMES_HOME, f"tick-{tick_id}")
    plans_dir = os.path.join(tick_dir, "plans")
    os.makedirs(plans_dir, exist_ok=True)

    # ── 4. 发射 FANOUT_START 事件 ──
    emit_phase_event("fanout_start", chain_id, f"multi-brain-{tick_id}",
                     "pending", f"Fan-out to {len(planners)} planners: {planners}",
                     {"tier": tier, "quorum": q_count, "planners": planners, "shadow": shadow,
                      "quota_snapshot": quota_snapshot, "quota_confidence": quota_confidence,
                      "skipped_due_to_quota": skipped_due_to_quota})

    # ── 5. 加载 state ──
    with open(state_file) as f:
        state = json.load(f)
    state.setdefault("budget", {})
    state["budget"]["model_quota_snapshot"] = quota_snapshot
    state["budget"]["model_quota_confidence"] = quota_confidence
    state["budget"]["skipped_due_to_quota"] = skipped_due_to_quota
    evidence_bundle = build_evidence_bundle(state)
    truth_gate = evaluate_truth_gate(evidence_bundle)
    state["evidence_bundle"] = evidence_bundle
    state["truth_gate"] = truth_gate

    # ── 6. Fan-out: 为每个 planner 生成计划 ──
    plan_files = []
    success_count = 0
    fail_count = 0

    for model in planners:
        safe_name = model.replace("/", "_").replace(" ", "_")
        plan_file = os.path.join(plans_dir, f"{safe_name}.json")
        plan_files.append(plan_file)

        print(f"[consult_models] → {model} planning...", file=sys.stderr)

        if shadow:
            # Phase 0: 生成影子模板
            plan = generate_shadow_plan(model, state_hash, tier, chain_id)
            with open(plan_file, "w") as f:
                json.dump(plan, f, indent=2, ensure_ascii=False)
            success_count += 1
            emit_phase_event(
                "planner_done", chain_id, f"planner-{safe_name}",
                "pass", f"Shadow plan generated for {model}",
                {"model": model, "shadow": True}
            )
        else:
            # Phase 1+: 通过模型专属 adapter 实际调用，不再用 Claude 冒充所有 planner。
            prompt = build_planner_prompt(state, state_hash, model, tier)
            plan, adapter_info = call_planner_model(
                model=model,
                prompt=prompt,
                state_hash=state_hash,
                tier=tier,
                chain_id=chain_id,
                config=config,
                timeout=timeout,
            )
            with open(plan_file, "w") as f:
                json.dump(plan, f, indent=2, ensure_ascii=False)

            ok = bool(adapter_info.get("ok"))
            if ok:
                success_count += 1
            else:
                fail_count += 1

            verdict = "pass" if ok else (
                "timeout" if "timeout_s" in adapter_info else "fail"
            )
            emit_phase_event(
                "planner_done", chain_id, f"planner-{safe_name}",
                verdict,
                f"{model} plan {'completed' if ok else 'failed'} via {adapter_info.get('adapter')}",
                {"model": model, "shadow": False, "adapter": adapter_info}
            )

    # ── 7. 降级检查 ──
    degradation = quorum.get("degradation", {})
    fanout_status = fanout_certification_status(
        success_count=success_count,
        planner_count=len(planners),
        min_quorum=min_q,
        fail_count=fail_count,
    )
    fanout_ok, fanout_errors = validate_fanout_certification_status(fanout_status)
    if not fanout_ok:
        print(f"[consult_models] Invalid fanout certification: {fanout_errors}", file=sys.stderr)
        fanout_status["status"] = "degraded_not_certified"
        fanout_status["certified"] = False
        fanout_status["multi_model_certified"] = False
        fanout_status["reason"] = "invalid fanout certification schema: " + "; ".join(fanout_errors)
    if fail_count >= len(planners):
        print("[consult_models] All planners failed — skip_tick", file=sys.stderr)
        emit_phase_event("fanout_end", chain_id, f"multi-brain-{tick_id}",
                         "fail", "All planners failed",
                         {"success": success_count, "fail": fail_count,
                          "fanout_certification": fanout_status,
                          "quota_confidence": quota_confidence})
        return {"error": "all_failed", "tick_dir": tick_dir, "chain_id": chain_id,
                "fanout_certification": fanout_status, "quota_confidence": quota_confidence}
    elif fail_count >= len(planners) - min_q + 1:
        print(f"[consult_models] Below min_quorum ({min_q}) — solo_plan_low_risk", file=sys.stderr)
        emit_phase_event("fanout_end", chain_id, f"multi-brain-{tick_id}",
                         "partial", f"Below min_quorum ({success_count}/{len(planners)})",
                         {"success": success_count, "fail": fail_count,
                          "fanout_certification": fanout_status,
                          "quota_confidence": quota_confidence})

    # ── 8. Consensus ──
    print(f"[consult_models] Running consensus on {len(plan_files)} plans...", file=sys.stderr)
    try:
        r = subprocess.run(
            [sys.executable, os.path.join(SCRIPTS_DIR, "consensus-plans.py"),
             "merge"] + plan_files,
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode == 0:
            merged = json.loads(r.stdout)
        else:
            merged = {"error": "consensus_failed", "detail": r.stderr[:500]}
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        merged = {"error": "consensus_error", "detail": str(e)}

    merged_file = os.path.join(tick_dir, "merged_plan.json")
    merged["quota_snapshot"] = quota_snapshot
    merged["quota_confidence"] = quota_confidence
    merged["skipped_due_to_quota"] = skipped_due_to_quota
    merged["fanout_certification"] = fanout_status
    merged["evidence_bundle"] = evidence_bundle
    merged["truth_assessment"] = truth_gate
    if not truth_gate.get("can_certify_truth", True):
        merged["certification_status"] = "truth_not_certified"
        merged.setdefault("degradation_reasons", []).extend(truth_gate.get("reasons", []))
    if fanout_status.get("below_min_quorum"):
        merged["certification_status"] = "degraded_not_certified"
        merged.setdefault("degradation_reasons", []).append(
            f"planner fan-out below min_quorum: {success_count}/{min_q}"
        )
    with open(merged_file, "w") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    discussion_result = None
    if discussion:
        loaded_plans = []
        for pf in plan_files:
            try:
                with open(pf) as f:
                    loaded_plans.append(json.load(f))
            except (OSError, json.JSONDecodeError) as e:
                print(f"[consult_models] WARN: failed to load plan for discussion {pf}: {e}", file=sys.stderr)
        if loaded_plans:
            discussion_result = run_discussion_rounds(
                loaded_plans,
                current_best=merged,
                models=planners,
                max_rounds=max_rounds,
                offline=shadow or os.environ.get("HERMES_MULTI_BRAIN_OFFLINE") == "1",
                call_model_fn=(lambda model, prompt: call_discussion_model(model, prompt, config, timeout=timeout)),
                evidence_bundle=evidence_bundle,
            )
        else:
            discussion_result = {"status": "not_certified", "reasons": ["no plans available for discussion"]}
        discussion_result["quota_snapshot"] = quota_snapshot
        discussion_result["quota_confidence"] = quota_confidence
        discussion_result["skipped_due_to_quota"] = skipped_due_to_quota
        discussion_result["fanout_certification"] = fanout_status
        discussion_result.setdefault("evidence_bundle", evidence_bundle)
        discussion_result.setdefault("truth_assessment", truth_gate)
        discussion_result.setdefault("evidence_requests", collect_evidence_requests(loaded_plans))
        if fanout_status.get("below_min_quorum"):
            discussion_result["status"] = "degraded_not_certified"
            discussion_result.setdefault("reasons", []).append(
                f"planner fan-out below min_quorum: {success_count}/{min_q}"
            )
        discussion_file = os.path.join(tick_dir, "discussion_result.json")
        with open(discussion_file, "w") as f:
            json.dump(discussion_result, f, indent=2, ensure_ascii=False)
        merged["discussion"] = {
            "status": discussion_result.get("status"),
            "result_file": discussion_file,
            "rounds_used": discussion_result.get("rounds_used"),
            "models_consulted": discussion_result.get("models_consulted", []),
        }

    # ── 9. 发射 FANOUT_END 事件 ──
    emit_phase_event("fanout_end", chain_id, f"multi-brain-{tick_id}",
                     "pass" if fanout_status.get("certified") and truth_gate.get("can_certify_truth", True) and "error" not in merged else "partial",
                     f"Consensus done — {success_count}/{len(planners)} planners succeeded" + 
                     (f" (degraded: {fail_count} failed)" if fail_count else ""),
                     {"success": success_count, "fail": fail_count,
                      "merged_file": merged_file, "tick_dir": tick_dir,
                      "fanout_certification": fanout_status,
                      "quota_confidence": quota_confidence,
                      "truth_assessment": truth_gate})

    # ── 10. 清理 (除非 --keep) ──
    if not keep_ticks:
        # 仅保留 merged_plan.json + plans/
        pass  # 保留 24h 内清理

    print(f"[consult_models] Done. Chain={chain_id} Artifacts in {tick_dir}/",
          file=sys.stderr)

    return {
        "merged_plan": merged,
        "chain_id": chain_id,
        "tick_dir": tick_dir,
        "plans_dir": plans_dir,
        "models_used": planners,
        "success_count": success_count,
        "fail_count": fail_count,
        "shadow": shadow,
        "discussion": discussion_result,
        "fanout_certification": fanout_status,
        "quota_snapshot": quota_snapshot,
        "quota_confidence": quota_confidence,
        "skipped_due_to_quota": skipped_due_to_quota,
        "evidence_bundle": evidence_bundle,
        "truth_assessment": truth_gate,
    }


def cli():
    parser = argparse.ArgumentParser(
        description="consult_models.py — 多脑 fan-out 编排器 v3"
    )
    sub = parser.add_subparsers(dest="cmd")

    # ── run ──
    run_p = sub.add_parser("run", help="Run multi-brain fan-out")
    run_p.add_argument("state_file", help="Path to state.json")
    run_p.add_argument("--tier", default="T2", help="Task tier (T0-T3)")
    run_p.add_argument("--quorum", type=int, default=None,
                       help="Override quorum count")
    run_p.add_argument("--shadow", action="store_true",
                       help="Phase 0 shadow mode (generate templates only)")
    run_p.add_argument("--keep", action="store_true",
                       help="Keep TICK_DIR after completion")
    run_p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                       help=f"Per-planner timeout in seconds (default: {DEFAULT_TIMEOUT})")
    run_p.add_argument("--discussion", action="store_true",
                       help="Run true multi-model discussion/ratification after fan-out")
    run_p.add_argument("--max-rounds", type=int, default=5,
                       help="Max discussion rounds before not_certified/certified_with_minor_risks")

    # ── state ──
    state_p = sub.add_parser("state", help="Create orchestrator-owned state.json from CLI inputs")
    state_p.add_argument("question", help="Problem/question for multi-model discussion")
    state_p.add_argument("--context-json", default="{}", help="JSON object with factual context")
    state_p.add_argument("--constraint", action="append", default=[], help="Constraint (repeatable)")
    state_p.add_argument("--accept", action="append", default=[], help="Acceptance criterion (repeatable)")
    state_p.add_argument("--file", action="append", default=[], help="Implementation target file (repeatable)")
    state_p.add_argument("--verify", action="append", default=[], help="Verification command (repeatable)")
    state_p.add_argument("--claim", action="append", default=[], help="Factual claim requiring evidence before truth certification; use id:text or plain text")
    state_p.add_argument("--evidence-json", action="append", default=[], help="JSON evidence object supporting/contradicting claims (repeatable)")
    state_p.add_argument("--out", default="", help="Write state JSON to this path instead of stdout")

    # ── status ──
    status_p = sub.add_parser("status", help="Show current quorum.yaml configuration")
    status_p.add_argument("--quota", action="store_true", help="Include current model quota snapshot")

    # ── cleanup ──
    sub.add_parser("cleanup", help="Clean all old TICK_DIRs")

    args = parser.parse_args()

    if args.cmd == "run":
        if not os.path.isfile(args.state_file):
            print(f"Error: not a file: {args.state_file}", file=sys.stderr)
            sys.exit(1)

        result = run_fanout(
            state_file=args.state_file,
            tier=args.tier,
            quorum_override=args.quorum,
            shadow=args.shadow,
            keep_ticks=args.keep,
            timeout=args.timeout,
            discussion=args.discussion,
            max_rounds=args.max_rounds,
        )

        # 输出 merged_plan
        if "merged_plan" in result:
            print(json.dumps(result["merged_plan"], indent=2, ensure_ascii=False))
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
            sys.exit(1)

    elif args.cmd == "state":
        try:
            context = json.loads(args.context_json)
            if not isinstance(context, dict):
                raise ValueError("--context-json must be a JSON object")
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error: invalid --context-json: {e}", file=sys.stderr)
            sys.exit(2)
        claims = []
        for i, raw_claim in enumerate(args.claim or [], start=1):
            if ":" in raw_claim and raw_claim.split(":", 1)[0].strip().startswith("C-"):
                cid, text = raw_claim.split(":", 1)
                claims.append({"id": cid.strip(), "text": text.strip(), "severity": 3})
            else:
                claims.append({"id": f"C-{i:03d}", "text": raw_claim, "severity": 3})
        evidence = []
        for raw_ev in args.evidence_json or []:
            try:
                ev = json.loads(raw_ev)
                if not isinstance(ev, dict):
                    raise ValueError("evidence JSON must be an object")
                evidence.append(ev)
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Error: invalid --evidence-json: {e}", file=sys.stderr)
                sys.exit(2)
        state = build_state(
            question=args.question,
            context=context,
            constraints=args.constraint,
            acceptance_criteria=args.accept,
            claims=claims,
            evidence=evidence,
            implementation_target={
                "files": args.file,
                "verify_commands": args.verify,
                "forbidden_changes": [],
            },
        )
        rendered = json.dumps(state, indent=2, ensure_ascii=False)
        if args.out:
            with open(args.out, "w") as f:
                f.write(rendered + "\n")
            print(args.out)
        else:
            print(rendered)

    elif args.cmd == "status":
        quorum = load_quorum()
        mb = quorum.get("multi_brain", {})
        tiers = quorum.get("tiers", {})
        offline = os.environ.get("HERMES_MULTI_BRAIN_OFFLINE") == "1"
        mode_label = "OFFLINE (dry-run, adapter only)" if offline else "ACTUAL (real model calls)"
        print(f"Mode:    {mode_label}")
        print(f"Phase:   {mb.get('phase', '?')}")
        print(f"Enabled: {mb.get('enabled', False)}")
        print(f"Shadow:  {mb.get('shadow_mode', True)}")
        print(f"Default arbiter: {mb.get('default_arbiter', '<none>')}")
        # Probe planner availability (best effort)
        avail_snapshot = {}
        snap_path = os.path.expanduser("~/.hermes/state/provider_availability.json")
        if os.path.exists(snap_path):
            try:
                with open(snap_path) as f:
                    avail_snapshot = json.load(f) or {}
            except Exception:
                avail_snapshot = {}
        for t_name in ["T0", "T1", "T2", "T3"]:
            t = tiers.get(t_name, {})
            planners = t.get("planners", [])
            skipped = []
            try:
                config = load_config()
                for m in planners:
                    p = model_provider(config, m)
                    key = f"{p}::{m}"
                    if avail_snapshot.get(key, {}).get("status") == "unavailable":
                        skipped.append(m)
            except Exception:
                pass
            extra = f" skipped={skipped}" if skipped else ""
            print(f"  {t_name}: quorum={t.get('quorum','?')} "
                  f"min={t.get('min_quorum','?')} "
                  f"arbiter={t.get('arbiter') or mb.get('default_arbiter') or '<none>'} "
                  f"planners={planners}{extra}")
        if getattr(args, "quota", False):
            print("\nQuota snapshot:")
            if model_quota:
                all_planners = []
                for t in tiers.values():
                    for m in t.get("planners", []) or []:
                        if m not in all_planners:
                            all_planners.append(m)
                snapshots = model_quota.snapshot_models(all_planners, config=load_config()) if all_planners else model_quota.load_state()
                print(model_quota.render_table(snapshots))
            else:
                print("  model_quota unavailable")

    elif args.cmd == "cleanup":
        cleanup_old_ticks()
        print("[consult_models] Cleanup complete.")

    else:
        parser.print_help()


if __name__ == "__main__":
    cli()
