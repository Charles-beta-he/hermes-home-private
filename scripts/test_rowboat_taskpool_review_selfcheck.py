#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import json

SCRIPT = Path(__file__).with_name("rowboat_taskpool_review_selfcheck.py")
spec = importlib.util.spec_from_file_location("rowboat_taskpool_review_selfcheck", SCRIPT)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def load_pack():
    pack_path = Path.home() / "Documents/brain/05-实践与项目/projects/hermes-self-improvement/evidence/rowboat-review-20260512/rowboat-evidence-pack.json"
    return json.loads(pack_path.read_text(encoding="utf-8"))


def test_current_rowboat_pack_passes_advisory_selfcheck():
    result = mod.check_pack(load_pack())
    assert result["ok"] is True
    assert result["status"] == "PASS"
    assert result["failures"] == []
    assert result["evidence_count"] >= 18
    assert result["claim_count"] >= 5
    assert "not a replacement for target-bound 4-model ratification" in result["boundary"]


def test_selfcheck_rejects_unknown_claim_evidence_reference():
    pack = load_pack()
    pack["claims"][0]["evidence"] = ["E-DOES-NOT-EXIST"]
    result = mod.check_pack(pack)
    assert result["ok"] is False
    assert any("claim_references_unknown_evidence:C-001->E-DOES-NOT-EXIST" == item for item in result["failures"])


def test_selfcheck_requires_reject_wholesale_boundary():
    pack = load_pack()
    pack["recommendations"] = [r for r in pack["recommendations"] if r.get("id") != "R-REJECT-1"]
    result = mod.check_pack(pack)
    assert result["ok"] is False
    assert any("missing_recommendation_ids:R-REJECT-1" == item for item in result["failures"])
    assert any("missing_reject_wholesale_decision" == item for item in result["failures"])
