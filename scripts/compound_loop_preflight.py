#!/usr/bin/env python3
"""Read-only preflight for compound/self-improving agent loop contracts.

Checks a YAML/Markdown/text contract for the minimum fields needed before dispatching
an autonomous maker/verifier loop. This script does not mutate taskpool state.
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

CLAIMED_COMPOUND_LOOP_PATTERNS = [
    r"compound[_ -]?agent[_ -]?loop",
    r"compound[_ -]?loop",
    r"bilevel",
    r"outer[_ -]?loop",
    r"meta[_ -]?loop",
    r"self[-_ ]?improv",
    r"meta[-_ ]?autoresearch",
]

CONDITIONAL_COMPOUND_CONCEPTS = {
    "measurable_objective": [
        r"measurable_objective",
        r"success[_ -]?metric",
        r"\bmetric\b",
        r"benchmark",
        r"comparator",
        r"baseline",
        r"可衡量",
    ],
    "outer_loop_change_surface": [
        r"outer_loop_change_surface",
        r"mechanism_change_surface",
        r"search[_ -]?strategy",
        r"change[_ -]?surface",
        r"mechanism[_ -]?carrier",
        r"exploration[_ -]?policy",
        r"机制.*变更",
    ],
}

ADVISORY_COMPOUND_CONCEPTS = {
    "benchmark_comparator": [r"benchmark", r"comparator", r"baseline", r"基线", r"对照"],
    "meta_loop_input_boundary": [
        r"meta_loop_input_boundary",
        r"trace/code",
        r"code.{0,40}trace",
        r"trace.{0,40}code",
        r"allowed[_ -]?observation[_ -]?surface",
        r"experiment[_ -]?ledger",
    ],
    "claims_not_proven_boundary": [r"claims_not_proven", r"unverified_claims", r"not proven", r"未证实"],
    "no_authority_expansion": [
        r"no_authority_expansion",
        r"no-authority-expansion",
        r"must not.{0,80}(widen|expand).{0,40}authority",
        r"authority.{0,80}(not|no).{0,40}(widen|expand)",
        r"not silently widen",
    ],
}

DANGEROUS_OPEN_PATTERNS = {
    "external_dispatch_maybe_open": [
        r"external_dispatch:\s*allowed",
        r"外发.*允许",
        r"send.*without.*approval",
    ],
    "secret_handling_maybe_open": [
        r"(password|api[_-]?key|secret|credential)[^\n]{0,80}(allowed to|send|sent)",
        r"(allowed to|send)[^\n]{0,80}(password|api[_-]?key|secret|credential)",
    ],
    "destructive_maybe_open": [
        r"rm -rf",
        r"delete production",
        r"drop table",
        r"destructive.*allowed",
    ],
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def has_any(text: str, patterns: List[str]) -> bool:
    return any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)


def claims_compound_loop(text: str) -> bool:
    return has_any(text, CLAIMED_COMPOUND_LOOP_PATTERNS)


def scan(text: str) -> Dict[str, object]:
    found: Dict[str, bool] = {}
    missing: List[str] = []
    for concept, patterns in REQUIRED_CONCEPTS.items():
        hit = has_any(text, patterns)
        found[concept] = hit
        if not hit:
            missing.append(concept)

    claimed_compound_loop = claims_compound_loop(text)
    found["claimed_compound_or_bilevel_loop"] = claimed_compound_loop
    conditional_missing: List[str] = []
    advisory_missing: List[str] = []

    if claimed_compound_loop:
        for concept, patterns in CONDITIONAL_COMPOUND_CONCEPTS.items():
            hit = has_any(text, patterns)
            found[concept] = hit
            if not hit:
                conditional_missing.append(concept)
                missing.append(concept)

        for concept, patterns in ADVISORY_COMPOUND_CONCEPTS.items():
            hit = has_any(text, patterns)
            found[concept] = hit
            if not hit:
                advisory_missing.append(concept)

    warnings: Dict[str, List[str]] = {}
    for name, patterns in DANGEROUS_OPEN_PATTERNS.items():
        hits = [p for p in patterns if re.search(p, text, flags=re.IGNORECASE)]
        if hits:
            warnings[name] = hits

    if advisory_missing:
        warnings["compound_loop_advisory_boundary_missing"] = advisory_missing

    status = "PASS" if not missing and not warnings else ("WARN" if not missing else "FAIL")
    return {
        "status": status,
        "schema": "compound_loop_preflight_v2",
        "found": found,
        "missing": missing,
        "conditional_missing": conditional_missing,
        "warnings": warnings,
        "policy": "read-only; advisory pre-dispatch check; does not grant execution authority",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only compound loop contract preflight")
    parser.add_argument("path", help="Path to contract/task/template text")
    parser.add_argument("--json", action="store_true", help="Emit JSON only")
    args = parser.parse_args()

    path = Path(args.path).expanduser()
    if not path.exists():
        result = {"status": "ERROR", "error": f"not found: {path}", "schema": "compound_loop_preflight_v2"}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2

    result = scan(read_text(path))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] in {"PASS", "WARN"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
