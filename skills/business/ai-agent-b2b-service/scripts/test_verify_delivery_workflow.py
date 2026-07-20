#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("verify_delivery_workflow.py")
spec = importlib.util.spec_from_file_location("verify_delivery_workflow", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)
validate = module.validate


def valid_manifest():
    stages = []
    for i, name in enumerate(module.STAGE_NAMES.values()):
        accepted = i <= 4
        stages.append({
            "id": f"S{i}",
            "name": name,
            "status": "accepted" if accepted else "not_started",
            "owner": "delivery-owner" if accepted else "",
            "artifacts": [f"artifact-S{i}"] if accepted else [],
            "evidence_refs": [f"evidence-S{i}"] if accepted else [],
            "blockers": [],
        })
    return {
        "schema": "b2b_delivery_workflow_v1",
        "engagement_id": "fixture-1",
        "client_alias": "anonymous",
        "service_type": "ai_assisted_software_delivery_governance",
        "completion_boundary": "pilot",
        "closure_state": "accepted",
        "confidentiality": "internal",
        "truth_sources": [{"id":"TS1","type":"repo","ref":"/private/source","observed_at":"2026-07-20","scope":"pilot"}],
        "claims": [{"id":"C1","text":"pilot claim","scope":"pilot/local","status":"verified","evidence_refs":["E1"],"negative_evidence_refs":["N1"],"limitations":["not production"]}],
        "contradictions": [],
        "authority": {"local_read_only":True,"local_reversible_write":True,"external_actions":[{"action":"push","allowed":False,"target":"","rollback":"","readback":""}]},
        "stages": stages,
        "metrics": [{"id":"M1","name":"consistency","baseline":0,"target":1,"measurement_ref":"report"}],
        "risks": [{"id":"R1","severity":"high","description":"claim drift","detection":"validator","mitigation":"narrow claim","rollback":"mark disputed"}],
        "public_case": {"status":"not_ready","publication_rights_verified":False,"anonymization_check":False,"sensitive_markers":["internal"]},
        "client_acceptance": {"status":"not_requested","accepted_by":"","accepted_at":"","scope":""},
    }


class ValidatorTests(unittest.TestCase):
    def test_valid_pilot_manifest(self):
        self.assertEqual(validate(valid_manifest()), [])

    def test_unresolved_contradiction_fails(self):
        data = valid_manifest()
        data["claims"].append({"id":"C2","text":"conflicting claim","scope":"whole project","status":"verified","evidence_refs":["E2"],"negative_evidence_refs":[],"limitations":[]})
        data["contradictions"] = [{"id":"X1","claim_refs":["C1","C2"],"status":"unresolved","resolution":""}]
        errors = validate(data)
        self.assertTrue(any("unresolved contradiction" in e for e in errors))
        self.assertTrue(any("cannot remain verified" in e for e in errors))

    def test_verified_claim_without_evidence_fails(self):
        data = valid_manifest()
        data["claims"][0]["evidence_refs"] = []
        self.assertTrue(any("must have evidence_refs" in e for e in validate(data)))

    def test_accepted_stage_without_artifact_fails(self):
        data = valid_manifest()
        data["stages"][3]["artifacts"] = []
        self.assertTrue(any("accepted stage S3 needs artifacts" in e for e in validate(data)))

    def test_allowed_external_action_requires_exact_controls(self):
        data = valid_manifest()
        data["authority"]["external_actions"][0]["allowed"] = True
        errors = validate(data)
        self.assertTrue(any("needs target" in e for e in errors))
        self.assertTrue(any("needs rollback" in e for e in errors))
        self.assertTrue(any("needs readback" in e for e in errors))

    def test_public_case_requires_rights_and_anonymization(self):
        data = valid_manifest()
        data["public_case"]["status"] = "ready"
        errors = validate(data)
        self.assertTrue(any("publication rights" in e for e in errors))
        self.assertTrue(any("anonymization" in e for e in errors))
        self.assertTrue(any("sensitive markers" in e for e in errors))

    def test_completion_boundary_cannot_skip_stage(self):
        data = valid_manifest()
        data["stages"][2]["status"] = "ready_for_review"
        self.assertTrue(any("requires accepted stage S2" in e for e in validate(data)))


if __name__ == "__main__":
    unittest.main()
