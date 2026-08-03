from __future__ import annotations

import array
import fcntl
import os
import re
import socket
import stat
import struct
from dataclasses import dataclass
from typing import Dict, FrozenSet, Mapping, Tuple

from .canonical import CanonicalJSONError, canonical_bytes, parse_canonical_bytes, with_self_digest
from .schema_bundle import SchemaBundleError, validate_instance
from .validation import ProtocolValidationError, validate_uuid


class DarwinLaunchdTransportError(RuntimeError):
    pass


PROTECTED_ROLES = (
    "entrypoint",
    "retained-executable",
    "version-root",
    "runtime-manifest",
    "runtime-inventory",
    "source",
)
_MAX_FRAME = 65_536


@dataclass(frozen=True)
class ReceivedFdBundle:
    transaction_uuid: str
    broker_pid: int
    nonce: str
    descriptors: Mapping[str, int]
    record: Mapping[str, object]

    def close(self) -> None:
        for fd in self.descriptors.values():
            try:
                os.close(fd)
            except OSError:
                pass


def _record(*, transaction_uuid: str, broker_pid: int, nonce: str) -> Dict[str, object]:
    try:
        validate_uuid(transaction_uuid)
    except (ProtocolValidationError, TypeError) as exc:
        raise DarwinLaunchdTransportError("bundle transaction UUID is invalid") from exc
    if (isinstance(broker_pid, bool) or not isinstance(broker_pid, int) or broker_pid <= 0):
        raise DarwinLaunchdTransportError("bundle broker PID is invalid")
    if not isinstance(nonce, str) or re.fullmatch(r"[0-9a-f]{64}", nonce) is None:
        raise DarwinLaunchdTransportError("bundle nonce is invalid")
    value = {
        "schema": 1,
        "transaction_uuid": transaction_uuid,
        "broker_pid": broker_pid,
        "nonce": nonce,
        "roles": list(PROTECTED_ROLES),
        "capability": "read-only-input-bundle",
        "record_digest": None,
    }
    finalized = with_self_digest(value, "record_digest")
    try:
        validate_instance("launchd-fd-bundle-final-v1", finalized)
    except SchemaBundleError as exc:
        raise DarwinLaunchdTransportError("bundle record schema is invalid") from exc
    return finalized


def _directory_is_within(fd: int, forbidden: FrozenSet[Tuple[int, int]]) -> bool:
    current = os.dup(fd)
    try:
        for _ in range(256):
            status = os.fstat(current)
            identity = (status.st_dev, status.st_ino)
            if identity in forbidden:
                return True
            parent = os.open(
                "..", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=current,
            )
            parent_status = os.fstat(parent)
            if (parent_status.st_dev, parent_status.st_ino) == identity:
                os.close(parent)
                return False
            os.close(current)
            current = parent
        raise DarwinLaunchdTransportError("version-root ancestry exceeds fixed bound")
    finally:
        os.close(current)


def send_fd_bundle(sock: socket.socket, *, transaction_uuid: str, broker_pid: int,
                   nonce: str, descriptors: Mapping[str, int],
                   expected_identities: Mapping[str, Tuple[int, int]],
                   mutation_root_identities: FrozenSet[Tuple[int, int]]) -> Mapping[str, object]:
    if (not isinstance(sock, socket.socket) or sock.family != socket.AF_UNIX
            or (sock.type & 0xF) != socket.SOCK_STREAM):
        raise DarwinLaunchdTransportError("bundle channel is not AF_UNIX stream")
    if set(descriptors) != set(PROTECTED_ROLES):
        raise DarwinLaunchdTransportError("protected descriptor roles are not exact")
    if set(expected_identities) != set(PROTECTED_ROLES):
        raise DarwinLaunchdTransportError("protected descriptor identity contract is not exact")
    if not isinstance(mutation_root_identities, frozenset):
        raise DarwinLaunchdTransportError("mutation-root identity set is not frozen")
    ordered = []
    identities = set()
    for role in PROTECTED_ROLES:
        fd = descriptors[role]
        if isinstance(fd, bool) or not isinstance(fd, int) or fd < 0:
            raise DarwinLaunchdTransportError(f"{role} descriptor is invalid")
        status = os.fstat(fd)
        if fcntl.fcntl(fd, fcntl.F_GETFL) & os.O_ACCMODE != os.O_RDONLY:
            raise DarwinLaunchdTransportError(f"{role} descriptor is not read-only")
        identity = (status.st_dev, status.st_ino)
        if expected_identities[role] != identity:
            raise DarwinLaunchdTransportError(f"{role} descriptor identity differs from approved handle")
        expected_type = stat.S_ISDIR(status.st_mode) if role == "version-root" else stat.S_ISREG(status.st_mode)
        if not expected_type:
            raise DarwinLaunchdTransportError(f"{role} descriptor type is invalid")
        if identity in mutation_root_identities:
            raise DarwinLaunchdTransportError(f"{role} descriptor is a canonical mutation root")
        if role == "version-root" and _directory_is_within(fd, mutation_root_identities):
            raise DarwinLaunchdTransportError("version-root is beneath a canonical mutation root")
        if identity in identities:
            raise DarwinLaunchdTransportError("protected descriptor inode alias")
        identities.add(identity)
        ordered.append(fd)
    record = _record(transaction_uuid=transaction_uuid, broker_pid=broker_pid, nonce=nonce)
    payload = canonical_bytes(record)
    frame = struct.pack(">I", len(payload)) + payload
    rights = array.array("i", ordered)
    try:
        sent = sock.sendmsg([frame], [(socket.SOL_SOCKET, socket.SCM_RIGHTS, rights)])
    except OSError as exc:
        raise DarwinLaunchdTransportError("protected descriptor bundle send failed") from exc
    if sent != len(frame):
        raise DarwinLaunchdTransportError("protected descriptor bundle send was short")
    return record


def receive_fd_bundle(sock: socket.socket) -> ReceivedFdBundle:
    if (not isinstance(sock, socket.socket) or sock.family != socket.AF_UNIX
            or (sock.type & 0xF) != socket.SOCK_STREAM):
        raise DarwinLaunchdTransportError("bundle channel is not AF_UNIX stream")
    item_size = array.array("i").itemsize
    flags = getattr(socket, "MSG_CMSG_CLOEXEC", 0)
    received: list[int] = []
    try:
        first, ancillary, message_flags, _address = sock.recvmsg(
            _MAX_FRAME + 4, socket.CMSG_SPACE(item_size * len(PROTECTED_ROLES)), flags,
        )
        if message_flags & (socket.MSG_TRUNC | socket.MSG_CTRUNC):
            raise DarwinLaunchdTransportError("protected descriptor bundle was truncated")
        if len(first) < 4:
            while len(first) < 4:
                chunk = sock.recv(4 - len(first))
                if not chunk:
                    raise DarwinLaunchdTransportError("protected descriptor bundle header was short")
                first += chunk
        length = struct.unpack(">I", first[:4])[0]
        if not 1 <= length <= _MAX_FRAME:
            raise DarwinLaunchdTransportError("protected descriptor bundle size is invalid")
        body = bytearray(first[4:])
        if len(body) > length:
            raise DarwinLaunchdTransportError("protected descriptor bundle has trailing frame data")
        while len(body) < length:
            chunk = sock.recv(length - len(body))
            if not chunk:
                raise DarwinLaunchdTransportError("protected descriptor bundle body was short")
            body.extend(chunk)
        payload = bytes(body)
        rights_records = [item for item in ancillary if item[0:2] == (socket.SOL_SOCKET, socket.SCM_RIGHTS)]
        if len(rights_records) != 1 or len(ancillary) != 1:
            raise DarwinLaunchdTransportError("protected descriptor ancillary set is not exact")
        raw = rights_records[0][2]
        if len(raw) != item_size * len(PROTECTED_ROLES):
            raise DarwinLaunchdTransportError("protected descriptor count is not exact")
        values = array.array("i")
        values.frombytes(raw)
        received = list(values)
        for role, fd in zip(PROTECTED_ROLES, received):
            os.set_inheritable(fd, False)
            if fcntl.fcntl(fd, fcntl.F_GETFL) & os.O_ACCMODE != os.O_RDONLY:
                raise DarwinLaunchdTransportError("received protected descriptor is not read-only")
            status = os.fstat(fd)
            expected_type = stat.S_ISDIR(status.st_mode) if role == "version-root" else stat.S_ISREG(status.st_mode)
            if not expected_type:
                raise DarwinLaunchdTransportError(f"received {role} descriptor type is invalid")
        try:
            value = parse_canonical_bytes(payload)
        except CanonicalJSONError as exc:
            raise DarwinLaunchdTransportError("bundle record is not canonical JSON") from exc
        if not isinstance(value, dict):
            raise DarwinLaunchdTransportError("bundle record is not an object")
        transaction_uuid_value = value.get("transaction_uuid")
        broker_pid_value = value.get("broker_pid")
        nonce_value = value.get("nonce")
        if (not isinstance(transaction_uuid_value, str)
                or isinstance(broker_pid_value, bool) or not isinstance(broker_pid_value, int)
                or not isinstance(nonce_value, str)):
            raise DarwinLaunchdTransportError("bundle identity fields are invalid")
        expected = _record(
            transaction_uuid=transaction_uuid_value,
            broker_pid=broker_pid_value,
            nonce=nonce_value,
        )
        if canonical_bytes(value) != canonical_bytes(expected):
            raise DarwinLaunchdTransportError("bundle record differs from exact protocol")
        descriptors: Dict[str, int] = dict(zip(PROTECTED_ROLES, received))
        if len({(os.fstat(fd).st_dev, os.fstat(fd).st_ino) for fd in received}) != len(received):
            raise DarwinLaunchdTransportError("received descriptor inode alias")
        received = []
        return ReceivedFdBundle(
            transaction_uuid=transaction_uuid_value,
            broker_pid=broker_pid_value,
            nonce=nonce_value,
            descriptors=descriptors,
            record=expected,
        )
    except (OSError, TypeError, ValueError) as exc:
        if isinstance(exc, DarwinLaunchdTransportError):
            raise
        raise DarwinLaunchdTransportError("protected descriptor bundle receive failed closed") from exc
    finally:
        for fd in received:
            try:
                os.close(fd)
            except OSError:
                pass
