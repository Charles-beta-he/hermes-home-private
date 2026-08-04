from __future__ import annotations

import grp
import os
import pwd
import re
import stat
import sys
from typing import Any, Callable

from .darwin_broker_worker import serve_launchd_worker_once
from .darwin_executor import DarwinExecutionPlan, DarwinLauncherExecutor
from .darwin_launchd import activate_worker_listener
from .darwin_launcher import PhysicalAncestor
from .fd_gateway import CleanMetadataAdapter


class DarwinWorkerServiceError(RuntimeError):
    pass


_RUNTIME = re.compile(
    r"^(/private/var/db/hermes-loop-a/runtime/versions/[0-9a-f]{64})/bin/python3$"
)
_ANCESTORS = ("/", "/private", "/private/var", "/private/var/db")
_ENTRYPOINT = "libexec/inner-entrypoint.py"
_ENVIRONMENT = {
    "LANG": "C",
    "LC_ALL": "C",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONHASHSEED": "0",
    "PYTHONNOUSERSITE": "1",
    "PYTHONUTF8": "1",
}


def _identity(worker_uid: int, worker_gid: int, *, euid: Callable[[], int], egid: Callable[[], int]) -> None:
    if (
        isinstance(worker_uid, bool)
        or not isinstance(worker_uid, int)
        or worker_uid <= 0
        or isinstance(worker_gid, bool)
        or not isinstance(worker_gid, int)
        or worker_gid <= 0
        or euid() != worker_uid
        or egid() != worker_gid
    ):
        raise DarwinWorkerServiceError("worker service identity is not the exact distinct UID/GID")


def build_execution_plan(
    *,
    executable: str,
    worker_uid: int,
    worker_gid: int,
    euid: Callable[[], int] = os.geteuid,
    egid: Callable[[], int] = os.getegid,
    stat_path: Callable[..., os.stat_result] = os.stat,
    metadata: CleanMetadataAdapter,
    timeout_seconds: float = 10.0,
) -> DarwinExecutionPlan:
    if not isinstance(executable, str):
        raise DarwinWorkerServiceError("worker runtime interpreter is not canonical")
    matched = _RUNTIME.fullmatch(executable)
    if matched is None:
        raise DarwinWorkerServiceError("worker runtime interpreter is not the exact digest path")
    _identity(worker_uid, worker_gid, euid=euid, egid=egid)
    if (
        isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, (int, float))
        or not 0 < timeout_seconds <= 30
    ):
        raise DarwinWorkerServiceError("worker service timeout is outside the fixed bound")

    ancestors = []
    identities = set()
    try:
        for path in _ANCESTORS:
            value = stat_path(path)
            identity = (value.st_dev, value.st_ino)
            if (
                not stat.S_ISDIR(value.st_mode)
                or value.st_uid != 0
                or value.st_gid != 0
                or identity in identities
            ):
                raise DarwinWorkerServiceError("worker physical ancestor identity is invalid")
            identities.add(identity)
            ancestors.append(
                PhysicalAncestor(
                    path=path,
                    device=value.st_dev,
                    inode=value.st_ino,
                    uid=value.st_uid,
                    gid=value.st_gid,
                    mode=stat.S_IMODE(value.st_mode),
                    flags=getattr(value, "st_flags", 0),
                )
            )
    except OSError as exc:
        raise DarwinWorkerServiceError("worker physical ancestor readback failed") from exc

    return DarwinExecutionPlan(
        version_root_path=matched.group(1),
        entrypoint_relative_path=_ENTRYPOINT,
        uid=0,
        gid=0,
        worker_uid=worker_uid,
        metadata=metadata,
        physical_ancestors=tuple(ancestors),
        mutation_root_identities=frozenset(),
        timeout_seconds=float(timeout_seconds),
    )


def run_worker_service_once(
    *,
    executable: str,
    worker_uid: int,
    worker_gid: int,
    euid: Callable[[], int] = os.geteuid,
    egid: Callable[[], int] = os.getegid,
    stat_path: Callable[..., os.stat_result] = os.stat,
    activate: Callable[[], Any] = activate_worker_listener,
    serve: Callable[..., Any] = serve_launchd_worker_once,
    executor_factory: Callable[[DarwinExecutionPlan], Any] = DarwinLauncherExecutor,
    metadata: CleanMetadataAdapter,
    timeout_seconds: float = 10.0,
) -> Any:
    plan = build_execution_plan(
        executable=executable,
        worker_uid=worker_uid,
        worker_gid=worker_gid,
        euid=euid,
        egid=egid,
        stat_path=stat_path,
        metadata=metadata,
        timeout_seconds=timeout_seconds,
    )
    executor = executor_factory(plan)
    try:
        listener = activate()
        return serve(listener=listener, executor=executor, timeout_seconds=float(timeout_seconds))
    except DarwinWorkerServiceError:
        raise
    except Exception as exc:
        raise DarwinWorkerServiceError("launchd worker service failed closed") from exc


def worker_bootstrap_bytes() -> bytes:
    environment = repr(dict(sorted(_ENVIRONMENT.items())))
    source = (
        "import os,sys\n"
        "os.environ.clear()\n"
        f"os.environ.update({environment})\n"
        "_root=os.path.dirname(os.path.dirname(sys.executable))\n"
        "sys.path.insert(0,os.path.join(_root,'libexec'))\n"
        "from loop_a_protected.darwin_worker_service import main\n"
        "raise SystemExit(main())\n"
    )
    return source.encode("ascii")


def main() -> int:
    try:
        user = pwd.getpwnam("_hermesloopa")
        group = grp.getgrnam("_hermesloopa")
    except KeyError as exc:
        raise DarwinWorkerServiceError("worker service account is absent") from exc
    if user.pw_gid != group.gr_gid:
        raise DarwinWorkerServiceError("worker service primary group differs")
    run_worker_service_once(
        executable=sys.executable,
        worker_uid=user.pw_uid,
        worker_gid=group.gr_gid,
        metadata=CleanMetadataAdapter(),
    )
    return 0
