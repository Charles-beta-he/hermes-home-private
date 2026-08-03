from __future__ import annotations

import ctypes
import errno
import fcntl
import hashlib
import os
import stat
from dataclasses import dataclass
from typing import Any, Callable, Dict, Mapping, Optional, Protocol, Tuple

from .fd_gateway import CleanMetadataAdapter, _validate_metadata
from .root_gate import RootMutationGate
from .swap_evidence import SwapEvidenceError, load_bound_swap_evidence
from .validation import ProtocolValidationError, validate_digest, validate_uuid

RENAME_SWAP = 0x00000002
RENAME_EXCL = 0x00000004
F_FULLFSYNC = 51
FaultHook = Callable[[str, Dict[str, Any]], None]


class LiveMutationGate(Protocol):
    def assert_live(self) -> None: ...


_libc = ctypes.CDLL(None, use_errno=True)
_renameatx_np = _libc.renameatx_np
_renameatx_np.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
_renameatx_np.restype = ctypes.c_int
_flistxattr = _libc.flistxattr
_flistxattr.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int]
_flistxattr.restype = ctypes.c_ssize_t


@dataclass(frozen=True)
class PublishedFile:
    name: str
    device: int
    inode: int
    mode: int
    uid: int
    gid: int
    byte_count: int
    sha256: str


@dataclass(frozen=True)
class PublishedDirectory:
    name: str
    device: int
    inode: int
    mode: int
    uid: int
    gid: int
    children: Dict[str, PublishedFile]


@dataclass(frozen=True)
class ReservedSwapResult:
    role: str
    current_name: str
    retained_name: str
    current_inode: int
    retained_inode: int
    current_digest: str
    retained_digest: str


class PublicationError(OSError):
    def __init__(self, message: str, temp_name: str, cause: Optional[BaseException] = None):
        super().__init__(message)
        self.temp_name = temp_name
        self.__cause__ = cause


def _rename_exclusive(parent_fd: int, source: str, final: str) -> None:
    result = _renameatx_np(parent_fd, os.fsencode(source), parent_fd, os.fsencode(final), RENAME_EXCL)
    if result != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), final)


def _has_extended_acl(fd: int) -> bool:
    return CleanMetadataAdapter().has_extended_acl(fd)


class _DefaultPublicationMetadata(CleanMetadataAdapter):
    def xattr_bytes(self, fd: int) -> int:
        size = _flistxattr(fd, None, 0, 0)
        if size < 0:
            error = ctypes.get_errno()
            raise OSError(error, "cannot prove staged inode xattr absence")
        return int(size)

    def has_extended_acl(self, fd: int) -> bool:
        return _has_extended_acl(fd)


def _read_held_bytes_and_digest(fd: int) -> Tuple[bytes, str]:
    os.lseek(fd, 0, os.SEEK_SET)
    chunks = []
    while True:
        chunk = os.read(fd, 131072)
        if not chunk:
            break
        chunks.append(chunk)
    data = b"".join(chunks)
    return data, hashlib.sha256(data).hexdigest()


def swap_reserved_regular_file(*, parent_fd: int, expected_parent_identity: Tuple[int, int],
                               gate: RootMutationGate, authorization: Dict[str, Any],
                               role: str, current_name: str, staged_name: str,
                               expected_current_digest: str, expected_staged_digest: str,
                               required_journal_state: str,
                               uid: int, gid: int, mode: int, metadata: CleanMetadataAdapter,
                               fault_hook: Optional[FaultHook] = None) -> ReservedSwapResult:
    allowed = {
        "epoch": (0o750, 0o440),
        "rollback-floor": (0o700, 0o400),
        "launchdaemon-plist": (0o755, 0o644),
    }
    _validate_basename(current_name, "current")
    _validate_basename(staged_name, "staged")
    if current_name == staged_name:
        raise ValueError("reserved swap names must differ")
    if role not in allowed:
        raise ValueError("role is not a reserved regular-file swap")
    parent_mode, role_mode = allowed[role]
    if mode != role_mode:
        raise ValueError("reserved swap mode differs from role")
    try:
        validate_digest(expected_current_digest)
        validate_digest(expected_staged_digest)
    except ProtocolValidationError as exc:
        raise ValueError(str(exc)) from exc
    if not required_journal_state:
        raise PublicationError("reserved swap requires durable journal state", staged_name)
    current_fd = -1
    staged_fd = -1
    try:
        gate.assert_live()
        parent = os.fstat(parent_fd)
        if (parent.st_dev, parent.st_ino) != expected_parent_identity:
            raise OSError("reserved swap parent identity mismatch")
        _validate_metadata(parent_fd, "directory", parent.st_dev, uid, gid, parent_mode, metadata)
        evidence = load_bound_swap_evidence(
            gate=gate, authorization=authorization, expected_state=required_journal_state,
            expected_role=role, uid=uid, gid=gid, metadata=metadata,
        )
        if (evidence["parent_device"], evidence["parent_inode"]) != expected_parent_identity:
            raise OSError("reserved swap journal parent identity mismatch")
        if (evidence["current_name"], evidence["staged_name"]) != (current_name, staged_name):
            raise OSError("reserved swap journal pathname binding mismatch")
        if (evidence["current_digest"], evidence["staged_digest"]) != (
                expected_current_digest, expected_staged_digest):
            raise OSError("reserved swap journal digest binding mismatch")
        current_fd = os.open(current_name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent_fd)
        staged_fd = os.open(staged_name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent_fd)
        current = _validate_fd(current_fd, parent.st_dev, mode, uid, gid, metadata)
        staged = _validate_fd(staged_fd, parent.st_dev, mode, uid, gid, metadata)
        if ((current.st_dev, current.st_ino), (staged.st_dev, staged.st_ino)) != (
                (evidence["current_device"], evidence["current_inode"]),
                (evidence["staged_device"], evidence["staged_inode"]),
        ):
            raise OSError("reserved swap inode differs from durable journal evidence")
        _current_bytes, current_digest = _read_held_bytes_and_digest(current_fd)
        _staged_bytes, staged_digest = _read_held_bytes_and_digest(staged_fd)
        if current_digest != expected_current_digest or staged_digest != expected_staged_digest:
            raise OSError("reserved swap digest mismatch")
        current_named = os.stat(current_name, dir_fd=parent_fd, follow_symlinks=False)
        staged_named = os.stat(staged_name, dir_fd=parent_fd, follow_symlinks=False)
        if ((current_named.st_dev, current_named.st_ino), (staged_named.st_dev, staged_named.st_ino)) != (
            (current.st_dev, current.st_ino), (staged.st_dev, staged.st_ino)
        ):
            raise OSError("reserved swap pathname identity changed before mutation")
        gate.assert_live()
        _emit(fault_hook, "before_reserved_swap", role=role, current_name=current_name, staged_name=staged_name)
        result = _renameatx_np(
            parent_fd, os.fsencode(current_name), parent_fd, os.fsencode(staged_name), RENAME_SWAP,
        )
        if result != 0:
            error = ctypes.get_errno()
            raise OSError(error, os.strerror(error))
        _emit(fault_hook, "after_reserved_swap", role=role, current_name=current_name, staged_name=staged_name)
        new_current = os.stat(current_name, dir_fd=parent_fd, follow_symlinks=False)
        retained = os.stat(staged_name, dir_fd=parent_fd, follow_symlinks=False)
        if ((new_current.st_dev, new_current.st_ino), (retained.st_dev, retained.st_ino)) != (
            (staged.st_dev, staged.st_ino), (current.st_dev, current.st_ino)
        ):
            raise OSError("reserved swap identity readback mismatch")
        os.fsync(parent_fd)
        _emit(fault_hook, "after_reserved_swap_parent_fsync", role=role)
        gate.assert_live()
        return ReservedSwapResult(
            role=role,
            current_name=current_name,
            retained_name=staged_name,
            current_inode=staged.st_ino,
            retained_inode=current.st_ino,
            current_digest=staged_digest,
            retained_digest=current_digest,
        )
    except BaseException as exc:
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        if isinstance(exc, PublicationError):
            raise
        raise PublicationError(str(exc), staged_name, exc) from exc
    finally:
        if staged_fd >= 0:
            os.close(staged_fd)
        if current_fd >= 0:
            os.close(current_fd)


def _emit(hook: Optional[FaultHook], event: str, **context: Any) -> None:
    if hook is not None:
        hook(event, context)


def _validate_basename(value: str, label: str) -> None:
    if not isinstance(value, str) or not value or value in {".", ".."} or "/" in value or "\x00" in value:
        raise ValueError(f"invalid {label} basename")


def _validate_fd(fd: int, parent_device: int, mode: int, uid: int, gid: int,
                 metadata: CleanMetadataAdapter) -> os.stat_result:
    status = os.fstat(fd)
    if not stat.S_ISREG(status.st_mode) or status.st_nlink != 1:
        raise OSError("staged inode must be one-link regular file")
    if status.st_dev != parent_device or (status.st_uid, status.st_gid) != (uid, gid):
        raise OSError("staged inode identity/ownership mismatch")
    if stat.S_IMODE(status.st_mode) != mode:
        raise OSError("staged inode mode mismatch")
    if getattr(status, "st_flags", 0) != 0:
        raise OSError("staged inode has BSD flags")
    try:
        xattr_size = metadata.xattr_bytes(fd)
    except OSError:
        raise
    except BaseException as exc:
        raise OSError("cannot prove staged inode xattr absence") from exc
    if xattr_size != 0:
        raise OSError("staged inode has xattrs")
    if metadata.has_extended_acl(fd):
        raise OSError("staged inode has an extended ACL")
    return status


def publish_regular_file(parent_fd: int, final_name: str, data: bytes, mode: int, uid: int, gid: int,
                         transaction_uuid: str, fault_hook: Optional[FaultHook] = None,
                         metadata: Optional[CleanMetadataAdapter] = None,
                         gate: Optional[LiveMutationGate] = None) -> PublishedFile:
    metadata = _DefaultPublicationMetadata() if metadata is None else metadata
    _validate_basename(final_name, "final")
    try:
        validate_uuid(transaction_uuid)
    except ProtocolValidationError as exc:
        raise ValueError(str(exc)) from exc
    if not isinstance(data, bytes) or mode not in {0o400, 0o440, 0o444, 0o500, 0o550, 0o555, 0o600, 0o640, 0o644}:
        raise ValueError("invalid publication bytes or mode")
    temp_name = f".{final_name}.txn-{transaction_uuid}.tmp"
    _validate_basename(temp_name, "temporary")
    parent_status = os.fstat(parent_fd)
    if not stat.S_ISDIR(parent_status.st_mode):
        raise ValueError("parent_fd is not a directory")
    if uid != os.geteuid() or (parent_status.st_uid, parent_status.st_gid) != (uid, gid):
        raise ValueError("publication parent is not owned by the effective broker UID")
    fd = -1
    try:
        if gate is not None:
            gate.assert_live()
        fd = os.open(temp_name, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent_fd)
        _emit(fault_hook, "after_create", fd=fd, temp_name=temp_name)
        current = os.fstat(fd)
        if (current.st_uid, current.st_gid) != (uid, gid):
            if gate is not None:
                gate.assert_live()
            os.fchown(fd, uid, gid)
        if gate is not None:
            gate.assert_live()
        os.fchmod(fd, mode)
        _validate_fd(fd, parent_status.st_dev, mode, uid, gid, metadata)
        _emit(fault_hook, "after_metadata", fd=fd, temp_name=temp_name)
        view = memoryview(data)
        offset = 0
        while offset < len(view):
            if gate is not None:
                gate.assert_live()
            written = os.write(fd, view[offset:])
            if written == 0:
                raise OSError("zero write before complete payload")
            offset += written
        _emit(fault_hook, "after_write", fd=fd, byte_count=offset)
        os.fsync(fd)
        _emit(fault_hook, "after_fsync", fd=fd)
        fcntl.fcntl(fd, F_FULLFSYNC)
        _emit(fault_hook, "after_full_fsync", fd=fd)
        before = _validate_fd(fd, parent_status.st_dev, mode, uid, gid, metadata)
        os.lseek(fd, 0, os.SEEK_SET)
        readback = bytearray()
        while True:
            chunk = os.read(fd, 131072)
            if not chunk:
                break
            readback.extend(chunk)
        if bytes(readback) != data:
            raise OSError("same-FD byte readback mismatch")
        digest = hashlib.sha256(readback).hexdigest()
        _emit(fault_hook, "before_rename_excl", fd=fd, temp_name=temp_name, final_name=final_name)
        immediately_before = _validate_fd(fd, parent_status.st_dev, mode, uid, gid, metadata)
        immediate_bytes, immediate_digest = _read_held_bytes_and_digest(fd)
        if ((immediately_before.st_dev, immediately_before.st_ino) != (before.st_dev, before.st_ino) or
                immediate_bytes != data or immediate_digest != digest):
            raise OSError("same-FD byte readback mismatch immediately before publication")
        if gate is not None:
            gate.assert_live()
        _rename_exclusive(parent_fd, temp_name, final_name)
        _emit(fault_hook, "after_rename_excl", fd=fd, final_name=final_name)
        held = os.fstat(fd)
        named = os.stat(final_name, dir_fd=parent_fd, follow_symlinks=False)
        if (held.st_dev, held.st_ino) != (named.st_dev, named.st_ino) or (held.st_dev, held.st_ino) != (before.st_dev, before.st_ino):
            raise OSError("held and published inode identities differ")
        _validate_fd(fd, parent_status.st_dev, mode, uid, gid, metadata)
        published_bytes, published_digest = _read_held_bytes_and_digest(fd)
        if published_bytes != data or published_digest != digest:
            raise OSError("published same-FD byte readback mismatch")
        os.fsync(parent_fd)
        _emit(fault_hook, "after_parent_fsync", fd=fd, final_name=final_name)
        return PublishedFile(final_name, held.st_dev, held.st_ino, mode, uid, gid, len(data), digest)
    except BaseException as exc:
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        raise PublicationError(str(exc), temp_name, exc) from exc
    finally:
        if fd >= 0:
            os.close(fd)


def _validate_directory_fd(fd: int, parent_device: int, mode: int, uid: int, gid: int,
                           metadata: CleanMetadataAdapter) -> os.stat_result:
    status = os.fstat(fd)
    if not stat.S_ISDIR(status.st_mode):
        raise OSError("staged inode must be a directory")
    if status.st_dev != parent_device or (status.st_uid, status.st_gid) != (uid, gid):
        raise OSError("staged directory identity/ownership mismatch")
    if stat.S_IMODE(status.st_mode) != mode:
        raise OSError("staged directory mode mismatch")
    if getattr(status, "st_flags", 0) != 0:
        raise OSError("staged directory has BSD flags")
    try:
        xattr_size = metadata.xattr_bytes(fd)
    except OSError:
        raise
    except BaseException as exc:
        raise OSError("cannot prove staged directory xattr absence") from exc
    if xattr_size != 0:
        raise OSError("staged directory has xattrs")
    if metadata.has_extended_acl(fd):
        raise OSError("staged directory has an extended ACL")
    return status


def publish_directory_tree(parent_fd: int, final_name: str,
                           files: Mapping[str, Tuple[bytes, int]], directory_mode: int,
                           uid: int, gid: int, transaction_uuid: str,
                           fault_hook: Optional[FaultHook] = None,
                           metadata: Optional[CleanMetadataAdapter] = None,
                           gate: Optional[LiveMutationGate] = None) -> PublishedDirectory:
    metadata = _DefaultPublicationMetadata() if metadata is None else metadata
    _validate_basename(final_name, "final directory")
    try:
        validate_uuid(transaction_uuid)
    except ProtocolValidationError as exc:
        raise ValueError(str(exc)) from exc
    if not isinstance(files, Mapping) or not files:
        raise ValueError("directory publication requires a nonempty file mapping")
    if directory_mode not in {0o500, 0o550, 0o555, 0o700, 0o750, 0o755}:
        raise ValueError("invalid directory publication mode")
    for name, specification in files.items():
        _validate_basename(name, "child")
        if not isinstance(specification, tuple) or len(specification) != 2:
            raise ValueError("child specification must be (bytes, mode)")
    temp_name = f".{final_name}.txn-{transaction_uuid}.tmp"
    parent_status = os.fstat(parent_fd)
    if not stat.S_ISDIR(parent_status.st_mode):
        raise ValueError("parent_fd is not a directory")
    if uid != os.geteuid() or (parent_status.st_uid, parent_status.st_gid) != (uid, gid):
        raise ValueError("publication parent is not owned by the effective broker UID")
    directory_fd = -1
    try:
        if gate is not None:
            gate.assert_live()
        os.mkdir(temp_name, 0o700, dir_fd=parent_fd)
        directory_fd = os.open(temp_name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                               dir_fd=parent_fd)
        current = os.fstat(directory_fd)
        if (current.st_uid, current.st_gid) != (uid, gid):
            if gate is not None:
                gate.assert_live()
            os.fchown(directory_fd, uid, gid)
        if gate is not None:
            gate.assert_live()
        os.fchmod(directory_fd, 0o700)
        _validate_directory_fd(directory_fd, parent_status.st_dev, 0o700, uid, gid, metadata)
        _emit(fault_hook, "after_tree_create", fd=directory_fd, temp_name=temp_name)
        children: Dict[str, PublishedFile] = {}
        for child_name in sorted(files):
            data, child_mode = files[child_name]
            children[child_name] = publish_regular_file(
                directory_fd, child_name, data, child_mode, uid, gid, transaction_uuid,
                fault_hook, metadata=metadata, gate=gate
            )
        _emit(fault_hook, "before_tree_verify", fd=directory_fd, temp_name=temp_name)
        names = set(os.listdir(directory_fd))
        expected_names = set(files)
        if names != expected_names:
            raise OSError("transaction directory child set mismatch")
        identities = set()
        for child_name in sorted(names):
            child_status = os.stat(child_name, dir_fd=directory_fd, follow_symlinks=False)
            published = children[child_name]
            identity = (child_status.st_dev, child_status.st_ino)
            if not stat.S_ISREG(child_status.st_mode) or child_status.st_nlink != 1:
                raise OSError("transaction child link count or type mismatch")
            if identity != (published.device, published.inode) or identity in identities:
                raise OSError("transaction child inode alias or identity mismatch")
            identities.add(identity)
        if gate is not None:
            gate.assert_live()
        os.fchmod(directory_fd, directory_mode)
        before = _validate_directory_fd(directory_fd, parent_status.st_dev, directory_mode, uid, gid, metadata)
        os.fsync(directory_fd)
        _emit(fault_hook, "after_tree_fsync", fd=directory_fd, temp_name=temp_name)
        if gate is not None:
            gate.assert_live()
        _rename_exclusive(parent_fd, temp_name, final_name)
        _emit(fault_hook, "after_tree_rename_excl", fd=directory_fd, final_name=final_name)
        named = os.stat(final_name, dir_fd=parent_fd, follow_symlinks=False)
        held = _validate_directory_fd(directory_fd, parent_status.st_dev, directory_mode, uid, gid, metadata)
        if (named.st_dev, named.st_ino) != (held.st_dev, held.st_ino) or (held.st_dev, held.st_ino) != (before.st_dev, before.st_ino):
            raise OSError("held and published directory identities differ")
        if set(os.listdir(directory_fd)) != expected_names:
            raise OSError("published directory child set changed")
        os.fsync(parent_fd)
        _emit(fault_hook, "after_tree_parent_fsync", fd=directory_fd, final_name=final_name)
        return PublishedDirectory(final_name, held.st_dev, held.st_ino, directory_mode, uid, gid, children)
    except BaseException as exc:
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        raise PublicationError(str(exc), temp_name, exc) from exc
    finally:
        if directory_fd >= 0:
            os.close(directory_fd)
