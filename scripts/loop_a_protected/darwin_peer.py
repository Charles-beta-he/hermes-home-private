from __future__ import annotations

import ctypes
import os
import socket
import sys
from dataclasses import dataclass
from typing import Optional


class DarwinPeerError(PermissionError):
    pass


_SOL_LOCAL = 0
_LOCAL_PEERPID = 0x002
_LOCAL_PEEREPID = 0x003


@dataclass(frozen=True)
class PeerCredentials:
    pid: int
    effective_pid: int
    uid: int
    gid: int


def _libc() -> ctypes.CDLL:
    library = ctypes.CDLL(None, use_errno=True)
    library.getpeereid.argtypes = [
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_uint32),
        ctypes.POINTER(ctypes.c_uint32),
    ]
    library.getpeereid.restype = ctypes.c_int
    library.getsockopt.argtypes = [
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_uint32),
    ]
    library.getsockopt.restype = ctypes.c_int
    return library


def _peer_pid(library: ctypes.CDLL, fd: int, option: int) -> int:
    value = ctypes.c_int()
    length = ctypes.c_uint32(ctypes.sizeof(value))
    ctypes.set_errno(0)
    if library.getsockopt(fd, _SOL_LOCAL, option, ctypes.byref(value), ctypes.byref(length)) != 0:
        error = ctypes.get_errno()
        raise DarwinPeerError(f"Darwin peer PID readback failed: errno={error}")
    if length.value != ctypes.sizeof(value) or value.value <= 0:
        raise DarwinPeerError("Darwin peer PID readback has an invalid ABI result")
    return int(value.value)


def read_peer_credentials(sock: socket.socket) -> PeerCredentials:
    if sys.platform != "darwin":
        raise DarwinPeerError("Darwin peer credentials require macOS")
    if (not isinstance(sock, socket.socket) or sock.family != socket.AF_UNIX
            or (sock.type & 0xF) not in {socket.SOCK_STREAM, socket.SOCK_SEQPACKET}):
        raise DarwinPeerError("peer channel must be an AF_UNIX stream or seqpacket socket")
    try:
        sock.getpeername()
        fd = sock.fileno()
        os.fstat(fd)
    except OSError as exc:
        raise DarwinPeerError("peer channel is not connected") from exc
    library = _libc()
    uid = ctypes.c_uint32()
    gid = ctypes.c_uint32()
    ctypes.set_errno(0)
    if library.getpeereid(fd, ctypes.byref(uid), ctypes.byref(gid)) != 0:
        error = ctypes.get_errno()
        raise DarwinPeerError(f"Darwin peer UID/GID readback failed: errno={error}")
    return PeerCredentials(
        pid=_peer_pid(library, fd, _LOCAL_PEERPID),
        effective_pid=_peer_pid(library, fd, _LOCAL_PEEREPID),
        uid=int(uid.value),
        gid=int(gid.value),
    )


def validate_root_broker_peer(sock: socket.socket, *, expected_pid: Optional[int] = None) -> PeerCredentials:
    if expected_pid is not None and (isinstance(expected_pid, bool) or not isinstance(expected_pid, int) or expected_pid <= 0):
        raise DarwinPeerError("expected root broker PID is invalid")
    observed = read_peer_credentials(sock)
    if observed.uid != 0 or observed.gid != 0:
        raise DarwinPeerError("worker channel peer is not the root broker identity")
    if expected_pid is not None and (observed.pid != expected_pid or observed.effective_pid != expected_pid):
        raise DarwinPeerError("worker channel root broker PID differs")
    return observed


def validate_launchd_worker_peer(sock: socket.socket, *, broker_euid: int,
                                 expected_pid: int, expected_uid: int,
                                 expected_gid: int) -> PeerCredentials:
    if broker_euid != 0:
        raise DarwinPeerError("launchd worker admission requires a root broker")
    for value, label in ((expected_pid, "PID"), (expected_uid, "UID"), (expected_gid, "GID")):
        if isinstance(value, bool) or not isinstance(value, int) or value < (1 if label in {"PID", "UID"} else 0):
            raise DarwinPeerError(f"expected worker {label} is invalid")
    observed = read_peer_credentials(sock)
    if observed.pid != expected_pid:
        raise DarwinPeerError("launchd worker peer PID differs")
    if observed.effective_pid != expected_pid:
        raise DarwinPeerError("launchd worker effective PID differs")
    if observed.uid != expected_uid:
        raise DarwinPeerError("launchd worker peer UID differs")
    if observed.gid != expected_gid:
        raise DarwinPeerError("launchd worker peer GID differs")
    return observed
