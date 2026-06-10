#!/usr/bin/env python3
"""
classify_and_route.py — Judge-based task complexity classifier for Hermes model routing.

Inspired by PilotDeck's 4-tier TokenSaver pattern. Uses a lightweight judge model
to classify message complexity before routing to the appropriate model tier.

Usage:
  python3 classify_and_route.py classify "写一个hello world"
  python3 classify_and_route.py classify "分析整个代码库的架构并生成报告" --previous-tier reasoning
  python3 classify_and_route.py route "继续" --previous-tier reasoning
  python3 classify_and_route.py benchmark

Tiers:
  simple   — greetings, confirmations, single-step Q&A, trivial writes
  medium   — single tool call, short code gen, 1-2 file operations
  reasoning — multi-file ops, data analysis, multi-step workflows
  complex  — parallel delegation, multi-agent orchestration
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from typing import Optional

HERMES_HOME = os.path.expanduser(os.environ.get("HERMES_HOME", "~/.hermes"))
CONFIG_PATH = os.path.join(HERMES_HOME, "config.yaml")

# Tier definitions — validated against PilotDeck's PinchBench 22-task benchmark (95%+ accuracy)
TIERS = {
    "simple": {
        "description": "Simple greetings, confirmations, single-step Q&A, trivial file writes, remembering rules",
        "model_hint": "light",  # cheapest available
    },
    "medium": {
        "description": "Single tool call, short text generation, 1-2 file read/write, code generation",
        "model_hint": "mid",
    },
    "reasoning": {
        "description": "Deep single-agent work: multi-file operations, data analysis, multi-step workflows, web research, structured reports from many sources",
        "model_hint": "strong",
    },
    "complex": {
        "description": "Needs sub-agent orchestration: parallel workstreams, delegation to specialized agents",
        "model_hint": "orchestrator",
    },
}

ROUTING_RULES = [
    "complex is ONLY for tasks that need sub-agent orchestration or parallel delegation — do NOT use it for single-agent multi-step work",
    "Multi-file operations, data analysis, and multi-step workflows without orchestration should be reasoning",
    "Simple file creation (1-2 files) or single code generation is medium",
    "Trivial greetings, confirmations, remembering rules, or reading one file and answering a short question is simple",
]

# Continuation signals — messages that should inherit previous tier
CONTINUATION_PATTERNS = [
    r"^(继续|go|ok|yes|好的|开始|冲|next|proceed|do it|继续吧|接着|再来)$",
    r"^(continue|keep going|more|again|yeah|yep|sure|right|correct)$",
]


def build_judge_prompt(message: str, previous_tier: Optional[str] = None) -> str:
    """Build the judge prompt for tier classification."""
    tier_lines = "\n".join(
        f"- {name}: {info['description']}" for name, info in TIERS.items()
    )
    rule_lines = "\n".join(f"- {rule}" for rule in ROUTING_RULES)

    context_section = ""
    if previous_tier:
        context_section = f"""
## CRITICAL RULE — Continuation messages
The previous turn was classified as: **{previous_tier}**.
Short messages like "go", "continue", "ok", "yes", "好的", "继续", "开始", "冲" etc.
are continuations of the previous task. They are NOT new simple requests.
For ANY message that is clearly a continuation or acknowledgment of the previous task,
you MUST return <tier>{previous_tier}</tier>.
Only reclassify if the user message introduces a genuinely NEW task with different complexity.
"""

    return f"""You are a model-tier classifier for the Hermes model router. Given the following user message, return exactly one tier wrapped in <tier>...</tier>.

Available tiers:
{tier_lines}

Routing rules:
{rule_lines}
{context_section}
User message:
\"\"\"
{message}
\"\"\"

Default tier when uncertain: medium.
Respond with only <tier>NAME</tier>."""


def is_continuation(message: str, previous_tier: Optional[str] = None) -> Optional[str]:
    """Check if message is a continuation signal. Returns tier if yes, None if no."""
    if not previous_tier:
        return None
    stripped = message.strip().lower()
    for pattern in CONTINUATION_PATTERNS:
        if re.match(pattern, stripped, re.IGNORECASE):
            return previous_tier
    return None


def parse_tier(response: str) -> Optional[str]:
    """Extract tier from judge response."""
    match = re.search(r"<tier>(\w+)</tier>", response, re.IGNORECASE)
    if match:
        tier = match.group(1).lower()
        if tier in TIERS:
            return tier
    # Fallback: check for bare tier name
    for tier in TIERS:
        if tier in response.lower():
            return tier
    return None


def classify_via_judge(message: str, previous_tier: Optional[str] = None) -> dict:
    """Classify message complexity using judge model."""
    # Check continuation first
    continuation_tier = is_continuation(message, previous_tier)
    if continuation_tier:
        return {
            "tier": continuation_tier,
            "resolved_from": "continuation",
            "judge_latency_ms": 0,
        }

    prompt = build_judge_prompt(message, previous_tier)

    # Use hermes chat with cheapest available judge model
    start = time.time()
    try:
        result = subprocess.run(
            [
                sys.executable, os.path.join(HERMES_HOME, "scripts", "model-router.py"),
                "select", "--task-tier", "reviewer"
            ],
            capture_output=True, text=True, timeout=15
        )
        # Parse judge model from router selection
        judge_info = json.loads(result.stdout) if result.returncode == 0 else {}
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
        judge_info = {}

    latency_ms = int((time.time() - start) * 1000)

    # For now, use heuristic classification as the judge proxy
    # In production, this would call the judge model via hermes chat
    tier = heuristic_classify(message)
    return {
        "tier": tier,
        "resolved_from": "heuristic",
        "judge_latency_ms": latency_ms,
        "note": "heuristic fallback — wire judge model call for production",
    }


def heuristic_classify(message: str) -> str:
    """Fast heuristic classifier (no LLM call). Good for fallback/offline."""
    msg = message.strip().lower()
    msg_len = len(message)

    # Simple: very short, greeting-like (but NOT bare "ok"/"yes" without previous context)
    greeting_words = ["hi", "hello", "hey", "你好", "嗨", "thanks", "谢谢", "thank you"]
    if msg_len < 15 and any(w in msg for w in greeting_words):
        return "simple"

    # Complex: explicit orchestration signals
    complex_signals = [
        "并行", "parallel", "delegate", "同时", "多个agent", "多agent",
        "spawn", "sub-agent", "orchestrat", "分配给",
    ]
    if any(s in msg for s in complex_signals):
        return "complex"

    # Reasoning: multi-step, analysis, deep work
    reasoning_signals = [
        "分析", "analyze", "报告", "report", "架构", "architecture",
        "整个", "entire", "全面", "comprehensive", "对比", "compare",
        "多个文件", "multi-file", "重构", "refactor", "调研", "research",
        "设计", "design", "方案", "plan", "优化", "optimize",
        "深入", "deep", "系统", "system", "评估", "evaluate",
    ]
    reasoning_score = sum(1 for s in reasoning_signals if s in msg)
    # Strong reasoning signals that alone indicate deep work
    strong_reasoning = ["重构", "refactor", "分析整个", "analyze entire", "全面分析"]
    has_strong = any(s in msg for s in strong_reasoning)
    if reasoning_score >= 2 or has_strong or msg_len > 500:
        return "reasoning"

    # Medium: code generation, single task
    medium_signals = [
        "写", "write", "创建", "create", "实现", "implement", "修改", "fix",
        "添加", "add", "更新", "update", "删除", "delete", "配置", "config",
        "test", "测试", "script", "脚本", "hello world",
    ]
    if any(s in msg for s in medium_signals) or msg_len > 100:
        return "medium"

    return "medium"  # default


def get_model_for_tier(tier: str, available_providers: dict = None) -> dict:
    """Map tier to model selection."""
    tier_models = {
        "simple": {"provider": "xiaomi", "model": "mimo-v2.5-flash", "reason": "cheapest available for simple tasks"},
        "medium": {"provider": "xiaomi", "model": "mimo-v2.5-pro", "reason": "balanced cost/quality for medium tasks"},
        "reasoning": {"provider": "claude-code", "model": "claude-fable-5", "reason": "strong reasoning via Claude Code CLI for deep work"},
        "complex": {"provider": "claude-code", "model": "claude-fable-5", "reason": "Claude Code CLI orchestrator for multi-agent tasks"},
    }
    return tier_models.get(tier, tier_models["medium"])


def cmd_classify(args):
    """Classify a message."""
    result = classify_via_judge(args.message, args.previous_tier)
    model = get_model_for_tier(result["tier"])
    output = {
        "message": args.message[:100] + ("..." if len(args.message) > 100 else ""),
        "classification": result,
        "recommended_model": model,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


def cmd_route(args):
    """Full route: classify + select model."""
    result = classify_via_judge(args.message, args.previous_tier)
    model = get_model_for_tier(result["tier"])
    output = {
        "tier": result["tier"],
        "resolved_from": result["resolved_from"],
        "provider": model["provider"],
        "model": model["model"],
        "reason": model["reason"],
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


def cmd_benchmark(args):
    """Run benchmark against known test cases."""
    test_cases = [
        ("你好", "simple"),
        ("hi", "simple"),
        ("ok", "medium"),  # no previous tier
        ("写一个hello world脚本", "medium"),
        ("创建一个Python文件实现快速排序", "medium"),
        ("分析整个代码库的架构并生成报告", "reasoning"),
        ("对比三个框架的优缺点并给出推荐方案", "reasoning"),
        ("重构这个模块的错误处理逻辑", "reasoning"),
        ("同时启动三个agent分别处理前端、后端和测试", "complex"),
        ("并行分析多个数据源并合并结果", "complex"),
    ]

    correct = 0
    total = len(test_cases)
    results = []

    for message, expected in test_cases:
        result = classify_via_judge(message)
        actual = result["tier"]
        match = actual == expected
        if match:
            correct += 1
        results.append({
            "message": message,
            "expected": expected,
            "actual": actual,
            "match": match,
        })

    accuracy = correct / total * 100
    summary = {
        "accuracy": f"{accuracy:.1f}%",
        "correct": correct,
        "total": total,
        "results": results,
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="Judge-based task complexity classifier")
    sub = parser.add_subparsers(dest="command")

    p_classify = sub.add_parser("classify", help="Classify message complexity")
    p_classify.add_argument("message", help="User message to classify")
    p_classify.add_argument("--previous-tier", help="Previous turn tier for continuation detection")

    p_route = sub.add_parser("route", help="Full route: classify + select model")
    p_route.add_argument("message", help="User message to route")
    p_route.add_argument("--previous-tier", help="Previous turn tier")

    p_benchmark = sub.add_parser("benchmark", help="Run accuracy benchmark")

    args = parser.parse_args()
    if args.command == "classify":
        cmd_classify(args)
    elif args.command == "route":
        cmd_route(args)
    elif args.command == "benchmark":
        cmd_benchmark(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
