from __future__ import annotations

import os
from typing import Any, Dict

from .authority import AuthorityError, validate_authorization
from .canonical import CanonicalJSONError, parse_canonical_bytes, with_self_digest
from .fd_gateway import CleanMetadataAdapter, FdGatewayError, _validate_metadata, read_regular_file_at_identity
from .root_gate import RootMutationGate
from .schema_bundle import SchemaBundleError, validate_instance


class SwapEvidenceError(OSError):
    pass


def finalize_swap_evidence(preimage: Dict[str, Any]) -> Dict[str, Any]:
    try:
        validate_instance("swap-evidence-preimage-v1", preimage)
        finalized = with_self_digest(preimage, "record_digest")
        validate_instance("swap-evidence-final-v1", finalized)
        _validate_semantics(finalized)
        return finalized
    except (SchemaBundleError, CanonicalJSONError, KeyError, TypeError, ValueError) as exc:
        raise SwapEvidenceError("invalid swap evidence") from exc


def evidence_filename(sequence: int, role: str) -> str:
    if not isinstance(sequence, int) or sequence < 1 or role not in {
        "rollback-floor", "epoch", "launchdaemon-plist", "runtime-pointer", "active-skills-pointer",
    }:
        raise ValueError("invalid swap evidence identity")
    return f"{sequence:08d}-{role}-swap.json"


def _validate_basename(name: str, label: str) -> None:
    if not isinstance(name, str) or not name or name in {".", ".."} or "/" in name or "\x00" in name:
        raise SwapEvidenceError(f"invalid swap evidence {label}")


def _validate_self_digest(value: Dict[str, Any]) -> None:
    preimage = dict(value)
    observed = preimage["record_digest"]
    preimage["record_digest"] = None
    if with_self_digest(preimage, "record_digest")["record_digest"] != observed:
        raise SwapEvidenceError("swap evidence self-digest mismatch")


def _validate_semantics(value: Dict[str, Any]) -> None:
    _validate_basename(value["current_name"], "current name")
    _validate_basename(value["staged_name"], "staged name")
    if value["current_name"] == value["staged_name"]:
        raise SwapEvidenceError("swap evidence names alias")
    transaction_uuid = value["transaction_uuid"]
    role = value["role"]
    if role.endswith("-pointer"):
        expected = f".current.txn-{transaction_uuid}.tmp"
        if value["current_name"] != "current" or value["staged_name"] != expected:
            raise SwapEvidenceError("pointer staged name is not exact transaction-qualified name")
        if (value["current_digest"], value["staged_digest"]) != (None, None):
            raise SwapEvidenceError("pointer evidence cannot carry byte digests")
        if not isinstance(value["current_target"], str) or not isinstance(value["staged_target"], str):
            raise SwapEvidenceError("pointer evidence requires exact targets")
    else:
        expected = f".{value['current_name']}.txn-{transaction_uuid}.tmp"
        if value["staged_name"] != expected:
            raise SwapEvidenceError("regular staged name is not exact transaction-qualified name")
        if (value["current_target"], value["staged_target"]) != (None, None):
            raise SwapEvidenceError("regular-file evidence cannot carry pointer targets")
        if not isinstance(value["current_digest"], str) or not isinstance(value["staged_digest"], str):
            raise SwapEvidenceError("regular-file evidence requires exact digests")


def _open_directory(parent_fd: int, name: str, device: int, uid: int, gid: int,
                    metadata: CleanMetadataAdapter) -> int:
    fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent_fd)
    try:
        _validate_metadata(fd, "directory", device, uid, gid, 0o700, metadata)
        return fd
    except BaseException:
        os.close(fd)
        raise


def load_bound_swap_evidence(*, gate: RootMutationGate, authorization: Dict[str, Any],
                             expected_state: str, expected_role: str,
                             uid: int, gid: int, metadata: CleanMetadataAdapter) -> Dict[str, Any]:
    from .journal_store import read_journal_records

    transactions_fd = transaction_fd = records_fd = evidence_fd = -1
    try:
        gate.assert_live()
        validate_authorization(authorization)
        payload = authorization["authorization_payload"]
        root = os.fstat(gate.root_fd)
        if (root.st_dev, root.st_ino) != gate.root_identity:
            raise SwapEvidenceError("swap evidence root identity mismatch")
        transactions_fd = _open_directory(
            gate.root_fd, "installer-transactions", root.st_dev, uid, gid, metadata,
        )
        transaction_fd = _open_directory(
            transactions_fd, payload["transaction_uuid"], root.st_dev, uid, gid, metadata,
        )
        if set(os.listdir(transaction_fd)) != {"records", "snapshots", "evidence"}:
            raise SwapEvidenceError("installer transaction namespace child set mismatch")
        records_fd = _open_directory(transaction_fd, "records", root.st_dev, uid, gid, metadata)
        evidence_fd = _open_directory(transaction_fd, "evidence", root.st_dev, uid, gid, metadata)
        records = read_journal_records(
            records_fd, uid, gid, metadata, journal_kind="installer",
            operation=payload["operation"], destination=payload["exact_destination"],
            authorization=authorization,
        )
        if not records or records[-1]["state"] != expected_state:
            raise SwapEvidenceError("durable installer journal state mismatch")
        latest = records[-1]
        assertion_name = f"swap-evidence:{expected_role}"
        assertions = [
            item for item in latest["operation_evidence"]
            if item["name"] == assertion_name and item["passed"] is True
        ]
        if len(assertions) != 1 or assertions[0]["detail_digest"] is None:
            raise SwapEvidenceError("durable installer record lacks unique swap evidence binding")
        data, _identity = read_regular_file_at_identity(
            evidence_fd, evidence_filename(latest["sequence"], expected_role), 2, 64 * 1024,
            uid, gid, 0o400, metadata,
        )
        value = parse_canonical_bytes(data)
        validate_instance("swap-evidence-final-v1", value)
        _validate_self_digest(value)
        _validate_semantics(value)
        if value["record_digest"] != assertions[0]["detail_digest"]:
            raise SwapEvidenceError("swap evidence digest differs from durable journal binding")
        if (value["transaction_uuid"], value["sequence"], value["state"], value["role"]) != (
            payload["transaction_uuid"], latest["sequence"], expected_state, expected_role,
        ):
            raise SwapEvidenceError("swap evidence transaction/state binding mismatch")
        return value
    except SwapEvidenceError:
        raise
    except (AuthorityError, CanonicalJSONError, FdGatewayError,
            SchemaBundleError, OSError, KeyError, TypeError, ValueError) as exc:
        raise SwapEvidenceError("durable swap evidence cannot be proven") from exc
    finally:
        for fd in (evidence_fd, records_fd, transaction_fd, transactions_fd):
            if fd >= 0:
                os.close(fd)
