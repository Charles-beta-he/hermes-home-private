#!/usr/bin/env python3
from __future__ import annotations

import copy
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


def example() -> dict:
    return json.loads((SKILL_DIR / "assets" / "example-inquiry-packet.json").read_text())


class InquiryPacketValidatorTests(unittest.TestCase):
    def test_complete_example_passes(self) -> None:
        self.assertEqual([], validator.validate(example()))

    def test_single_hypothesis_fails_standard_mode(self) -> None:
        packet = example()
        packet["hypotheses"] = packet["hypotheses"][:1]
        self.assertTrue(any("requires at least 2 hypotheses" in e for e in validator.validate(packet)))

    def test_lite_single_hypothesis_with_constraint_passes(self) -> None:
        packet = example()
        packet["mode"] = "lite"
        packet["problem"]["hypothesis_space_constraint"] = "Only one mechanism remains after authoritative elimination of alternatives."
        packet["hypotheses"] = packet["hypotheses"][:1]
        packet["probes"][0]["predicted_results"] = {"H1": "bounded result"}
        packet["evidence_updates"][0]["updates"] = {"H1": "strengthened"}
        self.assertEqual([], validator.validate(packet))

    def test_lite_single_hypothesis_without_constraint_fails(self) -> None:
        packet = example()
        packet["mode"] = "lite"
        packet["hypotheses"] = packet["hypotheses"][:1]
        packet["probes"][0]["predicted_results"] = {"H1": "bounded result"}
        self.assertIn("problem.hypothesis_space_constraint must justify Lite single-hypothesis mode", validator.validate(packet))

    def test_strong_inference_two_hypotheses_fails(self) -> None:
        packet = example()
        packet["mode"] = "strong_inference"
        self.assertTrue(any("requires at least 3 hypotheses" in e for e in validator.validate(packet)))

    def test_strong_inference_three_hypotheses_passes(self) -> None:
        packet = example()
        packet["mode"] = "strong_inference"
        h2 = copy.deepcopy(packet["hypotheses"][1])
        h2["id"] = "H2"
        h2["claim"] = "A second alternative mechanism is sufficient."
        packet["hypotheses"].append(h2)
        packet["probes"][0]["predicted_results"]["H2"] = "third distinct result"
        self.assertEqual([], validator.validate(packet))

    def test_unsupported_schema_version_fails(self) -> None:
        packet = example()
        packet["schema_version"] = "999"
        self.assertTrue(any("unsupported schema_version" in e for e in validator.validate(packet)))

    def test_empty_inquiry_id_fails(self) -> None:
        packet = example()
        packet["inquiry_id"] = ""
        self.assertIn("inquiry_id must be non-empty", validator.validate(packet))

    def test_problem_lists_are_required(self) -> None:
        packet = example()
        packet["problem"]["constraints"] = "bad"
        self.assertIn("problem.constraints must be a list", validator.validate(packet))

    def test_duplicate_probe_id_fails(self) -> None:
        packet = example()
        packet["probes"].append(copy.deepcopy(packet["probes"][0]))
        self.assertIn("duplicate probe id: P1", validator.validate(packet))

    def test_hypothesis_prediction_must_reference_existing_probe(self) -> None:
        packet = example()
        packet["hypotheses"][0]["predictions"] = ["P9"]
        self.assertTrue(any("references unknown probes" in e for e in validator.validate(packet)))

    def test_probe_predictions_cover_all_live_hypotheses(self) -> None:
        packet = example()
        del packet["probes"][0]["predicted_results"]["H0"]
        self.assertTrue(any("must exactly cover live hypotheses" in e for e in validator.validate(packet)))

    def test_probe_prediction_values_are_nonempty(self) -> None:
        packet = example()
        packet["probes"][0]["predicted_results"]["H1"] = ""
        self.assertTrue(any("predicted_results['H1'] must be non-empty" in e for e in validator.validate(packet)))

    def test_probe_result_enum_is_enforced(self) -> None:
        packet = example()
        packet["probes"][0]["result"] = "looks good"
        self.assertIn("probes[0].result is invalid", validator.validate(packet))

    def test_evidence_ledger_is_required(self) -> None:
        packet = example()
        packet.pop("evidence_ledger", None)
        self.assertIn("missing top-level field: evidence_ledger", validator.validate(packet))

    def test_duplicate_evidence_id_fails(self) -> None:
        packet = example()
        packet["evidence_ledger"].append(copy.deepcopy(packet["evidence_ledger"][0]))
        self.assertIn("duplicate evidence id: E1", validator.validate(packet))

    def test_verified_baseline_must_reference_verified_evidence(self) -> None:
        packet = example()
        packet["baseline"]["verified"] = ["missing-evidence"]
        self.assertTrue(any("baseline.verified has unknown evidence ids" in e for e in validator.validate(packet)))

    def test_verified_evidence_requires_source_ref(self) -> None:
        packet = example()
        packet["evidence_ledger"][0]["source_ref"] = ""
        self.assertIn("evidence_ledger[0].source_ref must be non-empty", validator.validate(packet))

    def test_evidence_update_requires_known_evidence_id(self) -> None:
        packet = example()
        packet["evidence_updates"][0]["evidence_ids"] = ["E9"]
        self.assertTrue(any("has unknown evidence ids" in e for e in validator.validate(packet)))

    def test_evidence_update_rejects_unknown_hypothesis(self) -> None:
        packet = example()
        packet["evidence_updates"][0]["updates"]["H9"] = "strengthened"
        self.assertTrue(any("updates has unknown hypotheses" in e for e in validator.validate(packet)))

    def test_intervention_must_be_object(self) -> None:
        packet = example()
        packet["intervention"] = "bad"
        self.assertIn("intervention must be an object", validator.validate(packet))

    def test_reproduction_must_be_object(self) -> None:
        packet = example()
        packet["reproduction"] = "bad"
        self.assertIn("reproduction must be an object", validator.validate(packet))

    def test_reproduction_evidence_ids_are_required(self) -> None:
        packet = example()
        packet["reproduction"].pop("evidence_ids", None)
        self.assertIn("reproduction.evidence_ids must be a non-empty list", validator.validate(packet))

    def test_closure_writeback_contract_is_required(self) -> None:
        packet = example()
        packet["closure"]["writeback"].pop("demotion_path")
        self.assertIn("closure.writeback.demotion_path must be non-empty", validator.validate(packet))

    def test_ratified_requires_fresh_verified_reproduction_evidence(self) -> None:
        packet = example()
        packet["closure"]["state"] = "ratified"
        packet["evidence_ledger"][0]["freshness"] = "historical"
        self.assertIn("ratified closure requires fresh verified reproduction evidence", validator.validate(packet))


if __name__ == "__main__":
    unittest.main()
