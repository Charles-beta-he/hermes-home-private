import json
import unittest
from pathlib import Path

from run_absorption_loop import build_packet, choose_families

ROOT = Path(__file__).resolve().parents[1]


class AbsorptionLoopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((ROOT / "module-pool/capability-catalog.json").read_text())
        cls.registry = json.loads((ROOT / "module-pool/module_registry.json").read_text())

    def test_routes_explicit_families(self):
        self.assertEqual(choose_families("RAG + memory + MCP"), ["rag", "memory", "mcp_tools"])

    def test_defaults_to_safe_p0_families(self):
        self.assertEqual(choose_families("吸收功能"), ["rag", "mcp_tools", "memory"])

    def test_packet_has_source_cards_and_closed_effects(self):
        packet = build_packet(self.catalog, self.registry, "RAG memory MCP")
        self.assertEqual(packet["gates"]["source_identity"], "PASS")
        self.assertEqual(packet["gates"]["module_coverage"], "PASS")
        self.assertEqual(packet["closure_state"], "static_evidence_only")
        self.assertTrue(all(value is False for value in packet["side_effects"].values()))
        self.assertTrue(all(card["source_examples"] for card in packet["source_cards"]))

    def test_runtime_gate_stays_warn_without_provider_proof(self):
        packet = build_packet(self.catalog, self.registry, "voice")
        self.assertEqual(packet["gates"]["runtime_evidence"], "WARN")
        self.assertIn("upstream runtime health", packet["cannot_prove"])


if __name__ == "__main__": unittest.main()
