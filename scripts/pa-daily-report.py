#!/usr/bin/env python3
"""
PA Daily Report — 个人助理日报
每日 23:00 自动发送给用户，并产出受治理的 taskpool 候选 sidecar。
"""

from __future__ import annotations

import datetime
import json
import os
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
HERMES_HOME = SCRIPT_DIR.parent

PA_HEALTH = Path(os.environ.get("HERMES_PA_HEALTH_PATH", str(HERMES_HOME / "notes" / "engineering-cybernetics" / "pa-health-history.jsonl"))).expanduser()
HEALTH = Path(os.environ.get("HERMES_HEALTH_PATH", str(HERMES_HOME / "notes" / "engineering-cybernetics" / "health-history.jsonl"))).expanduser()
PATTERNS = Path(os.environ.get("HERMES_ROUTINE_PATTERNS_PATH", str(HERMES_HOME / "notes" / "user-routine-patterns.json"))).expanduser()
REPORT_DIR = Path(os.environ.get("HERMES_PA_REPORT_DIR", str(HERMES_HOME / "notes" / "reports"))).expanduser()


def load_today_sessions() -> list[dict[str, Any]]:
    today = datetime.datetime.now().date().isoformat()
    sessions: list[dict[str, Any]] = []
    for path in (HEALTH, PA_HEALTH):
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if str(rec.get("timestamp", "")).startswith(today):
                    sessions.append(rec)
    return sessions


def load_patterns() -> dict[str, Any]:
    if not PATTERNS.exists():
        return {}
    with PATTERNS.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_latest_pa_health() -> tuple[float, float]:
    v_pa = 0.5
    vdot_pa = 0.0
    if not PA_HEALTH.exists():
        return v_pa, vdot_pa
    with PA_HEALTH.open("r", encoding="utf-8") as f:
        lines = [line for line in f if line.strip()]
    if not lines:
        return v_pa, vdot_pa
    latest = json.loads(lines[-1])
    return float(latest.get("V_pa", 0.5)), float(latest.get("Vdot_pa", 0.0))


def candidate_common(report_path: Path, report_date: str) -> dict[str, Any]:
    return {
        "report_id": f"pa-daily:{report_date}",
        "project": "hermes-agent",
        "concepts": ["task", "daily-report", "pa-report"],
        "lane": "auto",
        "expires_days": 14,
        "evidence_bundle": str(report_path),
        "truth_gate": "report-evidence-present",
        "expected_participants": [],
        "requires_multimodel": False,
        "multimodel_reason": "",
    }


def build_governed_candidates(
    report_path: Path,
    report_date: str,
    sessions: list[dict[str, Any]],
    patterns: dict[str, Any],
    v_pa: float,
    vdot_pa: float,
) -> list[dict[str, Any]]:
    base = candidate_common(report_path, report_date)
    candidates: list[dict[str, Any]] = []

    if v_pa < 0.6 or vdot_pa <= -0.05:
        priority = "P1" if v_pa < 0.5 or vdot_pa <= -0.10 else "P2"
        candidates.append(
            {
                **base,
                "dedupe_key": "pa-health-regression",
                "title": "复盘 PA 健康度退化并收敛修复方案",
                "priority": priority,
                "priority_layer": f"daily-report:{priority.lower()}:health-regression",
                "dependency_order": ["1"],
                "multimodel_triage_result": f"{priority}-daily-health-regression",
                "architecture_target": "taskpool",
                "objective": f"基于 {report_date} 日报复盘 PA 健康度退化：V_pa={v_pa:.4f}, Vdot_pa={vdot_pa:+.4f}，确认根因、修复顺序与回退策略。",
                "capability_delta": "把日报中的健康退化信号转成带证据和修复边界的治理任务，避免退化仅停留在告警文本。",
                "anti_drift_check": "禁止只记录告警；必须给出退化证据、根因假设、验证步骤与回退策略。",
                "acceptance_evidence": "日报证据、健康历史对比、根因分析、最小修复切片与回退方案。",
                "parallel_boundary": "先核对健康历史与变化幅度，再定位根因，最后确定修复或监控落点。",
            }
        )

    task_types = patterns.get("task_types") or {}
    repeated = sorted(task_types.items(), key=lambda item: (-item[1], item[0]))[:3]
    for index, (task_type, count) in enumerate(repeated, start=1):
        if count < 3:
            continue
        priority = "P2" if count >= 5 else "P3"
        candidates.append(
            {
                **base,
                "dedupe_key": f"routine-pattern:{task_type}",
                "title": f"将高频任务类型“{task_type}”沉淀为 skill 或自动化",
                "priority": priority,
                "priority_layer": f"daily-report:{priority.lower()}:routine-pattern",
                "dependency_order": [str(index + 1)],
                "multimodel_triage_result": f"{priority}-routine-pattern:{task_type}",
                "architecture_target": "taskpool",
                "objective": f"基于 {report_date} 日报识别到高频任务类型“{task_type}”累计 {count} 次，评估是否应沉淀为可复用 skill、自动化或治理规则。",
                "capability_delta": "把日报中的重复模式转成可执行的工程化沉淀任务，而不是只做统计展示。",
                "anti_drift_check": "禁止为单次偶发任务建 skill；必须确认是稳定高频模式，并明确沉淀边界、验证方式与维护责任。",
                "acceptance_evidence": "日报模式统计、候选 skill/自动化落点、验证步骤、回退策略。",
                "parallel_boundary": "先确认模式稳定性，再选择沉淀落点，最后验证是否真正减少重复劳动。",
            }
        )

    if len(sessions) >= 8 and not candidates:
        candidates.append(
            {
                **base,
                "dedupe_key": "daily-load-review",
                "title": "复盘高交互日的任务分布并识别自动化机会",
                "priority": "P3",
                "priority_layer": "daily-report:p3:load-review",
                "dependency_order": ["1"],
                "multimodel_triage_result": "P3-daily-load-review",
                "architecture_target": "taskpool",
                "objective": f"基于 {report_date} 当日 {len(sessions)} 次交互，复盘任务分布、识别可自动化或可前置治理的重复链路。",
                "capability_delta": "把高负载日的观察转成具体治理切片，避免日报只记录忙碌程度。",
                "anti_drift_check": "禁止泛泛复盘；必须给出具体的重复链路、候选落点与验证方式。",
                "acceptance_evidence": "日报交互量、任务分布切片、候选自动化/治理落点。",
                "parallel_boundary": "先确认高负载来源，再筛选最有杠杆的自动化候选。",
            }
        )

    return candidates


def write_governed_task_sidecar(report_path: Path, sessions: list[dict[str, Any]], patterns: dict[str, Any], v_pa: float, vdot_pa: float) -> Path:
    report_date = report_path.stem.removeprefix("pa-daily-")
    payload = {
        "schema": "daily_report_task_candidates_v1",
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "report_kind": "pa-daily-report",
        "report_id": f"pa-daily:{report_date}",
        "report_path": str(report_path),
        "summary": {
            "sessions": len(sessions),
            "v_pa": round(v_pa, 4),
            "vdot_pa": round(vdot_pa, 4),
            "task_types": patterns.get("task_types", {}),
        },
        "candidates": build_governed_candidates(report_path, report_date, sessions, patterns, v_pa, vdot_pa),
    }
    sidecar_path = report_path.with_suffix(".tasks.json")
    sidecar_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return sidecar_path


def main() -> None:
    sessions = load_today_sessions()
    patterns = load_patterns()
    v_pa, vdot_pa = load_latest_pa_health()

    lines: list[str] = []
    lines.append("═══════════════════════════════════════════════════════════════")
    lines.append("                  🤖 个人助理 — 每日进化报告")
    lines.append("═══════════════════════════════════════════════════════════════")
    lines.append(f"日期: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    lines.append("【今日交互】")
    lines.append(f"  Sessions: {len(sessions)}")
    lines.append("")

    lines.append("【PA 健康度】")
    status = "🟢" if v_pa > 0.7 else "🟡" if v_pa > 0.5 else "🔴"
    lines.append(f"  {status} V_PA = {v_pa:.4f}  (目标: 0.85)")
    lines.append(f"     V̇_PA = {vdot_pa:+.4f}")
    if vdot_pa > 0.05:
        lines.append("     ↑ 显著进化")
    elif vdot_pa < -0.05:
        lines.append("     ↓ 退化告警，建议复盘")
    lines.append("")

    lines.append("【习得模式】")
    if patterns.get("task_types"):
        for task_type, count in sorted(patterns["task_types"].items(), key=lambda x: -x[1])[:5]:
            marker = "🔒" if count >= 3 else "📊"
            lines.append(f"  {marker} {task_type}: {count} 次")
    else:
        lines.append("  持续观察中...")
    lines.append("")

    lines.append("【进化建议】")
    if v_pa < 0.6:
        lines.append("  • 多与我交互，帮助我学习您的偏好")
    if v_pa < 0.7:
        lines.append("  • 纠正我的输出，我会记住并改进")
    if not any(v >= 3 for v in patterns.get("task_types", {}).values()):
        lines.append("  • 重复任务类型出现 3 次后，我会自动优化")
    if v_pa > 0.7:
        lines.append("  • 运行良好！我可以开始尝试主动建议")
    lines.append("")

    lines.append("【等级】")
    if v_pa < 0.6:
        level = "Level 1: 指令执行"
    elif v_pa < 0.72:
        level = "Level 2: 主动确认"
    elif v_pa < 0.82:
        level = "Level 3: 主动建议"
    elif v_pa < 0.90:
        level = "Level 4: 自主执行"
    else:
        level = "Level 5: 预见性伙伴"
    lines.append(f"  {level}")
    lines.append("")
    lines.append("═══════════════════════════════════════════════════════════════")

    report = "\n".join(lines)
    print(report)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / f"pa-daily-{datetime.datetime.now().date().isoformat()}.md"
    report_path.write_text(report, encoding="utf-8")
    sidecar_path = write_governed_task_sidecar(report_path, sessions, patterns, v_pa, vdot_pa)
    payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
    print(f"\nGoverned task candidates sidecar: {sidecar_path}")
    print(f"Governed task candidates count: {len(payload.get('candidates', []))}")


if __name__ == "__main__":
    main()
