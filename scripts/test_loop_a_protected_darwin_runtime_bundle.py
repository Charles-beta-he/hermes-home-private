from __future__ import annotations

import hashlib
import os
import tarfile
from pathlib import Path

import pytest

from loop_a_protected.manifests import validate_manifest_inventory_pair


LINEAGE = "123e4567-e89b-42d3-a456-426614174000"
CREATED = "2026-08-03T01:02:03Z"
CLOSURE = {
    "protected_roles": [],
    "external_dependencies": [],
    "platform_build": "26A123",
    "snapshot_uuid": "123e4567-e89b-42d3-a456-426614174010",
    "seal_identity": "sealed-root",
    "cryptex_generation": "cryptex-1",
    "dyld_cache_uuid": "123e4567-e89b-42d3-a456-426614174011",
    "sip_enabled": True,
}


def _compiler(output_path):
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(b"deterministic-darwin-dylib\n")
    return output


def _build(cpython, digest, package_dir, **overrides):
    from loop_a_protected.darwin_runtime_bundle import (
        build_darwin_runtime_bundle, calculate_stdlib_source_digest,
    )

    stdlib = cpython.parent / "stdlib"
    stdlib.mkdir(exist_ok=True)
    marker = stdlib / "os.py"
    if not marker.exists():
        marker.write_bytes(b"# deterministic stdlib fixture\n")
    libpython = cpython.parent / "libpython3.11.dylib"
    if not libpython.exists():
        libpython.write_bytes(b"deterministic-libpython\n")
    values = {
        "cpython_source": cpython,
        "authorized_cpython_sha256": digest,
        "stdlib_source": stdlib,
        "authorized_stdlib_digest": calculate_stdlib_source_digest(stdlib),
        "libpython_source": libpython,
        "authorized_libpython_sha256": hashlib.sha256(libpython.read_bytes()).hexdigest(),
        "package_source": package_dir,
        "release_lineage": LINEAGE,
        "release_sequence": 7,
        "created_at": CREATED,
        "policy_generation": 3,
        "execution_closure": CLOSURE,
        "native_compiler": _compiler,
    }
    values.update(overrides)
    return build_darwin_runtime_bundle(**values)


def test_builder_assembles_exact_runtime_closure_and_validated_root_owned_model(tmp_path):
    cpython = tmp_path / "python3"
    cpython.write_bytes(b"authorized-cpython\n")
    cpython.chmod(0o755)
    package = tmp_path / "loop_a_protected"
    package.mkdir()
    (package / "__init__.py").write_bytes(b'"""package"""\n')
    (package / "zeta.py").write_bytes(b"Z = 1\n")
    (package / "alpha.py").write_bytes(b"A = 1\n")
    (package / "ignored.txt").write_bytes(b"not Python\n")
    digest = hashlib.sha256(cpython.read_bytes()).hexdigest()

    bundle = _build(cpython, digest, package)

    validate_manifest_inventory_pair(bundle.manifest, bundle.inventory)
    expected_files = {
        "bin/python3",
        "lib/python3.11/os.py",
        "lib/libpython3.11.dylib",
        "libexec/inner-entrypoint.py",
        "libexec/libloop_a_darwin_spawn.dylib",
        "libexec/loop_a_protected/__init__.py",
        "libexec/loop_a_protected/alpha.py",
        "libexec/loop_a_protected/zeta.py",
        "libexec/root-broker-entrypoint.py",
        "libexec/worker-bootstrap.py",
    }
    assert set(bundle.contents) == expected_files
    assert bundle.contents["bin/python3"] == b"authorized-cpython\n"
    assert bundle.contents["libexec/worker-bootstrap.py"]
    assert bundle.contents["libexec/root-broker-entrypoint.py"]
    assert bundle.contents["libexec/inner-entrypoint.py"]
    assert bundle.contents["libexec/libloop_a_darwin_spawn.dylib"] == b"deterministic-darwin-dylib\n"
    assert bundle.manifest_bytes.endswith(b"\n")
    assert bundle.inventory_bytes.endswith(b"\n")

    paths = [entry["relative_path"] for entry in bundle.manifest["entries"]]
    assert paths == sorted(paths, key=lambda value: value.encode("utf-8"))
    assert all(entry["uid"] == 0 and entry["gid"] == 0 for entry in bundle.manifest["entries"])
    assert bundle.manifest["execution_closure"]["protected_roles"] == sorted(
        expected_files, key=lambda value: value.encode("utf-8")
    )
    assert tuple(bundle.artifact_metadata) == tuple(bundle.manifest["entries"])


def test_builder_is_byte_deterministic_and_returns_utf8_sorted_content_mapping(tmp_path):
    cpython = tmp_path / "python3"
    cpython.write_bytes(b"authorized-cpython\n")
    cpython.chmod(0o755)
    package = tmp_path / "package"
    package.mkdir()
    (package / "b.py").write_bytes(b"B = 1\n")
    (package / "a.py").write_bytes(b"A = 1\n")
    digest = hashlib.sha256(cpython.read_bytes()).hexdigest()

    first = _build(cpython, digest, package)
    (package / "a.py").touch()
    cpython.touch()
    second = _build(cpython, digest, package)

    assert tuple(first.contents) == tuple(sorted(first.contents, key=lambda value: value.encode("utf-8")))
    assert first.contents == second.contents
    assert first.inventory_bytes == second.inventory_bytes
    assert first.manifest_bytes == second.manifest_bytes


def test_builder_rejects_unauthorized_or_unstable_cpython_before_compilation(tmp_path):
    from loop_a_protected.darwin_runtime_bundle import DarwinRuntimeBundleError

    cpython = tmp_path / "python3"
    cpython.write_bytes(b"not-authorized\n")
    cpython.chmod(0o755)
    package = tmp_path / "package"
    package.mkdir()
    (package / "only.py").write_bytes(b"X = 1\n")
    calls = []

    with pytest.raises(DarwinRuntimeBundleError, match="authorized digest"):
        _build(
            cpython,
            "0" * 64,
            package,
            native_compiler=lambda output: calls.append(output),
        )
    assert calls == []


def test_builder_accepts_digest_authorized_hardlinked_cpython_source(tmp_path):
    cpython = tmp_path / "python3"
    cpython.write_bytes(b"authorized-cpython\n")
    cpython.chmod(0o755)
    cpython_hardlink = tmp_path / "python3-hardlink"
    os.link(cpython, cpython_hardlink)
    package = tmp_path / "package"
    package.mkdir()
    (package / "only.py").write_bytes(b"X = 1\n")
    digest = hashlib.sha256(cpython.read_bytes()).hexdigest()

    bundle = _build(cpython, digest, package)
    assert bundle.contents["bin/python3"] == cpython.read_bytes()


def test_builder_rejects_symlinked_package_members_and_empty_module_inventory(tmp_path):
    from loop_a_protected.darwin_runtime_bundle import DarwinRuntimeBundleError

    cpython = tmp_path / "python3"
    cpython.write_bytes(b"authorized-cpython\n")
    cpython.chmod(0o755)
    digest = hashlib.sha256(cpython.read_bytes()).hexdigest()
    package = tmp_path / "package"
    package.mkdir()
    target = tmp_path / "outside.py"
    target.write_bytes(b"outside\n")
    (package / "alias.py").symlink_to(target)

    with pytest.raises(DarwinRuntimeBundleError, match="regular no-follow"):
        _build(cpython, digest, package)

    (package / "alias.py").unlink()
    with pytest.raises(DarwinRuntimeBundleError, match="Python module"):
        _build(cpython, digest, package)


def test_builder_binds_complete_standard_library_source_tree(tmp_path):
    from loop_a_protected.darwin_runtime_bundle import DarwinRuntimeBundleError

    cpython = tmp_path / "python3"
    cpython.write_bytes(b"authorized-cpython\n")
    cpython.chmod(0o755)
    package = tmp_path / "package"
    package.mkdir()
    (package / "only.py").write_bytes(b"X = 1\n")
    digest = hashlib.sha256(cpython.read_bytes()).hexdigest()

    with pytest.raises(DarwinRuntimeBundleError, match="standard-library source differs"):
        _build(cpython, digest, package, authorized_stdlib_digest="0" * 64)
    with pytest.raises(DarwinRuntimeBundleError, match="libpython source differs"):
        _build(cpython, digest, package, authorized_libpython_sha256="0" * 64)

    stdlib = tmp_path / "stdlib"
    target = tmp_path / "outside.py"
    target.write_bytes(b"outside\n")
    (stdlib / "alias.py").symlink_to(target)
    with pytest.raises(DarwinRuntimeBundleError, match="symlink"):
        _build(cpython, digest, package)


def test_runtime_archive_is_deterministic_and_carries_root_metadata(tmp_path):
    from loop_a_protected.darwin_runtime_bundle import (
        DarwinRuntimeBundleError,
        verify_runtime_archive,
        write_deterministic_runtime_archive,
    )

    cpython = tmp_path / "python3"
    cpython.write_bytes(b"authorized-cpython\n")
    cpython.chmod(0o755)
    package = tmp_path / "package"
    package.mkdir()
    (package / "only.py").write_bytes(b"X = 1\n")
    digest = hashlib.sha256(cpython.read_bytes()).hexdigest()
    bundle = _build(cpython, digest, package)

    first, first_digest = write_deterministic_runtime_archive(bundle, tmp_path / "first.tar")
    second, second_digest = write_deterministic_runtime_archive(bundle, tmp_path / "second.tar")
    assert first_digest == second_digest
    assert first.read_bytes() == second.read_bytes()
    assert verify_runtime_archive(bundle, first, first_digest) == first_digest
    with pytest.raises(DarwinRuntimeBundleError, match="digest differs"):
        verify_runtime_archive(bundle, first, "0" * 64)

    version = bundle.manifest["version_digest"]
    with tarfile.open(first, "r") as archive:
        members = archive.getmembers()
        assert all(item.uid == 0 and item.gid == 0 and item.mtime == 0 for item in members)
        python = archive.getmember(f"runtime/versions/{version}/bin/python3")
        assert python.mode == 0o555
        extracted = archive.extractfile(python)
        assert extracted is not None
        assert extracted.read() == b"authorized-cpython\n"
        assert archive.getmember(f"metadata/runtime-{version}.manifest.json").mode == 0o444
