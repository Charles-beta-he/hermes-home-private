from __future__ import annotations

import hashlib
import os
import stat
from dataclasses import dataclass
from typing import Dict, Optional

from .fd_gateway import CleanMetadataAdapter
from .publication import FaultHook, PublicationError, PublishedFile, _emit, publish_regular_file


class SourceCaptureError(OSError):
    pass


@dataclass(frozen=True)
class CapturedSource:
    byte_count: int
    sha256: str
    concurrently_changed: bool
    before: Dict[str, int]
    after: Dict[str, int]
    published: PublishedFile


def _basename(value: str) -> None:
    if not isinstance(value, str) or not value or value in {".", ".."} or "/" in value or "\x00" in value:
        raise ValueError("invalid approved source basename")


def _evidence(status: os.stat_result) -> Dict[str, int]:
    return {
        "device": status.st_dev, "inode": status.st_ino, "mode": status.st_mode,
        "uid": status.st_uid, "gid": status.st_gid, "link_count": status.st_nlink,
        "byte_count": status.st_size, "mtime_ns": status.st_mtime_ns, "ctime_ns": status.st_ctime_ns,
        "bsd_flags": getattr(status, "st_flags", 0),
    }


def capture_source(source_parent_fd: int, source_name: str, protected_parent_fd: int,
                   uid: int, gid: int, transaction_uuid: str, metadata: CleanMetadataAdapter,
                   fault_hook: Optional[FaultHook] = None) -> CapturedSource:
    _basename(source_name)
    source_fd = -1
    try:
        try:
            source_fd = os.open(source_name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
                                dir_fd=source_parent_fd)
        except OSError as exc:
            raise SourceCaptureError(exc.errno, "cannot open approved source through held parent FD") from exc
        before_status = os.fstat(source_fd)
        if not stat.S_ISREG(before_status.st_mode) or before_status.st_nlink != 1:
            raise SourceCaptureError("approved source must be a one-link regular file")
        if not 1 <= before_status.st_size <= 8_388_608:
            raise SourceCaptureError("approved source pre-read size is outside 1..8388608")
        before = _evidence(before_status)
        captured = bytearray()
        while True:
            try:
                chunk = os.read(source_fd, min(131072, 8_388_609 - len(captured)))
            except OSError as exc:
                raise SourceCaptureError(exc.errno, "source read failed") from exc
            if not chunk:
                break
            captured.extend(chunk)
            if len(captured) > 8_388_608:
                raise SourceCaptureError("source exceeded maximum during capture")
            _emit(fault_hook, "after_source_chunk", fd=source_fd, byte_count=len(captured))
        after_status = os.fstat(source_fd)
        after = _evidence(after_status)
        concurrently_changed = before != after
        payload = bytes(captured)
        digest = hashlib.sha256(payload).hexdigest()
        final_name = f"source-{digest}.bin"
        published = publish_regular_file(
            protected_parent_fd, final_name, payload, 0o400, uid, gid,
            transaction_uuid, fault_hook, metadata,
        )
        return CapturedSource(len(payload), digest, concurrently_changed, before, after, published)
    except SourceCaptureError:
        raise
    except PublicationError as exc:
        raise SourceCaptureError("protected source publication failed") from exc
    except BaseException as exc:
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        raise SourceCaptureError(str(exc)) from exc
    finally:
        if source_fd >= 0:
            os.close(source_fd)
