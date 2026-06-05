#!/usr/bin/env python3
"""Focused regression tests for taskpool handoff role-boundary contracts."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPT = Path.home() / ".hermes" / "scripts" / "brain_task_orchestrator.py"


def load_module():
    spec = importlib.util.spec_from_file_location("brain_task_orchestrator_handoff_under_test", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def make_task(mod):
    return mod.Task(
        path=mod.VAULT / "05-实践与项目" / "tasks" / "task-123.md",
        fm={
            "project": "hermes-agent",
            "claim_expires_at": "2099-01-01T00:00:00+00:00",
            "run_id": "run-1",
            "parallel_boundary": "agent-team-handoff-contract",
            "workspace": "/tmp/worktree",
            "workspace_isolation": "worktree",
            "acceptance_criteria": [
                "generated handoff read-back contains SSOT/controller-not-proof/feature-specific evidence contract",
                "focused pytest passes without weakening lifecycle gates",
            ],
        },
        body="# Task - Handoff contract\n",
    )


def assert_role_boundary_contract(text: str) -> None:
    assert "## Role-Boundary Evidence Contract" in text
    assert "ssot: `brain_task_orchestrator.py + kanban.db + task note task-123`" in text
    assert "controller_not_proof" in text
    assert "claim state, batch metadata, proof hashes, selfcheck, and proof-check prove control-plane integrity only" in text
    assert "executor_proof_required" in text
    assert "feature-specific implementation evidence" in text
    assert "parallel_boundary: `agent-team-handoff-contract`" in text
    assert "workspace_isolation: `worktree`" in text
    assert "stop_conditions:" in text
    assert "never force done" in text


def test_parallel_handoff_readback_contains_role_boundary_contract():
    mod = load_module()
    task = make_task(mod)
    text = mod.render_parallel_handoff(
        task,
        claim={"status": "OK", "task": "task-123"},
        boundary_info={"boundary_key": "agent-team-handoff-contract", "batch_size": 1},
        actor="hermes-parallel",
        run_id="run-1",
        batch_id="batch-1",
        batch_index=0,
    )
    assert_role_boundary_contract(text)
    assert "## Boundary Constraints" in text
    assert "## Claim Result" in text


def test_autorun_handoff_readback_contains_same_role_boundary_contract():
    mod = load_module()
    task = make_task(mod)
    text = mod.render_autorun_handoff(
        task,
        claim={"status": "OK", "task": "task-123"},
        proof_hash="sha256:abc",
        actor="hermes-autorun",
    )
    assert_role_boundary_contract(text)
    assert "Do not mark the task done from this handoff" in text
    assert "proof_evidence: `proof:sha256:abc`" in text


if __name__ == "__main__":
    test_parallel_handoff_readback_contains_role_boundary_contract()
    test_autorun_handoff_readback_contains_same_role_boundary_contract()
    print("PASS")
