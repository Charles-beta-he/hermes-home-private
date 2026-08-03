from __future__ import annotations

import ctypes
import errno
import os
import stat
from typing import Tuple


class FdGatewayError(OSError):
    pass


_libc = ctypes.CDLL(None, use_errno=True)
_flistxattr = _libc.flistxattr
_flistxattr.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int]
_flistxattr.restype = ctypes.c_ssize_t
_acl_get_fd_np = _libc.acl_get_fd_np
_acl_get_fd_np.argtypes = [ctypes.c_int, ctypes.c_int]
_acl_get_fd_np.restype = ctypes.c_void_p
_acl_get_entry = _libc.acl_get_entry
_acl_get_entry.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p)]
_acl_get_entry.restype = ctypes.c_int
_acl_free = _libc.acl_free
_acl_free.argtypes = [ctypes.c_void_p]
_acl_free.restype = ctypes.c_int
ACL_TYPE_EXTENDED = 0x00000100
ACL_FIRST_ENTRY = 0


class CleanMetadataAdapter:
    def xattr_bytes(self, fd: int) -> int:
        size = _flistxattr(fd, None, 0, 0)
        if size < 0:
            error = ctypes.get_errno()
            raise FdGatewayError(error, "cannot enumerate xattrs")
        return int(size)

    def has_extended_acl(self, fd: int) -> bool:
        acl = _acl_get_fd_np(fd, ACL_TYPE_EXTENDED)
        if not acl:
            error = ctypes.get_errno()
            if error in {0, errno.ENOENT}:
                return False
            raise FdGatewayError(error, "cannot inspect extended ACL")
        try:
            entry = ctypes.c_void_p()
            result = _acl_get_entry(acl, ACL_FIRST_ENTRY, ctypes.byref(entry))
            if result < 0:
                error = ctypes.get_errno()
                raise FdGatewayError(error, "cannot enumerate extended ACL")
            return result == 0 and bool(entry.value)
        finally:
            _acl_free(acl)


def _basename(value: str) -> None:
    if not isinstance(value, str) or not value or value in {".", ".."} or "/" in value or "\x00" in value:
        raise ValueError("invalid canonical basename")


def _components(relative_path: str):
    if not isinstance(relative_path, str) or not relative_path or relative_path.startswith("/"):
        raise ValueError("invalid canonical relative directory path")
    values = relative_path.split("/")
    if any(value in {"", ".", ".."} or "\x00" in value for value in values):
        raise ValueError("invalid canonical relative directory path")
    return values


def _validate_metadata(fd: int, expected_type: str, device: int, uid: int, gid: int, mode: int,
                       metadata: CleanMetadataAdapter):
    status = os.fstat(fd)
    expected_predicate = stat.S_ISDIR if expected_type == "directory" else stat.S_ISREG
    if not expected_predicate(status.st_mode):
        raise FdGatewayError(f"held FD is not a {expected_type}")
    if status.st_dev != device:
        raise FdGatewayError("held FD crossed filesystem device")
    if (status.st_uid, status.st_gid) != (uid, gid):
        raise FdGatewayError("held FD owner or group mismatch")
    if stat.S_IMODE(status.st_mode) != mode:
        raise FdGatewayError("held FD mode mismatch")
    if getattr(status, "st_flags", 0) != 0:
        raise FdGatewayError("held FD has nonzero BSD flags")
    if metadata.xattr_bytes(fd) != 0:
        raise FdGatewayError("held FD has xattrs")
    if metadata.has_extended_acl(fd):
        raise FdGatewayError("held FD has an extended ACL")
    return status


def open_directory_path(root_fd: int, relative_path: str, expected_root_identity: Tuple[int, int],
                        uid: int, gid: int, mode: int, metadata: CleanMetadataAdapter) -> int:
    components = _components(relative_path)
    root_status = os.fstat(root_fd)
    if (root_status.st_dev, root_status.st_ino) != expected_root_identity:
        raise FdGatewayError("canonical root identity mismatch")
    _validate_metadata(root_fd, "directory", root_status.st_dev, uid, gid, mode, metadata)
    current = os.dup(root_fd)
    try:
        for component in components:
            try:
                child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                                dir_fd=current)
            except OSError as exc:
                raise FdGatewayError(exc.errno, f"cannot open canonical directory component {component!r}") from exc
            try:
                _validate_metadata(child, "directory", root_status.st_dev, uid, gid, mode, metadata)
            except BaseException:
                os.close(child)
                raise
            os.close(current)
            current = child
        return current
    except BaseException:
        os.close(current)
        raise


def _stable_identity(status: os.stat_result):
    return (status.st_dev, status.st_ino, status.st_mode, status.st_uid, status.st_gid, status.st_nlink,
            status.st_size, status.st_mtime_ns, status.st_ctime_ns, getattr(status, "st_flags", 0))


def read_regular_file_at_identity(parent_fd: int, name: str, minimum_bytes: int, maximum_bytes: int,
                                  uid: int, gid: int, mode: int,
                                  metadata: CleanMetadataAdapter) -> Tuple[bytes, Tuple[int, int]]:
    _basename(name)
    if isinstance(minimum_bytes, bool) or isinstance(maximum_bytes, bool) or not isinstance(minimum_bytes, int) or not isinstance(maximum_bytes, int) or not 0 <= minimum_bytes <= maximum_bytes:
        raise ValueError("invalid byte bounds")
    parent_status = os.fstat(parent_fd)
    if not stat.S_ISDIR(parent_status.st_mode):
        raise FdGatewayError("parent FD is not a directory")
    try:
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent_fd)
    except OSError as exc:
        raise FdGatewayError(exc.errno, f"cannot open canonical regular file {name!r}") from exc
    try:
        before = _validate_metadata(fd, "regular file", parent_status.st_dev, uid, gid, mode, metadata)
        if before.st_nlink != 1:
            raise FdGatewayError("regular file link count is not one")
        if not minimum_bytes <= before.st_size <= maximum_bytes:
            raise FdGatewayError("regular file size outside bounds")
        chunks = bytearray()
        while True:
            chunk = os.read(fd, min(131072, maximum_bytes + 1 - len(chunks)))
            if not chunk:
                break
            chunks.extend(chunk)
            if len(chunks) > maximum_bytes:
                raise FdGatewayError("regular file exceeded maximum during read")
        after = _validate_metadata(fd, "regular file", parent_status.st_dev, uid, gid, mode, metadata)
        if _stable_identity(before) != _stable_identity(after) or len(chunks) != before.st_size:
            raise FdGatewayError("regular file changed during held-FD read")
        return bytes(chunks), (before.st_dev, before.st_ino)
    finally:
        os.close(fd)


def read_regular_file_at(parent_fd: int, name: str, minimum_bytes: int, maximum_bytes: int,
                         uid: int, gid: int, mode: int, metadata: CleanMetadataAdapter) -> bytes:
    data, _identity = read_regular_file_at_identity(
        parent_fd, name, minimum_bytes, maximum_bytes, uid, gid, mode, metadata,
    )
    return data
