#!/usr/bin/env python3
"""
Refresh Dashboard — 自动刷新进化仪表盘
由 session-health-logger.py 或 cronjob 触发
"""

import os, json, datetime, math

from hermes_evolution_store import default_store

STORE = default_store()
HEALTH_PATH = os.path.expanduser("~/.hermes/notes/engineering-cybernetics/health-history.jsonl")
DASHBOARD_PATH = os.path.expanduser("~/.hermes/notes/engineering-cybernetics/evolution-dashboard.md")


def configure_sources():
    """Resolve runtime evolution sources after tests or callers configure STORE."""
    global DB_RESOLUTION, RESULTS_RESOLUTION, DB_PATH, RESULTS_PATH, DB_SOURCE, RESULTS_SOURCE
    DB_RESOLUTION = STORE.resolve_artifact(os.path.join("bayesian-agent", "confidence-db.json"), intent="read")
    RESULTS_RESOLUTION = STORE.resolve_artifact(os.path.join("darwin-skill", "results.tsv"), intent="read")
    DB_PATH = str(DB_RESOLUTION.path)
    RESULTS_PATH = str(RESULTS_RESOLUTION.path)
    DB_SOURCE = DB_RESOLUTION.source
    RESULTS_SOURCE = RESULTS_RESOLUTION.source


configure_sources()

def get_vdot(record):
    """Return V̇ across historical schema aliases (Vdot and V_dot)."""
    return finite_number(record.get('Vdot', record.get('V_dot')))


def finite_number(value):
    """Return a finite float, preserving explicit unknown measurements as None."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(float(value)) else None


def summarize_skills(conf_db):
    """Summarize Darwin coverage without dropping the top-level S grade."""
    skills = conf_db.get("skills", {})
    grades = {"S": 0, "A": 0, "B": 0, "C": 0, "D": 0, "pending": 0}
    for skill in skills.values():
        grade = skill.get("darwin_grade", "pending")
        grades[grade] = grades.get(grade, 0) + 1
    evaluated = sum(1 for skill in skills.values() if finite_number(skill.get("darwin_score")) is not None)
    return len(skills), evaluated, grades


def load_latest_dream_run():
    if not STORE.runs_path.exists():
        return None
    latest = None
    with STORE.runs_path.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                latest = json.loads(line)
            except Exception:
                pass
    return latest

def refresh():
    data_warnings = []
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "r") as f:
            conf_db = json.load(f)
        if DB_SOURCE not in {"active", "canonical"}:
            data_warnings.append(f"active confidence-db 缺失；降级读取 {DB_PATH}")
    else:
        conf_db = {"skills": {}}
        data_warnings.append(f"confidence-db 缺失: {DB_PATH}")
    
    total, with_d, grades = summarize_skills(conf_db)
    
    health_records = []
    if os.path.exists(HEALTH_PATH):
        with open(HEALTH_PATH, "r") as f:
            for line in f:
                try:
                    health_records.append(json.loads(line))
                except:
                    pass
    latest_dream_run = load_latest_dream_run()
    if health_records:
        latest_health = health_records[-1]
        if finite_number(latest_health.get('V')) is None or get_vdot(latest_health) is None:
            status = latest_health.get('measurement_status', 'unknown')
            data_warnings.append(f"最新健康度证据不足: {status} (V/V̇ unavailable)")
    
    if os.path.exists(RESULTS_PATH):
        with open(RESULTS_PATH, "r") as f:
            results_lines = f.readlines()
        if RESULTS_SOURCE not in {"active", "canonical"}:
            data_warnings.append(f"active results.tsv 缺失；降级读取 {RESULTS_PATH}")
    else:
        results_lines = []
        data_warnings.append(f"results.tsv 缺失: {RESULTS_PATH}")
    
    lines = []
    lines.append("═══════════════════════════════════════════════════════════════════════════════")
    lines.append("                    Agent 控制论进化仪表盘")
    lines.append("═══════════════════════════════════════════════════════════════════════════════")
    lines.append(f"Timestamp: {datetime.datetime.now().isoformat()}")
    if data_warnings:
        lines.append("Status: ⚠️ DEGRADED — 健康证据或数据源降级")
        lines.append("")
        lines.append("【健康/数据告警】")
        for warning in data_warnings:
            lines.append(f"  ⚠️ {warning}")
    else:
        lines.append("Status: ✅ OK")
    lines.append("")
    
    lines.append("【健康度】")
    if health_records:
        latest = health_records[-1]
        v = finite_number(latest.get('V'))
        vdot = get_vdot(latest)
        lines.append(f"  V = {v:.4f}" if v is not None else "  V = UNKNOWN (insufficient evidence)")
        lines.append(f"  V̇ = {vdot:+.4f}" if vdot is not None else "  V̇ = UNKNOWN (insufficient evidence)")
        lines.append(f"  记录数: {len(health_records)}")
        
        # 趋势
        if len(health_records) >= 3:
            recent_v = [finite_number(r.get('V')) for r in health_records[-5:]]
            observed_v = [value for value in recent_v if value is not None]
            if len(observed_v) >= 2:
                trend = "↑" if observed_v[-1] > observed_v[0] else "↓" if observed_v[-1] < observed_v[0] else "→"
                lines.append(f"  趋势: {trend} (近5次有效观测)")
            else:
                lines.append("  趋势: UNKNOWN (近5次有效观测不足)")
    else:
        lines.append("  V = 0.8600 (基线)")
        lines.append("  V̇ = 0.0000")
    lines.append("")
    
    lines.append("【Dreaming / Nightly 有效健康】")
    if latest_dream_run:
        lines.append(f"  最近状态: {latest_dream_run.get('status', 'UNKNOWN')}")
        lines.append(f"  有效审计: {latest_dream_run.get('effective_audit')}")
        lines.append(f"  状态推进: {latest_dream_run.get('state_advanced')}")
        lines.append(f"  降级/阻写: degraded={latest_dream_run.get('degraded')} write_blocked={latest_dream_run.get('write_blocked')}")
        reasons = latest_dream_run.get('reasons') or []
        if reasons:
            lines.append(f"  原因: {', '.join(str(r) for r in reasons)}")
        proof = latest_dream_run.get('proof_hash') or latest_dream_run.get('dream_run_proof_hash')
        if proof:
            lines.append(f"  proof: {str(proof)[:16]}")
    else:
        lines.append("  尚无 canonical dream run ledger")
    lines.append("")

    lines.append("【Skill 生态】")
    lines.append(f"  总数: {total}")
    lines.append(f"  已评估: {with_d}")
    lines.append(f"  等级: S={grades.get('S',0)} A={grades.get('A',0)} B={grades.get('B',0)} C={grades.get('C',0)} D={grades.get('D',0)}")
    lines.append("")
    
    lines.append("【Phase 状态】")
    lines.append("  Phase 0: ✅ 跨学科基线")
    lines.append("  Phase 1: ✅ 控制论基线")
    lines.append("  Phase 2: ✅ 反馈优化")
    lines.append("  Phase 3: ✅ 智能升级")
    lines.append("  Phase 4: ✅ 大系统")
    lines.append("  Phase 5: 🔄 数据驱动验证")
    lines.append("")
    
    lines.append("【最近 Darwin 记录】")
    for line in results_lines[-5:]:
        cols = line.strip().split("\t")
        if len(cols) >= 6 and cols[0] != "timestamp":
            lines.append(f"  {cols[0][:10]} {cols[2]:<25} {cols[3]:>3}→{cols[4]:>3} [{cols[5]}]")
    lines.append("")
    
    lines.append("═══════════════════════════════════════════════════════════════════════════════")
    
    dashboard = "\n".join(lines)
    with open(DASHBOARD_PATH, "w") as f:
        f.write(dashboard)
    print("✓ Dashboard refreshed")

if __name__ == "__main__":
    refresh()
