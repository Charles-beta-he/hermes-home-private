#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("project_shared_canvas_state.py")


def load_module():
    spec = importlib.util.spec_from_file_location("project_shared_canvas_state", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load projector module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class SharedCanvasProjectorTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        self.state = {
            "schema_version": "shared_canvas_state.v1",
            "revision": 3,
            "nodes": [
                {
                    "id": "goal-1",
                    "kind": "goal",
                    "status": "confirmed",
                    "owner": "shared",
                    "revision": 3,
                    "summary": "Ship governed Canvas projection",
                    "source_refs": ["spec.md"],
                    "evidence_refs": ["test.log"],
                    "authority": "joint_review",
                },
                {
                    "id": "task-1",
                    "kind": "task",
                    "status": "in_progress",
                    "owner": "agent:hermes",
                    "revision": 2,
                    "summary": "Implement deterministic projector",
                    "source_refs": [],
                    "evidence_refs": [],
                    "authority": "agent_writable",
                },
            ],
            "edges": [
                {
                    "id": "edge-1",
                    "kind": "produces",
                    "from": "task-1",
                    "to": "goal-1",
                    "label": "contributes to",
                }
            ],
        }

    def test_projection_is_deterministic_and_json_canvas_compatible(self):
        first = self.module.project_state(self.state)
        second = self.module.project_state(json.loads(json.dumps(self.state)))

        self.assertEqual(first, second)
        self.assertEqual(set(first), {"nodes", "edges"})
        self.assertEqual([node["id"] for node in first["nodes"]], ["goal-1", "task-1"])
        self.assertEqual(first["edges"][0]["fromNode"], "task-1")
        self.assertEqual(first["edges"][0]["toNode"], "goal-1")
        self.assertIn("status: confirmed", first["nodes"][0]["text"])
        self.assertIn("authority: joint_review", first["nodes"][0]["text"])

    def test_duplicate_node_id_is_rejected(self):
        self.state["nodes"].append(dict(self.state["nodes"][0]))

        with self.assertRaisesRegex(ValueError, "duplicate node id"):
            self.module.project_state(self.state)

    def test_edge_to_missing_node_is_rejected(self):
        self.state["edges"][0]["to"] = "missing"

        with self.assertRaisesRegex(ValueError, "unknown endpoint"):
            self.module.project_state(self.state)

    def test_cli_writes_canvas_and_hash_receipt_without_execution_fields(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "state.json"
            canvas = root / "state.canvas"
            receipt = root / "receipt.json"
            source.write_text(json.dumps(self.state), encoding="utf-8")

            rc = self.module.main([str(source), str(canvas), "--receipt", str(receipt)])

            self.assertEqual(rc, 0)
            projected = json.loads(canvas.read_text(encoding="utf-8"))
            proof = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(proof["schema_version"], "shared_canvas_projection_receipt.v1")
            self.assertEqual(proof["source_revision"], 3)
            self.assertEqual(proof["node_count"], 2)
            self.assertEqual(proof["edge_count"], 1)
            self.assertEqual(len(proof["source_sha256"]), 64)
            self.assertEqual(len(proof["canvas_sha256"]), 64)
            self.assertNotIn("command", json.dumps(projected).lower())
            self.assertNotIn("side_effect", json.dumps(projected).lower())


if __name__ == "__main__":
    unittest.main()
