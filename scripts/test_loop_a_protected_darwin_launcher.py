from __future__ import annotations

import hashlib
import os
import stat

import pytest

from loop_a_protected.fd_gateway import CleanMetadataAdapter


class TestMetadata(CleanMetadataAdapter):
    def xattr_bytes(self, fd):
        return 0

    def has_extended_acl(self, fd):
        return False


def make_version(tmp_path):
    version = tmp_path / ("a" * 64)
    binary_dir = version / "bin"
    binary_dir.mkdir(parents=True)
    executable = binary_dir / "python3"
    executable.write_bytes(b"verified-interpreter-bytes")
    os.chmod(executable, 0o555)
    os.chmod(binary_dir, 0o555)
    os.chmod(version, 0o555)
    version_fd = os.open(version, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    executable_fd = os.open(executable, os.O_RDONLY | os.O_NOFOLLOW)
    return version, executable, version_fd, executable_fd


def test_launcher_rejects_root_or_any_process_not_already_running_as_worker(monkeypatch):
    import loop_a_protected.darwin_launcher as launcher

    monkeypatch.setattr(launcher.os, "geteuid", lambda: 0)
    with pytest.raises(launcher.DarwinLauncherError, match="non-root worker"):
        launcher.validate_worker_process_identity(0)
    with pytest.raises(launcher.DarwinLauncherError, match="non-root worker"):
        launcher.validate_worker_process_identity(501)
    monkeypatch.setattr(launcher.os, "geteuid", lambda: 501)
    launcher.validate_worker_process_identity(501)


def test_spawn_environment_is_fixed_and_does_not_inherit_ambient_values(monkeypatch):
    monkeypatch.setenv("PATH", "/hostile/bin")
    monkeypatch.setenv("PYTHONPATH", "/hostile/python")
    monkeypatch.setenv("PYTHONHOME", "/hostile/home")
    monkeypatch.setenv("DYLD_INSERT_LIBRARIES", "/hostile/inject.dylib")
    monkeypatch.setenv("PYTHONINSPECT", "1")

    from loop_a_protected.darwin_launcher import build_spawn_environment

    assert build_spawn_environment() == {
        "LANG": "C",
        "LC_ALL": "C",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONNOUSERSITE": "1",
        "PYTHONUTF8": "1",
    }


def test_spawn_argv_is_exact_and_uses_stdin_as_the_fd_backed_entrypoint():
    from loop_a_protected.darwin_launcher import build_spawn_argv

    version = "a" * 64
    interpreter = f"/private/var/db/hermes-loop-a/runtime/versions/{version}/bin/python3"
    assert build_spawn_argv(interpreter) == (
        interpreter,
        "-I",
        "-S",
        "-B",
        "-",
    )


@pytest.mark.parametrize("path", ["", "bin/python3", "/dev/fd/9", "/bin/sh", "/usr/bin/env"])
def test_spawn_argv_rejects_noncanonical_or_fallback_executables(path):
    from loop_a_protected.darwin_launcher import DarwinLauncherError, build_spawn_argv

    with pytest.raises(DarwinLauncherError):
        build_spawn_argv(path)


def test_adjacent_readback_binds_canonical_path_to_retained_fd_and_manifest_bytes(tmp_path):
    from loop_a_protected.darwin_launcher import verify_adjacent_executable

    version, executable, version_fd, executable_fd = make_version(tmp_path)
    try:
        result = verify_adjacent_executable(
            version_root_fd=version_fd,
            retained_executable_fd=executable_fd,
            version_root_path=str(version),
            expected_size=len(b"verified-interpreter-bytes"),
            expected_sha256=hashlib.sha256(b"verified-interpreter-bytes").hexdigest(),
            uid=os.fstat(version_fd).st_uid,
            gid=os.fstat(version_fd).st_gid,
            metadata=TestMetadata(),
        )
        assert result.canonical_path == str(executable)
        assert result.identity == (os.fstat(executable_fd).st_dev, os.fstat(executable_fd).st_ino)
        assert result.sha256 == hashlib.sha256(b"verified-interpreter-bytes").hexdigest()
    finally:
        os.close(executable_fd)
        os.close(version_fd)


def test_adjacent_readback_rejects_path_replacement_after_retaining_executable_fd(tmp_path):
    from loop_a_protected.darwin_launcher import DarwinLauncherError, verify_adjacent_executable

    version, executable, version_fd, executable_fd = make_version(tmp_path)
    replacement = executable.with_name("replacement")
    try:
        os.chmod(executable.parent, 0o755)
        replacement.write_bytes(b"verified-interpreter-bytes")
        os.chmod(replacement, 0o555)
        os.replace(replacement, executable)
        os.chmod(executable.parent, 0o555)
        with pytest.raises(DarwinLauncherError, match="link count|differs from retained FD"):
            verify_adjacent_executable(
                version_root_fd=version_fd,
                retained_executable_fd=executable_fd,
                version_root_path=str(version),
                expected_size=len(b"verified-interpreter-bytes"),
                expected_sha256=hashlib.sha256(b"verified-interpreter-bytes").hexdigest(),
                uid=os.fstat(version_fd).st_uid, gid=os.fstat(version_fd).st_gid, metadata=TestMetadata(),
            )
    finally:
        os.close(executable_fd)
        os.close(version_fd)


def test_adjacent_readback_rejects_in_place_byte_mutation_even_when_mode_is_restored(tmp_path):
    from loop_a_protected.darwin_launcher import DarwinLauncherError, verify_adjacent_executable

    version, executable, version_fd, executable_fd = make_version(tmp_path)
    try:
        os.chmod(executable, 0o755)
        executable.write_bytes(b"hostile-interpreter-bytes!")
        os.chmod(executable, 0o555)
        with pytest.raises(DarwinLauncherError, match="bytes differ"):
            verify_adjacent_executable(
                version_root_fd=version_fd,
                retained_executable_fd=executable_fd,
                version_root_path=str(version),
                expected_size=len(b"verified-interpreter-bytes"),
                expected_sha256=hashlib.sha256(b"verified-interpreter-bytes").hexdigest(),
                uid=os.fstat(version_fd).st_uid, gid=os.fstat(version_fd).st_gid, metadata=TestMetadata(),
            )
    finally:
        os.close(executable_fd)
        os.close(version_fd)


def test_low_level_posix_spawn_uses_fixed_fd_map_argv_environment_and_closes_other_fds(monkeypatch):
    import loop_a_protected.darwin_launcher as launcher

    version = "a" * 64
    interpreter = f"/private/var/db/hermes-loop-a/runtime/versions/{version}/bin/python3"
    source_fds = []
    captured = {}
    extra_read = extra_write = None
    try:
        for _ in range(10):
            read_fd, write_fd = os.pipe()
            os.close(write_fd)
            source_fds.append(read_fd)
        extra_read, extra_write = os.pipe()
        os.set_inheritable(extra_read, False)
        os.set_inheritable(extra_write, False)

        def fake_spawn(path, argv, env, *, file_actions):
            captured.update(path=path, argv=argv, env=env, file_actions=file_actions)
            return 43210

        monkeypatch.setattr(launcher.os, "posix_spawn", fake_spawn)
        monkeypatch.setattr(launcher, "_open_fd_numbers", lambda: set(
            source_fds + [10, extra_read, extra_write]
        ))
        pending = launcher._posix_spawn_pending(interpreter, tuple(source_fds))

        assert pending == 43210
        assert captured["path"] == interpreter
        assert captured["argv"] == (interpreter, "-I", "-S", "-B", "-")
        assert captured["env"] == launcher.build_spawn_environment()
        dup_targets = [action[2] for action in captured["file_actions"] if action[0] == os.POSIX_SPAWN_DUP2]
        assert dup_targets == list(range(10))
        close_fds = [action[1] for action in captured["file_actions"] if action[0] == os.POSIX_SPAWN_CLOSE]
        assert extra_read in close_fds
        assert extra_write in close_fds
        assert 10 in close_fds
    finally:
        for fd in source_fds:
            try:
                os.close(fd)
            except OSError:
                pass
        for fd in (extra_read, extra_write):
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass


def test_real_darwin_posix_spawn_harness_uses_stdin_script_and_duplex_handshake_fds(monkeypatch, tmp_path):
    import re
    import loop_a_protected.darwin_launcher as launcher

    script_read, script_write = os.pipe()
    stdout_read, stdout_write = os.pipe()
    stderr_read, stderr_write = os.pipe()
    challenge_read, challenge_write = os.pipe()
    response_read, response_write = os.pipe()
    executable_fd = os.open("/usr/bin/python3", os.O_RDONLY | os.O_NOFOLLOW)
    version_fd = os.open("/usr/bin", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    manifest_path = tmp_path / "manifest.json"
    inventory_path = tmp_path / "inventory.json"
    source_path = tmp_path / "source.bin"
    manifest_path.write_bytes(b"{}")
    inventory_path.write_bytes(b"{}")
    source_path.write_bytes(b"source-bytes")
    manifest_fd = os.open(manifest_path, os.O_RDONLY | os.O_NOFOLLOW)
    inventory_fd = os.open(inventory_path, os.O_RDONLY | os.O_NOFOLLOW)
    source_fd = os.open(source_path, os.O_RDONLY | os.O_NOFOLLOW)
    child_sources = (script_read, stdout_write, stderr_write, challenge_read, response_write,
                     executable_fd, version_fd, manifest_fd, inventory_fd, source_fd)
    all_fds = set(child_sources + (script_write, stdout_read, stderr_read, challenge_write, response_read))
    pid = None
    try:
        script = (
            b"import os\n"
            b"nonce = os.read(3, 128)\n"
            b"os.write(4, b'ACK:' + nonce)\n"
            b"print('LOOP_A_V9_SPAWN_OK:' + os.read(9, 32).decode())\n"
        )
        os.write(script_write, script)
        os.close(script_write)
        all_fds.remove(script_write)
        monkeypatch.setattr(launcher, "_FIXED_INTERPRETER", re.compile(r"^/usr/bin/python3$"))
        pid = launcher._posix_spawn_pending("/usr/bin/python3", child_sources)
        for fd in (script_read, stdout_write, stderr_write, challenge_read, response_write,
                   executable_fd, version_fd, manifest_fd, inventory_fd, source_fd):
            os.close(fd)
            all_fds.remove(fd)
        os.write(challenge_write, b"nonce-123")
        os.close(challenge_write)
        all_fds.remove(challenge_write)
        response = os.read(response_read, 1024)
        stdout = os.read(stdout_read, 1024)
        stderr = os.read(stderr_read, 4096)
        waited_pid, status = os.waitpid(pid, 0)
        pid = None
        assert waited_pid > 0
        assert os.waitstatus_to_exitcode(status) == 0, stderr.decode("utf-8", "replace")
        assert response == b"ACK:nonce-123"
        assert stdout == b"LOOP_A_V9_SPAWN_OK:source-bytes\n"
        assert stderr == b""
    finally:
        if pid is not None:
            try:
                os.kill(pid, 9)
            except ProcessLookupError:
                pass
            os.waitpid(pid, 0)
        for fd in all_fds:
            try:
                os.close(fd)
            except OSError:
                pass


def test_physical_spawn_ancestor_inventory_binds_every_retraversed_system_directory():
    from loop_a_protected.darwin_launcher import (
        DarwinLauncherError, PhysicalAncestor, verify_physical_spawn_ancestors,
    )

    entries = []
    for path in ("/", "/private", "/private/var", "/private/var/db"):
        value = os.stat(path, follow_symlinks=False)
        entries.append(PhysicalAncestor(
            path=path, device=value.st_dev, inode=value.st_ino, uid=value.st_uid,
            gid=value.st_gid, mode=stat.S_IMODE(value.st_mode),
            flags=getattr(value, "st_flags", 0),
        ))
    verify_physical_spawn_ancestors(entries)
    wrong = list(entries)
    wrong[-1] = PhysicalAncestor(**{**wrong[-1].__dict__, "inode": wrong[-1].inode + 1})
    with pytest.raises(DarwinLauncherError, match="drifted"):
        verify_physical_spawn_ancestors(wrong)
    with pytest.raises(DarwinLauncherError, match="not exact"):
        verify_physical_spawn_ancestors(entries[1:])


def test_high_level_launcher_places_no_caller_action_between_readback_and_spawn(monkeypatch, tmp_path):
    import loop_a_protected.darwin_launcher as launcher

    version = "a" * 64
    interpreter = f"/private/var/db/hermes-loop-a/runtime/versions/{version}/bin/python3"
    paths = [tmp_path / f"fd-{index}" for index in range(8)]
    for path in paths:
        path.write_bytes(b"x")
    fds = [os.open(path, os.O_RDONLY | os.O_NOFOLLOW) for path in paths]
    retained_stat = os.fstat(fds[3])
    events = []
    captured = {}

    def fake_fd_contract(rows, mutation_root_identities):
        assert tuple(row.role for row in rows) == (
            "entrypoint", "result", "diagnostics", "challenge", "attestation-control",
            "retained-executable", "version-root", "manifest", "inventory", "source",
        )
        assert mutation_root_identities == frozenset({(9, 10)})
        events.append("fd-contract")
        return tuple(rows)

    def fake_ancestors(entries):
        assert entries == ()
        assert events == ["fd-contract"]
        events.append("ancestors")

    def fake_verify(**kwargs):
        assert events == ["fd-contract", "ancestors"]
        events.append("verify")
        return launcher.ExecutableReadback(
            interpreter, (retained_stat.st_dev, retained_stat.st_ino), 1, "0" * 64,
        )

    def fake_spawn(path, source_fds):
        assert events == ["fd-contract", "ancestors", "verify"]
        events.append("spawn")
        captured["path"] = path
        captured["source_fds"] = source_fds
        return os.getpid()

    monkeypatch.setattr(launcher, "validate_exact_launcher_fd_contract", fake_fd_contract)
    monkeypatch.setattr(launcher, "verify_physical_spawn_ancestors", fake_ancestors)
    monkeypatch.setattr(launcher, "verify_adjacent_executable", fake_verify)
    monkeypatch.setattr(launcher, "_posix_spawn_pending", fake_spawn)
    pending = None
    try:
        pending = launcher.spawn_pending_handshake_after_adjacent_executable(
            canonical_interpreter_path=f"/private/var/db/hermes-loop-a/runtime/versions/{'b' * 64}/bin/python3",
            version_root_fd=fds[4], retained_executable_fd=fds[3],
            version_root_path=f"/private/var/db/hermes-loop-a/runtime/versions/{version}",
            expected_executable_size=1, expected_executable_sha256="0" * 64,
            uid=os.fstat(fds[4]).st_uid, gid=os.fstat(fds[4]).st_gid, metadata=TestMetadata(),
            worker_uid=os.geteuid(),
            entrypoint_fd=fds[0], result_fd=fds[1], diagnostics_fd=fds[2],
            manifest_fd=fds[5], inventory_fd=fds[6], source_fd=fds[7], entrypoint_sha256="1" * 64,
            manifest_digest="2" * 64, inventory_digest="3" * 64, source_digest="5" * 64,
            physical_ancestors=(),
            mutation_root_identities=frozenset({(9, 10)}),
        )
        assert events == ["fd-contract", "ancestors", "verify", "spawn"]
        assert captured["path"] == interpreter
        assert len(captured["source_fds"]) == 10
        source_item = next(
            item for item in pending.handshake.expectation.protected_fd_inventory
            if item["role"] == "source"
        )
        assert source_item["fd"] == 9
        assert source_item["sha256"] == "5" * 64
        assert pending.pid == os.getpid()
    finally:
        if pending is not None:
            pending.handshake.close()
        for fd in fds:
            os.close(fd)
