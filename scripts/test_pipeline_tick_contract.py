#!/usr/bin/env python3
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

SCRIPTS = Path.home() / ".hermes" / "scripts"
sys.path.insert(0, str(SCRIPTS))
SCRIPT = SCRIPTS / "pipeline_tick.py"


def load_module():
    spec = importlib.util.spec_from_file_location("pipeline_tick_under_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return cast(Any, module)


class PipelineTickContractTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tick = load_module()
        import envelope_bus as bus
        self.bus = bus
        self.bus.DB_PATH = Path(self.tmp.name) / "envelope_bus.db"
        self.bus.ESCAPE_ACK_PATH = Path(self.tmp.name) / "escape_ack.json"
        self.tick.create = self.bus.create
        self.tick.list_by_status = self.bus.list_by_status
        self.tick.append_trace = self.bus.append_trace
        self.tick.stats = self.bus.stats
        self.tick.check_timeout = self.bus.check_timeout
        self.tick.human_escape_check = self.bus.human_escape_check

    def tearDown(self):
        self.tmp.cleanup()

    def test_build_payload_preserves_harness_contract_fields(self):
        payload = self.tick.build_payload_from_task({
            "id": "brain-1",
            "title": "Implement thing",
            "project": "demo-project",
            "priority": "P1",
            "acceptance_criteria": ["test passes"],
            "evidence_refs": ["command:pytest"],
            "non_goals": ["do not change API"],
            "red_lines": ["no secrets"],
            "workflow_contract": {"proof": "PROOF_JSON"},
        }, "P1")

        self.assertEqual(payload["acceptance_criteria"], ["test passes"])
        self.assertEqual(payload["acceptance_evidence"], ["command:pytest"])
        self.assertEqual(payload["non_goals"], ["do not change API"])
        self.assertEqual(payload["red_lines"], ["no secrets"])
        self.assertEqual(payload["workflow_contract"], {"proof": "PROOF_JSON"})
        self.assertEqual(payload["harness_contract"]["acceptance"]["observable_results"], ["test passes"])
        self.assertEqual(payload["harness_contract"]["evidence"]["minimum_done_proof"], ["command:pytest"])
        self.assertEqual(payload["harness_contract"]["gates"]["risk_level"], "high")

    def test_sync_envelopes_carries_contract_into_created_envelope(self):
        task = {
            "id": "brain-2",
            "title": "Contracted task",
            "project": "demo-project",
            "priority": "P2",
            "dispatchable": True,
            "acceptance_criteria": ["artifact exists"],
            "evidence_refs": ["file:/tmp/artifact"],
        }
        with patch.object(self.tick, "get_dispatchable_tasks", return_value=[task]):
            created = self.tick.sync_envelopes()

        self.assertEqual(created, 1)
        env = self.bus.list_by_status("PENDING")[0]
        payload = json.loads(env["payload"])
        self.assertEqual(payload["acceptance_criteria"], ["artifact exists"])
        self.assertEqual(payload["harness_contract"]["evidence"]["minimum_done_proof"], ["file:/tmp/artifact"])


if __name__ == "__main__":
    unittest.main()
