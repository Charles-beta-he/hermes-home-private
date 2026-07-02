#!/usr/bin/env python3
"""Validate a reference-repo absorption SSOT pack.

Checks the artifact shape created by the Reference Repo Absorption Loop. No third-party dependencies.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REQUIRED_FILES = [
    "PLAN.md",
    "evidence/source-evidence.json",
    "graph/raven-everos-capability-graph.json",
    "proposals/experience-ratchet-created.json",
    "reports/final.md",
]
GATE_OUTCOMES = {"pass", "warn", "fail", "blocked"}
BOUNDARY_TERMS = ["no install", "no import", "no runtime", "no external dispatch", "no core mutation"]


def load_json(path: Path, errors: list[str]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"cannot read json {path}: {exc}")
        return None


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    if not root.is_dir():
        return [f"root is not directory: {root}"]
    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            errors.append(f"missing required file {rel}")

    evidence = load_json(root / "evidence/source-evidence.json", errors) if (root / "evidence/source-evidence.json").exists() else None
    if isinstance(evidence, dict):
        evidence_text = json.dumps(evidence, ensure_ascii=False).lower()
        if not any(token in evidence_text for token in ["head", "commit", "repo", "remote"]):
            errors.append("source evidence must pin repo/source identity and head/commit/remote")
        if "evidence" not in evidence_text and "source" not in evidence_text:
            errors.append("source evidence must include evidence/source refs")

    graph_path = root / "graph/raven-everos-capability-graph.json"
    graph = load_json(graph_path, errors) if graph_path.exists() else None
    if isinstance(graph, dict):
        nodes = graph.get("capability_nodes")
        wrappers = graph.get("agent_wrappers")
        gates = graph.get("gates")
        if not isinstance(nodes, list) or not nodes:
            errors.append("graph.capability_nodes must be non-empty list")
        if not isinstance(wrappers, list) or not wrappers:
            errors.append("graph.agent_wrappers must be non-empty list")
        if not isinstance(gates, list) or not gates:
            errors.append("graph.gates must be non-empty list")
        for wrapper in wrappers or []:
            if not isinstance(wrapper, dict):
                errors.append("agent wrapper must be object")
                continue
            wid = wrapper.get("id", "<unknown>")
            for key in ["wraps", "policy", "authority", "produces", "cannot_do"]:
                if key not in wrapper:
                    errors.append(f"agent wrapper {wid} missing {key}")
        for gate in gates or []:
            if not isinstance(gate, dict):
                errors.append("gate must be object")
                continue
            gid = gate.get("id", "<unknown>")
            outcomes = gate.get("outcomes")
            if not isinstance(outcomes, dict) or not GATE_OUTCOMES.issubset(outcomes.keys()):
                errors.append(f"gate {gid} missing outcomes {sorted(GATE_OUTCOMES)}")
        refs = graph.get("evidence_refs")
        if not isinstance(refs, list) or not refs:
            errors.append("graph.evidence_refs must be non-empty list")
        boundary = graph.get("authority_boundary")
        if isinstance(boundary, dict) and boundary.get("closed") is not True:
            errors.append("graph.authority_boundary.closed must be true when present")

    proposals_path = root / "proposals/experience-ratchet-created.json"
    proposals = load_json(proposals_path, errors) if proposals_path.exists() else None
    if isinstance(proposals, dict):
        created = proposals.get("created")
        if not isinstance(created, list) or not created:
            errors.append("proposals.created must be non-empty list")

    final_path = root / "reports/final.md"
    if final_path.exists():
        final = final_path.read_text(encoding="utf-8").lower()
        missing_terms = [term for term in BOUNDARY_TERMS if term not in final]
        if missing_terms:
            errors.append(f"final report missing not-done boundary terms: {missing_terms}")

    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: check_reference_absorption_pack.py <ssot-root>")
        return 2
    root = Path(argv[1])
    errors = validate(root)
    if errors:
        print("REFERENCE_ABSORPTION_PACK_INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    print("REFERENCE_ABSORPTION_PACK_OK")
    print(json.dumps({"root": str(root), "required_files": REQUIRED_FILES}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
