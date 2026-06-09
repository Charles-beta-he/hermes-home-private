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

    def test_worker_context_default_includes_agent_card_context(self):
        old = os.environ.pop("HERMES_ENABLE_AGENT_CARD_CONTEXT", None)
        try:
            ctx = controller.build_worker_context(
                {"id": "t_test", "title": "dispatch workflow", "iceberg_scope": "control_plane_taskpool"},
                "g1",
                profile={"agent_card_profile": "workflow"},
            )
            self.assertIn("AGENT CARD CONTEXT", ctx)
            self.assertIn("do not expand permissions", ctx)
        finally:
            if old is not None:
                os.environ["HERMES_ENABLE_AGENT_CARD_CONTEXT"] = old

    def test_worker_context_escape_hatch_excludes_agent_card_context(self):
        old = os.environ.get("HERMES_ENABLE_AGENT_CARD_CONTEXT")
        os.environ["HERMES_ENABLE_AGENT_CARD_CONTEXT"] = "off"
        try:
            ctx = controller.build_worker_context(
                {"id": "t_test", "title": "dispatch workflow", "iceberg_scope": "control_plane_taskpool"},
                "g1",
                profile={"agent_card_profile": "workflow"},
            )
            self.assertNotIn("AGENT CARD CONTEXT", ctx)
        finally:
            if old is None:
                os.environ.pop("HERMES_ENABLE_AGENT_CARD_CONTEXT", None)
            else:
                os.environ["HERMES_ENABLE_AGENT_CARD_CONTEXT"] = old

    def test_routing_decision_default_is_apply_with_escape_hatches(self):
        old_mode = os.environ.pop("HERMES_AGENT_CARD_ROUTING_MODE", None)
        old_short = os.environ.pop("HERMES_AGENT_CARD_ROUTING", None)
        try:
            result = runtime.routing_decision(
                {"iceberg_scope": "control_plane_taskpool", "title": "dispatch workflow"},
                self.sample_cards(),
            )
            self.assertEqual(result["mode"], "apply")
            self.assertTrue(result["applies"])
            os.environ["HERMES_AGENT_CARD_ROUTING_MODE"] = "shadow"
            shadow = runtime.routing_decision(
                {"iceberg_scope": "control_plane_taskpool", "title": "dispatch workflow"},
                self.sample_cards(),
            )
            self.assertEqual(shadow["mode"], "shadow")
            self.assertFalse(shadow["applies"])
        finally:
            if old_mode is None:
                os.environ.pop("HERMES_AGENT_CARD_ROUTING_MODE", None)
            else:
                os.environ["HERMES_AGENT_CARD_ROUTING_MODE"] = old_mode
            if old_short is None:
                os.environ.pop("HERMES_AGENT_CARD_ROUTING", None)
            else:
                os.environ["HERMES_AGENT_CARD_ROUTING"] = old_short

    def test_profile_provider_filter_drops_unavailable_gemini(self):
        controller._PROFILE_PROVIDER_STATUS_CACHE.clear()
        controller._PROFILE_PROVIDER_STATUS_CACHE["workflow"] = {
            "profile": "workflow",
            "doctor_ok": True,
            "openai_codex": True,
            "google_gemini": False,
        }
        chain = [
            ("gemini-3-flash-preview", "google-gemini-cli", 15, 300),
            ("gpt-5.5", "openai-codex", 15, 360),
            ("deepseek-v4-flash", "deepseek", 15, 300),
        ]
        filtered, dropped = controller._filter_model_chain_for_worker_profile(chain, "workflow")
        self.assertNotIn("google-gemini-cli", [entry[1] for entry in filtered])
        self.assertIn("openai-codex", [entry[1] for entry in filtered])
        self.assertEqual(dropped[0]["provider"], "google-gemini-cli")

    def test_routing_decision_shadow_recommends_without_applying(self):
        result = runtime.routing_decision(
            {"iceberg_scope": "control_plane_taskpool", "title": "dispatch workflow", "assignee": "brain-mirror"},
            self.sample_cards(),
            mode="shadow",
            current_profile="brain-mirror",
        )
        self.assertEqual(result["chosen_profile"], "workflow")
        self.assertFalse(result["applies"])
        self.assertEqual(result["mode"], "shadow")

    def test_routing_decision_apply_sets_apply_flag_but_does_not_mutate_task(self):
        task = {"iceberg_scope": "visual_ingest_runtime", "title": "Rokid 图片"}
        result = runtime.routing_decision(task, self.sample_cards(), mode="apply")
        self.assertEqual(result["chosen_profile"], "media")
        self.assertTrue(result["applies"])
        self.assertNotIn("assignee", task)

    def test_routing_decision_skips_placeholder_profiles(self):
        cards = self.sample_cards()
        cards["runtime_profiles"]["personal"] = {
            "status": "profile_dir_only_not_kanban_assignee", "role": "p", "goal": "g",
            "observation": ["o"], "memory": ["m"], "planning": "p", "tools": ["t"],
            "actions": ["a"], "policy": ["p"], "evaluation": ["e"],
            "collaboration": ["c"], "escalation": "e",
        }
        cards["architecture_domains"]["control_plane_taskpool"]["recommended_runtime_profiles"] = ["personal", "workflow"]
        result = runtime.routing_decision({"iceberg_scope": "control_plane_taskpool"}, cards, mode="apply")
        self.assertEqual(result["chosen_profile"], "workflow")
        self.assertTrue(result["applies"])

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
    def test_multimodel_conductor_default_apply_with_escape_hatch(self):
        old_mode = os.environ.pop("HERMES_MULTIMODEL_CONDUCTOR_MODE", None)
        old_short = os.environ.pop("HERMES_MULTIMODEL_CONDUCTOR", None)
        try:
            self.assertEqual(controller.multimodel_conductor_mode(), "apply")
            os.environ["HERMES_MULTIMODEL_CONDUCTOR_MODE"] = "off"
            self.assertEqual(controller.multimodel_conductor_mode(), "off")
            skipped = controller.run_multimodel_conductor({"title": "x"}, "output", {}, mode="off")
            self.assertEqual(skipped["status"], "skipped")
            self.assertEqual(skipped["authority"], "advisory_only_no_lifecycle_or_write_authority")
        finally:
            if old_mode is None:
                os.environ.pop("HERMES_MULTIMODEL_CONDUCTOR_MODE", None)
            else:
                os.environ["HERMES_MULTIMODEL_CONDUCTOR_MODE"] = old_mode
            if old_short is None:
                os.environ.pop("HERMES_MULTIMODEL_CONDUCTOR", None)
            else:
                os.environ["HERMES_MULTIMODEL_CONDUCTOR"] = old_short

    def test_multimodel_conductor_attaches_advisory_packet(self):
        original = getattr(controller, "verify_with_models")
        try:
            setattr(controller, "verify_with_models", lambda title, output, profile: {
                "passed": True,
                "verified": 3,
                "models_checked": 4,
                "errors": 0,
                "issues": [],
                "details": [{"model": "fake", "verified": True}],
                "model_errors": [],
            })
            packet = controller.run_multimodel_conductor(
                {"title": "dispatch workflow"},
                "worker output with PROOF_JSON",
                {"display_name": "Hermes"},
                worker_profile_name="workflow",
            )
            self.assertEqual(packet["status"], "certified")
            self.assertTrue(packet["passed"])
            self.assertEqual(packet["verified"], 3)
            self.assertEqual(packet["profile"], "workflow")
            self.assertEqual(packet["authority"], "advisory_only_no_lifecycle_or_write_authority")
        finally:
            setattr(controller, "verify_with_models", original)

    def test_worker_context_agent_card_prompt_delta_stays_bounded(self):
        task = {"id": "t_test", "title": "dispatch workflow", "iceberg_scope": "control_plane_taskpool"}
        old = os.environ.get("HERMES_ENABLE_AGENT_CARD_CONTEXT")
        try:
            os.environ["HERMES_ENABLE_AGENT_CARD_CONTEXT"] = "off"
            off = controller.build_worker_context(task, "g1", profile={"agent_card_profile": "workflow"})
            os.environ.pop("HERMES_ENABLE_AGENT_CARD_CONTEXT", None)
            on = controller.build_worker_context(task, "g1", profile={"agent_card_profile": "workflow"})
            self.assertIn("AGENT CARD CONTEXT", on)
            self.assertLessEqual(len(on) - len(off), 2200)
            self.assertLessEqual(len(on), 8000)
        finally:
            if old is None:
                os.environ.pop("HERMES_ENABLE_AGENT_CARD_CONTEXT", None)
            else:
                os.environ["HERMES_ENABLE_AGENT_CARD_CONTEXT"] = old


if __name__ == "__main__":
    unittest.main()
