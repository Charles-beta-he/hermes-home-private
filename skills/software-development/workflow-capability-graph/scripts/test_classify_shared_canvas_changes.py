#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parent


def load_module(name: str):
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class SharedCanvasChangeClassifierTests(unittest.TestCase):
    def setUp(self):
        self.projector = load_module("project_shared_canvas_state")
        self.classifier = load_module("classify_shared_canvas_changes")
        state = {
            "schema_version": "shared_canvas_state.v1",
            "revision": 4,
            "nodes": [
                {
                    "id": "goal-1",
                    "kind": "goal",
                    "status": "confirmed",
                    "owner": "shared",
                    "revision": 4,
                    "summary": "Ship governed Canvas",
                    "source_refs": [],
                    "evidence_refs": [],
                    "authority": "joint_review",
                },
                {
                    "id": "task-1",
                    "kind": "task",
                    "status": "in_progress",
                    "owner": "agent:hermes",
                    "revision": 2,
                    "summary": "Implement classifier",
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
                    "label": "contributes",
                }
            ],
        }
        self.baseline = self.projector.project_state(state)

    def test_layout_change_is_advisory_and_never_applied(self):
        edited = copy.deepcopy(self.baseline)
        edited["nodes"][0]["x"] += 120
        edited["nodes"][0]["color"] = "2"

        packet = self.classifier.classify_changes(self.baseline, edited, source_revision=4)

        self.assertEqual(packet["intent_count"], 1)
        intent = packet["intents"][0]
        self.assertEqual(intent["kind"], "layout_change")
        self.assertEqual(intent["target_id"], "goal-1")
        self.assertFalse(intent["requires_human_review"])
        self.assertFalse(packet["apply_performed"])
        self.assertFalse(packet["external_side_effects"])

    def test_text_change_becomes_semantic_edit_request(self):
        edited = copy.deepcopy(self.baseline)
        edited["nodes"][0]["text"] = edited["nodes"][0]["text"].replace(
            "Ship governed Canvas", "Ship unreviewed Canvas"
        )

        packet = self.classifier.classify_changes(self.baseline, edited, source_revision=4)

        intent = packet["intents"][0]
        self.assertEqual(intent["kind"], "semantic_edit_request")
        self.assertTrue(intent["requires_human_review"])
        self.assertEqual(len(intent["before_sha256"]), 64)
        self.assertEqual(len(intent["after_sha256"]), 64)

    def test_node_removal_is_soft_delete_request(self):
        edited = copy.deepcopy(self.baseline)
        edited["nodes"] = [node for node in edited["nodes"] if node["id"] != "task-1"]
        edited["edges"] = []

        packet = self.classifier.classify_changes(self.baseline, edited, source_revision=4)

        delete = next(intent for intent in packet["intents"] if intent["kind"] == "node_delete_request")
        self.assertEqual(delete["target_id"], "task-1")
        self.assertTrue(delete["requires_human_review"])
        self.assertFalse(delete["destructive_action_performed"])

    def test_added_edge_is_relationship_add_request(self):
        edited = copy.deepcopy(self.baseline)
        edited["edges"].append(
            {
                "id": "edge-2",
                "fromNode": "goal-1",
                "toNode": "task-1",
                "label": "depends_on",
            }
        )

        packet = self.classifier.classify_changes(self.baseline, edited, source_revision=4)

        added = next(intent for intent in packet["intents"] if intent["kind"] == "relationship_add_request")
        self.assertEqual(added["target_id"], "edge-2")
        self.assertTrue(added["requires_human_review"])

    def test_unknown_edge_endpoint_is_rejected(self):
        edited = copy.deepcopy(self.baseline)
        edited["edges"].append(
            {"id": "bad", "fromNode": "goal-1", "toNode": "missing", "label": "bad"}
        )

        with self.assertRaisesRegex(ValueError, "unknown endpoint"):
            self.classifier.classify_changes(self.baseline, edited, source_revision=4)

    def test_cli_writes_change_intent_packet_only(self):
        edited = copy.deepcopy(self.baseline)
        edited["nodes"][1]["y"] += 50
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            baseline = root / "baseline.canvas"
            changed = root / "changed.canvas"
            output = root / "intents.json"
            baseline.write_text(json.dumps(self.baseline), encoding="utf-8")
            changed.write_text(json.dumps(edited), encoding="utf-8")

            rc = self.classifier.main(
                [str(baseline), str(changed), str(output), "--source-revision", "4"]
            )

            self.assertEqual(rc, 0)
            packet = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(packet["schema_version"], "shared_canvas_change_intents.v1")
            self.assertEqual(packet["source_revision"], 4)
            self.assertFalse(packet["apply_performed"])
            self.assertFalse(packet["external_side_effects"])


if __name__ == "__main__":
    unittest.main()
