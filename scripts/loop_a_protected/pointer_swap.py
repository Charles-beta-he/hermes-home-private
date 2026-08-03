from __future__ import annotations

import ctypes
import os
import re
import stat
from dataclasses import dataclass
from typing import Any, Dict, Tuple

from .fd_gateway import CleanMetadataAdapter, _validate_metadata
from .publication import RENAME_SWAP, _renameatx_np
from .root_gate import RootMutationGate
from .swap_evidence import load_bound_swap_evidence


O_SYMLINK = 0x00200000
_TARGET = re.compile(r"versions/[0-9a-f]{64}\Z")
_STATES = {
    "runtime": "RUNTIME_POINTER_STAGED",
    "active-skills": "SKILL_POINTER_STAGED",
}


class PointerSwapError(OSError):
    pass


@dataclass(frozen=True)
class PointerSwapResult:
    kind: str
    current_inode: int
    retained_inode: int
    current_target: str
    retained_target: str
    retained_name: str


def _validate_target(value: str) -> None:
    if not isinstance(value, str) or not _TARGET.fullmatch(value):
        raise PointerSwapError("version pointer target is not canonical")


def _open_and_validate_symlink(parent_fd: int, name: str, device: int, uid: int, gid: int,
                               metadata: CleanMetadataAdapter):
    fd = os.open(name, os.O_RDONLY | os.O_CLOEXEC | O_SYMLINK, dir_fd=parent_fd)
    try:
        value = os.fstat(fd)
        if not stat.S_ISLNK(value.st_mode) or value.st_nlink != 1:
            raise PointerSwapError("version pointer is not a one-link symlink")
        if value.st_dev != device or (value.st_uid, value.st_gid) != (uid, gid):
            raise PointerSwapError("version pointer identity or owner mismatch")
        if getattr(value, "st_flags", 0) != 0:
            raise PointerSwapError("version pointer has BSD flags")
        if metadata.xattr_bytes(fd) != 0 or metadata.has_extended_acl(fd):
            raise PointerSwapError("version pointer has xattrs or extended ACL")
        return fd, value
    except BaseException:
        os.close(fd)
        raise


def swap_version_pointer(*, parent_fd: int, expected_parent_identity: Tuple[int, int],
                         gate: RootMutationGate, authorization: Dict[str, Any],
                         kind: str, staged_name: str,
                         expected_current_target: str, expected_staged_target: str,
                         uid: int, gid: int,
                         metadata: CleanMetadataAdapter) -> PointerSwapResult:
    if kind not in _STATES:
        raise ValueError("unknown protected version-pointer kind")
    expected_staged_name = f".current.txn-{authorization.get('authorization_payload', {}).get('transaction_uuid', '')}.tmp"
    if staged_name != expected_staged_name:
        raise PointerSwapError("version pointer staged name is not exact transaction-qualified name")
    if not isinstance(staged_name, str) or not staged_name or staged_name in {".", "..", "current"} or "/" in staged_name or "\x00" in staged_name:
        raise ValueError("invalid staged pointer basename")
    _validate_target(expected_current_target)
    _validate_target(expected_staged_target)
    current_fd = -1
    staged_fd = -1
    try:
        gate.assert_live()
        parent = os.fstat(parent_fd)
        if (parent.st_dev, parent.st_ino) != expected_parent_identity:
            raise PointerSwapError("version pointer parent identity mismatch")
        _validate_metadata(parent_fd, "directory", parent.st_dev, uid, gid, 0o755, metadata)
        evidence = load_bound_swap_evidence(
            gate=gate, authorization=authorization, expected_state=_STATES[kind],
            expected_role=f"{kind}-pointer", uid=uid, gid=gid, metadata=metadata,
        )
        if (evidence["parent_device"], evidence["parent_inode"]) != expected_parent_identity:
            raise PointerSwapError("version pointer journal parent identity mismatch")
        if (evidence["current_name"], evidence["staged_name"]) != ("current", staged_name):
            raise PointerSwapError("version pointer journal pathname binding mismatch")
        if (evidence["current_target"], evidence["staged_target"]) != (
                expected_current_target, expected_staged_target):
            raise PointerSwapError("version pointer journal target binding mismatch")
        current_fd, current = _open_and_validate_symlink(parent_fd, "current", parent.st_dev, uid, gid, metadata)
        staged_fd, staged = _open_and_validate_symlink(parent_fd, staged_name, parent.st_dev, uid, gid, metadata)
        if ((current.st_dev, current.st_ino), (staged.st_dev, staged.st_ino)) != (
                (evidence["current_device"], evidence["current_inode"]),
                (evidence["staged_device"], evidence["staged_inode"]),
        ):
            raise PointerSwapError("version pointer inode differs from durable journal evidence")
        current_target = os.readlink("current", dir_fd=parent_fd)
        staged_target = os.readlink(staged_name, dir_fd=parent_fd)
        if current_target != expected_current_target or staged_target != expected_staged_target:
            raise PointerSwapError("version pointer target mismatch")
        current_named = os.stat("current", dir_fd=parent_fd, follow_symlinks=False)
        staged_named = os.stat(staged_name, dir_fd=parent_fd, follow_symlinks=False)
        if ((current_named.st_dev, current_named.st_ino), (staged_named.st_dev, staged_named.st_ino)) != (
            (current.st_dev, current.st_ino), (staged.st_dev, staged.st_ino)
        ):
            raise PointerSwapError("version pointer pathname identity changed")
        gate.assert_live()
        result = _renameatx_np(
            parent_fd, os.fsencode("current"), parent_fd, os.fsencode(staged_name), RENAME_SWAP,
        )
        if result != 0:
            error = ctypes.get_errno()
            raise PointerSwapError(error, os.strerror(error))
        new_current = os.stat("current", dir_fd=parent_fd, follow_symlinks=False)
        retained = os.stat(staged_name, dir_fd=parent_fd, follow_symlinks=False)
        if ((new_current.st_dev, new_current.st_ino), (retained.st_dev, retained.st_ino)) != (
            (staged.st_dev, staged.st_ino), (current.st_dev, current.st_ino)
        ):
            raise PointerSwapError("version pointer swap identity readback mismatch")
        if os.readlink("current", dir_fd=parent_fd) != expected_staged_target:
            raise PointerSwapError("version pointer final target readback mismatch")
        if os.readlink(staged_name, dir_fd=parent_fd) != expected_current_target:
            raise PointerSwapError("version pointer retained target readback mismatch")
        os.fsync(parent_fd)
        gate.assert_live()
        return PointerSwapResult(
            kind=kind,
            current_inode=staged.st_ino,
            retained_inode=current.st_ino,
            current_target=expected_staged_target,
            retained_target=expected_current_target,
            retained_name=staged_name,
        )
    except BaseException as exc:
        if isinstance(exc, (KeyboardInterrupt, SystemExit, PointerSwapError)):
            raise
        raise PointerSwapError(str(exc)) from exc
    finally:
        if staged_fd >= 0:
            os.close(staged_fd)
        if current_fd >= 0:
            os.close(current_fd)
