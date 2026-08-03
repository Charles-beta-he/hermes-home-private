from __future__ import annotations

import pytest

from loop_a_protected.installer_journal import (
    InstallerJournalError,
    finalize_installer_record,
    validate_installer_chain,
)
from loop_a_protected.states import INSTALLER_PATHS

D = "ab" * 32
TXN = "123e4567-e89b-42d3-a456-426614174000"
LINEAGE = "123e4567-e89b-42d3-a456-426614174001"
SMOKE = "123e4567-e89b-42d3-a456-426614174002"


def fields(operation, destination, state, sequence, prior):
    initial = operation == "install-initial"
    single = operation in {"promote-runtime", "promote-skill", "rollback-protected"}
    proposed_floor = operation in {"install-initial", "update-floor"}
    tree_kind = "runtime" if state.startswith("RUNTIME_TREE_") else "active-skills" if state.startswith("SKILL_TREE_") else None
    pointer_kind = "runtime" if state.startswith("RUNTIME_POINTER_") else "active-skills" if state.startswith("SKILL_POINTER_") else None
    tree_inventory = None if tree_kind is None else {"kind": tree_kind, "entries": []}
    pointer_inventory = None if pointer_kind is None else {
        "kind": pointer_kind, "name": f".{pointer_kind}.next", "target": f"versions/{D}",
        "device": 1, "inode": sequence, "manifest_digest": D, "inventory_digest": D,
    }
    return {
        "schema": 1, "transaction_uuid": TXN, "sequence": sequence, "prior_record_digest": prior,
        "state": state, "timestamp": f"2026-08-03T01:00:{sequence:02d}Z", "authorization_id": "auth-1",
        "payload_digest": D, "authorization_digest": D, "authority_grant_digest": D,
        "policy_generation": 1, "release_lineage": LINEAGE, "release_sequence": 1 if single else None,
        "prior_floor_digest": None if initial else D, "proposed_floor_digest": D if proposed_floor else None,
        "expected_current_manifest_digest": D if single else None,
        "expected_current_inventory_digest": D if single else None,
        "target_manifest_digest": D if single else None, "target_inventory_digest": D if single else None,
        "initial_target_bundle_digest": D if initial else None, "architecture_digest": D,
        "protocol_appendix_digest": D, "schema_bundle_digest": D, "authority_packet_digest": D,
        "installer_manifest_digest": D, "runtime_manifest_digest": D, "red_evidence_digest": D,
        "scheduler_before_digest": D, "scheduler_action": {
            "old_job_id": "600370f80d83", "expected_enabled": True, "target_enabled": False,
            "launchd_label": "system/com.nous.hermes.loop-a", "launchd_target_state": "disabled-unloaded",
            "on_demand_plist_digest": D if initial else None, "final_plist_digest": D,
        },
        "smoke_transaction_uuid": SMOKE if initial else None, "smoke_gate_digest": D if initial else None,
        "on_demand_plist_digest": D if initial else None, "final_plist_digest": D,
        "tree_inventory": tree_inventory, "pointer_inventory": pointer_inventory,
        "operation_evidence": [{"name": "held-fd-readback", "passed": True, "detail_digest": D}],
        "record_digest": None,
    }


def chain_for(operation, destination):
    result = []
    prior = None
    for sequence, state in enumerate(INSTALLER_PATHS[(operation, destination)][1:], 1):
        record = finalize_installer_record(fields(operation, destination, state, sequence, prior), operation, destination)
        result.append(record)
        prior = record["record_digest"]
    return result


@pytest.mark.parametrize("operation,destination", sorted(INSTALLER_PATHS))
def test_every_exact_operation_path_commits(operation, destination):
    records = chain_for(operation, destination)
    validate_installer_chain(records, operation, destination)
    assert records[-1]["state"] == "COMMITTED"


def test_operation_path_substitution_and_direct_commit_are_rejected():
    runtime = chain_for("promote-runtime", "runtime")
    with pytest.raises(InstallerJournalError):
        validate_installer_chain(runtime, "promote-skill", "active-skills")
    with pytest.raises(InstallerJournalError):
        validate_installer_chain([runtime[0], runtime[-1]], "promote-runtime", "runtime")


def test_recovery_required_only_rolls_back_and_never_verifies():
    prepared = finalize_installer_record(fields("update-floor", "rollback-floor", "PREPARED", 1, None), "update-floor", "rollback-floor")
    consumed = finalize_installer_record(fields("update-floor", "rollback-floor", "AUTH_CONSUMED", 2, prepared["record_digest"]), "update-floor", "rollback-floor")
    recovery = finalize_installer_record(fields("update-floor", "rollback-floor", "RECOVERY_REQUIRED", 3, consumed["record_digest"]), "update-floor", "rollback-floor")
    verified = finalize_installer_record(fields("update-floor", "rollback-floor", "VERIFIED", 4, recovery["record_digest"]), "update-floor", "rollback-floor")
    with pytest.raises(InstallerJournalError):
        validate_installer_chain([prepared, consumed, recovery, verified], "update-floor", "rollback-floor")
    rolled = finalize_installer_record(fields("update-floor", "rollback-floor", "ROLLED_BACK", 4, recovery["record_digest"]), "update-floor", "rollback-floor")
    validate_installer_chain([prepared, consumed, recovery, rolled], "update-floor", "rollback-floor")


def test_kind_qualified_tree_or_pointer_evidence_cannot_be_substituted():
    bad = fields("promote-runtime", "runtime", "RUNTIME_TREE_STAGED", 3, D)
    bad["tree_inventory"] = {"kind": "active-skills", "entries": []}
    with pytest.raises(InstallerJournalError, match="kind"):
        finalize_installer_record(bad, "promote-runtime", "runtime")
