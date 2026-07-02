#!/usr/bin/env python3
"""Tests for check_reference_absorption_pack.py."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).with_name("check_reference_absorption_pack.py")


def make_pack(root: Path, *, bad: str | None = None) -> None:
    (root / "evidence").mkdir()
    (root / "graph").mkdir()
    (root / "proposals").mkdir()
    (root / "reports").mkdir()
    (root / "PLAN.md").write_text("# Plan\n- [x] source\n", encoding="utf-8")
    evidence = {"sources": [{"repo": "example/repo", "head": "abc123", "evidence_refs": ["README.md:1"]}]}
    (root / "evidence/source-evidence.json").write_text(json.dumps(evidence), encoding="utf-8")
    graph = {
        "capability_nodes": [{"id": "source_reference_intake"}],
        "agent_wrappers": [{"id": "reference_reviewer", "wraps": ["source_reference_intake"], "policy": ["read_only"], "authority": "read_only", "produces": ["report"], "cannot_do": ["external_write"]}],
        "gates": [{"id": "source_identity_gate", "outcomes": {"pass": "continue", "warn": "continue_with_warning", "fail": "retry_or_stop", "blocked": "human_gate"}}],
        "evidence_refs": ["evidence/source-evidence.json"],
        "authority_boundary": {"closed": True},
    }
    if bad == "no_gate_outcomes":
        graph["gates"][0]["outcomes"] = {"pass": "continue"}
    (root / "graph/raven-everos-capability-graph.json").write_text(json.dumps(graph), encoding="utf-8")
    manifest = {"created": [{"atom_id": "atom1", "status": "promoted_candidate"}]}
    (root / "proposals/experience-ratchet-created.json").write_text(json.dumps(manifest), encoding="utf-8")
    final = "# Final\nnot done: no install, no import, no runtime enablement, no external dispatch, no core mutation\n"
    if bad == "missing_boundaries":
        final = "# Final\nAll good\n"
    (root / "reports/final.md").write_text(final, encoding="utf-8")


def run_checker(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), str(root)], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def test_valid_pack_passes() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        make_pack(root)
        result = run_checker(root)
        assert result.returncode == 0, result.stdout
        assert "REFERENCE_ABSORPTION_PACK_OK" in result.stdout


def test_gate_without_outcomes_fails() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        make_pack(root, bad="no_gate_outcomes")
        result = run_checker(root)
        assert result.returncode != 0
        assert "source_identity_gate" in result.stdout


def test_missing_boundary_statement_fails() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        make_pack(root, bad="missing_boundaries")
        result = run_checker(root)
        assert result.returncode != 0
        assert "boundary" in result.stdout.lower() or "not-done" in result.stdout.lower()


if __name__ == "__main__":
    failures = []
    for test in [test_valid_pack_passes, test_gate_without_outcomes_fails, test_missing_boundary_statement_fails]:
        try:
            test()
            print(f"PASS {test.__name__}")
        except AssertionError as exc:
            print(f"FAIL {test.__name__}: {exc}")
            failures.append(test.__name__)
    if failures:
        raise SystemExit(1)
    print("ABSORPTION_CHECKER_TESTS_OK")
