from __future__ import annotations

import datetime
import grp
import hashlib
import os
import pwd
import re
import sys
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Callable, FrozenSet, Mapping, Tuple

from .broker_coordinator import TransactionBinding
from .broker_isolation import validate_mutation_roots
from .broker_transaction import JournalCandidateTransaction
from .canonical import CanonicalJSONError, canonical_bytes, parse_canonical_bytes, with_self_digest
from .darwin_activation import ActivatedWorkerSession, open_launchd_worker_session
from .darwin_broker_worker import run_root_broker_session
from .darwin_launchd_transport import PROTECTED_ROLES
from .fd_gateway import CleanMetadataAdapter, _validate_metadata
from .manifests import ManifestError, validate_manifest_inventory_pair
from .service_admission import ServiceRun, acquire_nightly_epoch_lease
from .validation import ProtocolValidationError, validate_digest, validate_uuid


class DarwinRootBrokerServiceError(RuntimeError):
    pass


_IDENTITY = Tuple[int, int]
_SKILL_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,80}")
_RUNTIME_INTERPRETER = re.compile(
    r"^/private/var/db/hermes-loop-a/runtime/versions/[0-9a-f]{64}/bin/python3$"
)
_ROOT_PATH = "/private/var/db/hermes-loop-a"
NIGHTLY_REQUEST_NAME = "nightly-request.json"
MUTATION_ROOT_ROLES = (
    "active-skills", "authorizations", "control", "installer-transactions",
    "locks", "policy", "runtime", "service", "service-transactions",
)
_REQUEST_FIELDS = {
    "schema", "transaction_uuid", "skill_name", "runtime_manifest_digest",
    "runtime_inventory_digest", "source_sha256", "source_byte_count",
    "worker_uid", "worker_gid", "request_digest",
}
_ENVIRONMENT = {
    "LANG": "C", "LC_ALL": "C", "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONHASHSEED": "0", "PYTHONNOUSERSITE": "1", "PYTHONUTF8": "1",
}


def _nonnegative_integer(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, int) and value >= 0


def _positive_integer(value: Any) -> bool:
    return _nonnegative_integer(value) and value > 0


def _validate_inode_identity(value: Any, label: str) -> _IDENTITY:
    if (
        not isinstance(value, tuple)
        or len(value) != 2
        or not all(_nonnegative_integer(item) for item in value)
    ):
        raise DarwinRootBrokerServiceError(f"{label} is invalid")
    return value


@dataclass(frozen=True)
class RootBrokerIdentity:
    root_uid: int
    root_gid: int
    service_uid: int
    service_gid: int
    worker_uid: int
    worker_gid: int

    def __post_init__(self) -> None:
        if self.root_uid != 0 or self.root_gid != 0:
            raise DarwinRootBrokerServiceError("root identity must be exact UID/GID 0")
        if not _positive_integer(self.worker_uid) or not _positive_integer(self.worker_gid):
            raise DarwinRootBrokerServiceError("worker identity must be distinct non-root UID/GID")
        if (self.service_uid, self.service_gid) != (self.worker_uid, self.worker_gid):
            raise DarwinRootBrokerServiceError("service identity differs from the exact worker identity")


@dataclass(frozen=True)
class RootBrokerTransaction:
    transaction_uuid: str
    skill_name: str
    runtime_manifest_digest: str
    runtime_inventory_digest: str
    source_sha256: str
    source_byte_count: int

    def __post_init__(self) -> None:
        try:
            validate_uuid(self.transaction_uuid)
            validate_digest(self.runtime_manifest_digest)
            validate_digest(self.runtime_inventory_digest)
            validate_digest(self.source_sha256)
        except (ProtocolValidationError, TypeError, ValueError) as exc:
            raise DarwinRootBrokerServiceError("root broker transaction identity is invalid") from exc
        if not isinstance(self.skill_name, str) or _SKILL_NAME.fullmatch(self.skill_name) is None:
            raise DarwinRootBrokerServiceError("root broker skill identity is invalid")
        if not _positive_integer(self.source_byte_count):
            raise DarwinRootBrokerServiceError("root broker source byte count is invalid")


@dataclass(frozen=True)
class RootBrokerDescriptorSet:
    protected: Mapping[str, int]
    expected_identities: Mapping[str, _IDENTITY]
    records_fd: int
    candidates_fd: int
    mutation_root_identities: FrozenSet[_IDENTITY]
    runtime_root_identity: _IDENTITY

    def __post_init__(self) -> None:
        if not isinstance(self.protected, Mapping) or set(self.protected) != set(PROTECTED_ROLES):
            raise DarwinRootBrokerServiceError("protected descriptor roles are not exact")
        if not isinstance(self.expected_identities, Mapping) or set(self.expected_identities) != set(PROTECTED_ROLES):
            raise DarwinRootBrokerServiceError("protected descriptor identity roles are not exact")
        protected = dict(self.protected)
        if any(not _nonnegative_integer(fd) for fd in protected.values()):
            raise DarwinRootBrokerServiceError("protected descriptor value is invalid")
        if len(set(protected.values())) != len(PROTECTED_ROLES):
            raise DarwinRootBrokerServiceError("protected descriptors are not distinct")
        for fd, label in ((self.records_fd, "records"), (self.candidates_fd, "candidates")):
            if not _nonnegative_integer(fd):
                raise DarwinRootBrokerServiceError(f"{label} transaction descriptor is invalid")
        if len(set(protected.values()) | {self.records_fd, self.candidates_fd}) != len(PROTECTED_ROLES) + 2:
            raise DarwinRootBrokerServiceError("transaction and protected descriptors are not distinct")

        identities = {
            role: _validate_inode_identity(value, f"{role} descriptor identity")
            for role, value in self.expected_identities.items()
        }
        if len(set(identities.values())) != len(PROTECTED_ROLES):
            raise DarwinRootBrokerServiceError("protected descriptor identities are not distinct")
        if not isinstance(self.mutation_root_identities, frozenset) or not self.mutation_root_identities:
            raise DarwinRootBrokerServiceError("mutation-root identity set is not exact and frozen")
        for value in self.mutation_root_identities:
            _validate_inode_identity(value, "mutation-root identity")
        runtime_identity = _validate_inode_identity(
            self.runtime_root_identity, "runtime mutation-root identity"
        )
        if runtime_identity not in self.mutation_root_identities:
            raise DarwinRootBrokerServiceError(
                "runtime mutation-root identity is absent from the frozen mutation roots"
            )

        object.__setattr__(self, "protected", MappingProxyType(protected))
        object.__setattr__(self, "expected_identities", MappingProxyType(identities))


@dataclass(frozen=True)
class OpenedNightlyTransaction:
    request: Mapping[str, Any]
    identity: Any
    descriptors: RootBrokerDescriptorSet
    transaction_spec: RootBrokerTransaction
    owned_fds: Tuple[int, ...]

    def __enter__(self) -> "OpenedNightlyTransaction":
        return self

    def close(self) -> None:
        for fd in reversed(self.owned_fds):
            try:
                os.close(fd)
            except OSError:
                pass

    def __exit__(self, _exc_type: Any, _exc: Any, _traceback: Any) -> None:
        self.close()


def finalize_nightly_request(
    *, transaction_uuid: str, skill_name: str, runtime_manifest_digest: str,
    runtime_inventory_digest: str, source_sha256: str, source_byte_count: int,
    worker_uid: int, worker_gid: int,
) -> dict[str, Any]:
    value = {
        "schema": 1, "transaction_uuid": transaction_uuid, "skill_name": skill_name,
        "runtime_manifest_digest": runtime_manifest_digest,
        "runtime_inventory_digest": runtime_inventory_digest,
        "source_sha256": source_sha256, "source_byte_count": source_byte_count,
        "worker_uid": worker_uid, "worker_gid": worker_gid, "request_digest": None,
    }
    _validate_nightly_request(value, finalized=False)
    return with_self_digest(value, "request_digest")


def _validate_nightly_request(value: Any, *, finalized: bool = True) -> Mapping[str, Any]:
    if not isinstance(value, dict) or set(value) != _REQUEST_FIELDS or value.get("schema") != 1:
        raise DarwinRootBrokerServiceError("nightly request fields are not exact")
    try:
        validate_uuid(value["transaction_uuid"])
        validate_digest(value["runtime_manifest_digest"])
        validate_digest(value["runtime_inventory_digest"])
        validate_digest(value["source_sha256"])
    except (ProtocolValidationError, KeyError, TypeError) as exc:
        raise DarwinRootBrokerServiceError("nightly request identity is invalid") from exc
    if not isinstance(value["skill_name"], str) or _SKILL_NAME.fullmatch(value["skill_name"]) is None:
        raise DarwinRootBrokerServiceError("nightly request skill identity is invalid")
    for field in ("source_byte_count", "worker_uid", "worker_gid"):
        if not _positive_integer(value[field]):
            raise DarwinRootBrokerServiceError(f"nightly request {field} is invalid")
    if not finalized:
        if value["request_digest"] is not None:
            raise DarwinRootBrokerServiceError("nightly request preimage digest is not null")
        return value
    try:
        validate_digest(value["request_digest"])
        if with_self_digest(dict(value, request_digest=None), "request_digest") != value:
            raise DarwinRootBrokerServiceError("nightly request self digest differs")
    except (ProtocolValidationError, CanonicalJSONError, TypeError) as exc:
        if isinstance(exc, DarwinRootBrokerServiceError):
            raise
        raise DarwinRootBrokerServiceError("nightly request self digest is invalid") from exc
    return value


def _open_directory(parent_fd: int, name: str, *, device: int, uid: int, gid: int,
                    mode: int, metadata: CleanMetadataAdapter) -> int:
    fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                 dir_fd=parent_fd)
    try:
        _validate_metadata(fd, "directory", device, uid, gid, mode, metadata)
        return fd
    except BaseException:
        os.close(fd)
        raise


def _open_regular(parent_fd: int, name: str, *, device: int, uid: int, gid: int,
                  mode: int, minimum: int, maximum: int,
                  metadata: CleanMetadataAdapter) -> tuple[int, bytes]:
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent_fd)
    try:
        before = _validate_metadata(fd, "regular", device, uid, gid, mode, metadata)
        if before.st_nlink != 1 or not minimum <= before.st_size <= maximum:
            raise DarwinRootBrokerServiceError("protected regular file metadata is invalid")
        data = bytearray()
        offset = 0
        while offset < before.st_size:
            chunk = os.pread(fd, min(131072, before.st_size - offset), offset)
            if not chunk:
                break
            data.extend(chunk)
            offset += len(chunk)
        after = _validate_metadata(fd, "regular", device, uid, gid, mode, metadata)
        stable = lambda item: (
            item.st_dev, item.st_ino, item.st_mode, item.st_uid, item.st_gid,
            item.st_nlink, item.st_size, item.st_mtime_ns, item.st_ctime_ns,
            getattr(item, "st_flags", 0),
        )
        if stable(before) != stable(after) or len(data) != before.st_size:
            raise DarwinRootBrokerServiceError("protected regular file changed during held-FD read")
        return fd, bytes(data)
    except BaseException:
        os.close(fd)
        raise


def _manifest_entry(value: Mapping[str, Any], relative_path: str) -> Mapping[str, Any]:
    matches = [row for row in value["entries"] if row.get("relative_path") == relative_path]
    if len(matches) != 1:
        raise DarwinRootBrokerServiceError("runtime manifest lacks one exact protected role")
    return matches[0]


def open_nightly_transaction(
    *, root_fd: int, expected_root_identity: _IDENTITY,
    root_uid: int, root_gid: int, metadata: CleanMetadataAdapter,
    mutation_root_validator: Callable[..., FrozenSet[_IDENTITY]] = validate_mutation_roots,
    identity_factory: Callable[..., Any] = RootBrokerIdentity,
) -> OpenedNightlyTransaction:
    owned: list[int] = []
    try:
        root = os.fstat(root_fd)
        if (root.st_dev, root.st_ino) != expected_root_identity:
            raise DarwinRootBrokerServiceError("canonical root identity differs")
        _validate_metadata(root_fd, "directory", root.st_dev, root_uid, root_gid, 0o755, metadata)
        modes = {
            "active-skills": 0o755, "authorizations": 0o755, "control": 0o750,
            "installer-transactions": 0o700, "locks": 0o755, "policy": 0o755,
            "runtime": 0o755, "service": 0o700, "service-transactions": 0o700,
        }
        mutation_fds = {}
        for role in MUTATION_ROOT_ROLES:
            fd = _open_directory(root_fd, role, device=root.st_dev, uid=root_uid,
                                 gid=root_gid, mode=modes[role], metadata=metadata)
            owned.append(fd)
            mutation_fds[role] = fd
        request_fd, request_bytes = _open_regular(
            mutation_fds["service"], NIGHTLY_REQUEST_NAME, device=root.st_dev,
            uid=root_uid, gid=root_gid, mode=0o400, minimum=2, maximum=65536,
            metadata=metadata,
        )
        owned.append(request_fd)
        try:
            parsed_request = parse_canonical_bytes(request_bytes)
        except CanonicalJSONError as exc:
            raise DarwinRootBrokerServiceError("nightly request is not canonical JSON") from exc
        request = dict(_validate_nightly_request(parsed_request))
        mutation_identities = mutation_root_validator(
            mutation_root_fds=mutation_fds, worker_uid=request["worker_uid"],
            worker_gids=(request["worker_gid"],), metadata=metadata,
        )
        if not isinstance(mutation_identities, frozenset):
            raise DarwinRootBrokerServiceError("mutation-root identity set is not frozen")

        metadata_fd = _open_directory(root_fd, "metadata", device=root.st_dev, uid=root_uid,
                                      gid=root_gid, mode=0o755, metadata=metadata)
        owned.append(metadata_fd)
        version = request["runtime_manifest_digest"]
        manifest_fd, manifest_bytes = _open_regular(
            metadata_fd, f"runtime-{version}.manifest.json", device=root.st_dev,
            uid=root_uid, gid=root_gid, mode=0o444, minimum=2, maximum=8_388_608,
            metadata=metadata,
        )
        owned.append(manifest_fd)
        inventory_fd, inventory_bytes = _open_regular(
            metadata_fd, f"runtime-{version}.inventory.json", device=root.st_dev,
            uid=root_uid, gid=root_gid, mode=0o444, minimum=2, maximum=8_388_608,
            metadata=metadata,
        )
        owned.append(inventory_fd)
        try:
            manifest = parse_canonical_bytes(manifest_bytes)
            inventory = parse_canonical_bytes(inventory_bytes)
            if not isinstance(manifest, dict) or not isinstance(inventory, dict):
                raise DarwinRootBrokerServiceError("runtime metadata is not an object")
            validate_manifest_inventory_pair(manifest, inventory)
        except (CanonicalJSONError, ManifestError) as exc:
            raise DarwinRootBrokerServiceError("runtime manifest/inventory validation failed") from exc
        if (manifest["version_digest"] != version
                or inventory["inventory_digest"] != request["runtime_inventory_digest"]):
            raise DarwinRootBrokerServiceError("runtime request differs from manifest/inventory")

        versions_fd = _open_directory(mutation_fds["runtime"], "versions", device=root.st_dev,
                                     uid=root_uid, gid=root_gid, mode=0o755, metadata=metadata)
        owned.append(versions_fd)
        version_fd = _open_directory(versions_fd, version, device=root.st_dev, uid=root_uid,
                                    gid=root_gid, mode=0o555, metadata=metadata)
        owned.append(version_fd)
        bin_fd = _open_directory(version_fd, "bin", device=root.st_dev, uid=root_uid,
                                gid=root_gid, mode=0o555, metadata=metadata)
        owned.append(bin_fd)
        libexec_fd = _open_directory(version_fd, "libexec", device=root.st_dev, uid=root_uid,
                                    gid=root_gid, mode=0o555, metadata=metadata)
        owned.append(libexec_fd)
        protected = {
            "version-root": version_fd, "runtime-manifest": manifest_fd,
            "runtime-inventory": inventory_fd,
        }
        for role, parent_fd, relative, basename in (
            ("retained-executable", bin_fd, "bin/python3", "python3"),
            ("entrypoint", libexec_fd, "libexec/inner-entrypoint.py", "inner-entrypoint.py"),
        ):
            row = _manifest_entry(manifest, relative)
            file_fd, data = _open_regular(
                parent_fd, basename, device=root.st_dev, uid=root_uid, gid=root_gid,
                mode=row["mode"], minimum=row["size"], maximum=row["size"], metadata=metadata,
            )
            owned.append(file_fd)
            if hashlib.sha256(data).hexdigest() != row["sha256"]:
                raise DarwinRootBrokerServiceError(f"{role} bytes differ from runtime manifest")
            protected[role] = file_fd

        transaction_fd = _open_directory(
            mutation_fds["service-transactions"], request["transaction_uuid"],
            device=root.st_dev, uid=root_uid, gid=root_gid, mode=0o700, metadata=metadata,
        )
        owned.append(transaction_fd)
        transaction_children = {}
        for child in ("records", "sources", "candidates", "receipts"):
            child_fd = _open_directory(transaction_fd, child, device=root.st_dev,
                                      uid=root_uid, gid=root_gid, mode=0o700, metadata=metadata)
            owned.append(child_fd)
            transaction_children[child] = child_fd
        source_fd, source_bytes = _open_regular(
            transaction_children["sources"], f"source-{request['source_sha256']}.bin",
            device=root.st_dev, uid=root_uid, gid=root_gid, mode=0o400,
            minimum=request["source_byte_count"], maximum=request["source_byte_count"],
            metadata=metadata,
        )
        owned.append(source_fd)
        if hashlib.sha256(source_bytes).hexdigest() != request["source_sha256"]:
            raise DarwinRootBrokerServiceError("protected source bytes differ from nightly request")
        protected["source"] = source_fd
        expected_identities = {
            role: (os.fstat(fd).st_dev, os.fstat(fd).st_ino) for role, fd in protected.items()
        }
        identity = identity_factory(
            root_uid=root_uid, root_gid=root_gid,
            service_uid=request["worker_uid"], service_gid=request["worker_gid"],
            worker_uid=request["worker_uid"], worker_gid=request["worker_gid"],
        )
        transaction_spec = RootBrokerTransaction(
            transaction_uuid=request["transaction_uuid"], skill_name=request["skill_name"],
            runtime_manifest_digest=version,
            runtime_inventory_digest=request["runtime_inventory_digest"],
            source_sha256=request["source_sha256"], source_byte_count=request["source_byte_count"],
        )
        descriptors = RootBrokerDescriptorSet(
            protected=protected, expected_identities=expected_identities,
            records_fd=transaction_children["records"], candidates_fd=transaction_children["candidates"],
            mutation_root_identities=mutation_identities,
            runtime_root_identity=(os.fstat(mutation_fds["runtime"]).st_dev,
                                   os.fstat(mutation_fds["runtime"]).st_ino),
        )
        return OpenedNightlyTransaction(
            request=MappingProxyType(request), identity=identity, descriptors=descriptors,
            transaction_spec=transaction_spec, owned_fds=tuple(owned),
        )
    except Exception as exc:
        for fd in reversed(owned):
            try:
                os.close(fd)
            except OSError:
                pass
        if isinstance(exc, DarwinRootBrokerServiceError):
            raise
        raise DarwinRootBrokerServiceError("nightly descriptor composition failed closed") from exc


class _EpochLiveGate:
    def __init__(self, service_run: ServiceRun) -> None:
        self._service_run = service_run

    def assert_live(self) -> None:
        self._service_run.assert_epoch_current()


def _require_exact_staged_binding(
    value: Any, transaction_spec: RootBrokerTransaction
) -> TransactionBinding:
    if (
        not isinstance(value, TransactionBinding)
        or value.state != "CANDIDATE_STAGED"
        or value.transaction_uuid != transaction_spec.transaction_uuid
        or value.skill_name != transaction_spec.skill_name
        or value.runtime_manifest_digest != transaction_spec.runtime_manifest_digest
        or value.runtime_inventory_digest != transaction_spec.runtime_inventory_digest
        or value.source_digest != transaction_spec.source_sha256
    ):
        raise DarwinRootBrokerServiceError(
            "root broker transaction is not the exact staged transaction"
        )
    return value


def run_root_broker_service_once(
    *,
    root_fd: int,
    expected_root_identity: _IDENTITY,
    identity: RootBrokerIdentity,
    descriptors: RootBrokerDescriptorSet,
    transaction_spec: RootBrokerTransaction,
    metadata: CleanMetadataAdapter,
    timestamp: Callable[[], str],
    timeout_seconds: float = 10.0,
    geteuid: Callable[[], int] = os.geteuid,
    admission_factory: Callable[..., Any] = acquire_nightly_epoch_lease,
    transaction_factory: Callable[..., Any] = JournalCandidateTransaction,
    activate: Callable[..., ActivatedWorkerSession] = open_launchd_worker_session,
    session_runner: Callable[..., Any] = run_root_broker_session,
) -> Any:
    """Run one admitted root-broker transaction against one launchd worker session.

    All business identity, descriptor roles, and the fixed transaction arrive from the
    root-owned caller. The worker receives only the exact protected descriptor set and
    cannot choose a path, operation, transaction, or publication target.
    """
    if not isinstance(identity, RootBrokerIdentity):
        raise DarwinRootBrokerServiceError("root and worker identity contract is invalid")
    if not isinstance(descriptors, RootBrokerDescriptorSet):
        raise DarwinRootBrokerServiceError("root broker descriptor contract is invalid")
    if not isinstance(transaction_spec, RootBrokerTransaction):
        raise DarwinRootBrokerServiceError("root broker transaction contract is invalid")
    if not _nonnegative_integer(root_fd):
        raise DarwinRootBrokerServiceError("canonical root descriptor is invalid")
    _validate_inode_identity(expected_root_identity, "canonical root identity")
    effective_uid = geteuid()
    if effective_uid != identity.root_uid or effective_uid != 0:
        raise DarwinRootBrokerServiceError("root identity differs from effective broker UID")
    if not callable(timestamp):
        raise DarwinRootBrokerServiceError("trusted timestamp source is not callable")
    if (
        isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, (int, float))
        or not 0 < timeout_seconds <= 30
    ):
        raise DarwinRootBrokerServiceError("root broker timeout is outside the fixed bound")

    activated_socket = None
    try:
        admission = admission_factory(
            root_fd,
            expected_root_identity,
            identity.root_uid,
            identity.root_gid,
            identity.service_uid,
            identity.service_gid,
            metadata,
        )
        with admission as service_run:
            gate = _EpochLiveGate(service_run)
            transaction = transaction_factory(
                records_fd=descriptors.records_fd,
                candidates_fd=descriptors.candidates_fd,
                uid=identity.root_uid,
                gid=identity.root_gid,
                worker_uid=identity.worker_uid,
                metadata=metadata,
                transaction_uuid=transaction_spec.transaction_uuid,
                skill_name=transaction_spec.skill_name,
                runtime_inventory_digest=transaction_spec.runtime_inventory_digest,
                source_byte_count=transaction_spec.source_byte_count,
                timestamp=timestamp,
            )
            binding = _require_exact_staged_binding(
                transaction.snapshot(), transaction_spec
            )
            gate.assert_live()
            activated = activate(
                worker_uid=identity.worker_uid,
                worker_gid=identity.worker_gid,
                timeout_seconds=float(timeout_seconds),
            )
            launchd_pid = getattr(activated, "launchd_pid", None)
            activated_socket = getattr(activated, "socket", None)
            close_activated_socket = getattr(activated_socket, "close", None)
            if not _positive_integer(launchd_pid) or not callable(close_activated_socket):
                raise DarwinRootBrokerServiceError(
                    "launchd activation returned an invalid worker session"
                )
            try:
                gate.assert_live()
                return session_runner(
                    sock=activated_socket,
                    launchd_worker_pid=launchd_pid,
                    worker_uid=identity.worker_uid,
                    worker_gid=identity.worker_gid,
                    descriptors=descriptors.protected,
                    binding=binding,
                    expected_descriptor_identities=descriptors.expected_identities,
                    mutation_root_identities=descriptors.mutation_root_identities,
                    runtime_root_identity=descriptors.runtime_root_identity,
                    gate=gate,
                    transaction=transaction,
                    timeout_seconds=float(timeout_seconds),
                )
            finally:
                try:
                    close_activated_socket()
                except Exception:
                    pass
                activated_socket = None
    except DarwinRootBrokerServiceError:
        raise
    except Exception as exc:
        raise DarwinRootBrokerServiceError("root broker service failed closed") from exc
    finally:
        if activated_socket is not None:
            try:
                activated_socket.close()
            except Exception:
                pass


def root_broker_bootstrap_bytes() -> bytes:
    environment = repr(dict(sorted(_ENVIRONMENT.items())))
    source = (
        "import os,sys\n"
        "os.environ.clear()\n"
        f"os.environ.update({environment})\n"
        "_root=os.path.dirname(os.path.dirname(sys.executable))\n"
        "sys.path.insert(0,os.path.join(_root,'libexec'))\n"
        "from loop_a_protected.darwin_root_broker_service import main\n"
        "raise SystemExit(main())\n"
    )
    return source.encode("ascii")


def _trusted_timestamp() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _validate_service_account(request: Mapping[str, Any]) -> None:
    try:
        user = pwd.getpwnam("_hermesloopa")
        group = grp.getgrnam("_hermesloopa")
        supplementary = tuple(
            item.gr_name for item in grp.getgrall() if "_hermesloopa" in item.gr_mem
        )
    except (KeyError, OSError) as exc:
        raise DarwinRootBrokerServiceError("root broker service account is absent") from exc
    if (
        user.pw_uid != request["worker_uid"]
        or user.pw_gid != request["worker_gid"]
        or group.gr_gid != request["worker_gid"]
        or user.pw_shell != "/usr/bin/false"
        or user.pw_dir != "/var/empty"
        or tuple(group.gr_mem)
        or supplementary
    ):
        raise DarwinRootBrokerServiceError("root broker service account differs from exact request")


def main() -> int:
    if _RUNTIME_INTERPRETER.fullmatch(sys.executable) is None:
        raise DarwinRootBrokerServiceError("root broker interpreter is not an exact runtime version")
    if os.geteuid() != 0 or os.getegid() != 0:
        raise DarwinRootBrokerServiceError("root broker main requires exact root UID/GID")
    root_fd = -1
    try:
        root_fd = os.open(
            _ROOT_PATH, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
        )
        root_status = os.fstat(root_fd)
        root_identity = (root_status.st_dev, root_status.st_ino)
        metadata = CleanMetadataAdapter()
        with open_nightly_transaction(
            root_fd=root_fd, expected_root_identity=root_identity,
            root_uid=0, root_gid=0, metadata=metadata,
        ) as opened:
            _validate_service_account(opened.request)
            run_root_broker_service_once(
                root_fd=root_fd, expected_root_identity=root_identity,
                identity=opened.identity, descriptors=opened.descriptors,
                transaction_spec=opened.transaction_spec, metadata=metadata,
                timestamp=_trusted_timestamp,
            )
        return 0
    except DarwinRootBrokerServiceError:
        raise
    except Exception as exc:
        raise DarwinRootBrokerServiceError("root broker main failed closed") from exc
    finally:
        if root_fd >= 0:
            os.close(root_fd)
