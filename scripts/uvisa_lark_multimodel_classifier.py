#!/usr/bin/env python3
"""UVISA Lark 多模型冰山分类共识。

不使用正则硬匹配。对确定性分类器输出的低置信度/待分诊任务，
调用真实外部模型做语义分析，多数投票得出最终分类。

流程：
1. 统一冰山分类器做第一轮确定性分析
2. 筛选 confidence=low / tier=M / scope=inferred 的任务
3. 发送给 2-3 个外部模型，每个模型独立分析
4. 多数投票得出最终 tier + scope + domain
5. 写回任务池 frontmatter

用法：
  python3 uvisa_lark_multimodel_classifier.py --input live-tasks.json [--dry-run] [--max-tasks 10]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# 导入确定性分类器
sys.path.insert(0, str(Path(__file__).resolve().parent))
from uvisa_lark_unified_classifier import iceberg_analyze, classify_all, _title

CONSULT_SCRIPT = Path.home() / ".hermes" / "scripts" / "consult_models.py"
TASKS_DIR = Path.home() / "Documents" / "brain" / "05-实践与项目" / "tasks"

# 参与分类共识的模型（按 canonical IDs）
CLASSIFICATION_MODELS = [
    "gpt-5.5",           # 强语义理解
    "deepseek-v4-pro",   # 低成本，中文理解好
    "mimo-v2.5-pro",     # 低成本，快速
]

CLASSIFICATION_PROMPT = """你是一个 UVISA 项目任务分类专家。分析以下 Lark 任务，判断它的真实工作范围。

任务标题：{title}

请从以下维度分析：
1. 这个任务需要改动哪些层？（纯前端 UI / 前端业务逻辑 / 后端接口 / 全栈）
2. 涉及什么业务域？（资产/兑换/汇款/充值/通知/财富/认证/管理后台/其他）
3. 是否需要人工介入？（明确说 AI 无法处理 / 缺少原型 / 需要产品确认）

请严格按以下 JSON 格式回答，不要输出其他内容：
{{"tier": "S0|S1|F|L|R|B|M", "scope": "simple_ui|compound_ui|frontend_logic|requires_backend|security_review|human_required|needs_triage", "domain": "asset|exchange|remit|topup|notification|wealth|auth|advisor|cards|wallet-accounting|channel-payout|risk-limits|dashboard-kyc|debit-inflow|hsbc-inflow|user-detail|unknown", "reasoning": "一句话理由"}}"""


def _call_model(model: str, prompt: str, timeout: int = 60) -> str | None:
    """调用单个模型做分类。"""
    try:
        result = subprocess.run(
            ["python3", str(CONSULT_SCRIPT), "--model", model, "--prompt", prompt, "--json"],
            capture_output=True, text=True, timeout=timeout,
            env={**os.environ, "CONSULT_SILENT": "1"},
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get("response") or data.get("content") or ""
    except Exception:
        pass
    return None


def _parse_vote(raw: str) -> dict[str, str] | None:
    """从模型输出中提取分类投票。"""
    if not raw:
        return None
    # 尝试直接解析 JSON
    try:
        # 处理可能的 markdown 代码块
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        data = json.loads(text)
        if isinstance(data, dict) and "tier" in data:
            return {
                "tier": str(data.get("tier", "")).upper().strip(),
                "scope": str(data.get("scope", "")).strip(),
                "domain": str(data.get("domain", "")).strip(),
                "reasoning": str(data.get("reasoning", ""))[:200],
            }
    except (json.JSONDecodeError, KeyError):
        pass
    return None


def _majority_vote(votes: list[dict[str, str]]) -> dict[str, Any]:
    """多数投票聚合。"""
    if not votes:
        return {"tier": "M", "scope": "needs_triage", "domain": "unknown", "confidence": "no_votes", "votes": []}

    tier_votes = Counter(v["tier"] for v in votes)
    scope_votes = Counter(v["scope"] for v in votes)
    domain_votes = Counter(v["domain"] for v in votes)

    top_tier = tier_votes.most_common(1)[0]
    agreement = top_tier[1] / len(votes)

    return {
        "tier": top_tier[0],
        "scope": scope_votes.most_common(1)[0][0],
        "domain": domain_votes.most_common(1)[0][0],
        "confidence": "high" if agreement >= 0.67 else "medium" if agreement >= 0.5 else "low",
        "agreement": agreement,
        "vote_counts": {
            "tier": dict(tier_votes),
            "scope": dict(scope_votes),
            "domain": dict(domain_votes),
        },
        "votes": votes,
    }


def multimodel_classify(tasks: list[dict[str, Any]], *, dry_run: bool = False, max_tasks: int = 20) -> dict[str, Any]:
    """多模型分类共识主流程。"""

    # 第一轮：确定性分类
    deterministic = classify_all(tasks)
    by_guid = {r["guid"]: r for r in deterministic["rows"]}

    # 筛选需要多模型确认的任务
    needs_review = []
    for r in deterministic["rows"]:
        if r["confidence"] == "low":
            needs_review.append(r)
        elif r["tier"] == "M":
            needs_review.append(r)
        elif r["scope"] in ("frontend_logic_inferred", "needs_triage"):
            needs_review.append(r)
    needs_review = needs_review[:max_tasks]

    # 第二轮：多模型共识
    consensus_results = []
    for task_row in needs_review:
        title = task_row["title"]
        prompt = CLASSIFICATION_PROMPT.format(title=title[:300])

        votes = []
        for model in CLASSIFICATION_MODELS:
            if dry_run:
                votes.append({"tier": task_row["tier"], "scope": task_row["scope"], "domain": task_row["domain"], "reasoning": f"dry-run ({model})"})
                continue
            raw = _call_model(model, prompt)
            vote = _parse_vote(raw)
            if vote:
                votes.append(vote)

        consensus = _majority_vote(votes)
        consensus["guid"] = task_row["guid"]
        consensus["title"] = title
        consensus["deterministic_tier"] = task_row["tier"]
        consensus["deterministic_confidence"] = task_row["confidence"]
        consensus_results.append(consensus)

    # 合并结果
    final_rows = []
    consensus_map = {r["guid"]: r for r in consensus_results}
    for r in deterministic["rows"]:
        if r["guid"] in consensus_map:
            c = consensus_map[r["guid"]]
            r["tier"] = c["tier"]
            r["scope"] = c["scope"]
            r["domain"] = c["domain"]
            r["confidence"] = c["confidence"]
            r["multimodel_consensus"] = {
                "agreement": c.get("agreement"),
                "vote_counts": c.get("vote_counts"),
                "deterministic_tier": c["deterministic_tier"],
                "models_used": CLASSIFICATION_MODELS,
            }
        final_rows.append(r)

    tier_counts = Counter(r["tier"] for r in final_rows)

    return {
        "schema": "uvisa_lark_multimodel_classifier_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(final_rows),
        "reviewed_by_models": len(consensus_results),
        "tier_counts": dict(tier_counts),
        "rows": final_rows,
        "consensus_details": consensus_results,
    }


def write_back_to_tasks(result: dict[str, Any], *, dry_run: bool = False) -> list[str]:
    """将分类结果写回任务池 frontmatter。"""
    updated = []
    by_guid = {}
    for r in result["rows"]:
        if r.get("guid"):
            by_guid[r["guid"][:8]] = r

    for p in TASKS_DIR.glob("*.md"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        if not text.startswith("---\n"):
            continue
        end_idx = text.find("\n---\n", 4)
        if end_idx < 0:
            continue
        fm = text[4:end_idx]

        # 提取 Lark GUID
        import re
        guid_m = re.search(r'lark-([0-9a-f]{8})', p.name)
        if not guid_m:
            continue
        short_guid = guid_m.group(1)

        if short_guid not in by_guid:
            continue

        r = by_guid[short_guid]
        if "multimodel_consensus" not in r:
            continue  # 没有多模型共识，跳过

        # 更新 iceberg 字段
        for field in ("iceberg_tier", "iceberg_scope", "iceberg_domain", "iceberg_confidence"):
            old_val = re.search(rf'^{field}:.*$', fm, re.M)
            key = field.replace("iceberg_", "")
            new_val = r.get(key, "")
            if old_val:
                fm = fm[:old_val.start()] + f"{field}: {new_val}" + fm[old_val.end():]

        # 添加多模型共识字段
        consensus = r["multimodel_consensus"]
        consensus_line = f"iceberg_multimodel_consensus: agreement={consensus.get('agreement', 0):.0%}; deterministic={consensus.get('deterministic_tier', '?')}; models={','.join(consensus.get('models_used', []))}"
        if "iceberg_multimodel_consensus:" in fm:
            old = re.search(r'^iceberg_multimodel_consensus:.*$', fm, re.M)
            fm = fm[:old.start()] + consensus_line + fm[old.end():]
        else:
            anchor = re.search(r'^iceberg_confidence:.*$', fm, re.M)
            if anchor:
                fm = fm[:anchor.end()] + "\n" + consensus_line + fm[anchor.end():]

        if not dry_run:
            new_text = '---\n' + fm + '\n---\n' + text[end_idx+5:]
            p.write_text(new_text, encoding="utf-8")
        updated.append(f"{r['tier']} | {short_guid} | {r['title'][:60]}")

    return updated


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="UVISA Lark 多模型冰山分类共识")
    ap.add_argument("--input", required=True, help="JSON snapshot from lark_task_reader.py")
    ap.add_argument("--out-dir", default="/tmp/uvisa_multimodel_iceberg")
    ap.add_argument("--dry-run", action="store_true", help="不调用模型，不写回任务池")
    ap.add_argument("--max-tasks", type=int, default=20, help="最多送多少任务给多模型")
    ap.add_argument("--write-back", action="store_true", help="写回任务池 frontmatter")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    data = json.loads(Path(args.input).read_text())
    result = multimodel_classify(data, dry_run=args.dry_run, max_tasks=args.max_tasks)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "multimodel-iceberg.latest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))

    if args.write_back and not args.dry_run:
        updated = write_back_to_tasks(result)
        print(f"写回 {len(updated)} 个任务")
        for u in updated:
            print(f"  {u}")

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"=== 多模型冰山分类共识 ===")
        print(f"总数: {result['total']}")
        print(f"多模型审查: {result['reviewed_by_models']}")
        print(f"最终分层: {result['tier_counts']}")
        print()
        for c in result.get("consensus_details", []):
            det = c.get("deterministic_tier", "?")
            final = c.get("tier", "?")
            agree = c.get("agreement", 0)
            marker = "✓" if det == final else "Δ"
            print(f'  {marker} {det}→{final} | agree={agree:.0%} | {c["title"][:65]}')
            for v in c.get("votes", []):
                print(f'      vote: {v["tier"]} | {v["scope"]} | {v["reasoning"][:60]}')

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
