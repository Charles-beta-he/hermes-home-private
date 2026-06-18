#!/usr/bin/env python3
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path.home() / ".hermes" / "scripts"
sys.path.insert(0, str(SCRIPTS))
SCRIPT = SCRIPTS / "envelope_executor.py"


def load_module():
    spec = importlib.util.spec_from_file_location("envelope_executor_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeCompleted:
    def __init__(self, stdout="", returncode=0):
        self.stdout = stdout
        self.stderr = ""
        self.returncode = returncode


class EnvelopeExecutorSafetyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.exec = load_module()
        import envelope_bus as bus
        self.bus = bus
        self.bus.DB_PATH = Path(self.tmp.name) / "envelope_bus.db"
        self.bus.ESCAPE_ACK_PATH = Path(self.tmp.name) / "escape_ack.json"
        # Rebind imported functions that were copied at import time.
        self.exec.get = self.bus.get
        self.exec.update_status = self.bus.update_status
        self.exec.append_trace = self.bus.append_trace
        self.exec.list_by_status = self.bus.list_by_status
        self.exec.increment_retry = self.bus.increment_retry
        self.exec.human_escape_check = self.bus.human_escape_check
        self.exec.stats = self.bus.stats
        self.eid = self.bus.create(
            type="TASK",
            title="safe task",
            payload={"brain_id": "brain-1"},
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_worker_without_proof_does_not_mark_done(self):
        with patch.object(self.exec, "can_continue", return_value=(False, 0)):
            with patch.object(self.exec, "run_worker_command", return_value=FakeCompleted("completed but forgot proof")):
                result = self.exec.delegate_to_worker(self.exec.get(self.eid))

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["reason"], "missing_proof")
        self.assertEqual(self.exec.get(self.eid)["status"], "FAILED")

    def test_invalid_proof_does_not_mark_done(self):
        with patch.object(self.exec, "can_continue", return_value=(False, 0)):
            with patch.object(self.exec, "run_worker_command", return_value=FakeCompleted("PROOF_JSON: {bad json}")):
                result = self.exec.delegate_to_worker(self.exec.get(self.eid))

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["reason"], "invalid_proof")
        self.assertEqual(self.exec.get(self.eid)["status"], "FAILED")

    def test_valid_proof_marks_done_with_proof_hash(self):
        output = 'work\nPROOF_JSON: {"status":"done","summary":"ok","files_changed":[],"tests_passed":1}\n'
        with patch.object(self.exec, "can_continue", return_value=(False, 0)):
            with patch.object(self.exec, "run_worker_command", return_value=FakeCompleted(output)):
                result = self.exec.delegate_to_worker(self.exec.get(self.eid))

        env = self.exec.get(self.eid)
        self.assertEqual(result["status"], "done")
        self.assertEqual(env["status"], "DONE")
        self.assertTrue(env["proof_sha"])

    def test_prompt_includes_harness_intake_contract(self):
        calls = []

        def fake_run(cmd, timeout=600, cwd=None):
            calls.append(cmd)
            output = 'work\nPROOF_JSON: {"status":"blocked","summary":"needs acceptance"}\n'
            return FakeCompleted(output)

        eid = self.bus.create(
            type="TASK",
            title="contract task",
            payload={
                "brain_id": "brain-2",
                "harness_contract": {
                    "goal": {"desired_state": "done state"},
                    "acceptance": {"observable_results": ["observable result"]},
                    "evidence": {"minimum_done_proof": ["command:pytest"]},
                },
            },
        )
        with patch.object(self.exec, "can_continue", return_value=(False, 0)):
            with patch.object(self.exec, "run_worker_command", side_effect=fake_run):
                self.exec.delegate_to_worker(self.exec.get(eid))

        prompt = calls[0][3]
        self.assertIn("HARNESS INTAKE CONTRACT", prompt)
        self.assertIn("observable result", prompt)
        self.assertIn("command:pytest", prompt)
        self.assertIn("acceptance_criteria_covered", prompt)

    def test_declared_acceptance_requires_covered_evidence(self):
        eid = self.bus.create(
            type="TASK",
            title="acceptance task",
            payload={"brain_id": "brain-3", "acceptance_criteria": ["criterion must be evidenced"]},
        )
        output = 'work\nPROOF_JSON: {"status":"done","summary":"ok","files_changed":[],"tests_passed":1}\n'
        with patch.object(self.exec, "can_continue", return_value=(False, 0)):
            with patch.object(self.exec, "run_worker_command", return_value=FakeCompleted(output)):
                result = self.exec.delegate_to_worker(self.exec.get(eid))

        self.assertEqual(result["status"], "failed")
        self.assertTrue(result["reason"].startswith("acceptance_criteria_covered_incomplete"))
        self.assertEqual(self.exec.get(eid)["status"], "FAILED")

    def test_declared_acceptance_with_covered_evidence_marks_done(self):
        eid = self.bus.create(
            type="TASK",
            title="acceptance task",
            payload={"brain_id": "brain-4", "acceptance_criteria": ["criterion must be evidenced"]},
        )
        output = (
            'work\nPROOF_JSON: {"status":"done","summary":"ok","files_changed":[],"tests_passed":1,'
            '"acceptance_criteria_covered":[{"criterion":"criterion must be evidenced","status":"covered","evidence":["command:pytest"]}]}\n'
        )
        with patch.object(self.exec, "can_continue", return_value=(False, 0)):
            with patch.object(self.exec, "run_worker_command", return_value=FakeCompleted(output)):
                result = self.exec.delegate_to_worker(self.exec.get(eid))

        self.assertEqual(result["status"], "done")
        self.assertEqual(self.exec.get(eid)["status"], "DONE")


if __name__ == "__main__":
    unittest.main()
