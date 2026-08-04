from __future__ import annotations

import os

import pytest


VERSION = "a" * 64
ROOT = f"/private/var/db/hermes-loop-a/runtime/versions/{VERSION}"
INTERPRETER = ROOT + "/bin/python3"


def _status(path):
    class Status:
        st_dev = 1
        st_ino = {"/": 1, "/private": 2, "/private/var": 3, "/private/var/db": 4}[path]
        st_uid = 0
        st_gid = 0
        st_mode = 0o040755
        st_flags = 0

    return Status()


def test_worker_service_derives_only_exact_digest_runtime_and_physical_ancestors():
    from loop_a_protected.darwin_worker_service import build_execution_plan

    plan = build_execution_plan(
        executable=INTERPRETER,
        worker_uid=222,
        worker_gid=223,
        euid=lambda: 222,
        egid=lambda: 223,
        stat_path=_status,
        metadata=object(),
    )
    assert plan.version_root_path == ROOT
    assert plan.entrypoint_relative_path == "libexec/inner-entrypoint.py"
    assert plan.uid == 0
    assert plan.gid == 0
    assert plan.worker_uid == 222
    assert plan.mutation_root_identities == frozenset()
    assert tuple(item.path for item in plan.physical_ancestors) == (
        "/", "/private", "/private/var", "/private/var/db",
    )


@pytest.mark.parametrize("path", [
    "/usr/bin/python3",
    f"/var/db/hermes-loop-a/runtime/versions/{VERSION}/bin/python3",
    f"{ROOT}/bin/python3.11",
    f"/private/var/db/hermes-loop-a/runtime/versions/{'g' * 64}/bin/python3",
])
def test_worker_service_rejects_noncanonical_runtime_before_activation(path):
    from loop_a_protected.darwin_worker_service import DarwinWorkerServiceError, run_worker_service_once

    called = []
    with pytest.raises(DarwinWorkerServiceError, match="runtime interpreter"):
        run_worker_service_once(
            executable=path,
            worker_uid=222,
            worker_gid=223,
            euid=lambda: 222,
            egid=lambda: 223,
            stat_path=_status,
            activate=lambda: called.append("activate"),
            serve=lambda **kwargs: None,
            executor_factory=lambda plan: object(),
            metadata=object(),
        )
    assert called == []


def test_worker_service_requires_exact_distinct_identity_before_activation():
    from loop_a_protected.darwin_worker_service import DarwinWorkerServiceError, run_worker_service_once

    for actual_uid, actual_gid in ((0, 223), (222, 0), (224, 223), (222, 224)):
        called = []
        with pytest.raises(DarwinWorkerServiceError, match="identity"):
            run_worker_service_once(
                executable=INTERPRETER,
                worker_uid=222,
                worker_gid=223,
                euid=lambda value=actual_uid: value,
                egid=lambda value=actual_gid: value,
                stat_path=_status,
                activate=lambda: called.append("activate"),
                serve=lambda **kwargs: None,
                executor_factory=lambda plan: object(),
                metadata=object(),
            )
        assert called == []


def test_worker_service_activates_one_listener_and_serves_one_bounded_session():
    from loop_a_protected.darwin_worker_service import run_worker_service_once

    events = []
    listener = object()
    executor = object()

    result = run_worker_service_once(
        executable=INTERPRETER,
        worker_uid=222,
        worker_gid=223,
        euid=lambda: 222,
        egid=lambda: 223,
        stat_path=_status,
        activate=lambda: events.append("activate") or listener,
        serve=lambda **kwargs: events.append(("serve", kwargs)) or "outcome",
        executor_factory=lambda plan: events.append(("executor", plan)) or executor,
        metadata=object(),
        timeout_seconds=7.0,
    )
    assert result == "outcome"
    assert events[0][0] == "executor"
    assert events[1] == "activate"
    assert events[2] == ("serve", {
        "listener": listener,
        "executor": executor,
        "timeout_seconds": 7.0,
    })


def test_bootstrap_bytes_clear_ambient_environment_before_protected_import():
    from loop_a_protected.darwin_worker_service import worker_bootstrap_bytes

    data = worker_bootstrap_bytes()
    assert data.startswith(b"import os,sys\n")
    assert b"os.environ.clear()" in data
    assert b"os.environ.update(" in data
    assert data.index(b"os.environ.clear()") < data.index(b"sys.path.insert(")
    assert data.index(b"sys.path.insert(") < data.index(b"from loop_a_protected.darwin_worker_service import main")
    assert b"PYTHONPATH" not in data
    compile(data, "worker-bootstrap", "exec")
