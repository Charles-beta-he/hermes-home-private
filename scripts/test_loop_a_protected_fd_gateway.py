from __future__ import annotations

import os
import subprocess

import pytest

from loop_a_protected.fd_gateway import (
    CleanMetadataAdapter,
    FdGatewayError,
    open_directory_path,
    read_regular_file_at,
)


class HostileMetadata(CleanMetadataAdapter):
    def __init__(self, *, xattrs=0, acl=False):
        self.xattrs = xattrs
        self.acl = acl

    def xattr_bytes(self, fd):
        return self.xattrs

    def has_extended_acl(self, fd):
        return self.acl


def root_fd(path):
    return os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)


def test_component_traversal_is_root_identity_pinned_and_reads_held_fd(tmp_path):
    os.chmod(tmp_path, 0o700)
    child = tmp_path / "a"
    child.mkdir(mode=0o700)
    payload = child / "payload.json"
    payload.write_bytes(b"exact bytes")
    os.chmod(payload, 0o600)
    root = root_fd(tmp_path)
    status = os.fstat(root)
    opened = -1
    try:
        opened = open_directory_path(root, "a", (status.st_dev, status.st_ino), os.getuid(), os.getgid(), 0o700,
                                     HostileMetadata())
        assert read_regular_file_at(opened, "payload.json", 1, 1024, os.getuid(), os.getgid(), 0o600,
                                    HostileMetadata()) == b"exact bytes"
    finally:
        if opened >= 0:
            os.close(opened)
        os.close(root)


def test_dotdot_absolute_symlink_and_wrong_root_identity_are_rejected(tmp_path):
    os.chmod(tmp_path, 0o700)
    real = tmp_path / "real"
    real.mkdir(mode=0o700)
    (tmp_path / "link").symlink_to(real, target_is_directory=True)
    root = root_fd(tmp_path)
    status = os.fstat(root)
    try:
        for path in ("../real", "/real", "real/../real", "", "."):
            with pytest.raises((FdGatewayError, ValueError)):
                open_directory_path(root, path, (status.st_dev, status.st_ino), os.getuid(), os.getgid(), 0o700,
                                    HostileMetadata())
        with pytest.raises(FdGatewayError):
            open_directory_path(root, "link", (status.st_dev, status.st_ino), os.getuid(), os.getgid(), 0o700,
                                HostileMetadata())
        with pytest.raises(FdGatewayError, match="root identity"):
            open_directory_path(root, "real", (status.st_dev, status.st_ino + 1), os.getuid(), os.getgid(), 0o700,
                                HostileMetadata())
    finally:
        os.close(root)


def test_real_darwin_extended_acl_is_detected(tmp_path):
    target = tmp_path / "acl-target"
    target.write_bytes(b"x")
    user = subprocess.run(["id", "-un"], check=True, capture_output=True, text=True).stdout.strip()
    subprocess.run(["chmod", "+a", f"user:{user} allow read", str(target)], check=True)
    fd = os.open(target, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        assert CleanMetadataAdapter().has_extended_acl(fd) is True
    finally:
        os.close(fd)


def test_directory_acl_xattr_flags_or_mode_mismatch_fails_before_descent(tmp_path):
    os.chmod(tmp_path, 0o700)
    (tmp_path / "a").mkdir(mode=0o700)
    root = root_fd(tmp_path)
    identity = (os.fstat(root).st_dev, os.fstat(root).st_ino)
    try:
        for adapter in (HostileMetadata(xattrs=4), HostileMetadata(acl=True)):
            with pytest.raises(FdGatewayError):
                open_directory_path(root, "a", identity, os.getuid(), os.getgid(), 0o700, adapter)
        os.chmod(tmp_path / "a", 0o755)
        with pytest.raises(FdGatewayError, match="mode"):
            open_directory_path(root, "a", identity, os.getuid(), os.getgid(), 0o700, HostileMetadata())
    finally:
        os.close(root)


def test_regular_file_symlink_hardlink_and_metadata_attacks_are_rejected(tmp_path):
    os.chmod(tmp_path, 0o700)
    target = tmp_path / "target"
    target.write_bytes(b"payload")
    os.chmod(target, 0o600)
    os.link(target, tmp_path / "hard")
    (tmp_path / "soft").symlink_to(target)
    root = root_fd(tmp_path)
    try:
        with pytest.raises(FdGatewayError, match="link count"):
            read_regular_file_at(root, "target", 1, 100, os.getuid(), os.getgid(), 0o600, HostileMetadata())
        with pytest.raises(FdGatewayError):
            read_regular_file_at(root, "soft", 1, 100, os.getuid(), os.getgid(), 0o600, HostileMetadata())
        os.unlink(tmp_path / "hard")
        with pytest.raises(FdGatewayError, match="xattr"):
            read_regular_file_at(root, "target", 1, 100, os.getuid(), os.getgid(), 0o600, HostileMetadata(xattrs=1))
    finally:
        os.close(root)
