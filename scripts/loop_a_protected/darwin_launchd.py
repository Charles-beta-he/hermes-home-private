from __future__ import annotations

import ctypes
import os
import plistlib
import re
import socket
import sys
from typing import Any, Mapping


class DarwinLaunchdError(RuntimeError):
    pass


_LABEL = "com.nous.hermes-loop-a.worker"
_SOCKET_NAME = "Broker"
_SOCKET_PATH = "/private/var/run/hermes-loop-a/worker.sock"
_EXACT_ENVIRONMENT = {
    "LANG": "C",
    "LC_ALL": "C",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONHASHSEED": "0",
    "PYTHONNOUSERSITE": "1",
    "PYTHONUTF8": "1",
}


def build_worker_plist(*, interpreter_path: str, entrypoint_path: str,
                       worker_user: str = "_hermesloopa",
                       worker_group: str = "_hermesloopa") -> dict[str, Any]:
    prefix = "/private/var/db/hermes-loop-a/runtime/versions/"
    suffix = "/bin/python3"
    if (not isinstance(interpreter_path, str) or not interpreter_path.startswith(prefix)
            or not interpreter_path.endswith(suffix)
            or re.fullmatch(r"[0-9a-f]{64}", interpreter_path[len(prefix):-len(suffix)]) is None):
        raise DarwinLaunchdError("launchd interpreter path is not an exact digest version")
    version_root = interpreter_path[:-len(suffix)]
    if (not isinstance(entrypoint_path, str)
            or not entrypoint_path.startswith(version_root + "/")
            or "/../" in entrypoint_path or "//" in entrypoint_path
            or entrypoint_path.endswith("/")):
        raise DarwinLaunchdError("launchd entrypoint path is not canonical protected form")
    if not worker_user or not worker_group:
        raise DarwinLaunchdError("launchd worker identity is empty")
    return {
        "Label": _LABEL,
        "ProgramArguments": [interpreter_path, "-I", "-S", "-B", "-"],
        "StandardInPath": entrypoint_path,
        "StandardOutPath": "/dev/null",
        "StandardErrorPath": "/dev/null",
        "UserName": worker_user,
        "GroupName": worker_group,
        "EnvironmentVariables": dict(_EXACT_ENVIRONMENT),
        "ProcessType": "Background",
        "RunAtLoad": False,
        "KeepAlive": False,
        "Umask": 0o077,
        "Sockets": {
            _SOCKET_NAME: {
                "SockPathName": _SOCKET_PATH,
                "SockPathMode": 0o600,
                "SockPathOwner": 0,
                "SockPathGroup": 0,
                "SockFamily": "Unix",
                "SockType": "stream",
                "SockPassive": True,
            },
        },
    }


def serialize_worker_plist(value: Mapping[str, Any]) -> bytes:
    if not isinstance(value, Mapping):
        raise DarwinLaunchdError("launchd worker plist is not a mapping")
    arguments = value.get("ProgramArguments")
    interpreter = arguments[0] if isinstance(arguments, list) and arguments else ""
    entrypoint = value.get("StandardInPath")
    worker_user = value.get("UserName")
    worker_group = value.get("GroupName")
    if not isinstance(interpreter, str) or not isinstance(entrypoint, str) or not isinstance(worker_user, str) or not isinstance(worker_group, str):
        raise DarwinLaunchdError("launchd worker plist identity fields are invalid")
    expected = build_worker_plist(
        interpreter_path=interpreter,
        entrypoint_path=entrypoint,
        worker_user=worker_user,
        worker_group=worker_group,
    )
    if dict(value) != expected:
        raise DarwinLaunchdError("launchd worker plist fields are not exact")
    encoded = plistlib.dumps(expected, fmt=plistlib.FMT_XML, sort_keys=True)
    if plistlib.loads(encoded) != expected:
        raise DarwinLaunchdError("launchd worker plist roundtrip differs")
    return encoded


def parse_launchctl_reported_pid(output: str, *, label: str = _LABEL) -> int:
    if not isinstance(output, str) or f'"{label}"' not in output:
        raise DarwinLaunchdError("launchctl output does not bind the worker label")
    matches = re.findall(r"(?m)^\s*pid\s*=\s*([0-9]+)\s*$", output)
    if len(matches) != 1 or int(matches[0]) <= 0:
        raise DarwinLaunchdError("launchctl output does not contain one live worker PID")
    return int(matches[0])


def activate_worker_listener(name: str = _SOCKET_NAME) -> socket.socket:
    if sys.platform != "darwin":
        raise DarwinLaunchdError("launchd socket activation is Darwin-only")
    if name != _SOCKET_NAME:
        raise DarwinLaunchdError("launchd socket activation name differs")
    library = ctypes.CDLL(None, use_errno=True)
    activate = library.launch_activate_socket
    activate.argtypes = [ctypes.c_char_p,
                         ctypes.POINTER(ctypes.POINTER(ctypes.c_int)),
                         ctypes.POINTER(ctypes.c_size_t)]
    activate.restype = ctypes.c_int
    raw = ctypes.POINTER(ctypes.c_int)()
    count = ctypes.c_size_t(0)
    result = activate(name.encode("ascii"), ctypes.byref(raw), ctypes.byref(count))
    if result != 0:
        raise DarwinLaunchdError(result, "launchd socket activation failed")
    fds = [raw[index] for index in range(count.value)]
    ctypes.CDLL(None).free(raw)
    if len(fds) != 1:
        for fd in fds:
            os.close(fd)
        raise DarwinLaunchdError("launchd socket activation did not return exactly one descriptor")
    listener = socket.socket(fileno=fds[0])
    try:
        if (listener.family != socket.AF_UNIX
                or listener.type & 0xF != socket.SOCK_STREAM
                or listener.getsockopt(socket.SOL_SOCKET, socket.SO_ACCEPTCONN) != 1):
            raise DarwinLaunchdError("activated launchd descriptor is not the exact listener")
        os.set_inheritable(listener.fileno(), False)
        return listener
    except Exception:
        listener.close()
        raise
