from __future__ import annotations

import hashlib
import os

import pytest

from loop_a_protected.canonical import canonical_bytes
from loop_a_protected.fd_gateway import CleanMetadataAdapter
from loop_a_protected.manifests import finalize_inventory, finalize_manifest


TX = "12345678-1234-5678-9234-567812345678"
LINEAGE = "123e4567-e89b-42d3-a456-426614174000"


class Metadata(CleanMetadataAdapter):
    def xattr_bytes(self, fd):
        return 0

    def has_extended_acl(self, fd):
        return False


def _replica_mutation_roots(*, mutation_root_fds, **_kwargs):
    return frozenset(
        (os.fstat(fd).st_dev, os.fstat(fd).st_ino)
        for fd in mutation_root_fds.values()
    )


def _replica_identity(**values):
    return values


def _file_entry(path, data, mode):
    return {
        "relative_path": path,
        "type": "file",
        "mode": mode,
        "uid": 0,
        "gid": 0,
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "executable": mode == 0o555,
    }


def _provision(root, module):
    uid, gid = os.getuid(), os.getgid()
    os.chmod(root, 0o755)
    for name in module.MUTATION_ROOT_ROLES:
        mode = 0o750 if name == "control" else 0o700
        if name in {"locks", "runtime", "active-skills", "authorizations", "policy"}:
            mode = 0o755
        (root / name).mkdir(mode=mode)

    runtime = b"python\n"
    entrypoint = b"print('nightly')\n"
    entries = [
        _file_entry("bin/python3", runtime, 0o555),
        _file_entry("libexec/inner-entrypoint.py", entrypoint, 0o444),
    ]
    entries.sort(key=lambda row: row["relative_path"].encode())
    inventory = finalize_inventory("runtime", LINEAGE, 1, entries)
    manifest = finalize_manifest(
        "runtime", LINEAGE, 1, "2026-08-03T01:00:00Z", 1, entries,
        inventory["inventory_digest"],
        {
            "protected_roles": ["bin/python3", "libexec/inner-entrypoint.py"],
            "external_dependencies": [],
            "platform_build": "26A123",
            "snapshot_uuid": "123e4567-e89b-42d3-a456-426614174010",
            "seal_identity": "sealed-root",
            "cryptex_generation": "cryptex-1",
            "dyld_cache_uuid": "123e4567-e89b-42d3-a456-426614174011",
            "sip_enabled": True,
        },
    )
    version = manifest["version_digest"]
    version_root = root / "runtime" / "versions" / version
    (version_root / "bin").mkdir(parents=True)
    (version_root / "libexec").mkdir()
    (version_root / "bin" / "python3").write_bytes(runtime)
    (version_root / "libexec" / "inner-entrypoint.py").write_bytes(entrypoint)
    for path in (version_root / "bin", version_root / "libexec", version_root):
        os.chmod(path, 0o555)
    os.chmod(version_root / "bin" / "python3", 0o555)
    os.chmod(version_root / "libexec" / "inner-entrypoint.py", 0o444)

    metadata_dir = root / "metadata"
    metadata_dir.mkdir(mode=0o755)
    manifest_path = metadata_dir / f"runtime-{version}.manifest.json"
    inventory_path = metadata_dir / f"runtime-{version}.inventory.json"
    manifest_path.write_bytes(canonical_bytes(manifest))
    inventory_path.write_bytes(canonical_bytes(inventory))
    os.chmod(manifest_path, 0o444)
    os.chmod(inventory_path, 0o444)

    transaction = root / "service-transactions" / TX
    for child in ("records", "sources", "candidates", "receipts"):
        (transaction / child).mkdir(parents=True, exist_ok=True)
        os.chmod(transaction / child, 0o700)
    os.chmod(transaction, 0o700)
    source = b"protected source\n"
    source_sha256 = hashlib.sha256(source).hexdigest()
    source_name = f"source-{source_sha256}.bin"
    (transaction / "sources" / source_name).write_bytes(source)
    os.chmod(transaction / "sources" / source_name, 0o400)

    request = module.finalize_nightly_request(
        transaction_uuid=TX,
        skill_name="example-skill",
        runtime_manifest_digest=version,
        runtime_inventory_digest=inventory["inventory_digest"],
        source_sha256=source_sha256,
        source_byte_count=len(source),
        worker_uid=uid + 1000,
        worker_gid=gid + 1000,
    )
    request_path = root / "service" / module.NIGHTLY_REQUEST_NAME
    request_path.write_bytes(canonical_bytes(request))
    os.chmod(request_path, 0o400)
    return request, version_root


def test_exact_root_owned_request_opens_one_held_fd_transaction(tmp_path):
    import loop_a_protected.darwin_root_broker_service as module

    request, version_root = _provision(tmp_path, module)
    root_fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    identity = (os.fstat(root_fd).st_dev, os.fstat(root_fd).st_ino)
    try:
        with module.open_nightly_transaction(
            root_fd=root_fd,
            expected_root_identity=identity,
            root_uid=os.getuid(),
            root_gid=os.getgid(),
            metadata=Metadata(),
            mutation_root_validator=_replica_mutation_roots,
            identity_factory=_replica_identity,
        ) as opened:
            assert opened.request == request
            assert opened.transaction_spec.source_sha256 == request["source_sha256"]
            assert opened.transaction_spec.runtime_manifest_digest == request["runtime_manifest_digest"]
            assert set(opened.descriptors.protected) == set(module.PROTECTED_ROLES)
            expected = os.stat(version_root)
            observed = os.fstat(opened.descriptors.protected["version-root"])
            assert (observed.st_dev, observed.st_ino) == (expected.st_dev, expected.st_ino)
            held = tuple(opened.owned_fds)
        for fd in held:
            with pytest.raises(OSError):
                os.fstat(fd)
    finally:
        os.close(root_fd)


def test_request_or_source_substitution_fails_before_returning_descriptors(tmp_path):
    import loop_a_protected.darwin_root_broker_service as module

    request, _version_root = _provision(tmp_path, module)
    source = tmp_path / "service-transactions" / TX / "sources" / f"source-{request['source_sha256']}.bin"
    os.chmod(source, 0o600)
    source.write_bytes(b"substituted\n")
    os.chmod(source, 0o400)
    root_fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    identity = (os.fstat(root_fd).st_dev, os.fstat(root_fd).st_ino)
    try:
        with pytest.raises(module.DarwinRootBrokerServiceError, match="failed closed|source|protected regular"):
            module.open_nightly_transaction(
                root_fd=root_fd,
                expected_root_identity=identity,
                root_uid=os.getuid(),
                root_gid=os.getgid(),
                metadata=Metadata(),
                mutation_root_validator=_replica_mutation_roots,
                identity_factory=_replica_identity,
            )
    finally:
        os.close(root_fd)


def test_root_broker_bootstrap_is_fixed_ascii_without_path_or_shell_fallback():
    import loop_a_protected.darwin_root_broker_service as module

    bootstrap = module.root_broker_bootstrap_bytes()
    assert bootstrap.decode("ascii")
    assert b"from loop_a_protected.darwin_root_broker_service import main" in bootstrap
    for forbidden in (b"PATH", b"PYTHONPATH", b"PYTHONHOME", b"subprocess", b"shell", b"/dev/fd"):
        assert forbidden not in bootstrap


def test_staged_binding_rejects_source_or_runtime_manifest_mismatch():
    import loop_a_protected.darwin_root_broker_service as module
    from loop_a_protected.broker_coordinator import TransactionBinding

    spec = module.RootBrokerTransaction(
        transaction_uuid=TX,
        skill_name="example-skill",
        runtime_manifest_digest="a" * 64,
        runtime_inventory_digest="b" * 64,
        source_sha256="c" * 64,
        source_byte_count=1,
    )
    binding = TransactionBinding(
        transaction_uuid=TX,
        state="CANDIDATE_STAGED",
        source_digest="d" * 64,
        runtime_manifest_digest="a" * 64,
        runtime_inventory_digest="b" * 64,
        skill_name="example-skill",
    )
    with pytest.raises(module.DarwinRootBrokerServiceError, match="exact staged"):
        module._require_exact_staged_binding(binding, spec)
