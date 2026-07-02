import json
import tempfile
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hewos_core.high_risk_boundaries import (
    BOUNDARY_CATALOG,
    REQUESTED_HIGH_RISK_BOUNDARIES,
    authorize_boundary_intent,
    boundary_coverage_matrix,
    validate_boundary_catalog,
)
from hewos_core.simulation_ledger import (
    append_simulation_receipt,
    read_simulation_ledger,
    rollback_simulation_receipt,
)


class HighRiskBoundaryTest(unittest.TestCase):
    def test_catalog_covers_authorized_taskpool_external_hardware_deploy_auth(self):
        result = validate_boundary_catalog(BOUNDARY_CATALOG)
        self.assertTrue(result["ok"], result)
        self.assertEqual(set(REQUESTED_HIGH_RISK_BOUNDARIES), set(BOUNDARY_CATALOG))
        matrix = boundary_coverage_matrix()
        self.assertEqual(matrix["governance_coverage_percent"], 100)
        for item in matrix["boundaries"]:
            self.assertTrue(item["governance_covered"])
            self.assertTrue(item["receipt_required"])
            self.assertTrue(item["readback_required"])
            self.assertFalse(item["executed"])
            self.assertFalse(item["token_read_allowed"])
            self.assertFalse(item["stores_secrets"])

    def test_unscoped_live_boundary_authorization_fails_closed(self):
        for boundary_id in REQUESTED_HIGH_RISK_BOUNDARIES:
            decision = authorize_boundary_intent({
                "boundary_id": boundary_id,
                "requested_action": "execute",
                "evidence_refs": ["test:evidence"],
            })
            self.assertEqual(decision["decision"], "blocked", boundary_id)
            self.assertFalse(decision["execution_enabled"])
            self.assertIn("missing_exact_target", decision["reasons"])

    def test_exact_intent_is_authorized_as_intent_only_not_live_execution(self):
        decision = authorize_boundary_intent({
            "boundary_id": "external_dispatch",
            "requested_action": "authorize_intent",
            "exact_target": "local-harness:external-dispatch-smoke",
            "payload_hash": "sha256:abc123",
            "evidence_refs": ["test:gate", "test:readback"],
            "readback_plan": "read local harness receipt",
            "rollback_plan": "delete local harness receipt by digest",
            "idempotency_key": "external-smoke-1",
        })
        self.assertEqual(decision["decision"], "authorized_intent_only")
        self.assertFalse(decision["execution_enabled"])
        self.assertEqual(decision["boundary_id"], "external_dispatch")
        self.assertTrue(decision["intent_digest"].startswith("sha256:"))

    def test_auth_boundary_never_allows_agent_secret_entry(self):
        decision = authorize_boundary_intent({
            "boundary_id": "auth_credential",
            "requested_action": "authorize_intent",
            "exact_target": "human-secret-entry:local-demo",
            "payload_hash": "sha256:authdemo",
            "evidence_refs": ["test:auth-gate"],
            "readback_plan": "read auth gate denied state",
            "rollback_plan": "remove local auth intent receipt",
            "idempotency_key": "auth-demo-1",
        })
        self.assertEqual(decision["decision"], "authorized_intent_only")
        self.assertFalse(decision["agent_may_type_secret"])
        self.assertFalse(decision["token_read_allowed"])
        self.assertFalse(decision["execution_enabled"])

    def test_simulation_ledger_append_is_idempotent_and_rollbackable(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "simulation-ledger.jsonl"
            decision = authorize_boundary_intent({
                "boundary_id": "taskpool_lifecycle",
                "requested_action": "authorize_intent",
                "exact_target": "local-ledger:task-123/status=blocked",
                "payload_hash": "sha256:taskpayload",
                "evidence_refs": ["test:taskpool"],
                "readback_plan": "read ledger row",
                "rollback_plan": "rollback receipt by id",
                "idempotency_key": "taskpool-demo-1",
            })
            first = append_simulation_receipt(path, decision)
            second = append_simulation_receipt(path, decision)
            self.assertEqual(first["receipt_id"], second["receipt_id"])
            self.assertTrue(second["idempotent_replay"])
            rows = read_simulation_ledger(path)
            self.assertEqual(len(rows), 1)
            rolled = rollback_simulation_receipt(path, first["receipt_id"])
            self.assertTrue(rolled["rolled_back"])
            self.assertEqual(read_simulation_ledger(path), [])


if __name__ == "__main__":
    unittest.main()
