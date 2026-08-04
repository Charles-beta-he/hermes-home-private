from __future__ import annotations

import os
import socket
import subprocess
import time
from dataclasses import dataclass
from typing import Any, Callable, Protocol

from .darwin_launchd import DarwinLaunchdError, parse_launchctl_reported_pid
from .darwin_peer import validate_launchd_worker_peer


class DarwinActivationError(RuntimeError):
    pass


_LABEL = "system/com.nous.hermes-loop-a.worker"
_SOCKET_PATH = "/private/var/run/hermes-loop-a/worker.sock"
_LAUNCHCTL = "/bin/launchctl"


class _Completed(Protocol):
    returncode: int
    stdout: str


@dataclass(frozen=True)
class ActivatedWorkerSession:
    socket: socket.socket
    launchd_pid: int


def _positive_non_root(value: int) -> bool:
    return not isinstance(value, bool) and isinstance(value, int) and value > 0


def wait_for_launchd_worker_pid(
    *,
    runner: Callable[..., _Completed] = subprocess.run,
    timeout_seconds: float = 5.0,
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> int:
    if (
        isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, (int, float))
        or not 0 < timeout_seconds <= 30
    ):
        raise DarwinActivationError("launchd PID timeout is outside the fixed bound")
    deadline = monotonic() + float(timeout_seconds)
    while True:
        try:
            completed = runner(
                [_LAUNCHCTL, "print", _LABEL],
                capture_output=True,
                text=True,
                timeout=1.0,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise DarwinActivationError("launchctl PID readback failed closed") from exc
        if (
            not isinstance(getattr(completed, "returncode", None), bool)
            and isinstance(getattr(completed, "returncode", None), int)
            and completed.returncode == 0
            and isinstance(getattr(completed, "stdout", None), str)
        ):
            try:
                return parse_launchctl_reported_pid(completed.stdout)
            except DarwinLaunchdError:
                pass
        if monotonic() >= deadline:
            raise DarwinActivationError("launchd worker PID deadline expired")
        sleep(0.05)


def open_launchd_worker_session(
    *,
    worker_uid: int,
    worker_gid: int,
    socket_factory: Callable[..., socket.socket] = socket.socket,
    runner: Callable[..., _Completed] = subprocess.run,
    peer_validator: Callable[..., Any] = validate_launchd_worker_peer,
    geteuid: Callable[[], int] = os.geteuid,
    timeout_seconds: float = 5.0,
    monotonic: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> ActivatedWorkerSession:
    broker_euid = geteuid()
    if isinstance(broker_euid, bool) or broker_euid != 0:
        raise DarwinActivationError("launchd activation requires the root broker")
    if not _positive_non_root(worker_uid) or not _positive_non_root(worker_gid):
        raise DarwinActivationError("launchd worker identity must be distinct non-root UID/GID")

    connection = None
    try:
        connection = socket_factory(socket.AF_UNIX, socket.SOCK_STREAM)
        if (
            getattr(connection, "family", None) != socket.AF_UNIX
            or (getattr(connection, "type", 0) & 0xF) != socket.SOCK_STREAM
        ):
            raise DarwinActivationError("launchd activation socket is not AF_UNIX stream")
        connection.connect(_SOCKET_PATH)
        launchd_pid = wait_for_launchd_worker_pid(
            runner=runner,
            timeout_seconds=timeout_seconds,
            monotonic=monotonic,
            sleep=sleep,
        )
        peer_validator(
            connection,
            broker_euid=broker_euid,
            expected_pid=launchd_pid,
            expected_uid=worker_uid,
            expected_gid=worker_gid,
        )
        result = ActivatedWorkerSession(connection, launchd_pid)
        connection = None
        return result
    except DarwinActivationError:
        raise
    except (OSError, DarwinLaunchdError) as exc:
        raise DarwinActivationError("launchd worker activation failed closed") from exc
    finally:
        if connection is not None:
            connection.close()
