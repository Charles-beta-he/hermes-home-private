#!/usr/bin/env python3
"""C端 Lark 任务冰山分析分类器。

不使用正则匹配做分类。而是对任务全文（标题 + 描述 + 评论 + 关联文档）做语义分析：
1. 表层：用户报告了什么症状
2. 中层：实际需要什么 scope 的改动
3. 深层：依赖什么外部条件

输出：tier + scope + domain + iceberg_signals + confidence
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ── 冰山信号提取器 ──────────────────────────────────────────────────────
# 每个信号提取器分析任务文本的一个维度，返回 (signal_name, evidence, weight)

def _text(task: dict[str, Any]) -> str:
    """聚合任务所有可用文本。"""
    parts = []
    for key in ("issue_title", "summary", "title", "description", "comments", "docs_content"):
        v = str(task.get(key) or "").strip()
        if v:
            parts.append(v)
    return "\n".join(parts)


def _has_images(task: dict[str, Any]) -> bool:
    imgs = task.get("comment_images") or []
    return any(img.get("status") in {"downloaded", "cached"} for img in imgs)


def _title(task: dict[str, Any]) -> str:
    return str(task.get("issue_title") or task.get("summary") or task.get("title") or "").strip()


def _split_phrases(text: str) -> list[str]:
    """按中文标点分句，保留有意义的短语。"""
    parts = re.split(r"[，。；,;！？!?]", text)
    return [p.strip() for p in parts if p.strip() and len(p.strip()) > 2]


def _analyze_money_semantics(phrases: list[str]) -> list[tuple[str, str, int]]:
    """分析涉及金额/币种的语义 — 这是最强的 scope 信号。"""
    signals = []
    for p in phrases:
        # 具体金额 + 币种：说明有真实的资金流转逻辑
        if re.search(r"\d+.*?(?:港币|美元|人民币|CNY|HKD|USD|USDT|EUR)", p):
            signals.append(("money_amount_with_currency", p, 3))
        # 到账 vs 发送 金额不一致：涉及后端计算/汇率
        elif "到账" in p and ("不符" in p or "不一致" in p or "错误" in p):
            signals.append(("amount_mismatch", p, 4))
        # 余额/可用余额/充值/提现：涉及钱包后端
        elif any(kw in p for kw in ["可用余额", "余额不足", "最多可充值", "提现到钱包"]):
            signals.append(("wallet_balance_logic", p, 3))
        # 汇率/FX：涉及后端汇率服务
        elif any(kw in p for kw in ["汇率", "兑换", "参考汇率", "报价"]):
            signals.append(("fx_rate_logic", p, 3))
        # 转账/汇款/转入/转出：涉及资金流转
        elif any(kw in p for kw in ["跨境汇款", "境内转账", "国际银行电汇", "SWIFT"]):
            signals.append(("remittance_flow", p, 3))
    return signals


def _analyze_ui_semantics(phrases: list[str]) -> list[tuple[str, str, int]]:
    """分析纯 UI 层面的语义。"""
    signals = []
    for p in phrases:
        # 纯视觉对齐：文案、样式、布局、色值、字体
        if any(kw in p for kw in ["1:1复刻", "1:1 复刻", "文案", "色值", "字体", "对齐", "排版"]):
            signals.append(("visual_parity", p, 1))
        # 空态/加载态/骨架屏
        elif any(kw in p for kw in ["骨架屏", "空状态", "加载中", "loading"]):
            signals.append(("loading_empty_state", p, 1))
        # 弹窗/横幅 UI 样式
        elif "弹框" in p and ("UI" in p or "样式" in p or "请按照" in p):
            signals.append(("modal_ui_style", p, 1))
        # 布局问题（显示一半、截断、溢出）
        elif any(kw in p for kw in ["显示一半", "截断", "溢出", "撑满", "蓝色方块"]):
            signals.append(("layout_overflow", p, 1))
    return signals


def _analyze_state_semantics(phrases: list[str]) -> list[tuple[str, str, int]]:
    """分析状态/数据正确性语义。"""
    signals = []
    for p in phrases:
        # 处理中/已完成等状态显示
        if any(kw in p for kw in ["处理中", "已完成", "进行中", "状态"]):
            if any(kw in p for kw in ["显示", "展示", "应该"]):
                signals.append(("state_display_logic", p, 2))
        # 数据适配/格式化（金额格式、币种显示）
        elif any(kw in p for kw in ["适配", "格式", "格式化", "千分位", "小数"]):
            signals.append(("data_formatting", p, 2))
        # 交易记录/列表展示
        elif any(kw in p for kw in ["交易记录", "交易列表", "最近交易", "订单号"]):
            signals.append(("transaction_display", p, 2))
    return signals


def _analyze_navigation_semantics(phrases: list[str]) -> list[tuple[str, str, int]]:
    """分析导航/路由语义。"""
    signals = []
    for p in phrases:
        if any(kw in p for kw in ["跳转", "路由", "导航", "返回", "进入", "链路"]):
            signals.append(("navigation_routing", p, 2))
    return signals


def _analyze_backend_signals(phrases: list[str]) -> list[tuple[str, str, int]]:
    """分析需要后端改动的深层信号。"""
    signals = []
    for p in phrases:
        # websocket/实时通信
        if any(kw in p for kw in ["websocket", "WebSocket", "实时", "站内信"]):
            signals.append(("websocket_realtime", p, 3))
        # 接口数据与显示不一致
        elif any(kw in p for kw in ["接口", "接口处理", "加密处理", "真实数据"]):
            signals.append(("api_data_issue", p, 3))
        # admin 后台配置 → C端联动
        elif "admin" in p.lower() and any(kw in p for kw in ["配置", "开关", "入口"]):
            signals.append(("admin_config_dependency", p, 2))
        # PWA/安装弹窗
        elif any(kw in p for kw in ["PWA", "安装弹窗", "二维码"]):
            signals.append(("pwa_installation", p, 2))
        # 邮箱验证码/OTP
        elif any(kw in p for kw in ["验证码", "OTP", "邮箱验证", "安全验证"]):
            signals.append(("otp_verification", p, 2))
        # 骨架屏/首屏渲染
        elif any(kw in p for kw in ["骨架屏", "首屏", "启动图", "渲染"]):
            signals.append(("initial_render", p, 2))
    return signals


def _analyze_human_requirement(text: str) -> list[tuple[str, str, int]]:
    """分析是否需要人工介入。"""
    signals = []
    if any(kw in text for kw in ["AI无法", "ai无法", "人工介入", "不关闭", "请让ai忽略"]):
        signals.append(("explicit_human_required", text[:100], 5))
    if any(kw in text for kw in ["无法获取原型", "原型图缺失", "原型缺失"]):
        signals.append(("missing_prototype", text[:100], 4))
    return signals


# ── 冰山分析主函数 ──────────────────────────────────────────────────────

def iceberg_analyze(task: dict[str, Any]) -> dict[str, Any]:
    """对单个 C端 Lark 任务做冰山分析。"""
    full_text = _text(task)
    title = _title(task)
    phrases = _split_phrases(title)
    has_imgs = _has_images(task)

    # 收集所有信号
    all_signals: list[tuple[str, str, int]] = []
    all_signals.extend(_analyze_money_semantics(phrases))
    all_signals.extend(_analyze_ui_semantics(phrases))
    all_signals.extend(_analyze_state_semantics(phrases))
    all_signals.extend(_analyze_navigation_semantics(phrases))
    all_signals.extend(_analyze_backend_signals(phrases))
    all_signals.extend(_analyze_human_requirement(full_text))

    # 按 scope 分桶
    ui_weight = 0
    fe_logic_weight = 0
    backend_weight = 0
    human_weight = 0

    signal_details = []
    for name, evidence, weight in all_signals:
        signal_details.append({
            "signal": name,
            "evidence": evidence[:120],
            "weight": weight,
        })
        # 归类到 scope
        if name in ("visual_parity", "loading_empty_state", "modal_ui_style", "layout_overflow"):
            ui_weight += weight
        elif name in ("explicit_human_required", "missing_prototype"):
            human_weight += weight
        elif name in ("api_data_issue", "websocket_realtime", "amount_mismatch",
                       "wallet_balance_logic", "fx_rate_logic", "remittance_flow",
                       "admin_config_dependency", "otp_verification", "pwa_installation"):
            backend_weight += weight
        else:
            fe_logic_weight += weight

    # 图片存在 → 视觉对比需求 +1
    if has_imgs:
        ui_weight += 1
        signal_details.append({"signal": "has_screenshot_evidence", "evidence": "comment images present", "weight": 1})

    # 决策树（不用 if-else 正则，用权重比较）
    if human_weight >= 4:
        tier = "B"
        scope = "human_required"
        confidence = "high"
    elif backend_weight > 0 and backend_weight >= fe_logic_weight and backend_weight >= ui_weight:
        tier = "L"
        scope = "requires_backend"
        confidence = "high" if backend_weight >= 3 else "medium"
    elif fe_logic_weight > 0 and fe_logic_weight >= ui_weight:
        tier = "F"
        scope = "frontend_logic"
        confidence = "medium"
    elif ui_weight > 0:
        # 区分 S0（简单）和 S1（复合）
        compound_signals = sum(1 for name, _, _ in all_signals if name not in ("has_screenshot_evidence",))
        if compound_signals >= 3 or len(phrases) >= 8:
            tier = "S1"
            scope = "compound_ui"
        else:
            tier = "S0"
            scope = "simple_ui"
        confidence = "medium" if compound_signals <= 2 else "high"
    else:
        # 无信号 → 用标题短语的通用 UI/前端语义兜底
        general_fe = sum(1 for p in phrases if any(kw in p for kw in [
            "显示", "页面", "弹窗", "按钮", "列表", "状态", "文案", "样式", "布局",
            "格式", "适配", "写死", "未区分", "未显示", "缺少", "多余", "错误展示",
            "应该", "需要", "不一致", "不符合", "design token",
        ]))
        if general_fe >= 2:
            tier = "F"
            scope = "frontend_logic_inferred"
            confidence = "low"
        elif general_fe == 1:
            tier = "F"
            scope = "frontend_logic_inferred"
            confidence = "low"
        else:
            tier = "M"
            scope = "needs_triage"
            confidence = "low"

    # 域推断（从标题语义推断，不用正则）
    domain = _infer_domain(title, phrases)

    return {
        "tier": tier,
        "scope": scope,
        "domain": domain,
        "confidence": confidence,
        "iceberg": {
            "surface": title[:120],
            "ui_weight": ui_weight,
            "fe_logic_weight": fe_logic_weight,
            "backend_weight": backend_weight,
            "human_weight": human_weight,
            "phrase_count": len(phrases),
            "has_images": has_imgs,
        },
        "signals": signal_details,
    }


def _infer_domain(title: str, phrases: list[str]) -> str:
    """从任务语义推断功能域。"""
    # 用语义聚类而非关键词匹配
    domain_signals: dict[str, int] = Counter()

    for p in phrases:
        # 资产域：钱包、余额、转入转出、交易记录
        if any(kw in p for kw in ["资产", "钱包", "余额", "转入", "转出", "交易", "加密钱包", "法币钱包"]):
            domain_signals["asset"] += 1
        # 兑换域：汇率、币种、兑换
        if any(kw in p for kw in ["兑换", "汇率", "币种选择", "收到币种", "支付币种"]):
            domain_signals["exchange"] += 1
        # 汇款域：跨境、收款人、SWIFT
        if any(kw in p for kw in ["汇款", "收款人", "跨境", "SWIFT", "电汇"]):
            domain_signals["remit"] += 1
        # 充值域：充值、U-VISA
        if any(kw in p for kw in ["充值", "U-VISA", "活期宝", "定期理财"]):
            domain_signals["topup"] += 1
        # 通知域：通知、消息、站内信
        if any(kw in p for kw in ["通知", "消息", "站内信", "横幅"]):
            domain_signals["notification"] += 1
        # 财富域：理财、持仓、收益、赎回
        if any(kw in p for kw in ["财富", "理财", "持仓", "收益", "赎回", "APY"]):
            domain_signals["wealth"] += 1
        # 认证域：登录、验证、注册
        if any(kw in p for kw in ["登录", "注册", "验证", "安全中心", "设备管理"]):
            domain_signals["auth"] += 1

    if not domain_signals:
        return "unknown"
    return domain_signals.most_common(1)[0][0]


# ── 批量处理 ──────────────────────────────────────────────────────────

def classify_all(tasks: list[dict[str, Any]], scope: str | None = None) -> dict[str, Any]:
    """批量冰山分析。scope 可过滤只处理 C端 或 admin。"""
    results = []
    for task in tasks:
        title = _title(task)
        # 可选过滤
        if scope == "c端" and "用户端" not in title:
            continue
        if scope == "admin" and "用户端" in title:
            continue

        analysis = iceberg_analyze(task)
        analysis["guid"] = str(task.get("lark_task_guid") or task.get("guid") or "")
        analysis["title"] = title
        results.append(analysis)

    # 统计
    tier_counts = Counter(r["tier"] for r in results)
    scope_counts = Counter(r["scope"] for r in results)
    domain_counts = Counter(r["domain"] for r in results)

    return {
        "schema": "uvisa_c端_lark_iceberg_classifier_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(results),
        "tier_counts": dict(tier_counts),
        "scope_counts": dict(scope_counts),
        "domain_counts": dict(domain_counts),
        "rows": results,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="C端 Lark 任务冰山分析分类器")
    ap.add_argument("--input", required=True, help="JSON snapshot from lark_task_reader.py")
    ap.add_argument("--out-dir", default="/tmp/uvisa_c端_iceberg")
    ap.add_argument("--scope", choices=["c端", "admin", "all"], default="c端")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    data = json.loads(Path(args.input).read_text())
    result = classify_all(data, scope=args.scope)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "iceberg.latest.json"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"=== C端冰山分析结果 ===")
        print(f"总数: {result['total']}")
        print(f"分层: {result['tier_counts']}")
        print(f"scope: {result['scope_counts']}")
        print(f"域: {result['domain_counts']}")
        print()
        tier_order = {"S0": 0, "S1": 1, "F": 2, "M": 3, "L": 4, "B": 5}
        for r in sorted(result["rows"], key=lambda x: (tier_order.get(x["tier"], 9), x["domain"])):
            print(f'{r["tier"]:>3} | {r["scope"]:<20} | {r["domain"]:<12} | {r["confidence"]:<6} | {r["title"][:65]}')
            for s in r["signals"]:
                print(f'      signal: {s["signal"]} (w={s["weight"]}) → {s["evidence"][:60]}')

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
