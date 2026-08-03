from __future__ import annotations

import hashlib
import os

import pytest

from loop_a_protected.canonical import canonical_bytes
from loop_a_protected.fd_gateway import CleanMetadataAdapter
from loop_a_protected.manifests import finalize_inventory, finalize_manifest
from loop_a_protected.version_tree import (
    VersionTreeError,
    publish_version_pair,
    stage_version_tree,
    verify_version_tree_at,
)

TXN = "123e4567-e89b-42d3-a456-426614174000"
LINEAGE = "123e4567-e89b-42d3-a456-426614174001"


class TestMetadata(CleanMetadataAdapter):
    def xattr_bytes(self, fd) -> int:
        return 0

    def has_extended_acl(self, fd) -> bool:
        return False


def entry(path, kind, payload=None, executable=False):
    if kind == "directory":
        return {"relative_path": path, "type": kind, "mode": 0o555, "uid": 0, "gid": 0,
                "size": None, "sha256": None, "executable": False}
    return {"relative_path": path, "type": kind, "mode": 0o555 if executable else 0o444,
            "uid": 0, "gid": 0, "size": len(payload), "sha256": hashlib.sha256(payload).hexdigest(),
            "executable": executable}


def objects(payload=b"runtime\n"):
    entries = [entry("bin", "directory"), entry("bin/python", "file", payload, True)]
    inventory = finalize_inventory("runtime", LINEAGE, 1, entries)
    closure = {
        "protected_roles": ["bin/python"], "external_dependencies": [], "platform_build": "26A1",
        "snapshot_uuid": "123e4567-e89b-42d3-a456-426614174010", "seal_identity": "sealed",
        "cryptex_generation": "c1", "dyld_cache_uuid": "123e4567-e89b-42d3-a456-426614174011",
        "sip_enabled": True,
    }
    manifest = finalize_manifest("runtime", LINEAGE, 1, "2026-08-03T01:02:03Z", 1,
                                 entries, inventory["inventory_digest"], closure)
    return manifest, inventory, {"bin/python": payload}


def open_dir(path):
    return os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)


def test_nested_tree_is_staged_under_transaction_name_then_manifest_and_tree_publish_exclusively(tmp_path):
    versions, manifests = tmp_path / "versions", tmp_path / "manifests"
    versions.mkdir(); manifests.mkdir()
    manifest, inventory, contents = objects()
    versions_fd, manifests_fd = open_dir(versions), open_dir(manifests)
    try:
        staged = stage_version_tree(versions_fd, manifest, inventory, contents,
                                    os.getuid(), os.getgid(), TXN, TestMetadata())
        assert staged.temp_name == f".tree-{TXN}.tmp"
        result = publish_version_pair(versions_fd, manifests_fd, staged, manifest, inventory,
                                      os.getuid(), os.getgid(), TXN, TestMetadata())
        verify_version_tree_at(versions_fd, manifest["version_digest"], manifest,
                               os.getuid(), os.getgid(), TestMetadata())
    finally:
        os.close(versions_fd); os.close(manifests_fd)
    assert result.version_digest == manifest["version_digest"]
    assert (manifests / f'{manifest["version_digest"]}.json').read_bytes() == canonical_bytes(manifest)
    assert (versions / manifest["version_digest"] / "bin/python").read_bytes() == b"runtime\n"


def test_content_digest_mismatch_fails_closed_and_retains_attributable_temp(tmp_path):
    versions = tmp_path / "versions"; versions.mkdir()
    manifest, inventory, _contents = objects()
    fd = open_dir(versions)
    try:
        with pytest.raises(VersionTreeError):
            stage_version_tree(fd, manifest, inventory, {"bin/python": b"wrong"},
                               os.getuid(), os.getgid(), TXN, TestMetadata())
    finally:
        os.close(fd)
    assert (versions / f".tree-{TXN}.tmp").is_dir()
    assert not (versions / manifest["version_digest"]).exists()


def test_verifier_rejects_extra_descendant(tmp_path):
    versions = tmp_path / "versions"; versions.mkdir()
    manifest, inventory, contents = objects()
    fd = open_dir(versions)
    try:
        staged = stage_version_tree(fd, manifest, inventory, contents,
                                    os.getuid(), os.getgid(), TXN, TestMetadata())
        os.chmod(versions / staged.temp_name, 0o755)
        (versions / staged.temp_name / "extra").write_bytes(b"x")
        os.chmod(versions / staged.temp_name, 0o555)
        with pytest.raises(VersionTreeError):
            verify_version_tree_at(fd, staged.temp_name, manifest, os.getuid(), os.getgid(), TestMetadata())
    finally:
        os.close(fd)


def test_invalid_transaction_uuid_has_zero_effect(tmp_path):
    versions = tmp_path / "versions"; versions.mkdir()
    manifest, inventory, contents = objects()
    fd = open_dir(versions)
    try:
        with pytest.raises((ValueError, VersionTreeError)):
            stage_version_tree(fd, manifest, inventory, contents, os.getuid(), os.getgid(),
                               "../../escape", TestMetadata())
    finally:
        os.close(fd)
    assert not list(versions.iterdir())


def test_crash_after_manifest_publication_leaves_exact_staged_peer_and_no_final_tree(tmp_path):
    versions, manifests = tmp_path / "versions", tmp_path / "manifests"
    versions.mkdir(); manifests.mkdir()
    manifest, inventory, contents = objects()
    versions_fd, manifests_fd = open_dir(versions), open_dir(manifests)
    def fault(event, _context):
        if event == "after_manifest_publication":
            raise RuntimeError("crash")
    try:
        staged = stage_version_tree(versions_fd, manifest, inventory, contents,
                                    os.getuid(), os.getgid(), TXN, TestMetadata())
        with pytest.raises(VersionTreeError):
            publish_version_pair(versions_fd, manifests_fd, staged, manifest, inventory,
                                 os.getuid(), os.getgid(), TXN, TestMetadata(), fault)
    finally:
        os.close(versions_fd); os.close(manifests_fd)
    assert (manifests / f'{manifest["version_digest"]}.json').is_file()
    assert (versions / staged.temp_name).is_dir()
    assert not (versions / manifest["version_digest"]).exists()


def test_manifest_collision_never_overwrites_existing_bytes_or_publishes_tree(tmp_path):
    versions, manifests = tmp_path / "versions", tmp_path / "manifests"
    versions.mkdir(); manifests.mkdir()
    manifest, inventory, contents = objects()
    collision = manifests / f'{manifest["version_digest"]}.json'
    collision.write_bytes(b"sentinel")
    versions_fd, manifests_fd = open_dir(versions), open_dir(manifests)
    try:
        staged = stage_version_tree(versions_fd, manifest, inventory, contents,
                                    os.getuid(), os.getgid(), TXN, TestMetadata())
        with pytest.raises(VersionTreeError):
            publish_version_pair(versions_fd, manifests_fd, staged, manifest, inventory,
                                 os.getuid(), os.getgid(), TXN, TestMetadata())
    finally:
        os.close(versions_fd); os.close(manifests_fd)
    assert collision.read_bytes() == b"sentinel"
    assert (versions / staged.temp_name).is_dir()
    assert not (versions / manifest["version_digest"]).exists()
