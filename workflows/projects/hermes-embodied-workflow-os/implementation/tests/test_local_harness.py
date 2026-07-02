import json
import tempfile
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hewos_core.high_risk_boundaries import authorize_boundary_intent
from hewos_core.local_harness import execute_local_harness, read_harness_receipts, rollback_harness_receipt


class LocalHarnessWriteThroughTest(unittest.TestCase):
    def _decision(self, boundary_id="taskpool_lifecycle", target="local-harness:taskpool_lifecycle:disposable"):
        return authorize_boundary_intent({
            "boundary_id": boundary_id,
            "requested_action": "authorize_intent",
            "exact_target": target,
            "payload_hash": f"sha256:{boundary_id}-payload",
            "evidence_refs": ["test:harness"],
            "readback_plan": "read local harness receipt",
            "rollback_plan": "rollback local harness receipt",
            "idempotency_key": f"{boundary_id}-harness-1",
        })

    def test_harness_writes_disposable_receipt_and_readback(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            receipt = execute_local_harness(root, self._decision())
            self.assertEqual(receipt["write_class"], "local_disposable_harness")
            self.assertFalse(receipt["live_adapter_touched"])
            self.assertTrue((root / "receipts.jsonl").exists())
            rows = read_harness_receipts(root)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["receipt_id"], receipt["receipt_id"])

    def test_harness_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            decision = self._decision("external_dispatch", "local-harness:external_dispatch:disposable")
            first = execute_local_harness(root, decision)
            second = execute_local_harness(root, decision)
            self.assertEqual(first["receipt_id"], second["receipt_id"])
            self.assertTrue(second["idempotent_replay"])
            self.assertEqual(len(read_harness_receipts(root)), 1)

    def test_harness_rejects_non_local_targets_and_live_execution(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            remote = self._decision("deploy_publish", "prod:deploy:main")
            with self.assertRaises(ValueError):
                execute_local_harness(root, remote)
            live = self._decision("hardware_execution", "local-harness:hardware_execution:disposable")
            live["execution_enabled"] = True
            with self.assertRaises(ValueError):
                execute_local_harness(root, live)

    def test_harness_rollback_removes_exact_receipt_only(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            first = execute_local_harness(root, self._decision("taskpool_lifecycle", "local-harness:taskpool_lifecycle:one"))
            second = execute_local_harness(root, self._decision("auth_credential", "local-harness:auth_credential:two"))
            result = rollback_harness_receipt(root, first["receipt_id"])
            self.assertTrue(result["rolled_back"])
            rows = read_harness_receipts(root)
            self.assertEqual([r["receipt_id"] for r in rows], [second["receipt_id"]])


if __name__ == "__main__":
    unittest.main()
