#!/usr/bin/env python3
"""
cross-patch.py — 双模型交叉审查编排器 (L4 T2)
Producer A 执行任务 → Reviewer B 审查并生成结构化补丁 → Merger 自动化合并

工作流:
  A (producer) → 生成 artifact
  B (reviewer) → 审查, 输出结构化补丁列表
  Merger        → 按置信度阈值合并补丁 → 最终 artifact

模型配置:
  producer: gpt-5.4 (openai-codex) — 主生产力
  reviewer: deepseek-v4-pro — 互补审查 (不同训练语料)
  (未来: xiaomi 加入 T3 adversarial 第三验证者)

用法:
  python3 cross-patch.py execute --task "Fix auth bug in src/auth.py" --workdir /path/to/repo
  python3 cross-patch.py merge --base <base_output> --patches '<patch_json>'
  python3 cross-patch.py status
"""

import argparse
import json
import os
import subprocess
import sys        # for ProtocolError
import yaml
from datetime import datetime, timezone
from typing import List, Dict, Tuple, Optional

# L2 协议导入 (替代内联 dict)
sys.path.insert(0, os.path.dirname(__file__))
from agent_protocol import (
    wrap as protocol_wrap,
    try_wrap as protocol_try_wrap,
    extract as protocol_extract,
    extract_strict as protocol_extract_strict,
    emit as protocol_emit,
    ProtocolError,
)


HERMES_HOME = os.path.expanduser(os.environ.get("HERMES_HOME", "~/.hermes"))
LOG_FILE = os.path.join(HERMES_HOME, "logs", "cross-patch.jsonl")


def load_config():
    """加载 verification.cross_patch 配置"""
    try:
        import yaml
        config_path = os.path.join(HERMES_HOME, "config.yaml")
        with open(config_path) as f:
            c = yaml.safe_load(f)
        v = c.get("verification", {})
        cp = v.get("cross_patch", {})
        return {
            "enabled": cp.get("enabled", False),
            "min_patch_conf": cp.get("min_patch_conf", 0.7),
            "producer_model": cp.get("producer_model", "gpt-5.4"),
            "reviewer_model": cp.get("reviewer_model", "deepseek-v4-pro"),
            "max_patches": cp.get("max_patches", 20),
            "budget_per_task_usd": v.get("budgets", {}).get("per_task_usd", 2.0),
        }
    except (yaml.YAMLError, FileNotFoundError, KeyError, OSError) as e:
        print(f"[cross-patch] Config load failed: {e}", file=sys.stderr)
        return None


def build_producer_prompt(task: str, workdir: str = None) -> str:
    """构建 Producer 的系统提示词"""
    return f"""You are a code producer. Execute this task carefully and completely:

TASK: {task}

WORKING DIRECTORY: {workdir or 'current directory'}

Requirements:
- Produce a complete, working solution
- Include error handling
- Follow existing project conventions
- Output your final result as clean, production-ready code

After completing, output your result in this format:
```json
{{"verdict": "pass", "summary": "<what you did>", "artifacts": ["<file_paths_modified>"]}}
```
"""


def build_reviewer_prompt(task: str, producer_output: str) -> str:
    """构建 Reviewer 的系统提示词"""
    return f"""You are a code reviewer. Review the following output from another model.

TASK: {task}

PRODUCER OUTPUT:
{producer_output}

Do NOT rewrite the entire solution. Instead, emit a structured patch list.
For each issue you find, output:
```json
{{
  "verdict": "pass" or "fail",
  "patches": [
    {{
      "file": "<file_path>",
      "line_hint": "<approximate location>",
      "original": "<short snippet of original code>",
      "suggested": "<corrected code>",
      "rationale": "<why this change is needed>",
      "severity": "block" | "major" | "minor",
      "confidence": 0.0-1.0
    }}
  ],
  "summary": "<overall assessment>"
}}
```

Rules:
- Only flag REAL issues — not style preferences
- "block" severity = security, correctness, data loss
- "major" severity = bug, missing edge case, performance
- "minor" severity = readability, naming, comments
- confidence = how sure you are this is a real issue (0.0-1.0)
- If you find NO issues, set patches=[] and verdict="pass"
"""


def parse_reviewer_output(output: str) -> dict:
    """从 Reviewer 输出提取结构化补丁 — 使用 L2 agent_protocol.extract() (灵活模式)"""
    # 1. 优先用 agent_protocol.extract (灵活模式, 接受非完全协议格式)
    result = protocol_extract(output)
    if result and "verdict" in result:
        return result

    # 2. 如果连灵活提取都失败，返回 safe fallback
    return {"verdict": "unknown", "patches": [],
            "summary": f"Failed to parse reviewer output: {output[:200]}"}


def apply_patches(
    base_content: str,
    patches: List[dict],
    min_confidence: float = 0.7,
) -> Tuple[str, dict]:
    """
    确定性合并: 应用置信度 >= min_confidence 的补丁
    
    Returns:
      (merged_content, stats)
    """
    # 仅应用 >= min_confidence 的补丁
    accepted = [p for p in patches if p.get("confidence", 0) >= min_confidence]
    rejected = [p for p in patches if p.get("confidence", 0) < min_confidence]
    
    # 按 severity 排序: block > major > minor
    severity_order = {"block": 0, "major": 1, "minor": 2}
    accepted.sort(key=lambda p: severity_order.get(p.get("severity", "minor"), 2))
    
    merged = base_content
    applied_count = 0
    conflicts = []
    applied_patches = []
    
    for patch in accepted:
        original = patch.get("original", "")
        suggested = patch.get("suggested", "")
        
        if not original or not suggested:
            continue
        
        # 简单字符串替换 (MVP — v2 用 fuzzy match)
        if original in merged:
            merged = merged.replace(original, suggested, 1)
            applied_count += 1
            applied_patches.append({
                "file": patch.get("file", ""),
                "rationale": patch.get("rationale", ""),
                "severity": patch.get("severity", "minor"),
                "confidence": patch.get("confidence", 0),
            })
        else:
            conflicts.append({
                "file": patch.get("file", ""),
                "original_snippet": original[:80],
                "severity": patch.get("severity", "minor"),
            })
    
    stats = {
        "total_patches": len(patches),
        "accepted": len(accepted),
        "applied": applied_count,
        "conflicts": len(conflicts),
        "rejected_low_conf": len(rejected),
        "conflict_details": conflicts[:5],
        "applied_details": applied_patches,
    }
    
    return merged, stats


def execute_cross_patch(
    task: str,
    workdir: str = None,
    config: dict = None,
) -> dict:
    """
    执行 T2 CROSS-PATCH 流程
    
    实际 delegate_task 调用由 Hermes ACP 层完成。
    此处输出编排框架、提示词和预期调用模式。
    """
    if config is None:
        config = load_config()
    
    if config is None or not config.get("enabled"):
        return {
            "verdict": "skipped",
            "reason": "cross_patch disabled in config",
            "pattern": "cross_patch",
        }
    
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    result = {
        "pattern": "cross_patch",
        "ts": timestamp,
        "task": task[:200],
        "workdir": workdir,
        "producer_model": config["producer_model"],
        "reviewer_model": config["reviewer_model"],
    }
    
    # ── Step 1: Producer 调用模式 ──
    producer_prompt = build_producer_prompt(task, workdir)
    result["producer"] = {
        "model": config["producer_model"],
        "delegate_task_call": {
            "goal": task,
            "context": producer_prompt,
            "toolsets": ["terminal", "file", "web"],
            "acp_command": None,  # 由 Hermes 根据 model 自动选择
        },
    }
    
    # ── Step 2: Reviewer 调用模式 ──
    # 注: 实际场景中 reviewer 接收 producer 的 stdout
    reviewer_prompt = build_reviewer_prompt(
        task,
        "<producer_output — injected from delegate_task result>"
    )
    result["reviewer"] = {
        "model": config["reviewer_model"],
        "delegate_task_call": {
            "goal": f"Review this output for task: {task[:100]}",
            "context": reviewer_prompt,
            "toolsets": ["terminal", "file"],
            "acp_command": None,
        },
    }
    
    # ── Step 3: 补丁提取与合并 ──
    result["merge"] = {
        "min_patch_confidence": config["min_patch_conf"],
        "max_patches": config.get("max_patches", 20),
        "strategy": "deterministic_replace",
        "note": "Apply patches where confidence >= min_patch_conf AND original string exact match in base content",
    }
    
    # ── 输出协议消息 (L2 agent_protocol v2.0.0) ──
    try:
        protocol_msg = protocol_wrap(
            agent_id="cross-patch-orchestrator",
            task_id=task_id,
            verdict="pending",  # valid in v2.0.0
            verification_pattern="cross_patch",
            extensions={
                "roles": {
                    "producer": config["producer_model"],
                    "reviewer": config["reviewer_model"],
                }
            },
        )
        result["agent_protocol"] = protocol_msg
        # 持久化到 protocol_messages
        protocol_emit(protocol_msg)
    except ProtocolError as e:
        print(f"[cross-patch] Protocol wrap failed: {e}", file=sys.stderr)
    
    # ── 成本估算 ──
    result["cost_estimate"] = {
        "producer_est_usd": 0.05,
        "reviewer_est_usd": 0.03,
        "total_est_usd": 0.08,
        "budget_per_task_usd": config.get("budget_per_task_usd", 2.0),
        "within_budget": True,
    }
    
    # 记录日志
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        log_entry = {k: v for k, v in result.items() if k != "producer"}
        log_entry["producer_model"] = config["producer_model"]
        log_entry["reviewer_model"] = config["reviewer_model"]
        f.write(json.dumps(log_entry) + "\n")
    
    return result


def cli():
    parser = argparse.ArgumentParser(description="Cross-Patch — 双模型交叉审查编排器")
    sub = parser.add_subparsers(dest="cmd")

    ex = sub.add_parser("execute", help="执行 T2 cross-patch 流程")
    ex.add_argument("--task", required=True, help="任务描述")
    ex.add_argument("--workdir", default=None, help="工作目录")

    mg = sub.add_parser("merge", help="合并补丁")
    mg.add_argument("--base", required=True, help="基础内容 (或 @filepath)")
    mg.add_argument("--patches", required=True, help="补丁 JSON (或 @filepath)")
    mg.add_argument("--min-confidence", type=float, default=0.7)

    sub.add_parser("status", help="查看配置和最近执行")

    args = parser.parse_args()

    if args.cmd == "execute":
        result = execute_cross_patch(task=args.task, workdir=args.workdir)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.cmd == "merge":
        base = args.base
        if base.startswith("@"):
            with open(base[1:]) as f:
                base = f.read()
        
        patches_str = args.patches
        if patches_str.startswith("@"):
            with open(patches_str[1:]) as f:
                patches_str = f.read()
        
        try:
            review = json.loads(patches_str)
        except json.JSONDecodeError:
            review = parse_reviewer_output(patches_str)
        
        patches = review.get("patches", [])
        merged, stats = apply_patches(base, patches, args.min_confidence)
        
        print(json.dumps({
            "verdict": "pass" if stats["conflicts"] == 0 else "partial",
            "stats": stats,
            "merged_length": len(merged),
            "merged_preview": merged[:500],
        }, indent=2, ensure_ascii=False))

    elif args.cmd == "status":
        config = load_config()
        if config:
            print(f"Cross-Patch Status:")
            print(f"  enabled:       {config['enabled']}")
            print(f"  producer:      {config['producer_model']}")
            print(f"  reviewer:      {config['reviewer_model']}")
            print(f"  min_patch_conf: {config['min_patch_conf']}")
            print(f"  budget/task:   ${config['budget_per_task_usd']}")
        else:
            print("Config not found or parse error.")
        
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE) as f:
                lines = f.readlines()
            print(f"\n  Recent executions: {len(lines)}")
            for line in lines[-5:]:
                try:
                    d = json.loads(line)
                    print(f"    {d.get('ts','?')} task={d.get('task','?')[:50]}")
                except (json.JSONDecodeError, ValueError, KeyError):
                    pass

    else:
        parser.print_help()


if __name__ == "__main__":
    cli()
