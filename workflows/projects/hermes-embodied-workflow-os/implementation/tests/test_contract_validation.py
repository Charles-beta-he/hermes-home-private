import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hewos_core.contracts import (
    ContractError,
    validate_action_intent,
    validate_evidence_ledger_entry,
    validate_observation,
    validate_verification_result,
)


def observation(**overrides):
    payload = {
        "observation_id": "obs.web.1",
        "session_id": "session.1",
        "source_adapter_id": "adapter.web.mock",
        "type": "image",
        "timestamp": "2026-07-02T19:05:00+08:00",
        "raw_ref_or_hash": "sha256:abc",
        "confidence": 0.7,
        "evidence_refs": ["ev.raw.1"],
        "derived_facts": {"visible": ["part-a"]},
    }
    payload.update(overrides)
    return payload


def action_intent(**overrides):
    payload = {
        "intent_id": "intent.1",
        "session_id": "session.1",
        "taskgraph_node_id": "step.1",
        "actor_id": "actor.human.operator",
        "capability_id": "cap.human.guidance",
        "verb": "ask_user",
        "target": "part-a",
        "parameters": {},
        "risk_level": "none",
        "preconditions": [],
        "expected_observation_delta": {},
        "verification_plan": {"type": "human_confirm"},
        "evidence_refs": ["ev.plan.1"],
        "requested_authority": "none",
        "dry_run": True,
        "idempotency_key": "intent.1",
        "rollback_or_abort": "abort_only",
    }
    payload.update(overrides)
    return payload


def ledger_entry(**overrides):
    payload = {
        "entry_id": "ev.1",
        "timestamp": "2026-07-02T19:05:00+08:00",
        "kind": "observation",
        "subject_id": "obs.web.1",
        "source": "adapter.web.mock",
        "claims": [{"claim": "part-a visible", "confidence": "medium"}],
        "evidence_refs": ["sha256:abc"],
        "checksum_or_hash": "sha256:def",
        "append_only": True,
    }
    payload.update(overrides)
    return payload


class ContractValidationTest(unittest.TestCase):
    def test_accepts_normalized_observation(self):
        self.assertEqual(validate_observation(observation())["type"], "image")

    def test_rejects_observation_with_invalid_confidence(self):
        with self.assertRaisesRegex(ContractError, "confidence"):
            validate_observation(observation(confidence=1.5))

    def test_rejects_physical_action_intent_without_gates(self):
        with self.assertRaisesRegex(ContractError, "Gate"):
            validate_action_intent(action_intent(risk_level="physical_action", requested_authority="physical"))

    def test_accepts_dry_run_physical_action_with_both_gates(self):
        payload = action_intent(
            risk_level="physical_action",
            requested_authority="physical",
            dry_run=True,
            gate_status={"SafetyGate": "pass", "ExternalControlGate": "pass"},
        )
        self.assertEqual(validate_action_intent(payload)["risk_level"], "physical_action")

    def test_rejects_non_append_only_ledger_entry(self):
        with self.assertRaisesRegex(ContractError, "append_only"):
            validate_evidence_ledger_entry(ledger_entry(append_only=False))

    def test_rejects_completion_verification_without_evidence(self):
        payload = {
            "verification_id": "verify.1",
            "intent_id": "intent.1",
            "status": "passed",
            "observations_checked": [],
            "evidence_refs": [],
            "world_state_delta": {"completed_steps": ["step.1"]},
            "next_action": "advance",
        }
        with self.assertRaisesRegex(ContractError, "evidence_refs"):
            validate_verification_result(payload)


if __name__ == "__main__":
    unittest.main()
