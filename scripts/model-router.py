#!/usr/bin/env python3
"""
model-router.py — ε-greedy 模型选择器 (L1, v2: cost-aware)
基于 route_outcomes 的 model_stats + pricing.py 的时间感知成本自动选择最优模型

用法:
  python3 model-router.py select --task-class feature.frontend
  python3 model-router.py select --task-tier codegen --task-class bugfix
  python3 model-router.py select-pair --task-tier codegen  # 返回 (producer, reviewer)
  python3 model-router.py status

v2 新增: 时间感知评分 (pricing.py), task_tier 过滤, select_pair 配对, MiMo 候补
"""

import argparse
import json
import os
import random
import sys
from datetime import datetime, timezone
from typing import List, Optional, Tuple
import subprocess
import yaml

# 延迟导入
_pricing = None

HERMES_HOME = os.path.expanduser(os.environ.get("HERMES_HOME", "~/.hermes"))
LOG_FILE = os.path.join(HERMES_HOME, "logs", "model-router.jsonl")
CONFIG_PATH = os.path.join(HERMES_HOME, "config.yaml")


def _get_pricing():
    global _pricing
    if _pricing is None:
        try:
            sys.path.insert(0, os.path.join(HERMES_HOME, "scripts"))
            from pricing import load_pricing
            _pricing = load_pricing(CONFIG_PATH)
        except (ImportError, AttributeError, yaml.YAMLError, OSError):
            pass
    return _pricing


def load_config():
    try:
        import yaml
    except ImportError:
        return None

    try:
        with open(CONFIG_PATH) as f:
            c = yaml.safe_load(f)
        routing = c.get("smart_model_routing", {})
        pt = _get_pricing()
        
        # 从 pricing 加载候选模型 (优先于 smart_model_routing 的静态列表)
        if pt:
            candidates = pt.get_candidate_models("codegen")  # 默认 codegen tier
        else:
            candidates = routing.get("candidate_models", [])
        
        return {
            "enabled": routing.get("enabled", False),
            "candidate_models": candidates,
            "epsilon": routing.get("epsilon", 0.1),
            "min_traces_per_model": routing.get("min_traces_per_model", 10),
            "default_model": c.get("model", {}).get("default", ""),
        }
    except (yaml.YAMLError, FileNotFoundError, OSError):
        return None


def get_model_stats(task_class=None, since_hours=168):
    import subprocess
    store_path = os.path.join(HERMES_HOME, "scripts", "route_store.py")
    args = [sys.executable, store_path, "model-stats", "--hours", str(since_hours)]
    if task_class:
        args += ["--task-class", task_class]
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=10)
        if r.returncode == 0 and r.stdout.strip():
            return json.loads(r.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        pass
    return []


def _effective_cost(model_name: str, tokens_est: int = 2000, now_utc=None) -> float:
    """时间感知的有效成本估算"""
    pt = _get_pricing()
    if pt is None:
        return 0.0
    return pt.estimate_cost(model_name, tokens_est, tokens_est // 2, now_utc)


def _schedule_label(model_name: str, now_utc=None) -> str:
    pt = _get_pricing()
    if pt is None:
        return "unknown"
    _, _, label = pt.effective_rate(model_name, now_utc)
    return label


def select_model(
    task_class=None,
    task_tier="codegen",
    epsilon=None,
    config=None,
    now_utc=None,
) -> dict:
    """ε-greedy 选择一个模型 (v2: cost-aware)
    
    新增:
    - task_tier: 从 pricing.candidate_groups 过滤候选
    - now_utc: 时间感知成本 (off-peak/peak/free)
    - 评分: pass_rate - λ_cost * effective_cost - λ_time * avg_dur
    """
    if now_utc is None:
        now_utc = datetime.now(timezone.utc)

    if config is None:
        config = load_config()
    if config is None:
        return {"model": "unknown", "reason": "config_load_failed"}

    if not config["enabled"]:
        return {"model": config["default_model"], "reason": "routing_disabled"}

    # 按 tier 过滤候选
    pt = _get_pricing()
    if pt:
        candidates = pt.get_candidate_models(task_tier)
        if not candidates:
            candidates = config.get("candidate_models", [])
    else:
        candidates = config.get("candidate_models", [])

    if not candidates:
        return {"model": config["default_model"], "reason": "no_candidates"}

    stats = get_model_stats(task_class=task_class)
    
    model_scores = {}
    for s in stats:
        model_scores[s["model"]] = s

    min_traces = config["min_traces_per_model"]
    cold_models = [
        m for m in candidates
        if m not in model_scores or model_scores[m]["count"] < min_traces
    ]

    if epsilon is None:
        epsilon = config["epsilon"]

    # 冷启动 → 强制探索, off-peak 偏向
    if cold_models:
        epsilon = 1.0
        reason = f"cold_start({len(cold_models)}_models_need_warmup)"
    else:
        reason = f"epsilon_greedy(epsilon={epsilon})"

    # ε-greedy 选择
    if random.random() < epsilon:
        # 探索: 随机选 (off-peak 时偏向便宜模型)
        if cold_models:
            chosen = random.choice(cold_models)
            reason = f"explore_cold({reason})"
        else:
            # off-peak: 偏向低成本模型
            pt_now = _get_pricing()
            if pt_now and pt_now.is_off_peak(candidates[0], now_utc):
                cheap = sorted(candidates, key=lambda m: _effective_cost(m, 2000, now_utc))
                chosen = cheap[0]
                reason = f"explore_offpeak({reason})"
            else:
                chosen = random.choice(candidates)
                reason = f"explore({reason})"
    else:
        # 利用: 选最高 score (含时间感知成本)
        def score_model(m):
            ms = model_scores.get(m, {})
            pr = ms.get("pass_rate", 0.5)
            ec = _effective_cost(m, 2000, now_utc)
            avg_dur = ms.get("avg_dur", 10)
            return pr - 0.1 * ec * 100 - 0.01 * avg_dur / 60  # λ_cost=0.1, λ_time=0.01

        scored = [(m, score_model(m)) for m in candidates]
        scored.sort(key=lambda x: x[1], reverse=True)
        chosen = scored[0][0]
        label = _schedule_label(chosen, now_utc)
        reason = f"exploit({reason}, score={scored[0][1]:.4f}, schedule={label})"

    return {
        "model": chosen,
        "reason": reason,
        "epsilon_used": epsilon,
        "candidates": candidates,
        "task_tier": task_tier,
        "schedule_label": _schedule_label(chosen, now_utc),
        "effective_cost_est": _effective_cost(chosen, 2000, now_utc),
        "model_scores": {
            m: model_scores[m]["score"] if m in model_scores else None
            for m in candidates
        },
    }


def select_pair(
    task_tier="codegen",
    task_class=None,
    diversity_rule="provider_or_savings",
    config=None,
    now_utc=None,
) -> dict:
    """为 verification 选择 (producer, reviewer) 对
    
    diversity_rule:
    - "provider_or_savings": 优先不同 provider; 同 provider 仅当 off-peak 节省 >30% 且 pass_rate≥0.9
    """
    if config is None:
        config = load_config()
    if now_utc is None:
        now_utc = datetime.now(timezone.utc)

    pt = _get_pricing()

    # 获取候选
    producer_candidates = pt.get_candidate_models(task_tier) if pt else config["candidate_models"]
    reviewer_candidates = pt.get_candidate_models("reviewer") if pt else config["candidate_models"]

    # 选择 producer
    prod = select_model(task_class=task_class, task_tier=task_tier, config=config, now_utc=now_utc)

    # 选择 reviewer (排除 producer 的 provider 优先)
    prod_provider = pt.get_provider(prod["model"]) if pt else "unknown"
    
    # 过滤: 优先不同 provider
    diverse_reviewers = [
        m for m in reviewer_candidates
        if m != prod["model"] and (not pt or pt.get_provider(m) != prod_provider)
    ]
    
    if diverse_reviewers:
        # 在 diverse reviewers 中选最优
        # 使用与 select_model 相同的逻辑
        rev_config = dict(config)
        rev_config["candidate_models"] = diverse_reviewers
        reviewer = select_model(
            task_class=task_class,
            task_tier="reviewer",
            config=rev_config,
            now_utc=now_utc,
        )
    else:
        # 无 diverse reviewer — 选同 provider 但要求 off-peak + 高 pass_rate
        same_provider = [m for m in reviewer_candidates if m != prod["model"]]
        if same_provider:
            # 检查 off-peak 节省
            if pt and pt.is_off_peak(prod["model"], now_utc):
                stats = get_model_stats(task_class=task_class)
                scored = [
                    (m, (stats.get(m, {}).get("pass_rate", 0.5) if m in {s["model"]: s for s in stats} else 0.5))
                    for m in same_provider
                ]
                best = max(scored, key=lambda x: x[1])
                if best[1] >= 0.9:
                    reviewer = {"model": best[0], "reason": "same_provider_offpeak_highconf"}
                else:
                    reviewer = select_model(task_class=task_class, task_tier="reviewer", config=config, now_utc=now_utc)
            else:
                reviewer = select_model(task_class=task_class, task_tier="reviewer", config=config, now_utc=now_utc)
        else:
            reviewer = {"model": None, "reason": "no_reviewer_available"}

    return {
        "producer": prod,
        "reviewer": reviewer,
        "diversity_rule": diversity_rule,
        "same_provider": (
            pt.get_provider(prod["model"]) == pt.get_provider(reviewer["model"])
            if pt and reviewer.get("model")
            else False
        ),
    }


def log_decision(decision, task_class=None):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "task_class": task_class or "",
        "task_tier": decision.get("task_tier", ""),
        "model": decision["model"],
        "reason": decision["reason"],
        "epsilon_used": decision.get("epsilon_used", 0),
        "schedule_label": decision.get("schedule_label", "?"),
        "eff_cost_est": decision.get("effective_cost_est", 0),
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def cli():
    parser = argparse.ArgumentParser(description="Model Router — ε-greedy 模型选择器 (v2: cost-aware)")
    sub = parser.add_subparsers(dest="cmd")

    sel = sub.add_parser("select", help="选择一个模型")
    sel.add_argument("--task-class", default="", help="任务分类")
    sel.add_argument("--task-tier", default="codegen", help="任务层级 (codegen/reviewer/arbiter/chat/tts)")
    sel.add_argument("--epsilon", type=float, default=None, help="探索率")
    sel.add_argument("--hour", type=int, default=None, help="模拟 UTC 小时 (0-23)")

    pair = sub.add_parser("select-pair", help="选择 (producer, reviewer) 对")
    pair.add_argument("--task-tier", default="codegen")
    pair.add_argument("--task-class", default="")
    pair.add_argument("--diversity-rule", default="provider_or_savings")
    pair.add_argument("--hour", type=int, default=None)

    sub.add_parser("status", help="显示路由状态")

    args = parser.parse_args()
    
    now = datetime.now(timezone.utc)
    hour = getattr(args, "hour", None)
    if hour is not None:
        now = now.replace(hour=hour, minute=0, second=0, microsecond=0)
    
    config = load_config()

    if args.cmd == "select":
        decision = select_model(
            task_class=args.task_class or None,
            task_tier=args.task_tier,
            epsilon=args.epsilon,
            config=config,
            now_utc=now,
        )
        log_decision(decision, task_class=args.task_class or None)
        print(decision["model"])

    elif args.cmd == "select-pair":
        result = select_pair(
            task_tier=args.task_tier,
            task_class=args.task_class or None,
            diversity_rule=args.diversity_rule,
            config=config,
            now_utc=now,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.cmd == "status":
        pt = _get_pricing()
        if config is None:
            print("Cannot load config")
            sys.exit(1)
        print(f"smart_model_routing: enabled={config['enabled']}")
        print(f"default model: {config['default_model']}")
        print(f"epsilon: {config['epsilon']}")
        print(f"min_traces: {config['min_traces_per_model']}")
        print(f"UTC hour: {now.hour:02d}:00")
        print()
        if pt:
            print("Pricing-aware candidates:")
            for tier in ["codegen", "reviewer", "arbiter", "chat", "tts"]:
                models = pt.get_candidate_models(tier)
                if models:
                    print(f"  {tier}: {models}")
        else:
            print(f"candidates (static): {config['candidate_models']}")
        print()
        stats = get_model_stats()
        if stats:
            print("Model stats (7d):")
            for s in stats:
                eff_cost = _effective_cost(s["model"], 2000, now)
                label = _schedule_label(s["model"], now)
                print(f"  {s['model']:25s} {s['count']:3d}x pass={s['pass_rate']:.0%} "
                      f"score={s['score']:.4f} eff_cost=${eff_cost:.5f} ({label})")
        print()
        if os.path.exists(LOG_FILE):
            print("Recent decisions:")
            with open(LOG_FILE) as f:
                lines = f.readlines()[-10:]
            for line in lines:
                try:
                    d = json.loads(line)
                    label = d.get("schedule_label", "?")
                    print(f"  {d['ts']} → {d['model']} ({d['reason'][:60]}) [{label}]")
                except json.JSONDecodeError:
                    pass

    else:
        parser.print_help()


if __name__ == "__main__":
    cli()
