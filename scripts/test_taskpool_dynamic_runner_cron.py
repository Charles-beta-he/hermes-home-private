#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "taskpool_dynamic_runner_cron.py"


def load_module():
    spec = importlib.util.spec_from_file_location("taskpool_dynamic_runner_cron", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_existing_live_lock_is_silent_ok_without_spawn():
    module = load_module()
    old_lock_pid = module.lock_pid
    old_alive = module.alive
    old_popen = module.subprocess.Popen
    try:
        module.lock_pid = lambda: 12345
        module.alive = lambda pid: pid == 12345
        def fake_popen(*args, **kwargs):
            raise AssertionError("should not spawn while live lock exists")
        module.subprocess.Popen = fake_popen
        payload = module.spawn_runner(env={})
    finally:
        module.lock_pid = old_lock_pid
        module.alive = old_alive
        module.subprocess.Popen = old_popen
    assert payload["status"] == "OK", payload
    assert payload["action"] == "already_running", payload
    assert payload["pid"] == 12345, payload


def test_spawns_runner_with_bounded_environment():
    module = load_module()
    old_lock_pid = module.lock_pid
    old_alive = module.alive
    old_popen = module.subprocess.Popen
    try:
        seen = {}
        class FakeProc:
            pid = 23456
            def poll(self):
                return None
        module.lock_pid = lambda: 0
        module.alive = lambda pid: False
        def fake_popen(args, **kwargs):
            seen["args"] = args
            seen["kwargs"] = kwargs
            return FakeProc()
        module.subprocess.Popen = fake_popen
        payload = module.spawn_runner(env={"PATH": os.environ.get("PATH", "")})
    finally:
        module.lock_pid = old_lock_pid
        module.alive = old_alive
        module.subprocess.Popen = old_popen
    assert payload["status"] == "OK", payload
    assert payload["action"] == "spawned", payload
    assert seen["kwargs"].get("start_new_session") is True, seen
    env = seen["kwargs"]["env"]
    assert env["HERMES_LOCAL_BRAIN_AUTORUN"] == "1", env
    assert env["HERMES_TASKPOOL_DYNAMIC_TIMEOUT"] == "700", env
    assert env["HERMES_BRAIN_AUTORUN_STEP_COMMAND_TIMEOUT_SECONDS"] == "220", env


if __name__ == "__main__":
    test_existing_live_lock_is_silent_ok_without_spawn()
    test_spawns_runner_with_bounded_environment()
    print("PASS")
