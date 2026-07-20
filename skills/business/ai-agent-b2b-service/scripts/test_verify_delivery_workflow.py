#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import importlib.util
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

SCRIPT = Path(__file__).with_name("verify_delivery_workflow.py")
spec = importlib.util.spec_from_file_location("verify_delivery_workflow", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)
validate = module.validate


def valid_manifest():
    sources = [
        {"id": "TS1", "type": "repo", "ref": "evidence://source-1", "observed_at": date.today().isoformat(), "scope": "pilot", "max_stage": "S4"},
        {"id": "TS_ACCEPT", "type": "client_acceptance", "ref": "evidence://acceptance", "observed_at": date.today().isoformat(), "scope": "acceptance", "max_stage": "S6"},
        {"id": "TS_RIGHTS", "type": "publication_rights", "ref": "evidence://rights", "observed_at": date.today().isoformat(), "scope": "publication", "max_stage": "S7"},
        {"id": "TS_ANON", "type": "anonymization_review", "ref": "evidence://anonymization", "observed_at": date.today().isoformat(), "scope": "privacy", "max_stage": "S7"},
        {"id": "TS_GRANT", "type": "authority_grant", "ref": "evidence://grant", "observed_at": date.today().isoformat(), "scope": "authority", "max_stage": "S5"},
        {"id": "TS_SUCCESSOR", "type": "successor_engagement", "ref": "evidence://successor", "observed_at": date.today().isoformat(), "scope": "engagement succession", "max_stage": "S4"},
    ]
    artifacts = []
    artifact_refs_by_stage = {}
    for i, sid in enumerate(module.STAGE_ORDER):
        refs = []
        for artifact_type in sorted(module.REQUIRED_ARTIFACT_TYPES[sid]):
            artifact_id = f"A{i}_{artifact_type}"
            refs.append(artifact_id)
            artifacts.append({
                "id": artifact_id,
                "type": artifact_type,
                "ref": f"artifact://{sid}/{artifact_type}",
                "owner": "delivery-owner",
                "scope": sid,
            })
        artifact_refs_by_stage[sid] = refs
    stages = []
    for i, name in enumerate(module.STAGE_NAMES.values()):
        accepted = i <= 4
        stages.append({
            "id": f"S{i}",
            "name": name,
            "status": "accepted" if accepted else "not_started",
            "owner": "delivery-owner" if accepted else "",
            "artifacts": artifact_refs_by_stage[f"S{i}"] if accepted else [],
            "evidence_refs": ["TS1"] if accepted else [],
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
        "truth_sources": sources,
        "artifacts": artifacts,
        "claims": [{
            "id": "C1", "text": "pilot claim", "scope": "pilot/local",
            "status": "verified", "evidence_refs": ["TS1"],
            "negative_evidence_refs": ["TS1"], "limitations": ["not production"],
            "stage_refs": ["S0", "S1", "S2", "S3", "S4"],
            "max_stage": "S4",
        }],
        "contradictions": [],
        "related_engagements": [],
        "authority": {
            "local_read_only": True,
            "local_reversible_write": True,
            "authority_grants": [],
            "external_actions": [{"action": "push", "allowed": False, "target": "", "rollback": "", "readback": ""}],
        },
        "stages": stages,
        "metrics": [{"id": "M1", "name": "consistency", "baseline": 0, "target": 1, "measurement_ref": "validator", "evidence_refs": ["TS1"]}],
        "risks": [{"id": "R1", "severity": "high", "description": "claim drift", "detection": "validator", "mitigation": "narrow claim", "rollback": "mark disputed"}],
        "public_case": {"status": "not_ready", "publication_rights_verified": False, "anonymization_check": False, "sensitive_markers": ["internal"]},
        "client_acceptance": {"status": "not_requested", "accepted_by": "", "accepted_at": "", "scope": ""},
    }


class ValidatorTests(unittest.TestCase):
    def test_manifest_root_must_be_object(self):
        self.assertIn("root must be a JSON object", validate([]))

    def test_valid_manifest_passes(self):
        self.assertEqual(validate(valid_manifest()), [])

    def test_draft_manifest_does_not_require_target_boundary_accepted(self):
        data = valid_manifest()
        data["closure_state"] = "in_progress"
        for stage in data["stages"]:
            stage.update({"status": "not_started", "owner": "", "artifacts": [], "evidence_refs": [], "blockers": []})
        self.assertEqual(validate(data), [])

    def test_accepted_closure_rejects_unverified_or_disputed_claims(self):
        for claim_status in ("unverified", "disputed"):
            with self.subTest(status=claim_status):
                data = valid_manifest()
                data["claims"][0]["status"] = claim_status
                errors = validate(data)
                self.assertTrue(any("accepted closure requires settled claim" in e for e in errors))

    def test_accepted_closure_requires_at_least_one_verified_claim(self):
        data = valid_manifest()
        data["claims"][0]["status"] = "superseded"
        errors = validate(data)
        self.assertTrue(any("at least one verified claim" in e for e in errors))

    def test_accepted_closure_malformed_claim_status_fails_without_crashing(self):
        for malformed in ([], {}):
            with self.subTest(value=malformed):
                data = valid_manifest()
                data["claims"][0]["status"] = malformed
                errors = validate(data)
                self.assertTrue(any("invalid status" in e for e in errors))

    def test_accepted_risk_contradiction_requires_approval_controls_and_evidence(self):
        data = valid_manifest()
        data["claims"].append({"id": "C2", "text": "conflicting claim", "scope": "whole project", "status": "superseded", "evidence_refs": [], "negative_evidence_refs": [], "limitations": []})
        data["contradictions"] = [{
            "id": "X1", "claim_refs": ["C1", "C2"], "status": "accepted_risk",
            "resolution": "temporary exception",
        }]
        errors = validate(data)
        for field in ("approved_by", "accepted_at", "compensating_controls", "evidence_refs"):
            self.assertTrue(any(field in e for e in errors))

    def test_public_case_ready_requires_rights_and_anonymization_evidence(self):
        data = valid_manifest()
        data["confidentiality"] = "public"
        data["public_case"] = {
            "status": "ready", "publication_rights_verified": True,
            "anonymization_check": True, "sensitive_markers": [],
        }
        errors = validate(data)
        self.assertTrue(any("publication_rights_evidence_refs" in e for e in errors))
        self.assertTrue(any("anonymization_evidence_refs" in e for e in errors))

    def test_client_acceptance_requires_evidence_and_valid_date(self):
        data = valid_manifest()
        data["client_acceptance"] = {
            "status": "accepted", "accepted_by": "client-sponsor",
            "accepted_at": "not-a-date", "scope": "pilot", "evidence_refs": [],
        }
        errors = validate(data)
        self.assertTrue(any("accepted_at must be ISO date" in e for e in errors))
        self.assertTrue(any("client_acceptance.evidence_refs must not be empty" in e for e in errors))

    def test_accepted_client_record_requires_S6_accepted(self):
        data = valid_manifest()
        data["client_acceptance"].update({
            "status": "accepted", "accepted_by": "client-sponsor",
            "accepted_at": date.today().isoformat(), "scope": "whole delivery",
            "evidence_refs": ["TS_ACCEPT"],
        })
        self.assertTrue(any("client_acceptance=accepted requires stage S6=accepted" in e for e in validate(data)))

    def test_client_acceptance_rejects_placeholder_identity_and_scope(self):
        data = valid_manifest()
        data["client_acceptance"].update({
            "status": "accepted", "accepted_by": "replace-with-client",
            "accepted_at": date.today().isoformat(), "scope": "replace-with-scope",
            "evidence_refs": ["TS1"],
        })
        errors = validate(data)
        self.assertTrue(any("accepted_by contains placeholder" in e for e in errors))
        self.assertTrue(any("scope contains placeholder" in e for e in errors))

    def test_client_acceptance_rejects_common_placeholder_tokens(self):
        for accepted_by, scope in (("TBD", "delivery"), ("client", "N/A"), ("TODO", "unknown")):
            with self.subTest(accepted_by=accepted_by, scope=scope):
                data = valid_manifest()
                data["client_acceptance"].update({
                    "status": "accepted", "accepted_by": accepted_by,
                    "accepted_at": date.today().isoformat(), "scope": scope,
                    "evidence_refs": ["TS_ACCEPT"],
                })
                self.assertTrue(any("contains placeholder" in e for e in validate(data)))

    def test_legitimate_bracket_qualifier_is_not_placeholder(self):
        data = valid_manifest()
        data["client_alias"] = "Acme [US]"
        self.assertEqual(validate(data), [])

    def test_client_acceptance_requires_semantic_evidence_type(self):
        data = valid_manifest()
        data["client_acceptance"].update({
            "status": "accepted", "accepted_by": "client-sponsor",
            "accepted_at": date.today().isoformat(), "scope": "delivery",
            "evidence_refs": ["TS1"],
        })
        self.assertTrue(any("client_acceptance evidence type" in e for e in validate(data)))

    def test_public_case_requires_semantic_evidence_types(self):
        data = valid_manifest()
        data["confidentiality"] = "public"
        data["public_case"] = {
            "status": "ready", "publication_rights_verified": True,
            "publication_rights_evidence_refs": ["TS1"],
            "anonymization_check": True, "anonymization_evidence_refs": ["TS1"],
            "sensitive_markers": [],
        }
        errors = validate(data)
        self.assertTrue(any("publication rights evidence type" in e for e in errors))
        self.assertTrue(any("anonymization evidence type" in e for e in errors))
        data["public_case"]["publication_rights_evidence_refs"] = ["TS_RIGHTS"]
        data["public_case"]["anonymization_evidence_refs"] = ["TS_ANON"]
        self.assertEqual(validate(data), [])

    def test_verified_claim_requires_nonempty_limitations(self):
        data = valid_manifest()
        data["claims"][0]["limitations"] = []
        self.assertTrue(any("needs limitations as a non-empty string list" in e for e in validate(data)))

    def test_unresolved_contradiction_fails(self):
        data = valid_manifest()
        data["claims"].append({"id": "C2", "text": "conflicting claim", "scope": "whole project", "status": "verified", "evidence_refs": ["TS1"], "negative_evidence_refs": [], "limitations": []})
        data["contradictions"] = [{"id": "X1", "claim_refs": ["C1", "C2"], "status": "unresolved", "resolution": ""}]
        errors = validate(data)
        self.assertTrue(any("unresolved contradiction" in e for e in errors))
        self.assertTrue(any("cannot remain verified" in e for e in errors))

    def test_verified_claim_without_evidence_fails(self):
        data = valid_manifest()
        data["claims"][0]["evidence_refs"] = []
        self.assertTrue(any("must not be empty" in e for e in validate(data)))

    def test_unknown_claim_evidence_fails(self):
        data = valid_manifest()
        data["claims"][0]["evidence_refs"] = ["UNKNOWN"]
        self.assertTrue(any("unknown id" in e for e in validate(data)))

    def test_negative_evidence_must_be_list_and_known(self):
        data = valid_manifest()
        data["claims"][0]["negative_evidence_refs"] = "TS1"
        self.assertTrue(any("negative_evidence_refs must be a list" in e for e in validate(data)))
        data = valid_manifest()
        data["claims"][0]["negative_evidence_refs"] = ["UNKNOWN"]
        self.assertTrue(any("unknown id" in e for e in validate(data)))

    def test_local_absolute_source_requires_existence_and_hash(self):
        data = valid_manifest()
        data["truth_sources"][0]["ref"] = "/definitely/missing/evidence.md"
        self.assertTrue(any("does not exist" in e for e in validate(data)))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "evidence.txt"
            path.write_text("evidence", encoding="utf-8")
            data = valid_manifest()
            data["truth_sources"][0].update({"ref": str(path), "sha256": "0" * 64})
            self.assertTrue(any("sha256 mismatch" in e for e in validate(data)))
            data["truth_sources"][0]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(validate(data), [])

    def test_observed_at_must_be_iso_and_not_future(self):
        data = valid_manifest()
        data["truth_sources"][0]["observed_at"] = "not-a-date"
        self.assertTrue(any("must be ISO date" in e for e in validate(data)))
        data["truth_sources"][0]["observed_at"] = "2999-01-01"
        self.assertTrue(any("cannot be in the future" in e for e in validate(data)))

    def test_accepted_stage_requires_known_artifact_and_evidence(self):
        data = valid_manifest()
        data["stages"][3]["artifacts"] = ["UNKNOWN"]
        self.assertTrue(any("unknown id" in e for e in validate(data)))
        data = valid_manifest()
        data["stages"][3]["artifacts"] = []
        self.assertTrue(any("accepted stage S3 needs artifacts" in e for e in validate(data)))

    def test_accepted_stage_requires_semantic_artifact_types(self):
        data = valid_manifest()
        data["stages"][4]["artifacts"] = ["A4_pilot_evidence"]
        errors = validate(data)
        self.assertTrue(any("missing required artifact types: test_evidence" in e for e in errors))

    def test_stage_beyond_completion_boundary_cannot_be_active(self):
        data = valid_manifest()
        data["stages"][5].update({
            "status": "accepted",
            "owner": "delivery-owner",
            "artifacts": [
                f"A5_{kind}" for kind in sorted(module.REQUIRED_ARTIFACT_TYPES["S5"])
            ],
            "evidence_refs": ["TS1"],
            "blockers": [],
        })
        self.assertTrue(any("stage S5 is beyond completion boundary pilot" in e for e in validate(data)))

    def test_stage_cannot_skip_unaccepted_prior_stage(self):
        data = valid_manifest()
        data["stages"][2]["status"] = "ready_for_review"
        self.assertTrue(any("stage S3 cannot be accepted before S2 is accepted" in e for e in validate(data)))

    def test_accepted_S6_requires_prior_stages_and_client_acceptance(self):
        data = valid_manifest()
        data["completion_boundary"] = "acceptance"
        for i in (5, 6):
            artifact_refs = [f"A{i}_{kind}" for kind in sorted(module.REQUIRED_ARTIFACT_TYPES[f"S{i}"])]
            data["stages"][i].update({"status": "accepted", "owner": "delivery-owner", "artifacts": artifact_refs, "evidence_refs": ["TS1"], "blockers": []})
        errors = validate(data)
        self.assertTrue(any("stage S6 requires client_acceptance=accepted" in e for e in errors))

    def test_authority_local_flags_are_boolean(self):
        data = valid_manifest()
        data["authority"]["local_read_only"] = "yes"
        self.assertTrue(any("local_read_only must be boolean" in e for e in validate(data)))

    def test_allowed_external_action_requires_grant_and_controls(self):
        data = valid_manifest()
        data["authority"]["external_actions"][0]["allowed"] = True
        errors = validate(data)
        for key in ("target", "scope", "grant_ref", "rollback", "readback"):
            self.assertTrue(any(f"needs {key}" in e for e in errors))

    def test_unknown_external_action_is_rejected(self):
        data = valid_manifest()
        data["authority"]["external_actions"].append({"action": "do_anything", "allowed": False})
        self.assertTrue(any("unknown external action: do_anything" in e for e in validate(data)))

    def test_payment_and_credential_actions_cannot_be_enabled(self):
        for action_name in ("credential_entry", "payment_or_funds"):
            with self.subTest(action=action_name):
                data = valid_manifest()
                data["authority"]["external_actions"].append({
                    "action": action_name,
                    "allowed": True,
                    "target": "human-gated-target",
                    "scope": "human-only",
                    "grant_ref": "GRANT-HUMAN-ONLY",
                    "rollback": "cancel before execution",
                    "readback": "human receipt",
                })
                self.assertTrue(any(f"{action_name} cannot be enabled" in e for e in validate(data)))

    def test_malformed_contradiction_claim_refs_does_not_crash(self):
        data = valid_manifest()
        data["contradictions"] = [{
            "id": "X1", "claim_refs": 1, "status": "unresolved", "resolution": "",
        }]
        errors = validate(data)
        self.assertTrue(any("contradictions[0].claim_refs must be a list" in error for error in errors))

    def test_malformed_stage_status_does_not_crash(self):
        data = valid_manifest()
        data["stages"][4]["status"] = []
        errors = validate(data)
        self.assertTrue(any("stage S4 has invalid status" in error for error in errors))

    def test_duplicate_ids_fail(self):
        data = valid_manifest()
        data["risks"].append(copy.deepcopy(data["risks"][0]))
        self.assertTrue(any("duplicate risk id" in e for e in validate(data)))

    def test_public_case_requires_public_confidentiality(self):
        data = valid_manifest()
        data["public_case"] = {"status": "ready", "publication_rights_verified": True, "anonymization_check": True, "sensitive_markers": []}
        self.assertTrue(any("confidentiality=public" in e for e in validate(data)))

    def test_placeholder_is_rejected(self):
        data = valid_manifest()
        data["engagement_id"] = "replace-with-stable-id"
        self.assertTrue(any("contains placeholder" in e for e in validate(data)))

    def test_ready_for_review_state_contract(self):
        data = valid_manifest()
        data["closure_state"] = "ready_for_review"
        data["stages"][4]["status"] = "ready_for_review"
        self.assertEqual(validate(data), [])

    def test_ready_for_review_requires_boundary_review_packet(self):
        data = valid_manifest()
        data["closure_state"] = "ready_for_review"
        data["stages"][4].update({
            "status": "ready_for_review", "artifacts": [], "evidence_refs": [],
        })
        errors = validate(data)
        self.assertTrue(any("reviewable stage S4 needs artifacts" in e for e in errors))
        self.assertTrue(any("reviewable stage S4 needs evidence_refs" in e for e in errors))

    def test_waiting_acceptance_requires_S6_review_packet(self):
        data = valid_manifest()
        data["completion_boundary"] = "acceptance"
        data["closure_state"] = "waiting_acceptance"
        data["claims"][0]["stage_refs"].extend(["S5", "S6"])
        refs = [f"A5_{kind}" for kind in sorted(module.REQUIRED_ARTIFACT_TYPES["S5"])]
        data["stages"][5].update({
            "status": "accepted", "owner": "delivery-owner", "artifacts": refs,
            "evidence_refs": ["TS1"], "blockers": [],
        })
        data["stages"][6].update({
            "status": "ready_for_review", "owner": "delivery-owner",
            "artifacts": [], "evidence_refs": [], "blockers": [],
        })
        data["client_acceptance"]["status"] = "pending"
        errors = validate(data)
        self.assertTrue(any("reviewable stage S6 needs artifacts" in e for e in errors))
        self.assertTrue(any("reviewable stage S6 needs evidence_refs" in e for e in errors))

    def test_superseded_closure_requires_record_and_boundary_stage(self):
        data = valid_manifest()
        data["closure_state"] = "superseded"
        errors = validate(data)
        self.assertTrue(any("superseded closure requires supersession record" in e for e in errors))
        self.assertTrue(any("superseded closure requires stage S4=superseded" in e for e in errors))

    def test_weak_supersession_record_is_rejected(self):
        data = valid_manifest()
        data["closure_state"] = "superseded"
        data["stages"][4].update({"status": "superseded", "owner": "", "artifacts": [], "evidence_refs": [], "blockers": []})
        data["supersession"] = {
            "superseded_by": "x", "superseded_at": date.today().isoformat(),
            "reason": "x", "evidence_refs": ["TS1"],
        }
        self.assertTrue(any("registered successor engagement" in e for e in validate(data)))

    def test_valid_superseded_closure_passes(self):
        data = valid_manifest()
        data["closure_state"] = "superseded"
        data["stages"][4].update({
            "status": "superseded", "owner": "", "artifacts": [],
            "evidence_refs": [], "blockers": [],
        })
        data["related_engagements"] = [{
            "id": "successor-engagement", "relationship": "successor", "status": "active",
            "evidence_refs": ["TS_SUCCESSOR"],
        }]
        data["supersession"] = {
            "superseded_by": "successor-engagement", "superseded_at": date.today().isoformat(),
            "reason": "scope replaced by a successor engagement", "evidence_refs": ["TS_SUCCESSOR"],
        }
        self.assertEqual(validate(data), [])

    def test_successor_requires_typed_engagement_evidence(self):
        data = valid_manifest()
        data["closure_state"] = "superseded"
        data["stages"][4].update({
            "status": "superseded", "owner": "", "artifacts": [],
            "evidence_refs": [], "blockers": [],
        })
        data["related_engagements"] = [{
            "id": "successor-engagement", "relationship": "successor", "status": "active",
            "evidence_refs": ["TS1"],
        }]
        data["supersession"] = {
            "superseded_by": "successor-engagement", "superseded_at": date.today().isoformat(),
            "reason": "scope replaced", "evidence_refs": ["TS1"],
        }
        self.assertTrue(any("evidence type" in e for e in validate(data)))

    def test_claim_max_stage_cannot_exceed_evidence_capability(self):
        data = valid_manifest()
        data["claims"][0]["max_stage"] = "S5"
        data["claims"][0]["stage_refs"].append("S5")
        self.assertTrue(any("exceeds evidence capability" in e for e in validate(data)))

    def test_truth_source_requires_stage_capability(self):
        data = valid_manifest()
        data["truth_sources"][0].pop("max_stage")
        errors = validate(data)
        self.assertTrue(any("truth_sources[0].max_stage" in e for e in errors))
        self.assertTrue(any("needs evidence with a declared max_stage" in e for e in errors))

    def test_allowed_external_action_requires_known_grant_reference(self):
        data = valid_manifest()
        data["authority"]["external_actions"][0].update({
            "allowed": True, "target": "repository-target", "scope": "single change",
            "grant_ref": "UNKNOWN-GRANT", "rollback": "revert change",
            "readback": "read target state",
        })
        self.assertTrue(any("grant_ref must reference a registered authority grant" in e for e in validate(data)))

    def test_allowed_external_action_rejects_untyped_source_as_grant(self):
        data = valid_manifest()
        data["authority"]["external_actions"][0].update({
            "allowed": True, "target": "repository-target", "scope": "single change",
            "grant_ref": "TS1", "rollback": "revert change", "readback": "read target state",
        })
        self.assertTrue(any("registered authority grant" in e for e in validate(data)))

    def test_allowed_external_action_accepts_bound_authority_grant(self):
        data = valid_manifest()
        data["authority"]["authority_grants"] = [{
            "id": "G1", "type": "authority_grant", "action": "push",
            "target": "repository-target", "scope": "single change",
            "granted_by": "authorized-owner", "granted_at": date.today().isoformat(),
            "expires_at": (date.today() + timedelta(days=1)).isoformat(), "revoked": False,
            "evidence_refs": ["TS_GRANT"],
        }]
        data["authority"]["external_actions"][0].update({
            "allowed": True, "target": "repository-target", "scope": "single change",
            "grant_ref": "G1", "rollback": "revert change", "readback": "read target state",
        })
        self.assertEqual(validate(data), [])

    def test_expired_or_revoked_authority_grant_is_rejected(self):
        for field, value, expected in (
            ("expires_at", (date.today() - timedelta(days=1)).isoformat(), "cannot be in the past"),
            ("revoked", True, "is revoked"),
        ):
            with self.subTest(field=field):
                data = valid_manifest()
                grant = {
                    "id": "G1", "type": "authority_grant", "action": "push",
                    "target": "repository-target", "scope": "single change",
                    "granted_by": "authorized-owner", "granted_at": date.today().isoformat(),
                    "expires_at": (date.today() + timedelta(days=1)).isoformat(), "revoked": False,
                    "evidence_refs": ["TS_GRANT"],
                }
                grant[field] = value
                data["authority"]["authority_grants"] = [grant]
                data["authority"]["external_actions"][0].update({
                    "allowed": True, "target": "repository-target", "scope": "single change",
                    "grant_ref": "G1", "rollback": "revert change", "readback": "read target state",
                })
                self.assertTrue(any(expected in e for e in validate(data)))

    def test_accepted_stage_requires_verified_claim_with_sufficient_max_stage(self):
        data = valid_manifest()
        data["completion_boundary"] = "production"
        refs = [f"A5_{kind}" for kind in sorted(module.REQUIRED_ARTIFACT_TYPES["S5"])]
        data["stages"][5].update({
            "status": "accepted", "owner": "delivery-owner", "artifacts": refs,
            "evidence_refs": ["TS1"], "blockers": [],
        })
        data["claims"][0]["stage_refs"].append("S5")
        errors = validate(data)
        self.assertTrue(any("exceeds claim max_stage S4" in e for e in errors))

    def test_blocked_closure_requires_blocked_stage(self):
        data = valid_manifest()
        data["closure_state"] = "blocked"
        self.assertTrue(any("requires a blocked stage" in e for e in validate(data)))

    def test_malformed_nested_types_return_errors_instead_of_crashing(self):
        mutations = [
            ("completion_boundary", []),
            ("closure_state", {}),
            ("confidentiality", []),
        ]
        for key, value in mutations:
            with self.subTest(key=key):
                data = valid_manifest()
                data[key] = value
                self.assertTrue(validate(data))
        data = valid_manifest()
        data["stages"][0]["id"] = []
        self.assertTrue(validate(data))
        data = valid_manifest()
        data["contradictions"] = [{"id": "X", "claim_refs": [{}], "status": "unresolved", "resolution": ""}]
        self.assertTrue(validate(data))


if __name__ == "__main__":
    unittest.main()
