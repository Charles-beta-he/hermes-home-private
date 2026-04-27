#!/usr/bin/env bash
# model-diversity-monitor.py — 追踪 per-pair 模型一致性趋势
# 检测模型间是否趋同 (should diverge for effective verification)

import sqlite3, json, os, sys
from collections import defaultdict

DB_PATH = os.path.expanduser(os.environ.get("HERMES_ROUTE_DB_PATH", "~/.hermes/route_outcomes.db"))

def monitor():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # 获取所有 model_chain (取第一个模型)
    rows = conn.execute("""
        SELECT id, ts, json_extract(model_chain, '$[0]') as model, verdict, route
        FROM route_outcomes
        WHERE model_chain IS NOT NULL AND model_chain != ''
        ORDER BY ts DESC
        LIMIT 500
    """).fetchall()

    # 按模型统计
    model_stats = defaultdict(lambda: {"pass": 0, "fail": 0, "total": 0})
    for r in rows:
        m = r["model"] or "unknown"
        model_stats[m]["total"] += 1
        if r["verdict"] == "pass":
            model_stats[m]["pass"] += 1
        else:
            model_stats[m]["fail"] += 1

    # 检测每对模型的一致性 (同一 route 的 verdict 是否相同)
    # 这需要同一 task_id 的多模型 trace — 目前 model_chain 是单模型
    # 改为检测 per-model per-route pass_rate 分化
    route_model = defaultdict(lambda: defaultdict(lambda: {"pass": 0, "total": 0}))
    for r in rows:
        route = r["route"] or "<blank>"
        m = r["model"] or "unknown"
        route_model[route][m]["total"] += 1
        if r["verdict"] == "pass":
            route_model[route][m]["pass"] += 1

    # 计算 per-route 的模型 pass_rate 方差 (高方差 = 好, 模型有分化)
    diversity_signals = []
    for route, models in route_model.items():
        rates = []
        for m, stats in models.items():
            if stats["total"] >= 3:
                rates.append((m, stats["pass"] / stats["total"]))
        if len(rates) >= 2:
            vals = [r[1] for r in rates]
            variance = max(vals) - min(vals)
            mean = sum(vals) / len(vals)
            if variance < 0.05 and mean > 0.9:
                diversity_signals.append({
                    "route": route,
                    "models": rates,
                    "variance": round(variance, 3),
                    "risk": "convergence_warning" if variance < 0.02 else "low_diversity",
                    "note": "Models agree too much — possible correlated errors or redundancy"
                })

    print(f"Model Diversity Monitor")
    print(f"  Models tracked: {len(model_stats)}")
    for m, s in sorted(model_stats.items()):
        pr = s["pass"] / s["total"] if s["total"] else 0
        print(f"    {m:25s} {s['total']:3d}x pass={pr:.0%}")

    if diversity_signals:
        print(f"\n  ⚠ Low diversity routes ({len(diversity_signals)}):")
        for ds in diversity_signals[:10]:
            print(f"    route={ds['route']} variance={ds['variance']} models={[m for m,_ in ds['models']]}")
        print(f"    Risk: {ds['risk']} — {ds['note']}")
    else:
        print(f"\n  ✓ All routes show healthy model diversity")

    conn.close()
    return {"models": len(model_stats), "diversity_warnings": len(diversity_signals)}

if __name__ == "__main__":
    monitor()
