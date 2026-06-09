#!/usr/bin/env python3
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runtime = load_module("agent_cards_runtime", SCRIPT_DIR / "agent_cards_runtime.py")
controller = load_module("agent_team_controller", SCRIPT_DIR / "agent_team_controller.py")


class AgentCardsRuntimeTest(unittest.TestCase):
    def sample_cards(self):
        return {
            "runtime_profiles": {
                "brain-mirror": {"role": "Brain", "goal": "Mirror", "observation": ["brain"], "memory": ["notes"], "planning": "plan", "tools": ["kanban"], "actions": ["mirror"], "policy": ["gate"], "evaluation": ["selfcheck"], "collaboration": ["human"], "escalation": "review"},
                "workflow": {"role": "Workflow", "goal": "Orchestrate", "observation": ["events"], "memory": ["ledger"], "planning": "state machine", "tools": ["kanban"], "actions": ["route"], "policy": ["event gate"], "evaluation": ["dry-run"], "collaboration": ["taskpool"], "escalation": "human"},
                "media": {"role": "Media", "goal": "Visual", "observation": ["image"], "memory": ["artifact"], "planning": "vision", "tools": ["vision"], "actions": ["analyze"], "policy": ["privacy"], "evaluation": ["readback"], "collaboration": ["workflow"], "escalation": "human"},
            },
            "architecture_domains": {
                "control_plane_taskpool": {"role": "Taskpool", "goal": "Dispatch", "observation": ["kanban"], "memory": ["runs"], "planning": "lifecycle", "tools": ["hermes kanban"], "actions": ["dispatch"], "policy": ["no fake proof"], "evaluation": ["coverage"], "collaboration": ["brain"], "escalation": "review", "recommended_runtime_profiles": ["workflow", "brain-mirror"]},
                "visual_ingest_runtime": {"role": "Visual", "goal": "Observe", "observation": ["images"], "memory": ["artifacts"], "planning": "classify", "tools": ["vision"], "actions": ["analyze"], "policy": ["privacy"], "evaluation": ["evidence"], "collaboration": ["media"], "escalation": "human", "recommended_runtime_profiles": ["media", "workflow"]},
            },
        }

    def test_recommend_profiles_prefers_domain_card_profiles(self):
        result = runtime.recommend_profiles(
            {"iceberg_scope": "control_plane_taskpool", "title": "dispatch workflow"},
            self.sample_cards(),
        )
        self.assertEqual(result["status"], "recommendation_only")
        self.assertEqual(result["recommended_profiles"][0], "workflow")
        self.assertIn("No task assignment", result["boundary"])

    def test_render_context_is_default_off(self):
        ctx = runtime.render_agent_card_context(
            {"iceberg_scope": "control_plane_taskpool", "assignee": "workflow"},
            cards=self.sample_cards(),
            enabled=False,
        )
        self.assertEqual(ctx, "")

    def test_render_context_when_enabled_has_no_authority_expansion(self):
        ctx = runtime.render_agent_card_context(
            {"iceberg_scope": "control_plane_taskpool", "assignee": "workflow"},
            profile="workflow",
            cards=self.sample_cards(),
            enabled=True,
        )
        self.assertIn("AGENT CARD CONTEXT", ctx)
        self.assertIn("do not expand permissions", ctx)
        self.assertIn("ARCHITECTURE_DOMAIN: control_plane_taskpool", ctx)

    def test_worker_context_default_excludes_agent_card_context(self):
        old = os.environ.pop("HERMES_ENABLE_AGENT_CARD_CONTEXT", None)
        try:
            ctx = controller.build_worker_context(
                {"id": "t_test", "title": "dispatch workflow", "iceberg_scope": "control_plane_taskpool"},
                "g1",
                profile={"name": "workflow"},
            )
            self.assertNotIn("AGENT CARD CONTEXT", ctx)
        finally:
            if old is not None:
                os.environ["HERMES_ENABLE_AGENT_CARD_CONTEXT"] = old

    def test_worker_context_opt_in_includes_agent_card_context(self):
        old = os.environ.get("HERMES_ENABLE_AGENT_CARD_CONTEXT")
        os.environ["HERMES_ENABLE_AGENT_CARD_CONTEXT"] = "1"
        try:
            ctx = controller.build_worker_context(
                {"id": "t_test", "title": "dispatch workflow", "iceberg_scope": "control_plane_taskpool"},
                "g1",
                profile={"name": "workflow"},
            )
            self.assertIn("AGENT CARD", ctx)
            self.assertIn("not extra authority", ctx)
        finally:
            if old is None:
                os.environ.pop("HERMES_ENABLE_AGENT_CARD_CONTEXT", None)
            else:
                os.environ["HERMES_ENABLE_AGENT_CARD_CONTEXT"] = old


if __name__ == "__main__":
    unittest.main()
