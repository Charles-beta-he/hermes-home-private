#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path.home() / ".hermes" / "scripts" / "skill_candidate_staging.py"


def load_module():
    spec = importlib.util.spec_from_file_location("skill_candidate_staging_under_test", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def write_fixture(root: Path):
    skill = root / "skills" / "software-development" / "example" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("---\nname: example\ndescription: Existing scoped skill\n---\n# Example\n", encoding="utf-8")
    evidence = root / "proof" / "stage-report.md"
    evidence.parent.mkdir(parents=True)
    evidence.write_text("proof: focused pytest passed\n", encoding="utf-8")
    proposal = root / "proposal.md"
    proposal.write_text(
        f"# Proposal\n\nPatch existing skill trigger guidance using evidence {evidence}.\n\nRollback: revert this staged patch if proof-check fails.\n",
        encoding="utf-8",
    )
    out = root / "evidence" / "skill-evolution-candidates"
    return skill, evidence, proposal, out


def test_stage_candidate_writes_json_and_markdown_without_touching_skill():
    mod = load_module()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        skill, evidence, proposal, out = write_fixture(root)
        before = skill.read_text(encoding="utf-8")
        result = mod.stage_candidate(skill, [evidence], proposal, out, "example candidate")
        assert result["status"] == "staged", result
        assert skill.read_text(encoding="utf-8") == before
        json_path = Path(result["artifact_paths"]["json"])
        md_path = Path(result["artifact_paths"]["markdown"])
        assert json_path.exists() and md_path.exists()
        payload = json.loads(json_path.read_text(encoding="utf-8"))
        assert payload["governance"]["no_direct_skill_write"] is True
        assert all(check["ok"] for check in payload["checks"]), payload["checks"]


def test_broad_trigger_or_missing_rollback_blocks_candidate():
    mod = load_module()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        skill, evidence, proposal, out = write_fixture(root)
        proposal.write_text(f"Update skill for any task using {evidence}.\n", encoding="utf-8")
        result = mod.stage_candidate(skill, [evidence], proposal, out, "bad candidate")
        assert result["status"] == "blocked", result
        failed = {c["name"] for c in result["checks"] if not c["ok"]}
        assert "proposal_has_rollback" in failed
        assert "trigger_breadth_limited" in failed
        assert not out.exists()


def test_cli_dry_run_returns_json_without_writing_artifact():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        skill, evidence, proposal, out = write_fixture(root)
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "stage",
                "--skill",
                str(skill),
                "--evidence",
                str(evidence),
                "--proposal",
                str(proposal),
                "--title",
                "dry run candidate",
                "--output-dir",
                str(out),
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(proc.stdout)
        assert payload["status"] == "dry_run_ok"
        assert "artifact_paths" not in payload
        assert not out.exists()
