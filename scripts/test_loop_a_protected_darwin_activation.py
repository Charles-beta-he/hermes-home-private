from __future__ import annotations

import socket
import subprocess

import pytest


SOCKET_PATH = "/private/var/run/hermes-loop-a/worker.sock"
LABEL = "system/com.nous.hermes-loop-a.worker"


class FakeSocket:
    family = socket.AF_UNIX
    type = socket.SOCK_STREAM

    def __init__(self, events):
        self.events = events
        self.closed = False

    def connect(self, path):
        self.events.append(("connect", path))

    def close(self):
        self.closed = True
        self.events.append(("close",))


def test_activation_connects_before_launchctl_pid_and_cross_binds_peer():
    from loop_a_protected.darwin_activation import open_launchd_worker_session

    events = []
    sock = FakeSocket(events)

    def runner(argv, **kwargs):
        events.append(("run", tuple(argv), kwargs))
        return subprocess.CompletedProcess(
            argv,
            0,
            'system/com.nous.hermes-loop-a.worker = {\n'
            '\t"com.nous.hermes-loop-a.worker"\n\tpid = 4321\n}',
            "",
        )

    def peer_validator(value, *, broker_euid, expected_pid, expected_uid, expected_gid):
        assert value is sock
        events.append(("peer", broker_euid, expected_pid, expected_uid, expected_gid))

    session = open_launchd_worker_session(
        worker_uid=222, worker_gid=223, socket_factory=lambda *_: sock,
        runner=runner, peer_validator=peer_validator, geteuid=lambda: 0,
        monotonic=iter((0.0, 0.0)).__next__, sleep=lambda _: None,
    )

    assert session.socket is sock
    assert session.launchd_pid == 4321
    assert events[0] == ("connect", SOCKET_PATH)
    assert events[1][0:2] == ("run", ("/bin/launchctl", "print", LABEL))
    assert events[1][2] == {
        "capture_output": True,
        "text": True,
        "timeout": 1.0,
        "check": False,
    }
    assert events[2] == ("peer", 0, 4321, 222, 223)
    assert sock.closed is False


def test_activation_retries_absent_pid_but_is_bounded():
    from loop_a_protected.darwin_activation import wait_for_launchd_worker_pid

    outputs = iter((
        subprocess.CompletedProcess([], 113, "", "service not found"),
        subprocess.CompletedProcess([], 0, '"com.nous.hermes-loop-a.worker"\npid = 77\n', ""),
    ))
    sleeps = []
    pid = wait_for_launchd_worker_pid(
        runner=lambda *args, **kwargs: next(outputs), timeout_seconds=2.0,
        monotonic=iter((1.0, 1.1, 1.2)).__next__, sleep=sleeps.append,
    )
    assert pid == 77
    assert sleeps == [0.05]


def test_activation_timeout_closes_connection_and_never_validates_peer():
    from loop_a_protected.darwin_activation import DarwinActivationError, open_launchd_worker_session

    events = []
    sock = FakeSocket(events)
    peer_calls = []
    with pytest.raises(DarwinActivationError, match="PID deadline"):
        open_launchd_worker_session(
            worker_uid=222, worker_gid=223, socket_factory=lambda *_: sock,
            runner=lambda *args, **kwargs: subprocess.CompletedProcess([], 113, "", "absent"),
            peer_validator=lambda *args, **kwargs: peer_calls.append(1),
            geteuid=lambda: 0,
            timeout_seconds=0.1,
            monotonic=iter((0.0, 0.0, 0.2)).__next__, sleep=lambda _: None,
        )
    assert sock.closed is True
    assert peer_calls == []


@pytest.mark.parametrize("uid,gid", [(0, 223), (222, 0), (-1, 223), (True, 223)])
def test_activation_rejects_root_or_invalid_worker_identity_before_connect(uid, gid):
    from loop_a_protected.darwin_activation import DarwinActivationError, open_launchd_worker_session

    called = []
    with pytest.raises(DarwinActivationError, match="worker identity"):
        open_launchd_worker_session(
            worker_uid=uid, worker_gid=gid,
            socket_factory=lambda *_: called.append(1),
            runner=lambda *args, **kwargs: None,
            peer_validator=lambda *args, **kwargs: None,
            geteuid=lambda: 0,
        )
    assert called == []


def test_activation_requires_root_broker_before_connect():
    from loop_a_protected.darwin_activation import DarwinActivationError, open_launchd_worker_session

    called = []
    with pytest.raises(DarwinActivationError, match="root broker"):
        open_launchd_worker_session(
            worker_uid=222, worker_gid=223,
            socket_factory=lambda *_: called.append(1),
            runner=lambda *args, **kwargs: None,
            peer_validator=lambda *args, **kwargs: None,
            geteuid=lambda: 501,
        )
    assert called == []
