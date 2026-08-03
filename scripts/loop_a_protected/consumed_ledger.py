from __future__ import annotations

import errno
import hashlib
import os
import re
import stat
from datetime import datetime
from typing import Any, Dict, Tuple

from .authority import AuthorityError, validate_authorization
from .canonical import CanonicalJSONError, canonical_bytes, parse_canonical_bytes, with_self_digest
from .fd_gateway import CleanMetadataAdapter, FdGatewayError, _validate_metadata, read_regular_file_at
from .journal_store import JournalStoreError, read_journal_records
from .publication import PublicationError, publish_regular_file
from .root_gate import RootMutationGate
from .schema_bundle import SchemaBundleError, validate_instance


class AuthorizationConsumedError(ValueError):
    pass


_AUTHORIZATION_ID = re.compile(r"[A-Za-z0-9._:-]+\Z")
_OBSERVATION_FIELDS = {
    "service_epoch", "policy_generation", "release_lineage", "prior_floor_digest",
    "current_manifest_digest", "current_inventory_digest", "scheduler_before_digest",
    "scheduler_action_digest",
}


def consumed_filename(authorization_id: str) -> str:
    if not isinstance(authorization_id, str) or not _AUTHORIZATION_ID.fullmatch(authorization_id):
        raise ValueError("authorization_id must be a canonical ASCII token")
    return f"{authorization_id}.json"


def derive_consumed_record_preimage(authorization: Dict[str, Any], observations: Dict[str, Any],
                                    consumed_at: str) -> Dict[str, Any]:
    try:
        validate_authorization(authorization)
    except AuthorityError as exc:
        raise AuthorizationConsumedError("finalized authorization is invalid") from exc
    if not isinstance(observations, dict) or set(observations) != _OBSERVATION_FIELDS:
        raise AuthorizationConsumedError("live precondition fields differ from exact contract")
    payload = authorization["authorization_payload"]
    try:
        now = datetime.strptime(consumed_at, "%Y-%m-%dT%H:%M:%SZ")
        issued = datetime.strptime(payload["issued_at"], "%Y-%m-%dT%H:%M:%SZ")
        expires = datetime.strptime(payload["expires_at"], "%Y-%m-%dT%H:%M:%SZ")
    except (TypeError, ValueError) as exc:
        raise AuthorizationConsumedError("invalid trusted consumption timestamp") from exc
    if now < issued:
        raise AuthorizationConsumedError("authorization is not yet valid")
    if now >= expires:
        raise AuthorizationConsumedError("authorization is expired")
    scheduler_action_digest = hashlib.sha256(canonical_bytes(payload["scheduler_action"])).hexdigest()
    expected = {
        "service_epoch": payload["service_epoch"],
        "policy_generation": payload["policy_generation"],
        "release_lineage": payload["release_lineage"],
        "prior_floor_digest": payload["prior_floor_digest"],
        "current_manifest_digest": payload["expected_current_manifest_digest"],
        "current_inventory_digest": payload["expected_current_inventory_digest"],
        "scheduler_before_digest": payload["scheduler_before_digest"],
        "scheduler_action_digest": scheduler_action_digest,
    }
    if observations != expected:
        raise AuthorizationConsumedError("live precondition mismatch")
    return {
        "schema": 1, "authorization_id": payload["authorization_id"],
        "payload_digest": payload["payload_digest"],
        "authorization_digest": authorization["authorization_digest"],
        "authority_grant_digest": authorization["authority_grant_digest"],
        "installer_transaction_uuid": payload["transaction_uuid"],
        "smoke_transaction_uuid": payload["smoke_transaction_uuid"],
        "operation": payload["operation"], "destination": payload["exact_destination"],
        "policy_generation": payload["policy_generation"], "release_lineage": payload["release_lineage"],
        "release_sequence": payload["release_sequence"], "prior_floor_digest": payload["prior_floor_digest"],
        "proposed_floor_digest": payload["proposed_floor_digest"], "consumed_at": consumed_at,
        "expected_current_manifest_digest": payload["expected_current_manifest_digest"],
        "expected_current_inventory_digest": payload["expected_current_inventory_digest"],
        "target_manifest_digest": payload["target_manifest_digest"],
        "target_inventory_digest": payload["target_inventory_digest"],
        "initial_target_bundle_digest": payload["initial_target_bundle_digest"],
        "scheduler_action_digest": scheduler_action_digest, "record_digest": None,
    }


def finalize_consumed_record(preimage: Dict[str, Any]) -> Dict[str, Any]:
    try:
        validate_instance("consumed-record-preimage-v1", preimage)
        finalized = with_self_digest(preimage, "record_digest")
        validate_instance("consumed-record-final-v1", finalized)
        return finalized
    except (SchemaBundleError, CanonicalJSONError) as exc:
        raise ValueError(str(exc)) from exc


def _validate_lock(lock_fd: int, parent_device: int, uid: int, lock_gid: int,
                   metadata: CleanMetadataAdapter) -> None:
    status = os.fstat(lock_fd)
    if not stat.S_ISREG(status.st_mode) or status.st_nlink != 1:
        raise AuthorizationConsumedError("ledger lock is not a one-link regular file")
    if status.st_dev != parent_device or (status.st_uid, status.st_gid) != (uid, lock_gid):
        raise AuthorizationConsumedError("installer lock identity or owner mismatch")
    if stat.S_IMODE(status.st_mode) != 0o640 or getattr(status, "st_flags", 0) != 0:
        raise AuthorizationConsumedError("installer lock mode or BSD flags mismatch")
    try:
        if metadata.xattr_bytes(lock_fd) != 0 or metadata.has_extended_acl(lock_fd):
            raise AuthorizationConsumedError("ledger lock has forbidden metadata")
    except AuthorizationConsumedError:
        raise
    except BaseException as exc:
        raise AuthorizationConsumedError("cannot prove ledger lock metadata") from exc


def _read_existing(parent_fd: int, name: str, uid: int, gid: int,
                   metadata: CleanMetadataAdapter) -> Dict[str, Any]:
    try:
        data = read_regular_file_at(parent_fd, name, 1, 1024 * 1024, uid, gid, 0o400, metadata)
        value = parse_canonical_bytes(data)
        validate_instance("consumed-record-final-v1", value)
    except FdGatewayError as exc:
        if exc.errno == errno.ENOENT:
            raise FileNotFoundError(name) from exc
        raise AuthorizationConsumedError("existing consumed record is invalid; installer must fence") from exc
    except (CanonicalJSONError, SchemaBundleError) as exc:
        raise AuthorizationConsumedError("existing consumed record is invalid; installer must fence") from exc
    return value


def _consume_authorization_under_gate(parent_fd: int, lock_fd: int, authorization: Dict[str, Any],
                                      observations: Dict[str, Any], consumed_at: str, uid: int, gid: int,
                                      lock_gid: int, metadata: CleanMetadataAdapter,
                                      gate: RootMutationGate) -> Tuple[Dict[str, Any], bool]:
    try:
        validate_authorization(authorization)
        name = consumed_filename(authorization["authorization_payload"]["authorization_id"])
    except (AuthorityError, KeyError, ValueError, TypeError) as exc:
        raise AuthorizationConsumedError("finalized authorization is invalid") from exc
    parent_status = os.fstat(parent_fd)
    if not stat.S_ISDIR(parent_status.st_mode):
        raise AuthorizationConsumedError("consumed-ledger parent is not a directory")
    _validate_lock(lock_fd, parent_status.st_dev, uid, lock_gid, metadata)
    gate.assert_live()
    finalized = finalize_consumed_record(
        derive_consumed_record_preimage(authorization, observations, consumed_at)
    )
    try:
        existing = _read_existing(parent_fd, name, uid, gid, metadata)
    except FileNotFoundError:
        existing = None
    if existing is not None:
        comparable_fields = set(finalized) - {"consumed_at", "record_digest"}
        if all(existing[field] == finalized[field] for field in comparable_fields):
            raise AuthorizationConsumedError("authorization is already consumed")
        raise AuthorizationConsumedError("authorization is already consumed by another authorization target")
    gate.assert_live()
    try:
        publish_regular_file(parent_fd, name, canonical_bytes(finalized), 0o400, uid, gid,
                             finalized["installer_transaction_uuid"], metadata=metadata)
    except PublicationError as exc:
        raise AuthorizationConsumedError("cannot durably publish consumed authorization record") from exc
    readback = _read_existing(parent_fd, name, uid, gid, metadata)
    if readback != finalized:
        raise AuthorizationConsumedError("consumed authorization readback mismatch")
    gate.assert_live()
    return finalized, True


def _open_canonical_directory(parent_fd: int, name: str, device: int, uid: int, gid: int, mode: int,
                              metadata: CleanMetadataAdapter) -> int:
    try:
        fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent_fd)
        try:
            _validate_metadata(fd, "directory", device, uid, gid, mode, metadata)
        except BaseException:
            os.close(fd)
            raise
        return fd
    except BaseException as exc:
        raise AuthorizationConsumedError(f"cannot validate canonical directory {name}") from exc


def _assert_durable_prepared(root_fd: int, root_device: int, authorization: Dict[str, Any],
                             uid: int, gid: int, metadata: CleanMetadataAdapter) -> None:
    transactions_fd = transaction_fd = records_fd = -1
    payload = authorization["authorization_payload"]
    try:
        transactions_fd = _open_canonical_directory(
            root_fd, "installer-transactions", root_device, uid, gid, 0o700, metadata,
        )
        transaction_fd = _open_canonical_directory(
            transactions_fd, payload["transaction_uuid"], root_device, uid, gid, 0o700, metadata,
        )
        if set(os.listdir(transaction_fd)) != {"records", "snapshots", "evidence"}:
            raise AuthorizationConsumedError("installer transaction namespace child set mismatch")
        records_fd = _open_canonical_directory(
            transaction_fd, "records", root_device, uid, gid, 0o700, metadata,
        )
        records = read_journal_records(
            records_fd, uid, gid, metadata,
            journal_kind="installer", operation=payload["operation"],
            destination=payload["exact_destination"], authorization=authorization,
        )
        if len(records) != 1 or records[0]["sequence"] != 1 or records[0]["state"] != "PREPARED":
            raise AuthorizationConsumedError("authorization consumption requires exactly durable PREPARED")
        os.fsync(records_fd)
        os.fsync(transaction_fd)
        os.fsync(transactions_fd)
    except AuthorizationConsumedError as exc:
        raise AuthorizationConsumedError("durable PREPARED installer transaction cannot be proven") from exc
    except (JournalStoreError, FdGatewayError, OSError, KeyError, TypeError) as exc:
        raise AuthorizationConsumedError("durable PREPARED installer transaction cannot be proven") from exc
    finally:
        for fd in (records_fd, transaction_fd, transactions_fd):
            if fd >= 0:
                os.close(fd)


def consume_authorization(root_fd: int, expected_root_identity: Tuple[int, int],
                          authorization: Dict[str, Any], observations: Dict[str, Any], consumed_at: str,
                          root_uid: int, root_gid: int, lock_gid: int,
                          metadata: CleanMetadataAdapter, *, gate: RootMutationGate) -> Tuple[Dict[str, Any], bool]:
    locks_fd = authorizations_fd = consumed_fd = lock_fd = -1
    try:
        if gate.root_identity != expected_root_identity:
            raise AuthorizationConsumedError("root mutation gate identity mismatch")
        gate.assert_live()
        root_status = os.fstat(root_fd)
        if (root_status.st_dev, root_status.st_ino) != expected_root_identity:
            raise AuthorizationConsumedError("canonical root identity mismatch")
        _validate_metadata(root_fd, "directory", root_status.st_dev, root_uid, root_gid, 0o755, metadata)
        locks_fd = _open_canonical_directory(root_fd, "locks", root_status.st_dev,
                                             root_uid, root_gid, 0o755, metadata)
        authorizations_fd = _open_canonical_directory(root_fd, "authorizations", root_status.st_dev,
                                                      root_uid, root_gid, 0o700, metadata)
        consumed_fd = _open_canonical_directory(authorizations_fd, "consumed", root_status.st_dev,
                                                root_uid, root_gid, 0o700, metadata)
        try:
            lock_fd = os.open("installer.lock", os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=locks_fd)
        except OSError as exc:
            raise AuthorizationConsumedError("cannot open canonical installer lock") from exc
        _validate_lock(lock_fd, root_status.st_dev, root_uid, lock_gid, metadata)
        canonical_lock = os.fstat(lock_fd)
        held_lock = os.fstat(gate.installer_lock_fd)
        if (canonical_lock.st_dev, canonical_lock.st_ino) != (held_lock.st_dev, held_lock.st_ino):
            raise AuthorizationConsumedError("root mutation gate does not hold canonical installer lock")
        payload = authorization["authorization_payload"]
        try:
            existing = _read_existing(
                consumed_fd, consumed_filename(payload["authorization_id"]), root_uid, root_gid, metadata,
            )
        except FileNotFoundError:
            existing = None
        if existing is not None:
            if existing["authorization_digest"] != authorization["authorization_digest"]:
                raise AuthorizationConsumedError("authorization id is already bound to another authorization target")
            raise AuthorizationConsumedError("authorization is already consumed")
        _assert_durable_prepared(
            root_fd, root_status.st_dev, authorization, root_uid, root_gid, metadata,
        )
        gate.assert_live()
        return _consume_authorization_under_gate(
            consumed_fd, gate.installer_lock_fd, authorization, observations, consumed_at,
            root_uid, root_gid, lock_gid, metadata, gate,
        )
    except (FdGatewayError, OSError) as exc:
        raise AuthorizationConsumedError("canonical authorization ledger validation failed") from exc
    finally:
        for fd in (lock_fd, consumed_fd, authorizations_fd, locks_fd):
            if fd >= 0:
                os.close(fd)
