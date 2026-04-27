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
    execute: bool = True,
) -> dict:
    """
    执行多模型投票。

    execute=True (默认): 实际调用每个模型 (via hermes chat -q),
    收集 verdict，运行聚合策略。

    execute=False: 仅输出框架 (兼容旧行为，用于 delegate_task 场景)。
    """
    weights = get_model_weights(models)

    result = {
        "task": task,
        "models": models,
        "strategy": strategy,
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "model_weights": weights,
    }

    if not execute:
        # 兼容旧行为: 仅框架输出
        result["consensus"] = False
        result["note"] = (
            "Framework mode — set execute=True or use delegate_task "
            "for actual parallel model execution."
        )
        _log_and_emit(result, strategy, models, weights)
        return result

    # ── 实际执行: 顺序调用每个模型 ──
    results = []
    for model in models:
        model_result = _call_model(task, model, workdir)
        results.append(model_result)

    # ── 聚合 ──
    if strategy == "weighted":
        aggregated = weighted_vote(results, weights)
    elif strategy == "arbiter":
        # Arbiter: 所有结果喂给 claude-opus-4-7 做最终裁决
        aggregated = _arbiter_vote(results, task)
    else:
        aggregated = majority_vote(results)

    result["model_results"] = results
    result.update(aggregated)
    result["consensus"] = aggregated.get("consensus",
                                         aggregated.get("verdict", "unknown") != "unknown")

    _log_and_emit(result, strategy, models, weights)
    return result


def _call_model(task: str, model: str, workdir: str = None) -> dict:
    """
    通过 hermes chat -q 调用模型执行投票任务。

    返回 {"model": str, "verdict": str, "output": str|None}
    """
    import shutil
    hermes = shutil.which("hermes")
    if not hermes:
        return {"model": model, "verdict": "unknown",
                "output": None, "error": "hermes command not found"}

    prompt = (
        f"You are an expert code reviewer. Review this task and respond with your verdict.\n\n"
        f"TASK:\n{task}\n\n"
        f"Output ONLY a JSON object with:\n"
        f'{{"verdict": "pass"|"fail"|"partial", "summary": "<brief reason>"}}'
    )

    try:
        r = subprocess.run(
            [hermes, "chat", "-q", prompt, "--model", model],
            capture_output=True, text=True,
            timeout=120,
            cwd=workdir,
        )
        # 从输出提取 verdict
        try:
            data = json.loads(r.stdout)
            verdict = data.get("verdict", "unknown")
        except json.JSONDecodeError:
            # 尝试从输出文本中探测
            out_lower = r.stdout.lower()
            if "pass" in out_lower and "fail" not in out_lower:
                verdict = "pass"
            elif "fail" in out_lower:
                verdict = "fail"
            else:
                verdict = "unknown"

        return {
            "model": model,
            "verdict": verdict,
            "output": r.stdout[:500],
            "exit_code": r.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"model": model, "verdict": "timeout", "output": None}
    except (OSError, ValueError) as e:
        return {"model": model, "verdict": "unknown", "output": None, "error": str(e)}


def _arbiter_vote(results: List[dict], task: str) -> dict:
    """仲裁投票: 将结果喂给 Claude 做裁决"""
    summary = "\n".join(
        f"- {r['model']}: verdict={r['verdict']}"
        for r in results
    )
    prompt = (
        f"You are the final arbiter. Review these model verdicts and decide.\n\n"
        f"TASK: {task}\n\n"
        f"VOTES:\n{summary}\n\n"
        f"Output ONLY: {{\"verdict\": \"pass\"|\"fail\"|\"partial\", \"reason\": \"...\"}}"
    )

    # 使用 hermes chat -q --model claude-opus-4-7 或 claude
    import shutil
    hermes = shutil.which("hermes")
    if not hermes:
        return {"strategy": "arbiter", "verdict": "unknown", "reason": "hermes not found"}

    try:
        r = subprocess.run(
            [hermes, "chat", "-q", prompt, "--model", "claude-sonnet-4-6"],
            capture_output=True, text=True, timeout=120,
        )
        try:
            data = json.loads(r.stdout)
            return {"strategy": "arbiter", "verdict": data.get("verdict", "unknown"),
                    "arbiter_reason": data.get("reason", "")}
        except json.JSONDecodeError:
            return {"strategy": "arbiter", "verdict": "unknown", "raw": r.stdout[:200]}
    except (subprocess.TimeoutExpired, OSError) as e:
        return {"strategy": "arbiter", "verdict": "timeout", "error": str(e)}


def _log_and_emit(result: dict, strategy: str, models: List[str], weights: dict):
    """记录日志 + L2 协议 emit"""
    # 记录到日志
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        # 序列化安全副本
        log_entry = {k: v for k, v in result.items()
                     if k not in ("model_results",)}
        f.write(json.dumps(log_entry) + "\n")

    # ── L2 协议 emit ──
    try:
        consensus = result.get("consensus", False)
        protocol_msg = protocol_wrap(
            agent_id="ensemble-vote",
            task_id="vote-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S"),
            verdict="pass" if consensus else "partial",
            verification_pattern="ensemble_vote",
            extensions={
                "strategy": strategy,
                "models": models,
                "weights": weights,
                "metadata": result.get("weighted_scores", result.get("votes", {})),
            },
        )
        result["agent_protocol"] = protocol_msg
        protocol_emit(protocol_msg)
    except ProtocolError as e:
        print(f"[ensemble-vote] Protocol emit failed: {e}", file=sys.stderr)


def cli():
    parser = argparse.ArgumentParser(description="Ensemble Vote — 多模型投票")
    sub = parser.add_subparsers(dest="cmd")

    vt = sub.add_parser("vote", help="执行多模型投票")
    vt.add_argument("--task", required=True, help="任务描述")
    vt.add_argument("--models", required=True, help="逗号分隔的模型列表")
    vt.add_argument("--strategy", default="majority", 
                    choices=["majority", "weighted", "arbiter"])
    vt.add_argument("--execute", action="store_true", default=False,
                    help="Actually call models (default: framework-only)")
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
            execute=args.execute,
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
