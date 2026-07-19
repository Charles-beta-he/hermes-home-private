#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_DIR = HERE.parent
SPEC = importlib.util.spec_from_file_location("validator", HERE / "validate_inquiry_packet.py")
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


class InquiryPacketValidatorTests(unittest.TestCase):
    def test_complete_example_passes(self) -> None:
        packet = json.loads((SKILL_DIR / "assets" / "example-inquiry-packet.json").read_text())
        self.assertEqual([], validator.validate(packet))

    def test_single_hypothesis_fails_standard_mode(self) -> None:
        packet = json.loads((SKILL_DIR / "assets" / "example-inquiry-packet.json").read_text())
        packet["hypotheses"] = packet["hypotheses"][:1]
        errors = validator.validate(packet)
        self.assertIn("standard or stronger modes require at least two hypotheses", errors)

    def test_non_discriminating_probe_fails(self) -> None:
        packet = json.loads((SKILL_DIR / "assets" / "example-inquiry-packet.json").read_text())
        packet["probes"][0]["predicted_results"] = {"H1": "same", "H0": "same"}
        errors = validator.validate(packet)
        self.assertTrue(any("do not discriminate" in error for error in errors))

    def test_unknown_hypothesis_reference_fails(self) -> None:
        packet = json.loads((SKILL_DIR / "assets" / "example-inquiry-packet.json").read_text())
        packet["probes"][0]["predicted_results"]["H9"] = "unexpected"
        errors = validator.validate(packet)
        self.assertTrue(any("unknown hypotheses" in error for error in errors))

    def test_unknown_evidence_probe_fails(self) -> None:
        packet = json.loads((SKILL_DIR / "assets" / "example-inquiry-packet.json").read_text())
        packet["evidence_updates"][0]["probe_id"] = "P9"
        errors = validator.validate(packet)
        self.assertIn("evidence_updates[0].probe_id references an unknown probe", errors)

    def test_empty_inquiry_id_fails(self) -> None:
        packet = json.loads((SKILL_DIR / "assets" / "example-inquiry-packet.json").read_text())
        packet["inquiry_id"] = ""
        errors = validator.validate(packet)
        self.assertIn("inquiry_id must be non-empty", errors)

    def test_missing_independent_readback_fails(self) -> None:
        packet = json.loads((SKILL_DIR / "assets" / "example-inquiry-packet.json").read_text())
        packet["reproduction"]["independent_readback"] = ""
        errors = validator.validate(packet)
        self.assertIn("reproduction.independent_readback must be non-empty", errors)


if __name__ == "__main__":
    unittest.main()
