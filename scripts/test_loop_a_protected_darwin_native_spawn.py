from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "darwin", reason="Darwin-only native spawn adapter")


@pytest.fixture(scope="module")
def native_library(tmp_path_factory):
    from loop_a_protected.darwin_native_spawn import compile_native_library

    output = tmp_path_factory.mktemp("darwin-native-spawn") / "libloop_a_darwin_spawn.dylib"
    return compile_native_library(output)


def _open_sources(tmp_path: Path):
    script = tmp_path / "child.py"
    output = tmp_path / "stdout.json"
    diagnostics = tmp_path / "stderr.txt"
    inputs = []
    script.write_text(
        "import json, os\n"
        "values = {}\n"
        "for fd in range(3, 10):\n"
        "    os.lseek(fd, 0, os.SEEK_SET)\n"
        "    values[str(fd)] = os.read(fd, 128).decode('ascii')\n"
        "open_high = []\n"
        "for fd in range(10, 256):\n"
        "    try:\n"
        "        os.fstat(fd)\n"
        "    except OSError:\n"
        "        continue\n"
        "    open_high.append(fd)\n"
        "os.write(1, json.dumps({'values': values, 'open_high': open_high}, sort_keys=True).encode())\n",
        encoding="utf-8",
    )
    output.write_bytes(b"")
    diagnostics.write_bytes(b"")
    for fd in range(3, 10):
        path = tmp_path / f"input-{fd}.txt"
        path.write_text(f"source-for-{fd}", encoding="ascii")
        inputs.append(path)

    fds = [
        os.open(script, os.O_RDONLY),
        os.open(output, os.O_WRONLY | os.O_TRUNC),
        os.open(diagnostics, os.O_WRONLY | os.O_TRUNC),
        *(os.open(path, os.O_RDONLY) for path in inputs),
    ]
    return fds, output, diagnostics


def test_native_spawn_maps_exact_ten_fds_and_closes_every_other_inherited_fd(native_library, tmp_path):
    from loop_a_protected.darwin_native_spawn import DarwinNativeSpawner

    source_fds, output, diagnostics = _open_sources(tmp_path)
    extra_read, extra_write = os.pipe()
    os.set_inheritable(extra_read, True)
    os.set_inheritable(extra_write, True)
    try:
        pid = DarwinNativeSpawner(native_library).spawn(
            "/usr/bin/python3",
            ("/usr/bin/python3", "-I", "-S", "-B", "-"),
            {"PATH": "/usr/bin", "LANG": "C", "LC_ALL": "C", "PYTHONHASHSEED": "0"},
            tuple(source_fds),
        )
    finally:
        for fd in source_fds:
            os.close(fd)
        os.close(extra_read)
        os.close(extra_write)

    waited, status = os.waitpid(pid, 0)
    assert waited == pid
    assert os.waitstatus_to_exitcode(status) == 0, diagnostics.read_text(encoding="utf-8")
    observed = json.loads(output.read_text(encoding="utf-8"))
    assert observed["values"] == {str(fd): f"source-for-{fd}" for fd in range(3, 10)}
    assert observed["open_high"] == []
    assert diagnostics.read_bytes() == b""


def test_spawn_rejects_non_exact_path_and_invalid_fd_contract_before_native_call(native_library):
    from loop_a_protected.darwin_native_spawn import DarwinNativeSpawnError, DarwinNativeSpawner

    spawner = DarwinNativeSpawner(native_library)
    with pytest.raises(DarwinNativeSpawnError, match="absolute"):
        spawner.spawn("python3", ("python3",), {}, tuple(range(10)))
    with pytest.raises(DarwinNativeSpawnError, match="exactly ten"):
        spawner.spawn("/usr/bin/python3", ("/usr/bin/python3",), {}, tuple(range(9)))
    with pytest.raises(DarwinNativeSpawnError, match="distinct"):
        spawner.spawn("/usr/bin/python3", ("/usr/bin/python3",), {}, (0,) * 10)
    with pytest.raises(DarwinNativeSpawnError, match="non-negative integers"):
        spawner.spawn("/usr/bin/python3", ("/usr/bin/python3",), {}, tuple(range(9)) + (True,))


def test_native_source_uses_cloexec_default_without_shell_path_search_or_fd_enumeration():
    source = (Path(__file__).parent / "loop_a_protected" / "native" / "loop_a_darwin_spawn.c").read_text(
        encoding="utf-8"
    )
    assert "POSIX_SPAWN_CLOEXEC_DEFAULT" in source
    assert "posix_spawn(" in source
    for forbidden in ("posix_spawnp", "system(", "popen(", "execvp", "/dev/fd", "proc_pidinfo"):
        assert forbidden not in source
    launcher_source = (
        Path(__file__).parent / "loop_a_protected" / "darwin_launcher.py"
    ).read_text(encoding="utf-8")
    assert "os.posix_spawn" not in launcher_source
    assert "/dev/fd" not in launcher_source


def test_native_source_compiles_under_strict_clang(tmp_path):
    source = Path(__file__).parent / "loop_a_protected" / "native" / "loop_a_darwin_spawn.c"
    output = tmp_path / "libloop_a_darwin_spawn.dylib"
    completed = subprocess.run(
        [
            "clang", "-std=c11", "-Wall", "-Wextra", "-Werror", "-fvisibility=hidden",
            "-dynamiclib", str(source), "-o", str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert output.is_file()


def test_compile_native_library_emits_reproducible_bytes(tmp_path):
    from loop_a_protected.darwin_native_spawn import compile_native_library

    first = compile_native_library(tmp_path / "first" / "libloop_a_darwin_spawn.dylib").read_bytes()
    second = compile_native_library(tmp_path / "second" / "libloop_a_darwin_spawn.dylib").read_bytes()
    assert first == second
