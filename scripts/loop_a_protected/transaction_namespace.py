from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .canonical import CanonicalJSONError, canonical_bytes, with_self_digest
from .fd_gateway import CleanMetadataAdapter
from .publication import (
    FaultHook,
    PublishedFile,
    _DefaultPublicationMetadata,
    _emit,
    _rename_exclusive,
    _validate_directory_fd,
    publish_regular_file,
)
from .validation import ProtocolValidationError, validate_uuid


class TransactionNamespaceError(OSError):
    def __init__(self, message: str, temp_name: str, cause: Optional[BaseException] = None):
        super().__init__(message)
        self.temp_name = temp_name
        self.__cause__ = cause


@dataclass(frozen=True)
class PublishedTransactionNamespace:
    transaction_uuid: str
    device: int
    inode: int
    child_inodes: Dict[str, int]
    prepared: PublishedFile


_CHILDREN = {
    "service": ("records", "sources", "candidates", "receipts"),
    "installer": ("records", "snapshots", "evidence"),
}


def _validate_prepared(record: Dict[str, Any], transaction_uuid: str) -> bytes:
    if (not isinstance(record, dict) or record.get("sequence") != 1 or record.get("state") != "PREPARED" or
            record.get("prior_record_digest") is not None or record.get("transaction_uuid") != transaction_uuid or
            not isinstance(record.get("record_digest"), str)):
        raise ValueError("transaction namespace requires finalized sequence-1 PREPARED")
    preimage = dict(record)
    preimage["record_digest"] = None
    try:
        if with_self_digest(preimage, "record_digest") != record:
            raise ValueError("PREPARED record self-digest mismatch")
        return canonical_bytes(record)
    except CanonicalJSONError as exc:
        raise ValueError("PREPARED record is not canonical") from exc


def publish_transaction_namespace(parent_fd: int, transaction_uuid: str, prepared_record: Dict[str, Any],
                                  kind: str, uid: int, gid: int, metadata: CleanMetadataAdapter,
                                  fault_hook: Optional[FaultHook] = None) -> PublishedTransactionNamespace:
    try:
        validate_uuid(transaction_uuid)
    except ProtocolValidationError as exc:
        raise ValueError(str(exc)) from exc
    if kind not in _CHILDREN:
        raise ValueError("transaction namespace kind must be service or installer")
    prepared_bytes = _validate_prepared(prepared_record, transaction_uuid)
    temp_name = f".{transaction_uuid}.tmp"
    root_fd = -1
    child_fds: Dict[str, int] = {}
    try:
        parent_status = os.fstat(parent_fd)
        if uid != os.geteuid():
            raise OSError("transaction publication UID differs from effective broker UID")
        _validate_directory_fd(parent_fd, parent_status.st_dev, 0o700, uid, gid, metadata)
        os.mkdir(temp_name, 0o700, dir_fd=parent_fd)
        root_fd = os.open(temp_name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                          dir_fd=parent_fd)
        current = os.fstat(root_fd)
        if (current.st_uid, current.st_gid) != (uid, gid):
            os.fchown(root_fd, uid, gid)
        os.fchmod(root_fd, 0o700)
        root_before = _validate_directory_fd(root_fd, parent_status.st_dev, 0o700, uid, gid, metadata)
        for child_name in _CHILDREN[kind]:
            os.mkdir(child_name, 0o700, dir_fd=root_fd)
            child_fd = os.open(child_name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                               dir_fd=root_fd)
            child_status = os.fstat(child_fd)
            if (child_status.st_uid, child_status.st_gid) != (uid, gid):
                os.fchown(child_fd, uid, gid)
            os.fchmod(child_fd, 0o700)
            _validate_directory_fd(child_fd, parent_status.st_dev, 0o700, uid, gid, metadata)
            child_fds[child_name] = child_fd
        prepared = publish_regular_file(
            child_fds["records"], "00000001-PREPARED.json", prepared_bytes, 0o400, uid, gid,
            transaction_uuid, fault_hook, metadata,
        )
        _emit(fault_hook, "before_transaction_verify", fd=root_fd, temp_name=temp_name)
        expected = set(_CHILDREN[kind])
        if set(os.listdir(root_fd)) != expected:
            raise OSError("transaction namespace child set mismatch")
        identities = {(root_before.st_dev, root_before.st_ino)}
        child_inodes: Dict[str, int] = {}
        for child_name in _CHILDREN[kind]:
            child_fd = child_fds[child_name]
            status = _validate_directory_fd(child_fd, parent_status.st_dev, 0o700, uid, gid, metadata)
            identity = (status.st_dev, status.st_ino)
            if identity in identities:
                raise OSError("transaction namespace directory inode alias")
            identities.add(identity)
            child_inodes[child_name] = status.st_ino
            names = set(os.listdir(child_fd))
            expected_names = {"00000001-PREPARED.json"} if child_name == "records" else set()
            if names != expected_names:
                raise OSError("transaction namespace nested child set mismatch")
            os.fsync(child_fd)
        os.fsync(root_fd)
        _emit(fault_hook, "before_transaction_rename_excl", fd=root_fd, records_fd=child_fds["records"],
              temp_name=temp_name, final_name=transaction_uuid)
        if set(os.listdir(root_fd)) != expected:
            raise OSError("transaction namespace child set changed before publication")
        for child_name in _CHILDREN[kind]:
            expected_names = {"00000001-PREPARED.json"} if child_name == "records" else set()
            if set(os.listdir(child_fds[child_name])) != expected_names:
                raise OSError("transaction namespace nested child set changed before publication")
        _rename_exclusive(parent_fd, temp_name, transaction_uuid)
        _emit(fault_hook, "after_transaction_rename_excl", fd=root_fd, final_name=transaction_uuid)
        named = os.stat(transaction_uuid, dir_fd=parent_fd, follow_symlinks=False)
        held = _validate_directory_fd(root_fd, parent_status.st_dev, 0o700, uid, gid, metadata)
        if (named.st_dev, named.st_ino) != (held.st_dev, held.st_ino):
            raise OSError("published transaction root identity mismatch")
        if set(os.listdir(root_fd)) != expected:
            raise OSError("published transaction child set changed")
        for child_name in _CHILDREN[kind]:
            expected_names = {"00000001-PREPARED.json"} if child_name == "records" else set()
            if set(os.listdir(child_fds[child_name])) != expected_names:
                raise OSError("published transaction nested child set changed")
        os.fsync(parent_fd)
        return PublishedTransactionNamespace(transaction_uuid, held.st_dev, held.st_ino, child_inodes, prepared)
    except BaseException as exc:
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        raise TransactionNamespaceError(str(exc), temp_name, exc) from exc
    finally:
        for child_fd in child_fds.values():
            os.close(child_fd)
        if root_fd >= 0:
            os.close(root_fd)
