from __future__ import annotations

import ctypes
import os
import subprocess
import sys
from pathlib import Path
from typing import Mapping, Sequence, Tuple


_FD_COUNT = 10
_NATIVE_SOURCE = Path(__file__).with_name("native") / "loop_a_darwin_spawn.c"


class DarwinNativeSpawnError(RuntimeError):
    """A fail-closed native spawn validation, build, or syscall failure."""

    def __init__(self, message: str, *, errno_value: int | None = None) -> None:
        super().__init__(message)
        self.errno = errno_value


def _require_darwin() -> None:
    if sys.platform != "darwin":
        raise DarwinNativeSpawnError("native spawn adapter requires Darwin")


def compile_native_library(output_path: os.PathLike[str] | str) -> Path:
    """Compile the isolated adapter with strict warnings and no shell invocation."""
    _require_darwin()
    output = Path(output_path)
    if not output.is_absolute():
        raise DarwinNativeSpawnError("native library output path must be absolute")
    output.parent.mkdir(parents=True, exist_ok=True)
    command = (
        "clang",
        "-std=c11",
        "-Wall",
        "-Wextra",
        "-Werror",
        "-fvisibility=hidden",
        "-dynamiclib",
        "-Wl,-install_name,@rpath/libloop_a_darwin_spawn.dylib",
        str(_NATIVE_SOURCE),
        "-o",
        str(output),
    )
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or "clang failed without diagnostics"
        raise DarwinNativeSpawnError(f"native spawn adapter compilation failed: {detail}")
    if not output.is_file():
        raise DarwinNativeSpawnError("clang reported success without producing the native library")
    return output


def _encode_text(value: str, *, label: str) -> bytes:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise DarwinNativeSpawnError(f"{label} must be one non-empty NUL-free string")
    return os.fsencode(value)


def _validate_source_fds(source_fds: Sequence[int]) -> Tuple[int, ...]:
    values = tuple(source_fds)
    if len(values) != _FD_COUNT:
        raise DarwinNativeSpawnError("spawn requires exactly ten ordered source FDs")
    if any(isinstance(fd, bool) or not isinstance(fd, int) or fd < 0 for fd in values):
        raise DarwinNativeSpawnError("spawn source FDs must be non-negative integers")
    if len(set(values)) != _FD_COUNT:
        raise DarwinNativeSpawnError("spawn source FDs must be distinct")
    return values


class DarwinNativeSpawner:
    """Load and invoke the Darwin exact-path, exact-ten-FD spawn boundary."""

    def __init__(self, library_path: os.PathLike[str] | str) -> None:
        _require_darwin()
        path = Path(library_path)
        if not path.is_absolute() or not path.is_file():
            raise DarwinNativeSpawnError("native library path must name an existing absolute file")
        try:
            library = ctypes.CDLL(str(path))
            function = library.loop_a_darwin_spawn
        except (OSError, AttributeError) as exc:
            raise DarwinNativeSpawnError("native spawn library could not be loaded") from exc
        function.argtypes = (
            ctypes.c_char_p,
            ctypes.POINTER(ctypes.c_char_p),
            ctypes.POINTER(ctypes.c_char_p),
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int),
        )
        function.restype = ctypes.c_int
        self._library = library
        self._spawn = function

    def spawn(
        self,
        executable_path: str,
        argv: Sequence[str],
        environment: Mapping[str, str],
        source_fds: Sequence[int],
    ) -> int:
        path_bytes = _encode_text(executable_path, label="executable path")
        if not os.path.isabs(executable_path):
            raise DarwinNativeSpawnError("executable path must be absolute")
        argv_values = tuple(argv)
        if not argv_values:
            raise DarwinNativeSpawnError("argv must not be empty")
        argv_bytes = tuple(_encode_text(value, label="argv item") for value in argv_values)
        if not isinstance(environment, Mapping):
            raise DarwinNativeSpawnError("environment must be a mapping")
        environment_bytes = []
        for key, value in sorted(environment.items()):
            if not isinstance(key, str) or not key or "=" in key or "\x00" in key:
                raise DarwinNativeSpawnError("environment keys must be non-empty and contain neither '=' nor NUL")
            value_bytes = _encode_text(value, label="environment value")
            environment_bytes.append(os.fsencode(key) + b"=" + value_bytes)
        fd_values = _validate_source_fds(source_fds)

        argv_array = (ctypes.c_char_p * (len(argv_bytes) + 1))(*argv_bytes, None)
        env_array = (ctypes.c_char_p * (len(environment_bytes) + 1))(*environment_bytes, None)
        fd_array = (ctypes.c_int * _FD_COUNT)(*fd_values)
        child_pid = ctypes.c_int(-1)
        result = self._spawn(path_bytes, argv_array, env_array, fd_array, ctypes.byref(child_pid))
        if result != 0:
            try:
                detail = os.strerror(result)
            except ValueError:
                detail = "unknown native error"
            raise DarwinNativeSpawnError(
                f"native posix_spawn failed closed: {detail}", errno_value=result
            )
        if child_pid.value <= 0:
            raise DarwinNativeSpawnError("native posix_spawn returned an invalid child PID")
        return child_pid.value
