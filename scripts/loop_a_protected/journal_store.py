from __future__ import annotations

import os
import re
import stat
from typing import Any, Dict, List, Optional, Set, Tuple

from .canonical import CanonicalJSONError, canonical_bytes, parse_canonical_bytes, with_self_digest
from .fd_gateway import CleanMetadataAdapter, FdGatewayError, read_regular_file_at_identity
from .installer_journal import (
    InstallerJournalError,
    validate_installer_authorization,
    validate_installer_chain,
)
from .publication import LiveMutationGate, PublicationError, publish_regular_file
from .service_journal import ServiceJournalError, validate_service_chain


class JournalStoreError(ValueError):
    pass


_RECORD_NAME = re.compile(r"^([0-9]{8})-([A-Z][A-Z0-9_]*)\.json$")


def _record_name(record: Dict[str, Any]) -> str:
    sequence = record.get("sequence")
    state = record.get("state")
    if isinstance(sequence, bool) or not isinstance(sequence, int) or not 1 <= sequence <= 99_999_999:
        raise JournalStoreError("journal record sequence must be an eight-digit positive integer")
    if not isinstance(state, str) or re.fullmatch(r"[A-Z][A-Z0-9_]*", state) is None:
        raise JournalStoreError("journal record state is not a canonical token")
    return f"{sequence:08d}-{state}.json"


def _verify_self_digest(record: Dict[str, Any]) -> None:
    if not isinstance(record, dict) or not isinstance(record.get("record_digest"), str):
        raise JournalStoreError("journal record lacks finalized record digest")
    preimage = dict(record)
    preimage["record_digest"] = None
    try:
        expected = with_self_digest(preimage, "record_digest")
    except CanonicalJSONError as exc:
        raise JournalStoreError("journal record is not canonical or self-digestible") from exc
    if expected != record:
        raise JournalStoreError("journal record self-digest mismatch")


def _validate_parent(parent_fd: int, uid: int, gid: int, metadata: CleanMetadataAdapter) -> None:
    status = os.fstat(parent_fd)
    if not stat.S_ISDIR(status.st_mode) or (status.st_uid, status.st_gid) != (uid, gid):
        raise JournalStoreError("journal parent identity or owner mismatch")
    if stat.S_IMODE(status.st_mode) != 0o700 or getattr(status, "st_flags", 0) != 0:
        raise JournalStoreError("journal parent mode or BSD flags mismatch")
    try:
        if metadata.xattr_bytes(parent_fd) != 0 or metadata.has_extended_acl(parent_fd):
            raise JournalStoreError("journal parent has forbidden metadata")
    except JournalStoreError:
        raise
    except BaseException as exc:
        raise JournalStoreError("cannot prove journal parent metadata") from exc


def _read_named(parent_fd: int, name: str, uid: int, gid: int,
                metadata: CleanMetadataAdapter) -> Tuple[Dict[str, Any], Tuple[int, int]]:
    match = _RECORD_NAME.fullmatch(name)
    if match is None:
        raise JournalStoreError(f"unknown journal entry name: {name!r}")
    try:
        data, identity = read_regular_file_at_identity(parent_fd, name, 1, 1024 * 1024,
                                                       uid, gid, 0o400, metadata)
        value = parse_canonical_bytes(data)
        _verify_self_digest(value)
    except (FdGatewayError, CanonicalJSONError, JournalStoreError) as exc:
        raise JournalStoreError(f"invalid journal record {name!r}") from exc
    if value.get("sequence") != int(match.group(1)) or value.get("state") != match.group(2):
        raise JournalStoreError("journal filename does not match record sequence/state")
    return value, identity


def _validate_chain_basics(records: List[Dict[str, Any]], transaction_uuid: Optional[str] = None) -> None:
    if not records:
        return
    expected_transaction = records[0].get("transaction_uuid") if transaction_uuid is None else transaction_uuid
    if records[0].get("state") != "PREPARED" or records[0].get("prior_record_digest") is not None:
        raise JournalStoreError("journal chain must begin with PREPARED and null predecessor")
    prior = None
    for sequence, record in enumerate(records, 1):
        if record.get("sequence") != sequence:
            raise JournalStoreError("journal sequence is not contiguous")
        if record.get("transaction_uuid") != expected_transaction:
            raise JournalStoreError("journal transaction UUID changed")
        if record.get("prior_record_digest") != prior:
            raise JournalStoreError("journal predecessor digest mismatch")
        prior = record.get("record_digest")


def _validate_purpose(records: List[Dict[str, Any]], journal_kind: str,
                      operation: Optional[str], destination: Optional[str],
                      authorization: Optional[Dict[str, Any]]) -> None:
    try:
        if journal_kind == "service":
            if operation is not None or destination is not None or authorization is not None:
                raise JournalStoreError("service journal cannot carry installer dispatch fields")
            validate_service_chain(records)
        elif journal_kind == "installer":
            if not isinstance(operation, str) or not isinstance(destination, str):
                raise JournalStoreError("installer journal requires operation and destination")
            if not isinstance(authorization, dict):
                raise JournalStoreError("installer journal requires finalized authorization")
            validate_installer_chain(records, operation, destination)
            validate_installer_authorization(records, authorization, operation, destination)
        else:
            raise JournalStoreError("unknown journal kind")
    except (ServiceJournalError, InstallerJournalError) as exc:
        raise JournalStoreError(f"invalid {journal_kind} journal schema or state chain") from exc


def append_journal_record(parent_fd: int, record: Dict[str, Any], uid: int, gid: int,
                          transaction_uuid: str, metadata: CleanMetadataAdapter, *,
                          journal_kind: str, gate: LiveMutationGate,
                          operation: Optional[str] = None,
                          destination: Optional[str] = None,
                          authorization: Optional[Dict[str, Any]] = None) -> None:
    if gate is None or not callable(getattr(gate, "assert_live", None)):
        raise JournalStoreError("journal publication requires a live root mutation gate")
    gate.assert_live()
    if uid != os.geteuid():
        raise JournalStoreError("journal publication UID differs from effective broker UID")
    _validate_parent(parent_fd, uid, gid, metadata)
    _verify_self_digest(record)
    existing = _read_journal_records_unvalidated(parent_fd, uid, gid, metadata)
    candidate = existing + [record]
    _validate_chain_basics(candidate, transaction_uuid)
    _validate_purpose(candidate, journal_kind, operation, destination, authorization)
    name = _record_name(record)
    try:
        publish_regular_file(parent_fd, name, canonical_bytes(record), 0o400, uid, gid,
                             transaction_uuid, metadata=metadata, gate=gate)
    except (PublicationError, CanonicalJSONError) as exc:
        raise JournalStoreError("cannot publish immutable journal record") from exc
    readback, _identity = _read_named(parent_fd, name, uid, gid, metadata)
    if readback != record:
        raise JournalStoreError("journal record durable readback mismatch")
    durable = _read_journal_records_unvalidated(parent_fd, uid, gid, metadata)
    _validate_purpose(durable, journal_kind, operation, destination, authorization)


def _read_journal_records_unvalidated(parent_fd: int, uid: int, gid: int,
                                      metadata: CleanMetadataAdapter) -> List[Dict[str, Any]]:
    _validate_parent(parent_fd, uid, gid, metadata)
    try:
        names = os.listdir(parent_fd)
    except OSError as exc:
        raise JournalStoreError("cannot enumerate journal records") from exc
    parsed: List[Tuple[int, str]] = []
    sequences: Set[int] = set()
    for name in names:
        match = _RECORD_NAME.fullmatch(name)
        if match is None:
            raise JournalStoreError(f"unknown journal entry name: {name!r}")
        sequence = int(match.group(1))
        if sequence in sequences:
            raise JournalStoreError("duplicate sequence in journal directory")
        sequences.add(sequence)
        parsed.append((sequence, name))
    records: List[Dict[str, Any]] = []
    identities: Set[Tuple[int, int]] = set()
    for _sequence, name in sorted(parsed):
        value, identity = _read_named(parent_fd, name, uid, gid, metadata)
        if identity in identities:
            raise JournalStoreError("journal record inode alias detected")
        identities.add(identity)
        records.append(value)
    _validate_chain_basics(records)
    return records


def read_journal_records(parent_fd: int, uid: int, gid: int,
                         metadata: CleanMetadataAdapter, *, journal_kind: str,
                         operation: Optional[str] = None,
                         destination: Optional[str] = None,
                         authorization: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    records = _read_journal_records_unvalidated(parent_fd, uid, gid, metadata)
    _validate_purpose(records, journal_kind, operation, destination, authorization)
    return records
