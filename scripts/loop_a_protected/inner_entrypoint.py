from __future__ import annotations

import hashlib
import json
import os
import socket
import stat
import struct


_ROLES = (
    "entrypoint",
    "result",
    "diagnostics",
    "challenge",
    "attestation-control",
    "retained-executable",
    "version-root",
    "manifest",
    "inventory",
    "source",
)
_ENTRYPOINT = "libexec/inner-entrypoint.py"


def _canonical_bytes(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"), sort_keys=True).encode("utf-8") + b"\n"


def _with_digest(value, field):
    finalized = dict(value)
    finalized[field] = hashlib.sha256(_canonical_bytes(value)).hexdigest()
    return finalized


def _read_all(fd):
    os.lseek(fd, 0, os.SEEK_SET)
    chunks = bytearray()
    while True:
        chunk = os.read(fd, 131072)
        if not chunk:
            return bytes(chunks)
        chunks.extend(chunk)


def _recv_exact(channel, count):
    chunks = bytearray()
    while len(chunks) < count:
        chunk = channel.recv(count - len(chunks))
        if not chunk:
            raise RuntimeError("attestation acknowledgement closed early")
        chunks.extend(chunk)
    return bytes(chunks)


def _inventory_item(role, fd, digest):
    value = os.fstat(fd)
    return {
        "role": role,
        "fd": fd,
        "device": value.st_dev,
        "inode": value.st_ino,
        "mode": stat.S_IMODE(value.st_mode),
        "uid": value.st_uid,
        "gid": value.st_gid,
        "link_count": value.st_nlink,
        "byte_count": value.st_size if stat.S_ISREG(value.st_mode) else None,
        "sha256": digest,
    }


def main():
    manifest = json.loads(_read_all(7))
    inventory = json.loads(_read_all(8))
    source = _read_all(9)
    entries = {
        item["relative_path"]: item
        for item in inventory["entries"]
        if item.get("type") == "file"
    }
    digests = (
        entries[_ENTRYPOINT]["sha256"],
        None,
        None,
        None,
        None,
        entries["bin/python3"]["sha256"],
        None,
        manifest["version_digest"],
        inventory["inventory_digest"],
        hashlib.sha256(source).hexdigest(),
    )
    nonce = os.read(3, 33)
    if len(nonce) != 32:
        raise RuntimeError("attestation challenge must be exactly 32 bytes")
    record = {
        "schema": 1,
        "nonce": nonce.hex(),
        "child_pid": os.getpid(),
        "executable_device": os.fstat(5).st_dev,
        "executable_inode": os.fstat(5).st_ino,
        "executable_byte_count": os.fstat(5).st_size,
        "executable_sha256": entries["bin/python3"]["sha256"],
        "manifest_digest": manifest["version_digest"],
        "inventory_digest": inventory["inventory_digest"],
        "protected_fd_inventory": [
            _inventory_item(role, fd, digest)
            for fd, (role, digest) in enumerate(zip(_ROLES, digests))
        ],
        "record_digest": None,
    }
    record = _with_digest(record, "record_digest")
    payload = _canonical_bytes(record)
    channel = socket.socket(fileno=4)
    channel.sendall(struct.pack(">I", len(payload)) + payload)
    channel.shutdown(socket.SHUT_WR)
    length = struct.unpack(">I", _recv_exact(channel, 4))[0]
    if not 1 <= length <= 65536:
        raise RuntimeError("attestation acknowledgement is outside the fixed bound")
    acknowledgement = json.loads(_recv_exact(channel, length))
    if (
        acknowledgement.get("schema") != 1
        or acknowledgement.get("nonce") != nonce.hex()
        or acknowledgement.get("child_pid") != os.getpid()
        or acknowledgement.get("capability") != "attestation-only"
    ):
        raise RuntimeError("attestation acknowledgement differs")
    os.write(1, source)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
