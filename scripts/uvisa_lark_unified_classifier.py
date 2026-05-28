#!/usr/bin/env python3
"""UVISA Lark 统一冰山分类器。

admin + C端 共用同一套冰山分析引擎，不再用正则做分类决策。
admin 额外加载域信号提取器（安全审查、页面批次、跨端依赖）。

输出：tier + scope + domain + side + iceberg_signals + confidence
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ── 工具函数 ──────────────────────────────────────────────────────────

def _text(task: dict[str, Any]) -> str:
    return "\n".join(str(task.get(k) or "").strip() for k in
                     ("issue_title", "summary", "title", "description", "comments", "docs_content") if task.get(k))


def _title(task: dict[str, Any]) -> str:
    return str(task.get("issue_title") or task.get("summary") or task.get("title") or "").strip()


def _has_images(task: dict[str, Any]) -> bool:
    return any(img.get("status") in {"downloaded", "cached"} for img in (task.get("comment_images") or []))


def _split_phrases(text: str) -> list[str]:
    parts = re.split(r"[，。；,;！？!?]", text)
    return [p.strip() for p in parts if p.strip() and len(p.strip()) > 2]


def _detect_side(title: str) -> str:
    """检测任务归属端。"""
    if any(kw in title for kw in ["admin管理后台", "管理后台", "后台", "左侧菜单", "admin后台"]):
        return "admin"
    if any(kw in title for kw in ["用户端", "移动端", "APP端", "C端"]):
        return "c端"
    if any(kw in title for kw in ["U-VISA", "充值", "提现", "资产", "底部导航栏"]):
        return "c端"
    return "unknown"


# ── 通用冰山信号提取器（admin + C端 共用）──────────────────────────────

def _analyze_money_semantics(phrases: list[str]) -> list[tuple[str, str, int]]:
    signals = []
    for p in phrases:
        if re.search(r"\d+.*?(?:港币|美元|人民币|CNY|HKD|USD|USDT|EUR)", p):
            signals.append(("money_amount_with_currency", p, 3))
        elif "到账" in p and ("不符" in p or "不一致" in p or "错误" in p):
            signals.append(("amount_mismatch", p, 4))
        elif any(kw in p for kw in ["可用余额", "余额不足", "最多可充值", "提现到钱包"]):
            signals.append(("wallet_balance_logic", p, 3))
        elif any(kw in p for kw in ["汇率", "兑换", "参考汇率", "报价", "FX币对", "换汇"]):
            signals.append(("fx_rate_logic", p, 3))
        elif any(kw in p for kw in ["跨境汇款", "境内转账", "国际银行电汇", "SWIFT", "通道代付"]):
            signals.append(("remittance_flow", p, 3))
    return signals


def _analyze_ui_semantics(phrases: list[str]) -> list[tuple[str, str, int]]:
    signals = []
    for p in phrases:
        if any(kw in p for kw in ["1:1复刻", "1:1 复刻", "文案", "色值", "字体", "对齐", "排版", "样式", "布局"]):
            signals.append(("visual_parity", p, 1))
        elif any(kw in p for kw in ["骨架屏", "空状态", "加载中", "loading"]):
            signals.append(("loading_empty_state", p, 1))
        elif "弹框" in p and ("UI" in p or "样式" in p or "请按照" in p):
            signals.append(("modal_ui_style", p, 1))
        elif any(kw in p for kw in ["显示一半", "截断", "溢出", "撑满", "蓝色方块"]):
            signals.append(("layout_overflow", p, 1))
    return signals


def _analyze_state_semantics(phrases: list[str]) -> list[tuple[str, str, int]]:
    signals = []
    for p in phrases:
        if any(kw in p for kw in ["处理中", "已完成", "进行中", "状态"]):
            if any(kw in p for kw in ["显示", "展示", "应该"]):
                signals.append(("state_display_logic", p, 2))
        elif any(kw in p for kw in ["适配", "格式", "格式化", "千分位", "小数"]):
            signals.append(("data_formatting", p, 2))
        elif any(kw in p for kw in ["交易记录", "交易列表", "最近交易", "订单号"]):
            signals.append(("transaction_display", p, 2))
    return signals


def _analyze_navigation_semantics(phrases: list[str]) -> list[tuple[str, str, int]]:
    signals = []
    for p in phrases:
        if any(kw in p for kw in ["跳转", "路由", "导航", "返回", "进入", "链路"]):
            signals.append(("navigation_routing", p, 2))
    return signals


def _analyze_backend_signals(phrases: list[str]) -> list[tuple[str, str, int]]:
    signals = []
    for p in phrases:
        if any(kw in p for kw in ["websocket", "WebSocket", "实时", "站内信"]):
            signals.append(("websocket_realtime", p, 3))
        elif any(kw in p for kw in ["接口", "接口处理", "加密处理", "真实数据", "真实接口", "接通", "打通"]):
            signals.append(("api_data_issue", p, 3))
        elif "admin" in p.lower() and any(kw in p for kw in ["配置", "开关", "入口"]):
            signals.append(("admin_config_dependency", p, 2))
        elif any(kw in p for kw in ["PWA", "安装弹窗", "二维码"]):
            signals.append(("pwa_installation", p, 2))
        elif any(kw in p for kw in ["验证码", "OTP", "邮箱验证", "安全验证"]):
            signals.append(("otp_verification", p, 2))
        elif any(kw in p for kw in ["骨架屏", "首屏", "启动图", "渲染"]):
            signals.append(("initial_render", p, 2))
    return signals


def _analyze_human_requirement(text: str) -> list[tuple[str, str, int]]:
    signals = []
    if any(kw in text for kw in ["AI无法", "ai无法", "人工介入", "不关闭", "请让ai忽略"]):
        signals.append(("explicit_human_required", text[:100], 5))
    if any(kw in text for kw in ["无法获取原型", "原型图缺失", "原型缺失"]):
        signals.append(("missing_prototype", text[:100], 4))
    return signals


# ── admin 域专用信号提取器 ─────────────────────────────────────────────

def _analyze_admin_security(phrases: list[str]) -> list[tuple[str, str, int]]:
    """admin 安全审查信号。"""
    signals = []
    for p in phrases:
        if any(kw in p for kw in ["PII", "revealPii", "明文", "脱敏眼睛", "敏感字段", "身份证", "银行卡", "审计日志"]):
            signals.append(("admin_security_pii", p, 5))
        elif any(kw in p for kw in ["可读 ID 明文", "admin 角色", "权限"]):
            signals.append(("admin_permission", p, 4))
    return signals


def _analyze_admin_cross_terminal(phrases: list[str]) -> list[tuple[str, str, int]]:
    """admin 跨端依赖信号。"""
    signals = []
    for p in phrases:
        if any(kw in p for kw in ["C端", "用户端", "用户列表", "用户详情", "UID"]):
            signals.append(("admin_cross_terminal_user", p, 3))
        elif any(kw in p for kw in ["webhook", "银行回调", "GSalary", "通道状态"]):
            signals.append(("admin_webhook_dependency", p, 3))
        elif any(kw in p for kw in ["币种管理", "钱包账本", "钱包与账务"]):
            signals.append(("admin_wallet_config", p, 2))
        elif any(kw in p for kw in ["风控阈值", "免审", "判免审"]):
            signals.append(("admin_risk_config", p, 3))
        elif any(kw in p for kw in ["理财产品配置", "APY", "持仓", "理财"]):
            signals.append(("admin_wealth_config", p, 2))
    return signals


def _analyze_admin_page_batch(phrases: list[str]) -> list[tuple[str, str, int]]:
    """admin 页面批次信号（用于 S0/S1 区分）。"""
    signals = []
    for p in phrases:
        if any(kw in p for kw in ["理财师管理", "理财师钱包", "业绩统计"]):
            signals.append(("page_advisor", p, 1))
        elif any(kw in p for kw in ["激活台", "扫描新卡", "重新分配并激活", "冻结"]):
            signals.append(("page_card_activation", p, 1))
        elif any(kw in p for kw in ["换汇记录", "聚合交易记录", "导出csv"]):
            signals.append(("page_wallet_accounting", p, 1))
        elif any(kw in p for kw in ["工作台", "待复核 KYC", "KYC cases", "平台 AUM"]):
            signals.append(("page_dashboard_kyc", p, 1))
        elif any(kw in p for kw in ["Debit 入金", "已驳回", "技术终审"]):
            signals.append(("page_debit_inflow", p, 1))
        elif any(kw in p for kw in ["公户", "录入新到账", "HSBC", "Dena"]):
            signals.append(("page_hsbc_inflow", p, 1))
        elif any(kw in p for kw in ["卡列表", "Card ID", "卡号", "调整限额", "3DS"]):
            signals.append(("page_cards", p, 1))
    return signals


# ── 统一冰山分析 ──────────────────────────────────────────────────────

def iceberg_analyze(task: dict[str, Any]) -> dict[str, Any]:
    full_text = _text(task)
    title = _title(task)
    phrases = _split_phrases(title)
    has_imgs = _has_images(task)
    side = _detect_side(title)

    # 收集通用信号
    all_signals: list[tuple[str, str, int]] = []
    all_signals.extend(_analyze_money_semantics(phrases))
    all_signals.extend(_analyze_ui_semantics(phrases))
    all_signals.extend(_analyze_state_semantics(phrases))
    all_signals.extend(_analyze_navigation_semantics(phrases))
    all_signals.extend(_analyze_backend_signals(phrases))
    all_signals.extend(_analyze_human_requirement(full_text))

    # admin 额外信号
    if side == "admin":
        all_signals.extend(_analyze_admin_security(phrases))
        all_signals.extend(_analyze_admin_cross_terminal(phrases))
        all_signals.extend(_analyze_admin_page_batch(phrases))

    # 按 scope 分桶
    ui_weight = 0
    fe_logic_weight = 0
    backend_weight = 0
    human_weight = 0
    security_weight = 0

    signal_details = []
    for name, evidence, weight in all_signals:
        signal_details.append({"signal": name, "evidence": evidence[:120], "weight": weight})
        if name in ("admin_security_pii", "admin_permission"):
            security_weight += weight
        elif name in ("visual_parity", "loading_empty_state", "modal_ui_style", "layout_overflow"):
            ui_weight += weight
        elif name in ("explicit_human_required", "missing_prototype"):
            human_weight += weight
        elif name in ("api_data_issue", "websocket_realtime", "amount_mismatch",
                       "wallet_balance_logic", "fx_rate_logic", "remittance_flow",
                       "admin_config_dependency", "otp_verification", "pwa_installation",
                       "admin_webhook_dependency", "admin_risk_config", "admin_wallet_config",
                       "admin_cross_terminal_user", "admin_wealth_config"):
            backend_weight += weight
        else:
            fe_logic_weight += weight

    if has_imgs:
        ui_weight += 1
        signal_details.append({"signal": "has_screenshot_evidence", "evidence": "comment images present", "weight": 1})

    # 决策树
    if security_weight >= 4:
        tier, scope, confidence = "R", "security_review_required", "high"
    elif human_weight >= 4:
        tier, scope, confidence = "B", "human_required", "high"
    elif backend_weight > 0 and backend_weight >= fe_logic_weight and backend_weight >= ui_weight:
        tier = "L"
        scope = "requires_backend"
        confidence = "high" if backend_weight >= 3 else "medium"
    elif fe_logic_weight > 0 and fe_logic_weight >= ui_weight:
        tier = "F"
        scope = "frontend_logic"
        confidence = "medium"
    elif ui_weight > 0:
        compound = sum(1 for name, _, _ in all_signals if name not in ("has_screenshot_evidence",))
        if compound >= 3 or len(phrases) >= 8:
            tier, scope = "S1", "compound_ui"
        else:
            tier, scope = "S0", "simple_ui"
        confidence = "medium" if compound <= 2 else "high"
    else:
        general_fe = sum(1 for p in phrases if any(kw in p for kw in [
            "显示", "页面", "弹窗", "按钮", "列表", "状态", "文案", "样式", "布局",
            "格式", "适配", "写死", "未区分", "未显示", "缺少", "多余", "错误展示",
            "应该", "需要", "不一致", "不符合", "design token",
        ]))
        if general_fe >= 1:
            tier, scope, confidence = "F", "frontend_logic_inferred", "low"
        else:
            tier, scope, confidence = "M", "needs_triage", "low"

    domain = _infer_domain(title, phrases, side)

    return {
        "tier": tier,
        "scope": scope,
        "domain": domain,
        "side": side,
        "confidence": confidence,
        "iceberg": {
            "surface": title[:120],
            "ui_weight": ui_weight,
            "fe_logic_weight": fe_logic_weight,
            "backend_weight": backend_weight,
            "human_weight": human_weight,
            "security_weight": security_weight,
            "phrase_count": len(phrases),
            "has_images": has_imgs,
        },
        "signals": signal_details,
    }


def _infer_domain(title: str, phrases: list[str], side: str) -> str:
    domain_signals: dict[str, int] = Counter()
    for p in phrases:
        if side == "admin":
            if any(kw in p for kw in ["理财师", "业绩统计"]):
                domain_signals["advisor"] += 1
            if any(kw in p for kw in ["激活台", "扫描新卡", "卡列表", "Card ID", "3DS"]):
                domain_signals["cards"] += 1
            if any(kw in p for kw in ["钱包与账务", "币种管理", "换汇记录", "钱包账本"]):
                domain_signals["wallet-accounting"] += 1
            if any(kw in p for kw in ["通道代付", "GSalary", "通道储备金"]):
                domain_signals["channel-payout"] += 1
            if any(kw in p for kw in ["风控阈值", "免审"]):
                domain_signals["risk-limits"] += 1
            if any(kw in p for kw in ["工作台", "KYC", "平台 AUM"]):
                domain_signals["dashboard-kyc"] += 1
            if any(kw in p for kw in ["Debit 入金", "已驳回", "技术终审"]):
                domain_signals["debit-inflow"] += 1
            if any(kw in p for kw in ["公户", "HSBC", "Dena"]):
                domain_signals["hsbc-inflow"] += 1
            if any(kw in p for kw in ["用户列表", "用户详情", "UID"]):
                domain_signals["user-detail"] += 1
            if any(kw in p for kw in ["理财产品配置", "APY", "持仓"]):
                domain_signals["wealth"] += 1
        # C端 + admin 共用
        if any(kw in p for kw in ["资产", "钱包", "余额", "转入", "转出", "交易", "加密钱包", "法币钱包"]):
            domain_signals["asset"] += 1
        if any(kw in p for kw in ["兑换", "汇率", "币种选择", "收到币种", "支付币种"]):
            domain_signals["exchange"] += 1
        if any(kw in p for kw in ["汇款", "收款人", "跨境", "SWIFT", "电汇"]):
            domain_signals["remit"] += 1
        if any(kw in p for kw in ["充值", "U-VISA", "活期宝", "定期理财"]):
            domain_signals["topup"] += 1
        if any(kw in p for kw in ["通知", "消息", "站内信", "横幅"]):
            domain_signals["notification"] += 1
        if any(kw in p for kw in ["财富", "理财", "持仓", "收益", "赎回"]):
            domain_signals["wealth"] += 1
        if any(kw in p for kw in ["登录", "注册", "验证", "安全中心", "设备管理"]):
            domain_signals["auth"] += 1
    if not domain_signals:
        return "unknown"
    return domain_signals.most_common(1)[0][0]


# ── 批量处理 ──────────────────────────────────────────────────────────

def classify_all(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    results = []
    for task in tasks:
        analysis = iceberg_analyze(task)
        analysis["guid"] = str(task.get("lark_task_guid") or task.get("guid") or "")
        analysis["title"] = _title(task)
        results.append(analysis)

    tier_counts = Counter(r["tier"] for r in results)
    scope_counts = Counter(r["scope"] for r in results)
    domain_counts = Counter(r["domain"] for r in results)
    side_counts = Counter(r["side"] for r in results)

    return {
        "schema": "uvisa_lark_unified_iceberg_classifier_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(results),
        "tier_counts": dict(tier_counts),
        "scope_counts": dict(scope_counts),
        "domain_counts": dict(domain_counts),
        "side_counts": dict(side_counts),
        "rows": results,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="UVISA Lark 统一冰山分类器")
    ap.add_argument("--input", required=True, help="JSON snapshot from lark_task_reader.py")
    ap.add_argument("--out-dir", default="/tmp/uvisa_unified_iceberg")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--side", choices=["all", "admin", "c端"], default="all")
    args = ap.parse_args(argv)

    data = json.loads(Path(args.input).read_text())
    result = classify_all(data)

    if args.side != "all":
        result["rows"] = [r for r in result["rows"] if r["side"] == args.side or r["side"] == "unknown"]
        result["total"] = len(result["rows"])
        result["tier_counts"] = dict(Counter(r["tier"] for r in result["rows"]))
        result["side_counts"] = dict(Counter(r["side"] for r in result["rows"]))

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "iceberg.latest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"=== UVISA Lark 统一冰山分析 ===")
        print(f"总数: {result['total']}")
        print(f"端: {result['side_counts']}")
        print(f"分层: {result['tier_counts']}")
        print(f"scope: {result['scope_counts']}")
        print(f"域: {result['domain_counts']}")
        print()
        tier_order = {"S0": 0, "S1": 1, "F": 2, "M": 3, "L": 4, "R": 5, "B": 6}
        for r in sorted(result["rows"], key=lambda x: (tier_order.get(x["tier"], 9), x["side"], x["domain"])):
            print(f'{r["tier"]:>3} | {r["side"]:<5} | {r["scope"]:<25} | {r["domain"]:<18} | {r["confidence"]:<6} | {r["title"][:55]}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
