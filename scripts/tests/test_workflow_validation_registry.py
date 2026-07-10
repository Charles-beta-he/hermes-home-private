import hashlib
import json
import os
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import workflow_validation_registry as wvr

TEST_AUTHORITY_ROOT = Path.home() / ".hermes" / "cache" / f"procedure-authority-tests-{os.getpid()}"
TEST_AUTHORITY_ROOT.mkdir(parents=True, exist_ok=True)


def evaluate(**kwargs):
    kwargs.setdefault(
        "system_inventory_attestations",
        {
            "profile:lark": {
                "scope_complete": True,
                "reviewed_at": "2026-07-10T00:00:00Z",
                "freshness_seconds": 86400,
                "basis": "test fixture inventory audit",
            }
        },
    )
    return wvr.evaluate_registry(**kwargs)


def declaration(**overrides):
    value = {
        "procedure_id": "lark.oauth.recovery",
        "system_id": "profile:lark",
        "required": True,
        "implementation_state": "enabled",
        "side_effect_class": "browser_auth",
        "authority_policy": "exact_grant_required",
        "authority_grant_root": str(TEST_AUTHORITY_ROOT),
        "authority_issuer": "human_authority",
        "freshness_seconds": 3600,
        "min_independent_successes": 1,
        "required_acceptance_atoms": ["callback_received", "token_valid"],
        "required_negative_assertions": ["no_task_read", "no_lark_write"],
        "validation_policy": "fresh_live_e2e_receipt",
        "required_evidence_kinds": ["evidence_refs", "acceptance_atoms", "negative_assertions", "cleanup_readback"],
        "failure_expectation": "fail_closed_and_surface_finding",
        "recovery_expectation": "wait_for_exact_grant_then_revalidate",
        "propagation_targets": ["procedure_registry", "agent_os_projection", "workflow_loop_evaluator"],
    }
    value.update(overrides)
    return value


def write_evidence(tmp_path: Path, name: str = "evidence.json") -> Path:
    path = tmp_path / name
    path.write_text("{}\n", encoding="utf-8")
    return path


def write_authority_grant(tmp_path: Path, name: str = "authority-grant.json", **overrides) -> Path:
    path = TEST_AUTHORITY_ROOT / name
    value = {
        "schema": "hermes_procedure_authority_grant_v1",
        "grant_id": path.stem,
        "status": "active",
        "procedure_id": "lark.oauth.recovery",
        "system_id": "profile:lark",
        "action": "execute_live_e2e_validation",
        "scope": "lark.oauth.recovery",
        "receipt_id": "r-001",
        "issued_by": "human_authority",
        "valid_from": "2026-07-09T00:00:00Z",
        "expires_at": "2026-07-11T00:00:00Z",
    }
    value.update(overrides)
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def receipt(tmp_path: Path, **overrides):
    evidence = write_evidence(tmp_path)
    receipt_id = str(overrides.get("receipt_id", "r-001"))
    authority_grant = write_authority_grant(
        tmp_path,
        name=f"authority-grant-{receipt_id}.json",
        receipt_id=receipt_id,
    )
    value = {
        "schema": "hermes_procedure_e2e_receipt_v1",
        "receipt_id": receipt_id,
        "procedure_id": "lark.oauth.recovery",
        "started_at": "2026-07-10T00:00:00Z",
        "completed_at": "2026-07-10T00:01:00Z",
        "result": "PASS",
        "execution_mode": "live_e2e",
        "evidence_refs": [str(evidence)],
        "acceptance_atoms": {"callback_received": True, "token_valid": True},
        "negative_assertions": {"no_task_read": True, "no_lark_write": True},
        "cleanup_readback": "PASS",
        "authority": {
            "status": "granted",
            "ref": str(authority_grant),
            "sha256": hashlib.sha256(authority_grant.read_bytes()).hexdigest(),
        },
        "side_effects_observed": ["browser_auth"],
    }
    value.update(overrides)
    return value


def test_declaration_contract_requires_policy_evidence_failure_recovery_and_propagation_metadata():
    for field, expected_issue in (
        ("validation_policy", "missing_validation_policy"),
        ("required_evidence_kinds", "missing_required_evidence_kinds"),
        ("failure_expectation", "missing_failure_expectation"),
        ("recovery_expectation", "missing_recovery_expectation"),
        ("propagation_targets", "missing_propagation_targets"),
    ):
        candidate = declaration()
        candidate.pop(field)
        assert expected_issue in wvr.validate_declaration(candidate)


def test_declaration_contract_rejects_semantically_invalid_governance_metadata():
    cases = (
        ({"validation_policy": "trust_any_receipt"}, "invalid_validation_policy"),
        ({"required_evidence_kinds": ["evidence_refs"]}, "invalid_required_evidence_kinds"),
        ({"failure_expectation": "ignore_failure"}, "invalid_failure_expectation"),
        ({"recovery_expectation": "auto_promote"}, "invalid_recovery_expectation"),
        ({"propagation_targets": ["unknown_sink"]}, "invalid_propagation_targets"),
        ({"required_acceptance_atoms": [{"not": "a string"}]}, "missing_required_acceptance_atoms"),
        ({"required": 0}, "invalid_required"),
        ({"required": []}, "invalid_required"),
        ({"required": ""}, "invalid_required"),
        ({"freshness_seconds": "bad"}, "invalid_freshness_seconds"),
        ({"min_independent_successes": "bad"}, "invalid_min_independent_successes"),
    )
    for override, expected_issue in cases:
        assert expected_issue in wvr.validate_declaration(declaration(**override))


def test_malformed_required_and_numeric_policy_fields_fail_closed_without_crashing():
    for override in (
        {"required": 0}, {"required": []}, {"required": ""},
        {"freshness_seconds": "bad"}, {"min_independent_successes": "bad"},
    ):
        result = evaluate(
            declarations=[declaration(**override)],
            receipts=[],
            enabled_system_ids=["profile:lark"],
            system_exemptions={},
            now="2026-07-10T00:30:00Z",
        )
        procedure = result["procedures"][0]
        assert procedure["required"] is True
        assert procedure["delivery_state"] == "pending"
        assert "procedure_declaration_invalid" in procedure["findings"]
        assert result["summary"]["required_procedures"] == 1
        assert result["summary"]["can_claim_complete_procedure_validation"] is False


def test_declaration_contract_rejects_mixed_type_governance_lists():
    mixed_evidence = declaration(required_evidence_kinds=[
        "evidence_refs", "acceptance_atoms", "negative_assertions", "cleanup_readback", {"malformed": True},
    ])
    mixed_targets = declaration(propagation_targets=["procedure_registry", {"malformed": True}])
    assert "invalid_required_evidence_kinds" in wvr.validate_declaration(mixed_evidence)
    assert "invalid_propagation_targets" in wvr.validate_declaration(mixed_targets)


def test_empty_registry_cannot_claim_complete_procedure_validation():
    result = evaluate(
        declarations=[],
        receipts=[],
        enabled_system_ids=[],
        system_exemptions={},
        now="2026-07-10T00:00:00Z",
    )

    assert result["summary"]["required_procedures"] == 0
    assert result["summary"]["inventory_complete"] is True
    assert result["summary"]["can_claim_complete_procedure_validation"] is False
    assert result["summary"]["global_certification_status"] == "not_certified"


def test_receipt_contract_rejects_malformed_list_members_and_authority_ref(tmp_path):
    candidate = receipt(
        tmp_path,
        evidence_refs=[str(write_evidence(tmp_path, "valid.json")), {"not": "a path"}],
        side_effects_observed=["browser_auth", {"not": "an effect"}],
        authority={"status": "granted", "ref": {"not": "a string"}},
    )
    issues = wvr.validate_receipt(candidate, declaration(), wvr.parse_time("2026-07-10T00:30:00Z"))
    assert "missing_evidence_ref" in issues
    assert "invalid_side_effects_observed" in issues
    assert "authority_not_granted" in issues


def test_receipt_rejects_directory_evidence_and_unverifiable_authority(tmp_path):
    nonexistent = tmp_path / "missing-grant.json"
    candidate = receipt(
        tmp_path,
        evidence_refs=[str(tmp_path)],
        authority={"status": "granted", "ref": str(nonexistent)},
    )
    issues = wvr.validate_receipt(candidate, declaration(), wvr.parse_time("2026-07-10T00:30:00Z"))
    assert "missing_evidence_ref" in issues
    assert "authority_not_granted" in issues


def test_receipt_rejects_evidence_below_symlinked_ancestor(tmp_path):
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    evidence = write_evidence(real_dir)
    linked_dir = tmp_path / "linked"
    linked_dir.symlink_to(real_dir, target_is_directory=True)
    candidate = receipt(tmp_path, evidence_refs=[str(linked_dir / evidence.name)])
    issues = wvr.validate_receipt(candidate, declaration(), wvr.parse_time("2026-07-10T00:30:00Z"))
    assert "missing_evidence_ref" in issues


def test_receipt_rejects_authority_grant_scope_action_and_identity_mismatch(tmp_path):
    grant = write_authority_grant(
        tmp_path,
        "mismatched-authority.json",
        procedure_id="another.procedure",
        system_id="another-system",
        action="external_send",
        scope="unrelated-scope",
    )
    candidate = receipt(tmp_path, authority={"status": "granted", "ref": str(grant)})
    issues = wvr.validate_receipt(candidate, declaration(), wvr.parse_time("2026-07-10T00:30:00Z"))
    assert "authority_not_granted" in issues


def test_receipt_rejects_self_authored_grant_outside_trusted_root(tmp_path):
    grant = tmp_path / "authority-grant.json"
    grant.write_text(json.dumps({
        "schema": "hermes_procedure_authority_grant_v1",
        "grant_id": "authority-grant",
        "status": "active",
        "procedure_id": "lark.oauth.recovery",
        "system_id": "profile:lark",
        "action": "execute_live_e2e_validation",
        "scope": "lark.oauth.recovery",
        "receipt_id": "r-001",
        "issued_by": "human_authority",
        "valid_from": "2026-07-09T00:00:00Z",
        "expires_at": "2026-07-11T00:00:00Z",
    }), encoding="utf-8")
    candidate = receipt(tmp_path, authority={
        "status": "granted",
        "ref": str(grant),
        "sha256": hashlib.sha256(grant.read_bytes()).hexdigest(),
    })
    issues = wvr.validate_receipt(candidate, declaration(), wvr.parse_time("2026-07-10T00:30:00Z"))
    assert "authority_not_granted" in issues


def test_receipt_rejects_authority_digest_issuer_and_execution_window_mismatch(tmp_path):
    cases = (
        ({"sha256": "0" * 64}, {}),
        ({}, {"issued_by": "receipt_producer"}),
        ({}, {"expires_at": "2026-07-09T23:59:59Z"}),
        ({}, {"valid_from": "2026-07-10T00:00:30Z"}),
    )
    for index, (authority_overrides, grant_overrides) in enumerate(cases):
        grant = write_authority_grant(tmp_path, f"authority-mismatch-{index}.json", **grant_overrides)
        authority = {
            "status": "granted",
            "ref": str(grant),
            "sha256": hashlib.sha256(grant.read_bytes()).hexdigest(),
            **authority_overrides,
        }
        candidate = receipt(tmp_path, authority=authority)
        issues = wvr.validate_receipt(candidate, declaration(), wvr.parse_time("2026-07-10T00:30:00Z"))
        assert "authority_not_granted" in issues


def test_authority_grant_digest_and_parse_use_one_byte_snapshot(tmp_path, monkeypatch):
    grant = write_authority_grant(tmp_path, "single-snapshot.json")
    candidate = receipt(tmp_path, authority={
        "status": "granted",
        "ref": str(grant),
        "sha256": hashlib.sha256(grant.read_bytes()).hexdigest(),
    })
    original_read = wvr._read_regular_file_no_symlinks
    calls = {"snapshot": 0}

    def tracked_read(path, **kwargs):
        assert path == grant.absolute()
        calls["snapshot"] += 1
        return original_read(path, **kwargs)

    monkeypatch.setattr(wvr, "_read_regular_file_no_symlinks", tracked_read)

    issues = wvr.validate_receipt(candidate, declaration(), wvr.parse_time("2026-07-10T00:30:00Z"))

    assert "authority_not_granted" not in issues
    assert calls == {"snapshot": 1}


def test_receipt_rejects_non_utf8_authority_grant_without_crashing(tmp_path):
    grant = TEST_AUTHORITY_ROOT / "non-utf8.json"
    grant.write_bytes(b"\xff\xfe\x00")
    candidate = receipt(tmp_path, authority={
        "status": "granted",
        "ref": str(grant),
        "sha256": hashlib.sha256(grant.read_bytes()).hexdigest(),
    })

    issues = wvr.validate_receipt(candidate, declaration(), wvr.parse_time("2026-07-10T00:30:00Z"))

    assert "authority_not_granted" in issues


def test_fresh_complete_receipt_produces_fully_connected_candidate(tmp_path):
    result = evaluate(
        declarations=[declaration()],
        receipts=[receipt(tmp_path)],
        enabled_system_ids=["profile:lark"],
        system_exemptions={},
        now="2026-07-10T00:30:00Z",
    )

    procedure = result["procedures"][0]
    assert procedure["validation_state"] == "e2e_passed"
    assert procedure["delivery_state"] == "fully_connected"
    assert procedure["operational_state"] == "healthy"
    assert result["summary"]["fully_connected"] == 1
    assert result["summary"]["can_claim_complete_procedure_validation"] is True
    assert result["summary"]["global_certification_status"] == "candidate_not_certified"


def test_missing_receipt_with_authority_requirement_is_blocked_not_failed():
    result = evaluate(
        declarations=[declaration()],
        receipts=[],
        enabled_system_ids=["profile:lark"],
        system_exemptions={},
        now="2026-07-10T00:30:00Z",
    )

    procedure = result["procedures"][0]
    assert procedure["validation_state"] == "blocked_by_authority"
    assert procedure["delivery_state"] == "blocked"
    assert procedure["operational_state"] == "unknown"
    assert "procedure_authority_blocked" in procedure["findings"]
    assert "procedure_e2e_failed" not in procedure["findings"]


def test_missing_receipt_without_authority_is_landed_unverified():
    result = evaluate(
        declarations=[declaration(authority_policy="none")],
        receipts=[],
        enabled_system_ids=["profile:lark"],
        system_exemptions={},
        now="2026-07-10T00:30:00Z",
    )

    procedure = result["procedures"][0]
    assert procedure["validation_state"] == "untested"
    assert procedure["delivery_state"] == "landed_unverified"
    assert "procedure_validation_pending" in procedure["findings"]


def test_expired_receipt_is_stale_and_blocks_complete_claim(tmp_path):
    result = evaluate(
        declarations=[declaration(freshness_seconds=60)],
        receipts=[receipt(tmp_path)],
        enabled_system_ids=["profile:lark"],
        system_exemptions={},
        now="2026-07-10T00:30:00Z",
    )

    procedure = result["procedures"][0]
    assert procedure["validation_state"] == "stale"
    assert procedure["delivery_state"] == "landed_unverified"
    assert "procedure_validation_stale" in procedure["findings"]
    assert result["summary"]["can_claim_complete_procedure_validation"] is False


def test_missing_evidence_or_acceptance_atom_rejects_receipt(tmp_path):
    missing = tmp_path / "does-not-exist.json"
    broken = receipt(
        tmp_path,
        evidence_refs=[str(missing)],
        acceptance_atoms={"callback_received": True, "token_valid": False},
    )
    result = evaluate(
        declarations=[declaration()],
        receipts=[broken],
        enabled_system_ids=["profile:lark"],
        system_exemptions={},
        now="2026-07-10T00:30:00Z",
    )

    procedure = result["procedures"][0]
    assert procedure["validation_state"] == "e2e_failed"
    assert "missing_evidence_ref" in procedure["receipt_issues"]
    assert "acceptance_atom_not_passed:token_valid" in procedure["receipt_issues"]


def test_forbidden_or_undeclared_side_effect_fails_closed(tmp_path):
    broken = receipt(tmp_path, side_effects_observed=["browser_auth", "external_write"])
    result = evaluate(
        declarations=[declaration()],
        receipts=[broken],
        enabled_system_ids=["profile:lark"],
        system_exemptions={},
        now="2026-07-10T00:30:00Z",
    )

    procedure = result["procedures"][0]
    assert procedure["validation_state"] == "e2e_failed"
    assert "undeclared_side_effect:external_write" in procedure["receipt_issues"]


def test_authority_mismatch_fails_closed(tmp_path):
    broken = receipt(tmp_path, authority={"status": "not_required", "ref": ""})
    result = evaluate(
        declarations=[declaration()],
        receipts=[broken],
        enabled_system_ids=["profile:lark"],
        system_exemptions={},
        now="2026-07-10T00:30:00Z",
    )

    procedure = result["procedures"][0]
    assert procedure["validation_state"] == "e2e_failed"
    assert "authority_not_granted" in procedure["receipt_issues"]


def test_duplicate_receipt_ids_do_not_satisfy_independent_success_threshold(tmp_path):
    first = receipt(tmp_path, receipt_id="same-id", completed_at="2026-07-10T00:01:00Z")
    duplicate = receipt(tmp_path, receipt_id="same-id", completed_at="2026-07-10T00:02:00Z")
    result = evaluate(
        declarations=[declaration(min_independent_successes=2)],
        receipts=[first, duplicate],
        enabled_system_ids=["profile:lark"],
        system_exemptions={},
        now="2026-07-10T00:30:00Z",
    )

    procedure = result["procedures"][0]
    assert procedure["successful_receipt_count"] == 1
    assert procedure["delivery_state"] == "partially_landed"
    assert "ratchet_threshold_not_met" in procedure["findings"]


def test_authority_grant_cannot_be_reused_for_distinct_receipt_execution(tmp_path):
    first = receipt(tmp_path, receipt_id="r-one", completed_at="2026-07-10T00:01:00Z")
    second = receipt(
        tmp_path,
        receipt_id="r-two",
        completed_at="2026-07-10T00:02:00Z",
        authority=dict(first["authority"]),
    )
    result = evaluate(
        declarations=[declaration(min_independent_successes=2)],
        receipts=[first, second],
        enabled_system_ids=["profile:lark"],
        system_exemptions={},
        now="2026-07-10T00:30:00Z",
    )

    procedure = result["procedures"][0]
    assert procedure["successful_receipt_count"] == 1
    assert procedure["delivery_state"] == "partially_landed"
    assert "authority_not_granted" in procedure["receipt_issues"]


def test_receipt_completed_far_in_future_is_rejected(tmp_path):
    future = receipt(
        tmp_path,
        started_at="2026-07-10T01:00:00Z",
        completed_at="2026-07-10T01:01:00Z",
    )
    result = evaluate(
        declarations=[declaration()],
        receipts=[future],
        enabled_system_ids=["profile:lark"],
        system_exemptions={},
        now="2026-07-10T00:30:00Z",
    )

    procedure = result["procedures"][0]
    assert procedure["validation_state"] == "e2e_failed"
    assert "completed_at_in_future" in procedure["receipt_issues"]


def test_unknown_receipt_and_unmapped_enabled_system_are_inventory_findings(tmp_path):
    unknown = receipt(tmp_path, procedure_id="unknown.flow")
    result = evaluate(
        declarations=[declaration(required=False)],
        receipts=[unknown],
        enabled_system_ids=["profile:lark", "delivery:telegram"],
        system_exemptions={},
        now="2026-07-10T00:30:00Z",
    )

    assert result["summary"]["inventory_complete"] is False
    assert result["inventory"]["unmapped_system_ids"] == ["delivery:telegram"]
    assert result["inventory"]["unknown_receipt_procedure_ids"] == ["unknown.flow"]
    assert result["summary"]["can_claim_complete_procedure_validation"] is False


def test_explicit_system_exemption_closes_inventory_without_certifying_optional_flow():
    result = evaluate(
        declarations=[],
        receipts=[],
        enabled_system_ids=["profile:reference-only"],
        system_exemptions={"profile:reference-only": "profile artifact only; no runtime procedure in this control plane"},
        now="2026-07-10T00:30:00Z",
    )

    assert result["summary"]["inventory_complete"] is True
    assert result["inventory"]["unmapped_system_ids"] == []
    assert result["summary"]["can_claim_complete_procedure_validation"] is False
    assert result["summary"]["global_certification_status"] == "not_certified"


def test_independent_success_threshold_ratchets_before_full_connection(tmp_path):
    first = receipt(tmp_path, receipt_id="r-001")
    result = evaluate(
        declarations=[declaration(min_independent_successes=2)],
        receipts=[first],
        enabled_system_ids=["profile:lark"],
        system_exemptions={},
        now="2026-07-10T00:30:00Z",
    )

    procedure = result["procedures"][0]
    assert procedure["validation_state"] == "e2e_passed"
    assert procedure["delivery_state"] == "partially_landed"
    assert procedure["successful_receipt_count"] == 1
    assert "ratchet_threshold_not_met" in procedure["findings"]


def test_mapped_system_without_fresh_inventory_attestation_remains_inventory_gap(tmp_path):
    result = wvr.evaluate_registry(
        declarations=[declaration(required=False)],
        receipts=[],
        enabled_system_ids=["profile:lark"],
        system_exemptions={},
        system_inventory_attestations={},
        now="2026-07-10T10:00:00Z",
    )

    assert result["inventory"]["unattested_system_ids"] == ["profile:lark"]
    assert result["summary"]["inventory_complete"] is False
    assert result["summary"]["can_claim_complete_procedure_validation"] is False


def test_inventory_attestation_far_in_future_fails_closed(tmp_path):
    result = wvr.evaluate_registry(
        declarations=[declaration(required=False)],
        receipts=[],
        enabled_system_ids=["profile:lark"],
        system_exemptions={},
        system_inventory_attestations={
            "profile:lark": {
                "scope_complete": True,
                "reviewed_at": "2099-01-01T00:00:00Z",
                "freshness_seconds": 86400,
                "basis": "future-dated fixture must not pass",
            }
        },
        now="2026-07-10T10:00:00Z",
    )

    attestation = result["inventory"]["system_inventory_attestations"]["profile:lark"]
    assert attestation["valid"] is False
    assert attestation["future_dated"] is True
    assert result["inventory"]["unattested_system_ids"] == ["profile:lark"]
    assert result["summary"]["inventory_complete"] is False
    assert result["summary"]["can_claim_complete_procedure_validation"] is False


def test_inventory_attestation_one_second_in_future_fails_closed():
    result = wvr.evaluate_registry(
        declarations=[declaration(required=False)],
        receipts=[],
        enabled_system_ids=["profile:lark"],
        system_exemptions={},
        system_inventory_attestations={
            "profile:lark": {
                "scope_complete": True,
                "reviewed_at": "2026-07-10T10:00:01Z",
                "freshness_seconds": 1,
                "basis": "any future-dated attestation must fail closed",
            }
        },
        now="2026-07-10T10:00:00Z",
    )
    attestation = result["inventory"]["system_inventory_attestations"]["profile:lark"]
    assert attestation["valid"] is False
    assert attestation["future_dated"] is True
    assert result["summary"]["inventory_complete"] is False


def test_previous_full_connection_is_demoted_when_latest_receipt_expires(tmp_path):
    result = evaluate(
        declarations=[declaration(freshness_seconds=60)],
        receipts=[receipt(tmp_path)],
        enabled_system_ids=["profile:lark"],
        system_exemptions={},
        previous_registry={
            "procedures": [{"procedure_id": "lark.oauth.recovery", "delivery_state": "fully_connected"}]
        },
        now="2026-07-10T00:30:00Z",
    )

    procedure = result["procedures"][0]
    assert procedure["ratchet_transition"] == "demoted:fully_connected->landed_unverified"
    assert procedure["promotion_allowed"] is False


def test_cli_evaluate_writes_deterministic_readback(tmp_path):
    definitions = tmp_path / "definitions.json"
    receipts = tmp_path / "receipts"
    receipts.mkdir()
    evidence = write_evidence(tmp_path)
    definitions.write_text(json.dumps({
        "schema": "hermes_procedure_definitions_v1",
        "procedures": [declaration(authority_policy="none")],
        "system_exemptions": {},
    }), encoding="utf-8")
    (receipts / "r-001.json").write_text(json.dumps(receipt(tmp_path, evidence_refs=[str(evidence)])), encoding="utf-8")
    output = tmp_path / "registry.json"

    exit_code = wvr.main([
        "evaluate",
        "--definitions", str(definitions),
        "--receipts-dir", str(receipts),
        "--enabled-system", "profile:lark",
        "--now", "2026-07-10T00:30:00Z",
        "--out", str(output),
    ])

    assert exit_code == 0
    loaded = json.loads(output.read_text(encoding="utf-8"))
    assert loaded["summary"]["fully_connected"] == 1
