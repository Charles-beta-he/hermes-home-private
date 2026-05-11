#!/usr/bin/env python3
"""Tests for architecture_theory_impact_ratchet.py."""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOME = Path.home()
SCRIPT = HOME / ".hermes" / "scripts" / "architecture_theory_impact_ratchet.py"


def load_module():
    spec = importlib.util.spec_from_file_location("architecture_theory_impact_ratchet", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def matrix_rows(module) -> str:
    surfaces = [
        "L0-trace, L1-router, L2-protocol",
        "L1-router, L3-ensemble, L5-consult-models",
        "L0-trace, L4-taskpool-brain, LX-health-quota",
        "skills, L4-taskpool-brain, L5-consult-models",
        "L2-protocol, L4-taskpool-brain, cron-gateway",
        "L3-ensemble, L5-consult-models, LX-health-quota",
        "L1-router, L5-consult-models, skills",
        "L2-protocol, L4-taskpool-brain, LX-health-quota",
    ]
    levers = [
        "evidence beats agreement",
        "requisite variety",
        "negative feedback and Lyapunov stability",
        "rule mutation from repeated correction",
        "near-decomposable boundary",
        "Bayesian uncertainty propagation",
        "entropy and communication budget",
        "target-bound 4/4 closeout",
    ]
    out = []
    for idx, theory in enumerate(module.REQUIRED_THEORY_IDS):
        out.append(
            f"| {theory} | {levers[idx]} | slice-{idx} | same-{idx}-a, same-{idx}-b | {surfaces[idx]} | rollback + evidence diff + health variance gate | py_compile + selfcheck + ratchet |"
        )
    return "\n".join(out)


def build_vault(root: Path) -> Path:
    module = load_module()
    write(root / module.MATRIX_REL, f"""---
type: playbook
status: active
---
# 08 - 理论到影响全架构传播矩阵

| Theory ID | Theory lever | Optimized slice | Same-theory propagation targets | Impact surfaces | Smoothing gate | Verification |
|---|---|---|---|---|---|---|
{matrix_rows(module)}
""")
    write(root / module.ATOM_REL, """---
type: atom
status: active
---
# Theory Impact Propagation

Theory Point ID is canonical. Layer Impact Map covers L0 through L5 and LX.
Same-theory propagation scans equivalent targets before closeout.
Impact Smoothing uses two-phase prepare/apply, health variance, evidence diff, rollback, and fail-closed gates.
局部优化不能直接升级为全局规则；local patch is only a candidate until verification passes.
""")
    return root


def test_full_fixture_passes_with_all_theories_and_surfaces():
    module = load_module()
    with tempfile.TemporaryDirectory() as td:
        report = module.evaluate(build_vault(Path(td)))
        assert report["status"] == "PASS", report["failed_checks"]
        assert report["coverage"]["theories"]["covered"] == len(module.REQUIRED_THEORY_IDS)
        assert report["coverage"]["surfaces"]["covered"] == len(module.REQUIRED_SURFACES)


def test_missing_required_theory_fails_closed():
    module = load_module()
    with tempfile.TemporaryDirectory() as td:
        vault = build_vault(Path(td))
        p = vault / module.MATRIX_REL
        text = p.read_text(encoding="utf-8").replace("| evidence-first |", "| evidence-first-missing |", 1)
        p.write_text(text, encoding="utf-8")
        report = module.evaluate(vault)
        assert report["status"] == "FAIL", report
        names = {c["name"] for c in report["failed_checks"]}
        assert "matrix:theory:evidence-first" in names, names


def test_same_theory_targets_must_not_be_singleton():
    module = load_module()
    with tempfile.TemporaryDirectory() as td:
        vault = build_vault(Path(td))
        p = vault / module.MATRIX_REL
        text = p.read_text(encoding="utf-8").replace("same-0-a, same-0-b", "only-one-target", 1)
        p.write_text(text, encoding="utf-8")
        report = module.evaluate(vault)
        assert report["status"] == "FAIL", report
        names = {c["name"] for c in report["failed_checks"]}
        assert "row:evidence-first:same_theory_targets_at_least_2" in names, names


def test_smoothing_gate_must_be_operational_not_prose_only():
    module = load_module()
    with tempfile.TemporaryDirectory() as td:
        vault = build_vault(Path(td))
        p = vault / module.MATRIX_REL
        text = p.read_text(encoding="utf-8").replace("rollback + evidence diff + health variance gate", "be careful", 1)
        p.write_text(text, encoding="utf-8")
        report = module.evaluate(vault)
        assert report["status"] == "FAIL", report
        names = {c["name"] for c in report["failed_checks"]}
        assert "row:evidence-first:smoothing_gate_has_operational_keywords" in names, names


def test_missing_atom_contract_fails_closed():
    module = load_module()
    with tempfile.TemporaryDirectory() as td:
        vault = build_vault(Path(td))
        (vault / module.ATOM_REL).write_text("# Too thin\n", encoding="utf-8")
        report = module.evaluate(vault)
        assert report["status"] == "FAIL", report
        names = {c["name"] for c in report["failed_checks"]}
        assert "atom:phrase:Theory Point ID" in names, names
        assert "atom:phrase:Layer Impact Map" in names, names


def test_cli_writes_json_and_markdown_report():
    module = load_module()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        vault = build_vault(root / "brain")
        out_json = root / "report.json"
        out_md = root / "report.md"
        env = dict(os.environ, HERMES_BRAIN_VAULT=str(vault))
        r = subprocess.run([
            sys.executable,
            str(SCRIPT),
            "--write-json",
            str(out_json),
            "--write-report",
            str(out_md),
            "--json",
        ], capture_output=True, text=True, env=env)
        assert r.returncode == 0, r.stderr or r.stdout
        payload = json.loads(out_json.read_text(encoding="utf-8"))
        assert payload["status"] == "PASS", payload
        assert "理论到影响全架构传播棘轮复审" in out_md.read_text(encoding="utf-8")


if __name__ == "__main__":
    tests = [name for name in globals() if name.startswith("test_")]
    for name in tests:
        globals()[name]()
    print(f"PASS {len(tests)} tests")
