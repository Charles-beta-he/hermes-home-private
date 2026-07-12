#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).with_name("workspace_projection_gate.py")
spec = importlib.util.spec_from_file_location("workspace_projection_gate", SCRIPT)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

SAMPLE = Path("/Users/charles/.hermes/skills/software-development/workflow-capability-graph/templates/workspace-projection-packet.sample.json")


def sample_packet():
    return mod.load_packet(SAMPLE)


def test_sample_passes() -> None:
    result = mod.validate(sample_packet())
    assert result["status"] == "PASS", result
    assert result["errors"] == []


def test_hidden_state_claim_fails() -> None:
    pkt = sample_packet()
    pkt["source_boundary"]["hidden_state_access"] = True
    result = mod.validate(pkt)
    assert result["status"] == "FAIL"
    assert any("hidden_state_access" in e for e in result["errors"])


def test_model_judgment_cannot_close_verified_local() -> None:
    pkt = sample_packet()
    pkt["evidence_dag"]["evidence"][0]["authority"] = "model_judgment"
    result = mod.validate(pkt)
    assert result["status"] == "FAIL"
    assert any("model-only" in e or "objective" in e for e in result["errors"])


def test_dangerous_allowed_authority_fails() -> None:
    pkt = sample_packet()
    pkt["workspace_projection"]["authority_boundary"]["allowed"].append("external_dispatch")
    result = mod.validate(pkt)
    assert result["status"] == "FAIL"
    assert any("dangerous authority" in e for e in result["errors"])


def test_missing_negative_evidence_fails() -> None:
    pkt = sample_packet()
    pkt["completion_claim_packet"]["negative_evidence"] = ["no_hidden_state_access"]
    result = mod.validate(pkt)
    assert result["status"] == "FAIL"
    assert any("negative evidence" in e for e in result["errors"])


if __name__ == "__main__":
    test_sample_passes()
    test_hidden_state_claim_fails()
    test_model_judgment_cannot_close_verified_local()
    test_dangerous_allowed_authority_fails()
    test_missing_negative_evidence_fails()
    print("PASS")
