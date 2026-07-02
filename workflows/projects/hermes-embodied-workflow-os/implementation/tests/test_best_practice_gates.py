import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hewos_core.best_practice_gates import (
    BEST_PRACTICE_PHASES,
    GateError,
    build_gate_packet,
    evaluate_authority_ladder,
    next_allowed_phase,
    validate_gate_packet,
    validate_process_phase,
)


class BestPracticeGateTest(unittest.TestCase):
    def valid_packet(self, **overrides):
        packet = {
            "gate_id": "gate.local.runtime.smoke",
            "phase": "local_runtime_smoke",
            "risk_class": "local_runtime",
            "side_effect_class": "local_process",
            "required_evidence": ["tests", "py_compile", "readback", "rollback"],
            "provided_evidence": {
                "tests": "27 unittest tests OK",
                "py_compile": "py_compile OK",
                "readback": "healthz execution_enabled false",
                "rollback": "kill server process; git revert commit",
            },
            "authority": {
                "scope": "local-only",
                "expires_at": "2026-07-02T23:59:00+08:00",
                "allowed_actions": ["local_read", "local_test", "local_process_smoke"],
                "forbidden_actions": ["external_dispatch", "taskpool_write", "hardware_execution", "deploy", "credential_entry"],
            },
            "idempotency_key": "hewos-local-runtime-smoke-v1",
            "rollback_plan": "kill managed local process and revert commit",
            "readback_plan": "GET /healthz and /execute 404",
            "next_phase": "ui_quality_audit",
        }
        packet.update(overrides)
        return packet

    def test_gate_packet_requires_all_evidence_classes(self):
        packet = self.valid_packet(provided_evidence={"tests": "OK"})
        with self.assertRaisesRegex(GateError, "missing evidence"):
            validate_gate_packet(packet)

    def test_gate_packet_requires_explicit_forbidden_high_risk_actions(self):
        packet = self.valid_packet()
        packet["authority"] = dict(packet["authority"])
        packet["authority"]["forbidden_actions"] = ["deploy"]
        with self.assertRaisesRegex(GateError, "forbidden_actions"):
            validate_gate_packet(packet)

    def test_gate_packet_accepts_local_only_runtime_smoke_boundary(self):
        validated = validate_gate_packet(self.valid_packet())
        self.assertEqual(validated["decision"], "pass")
        self.assertFalse(validated["execution_enabled"])
        self.assertEqual(validated["next_phase"], "ui_quality_audit")

    def test_process_phase_enforces_order_and_previous_receipt(self):
        phase = {
            "phase": "ui_quality_audit",
            "previous_phase": "local_runtime_smoke",
            "previous_receipt": "commit:26142337",
            "allowed_side_effects": ["local_file_write", "local_browser_smoke"],
            "exit_criteria": ["uimax_report", "screenshot_readback", "console_readback"],
        }
        self.assertEqual(validate_process_phase(phase)["phase"], "ui_quality_audit")
        phase["previous_receipt"] = ""
        with self.assertRaisesRegex(GateError, "previous_receipt"):
            validate_process_phase(phase)

    def test_next_allowed_phase_is_sequential_and_fail_closed(self):
        self.assertEqual(next_allowed_phase("local_runtime_smoke"), "ui_quality_audit")
        with self.assertRaisesRegex(GateError, "unknown phase"):
            next_allowed_phase("real_hardware_execution")

    def test_authority_ladder_blocks_skipped_external_execution(self):
        result = evaluate_authority_ladder(
            current_phase="local_runtime_smoke",
            requested_phase="external_adapter_intent",
            requested_actions=["external_dispatch"],
        )
        self.assertEqual(result["decision"], "blocked")
        self.assertIn("phase_skip", result["reasons"])
        self.assertIn("forbidden_action", result["reasons"])

    def test_build_gate_packet_has_stable_required_best_practice_evidence(self):
        packet = build_gate_packet(
            gate_id="gate.ui.audit",
            phase="ui_quality_audit",
            risk_class="local_ui",
            side_effect_class="local_file_write",
            provided_evidence={
                "tests": "OK",
                "browser_smoke": "title visible",
                "console_readback": "0 errors",
                "screenshot_readback": "sections visible",
                "rollback": "git revert",
            },
            next_phase="simulation_write_local_ledger",
        )
        self.assertEqual(packet["required_evidence"], BEST_PRACTICE_PHASES["ui_quality_audit"]["required_evidence"])
        self.assertEqual(validate_gate_packet(packet)["decision"], "pass")


if __name__ == "__main__":
    unittest.main()
