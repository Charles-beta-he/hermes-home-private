#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from typing import Any

FAMILY_ALIASES = {
    "rag": {"rag", "retrieval", "检索", "知识库"},
    "research": {"research", "研究", "调研"},
    "memory": {"memory", "记忆"},
    "mcp_tools": {"mcp", "tool", "tools", "工具"},
    "voice": {"voice", "语音"},
    "monitoring": {"monitor", "monitoring", "监控", "always-on"},
    "finance": {"finance", "financial", "金融", "投资"},
    "data_analysis": {"data", "analysis", "analytics", "数据分析"},
    "coding": {"coding", "code", "代码", "github"},
    "content": {"content", "内容"},
    "generative_ui": {"ui", "frontend", "界面", "前端"},
    "multi_agent": {"multi-agent", "multi_agent", "多智能体", "多agent"},
}


def choose_families(intent: str) -> list[str]:
    text = intent.lower()
    selected = [family for family, aliases in FAMILY_ALIASES.items() if any(alias in text for alias in aliases)]
    return selected or ["rag", "mcp_tools", "memory"]


def build_packet(catalog: dict[str, Any], registry: dict[str, Any], intent: str, max_examples: int = 3) -> dict[str, Any]:
    families = choose_families(intent)
    modules = {m["id"]: m for m in registry["modules"]}
    cards = []
    for family in families:
        rows = [a for a in catalog["apps"] if family in a["capabilities"]][:max_examples]
        cards.append({
            "family": family,
            "module_id": f"awesome_{family}",
            "module_available": f"awesome_{family}" in modules,
            "source_examples": [{"path": r["path"], "readme": r["evidence"]["readme"], "verification_status": r["verification_status"]} for r in rows],
            "owned_prototype_refs": modules.get(f"awesome_{family}", {}).get("owned_prototype_refs", []),
            "runtime_state": modules.get(f"awesome_{family}", {}).get("verification", {}).get("state", "static_evidence_only"),
        })
    missing = [c["family"] for c in cards if not c["module_available"] or not c["source_examples"]]
    return {
        "schema": "awesome_llm_apps_absorption_run_v1",
        "intent": intent,
        "source": catalog["source"],
        "selected_families": families,
        "source_cards": cards,
        "gates": {
            "source_identity": "PASS" if catalog["source"].get("commit") else "FAIL",
            "module_coverage": "PASS" if not missing else "WARN",
            "runtime_evidence": "WARN",
            "authority": "PASS",
        },
        "missing": missing,
        "next_actions": [
            {"family": c["family"], "action": "source_review" if c["runtime_state"] == "static_evidence_only" else "extend_owned_runtime_verification"}
            for c in cards
        ],
        "side_effects": {"external": False, "cron": False, "taskpool": False, "agentos": False, "publish": False, "destructive": False},
        "closure_state": "static_evidence_only",
        "cannot_prove": ["upstream runtime health", "provider availability", "production readiness"],
    }


def main():
    p=argparse.ArgumentParser(); p.add_argument("--intent", required=True); p.add_argument("--catalog", required=True); p.add_argument("--registry", required=True); p.add_argument("--out"); a=p.parse_args()
    catalog=json.loads(Path(a.catalog).read_text()); registry=json.loads(Path(a.registry).read_text())
    packet=build_packet(catalog, registry, a.intent)
    text=json.dumps(packet, ensure_ascii=False, indent=2)+"\n"
    if a.out:
        out=Path(a.out); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(text)
    print(text, end="")
    return 0 if packet["gates"]["source_identity"] == "PASS" else 1


if __name__ == "__main__": raise SystemExit(main())
