from __future__ import annotations

import hashlib
import io
import os
import stat
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Dict, Mapping, Sequence, Tuple, Union

from .canonical import canonical_bytes
from .darwin_native_spawn import compile_native_library
from .darwin_root_broker_service import root_broker_bootstrap_bytes
from .darwin_worker_service import worker_bootstrap_bytes
from .manifests import finalize_inventory, finalize_manifest, validate_manifest_inventory_pair
from .validation import ProtocolValidationError, validate_digest


class DarwinRuntimeBundleError(ValueError):
    """The requested Darwin runtime closure cannot be built without weakening its model."""


@dataclass(frozen=True)
class DarwinRuntimeBundle:
    manifest: Dict[str, Any]
    inventory: Dict[str, Any]
    contents: Mapping[str, bytes]
    artifact_metadata: Tuple[Dict[str, Any], ...]

    @property
    def manifest_bytes(self) -> bytes:
        return canonical_bytes(self.manifest)

    @property
    def inventory_bytes(self) -> bytes:
        return canonical_bytes(self.inventory)


NativeCompiler = Callable[[Union[os.PathLike[str], str]], Path]
_PACKAGE_SOURCE = Path(__file__).parent
_INNER_ENTRYPOINT_SOURCE = _PACKAGE_SOURCE / "inner_entrypoint.py"


def _stable_regular_bytes(
    path: Path,
    *,
    label: str,
    require_executable: bool = False,
    require_single_link: bool = True,
) -> bytes:
    fd = -1
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or (require_single_link and before.st_nlink != 1):
            raise DarwinRuntimeBundleError(f"{label} must be one regular no-follow file")
        if require_executable and stat.S_IMODE(before.st_mode) & 0o111 == 0:
            raise DarwinRuntimeBundleError(f"{label} must be executable")
        chunks = bytearray()
        offset = 0
        while offset <= before.st_size:
            chunk = os.pread(fd, min(131072, before.st_size + 1 - offset), offset)
            if not chunk:
                break
            chunks.extend(chunk)
            offset += len(chunk)
            if len(chunks) > before.st_size:
                raise DarwinRuntimeBundleError(f"{label} changed during read")
        after = os.fstat(fd)
        identity = lambda value: (
            value.st_dev,
            value.st_ino,
            value.st_mode,
            value.st_uid,
            value.st_gid,
            value.st_nlink,
            value.st_size,
            value.st_mtime_ns,
            value.st_ctime_ns,
            getattr(value, "st_flags", 0),
        )
        if identity(before) != identity(after) or len(chunks) != before.st_size:
            raise DarwinRuntimeBundleError(f"{label} changed during read")
        return bytes(chunks)
    except DarwinRuntimeBundleError:
        raise
    except OSError as exc:
        raise DarwinRuntimeBundleError(f"{label} must be one regular no-follow file") from exc
    finally:
        if fd >= 0:
            os.close(fd)


def _python_modules(package_source: Path) -> Dict[str, bytes]:
    directory_fd = -1
    try:
        directory_fd = os.open(package_source, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        names = sorted(
            (name for name in os.listdir(directory_fd) if name.endswith(".py")),
            key=lambda value: value.encode("utf-8"),
        )
        if not names:
            raise DarwinRuntimeBundleError("runtime package contains no Python module")
        modules: Dict[str, bytes] = {}
        for name in names:
            modules[f"libexec/loop_a_protected/{name}"] = _stable_regular_bytes(
                package_source / name, label=f"Python module {name}"
            )
        return modules
    except DarwinRuntimeBundleError:
        raise
    except OSError as exc:
        raise DarwinRuntimeBundleError("runtime package source must be one no-follow directory") from exc
    finally:
        if directory_fd >= 0:
            os.close(directory_fd)


def _file_entry(relative_path: str, data: bytes, *, executable: bool) -> Dict[str, Any]:
    return {
        "relative_path": relative_path,
        "type": "file",
        "mode": 0o555 if executable else 0o444,
        "uid": 0,
        "gid": 0,
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "executable": executable,
    }


def _directory_entry(relative_path: str) -> Dict[str, Any]:
    return {
        "relative_path": relative_path,
        "type": "directory",
        "mode": 0o555,
        "uid": 0,
        "gid": 0,
        "size": None,
        "sha256": None,
        "executable": False,
    }


def _source_tree(
    source_root: Path, *, destination_root: str, excluded_components: Sequence[str]
) -> Tuple[Dict[str, bytes], Tuple[str, ...]]:
    if not source_root.is_absolute():
        raise DarwinRuntimeBundleError("standard-library source path must be absolute")
    try:
        root_stat = os.lstat(source_root)
    except OSError as exc:
        raise DarwinRuntimeBundleError("standard-library source is unavailable") from exc
    if not stat.S_ISDIR(root_stat.st_mode) or stat.S_ISLNK(root_stat.st_mode):
        raise DarwinRuntimeBundleError("standard-library source must be one no-follow directory")
    excluded = frozenset(excluded_components)
    contents: Dict[str, bytes] = {}
    directories = {destination_root}
    for current, dirnames, filenames in os.walk(source_root, topdown=True, followlinks=False):
        current_path = Path(current)
        relative = current_path.relative_to(source_root)
        kept_dirs = []
        for name in sorted(dirnames, key=lambda value: value.encode("utf-8")):
            child = current_path / name
            value = os.lstat(child)
            if stat.S_ISLNK(value.st_mode):
                raise DarwinRuntimeBundleError("standard-library source contains a symlink")
            if name in excluded or not stat.S_ISDIR(value.st_mode):
                continue
            kept_dirs.append(name)
            destination = Path(destination_root) / relative / name
            directories.add(destination.as_posix())
        dirnames[:] = kept_dirs
        for name in sorted(filenames, key=lambda value: value.encode("utf-8")):
            if name.endswith((".pyc", ".pyo")):
                continue
            source = current_path / name
            value = os.lstat(source)
            if stat.S_ISLNK(value.st_mode):
                raise DarwinRuntimeBundleError("standard-library source contains a symlink")
            if not stat.S_ISREG(value.st_mode):
                raise DarwinRuntimeBundleError("standard-library source contains a non-regular file")
            destination = (Path(destination_root) / relative / name).as_posix()
            contents[destination] = _stable_regular_bytes(
                source, label=f"standard-library file {source.relative_to(source_root)}"
            )
    if not contents:
        raise DarwinRuntimeBundleError("standard-library source contains no runtime files")
    return contents, tuple(sorted(directories, key=lambda value: value.encode("utf-8")))


def source_tree_digest(contents: Mapping[str, bytes]) -> str:
    records = [
        {"relative_path": path, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        for path, data in sorted(contents.items(), key=lambda item: item[0].encode("utf-8"))
    ]
    return hashlib.sha256(canonical_bytes({"schema": 1, "files": records})).hexdigest()


def calculate_stdlib_source_digest(source_root: os.PathLike[str] | str) -> str:
    contents, _ = _source_tree(
        Path(source_root),
        destination_root="lib/python3.11",
        excluded_components=("__pycache__", "site-packages"),
    )
    return source_tree_digest(contents)


def build_darwin_runtime_bundle(
    *,
    cpython_source: os.PathLike[str] | str,
    authorized_cpython_sha256: str,
    stdlib_source: os.PathLike[str] | str,
    authorized_stdlib_digest: str,
    libpython_source: os.PathLike[str] | str,
    authorized_libpython_sha256: str,
    release_lineage: str,
    release_sequence: int,
    created_at: str,
    policy_generation: int,
    execution_closure: Mapping[str, Any],
    package_source: os.PathLike[str] | str = _PACKAGE_SOURCE,
    inner_entrypoint_source: os.PathLike[str] | str = _INNER_ENTRYPOINT_SOURCE,
    native_compiler: NativeCompiler = compile_native_library,
) -> DarwinRuntimeBundle:
    """Build an in-memory, manifest-bound Darwin runtime candidate.

    The only filesystem writes are compiler scratch files in a private temporary
    directory. No protected/runtime/root path is created, changed, or published.
    Ownership and modes in the returned entries are the installation model, not
    claims about the invoking process or scratch files.
    """
    source = Path(cpython_source)
    if not source.is_absolute():
        raise DarwinRuntimeBundleError("authorized CPython source path must be absolute")
    try:
        expected_digest = validate_digest(authorized_cpython_sha256)
    except ProtocolValidationError as exc:
        raise DarwinRuntimeBundleError("authorized CPython digest is invalid") from exc
    python_bytes = _stable_regular_bytes(
        source, label="authorized CPython source", require_executable=True, require_single_link=False
    )
    if hashlib.sha256(python_bytes).hexdigest() != expected_digest:
        raise DarwinRuntimeBundleError("CPython source differs from authorized digest")
    stdlib_contents, stdlib_directories = _source_tree(
        Path(stdlib_source),
        destination_root="lib/python3.11",
        excluded_components=("__pycache__", "site-packages"),
    )
    try:
        expected_stdlib_digest = validate_digest(authorized_stdlib_digest)
    except ProtocolValidationError as exc:
        raise DarwinRuntimeBundleError("authorized standard-library digest is invalid") from exc
    if source_tree_digest(stdlib_contents) != expected_stdlib_digest:
        raise DarwinRuntimeBundleError("standard-library source differs from authorized digest")
    libpython = Path(libpython_source)
    if not libpython.is_absolute():
        raise DarwinRuntimeBundleError("libpython source path must be absolute")
    try:
        expected_libpython_digest = validate_digest(authorized_libpython_sha256)
    except ProtocolValidationError as exc:
        raise DarwinRuntimeBundleError("authorized libpython digest is invalid") from exc
    libpython_bytes = _stable_regular_bytes(
        libpython, label="authorized libpython source", require_single_link=False
    )
    if hashlib.sha256(libpython_bytes).hexdigest() != expected_libpython_digest:
        raise DarwinRuntimeBundleError("libpython source differs from authorized digest")

    modules = _python_modules(Path(package_source))
    entrypoint_bytes = _stable_regular_bytes(
        Path(inner_entrypoint_source), label="inner entrypoint source"
    )
    try:
        bootstrap_bytes = worker_bootstrap_bytes()
        broker_bootstrap_bytes = root_broker_bootstrap_bytes()
    except Exception as exc:
        raise DarwinRuntimeBundleError("service bootstrap generation failed") from exc
    if not isinstance(bootstrap_bytes, bytes) or not bootstrap_bytes:
        raise DarwinRuntimeBundleError("worker bootstrap generation returned no bytes")
    if not isinstance(broker_bootstrap_bytes, bytes) or not broker_bootstrap_bytes:
        raise DarwinRuntimeBundleError("root broker bootstrap generation returned no bytes")

    with tempfile.TemporaryDirectory(prefix="loop-a-darwin-runtime-") as scratch:
        output = Path(scratch) / "libloop_a_darwin_spawn.dylib"
        try:
            compiled = Path(native_compiler(output))
        except Exception as exc:
            raise DarwinRuntimeBundleError("Darwin native adapter compilation failed") from exc
        if compiled != output:
            raise DarwinRuntimeBundleError("Darwin native compiler returned an unexpected artifact path")
        dylib_bytes = _stable_regular_bytes(output, label="compiled Darwin native adapter")
    if not dylib_bytes:
        raise DarwinRuntimeBundleError("compiled Darwin native adapter is empty")

    raw_contents: Dict[str, bytes] = {
        "bin/python3": python_bytes,
        "lib/libpython3.11.dylib": libpython_bytes,
        "libexec/inner-entrypoint.py": entrypoint_bytes,
        "libexec/libloop_a_darwin_spawn.dylib": dylib_bytes,
        "libexec/root-broker-entrypoint.py": broker_bootstrap_bytes,
        "libexec/worker-bootstrap.py": bootstrap_bytes,
        **stdlib_contents,
        **modules,
    }
    contents = {
        path: raw_contents[path]
        for path in sorted(raw_contents, key=lambda value: value.encode("utf-8"))
    }
    entries = [
        _directory_entry("bin"),
        _directory_entry("lib"),
        *(_directory_entry(path) for path in stdlib_directories),
        _directory_entry("libexec"),
        _directory_entry("libexec/loop_a_protected"),
        *(
            _file_entry(path, data, executable=(path == "bin/python3"))
            for path, data in contents.items()
        ),
    ]
    entries.sort(key=lambda entry: entry["relative_path"].encode("utf-8"))

    closure = dict(execution_closure)
    closure["protected_roles"] = list(contents)
    inventory = finalize_inventory("runtime", release_lineage, release_sequence, entries)
    manifest = finalize_manifest(
        "runtime",
        release_lineage,
        release_sequence,
        created_at,
        policy_generation,
        entries,
        inventory["inventory_digest"],
        closure,
    )
    validate_manifest_inventory_pair(manifest, inventory)
    return DarwinRuntimeBundle(
        manifest=manifest,
        inventory=inventory,
        contents=MappingProxyType(contents),
        artifact_metadata=tuple(dict(entry) for entry in entries),
    )


def verify_runtime_archive(
    bundle: DarwinRuntimeBundle,
    archive_path: os.PathLike[str] | str,
    expected_sha256: str,
) -> str:
    try:
        expected = validate_digest(expected_sha256)
    except ProtocolValidationError as exc:
        raise DarwinRuntimeBundleError("runtime archive expected digest is invalid") from exc
    archive_file = Path(archive_path)
    data = _stable_regular_bytes(archive_file, label="runtime archive", require_single_link=True)
    observed = hashlib.sha256(data).hexdigest()
    if observed != expected:
        raise DarwinRuntimeBundleError("runtime archive digest differs")
    version_value = bundle.manifest.get("version_digest")
    if not isinstance(version_value, str):
        raise DarwinRuntimeBundleError("runtime archive manifest digest is invalid")
    version = validate_digest(version_value)
    expected_members: Dict[str, Tuple[str, int, bytes | None]] = {}
    prefix = f"runtime/versions/{version}"
    for entry in bundle.inventory["entries"]:
        relative = entry["relative_path"]
        content = None if entry["type"] == "directory" else bundle.contents[relative]
        archive_name = f"{prefix}/{relative}"
        expected_members[archive_name] = (entry["type"], entry["mode"], content)
    expected_members[f"metadata/runtime-{version}.manifest.json"] = (
        "file", 0o444, bundle.manifest_bytes
    )
    expected_members[f"metadata/runtime-{version}.inventory.json"] = (
        "file", 0o444, bundle.inventory_bytes
    )
    with tarfile.open(archive_file, "r") as archive:
        members = archive.getmembers()
        names = [item.name.rstrip("/") if item.isdir() else item.name for item in members]
        if len(names) != len(set(names)) or set(names) != set(expected_members):
            raise DarwinRuntimeBundleError("runtime archive member set differs")
        for member, canonical_name in zip(members, names):
            expected_type, expected_mode, expected_content = expected_members[canonical_name]
            if (
                member.uid != 0
                or member.gid != 0
                or member.uname != "root"
                or member.gname != "wheel"
                or member.mtime != 0
                or member.mode != expected_mode
                or (expected_type == "directory" and not member.isdir())
                or (expected_type == "file" and not member.isfile())
            ):
                raise DarwinRuntimeBundleError("runtime archive member metadata differs")
            if expected_content is not None:
                if member.size != len(expected_content):
                    raise DarwinRuntimeBundleError("runtime archive member size differs")
                extracted = archive.extractfile(member)
                if extracted is None or extracted.read(len(expected_content) + 1) != expected_content:
                    raise DarwinRuntimeBundleError("runtime archive member content differs")
    return observed


def write_deterministic_runtime_archive(
    bundle: DarwinRuntimeBundle, output_path: os.PathLike[str] | str
) -> Tuple[Path, str]:
    """Write a root-metadata deterministic tar without mutating a protected root."""
    if not isinstance(bundle, DarwinRuntimeBundle):
        raise DarwinRuntimeBundleError("runtime archive requires a validated bundle")
    output = Path(output_path)
    if not output.is_absolute():
        raise DarwinRuntimeBundleError("runtime archive output path must be absolute")
    version_value = bundle.manifest.get("version_digest")
    if not isinstance(version_value, str):
        raise DarwinRuntimeBundleError("runtime archive manifest digest is invalid")
    try:
        version = validate_digest(version_value)
    except ProtocolValidationError as exc:
        raise DarwinRuntimeBundleError("runtime archive manifest digest is invalid") from exc
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.{os.getpid()}.tmp")
    try:
        with tarfile.open(temporary, "w", format=tarfile.GNU_FORMAT) as archive:
            prefix = f"runtime/versions/{version}"
            entries = bundle.inventory["entries"]
            for entry in entries:
                relative = entry["relative_path"]
                archive_name = f"{prefix}/{relative}"
                if entry["type"] == "directory":
                    archive_name += "/"
                info = tarfile.TarInfo(archive_name)
                info.uid = 0
                info.gid = 0
                info.uname = "root"
                info.gname = "wheel"
                info.mtime = 0
                info.mode = entry["mode"]
                if entry["type"] == "directory":
                    info.type = tarfile.DIRTYPE
                    archive.addfile(info)
                else:
                    data = bundle.contents[relative]
                    info.type = tarfile.REGTYPE
                    info.size = len(data)
                    archive.addfile(info, io.BytesIO(data))
            for name, data in (
                (f"metadata/runtime-{version}.manifest.json", bundle.manifest_bytes),
                (f"metadata/runtime-{version}.inventory.json", bundle.inventory_bytes),
            ):
                info = tarfile.TarInfo(name)
                info.uid = 0
                info.gid = 0
                info.uname = "root"
                info.gname = "wheel"
                info.mtime = 0
                info.mode = 0o444
                info.type = tarfile.REGTYPE
                info.size = len(data)
                archive.addfile(info, io.BytesIO(data))
        with temporary.open("rb") as handle:
            os.fsync(handle.fileno())
        os.replace(temporary, output)
        directory_fd = os.open(output.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        data = _stable_regular_bytes(output, label="runtime archive", require_single_link=True)
        digest = hashlib.sha256(data).hexdigest()
        verify_runtime_archive(bundle, output, digest)
        return output, digest
    except Exception:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise


# Concise compatibility alias for callers that already select the Darwin builder module.
build_runtime_bundle = build_darwin_runtime_bundle
