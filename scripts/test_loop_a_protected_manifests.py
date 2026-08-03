from __future__ import annotations

import pytest

from loop_a_protected.manifests import (
    ManifestError,
    finalize_inventory,
    finalize_manifest,
    validate_manifest_inventory_pair,
)

LINEAGE = "123e4567-e89b-42d3-a456-426614174000"
CREATED = "2026-08-03T01:02:03Z"
POLICY = 1
CLOSURE = {
    "protected_roles": ["bin/python"], "external_dependencies": [],
    "platform_build": "26A123", "snapshot_uuid": "123e4567-e89b-42d3-a456-426614174010",
    "seal_identity": "sealed-root", "cryptex_generation": "cryptex-1",
    "dyld_cache_uuid": "123e4567-e89b-42d3-a456-426614174011", "sip_enabled": True,
}


def directory(path: str):
    return {"relative_path": path, "type": "directory", "mode": 0o555, "uid": 0, "gid": 0,
            "size": None, "sha256": None, "executable": False}


def regular(path: str, digest: str = "ab" * 32, executable: bool = False):
    return {"relative_path": path, "type": "file", "mode": 0o555 if executable else 0o444,
            "uid": 0, "gid": 0, "size": 7, "sha256": digest, "executable": executable}


def test_inventory_and_manifest_finalize_with_acyclic_self_digests():
    entries = [directory("bin"), regular("bin/python", executable=True)]
    inventory = finalize_inventory("runtime", LINEAGE, 1, entries)
    manifest = finalize_manifest("runtime", LINEAGE, 1, CREATED, POLICY, entries, inventory["inventory_digest"], CLOSURE)
    validate_manifest_inventory_pair(manifest, inventory)
    assert manifest["version_digest"] and inventory["inventory_digest"]


def test_active_skills_requires_null_execution_closure():
    entries = [directory("skill"), regular("skill/SKILL.md")]
    inventory = finalize_inventory("active-skills", LINEAGE, 1, entries)
    with pytest.raises(ManifestError):
        finalize_manifest("active-skills", LINEAGE, 1, CREATED, POLICY, entries, inventory["inventory_digest"], CLOSURE)


def test_inventory_rejects_non_utf8_path_order_and_duplicate_paths():
    with pytest.raises(ManifestError):
        finalize_inventory("runtime", LINEAGE, 1, [regular("z"), regular("a")])
    with pytest.raises(ManifestError):
        finalize_inventory("runtime", LINEAGE, 1, [regular("a"), regular("a")])


@pytest.mark.parametrize(
    "bad_entry",
    [
        {**directory("bin"), "size": 0},
        {**directory("bin"), "mode": 0o755},
        {**regular("bin/x"), "sha256": None},
        {**regular("bin/x"), "uid": 501},
        {**regular("bin/x"), "extra": None},
    ],
)
def test_inventory_rejects_invalid_entry_metadata(bad_entry):
    with pytest.raises(ManifestError):
        finalize_inventory("runtime", LINEAGE, 1, [bad_entry])


def test_runtime_execution_closure_is_closed_sorted_and_inventory_bound():
    entries = [directory("bin"), regular("bin/python", executable=True)]
    inventory = finalize_inventory("runtime", LINEAGE, 1, entries)
    with pytest.raises(ManifestError):
        finalize_manifest("runtime", LINEAGE, 1, CREATED, POLICY, entries, inventory["inventory_digest"],
                          dict(CLOSURE, extra=True))
    with pytest.raises(ManifestError, match="protected_roles"):
        finalize_manifest("runtime", LINEAGE, 1, CREATED, POLICY, entries, inventory["inventory_digest"],
                          dict(CLOSURE, protected_roles=["missing", "bin/python"]))


def test_pair_rejects_byte_different_entry_array_or_identity():
    entries = [directory("bin"), regular("bin/python", executable=True)]
    inventory = finalize_inventory("runtime", LINEAGE, 1, entries)
    manifest = finalize_manifest("runtime", LINEAGE, 1, CREATED, POLICY, entries, inventory["inventory_digest"], CLOSURE)
    forged = dict(inventory)
    forged["release_sequence"] = 2
    with pytest.raises(ManifestError):
        validate_manifest_inventory_pair(manifest, forged)
