from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

from loop_a_protected.authority import (
    finalize_authorization,
    finalize_authorization_payload,
    parse_authority_grant_wire,
)
from loop_a_protected.canonical import canonical_bytes
from loop_a_protected.installer_journal import finalize_installer_record
from loop_a_protected.policy import finalize_rollback_floor
from loop_a_protected.states import INSTALLER_PATHS
from loop_a_protected.swap_evidence import evidence_filename, finalize_swap_evidence
from test_loop_a_protected_authority import D, D2, D3, U2, payload_preimage
from test_loop_a_protected_installer_journal import fields


def make_authorization(operation: str, destination: str) -> Dict[str, Any]:
    preimage = payload_preimage()
    if (operation, destination) == ("update-floor", "rollback-floor"):
        floor = finalize_rollback_floor(
            2, U2, 1,
            [
                {"kind": "active-skills", "release_sequence": 1, "manifest_digest": D2,
                 "inventory_digest": D3, "disposition": "forward"},
                {"kind": "runtime", "release_sequence": 1, "manifest_digest": D,
                 "inventory_digest": D2, "disposition": "forward"},
            ],
            "2026-08-03T01:00:00Z", D, "auth-1",
        )
        preimage.update(
            operation=operation,
            exact_destination=destination,
            policy_generation=2,
            release_sequence=None,
            smoke_transaction_uuid=None,
            protected_source_digest=None,
            candidate_digest=None,
            expected_current_manifest_digest=None,
            expected_current_inventory_digest=None,
            target_manifest_digest=None,
            target_inventory_digest=None,
            initial_target_bundle=None,
            initial_target_bundle_digest=None,
            proposed_floor=floor,
            proposed_floor_digest=floor["record_digest"],
        )
    elif (operation, destination) != ("promote-runtime", "runtime"):
        raise ValueError("unsupported swap-test authorization")
    payload = finalize_authorization_payload(preimage)
    wire = (
        "HERMES-AUTH-V1 authorization_id=" + payload["authorization_id"] +
        " payload_sha256=" + payload["payload_digest"] +
        " operation=" + operation + " destination=" + destination +
        " issued_at=" + payload["issued_at"] + " expires_at=" + payload["expires_at"] +
        " nonce=" + payload["nonce"] + "\n"
    ).encode("ascii")
    grant = parse_authority_grant_wire(wire)
    return finalize_authorization(payload, grant)


def make_swap_evidence(*, authorization: Dict[str, Any], sequence: int, state: str, role: str,
                       parent_status: os.stat_result, current_name: str, current_status: os.stat_result,
                       staged_name: str, staged_status: os.stat_result,
                       current_digest: str | None = None, staged_digest: str | None = None,
                       current_target: str | None = None, staged_target: str | None = None) -> Dict[str, Any]:
    return finalize_swap_evidence({
        "schema": 1,
        "transaction_uuid": authorization["authorization_payload"]["transaction_uuid"],
        "sequence": sequence,
        "state": state,
        "role": role,
        "parent_device": parent_status.st_dev,
        "parent_inode": parent_status.st_ino,
        "current_name": current_name,
        "current_device": current_status.st_dev,
        "current_inode": current_status.st_ino,
        "current_digest": current_digest,
        "current_target": current_target,
        "staged_name": staged_name,
        "staged_device": staged_status.st_dev,
        "staged_inode": staged_status.st_ino,
        "staged_digest": staged_digest,
        "staged_target": staged_target,
        "record_digest": None,
    })


def _bind_authorization(record: Dict[str, Any], authorization: Dict[str, Any]) -> None:
    payload = authorization["authorization_payload"]
    direct = (
        "authorization_id", "transaction_uuid", "policy_generation", "release_lineage",
        "release_sequence", "prior_floor_digest", "proposed_floor_digest",
        "expected_current_manifest_digest", "expected_current_inventory_digest",
        "target_manifest_digest", "target_inventory_digest", "initial_target_bundle_digest",
        "architecture_digest", "protocol_appendix_digest", "schema_bundle_digest",
        "authority_packet_digest", "installer_manifest_digest", "runtime_manifest_digest",
        "red_evidence_digest", "scheduler_before_digest", "scheduler_action",
        "smoke_transaction_uuid",
    )
    for name in direct:
        record[name] = payload[name]
    record.update(
        payload_digest=authorization["payload_digest"],
        authorization_digest=authorization["authorization_digest"],
        authority_grant_digest=authorization["authority_grant_digest"],
        on_demand_plist_digest=payload["scheduler_action"]["on_demand_plist_digest"],
        final_plist_digest=payload["scheduler_action"]["final_plist_digest"],
    )


def provision_swap_journal(root: Path, authorization: Dict[str, Any], state: str,
                           role: str, evidence: Dict[str, Any]) -> None:
    payload = authorization["authorization_payload"]
    path = INSTALLER_PATHS[(payload["operation"], payload["exact_destination"])]
    states = path[1:path.index(state) + 1]
    transaction = root / "installer-transactions" / payload["transaction_uuid"]
    records_dir = transaction / "records"
    evidence_dir = transaction / "evidence"
    records_dir.mkdir(parents=True)
    evidence_dir.mkdir()
    (transaction / "snapshots").mkdir()
    os.chmod(root / "installer-transactions", 0o700)
    os.chmod(transaction, 0o700)
    for child in (records_dir, evidence_dir, transaction / "snapshots"):
        os.chmod(child, 0o700)
    prior = None
    for sequence, item_state in enumerate(states, 1):
        record = fields(payload["operation"], payload["exact_destination"], item_state, sequence, prior)
        _bind_authorization(record, authorization)
        if item_state == state:
            if evidence["sequence"] != sequence:
                raise ValueError("swap evidence sequence differs from durable journal sequence")
            record["operation_evidence"] = [
                {"name": f"swap-evidence:{role}", "passed": True,
                 "detail_digest": evidence["record_digest"]},
            ]
            if role.endswith("-pointer"):
                record["pointer_inventory"] = {
                    "kind": "runtime" if role == "runtime-pointer" else "active-skills",
                    "name": evidence["staged_name"], "target": evidence["staged_target"],
                    "device": evidence["staged_device"], "inode": evidence["staged_inode"],
                    "manifest_digest": payload["target_manifest_digest"],
                    "inventory_digest": payload["target_inventory_digest"],
                }
        finalized = finalize_installer_record(
            record, payload["operation"], payload["exact_destination"],
        )
        record_path = records_dir / f"{sequence:08d}-{item_state}.json"
        record_path.write_bytes(canonical_bytes(finalized))
        os.chmod(record_path, 0o400)
        prior = finalized["record_digest"]
    evidence_path = evidence_dir / evidence_filename(evidence["sequence"], role)
    evidence_path.write_bytes(canonical_bytes(evidence))
    os.chmod(evidence_path, 0o400)
