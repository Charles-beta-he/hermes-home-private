from __future__ import annotations

import hashlib
import os
import select
import signal
import stat
import time
from dataclasses import dataclass
from typing import Any, Dict, FrozenSet, Mapping, Sequence, Tuple

from .canonical import CanonicalJSONError, parse_canonical_bytes
from .darwin_broker_worker import WorkerExecution
from .darwin_launchd_transport import PROTECTED_ROLES, ReceivedFdBundle
from .darwin_launcher import (
    PhysicalAncestor,
    spawn_pending_handshake_after_adjacent_executable,
)
from .fd_gateway import CleanMetadataAdapter
from .manifests import ManifestError, validate_manifest_inventory_pair


class DarwinExecutorError(RuntimeError):
    pass


_MAX_INPUT = 8_388_608
_MAX_CANDIDATE = 8_388_608
_MAX_DIAGNOSTICS = 65_536
_FIXED_INTERPRETER_ENTRY = "bin/python3"


@dataclass(frozen=True)
class DarwinExecutionPlan:
    version_root_path: str
    entrypoint_relative_path: str
    uid: int
    gid: int
    worker_uid: int
    metadata: CleanMetadataAdapter
    physical_ancestors: Sequence[PhysicalAncestor]
    mutation_root_identities: FrozenSet[Tuple[int, int]]
    timeout_seconds: float = 10.0


def _stable_status(value: os.stat_result) -> Tuple[int, ...]:
    return (
        value.st_dev, value.st_ino, value.st_mode, value.st_uid, value.st_gid,
        value.st_nlink, value.st_size, value.st_mtime_ns, value.st_ctime_ns,
        getattr(value, "st_flags", 0),
    )


def _read_stable_regular(fd: int, *, limit: int, label: str) -> bytes:
    before = os.fstat(fd)
    if (not stat.S_ISREG(before.st_mode) or before.st_size < 1 or before.st_size > limit):
        raise DarwinExecutorError(f"{label} is not one bounded regular file")
    chunks = bytearray()
    offset = 0
    while offset <= before.st_size:
        chunk = os.pread(fd, min(131072, before.st_size + 1 - offset), offset)
        if not chunk:
            break
        chunks.extend(chunk)
        offset += len(chunk)
        if len(chunks) > before.st_size:
            raise DarwinExecutorError(f"{label} grew during held-FD read")
    after = os.fstat(fd)
    if _stable_status(before) != _stable_status(after) or len(chunks) != before.st_size:
        raise DarwinExecutorError(f"{label} changed during held-FD read")
    return bytes(chunks)


def _parse_record(data: bytes, *, label: str) -> Dict[str, Any]:
    try:
        value = parse_canonical_bytes(data)
    except CanonicalJSONError as exc:
        raise DarwinExecutorError(f"{label} is not canonical JSON") from exc
    if not isinstance(value, dict):
        raise DarwinExecutorError(f"{label} is not an object")
    return value


def _file_entry(inventory: Mapping[str, Any], relative_path: str) -> Mapping[str, Any]:
    entries = inventory.get("entries")
    if not isinstance(entries, list):
        raise DarwinExecutorError("runtime inventory entries are invalid")
    matches = [item for item in entries if isinstance(item, dict) and item.get("relative_path") == relative_path]
    if len(matches) != 1 or matches[0].get("type") != "file":
        raise DarwinExecutorError(f"runtime inventory does not contain exact file: {relative_path}")
    return matches[0]


def _verify_file_descriptor(fd: int, entry: Mapping[str, Any], data: bytes, *, label: str) -> None:
    status = os.fstat(fd)
    expected_mode = entry.get("mode")
    expected_size = entry.get("size")
    expected_digest = entry.get("sha256")
    if (
        status.st_uid != entry.get("uid")
        or status.st_gid != entry.get("gid")
        or stat.S_IMODE(status.st_mode) != expected_mode
        or len(data) != expected_size
        or hashlib.sha256(data).hexdigest() != expected_digest
    ):
        raise DarwinExecutorError(f"{label} descriptor differs from runtime inventory")


def _write_all(fd: int, data: bytes) -> None:
    view = memoryview(data)
    while view:
        written = os.write(fd, view)
        if written <= 0:
            raise DarwinExecutorError("entrypoint pipe write was short")
        view = view[written:]


def _drain_child(stdout_fd: int, diagnostics_fd: int, *, deadline: float) -> bytes:
    streams = {stdout_fd: bytearray(), diagnostics_fd: bytearray()}
    limits = {stdout_fd: _MAX_CANDIDATE, diagnostics_fd: _MAX_DIAGNOSTICS}
    open_fds = set(streams)
    while open_fds:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise DarwinExecutorError("inner child output deadline expired")
        ready, _, _ = select.select(sorted(open_fds), [], [], remaining)
        if not ready:
            raise DarwinExecutorError("inner child output deadline expired")
        for fd in ready:
            chunk = os.read(fd, 131072)
            if not chunk:
                open_fds.remove(fd)
                continue
            streams[fd].extend(chunk)
            if len(streams[fd]) > limits[fd]:
                raise DarwinExecutorError("inner child output exceeded its fixed bound")
    candidate = bytes(streams[stdout_fd])
    if not candidate:
        raise DarwinExecutorError("inner child produced an empty candidate")
    return candidate


def _kill_and_reap(pid: int) -> None:
    if pid <= 0:
        return
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    try:
        os.waitpid(pid, 0)
    except ChildProcessError:
        pass


def _wait_success(pid: int, *, deadline: float) -> None:
    while True:
        waited, status = os.waitpid(pid, os.WNOHANG)
        if waited == pid:
            if not os.WIFEXITED(status) or os.WEXITSTATUS(status) != 0:
                raise DarwinExecutorError("inner child exited unsuccessfully")
            return
        if time.monotonic() >= deadline:
            raise DarwinExecutorError("inner child exit deadline expired")
        time.sleep(0.01)


class DarwinLauncherExecutor:
    """Convert the exact six read-only outer inputs into the fixed ten-FD child contract."""

    def __init__(self, plan: DarwinExecutionPlan) -> None:
        self.plan = plan

    def execute(self, bundle: ReceivedFdBundle) -> WorkerExecution:
        if tuple(bundle.descriptors) != PROTECTED_ROLES:
            raise DarwinExecutorError("outer worker descriptor order is not exact")
        if (
            isinstance(self.plan.timeout_seconds, bool)
            or not isinstance(self.plan.timeout_seconds, (int, float))
            or not 0 < self.plan.timeout_seconds <= 30
        ):
            raise DarwinExecutorError("executor timeout is outside the fixed bound")
        descriptors = bundle.descriptors
        manifest_bytes = _read_stable_regular(
            descriptors["runtime-manifest"], limit=_MAX_INPUT, label="runtime manifest"
        )
        inventory_bytes = _read_stable_regular(
            descriptors["runtime-inventory"], limit=_MAX_INPUT, label="runtime inventory"
        )
        source_bytes = _read_stable_regular(descriptors["source"], limit=_MAX_INPUT, label="source")
        entrypoint_bytes = _read_stable_regular(
            descriptors["entrypoint"], limit=_MAX_INPUT, label="entrypoint"
        )
        executable_bytes = _read_stable_regular(
            descriptors["retained-executable"], limit=536_870_912, label="retained executable"
        )
        manifest = _parse_record(manifest_bytes, label="runtime manifest")
        inventory = _parse_record(inventory_bytes, label="runtime inventory")
        try:
            validate_manifest_inventory_pair(manifest, inventory)
        except ManifestError as exc:
            raise DarwinExecutorError("runtime manifest/inventory pair is invalid") from exc
        if manifest.get("kind") != "runtime":
            raise DarwinExecutorError("worker runtime manifest kind is invalid")
        entrypoint_entry = _file_entry(inventory, self.plan.entrypoint_relative_path)
        executable_entry = _file_entry(inventory, _FIXED_INTERPRETER_ENTRY)
        _verify_file_descriptor(
            descriptors["entrypoint"], entrypoint_entry, entrypoint_bytes, label="entrypoint"
        )
        _verify_file_descriptor(
            descriptors["retained-executable"], executable_entry, executable_bytes,
            label="retained executable",
        )
        protected_roles = manifest.get("execution_closure", {}).get("protected_roles")
        if (
            not isinstance(protected_roles, list)
            or self.plan.entrypoint_relative_path not in protected_roles
            or _FIXED_INTERPRETER_ENTRY not in protected_roles
        ):
            raise DarwinExecutorError("runtime execution closure omits launcher inputs")

        entry_read = entry_write = result_read = result_write = diagnostics_read = diagnostics_write = -1
        pending = None
        child_pid = -1
        executor_owns_child = False
        deadline = time.monotonic() + float(self.plan.timeout_seconds)
        try:
            entry_read, entry_write = os.pipe()
            result_read, result_write = os.pipe()
            diagnostics_read, diagnostics_write = os.pipe()
            for fd in (entry_read, entry_write, result_read, result_write, diagnostics_read, diagnostics_write):
                os.set_inheritable(fd, False)
            pending = spawn_pending_handshake_after_adjacent_executable(
                canonical_interpreter_path=os.path.join(self.plan.version_root_path, _FIXED_INTERPRETER_ENTRY),
                version_root_fd=descriptors["version-root"],
                retained_executable_fd=descriptors["retained-executable"],
                version_root_path=self.plan.version_root_path,
                expected_executable_size=len(executable_bytes),
                expected_executable_sha256=hashlib.sha256(executable_bytes).hexdigest(),
                uid=self.plan.uid,
                gid=self.plan.gid,
                metadata=self.plan.metadata,
                worker_uid=self.plan.worker_uid,
                entrypoint_fd=entry_read,
                result_fd=result_write,
                diagnostics_fd=diagnostics_write,
                manifest_fd=descriptors["runtime-manifest"],
                inventory_fd=descriptors["runtime-inventory"],
                source_fd=descriptors["source"],
                entrypoint_sha256=hashlib.sha256(entrypoint_bytes).hexdigest(),
                manifest_digest=manifest["version_digest"],
                inventory_digest=inventory["inventory_digest"],
                source_digest=hashlib.sha256(source_bytes).hexdigest(),
                physical_ancestors=self.plan.physical_ancestors,
                mutation_root_identities=self.plan.mutation_root_identities,
                timeout_seconds=min(self.plan.timeout_seconds, 5.0),
                challenge_nonce=bytes.fromhex(bundle.nonce),
            )
            child_pid = pending.pid
            executor_owns_child = True
            for fd_name in ("entry_read", "result_write", "diagnostics_write"):
                fd = locals()[fd_name]
                os.close(fd)
                if fd_name == "entry_read":
                    entry_read = -1
                elif fd_name == "result_write":
                    result_write = -1
                else:
                    diagnostics_write = -1
            _write_all(entry_write, entrypoint_bytes)
            os.close(entry_write)
            entry_write = -1
            try:
                ack = pending.handshake.complete()
            except BaseException as exc:
                if getattr(exc, "child_reaped", False):
                    child_pid = -1
                    executor_owns_child = False
                raise
            candidate = _drain_child(result_read, diagnostics_read, deadline=deadline)
            _wait_success(child_pid, deadline=deadline)
            child_pid = -1
            executor_owns_child = False
            return WorkerExecution(
                child_pid=pending.pid,
                handshake_ack=ack,
                source_digest=hashlib.sha256(source_bytes).hexdigest(),
                runtime_manifest_digest=manifest["version_digest"],
                runtime_inventory_digest=inventory["inventory_digest"],
                candidate_bytes=candidate,
            )
        except DarwinExecutorError:
            raise
        except Exception as exc:
            raise DarwinExecutorError("inner child execution failed closed") from exc
        finally:
            if executor_owns_child and child_pid > 0:
                _kill_and_reap(child_pid)
            for fd in (entry_read, entry_write, result_read, result_write, diagnostics_read, diagnostics_write):
                if fd >= 0:
                    try:
                        os.close(fd)
                    except OSError:
                        pass
