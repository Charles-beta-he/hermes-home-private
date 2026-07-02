import tempfile
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hewos_core.ordered_live_boundaries import (
    append_external_outbox_dry_run,
    auth_human_secret_gate,
    deploy_push_preflight_record,
    hardware_safety_gate,
    read_jsonl,
)


class OrderedLiveBoundariesTest(unittest.TestCase):
    def test_external_outbox_dry_run_requires_allowlisted_exact_target_and_never_sends(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "outbox.jsonl"
            row = append_external_outbox_dry_run(
                path,
                platform="local-outbox",
                target="hewos-dry-run-channel",
                payload_hash="sha256:payload",
                allowlist=["local-outbox:hewos-dry-run-channel"],
                idempotency_key="outbox-1",
            )
            self.assertFalse(row["send_executed"])
            self.assertEqual(row["status"], "dry_run_recorded")
            self.assertEqual(len(read_jsonl(path)), 1)
            replay = append_external_outbox_dry_run(
                path,
                platform="local-outbox",
                target="hewos-dry-run-channel",
                payload_hash="sha256:payload",
                allowlist=["local-outbox:hewos-dry-run-channel"],
                idempotency_key="outbox-1",
            )
            self.assertTrue(replay["idempotent_replay"])
            with self.assertRaises(ValueError):
                append_external_outbox_dry_run(path, platform="telegram", target="unknown", payload_hash="sha256:x", allowlist=[], idempotency_key="bad")

    def test_deploy_push_preflight_records_rejected_dry_run_without_mutation(self):
        record = deploy_push_preflight_record(
            repo="/Users/charles/.hermes",
            remote="origin",
            branch="master",
            dry_run_exit_code=1,
            dry_run_output="non-fast-forward",
            rollback_plan="git reset --hard ORIG_HEAD after explicit review",
        )
        self.assertEqual(record["status"], "blocked_preflight")
        self.assertFalse(record["push_executed"])
        self.assertIn("non-fast-forward", record["readback"])

    def test_hardware_gate_requires_telemetry_safety_and_onsite_for_physical(self):
        blocked = hardware_safety_gate(
            device_id="hewos-local-virtual-device-20260703",
            telemetry={"fresh": True, "age_seconds": 0, "state": "virtual_dry_run"},
            safety_gate=True,
            external_control_gate=True,
            onsite_gate=False,
            physical_risk=True,
        )
        self.assertEqual(blocked["decision"], "blocked")
        self.assertIn("onsite_gate_required", blocked["reasons"])
        ok = hardware_safety_gate(
            device_id="hewos-local-virtual-device-20260703",
            telemetry={"fresh": True, "age_seconds": 0, "state": "virtual_dry_run"},
            safety_gate=True,
            external_control_gate=True,
            onsite_gate=True,
            physical_risk=False,
        )
        self.assertEqual(ok["decision"], "dry_run_pass_no_execution")
        self.assertFalse(ok["execution_enabled"])

    def test_auth_gate_is_human_secret_entry_only(self):
        gate = auth_human_secret_gate(
            provider="local-human-secret-entry",
            actor="human-operator",
            requested_scope="record-non-secret-readiness",
        )
        self.assertEqual(gate["decision"], "human_secret_entry_only")
        self.assertFalse(gate["agent_may_type_secret"])
        self.assertFalse(gate["token_read_allowed"])
        self.assertFalse(gate["stores_secrets"])


if __name__ == "__main__":
    unittest.main()
