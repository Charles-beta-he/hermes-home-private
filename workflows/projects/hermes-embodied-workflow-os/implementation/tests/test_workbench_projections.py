import ast
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hewos_core.ledger import EvidenceLedger
from hewos_core.projections import (
    action_intent_projection,
    build_dashboard_projection,
    capability_projection,
    evidence_entry_projection,
    task_graph_projection,
)


class ProjectionFixtureTest(unittest.TestCase):
    def test_builds_dashboard_from_registry_and_ledger_replay(self):
        capabilities = [
            {
                "capability_id": "cap.web.text_observation",
                "actor_id": "actor.web.mock",
                "adapter_id": "adapter.web.mock",
                "capability_type": "observation",
                "risk_class": "none",
                "dry_run_default": True,
            },
            {
                "capability_id": "cap.robot.dry_run",
                "actor_id": "actor.robot.mock",
                "adapter_id": "adapter.robot.mock",
                "capability_type": "physical_action",
                "risk_class": "physical_action",
                "dry_run_default": True,
            },
        ]
        ledger = EvidenceLedger()
        entry = ledger.append(
            kind="observation",
            subject_id="obs.1",
            source="adapter.web.mock",
            claims=[{"claim": "part-a visible"}],
            evidence_refs=["sha256:raw-1"],
            payload={"session_id": "session.1", "derived_facts": {"visible_parts": ["part-a"]}},
        )

        dashboard = build_dashboard_projection(capabilities, ledger.entries(), pending_action_intents=[{"risk_level": "physical_action"}])

        self.assertEqual(dashboard["capability_count"], 2)
        self.assertEqual(dashboard["ledger_entry_count"], 1)
        self.assertEqual(dashboard["pending_action_intents_by_risk"], {"physical_action": 1})
        self.assertEqual(dashboard["world_state"]["visible_parts"], ["part-a"])
        self.assertEqual(evidence_entry_projection(entry)["redaction_status"], "checked")

    def test_projection_shapes_are_workbench_safe(self):
        capability = capability_projection({
            "capability_id": "cap.web.text_observation",
            "actor_id": "actor.web.mock",
            "adapter_id": "adapter.web.mock",
            "capability_type": "observation",
            "risk_class": "none",
            "dry_run_default": True,
        })
        task_graph = task_graph_projection(
            "tg.example",
            "Install shelf bracket",
            nodes=[{"id": "step.1", "label": "identify parts", "state": "pending"}],
            edges=[],
        )
        action = action_intent_projection({
            "intent_id": "ai.example",
            "capability_id": "cap.robot.dry_run",
            "risk_level": "physical_action",
            "preview": "dry-run only",
            "required_gates": ["SafetyGate", "ExternalControlGate", "OnsiteHumanGate"],
            "evidence_refs": ["ev.1"],
        })

        self.assertEqual(capability["status"], "simulated")
        self.assertEqual(task_graph["world_state_ref"], "replay:latest")
        self.assertEqual(action["status"], "blocked")

    def test_projection_module_has_no_external_side_effect_calls_or_hardware_imports(self):
        module = ROOT / "hewos_core" / "projections.py"
        tree = ast.parse(module.read_text())
        forbidden_imports = {"requests", "subprocess", "socket", "serial", "rospy", "rclpy", "paho", "mqtt"}
        forbidden_calls = {"execute", "send", "deploy", "push", "publish", "taskpool", "dispatch"}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = {alias.name.split(".")[0] for alias in node.names}
                self.assertTrue(imported.isdisjoint(forbidden_imports), imported)
            if isinstance(node, ast.ImportFrom) and node.module:
                self.assertNotIn(node.module.split(".")[0], forbidden_imports)
            if isinstance(node, ast.Call):
                name = ""
                if isinstance(node.func, ast.Name):
                    name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    name = node.func.attr
                self.assertNotIn(name, forbidden_calls)


if __name__ == "__main__":
    unittest.main()
