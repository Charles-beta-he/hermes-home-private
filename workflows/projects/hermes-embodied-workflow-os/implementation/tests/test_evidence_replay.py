import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hewos_core.contracts import ContractError
from hewos_core.ledger import EvidenceLedger, replay_world_state


class EvidenceReplayTest(unittest.TestCase):
    def test_appends_entries_and_replays_world_state(self):
        ledger = EvidenceLedger()
        ledger.append(
            kind="observation",
            subject_id="obs.1",
            source="adapter.web.mock",
            claims=[{"claim": "part-a visible"}],
            evidence_refs=["sha256:raw-1"],
            payload={"session_id": "session.1", "derived_facts": {"visible_parts": ["part-a"]}},
        )
        ledger.append(
            kind="verification",
            subject_id="verify.1",
            source="SafetyGate",
            claims=[{"claim": "step.1 passed"}],
            evidence_refs=["obs.1"],
            payload={"session_id": "session.1", "world_state_delta": {"completed_steps": ["step.1"]}},
        )

        world_state = replay_world_state(ledger.entries())

        self.assertEqual(world_state["visible_parts"], ["part-a"])
        self.assertEqual(world_state["completed_steps"], ["step.1"])

    def test_rejects_append_without_evidence(self):
        ledger = EvidenceLedger()
        with self.assertRaisesRegex(ContractError, "evidence_refs"):
            ledger.append(
                kind="observation",
                subject_id="obs.1",
                source="adapter.web.mock",
                claims=[{"claim": "part-a visible"}],
                evidence_refs=[],
                payload={"session_id": "session.1"},
            )

    def test_entries_are_copied_not_mutable_world_state_backdoors(self):
        ledger = EvidenceLedger()
        entry = ledger.append(
            kind="observation",
            subject_id="obs.1",
            source="adapter.web.mock",
            claims=[{"claim": "part-a visible"}],
            evidence_refs=["sha256:raw-1"],
            payload={"session_id": "session.1", "derived_facts": {"visible_parts": ["part-a"]}},
        )
        entry["payload"]["derived_facts"]["visible_parts"].append("mutated")

        world_state = replay_world_state(ledger.entries())

        self.assertEqual(world_state["visible_parts"], ["part-a"])


if __name__ == "__main__":
    unittest.main()
