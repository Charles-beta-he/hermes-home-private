from __future__ import annotations

import plistlib

import pytest

from loop_a_protected.darwin_launchd import (
    DarwinLaunchdError,
    build_root_broker_plist,
    build_worker_plist,
    parse_launchctl_reported_pid,
    serialize_root_broker_plist,
    serialize_worker_plist,
)


VERSION = "a" * 64
INTERPRETER = f"/private/var/db/hermes-loop-a/runtime/versions/{VERSION}/bin/python3"
ENTRYPOINT = f"/private/var/db/hermes-loop-a/runtime/versions/{VERSION}/libexec/worker-entrypoint.py"
BROKER_ENTRYPOINT = f"/private/var/db/hermes-loop-a/runtime/versions/{VERSION}/libexec/root-broker-entrypoint.py"


def test_launchd_plist_is_exact_distinct_uid_private_seqpacket_contract():
    value = build_worker_plist(interpreter_path=INTERPRETER, entrypoint_path=ENTRYPOINT)
    assert value["UserName"] == "_hermesloopa"
    assert value["GroupName"] == "_hermesloopa"
    assert value["ProgramArguments"] == [INTERPRETER, "-I", "-S", "-B", "-"]
    assert value["EnvironmentVariables"] == {
        "LANG": "C", "LC_ALL": "C", "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0", "PYTHONNOUSERSITE": "1", "PYTHONUTF8": "1",
    }
    assert value["Sockets"] == {
        "Broker": {
            "SockPathName": "/private/var/run/hermes-loop-a/worker.sock",
            "SockPathMode": 0o600, "SockPathOwner": 0, "SockPathGroup": 0,
            "SockFamily": "Unix", "SockType": "stream", "SockPassive": True,
        },
    }
    encoded = serialize_worker_plist(value)
    assert plistlib.loads(encoded) == value


def test_launchd_plist_rejects_wrong_version_entrypoint_or_extra_authority():
    with pytest.raises(DarwinLaunchdError):
        build_worker_plist(interpreter_path="/usr/bin/python3", entrypoint_path=ENTRYPOINT)
    with pytest.raises(DarwinLaunchdError):
        build_worker_plist(
            interpreter_path=INTERPRETER,
            entrypoint_path=f"/private/var/db/hermes-loop-a/runtime/versions/{'b' * 64}/worker.py",
        )
    value = build_worker_plist(interpreter_path=INTERPRETER, entrypoint_path=ENTRYPOINT)
    value["MachServices"] = {"public": True}
    with pytest.raises(DarwinLaunchdError, match="not exact"):
        serialize_worker_plist(value)


def test_root_broker_plist_is_exact_root_one_run_contract():
    value = build_root_broker_plist(
        interpreter_path=INTERPRETER,
        entrypoint_path=BROKER_ENTRYPOINT,
    )
    assert value == {
        "Label": "com.nous.hermes-loop-a.root-broker",
        "ProgramArguments": [INTERPRETER, "-I", "-S", "-B", "-"],
        "StandardInPath": BROKER_ENTRYPOINT,
        "StandardOutPath": "/dev/null",
        "StandardErrorPath": "/dev/null",
        "UserName": "root",
        "GroupName": "wheel",
        "EnvironmentVariables": {
            "LANG": "C", "LC_ALL": "C", "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0", "PYTHONNOUSERSITE": "1", "PYTHONUTF8": "1",
        },
        "ProcessType": "Background",
        "StartCalendarInterval": {"Hour": 2, "Minute": 0},
        "RunAtLoad": False,
        "KeepAlive": False,
        "Umask": 0o077,
    }
    encoded = serialize_root_broker_plist(value)
    assert plistlib.loads(encoded) == value


def test_root_broker_plist_rejects_nonexact_identity_and_extra_authority():
    with pytest.raises(DarwinLaunchdError):
        build_root_broker_plist(
            interpreter_path="/usr/bin/python3",
            entrypoint_path=BROKER_ENTRYPOINT,
        )
    with pytest.raises(DarwinLaunchdError):
        build_root_broker_plist(
            interpreter_path=INTERPRETER,
            entrypoint_path=f"/private/var/db/hermes-loop-a/runtime/versions/{'b' * 64}/root.py",
        )
    with pytest.raises(DarwinLaunchdError):
        build_root_broker_plist(
            interpreter_path=INTERPRETER,
            entrypoint_path=f"/private/var/db/hermes-loop-a/runtime/versions/{VERSION}/libexec/..",
        )
    value = build_root_broker_plist(
        interpreter_path=INTERPRETER,
        entrypoint_path=BROKER_ENTRYPOINT,
    )
    value["UserName"] = "_hermesloopa"
    with pytest.raises(DarwinLaunchdError, match="not exact"):
        serialize_root_broker_plist(value)


def test_launchctl_pid_parser_requires_exact_label_and_one_positive_pid():
    output = 'system/com.nous.hermes-loop-a.worker = {\n\t"com.nous.hermes-loop-a.worker"\n\tpid = 4321\n}'
    assert parse_launchctl_reported_pid(output) == 4321
    for malformed in (
        '"wrong"\npid = 4321',
        '"com.nous.hermes-loop-a.worker"\npid = 0',
        '"com.nous.hermes-loop-a.worker"\npid = 1\npid = 2',
    ):
        with pytest.raises(DarwinLaunchdError):
            parse_launchctl_reported_pid(malformed)
