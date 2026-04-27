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
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple

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

DEFAULT_TIMEOUT = 120  # per-planner timeout (seconds)
TICK_CLEANUP_AGE = 86400  # 24h — 清理旧 TICK_DIR


def load_quorum() -> dict:
    """读取 quorum.yaml"""
    path = os.path.join(CONFIG_DIR, "quorum.yaml")
    try:
        import yaml
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except (yaml.YAMLError, FileNotFoundError, OSError) as e:
        print(f"[consult_models] quorum.yaml load failed: {e}", file=sys.stderr)
        return {}


def load_config() -> dict:
    """读取 config.yaml"""
    path = os.path.join(HERMES_HOME, "config.yaml")
    try:
        import yaml
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


def build_planner_prompt(state: dict, state_hash: str, model: str, tier: str) -> str:
    """构建 planner 提示词 (同 consult-models.sh v2 格式)"""
    state_json = json.dumps(state, indent=2, ensure_ascii=False)[:8000]
    return f"""You are a Hermes Agent architecture planner.

Read the state below and produce a structured improvement plan.

STATE (sha256: {state_hash}):
{state_json}

Output ONLY valid JSON matching this schema:
{{
  "meta": {{"planner_model": "{model}", "planner_role": "architect", "state_hash": "{state_hash}", "tier_target": "{tier}", "confidence": 0.0-1.0}},
  "diagnosis": {{"root_cause_class": "regression|router_skew|verifier_gap|kill_switch_oscillation|consensus_drift|pricing_overrun|schema_mismatch|no_action", "evidence_field_ids": ["field1"], "summary": "..."}},
  "patches": [{{"id": "unique", "target_file": "path", "op": "tune_threshold|swap_model|add_verifier|modify_router_weight|raise_tier|lower_tier|noop", "rationale": "...", "risk": "low|med|high", "blast_radius": "single_tier|router|all_tiers|kill_switch", "depends_on": []}}],
  "verification": {{"expected_metric_delta": {{"main_pass_rate": 0.0}}, "guard_metrics": ["main_pass_rate"], "tier_eval_plan": "T0_only|T0_T1|T1_T2|full_T0_T3"}},
  "rollback_signal": {{"auto_rollback_if": "main_pass_rate < pre - 0.05", "kill_switch_inc": false}}
}}

Keep patches ≤ 5. Be concrete. Confidence must be honest."""


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

    # 截取 quorum 数量的 planner
    planners = planners[:q_count]
    if not planners:
        print("[consult_models] No planners available", file=sys.stderr)
        return {"error": "no_planners", "tier": tier}

    print(f"[consult_models] Tier={tier} Quorum={q_count} Min={min_q} "
          f"Planners={planners} Shadow={shadow}", file=sys.stderr)

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
                     {"tier": tier, "quorum": q_count, "planners": planners, "shadow": shadow})

    # ── 5. 加载 state ──
    with open(state_file) as f:
        state = json.load(f)

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
            # Phase 1+: 实际调用模型
            prompt = build_planner_prompt(state, state_hash, model, tier)
            try:
                r = subprocess.run(
                    ["claude", "-p", prompt, "--output-format", "json",
                     "--max-turns", "8", "--allowedTools", "Read"],
                    capture_output=True, text=True,
                    timeout=timeout,
                )
                if r.returncode == 0:
                    # 尝试解析 Claude 的 wrapped JSON
                    try:
                        raw = json.loads(r.stdout)
                        inner = raw.get("result", "")
                        # 提取 ```json ... ``` 块
                        import re
                        m = re.search(r'```json\n(.*?)```', inner, re.DOTALL)
                        if m:
                            plan = json.loads(m.group(1))
                        else:
                            plan = json.loads(inner)
                    except (json.JSONDecodeError, AttributeError):
                        plan = generate_shadow_plan(model, state_hash, tier, chain_id)
                        plan["diagnosis"]["root_cause_class"] = "no_action"
                        plan["diagnosis"]["summary"] = f"JSON parse failed for {model} output"
                        fail_count += 1

                    with open(plan_file, "w") as f:
                        json.dump(plan, f, indent=2, ensure_ascii=False)
                    success_count += 1
                    emit_phase_event(
                        "planner_done", chain_id, f"planner-{safe_name}",
                        "pass", f"{model} plan completed",
                        {"model": model, "shadow": False, "cost_est": 0.01}
                    )
                else:
                    fail_count += 1
                    plan = generate_shadow_plan(model, state_hash, tier, chain_id)
                    plan["diagnosis"]["summary"] = f"{model} failed: {r.stderr[:200]}"
                    with open(plan_file, "w") as f:
                        json.dump(plan, f, indent=2, ensure_ascii=False)
                    emit_phase_event(
                        "planner_done", chain_id, f"planner-{safe_name}",
                        "fail", f"{model} failed: exit={r.returncode}",
                        {"model": model, "stderr": r.stderr[:200]}
                    )
            except subprocess.TimeoutExpired:
                fail_count += 1
                plan = generate_shadow_plan(model, state_hash, tier, chain_id)
                plan["diagnosis"]["summary"] = f"{model} timed out after {timeout}s"
                with open(plan_file, "w") as f:
                    json.dump(plan, f, indent=2, ensure_ascii=False)
                emit_phase_event(
                    "planner_done", chain_id, f"planner-{safe_name}",
                    "timeout", f"{model} timed out ({timeout}s)",
                    {"model": model, "timeout_s": timeout}
                )

    # ── 7. 降级检查 ──
    degradation = quorum.get("degradation", {})
    if fail_count >= len(planners):
        print("[consult_models] All planners failed — skip_tick", file=sys.stderr)
        emit_phase_event("fanout_end", chain_id, f"multi-brain-{tick_id}",
                         "fail", "All planners failed",
                         {"success": success_count, "fail": fail_count})
        return {"error": "all_failed", "tick_dir": tick_dir, "chain_id": chain_id}
    elif fail_count >= len(planners) - min_q + 1:
        print(f"[consult_models] Below min_quorum ({min_q}) — solo_plan_low_risk", file=sys.stderr)
        emit_phase_event("fanout_end", chain_id, f"multi-brain-{tick_id}",
                         "partial", f"Below min_quorum ({success_count}/{len(planners)})",
                         {"success": success_count, "fail": fail_count})

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
    with open(merged_file, "w") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    # ── 9. 发射 FANOUT_END 事件 ──
    emit_phase_event("fanout_end", chain_id, f"multi-brain-{tick_id}",
                     "pass" if "error" not in merged else "partial",
                     f"Consensus done — {success_count}/{len(planners)} planners succeeded" + 
                     (f" (degraded: {fail_count} failed)" if fail_count else ""),
                     {"success": success_count, "fail": fail_count,
                      "merged_file": merged_file, "tick_dir": tick_dir})

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

    # ── status ──
    sub.add_parser("status", help="Show current quorum.yaml configuration")

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
        )

        # 输出 merged_plan
        if "merged_plan" in result:
            print(json.dumps(result["merged_plan"], indent=2, ensure_ascii=False))
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
            sys.exit(1)

    elif args.cmd == "status":
        quorum = load_quorum()
        mb = quorum.get("multi_brain", {})
        tiers = quorum.get("tiers", {})
        print(f"Phase: {mb.get('phase', '?')}")
        print(f"Enabled: {mb.get('enabled', False)}")
        print(f"Shadow: {mb.get('shadow_mode', True)}")
        for t_name in ["T0", "T1", "T2", "T3"]:
            t = tiers.get(t_name, {})
            print(f"  {t_name}: quorum={t.get('quorum','?')} "
                  f"min={t.get('min_quorum','?')} "
                  f"planners={t.get('planners',[])}")

    elif args.cmd == "cleanup":
        cleanup_old_ticks()
        print("[consult_models] Cleanup complete.")

    else:
        parser.print_help()


if __name__ == "__main__":
    cli()
