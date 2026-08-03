from __future__ import annotations

import errno
import fcntl
import os
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from .canonical import CanonicalJSONError, canonical_bytes, parse_canonical_bytes, with_self_digest
from .fd_gateway import CleanMetadataAdapter, FdGatewayError, _validate_metadata, read_regular_file_at_identity
from .journal_store import JournalStoreError, read_journal_records
from .schema_bundle import SchemaBundleError, validate_instance


class ServiceAdmissionError(OSError):
    pass


def _open_directory(parent_fd: int, name: str, device: int, uid: int, gid: int, mode: int,
                    metadata: CleanMetadataAdapter) -> int:
    fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent_fd)
    try:
        _validate_metadata(fd, "directory", device, uid, gid, mode, metadata)
        return fd
    except BaseException:
        os.close(fd)
        raise


def _read_epoch(control_fd: int, root_uid: int, service_gid: int,
                metadata: CleanMetadataAdapter) -> Tuple[Dict[str, Any], Tuple[int, int]]:
    try:
        data, identity = read_regular_file_at_identity(
            control_fd, "epoch.json", 2, 1024, root_uid, service_gid, 0o440, metadata,
        )
        value = parse_canonical_bytes(data)
        if not isinstance(value, dict):
            raise ServiceAdmissionError("epoch is not an object")
        validate_instance("epoch-final-v1", value)
        return value, identity
    except (CanonicalJSONError, FdGatewayError, SchemaBundleError, KeyError, TypeError, ValueError, OSError) as exc:
        if isinstance(exc, ServiceAdmissionError):
            raise
        raise ServiceAdmissionError("epoch validation failed") from exc


class ServiceRun:
    def __init__(self, context: "_ServiceRunContext", startup_epoch: Dict[str, Any],
                 startup_epoch_identity: Tuple[int, int]):
        self._context = context
        self.startup_epoch = startup_epoch
        self.startup_epoch_identity = startup_epoch_identity

    @property
    def lease_fd(self) -> int:
        return self._context.lease_fd

    def assert_epoch_current(self) -> Dict[str, Any]:
        if not self._context.active:
            raise ServiceAdmissionError("service run is not active")
        self._context._assert_canonical_lease()
        self._context._assert_unfenced()
        smoke_gate = self._context._assert_smoke_gate()
        self._context._assert_initial_smoke_transaction(prepared_only=False)
        current, _identity = _read_epoch(
            self._context.control_fd, self._context.root_uid,
            self._context.service_gid, self._context.metadata,
        )
        if smoke_gate is not None and (smoke_gate["service_epoch"], smoke_gate["service_instance"]) != (
                current["epoch"], current["service_instance"]):
            raise ServiceAdmissionError("smoke gate epoch or service instance mismatch")
        if (current["epoch"], current["service_instance"]) != (
            self.startup_epoch["epoch"], self.startup_epoch["service_instance"],
        ):
            raise ServiceAdmissionError("stale epoch blocks service mutation")
        return current


class _ServiceRunContext:
    def __init__(self, root_fd: int, expected_root_identity: Tuple[int, int],
                 root_uid: int, root_gid: int, service_uid: int, service_gid: int,
                 metadata: CleanMetadataAdapter, *, admission_kind: str = "nightly",
                 expected_smoke_gate: Optional[Dict[str, Any]] = None,
                 admitted_at: Optional[str] = None):
        self.root_fd = root_fd
        self.expected_root_identity = expected_root_identity
        self.root_uid = root_uid
        self.root_gid = root_gid
        self.service_uid = service_uid
        self.service_gid = service_gid
        self.metadata = metadata
        if admission_kind not in {"nightly", "initial-smoke"}:
            raise ServiceAdmissionError("unknown service admission kind")
        self.admission_kind = admission_kind
        self.expected_smoke_gate = expected_smoke_gate
        self.admitted_at = admitted_at
        self.service_fd = -1
        self.control_fd = -1
        self.lease_fd = -1
        self.active = False
        self._locked = False

    def _assert_canonical_lease(self) -> None:
        fresh_service_fd = fresh_lease_fd = -1
        try:
            root = os.fstat(self.root_fd)
            fresh_service_fd = _open_directory(
                self.root_fd, "service", root.st_dev,
                self.root_uid, self.root_gid, 0o700, self.metadata,
            )
            fresh_service = os.fstat(fresh_service_fd)
            held_service = os.fstat(self.service_fd)
            if (fresh_service.st_dev, fresh_service.st_ino) != (held_service.st_dev, held_service.st_ino):
                raise ServiceAdmissionError("canonical service directory identity changed")
            fresh_lease_fd = os.open(
                "lease.lock", os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=fresh_service_fd,
            )
            fresh_lease = _validate_metadata(
                fresh_lease_fd, "regular", root.st_dev,
                self.root_uid, self.root_gid, 0o600, self.metadata,
            )
            held_lease = os.fstat(self.lease_fd)
            if fresh_lease.st_nlink != 1 or (fresh_lease.st_dev, fresh_lease.st_ino) != (
                    held_lease.st_dev, held_lease.st_ino):
                raise ServiceAdmissionError("canonical service lease identity changed")
        except ServiceAdmissionError:
            raise
        except BaseException as exc:
            raise ServiceAdmissionError("canonical service lease identity cannot be proven") from exc
        finally:
            if fresh_lease_fd >= 0:
                os.close(fresh_lease_fd)
            if fresh_service_fd >= 0:
                os.close(fresh_service_fd)

    def _assert_unfenced(self) -> None:
        try:
            os.stat("FENCED", dir_fd=self.root_fd, follow_symlinks=False)
        except FileNotFoundError:
            return
        except OSError as exc:
            if exc.errno == errno.ENOENT:
                return
            raise ServiceAdmissionError("cannot determine FENCED state") from exc
        raise ServiceAdmissionError("FENCED blocks service admission")

    def _assert_initial_smoke_transaction(self, *, prepared_only: bool) -> None:
        if self.admission_kind != "initial-smoke":
            return
        transactions_fd = transaction_fd = records_fd = -1
        gate = self.expected_smoke_gate
        assert gate is not None
        try:
            root = os.fstat(self.root_fd)
            transactions_fd = _open_directory(
                self.root_fd, "service-transactions", root.st_dev,
                self.root_uid, self.root_gid, 0o700, self.metadata,
            )
            transaction_fd = _open_directory(
                transactions_fd, gate["smoke_transaction_uuid"], root.st_dev,
                self.root_uid, self.root_gid, 0o700, self.metadata,
            )
            if set(os.listdir(transaction_fd)) != {"records", "sources", "candidates", "receipts"}:
                raise ServiceAdmissionError("initial-smoke transaction child set mismatch")
            records_fd = _open_directory(
                transaction_fd, "records", root.st_dev,
                self.root_uid, self.root_gid, 0o700, self.metadata,
            )
            records = read_journal_records(
                records_fd, self.root_uid, self.root_gid, self.metadata, journal_kind="service",
            )
            first = records[0] if records else None
            if first is None or first["sequence"] != 1 or first["state"] != "PREPARED":
                raise ServiceAdmissionError("initial-smoke transaction lacks durable PREPARED")
            if prepared_only and len(records) != 1:
                raise ServiceAdmissionError("initial-smoke admission requires exactly PREPARED")
            if records[-1]["state"] in {"COMMITTED", "ABORTED", "RECOVERY_REQUIRED", "ROLLED_BACK"}:
                raise ServiceAdmissionError("initial-smoke transaction is already terminal")
            expected = {
                "transaction_uuid": gate["smoke_transaction_uuid"],
                "purpose": "initial-cutover-smoke",
                "service_epoch": gate["service_epoch"],
                "service_instance": gate["service_instance"],
                "runtime_manifest_digest": gate["runtime_manifest_digest"],
                "skill_manifest_digest": gate["skill_manifest_digest"],
            }
            if any(first[field] != value for field, value in expected.items()):
                raise ServiceAdmissionError("initial-smoke PREPARED binding mismatch")
        except ServiceAdmissionError:
            raise
        except (JournalStoreError, FdGatewayError, OSError, KeyError, TypeError) as exc:
            raise ServiceAdmissionError("initial-smoke transaction evidence cannot be proven") from exc
        finally:
            for fd in (records_fd, transaction_fd, transactions_fd):
                if fd >= 0:
                    os.close(fd)

    def _assert_smoke_gate(self) -> Optional[Dict[str, Any]]:
        if self.admission_kind == "nightly":
            try:
                os.stat("smoke-pending.json", dir_fd=self.control_fd, follow_symlinks=False)
            except FileNotFoundError:
                return None
            except OSError as exc:
                if exc.errno == errno.ENOENT:
                    return None
                raise ServiceAdmissionError("cannot determine smoke gate state") from exc
            raise ServiceAdmissionError("present smoke gate blocks normal nightly admission")
        if not isinstance(self.expected_smoke_gate, dict) or not isinstance(self.admitted_at, str):
            raise ServiceAdmissionError("initial smoke admission lacks exact expected gate or trusted time")
        try:
            validate_instance("smoke-gate-final-v1", self.expected_smoke_gate)
            preimage = dict(self.expected_smoke_gate, record_digest=None)
            if with_self_digest(preimage, "record_digest") != self.expected_smoke_gate:
                raise ServiceAdmissionError("expected smoke gate self digest mismatch")
            data, _identity = read_regular_file_at_identity(
                self.control_fd, "smoke-pending.json", 2, 64 * 1024,
                self.root_uid, self.service_gid, 0o440, self.metadata,
            )
            gate = parse_canonical_bytes(data)
            validate_instance("smoke-gate-final-v1", gate)
            if canonical_bytes(gate) != canonical_bytes(self.expected_smoke_gate):
                raise ServiceAdmissionError("smoke gate differs from exact authorization expectation")
            now = datetime.strptime(self.admitted_at, "%Y-%m-%dT%H:%M:%SZ")
            issued = datetime.strptime(gate["issued_at"], "%Y-%m-%dT%H:%M:%SZ")
            expires = datetime.strptime(gate["expires_at"], "%Y-%m-%dT%H:%M:%SZ")
            if now < issued or now >= expires:
                raise ServiceAdmissionError("smoke gate is outside its admission window")
            return gate
        except ServiceAdmissionError:
            raise
        except (CanonicalJSONError, FdGatewayError, SchemaBundleError, OSError, TypeError, ValueError) as exc:
            raise ServiceAdmissionError("initial smoke gate validation failed") from exc

    def __enter__(self) -> ServiceRun:
        try:
            root = os.fstat(self.root_fd)
            if (root.st_dev, root.st_ino) != self.expected_root_identity:
                raise ServiceAdmissionError("canonical root identity mismatch")
            _validate_metadata(
                self.root_fd, "directory", root.st_dev,
                self.root_uid, self.root_gid, 0o755, self.metadata,
            )
            self.service_fd = _open_directory(
                self.root_fd, "service", root.st_dev,
                self.root_uid, self.root_gid, 0o700, self.metadata,
            )
            self.control_fd = _open_directory(
                self.root_fd, "control", root.st_dev,
                self.root_uid, self.service_gid, 0o750, self.metadata,
            )
            self.lease_fd = os.open(
                "lease.lock", os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=self.service_fd,
            )
            lease = _validate_metadata(
                self.lease_fd, "regular", root.st_dev,
                self.root_uid, self.root_gid, 0o600, self.metadata,
            )
            if lease.st_nlink != 1:
                raise ServiceAdmissionError("service lease is not a one-link regular file")
            fcntl.flock(self.lease_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self._locked = True
            self._assert_canonical_lease()
            self._assert_unfenced()
            smoke_gate = self._assert_smoke_gate()
            self._assert_initial_smoke_transaction(prepared_only=True)
            startup, identity = _read_epoch(
                self.control_fd, self.root_uid, self.service_gid, self.metadata,
            )
            if smoke_gate is not None and (smoke_gate["service_epoch"], smoke_gate["service_instance"]) != (
                    startup["epoch"], startup["service_instance"]):
                raise ServiceAdmissionError("smoke gate epoch or service instance mismatch")
            self.active = True
            return ServiceRun(self, startup, identity)
        except BaseException as exc:
            self.__exit__(type(exc), exc, exc.__traceback__)
            if isinstance(exc, (ServiceAdmissionError, BlockingIOError)):
                raise
            raise ServiceAdmissionError(str(exc)) from exc

    def __exit__(self, _exc_type, _exc, _traceback) -> None:
        self.active = False
        if self._locked and self.lease_fd >= 0:
            fcntl.flock(self.lease_fd, fcntl.LOCK_UN)
        self._locked = False
        for name in ("lease_fd", "control_fd", "service_fd"):
            fd = getattr(self, name)
            if fd >= 0:
                os.close(fd)
                setattr(self, name, -1)


def acquire_nightly_epoch_lease(root_fd: int, expected_root_identity: Tuple[int, int],
                        root_uid: int, root_gid: int, service_uid: int, service_gid: int,
                        metadata: CleanMetadataAdapter) -> _ServiceRunContext:
    return _ServiceRunContext(
        root_fd, expected_root_identity, root_uid, root_gid,
        service_uid, service_gid, metadata,
    )


def acquire_initial_smoke_epoch_lease(
        root_fd: int, expected_root_identity: Tuple[int, int],
        root_uid: int, root_gid: int, service_uid: int, service_gid: int,
        metadata: CleanMetadataAdapter, *, expected_smoke_gate: Dict[str, Any],
        admitted_at: str) -> _ServiceRunContext:
    return _ServiceRunContext(
        root_fd, expected_root_identity, root_uid, root_gid,
        service_uid, service_gid, metadata,
        admission_kind="initial-smoke", expected_smoke_gate=expected_smoke_gate,
        admitted_at=admitted_at,
    )
