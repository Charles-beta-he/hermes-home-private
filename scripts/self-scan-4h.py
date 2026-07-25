#!/usr/bin/env python3
"""
4-Hour Self-Scan — 自动化健康检查
每 4 小时运行一次，检查系统健康状态
"""

import os, json, datetime, math

from hermes_evolution_store import default_store

STORE = default_store()
HEALTH_PATH = os.path.expanduser("~/.hermes/notes/engineering-cybernetics/health-history.jsonl")

DB_RESOLUTION = STORE.resolve_artifact(os.path.join("bayesian-agent", "confidence-db.json"), intent="read")
RESULTS_RESOLUTION = STORE.resolve_artifact(os.path.join("darwin-skill", "results.tsv"), intent="read")
DB_PATH = str(DB_RESOLUTION.path)
RESULTS_PATH = str(RESULTS_RESOLUTION.path)
DB_SOURCE = DB_RESOLUTION.source
RESULTS_SOURCE = RESULTS_RESOLUTION.source

def get_vdot(record):
    """Return V̇ across historical schema aliases (Vdot and V_dot)."""
    value = record.get("Vdot", record.get("V_dot"))
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(float(value)) else None

def check_health():
    issues = []
    
    # 1. 检查 V̇ 趋势
    if os.path.exists(HEALTH_PATH):
        with open(HEALTH_PATH, "r") as f:
            records = [json.loads(l) for l in f if l.strip()]
        if len(records) >= 2:
            recent = records[-3:]
            vdots = [get_vdot(r) for r in recent]
            if len(vdots) == 3 and all(v is not None and v < -0.05 for v in vdots):
                issues.append(f"CRITICAL: V̇ 连续 3 次负值 ({vdots})")
            elif vdots[-1] is None:
                status = recent[-1].get("measurement_status", "unknown")
                issues.append(f"WARNING: V̇ 最新不可用 ({status})")
            elif vdots[-1] < -0.05:
                issues.append(f"WARNING: V̇ 最新为负 ({vdots[-1]})")
    else:
        issues.append("WARNING: health-history.jsonl 不存在")
    
    # 2. 检查 D 级 skill 数量
    db = {"skills": {}}
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "r") as f:
            db = json.load(f)
        if DB_SOURCE not in {"active", "canonical"}:
            issues.append(f"WARNING: active confidence-db 缺失，降级读取 {DB_PATH}")
    else:
        issues.append(f"ERROR: confidence-db 不存在: {DB_PATH}")
    d_count = sum(1 for s in db.get("skills", {}).values() if s.get("darwin_grade") == "D")
    if d_count > 20:
        issues.append(f"WARNING: D 级 skill 过多 ({d_count})")
    
    # 3. 检查 confidence-db 完整性
    total = len(db.get("skills", {}))
    with_score = sum(1 for s in db.get("skills", {}).values() if s.get("darwin_score"))
    if total and with_score < total * 0.5:
        issues.append(f"WARNING: 仅 {with_score}/{total} skill 有 Darwin 评分")
    
    # 4. 检查 results.tsv 是否存在
    if not os.path.exists(RESULTS_PATH):
        issues.append(f"ERROR: results.tsv 不存在: {RESULTS_PATH}")
    elif RESULTS_SOURCE not in {"active", "canonical"}:
        issues.append(f"WARNING: active results.tsv 缺失，降级读取 {RESULTS_PATH}")
    
    # 5. 检查核心脚本存在
    scripts = ["agent-health-monitor.py", "session-history-analyzer.py", "backup-critical-config.py"]
    for s in scripts:
        if not os.path.exists(os.path.expanduser(f"~/.hermes/scripts/{s}")):
            issues.append(f"ERROR: 核心脚本缺失 {s}")
    
    return issues

def main():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    issues = check_health()
    
    print(f"[{now}] 4H Self-Scan Report")
    print("=" * 50)
    
    if not issues:
        print("✓ 所有检查通过，系统健康")
    else:
        for issue in issues:
            print(f"  {issue}")
    
    print("=" * 50)
    
    # 写入扫描日志
    log_path = os.path.expanduser("~/.hermes/notes/engineering-cybernetics/self-scan-log.jsonl")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a") as f:
        f.write(json.dumps({"timestamp": now, "issues": issues, "issue_count": len(issues)}) + "\n")
    
    # 自动刷新 dashboard
    os.system("python3 ~/.hermes/scripts/refresh-dashboard.py > /dev/null 2>&1")

if __name__ == "__main__":
    main()
