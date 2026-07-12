#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).with_name("compound_loop_preflight.py")
spec = importlib.util.spec_from_file_location("compound_loop_preflight", SCRIPT)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_contract_template_passes_without_false_secret_warning() -> None:
    text = Path("/Users/charles/.hermes/skills/autonomous-ai-agents/templates/compound-agent-loop-contract.yaml.md").read_text()
    result = mod.scan(text)
    assert result["status"] == "PASS"
    assert result["missing"] == []
    assert result["warnings"] == {}


def test_missing_fields_fail() -> None:
    result = mod.scan("goal: do a thing\n")
    assert result["status"] == "FAIL"
    assert "acceptance" in result["missing"]
    assert "verifier" in result["missing"]


def test_dangerous_open_secret_warns() -> None:
    text = """
    goal: x
    acceptance: y
    budget: max_turns 1
    maker: executor
    verifier: reviewer
    evidence: command:
    state_read: context_read
    state_write: writeback
    authority_gates: gate
    closure: pass | warn | fail | blocked
    api_key is allowed to be stored and sent
    """
    result = mod.scan(text)
    assert result["status"] == "WARN"
    assert "secret_handling_maybe_open" in result["warnings"]


def test_claimed_bilevel_loop_requires_measurable_objective_and_outer_loop_surface() -> None:
    text = """
    compound_agent_loop:
      objective:
        goal: improve the agent loop
        success_criteria: [better output]
      budget: max_turns 2
      maker: executor
      verifier: reviewer
      evidence: command:
      state_read: context_read
      state_write: writeback
      authority_gates: gate
      closure: pass | warn | fail | blocked
      loop_type: bilevel
    """
    result = mod.scan(text)
    assert result["status"] == "FAIL"
    assert "measurable_objective" in result["missing"]
    assert "outer_loop_change_surface" in result["missing"]


def test_complete_bilevel_loop_contract_passes_without_authority_expansion() -> None:
    text = """
    compound_agent_loop:
      source:
        claims_not_proven: []
      objective:
        goal: improve inner-loop search
        success_criteria: [benchmark beats baseline comparator]
        measurable_objective:
          metric: validation_loss
          benchmark: fixed_5_minute_run
          comparator: inner_loop_baseline
      budget: max_turns 2
      maker: executor
      verifier: reviewer
      evidence: command:
      state_read: context_read
      context_read:
        meta_loop_input_boundary:
          allowed: [code, traces, experiment_ledger]
      state_write: writeback
      outer_loop:
        responsibility: change search mechanism, not task execution
        outer_loop_change_surface: prompt_strategy
        mechanism_change_surface: exploration_policy
        no_authority_expansion: true
      inner_loop:
        responsibility: run bounded experiments
      authority_gates: gate
      closure: pass | warn | fail | blocked
    """
    result = mod.scan(text)
    assert result["status"] == "PASS"
    assert result["missing"] == []
    assert result["warnings"] == {}


if __name__ == "__main__":
    test_contract_template_passes_without_false_secret_warning()
    test_missing_fields_fail()
    test_dangerous_open_secret_warns()
    test_claimed_bilevel_loop_requires_measurable_objective_and_outer_loop_surface()
    test_complete_bilevel_loop_contract_passes_without_authority_expansion()
    print("PASS")
