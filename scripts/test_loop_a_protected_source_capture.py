from __future__ import annotations

import os

import pytest

from loop_a_protected.fd_gateway import CleanMetadataAdapter
from loop_a_protected.source_capture import SourceCaptureError, capture_source

TXN = "123e4567-e89b-42d3-a456-426614174000"


class TestMetadata(CleanMetadataAdapter):
    def xattr_bytes(self, fd) -> int:
        return 0

    def has_extended_acl(self, fd) -> bool:
        return False


def open_dir(path):
    return os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)


def test_untrusted_source_is_copied_once_to_digest_named_protected_inode(tmp_path):
    source_dir = tmp_path / "source"
    protected_dir = tmp_path / "protected"
    source_dir.mkdir(mode=0o700)
    protected_dir.mkdir(mode=0o700)
    payload = b"immutable protected capture\n"
    (source_dir / "input.bin").write_bytes(payload)
    source_fd, protected_fd = open_dir(source_dir), open_dir(protected_dir)
    try:
        result = capture_source(source_fd, "input.bin", protected_fd, os.getuid(), os.getgid(), TXN, TestMetadata())
    finally:
        os.close(source_fd)
        os.close(protected_fd)
    assert result.byte_count == len(payload)
    assert result.concurrently_changed is False
    assert (protected_dir / result.published.name).read_bytes() == payload
    assert result.published.name == f"source-{result.sha256}.bin"


def test_source_change_during_capture_is_recorded_but_cannot_change_protected_bytes(tmp_path):
    source_dir = tmp_path / "source"
    protected_dir = tmp_path / "protected"
    source_dir.mkdir(mode=0o700)
    protected_dir.mkdir(mode=0o700)
    source = source_dir / "input.bin"
    source.write_bytes(b"before")

    def fault(event, _context):
        if event == "after_source_chunk":
            source.write_bytes(b"after-longer")

    source_fd, protected_fd = open_dir(source_dir), open_dir(protected_dir)
    try:
        result = capture_source(
            source_fd, "input.bin", protected_fd, os.getuid(), os.getgid(), TXN, TestMetadata(), fault,
        )
    finally:
        os.close(source_fd)
        os.close(protected_fd)
    assert result.concurrently_changed is True
    protected = protected_dir / result.published.name
    captured = protected.read_bytes()
    assert captured == b"beforelonger"
    source.write_bytes(b"third mutation")
    assert protected.read_bytes() == captured


@pytest.mark.parametrize("source_kind", ["symlink", "hardlink", "empty"])
def test_non_regular_alias_or_empty_preimage_is_rejected_before_publication(tmp_path, source_kind):
    source_dir = tmp_path / "source"
    protected_dir = tmp_path / "protected"
    source_dir.mkdir(mode=0o700)
    protected_dir.mkdir(mode=0o700)
    original = source_dir / "original"
    original.write_bytes(b"x")
    name = "input.bin"
    if source_kind == "symlink":
        os.symlink("original", source_dir / name)
    elif source_kind == "hardlink":
        os.link(original, source_dir / name)
    else:
        (source_dir / name).write_bytes(b"")
    source_fd, protected_fd = open_dir(source_dir), open_dir(protected_dir)
    try:
        with pytest.raises(SourceCaptureError):
            capture_source(source_fd, name, protected_fd, os.getuid(), os.getgid(), TXN, TestMetadata())
    finally:
        os.close(source_fd)
        os.close(protected_fd)
    assert not list(protected_dir.iterdir())
