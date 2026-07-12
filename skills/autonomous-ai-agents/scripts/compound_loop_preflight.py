#!/usr/bin/env python3
"""Read-only preflight for compound/self-improving agent loop contracts.

Checks a YAML/Markdown/text contract for the minimum fields needed before dispatching
an autonomous maker/verifier loop. This script is advisory only and does not mutate
runtime/taskpool state or grant execution authority.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List

REQUIRED_CONCEPTS = {
    "goal": [r"\bgoal\b", r"目标", r"objective"],
    "acceptance": [r"acceptance", r"验收", r"success_criteria"],
    "budget_or_stop": [r"budget", r"max_turns", r"max_runtime", r"stop_conditions", r"预算", r"停止"],
    "maker": [r"\bmaker\b", r"executor", r"执行者", r"worker"],
    "verifier": [r"verifier", r"validator", r"验证", r"reviewer"],
    "evidence": [r"evidence", r"proof", r"artifact:", r"command:", r"证据"],
    "state_read": [r"state_read", r"context_read", r"prior_context", r"SSOT", r"上下文"],
    "state_write": [r"state_write", r"writeback", r"ratchet", r"写回"],
    "authority_gates": [r"authority", r"gate", r"permission", r"red_lines", r"权限", r"门禁"],
    "closure": [r"closure", r"verdict", r"pass \| warn \| fail \| blocked", r"闭环", r"状态"],
}

DANGEROUS_OPEN_PATTERNS = {
    "external_dispatch_maybe_open": [
        r"external_dispatch:\s*allowed",
        r"外发.*允许",
        r"send.*without.*approval",
    ],
    "secret_handling_maybe_open": [
        r"(password|api[_-]?key|secret|credential).{0,80}(allowed|send|publish)",
        r"(allowed|send|publish).{0,80}(password|api[_-]?key|secret|credential)",
    ],
    "destructive_maybe_open": [
        r"rm -rf",
        r"delete production",
        r"drop table",
        r"destructive.*allowed",
    ],
}


def scan(text: str) -> Dict[str, object]:
    found: Dict[str, bool] = {}
    missing: List[str] = []
    for concept, patterns in REQUIRED_CONCEPTS.items():
        hit = any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)
        found[concept] = hit
        if not hit:
            missing.append(concept)

    warnings: Dict[str, List[str]] = {}
    for name, patterns in DANGEROUS_OPEN_PATTERNS.items():
        hits = [p for p in patterns if re.search(p, text, flags=re.IGNORECASE)]
        if hits:
            warnings[name] = hits

    status = "PASS" if not missing and not warnings else ("WARN" if not missing else "FAIL")
    return {
        "status": status,
        "schema": "compound_loop_preflight_v1",
        "found": found,
        "missing": missing,
        "warnings": warnings,
        "policy": "read-only; advisory pre-dispatch check; does not grant execution authority",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only compound loop contract preflight")
    parser.add_argument("path", help="Path to contract/task/template text")
    args = parser.parse_args()

    path = Path(args.path).expanduser()
    if not path.exists():
        print(json.dumps({"status": "ERROR", "error": f"not found: {path}", "schema": "compound_loop_preflight_v1"}, ensure_ascii=False, indent=2))
        return 2

    result = scan(path.read_text(encoding="utf-8", errors="replace"))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] in {"PASS", "WARN"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
