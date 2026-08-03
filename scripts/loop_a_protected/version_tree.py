from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Set, Tuple

from .canonical import canonical_bytes
from .fd_gateway import CleanMetadataAdapter, FdGatewayError, read_regular_file_at_identity
from .manifests import ManifestError, validate_manifest_inventory_pair
from .publication import (
    FaultHook,
    PublicationError,
    _emit,
    _rename_exclusive,
    _validate_directory_fd,
    publish_regular_file,
)
from .validation import ProtocolValidationError, validate_uuid


class VersionTreeError(OSError):
    pass


@dataclass(frozen=True)
class StagedVersionTree:
    temp_name: str
    device: int
    inode: int
    version_digest: str


@dataclass(frozen=True)
class PublishedVersionPair:
    version_digest: str
    manifest_name: str
    tree_device: int
    tree_inode: int


def _transaction_uuid(value: str) -> None:
    try:
        validate_uuid(value)
    except ProtocolValidationError as exc:
        raise ValueError(str(exc)) from exc


def _children(entries):
    result: Dict[str, Set[str]] = {"": set()}
    directories = {entry["relative_path"] for entry in entries if entry["type"] == "directory"}
    for directory in directories:
        result[directory] = set()
    for entry in entries:
        path = entry["relative_path"]
        parent, _, name = path.rpartition("/")
        if parent and parent not in directories:
            raise VersionTreeError(f"entry parent directory is absent: {path}")
        result[parent].add(name)
    return result


def _open_directory(parent_fd: int, name: str) -> int:
    try:
        return os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                       dir_fd=parent_fd)
    except OSError as exc:
        raise VersionTreeError(exc.errno, f"cannot open version directory {name!r}") from exc


def _verify_tree_fd(root_fd: int, manifest: Dict[str, Any], uid: int, gid: int,
                    metadata: CleanMetadataAdapter) -> Tuple[int, int]:
    root_status = os.fstat(root_fd)
    _validate_directory_fd(root_fd, root_status.st_dev, 0o555, uid, gid, metadata)
    expected_children = _children(manifest["entries"])
    entries = {entry["relative_path"]: entry for entry in manifest["entries"]}
    identities: Set[Tuple[int, int]] = {(root_status.st_dev, root_status.st_ino)}
    directory_fds: Dict[str, int] = {"": root_fd}
    owned = []
    try:
        for path, entry in entries.items():
            parent, _, name = path.rpartition("/")
            parent_fd = directory_fds[parent]
            if set(os.listdir(parent_fd)) != expected_children[parent]:
                raise VersionTreeError(f"version child set mismatch at {parent or '.'}")
            if entry["type"] == "directory":
                child_fd = _open_directory(parent_fd, name)
                owned.append(child_fd)
                status = _validate_directory_fd(child_fd, root_status.st_dev, 0o555, uid, gid, metadata)
                identity = (status.st_dev, status.st_ino)
                if identity in identities:
                    raise VersionTreeError("version tree contains an inode alias")
                identities.add(identity)
                directory_fds[path] = child_fd
            else:
                try:
                    data, identity = read_regular_file_at_identity(
                        parent_fd, name, entry["size"], entry["size"], uid, gid, entry["mode"], metadata,
                    )
                except FdGatewayError as exc:
                    raise VersionTreeError(str(exc)) from exc
                if identity in identities:
                    raise VersionTreeError("version tree contains an inode alias")
                identities.add(identity)
                if hashlib.sha256(data).hexdigest() != entry["sha256"]:
                    raise VersionTreeError(f"version file digest mismatch: {path}")
        for path, expected in expected_children.items():
            if path not in directory_fds or set(os.listdir(directory_fds[path])) != expected:
                raise VersionTreeError(f"version child set mismatch at {path or '.'}")
        return root_status.st_dev, root_status.st_ino
    finally:
        for fd in reversed(owned):
            os.close(fd)


def verify_version_tree_at(versions_parent_fd: int, name: str, manifest: Dict[str, Any],
                           uid: int, gid: int, metadata: CleanMetadataAdapter) -> Tuple[int, int]:
    root_fd = _open_directory(versions_parent_fd, name)
    try:
        parent = os.fstat(versions_parent_fd)
        root = os.fstat(root_fd)
        if root.st_dev != parent.st_dev:
            raise VersionTreeError("version root crosses versions parent device")
        return _verify_tree_fd(root_fd, manifest, uid, gid, metadata)
    except (OSError, ManifestError) as exc:
        if isinstance(exc, VersionTreeError):
            raise
        raise VersionTreeError(str(exc)) from exc
    finally:
        os.close(root_fd)


def stage_version_tree(versions_parent_fd: int, manifest: Dict[str, Any], inventory: Dict[str, Any],
                       contents: Mapping[str, bytes], uid: int, gid: int, transaction_uuid: str,
                       metadata: CleanMetadataAdapter,
                       fault_hook: Optional[FaultHook] = None) -> StagedVersionTree:
    _transaction_uuid(transaction_uuid)
    temp_name = f".tree-{transaction_uuid}.tmp"
    root_fd = -1
    directory_fds: Dict[str, int] = {}
    owned = []
    try:
        validate_manifest_inventory_pair(manifest, inventory)
        expected_files = {entry["relative_path"] for entry in manifest["entries"] if entry["type"] == "file"}
        if set(contents) != expected_files or not manifest["entries"]:
            raise VersionTreeError("version content mapping differs from manifest files")
        os.mkdir(temp_name, 0o700, dir_fd=versions_parent_fd)
        root_fd = _open_directory(versions_parent_fd, temp_name)
        directory_fds[""] = root_fd
        parent_status = os.fstat(versions_parent_fd)
        current = os.fstat(root_fd)
        if (current.st_uid, current.st_gid) != (uid, gid):
            os.fchown(root_fd, uid, gid)
        os.fchmod(root_fd, 0o700)
        _validate_directory_fd(root_fd, parent_status.st_dev, 0o700, uid, gid, metadata)
        for entry in manifest["entries"]:
            if entry["type"] != "directory":
                continue
            path = entry["relative_path"]
            parent, _, name = path.rpartition("/")
            if parent not in directory_fds:
                raise VersionTreeError(f"entry parent directory is absent: {path}")
            os.mkdir(name, 0o700, dir_fd=directory_fds[parent])
            child_fd = _open_directory(directory_fds[parent], name)
            owned.append(child_fd)
            status = os.fstat(child_fd)
            if (status.st_uid, status.st_gid) != (uid, gid):
                os.fchown(child_fd, uid, gid)
            os.fchmod(child_fd, 0o700)
            _validate_directory_fd(child_fd, parent_status.st_dev, 0o700, uid, gid, metadata)
            directory_fds[path] = child_fd
        for entry in manifest["entries"]:
            if entry["type"] != "file":
                continue
            path = entry["relative_path"]
            data = contents[path]
            if not isinstance(data, bytes) or len(data) != entry["size"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
                raise VersionTreeError(f"version content differs from manifest: {path}")
            parent, _, name = path.rpartition("/")
            publish_regular_file(directory_fds[parent], name, data, entry["mode"], uid, gid,
                                 transaction_uuid, fault_hook, metadata)
        ordered_directories = sorted(directory_fds, key=lambda path: (path.count("/"), path.encode("utf-8")), reverse=True)
        for path in ordered_directories:
            os.fsync(directory_fds[path])
        for path in ordered_directories:
            os.fchmod(directory_fds[path], 0o555)
            _validate_directory_fd(directory_fds[path], parent_status.st_dev, 0o555, uid, gid, metadata)
            os.fsync(directory_fds[path])
        device, inode = _verify_tree_fd(root_fd, manifest, uid, gid, metadata)
        os.fsync(versions_parent_fd)
        _emit(fault_hook, "after_tree_staged", temp_name=temp_name, device=device, inode=inode)
        return StagedVersionTree(temp_name, device, inode, manifest["version_digest"])
    except BaseException as exc:
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        if isinstance(exc, VersionTreeError):
            raise
        raise VersionTreeError(str(exc)) from exc
    finally:
        for fd in reversed(owned):
            os.close(fd)
        if root_fd >= 0:
            os.close(root_fd)


def publish_version_pair(versions_parent_fd: int, manifests_parent_fd: int, staged: StagedVersionTree,
                         manifest: Dict[str, Any], inventory: Dict[str, Any], uid: int, gid: int,
                         transaction_uuid: str, metadata: CleanMetadataAdapter,
                         fault_hook: Optional[FaultHook] = None) -> PublishedVersionPair:
    _transaction_uuid(transaction_uuid)
    root_fd = -1
    try:
        validate_manifest_inventory_pair(manifest, inventory)
        digest = manifest["version_digest"]
        if staged.version_digest != digest:
            raise VersionTreeError("staged tree digest binding differs from manifest")
        root_fd = _open_directory(versions_parent_fd, staged.temp_name)
        held = os.fstat(root_fd)
        if (held.st_dev, held.st_ino) != (staged.device, staged.inode):
            raise VersionTreeError("staged tree inode binding mismatch")
        _verify_tree_fd(root_fd, manifest, uid, gid, metadata)
        manifest_name = f"{digest}.json"
        publish_regular_file(manifests_parent_fd, manifest_name, canonical_bytes(manifest), 0o444,
                             uid, gid, transaction_uuid, fault_hook, metadata)
        _emit(fault_hook, "after_manifest_publication", manifest_name=manifest_name)
        _rename_exclusive(versions_parent_fd, staged.temp_name, digest)
        named = os.stat(digest, dir_fd=versions_parent_fd, follow_symlinks=False)
        if (named.st_dev, named.st_ino) != (held.st_dev, held.st_ino):
            raise VersionTreeError("published tree identity readback mismatch")
        _verify_tree_fd(root_fd, manifest, uid, gid, metadata)
        os.fsync(versions_parent_fd)
        os.fsync(manifests_parent_fd)
        _emit(fault_hook, "after_tree_publication", final_name=digest)
        return PublishedVersionPair(digest, manifest_name, held.st_dev, held.st_ino)
    except BaseException as exc:
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        if isinstance(exc, VersionTreeError):
            raise
        if isinstance(exc, PublicationError):
            raise VersionTreeError("version manifest publication failed") from exc
        raise VersionTreeError(str(exc)) from exc
    finally:
        if root_fd >= 0:
            os.close(root_fd)
