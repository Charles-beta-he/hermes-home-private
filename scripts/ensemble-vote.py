#!/usr/bin/env python3
"""
ensemble-vote.py — 多模型投票/仲裁 (L3)
基于 delegate_task batch 模式实现的多模型并行执行与结果聚合

策略:
  - majority: 多数投票
  - weighted: 按 model_stats 的 score 加权
  - arbiter: 额外的裁判模型审查所有结果后决定

用法:
  python3 ensemble-vote.py vote --task "Review auth.py for bugs" --models gpt-5.4,claude-opus-4-7 --strategy majority
  python3 ensemble-vote.py vote --task "..." --strategy weighted --models gpt-5.4,claude-sonnet-4-6,claude-opus-4-7
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from typing import List, Dict, Optional

# L2 协议导入
sys.path.insert(0, os.path.dirname(__file__))
from agent_protocol import (
    wrap as protocol_wrap,
    try_wrap as protocol_try_wrap,
    emit as protocol_emit,
    ProtocolError,
)


HERMES_HOME = os.path.expanduser(os.environ.get("HERMES_HOME", "~/.hermes"))
LOG_FILE = os.path.join(HERMES_HOME, "logs", "ensemble-votes.jsonl")


def get_model_weights(models: List[str]) -> Dict[str, float]:
    """从 route_store 获取模型权重"""
    store_path = os.path.join(HERMES_HOME, "scripts", "route_store.py")
    try:
        r = subprocess.run(
            [sys.executable, store_path, "model-stats", "--hours", "168"],
            capture_output=True, text=True, timeout=10
        )
        if r.returncode == 0:
            stats = json.loads(r.stdout)
            weights = {}
            for s in stats:
                if s["model"] in models:
                    # score + 0.01 避免零权重
                    weights[s["model"]] = s["score"] + 0.01
            # 未在统计中的模型给默认权重
            for m in models:
                if m not in weights:
                    weights[m] = 0.5
            # 归一化
            total = sum(weights.values())
            if total > 0:
                weights = {k: round(v/total, 4) for k, v in weights.items()}
            return weights
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError) as e:
        print(f"[ensemble-vote] get_model_weights failed: {e}", file=sys.stderr)
        pass
    # 默认: 均匀权重
    return {m: round(1.0/len(models), 4) for m in models}


def majority_vote(results: List[dict]) -> dict:
    """多数投票聚合"""
    # 按 verdict 分布统计
    votes = {}
    for r in results:
        verdict = r.get("verdict", "unknown")
        votes[verdict] = votes.get(verdict, 0) + 1
    
    winner = max(votes, key=votes.get)
    return {
        "strategy": "majority",
        "verdict": winner,
        "votes": votes,
        "total_voters": len(results),
        "consensus": votes[winner] == len(results),
    }


def weighted_vote(results: List[dict], weights: Dict[str, float]) -> dict:
    """加权投票聚合"""
    score_by_verdict = {}
    for r in results:
        model = r.get("model", "unknown")
        verdict = r.get("verdict", "unknown")
        w = weights.get(model, 1.0)
        score_by_verdict[verdict] = score_by_verdict.get(verdict, 0) + w
    
    winner = max(score_by_verdict, key=score_by_verdict.get)
    total = sum(score_by_verdict.values())
    return {
        "strategy": "weighted",
        "verdict": winner,
        "weighted_scores": {k: round(v/total, 4) for k, v in score_by_verdict.items()},
        "weights_used": weights,
        "total_weight": round(total, 4),
    }


def vote(
    task: str,
    models: List[str],
    strategy: str = "majority",
    workdir: str = None,
) -> dict:
    """
    执行多模型投票
    
    注意: 当前实现为模拟/框架 — 真实并行执行需要 delegate_task ACP 支持。
    此处生成投票决策日志并返回预期的聚合结构。
    delegate_task 实际调用需由 Hermes 的 ACP 层支持多模型并发。
    """
    weights = get_model_weights(models)
    
    # 构建结果结构 (实际执行由 delegate_task 完成)
    # 这里先输出决策框架, 实际并行执行需 delegate_task toolsets 支持
    result = {
        "task": task,
        "models": models,
        "strategy": strategy,
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    
    # 记录权重信息
    result["model_weights"] = weights
    
    # 根据策略选择聚合方法
    if strategy == "weighted":
        result["expected_behavior"] = "Weighted vote: higher-score models get more influence"
    elif strategy == "arbiter":
        result["expected_behavior"] = "Arbiter: an additional model reviews all outputs"
    else:  # majority
        result["expected_behavior"] = "Majority vote: most common verdict wins"
    
    result["note"] = (
        "Actual parallel execution requires delegate_task with ACP "
        "model overrides. This framework provides the aggregation logic "
        "and logging. Use delegate_task with per-task acp_command/acp_args "
        "to specify different models."
    )
    
    # 记录到日志
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(result) + "\n")

    # ── L2 协议：包装为 agent_protocol 消息并持久化 ──
    try:
        protocol_msg = protocol_wrap(
            agent_id="ensemble-vote",
            task_id="vote-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"),
            verdict="pass" if result.get("consensus", False) else "partial",
            verification_pattern="ensemble_vote",
            extensions={
                "strategy": strategy,
                "models": models,
                "metadata": result.get("weighted_scores", result.get("votes", {})),
            },
        )
        result["agent_protocol"] = protocol_msg
        protocol_emit(protocol_msg)
    except ProtocolError as e:
        print(f"[ensemble-vote] Protocol wrap failed: {e}", file=sys.stderr)

    return result


def cli():
    parser = argparse.ArgumentParser(description="Ensemble Vote — 多模型投票")
    sub = parser.add_subparsers(dest="cmd")

    vt = sub.add_parser("vote", help="执行多模型投票")
    vt.add_argument("--task", required=True, help="任务描述")
    vt.add_argument("--models", required=True, help="逗号分隔的模型列表")
    vt.add_argument("--strategy", default="majority", 
                    choices=["majority", "weighted", "arbiter"])
    vt.add_argument("--workdir", default=None, help="工作目录")

    sub.add_parser("history", help="查看投票历史")

    args = parser.parse_args()

    if args.cmd == "vote":
        models = [m.strip() for m in args.models.split(",") if m.strip()]
        if len(models) < 2:
            print("Need at least 2 models for voting", file=sys.stderr)
            sys.exit(1)
        
        result = vote(
            task=args.task,
            models=models,
            strategy=args.strategy,
            workdir=args.workdir,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.cmd == "history":
        if not os.path.exists(LOG_FILE):
            print("No vote history yet.")
            return
        with open(LOG_FILE) as f:
            entries = f.readlines()
        print(f"Vote history ({len(entries)} entries):")
        for line in entries[-20:]:
            try:
                d = json.loads(line)
                print(f"  {d['ts']} task={d['task'][:50]} models={d['models']} strategy={d['strategy']}")
            except (json.JSONDecodeError, ValueError, KeyError):
                pass

    else:
        parser.print_help()


if __name__ == "__main__":
    cli()
