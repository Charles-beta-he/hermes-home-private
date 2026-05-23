#!/usr/bin/env python3
"""Generate a fast-track matrix for UVISA admin Lark tasks.

Read-only helper. It does not call Lark itself; pass a JSON snapshot from
lark_task_reader.py. Output is a GUID-indexed matrix used to batch S0/S1 admin
UI work without weakening closeout gates.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ADMIN_RE = re.compile(r"admin|管理后台|后台", re.I)
SECURITY_RE = re.compile(r"PII|revealPii|明文|脱敏眼睛|5 admin 角色|可读 ID 明文|审计日志|敏感字段|身份证|银行卡", re.I)
BACKEND_RE = re.compile(r"后端|接口|API|真实接口|真实数据|接通|打通|webhook|银行回调|流水|GSalary|C端|用户端|backend|计算|汇率|钱包账本|OCR|IP所在地|插件|第三方", re.I)
BLOCKED_RE = re.compile(r"AI无法|ai无法|人工介入|不关闭|OTP|登录|真实数据不存在|无法获取原型|原型图缺失", re.I)
FAST_RE = re.compile(r"文案|修改为|左对齐|对齐|下拉框|筛选框|字段|标题|删除|多余|换行|不超出|样式|显示了key|key|placeholder|按钮|色值|字体|1:1复刻|位置|格式|布局|排版", re.I)
PAGE_RULES = [
    ("advisor", re.compile(r"理财师管理|理财师钱包|业绩统计")),
    ("card-activation", re.compile(r"激活台|扫描新卡|重新分配并激活|冻结|异常待处理")),
    ("wallet-accounting", re.compile(r"钱包与账务|币种管理|换汇记录|聚合交易记录|导出csv|FX币对|钱包账本")),
    ("channel-payout", re.compile(r"通道代付记录|通道储备金|GSalary|实际汇出|通道状态")),
    ("risk-limits", re.compile(r"风控阈值|免审|判免审算法")),
    ("dashboard-kyc", re.compile(r"工作台|待复核 KYC|KYC cases|七个模块|平台 AUM|今日入金|今日出金")),
    ("debit-inflow", re.compile(r"Debit 入金|已驳回")),
    ("hsbc-inflow", re.compile(r"Dena 公户入金|公户|录入新到账|HSBC")),
    ("user-detail", re.compile(r"用户列表|用户详情|UID|卡片|卡交易|钱包流水|钱包列表|基本信息|KYC.*理财师|联系客户")),
    ("cards", re.compile(r"卡列表|Card ID|卡号|调整限额|实体卡|3DS")),
    ("wealth", re.compile(r"理财产品配置|持仓|财富持仓|APY|理财")),
]


def text_of(task: dict[str, Any]) -> str:
    return "\n".join(str(task.get(k) or "") for k in ("summary", "title", "description", "comments", "docs_content"))


def title_of(task: dict[str, Any]) -> str:
    # issue_title is the actual Lark task title. summary/description may contain
    # previous writeback bodies and would poison page/tier classification.
    return str(task.get("issue_title") or task.get("summary") or task.get("title") or "").strip()


def guid_of(task: dict[str, Any]) -> str:
    return str(task.get("guid") or task.get("lark_task_guid") or "").strip()


def page_of(text: str) -> str:
    for name, pat in PAGE_RULES:
        if pat.search(text):
            return name
    return "admin-misc"


def evidence_status(blob: str) -> str:
    if "完成回写" in blob:
        return "completed_writeback_but_live"
    if re.search(r"PR #|commit|npm run build|ship|修法|自动处理|已完成|✅", blob, re.I):
        return "implementation_evidence_but_live"
    return "no_local_evidence"


def classify(title: str, blob: str) -> tuple[str, str, list[str]]:
    reasons: list[str] = []
    # Tier from the task's own requirement, not previous comments/writebacks.
    combined = title
    evidence_blob = f"{title}\n{blob}"
    if title.startswith("🔴") or SECURITY_RE.search(combined):
        reasons.append("security_or_sensitive_or_permission")
        return "R", "security_review_required", reasons
    if "不关闭" in combined or "人工介入" in combined or re.search(r"AI无法|ai无法", combined):
        reasons.append("task_explicitly_says_do_not_close_or_manual")
        return "B", "blocked_manual_owner_required", reasons
    if BLOCKED_RE.search(combined) and not re.search(r"已完成|完成回写|PR #|commit|ship", evidence_blob, re.I):
        reasons.append("missing_external_access_or_manual_owner")
        return "B", "blocked_missing_prototype_or_access", reasons
    if BACKEND_RE.search(combined):
        reasons.append("backend_api_cross_terminal_or_real_data")
        return "L", "requires_backend_or_contract", reasons
    if FAST_RE.search(combined):
        reasons.append("ui_copy_alignment_field_fast_track")
        # Long titles often hide multiple atoms; still fast-track if purely UI-ish.
        if len(title) > 180 or title.count("，") + title.count("。") > 4:
            reasons.append("compound_page_ui")
            return "S1", "triaged_page_batch", reasons
        return "S0", "triaged_fast_track", reasons
    reasons.append("admin_page_unknown_requires_triage")
    return "M", "triaged_page_batch", reasons


def atoms_for(title: str, tier: str) -> list[str]:
    atoms: list[str] = []
    phrases = re.split(r"[。；;]\s*", title)
    for p in phrases:
        p = p.strip()
        if not p:
            continue
        # Keep atoms short but concrete.
        if len(p) > 180:
            parts = re.split(r"，|,", p)
            atoms.extend(x.strip() for x in parts if x.strip())
        else:
            atoms.append(p)
    if not atoms:
        atoms = [title[:160] or "inspect task details"]
    if tier in {"L", "R", "B"}:
        atoms.append(f"升级门检查: {tier} 类任务不得按 UI 快修直接关闭")
    return atoms[:12]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="JSON snapshot from lark_task_reader.py")
    ap.add_argument("--out-dir", default="/Users/charles/.hermes/state/uvisa-admin-lark-fasttrack")
    ap.add_argument("--include-non-admin", action="store_true")
    args = ap.parse_args()

    data = json.loads(Path(args.input).read_text())
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, Any]] = []
    for task in data:
        title = title_of(task)
        blob = text_of(task)
        if not args.include_non_admin and not ADMIN_RE.search(title):
            continue
        tier, status, reasons = classify(title, blob)
        page = page_of(title)
        guid = guid_of(task)
        atoms = atoms_for(title, tier)
        rows.append({
            "guid": guid,
            "suite_entity_num": task.get("suite_entity_num") or task.get("suite_entity") or "",
            "title": title,
            "page_batch": page,
            "tier": tier,
            "fasttrack_status": status,
            "evidence_status": evidence_status(blob),
            "reasons": reasons,
            "acceptance_atoms": atoms,
            "local_status": "live_incomplete",
            "implementation_status": "not_started" if evidence_status(blob) == "no_local_evidence" else "evidence_exists_needs_verification",
            "online_ui_retest_status": "pending_user_dispatch",
            "lark_final_close_status": "not_closed",
            "shared_evidence_allowed": tier in {"S0", "S1", "M"},
            "escalation_required": tier in {"L", "R", "B"},
        })

    summary = {
        "schema": "uvisa_admin_lark_fasttrack_matrix_v1",
        "generated_at": generated_at,
        "source": str(Path(args.input).resolve()),
        "total_rows": len(rows),
        "tier_counts": dict(Counter(r["tier"] for r in rows)),
        "batch_counts": dict(Counter(r["page_batch"] for r in rows)),
        "evidence_counts": dict(Counter(r["evidence_status"] for r in rows)),
        "status_counts": dict(Counter(r["fasttrack_status"] for r in rows)),
        "rules": {
            "implementation_done_is_not_lark_closed": True,
            "final_lark_close_requires_online_ui_retest": True,
            "shared_evidence_requires_guid_atom_mapping": True,
        },
    }
    payload = {"summary": summary, "rows": rows}
    json_path = out_dir / "matrix.latest.json"
    md_path = out_dir / "matrix.latest.md"
    csv_path = out_dir / "matrix.latest.csv"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))

    with csv_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["guid", "tier", "page_batch", "fasttrack_status", "evidence_status", "title"])
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in ["guid", "tier", "page_batch", "fasttrack_status", "evidence_status", "title"]})

    by_batch: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_batch[r["page_batch"]].append(r)
    lines = [
        "# UVISA Admin Lark Fast-track Matrix",
        "",
        f"Generated: `{generated_at}`",
        f"Source: `{Path(args.input).resolve()}`",
        "",
        "## Summary",
        "",
        f"- rows: {len(rows)}",
        f"- tiers: {summary['tier_counts']}",
        f"- batches: {summary['batch_counts']}",
        f"- evidence: {summary['evidence_counts']}",
        "",
        "## Batch Plan",
        "",
    ]
    tier_order = {"S0": 0, "S1": 1, "M": 2, "L": 3, "R": 4, "B": 5}
    for batch, items in sorted(by_batch.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        lines.append(f"### {batch} ({len(items)})")
        for r in sorted(items, key=lambda x: (tier_order.get(x["tier"], 9), x["guid"])):
            lines.append(f"- `{r['tier']}` `{r['guid'][:8]}` {r['fasttrack_status']} / {r['evidence_status']} — {r['title'][:140]}")
            for atom in r["acceptance_atoms"][:4]:
                lines.append(f"  - atom: {atom[:160]}")
        lines.append("")
    md_path.write_text("\n".join(lines))
    print(json.dumps({"status": "OK", "summary": summary, "json": str(json_path), "md": str(md_path), "csv": str(csv_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
