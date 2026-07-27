import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent
sys.path.insert(0, str(ROOT))

from cocos_work_package_adapter import compile_cocos_integration


class CocosWorkflowAssetsTests(unittest.TestCase):
    def setUp(self):
        self.package = json.loads(
            (PROJECT / "evidence" / "sample-work-package.json").read_text(encoding="utf-8")
        )
        self.profile = json.loads(
            (PROJECT / "runtime" / "cocos" / "cocos-integration-profile.json").read_text(
                encoding="utf-8"
            )
        )
        self.packet = compile_cocos_integration(self.package, self.profile)

    def test_packet_matches_machine_readable_schema_contract(self):
        schema = json.loads(
            (PROJECT / "runtime" / "cocos" / "cocos-integration-packet.schema.json").read_text(
                encoding="utf-8"
            )
        )
        required = set(schema["required"])
        self.assertEqual(required - set(self.packet), set())
        self.assertEqual(schema["properties"]["closure_state"]["const"], self.packet["closure_state"])
        self.assertEqual(schema["properties"]["candidate_only"]["const"], True)
        authority_required = set(schema["properties"]["authority"]["required"])
        self.assertEqual(authority_required, set(self.packet["authority"]))
        for field in authority_required:
            self.assertEqual(schema["properties"]["authority"]["properties"][field]["const"], False)

    def test_platform_port_contract_keeps_gameplay_and_release_out(self):
        contract = json.loads(
            (PROJECT / "runtime" / "cocos" / "platform-port-contract.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(contract["owner"], "PlatformAdapter")
        self.assertEqual(
            set(contract["operations"]),
            {"lifecycle", "storage", "share", "login", "rewarded_ad", "system_info"},
        )
        self.assertIn("win_condition", contract["forbidden_ownership"])
        self.assertIn("publish", contract["forbidden_ownership"])
        self.assertFalse(contract["authority"]["may_invoke_platform_sdk"])

    def test_devtools_handoff_template_is_blocked_and_secret_free(self):
        handoff = json.loads(
            (PROJECT / "08-shipping" / "devtools-handoff-template.json").read_text(encoding="utf-8")
        )
        rendered = json.dumps(handoff, ensure_ascii=False).lower()
        self.assertEqual(handoff["status"], "blocked")
        self.assertNotIn("app_id", handoff)
        self.assertFalse(handoff["authority"]["may_invoke_devtools"])
        self.assertFalse(handoff["authority"]["may_submit_platform"])
        self.assertNotIn("secret", rendered)
        self.assertNotIn("token", rendered)
        self.assertNotIn("password", rendered)

    def test_capability_graph_places_cocos_before_runtime_and_platform(self):
        graph = json.loads((PROJECT / "capability-graph.json").read_text(encoding="utf-8"))
        self.assertIn("cocos_integration_planned", graph["closure_states"])
        self.assertIn("cocos_candidate_materialized", graph["closure_states"])
        nodes = {node["id"]: node for node in graph["nodes"]}
        self.assertEqual(nodes["cocos-integration"]["depends_on"], ["work-package-compiler"])
        self.assertEqual(nodes["implementation"]["depends_on"], ["gameplay-runtime-core"])
        self.assertEqual(nodes["gameplay-runtime-core"]["depends_on"], ["cocos-integration"])
        self.assertEqual(nodes["cocos-project-generator"]["depends_on"], ["gameplay-runtime-core"])
        self.assertEqual(nodes["cocos-build-preflight"]["depends_on"], ["cocos-project-generator"])
        self.assertIn("authority-closed", nodes["cocos-integration"]["gates"])
        self.assertEqual(nodes["cocos-creator-build"]["side_effects"], "local_process_requires_exact_authority")
        self.assertEqual(nodes["cocos-creator-build"]["depends_on"], ["cocos-build-preflight"])
        self.assertEqual(nodes["devtools-handoff-verifier"]["depends_on"], ["cocos-creator-build"])
        self.assertEqual(nodes["platform-adapter"]["depends_on"], ["devtools-handoff-verifier"])

    def test_workflow_state_does_not_promote_runtime_or_shipping(self):
        state = (PROJECT / "workflow-state.yaml.md").read_text(encoding="utf-8")
        self.assertIn("creator_project_candidate_materialized", state)
        self.assertIn("Creator import/build not executed", state)
        self.assertIn("build preflight: blocked with no command", state)
        self.assertIn("status: blocked", state)
        self.assertIn("authority: no platform submission or publish", state)


if __name__ == "__main__":
    unittest.main()
