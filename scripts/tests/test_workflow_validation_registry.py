import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import workflow_validation_registry as wvr


def evaluate(**kwargs):
    kwargs.setdefault(
        "system_inventory_attestations",
        {
            "profile:lark": {
                "scope_complete": True,
                "reviewed_at": "2026-07-10T09:00:00Z",
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
        "freshness_seconds": 3600,
        "min_independent_successes": 1,
        "required_acceptance_atoms": ["callback_received", "token_valid"],
        "required_negative_assertions": ["no_task_read", "no_lark_write"],
    }
    value.update(overrides)
    return value


def write_evidence(tmp_path: Path, name: str = "evidence.json") -> Path:
    path = tmp_path / name
    path.write_text("{}\n", encoding="utf-8")
    return path


def receipt(tmp_path: Path, **overrides):
    evidence = write_evidence(tmp_path)
    value = {
        "schema": "hermes_procedure_e2e_receipt_v1",
        "receipt_id": "r-001",
        "procedure_id": "lark.oauth.recovery",
        "started_at": "2026-07-10T00:00:00Z",
        "completed_at": "2026-07-10T00:01:00Z",
        "result": "PASS",
        "execution_mode": "live_e2e",
        "evidence_refs": [str(evidence)],
        "acceptance_atoms": {"callback_received": True, "token_valid": True},
        "negative_assertions": {"no_task_read": True, "no_lark_write": True},
        "cleanup_readback": "PASS",
        "authority": {"status": "granted", "ref": "user-grant:scoped"},
        "side_effects_observed": ["browser_auth"],
    }
    value.update(overrides)
    return value


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
    assert result["summary"]["can_claim_complete_procedure_validation"] is True


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
