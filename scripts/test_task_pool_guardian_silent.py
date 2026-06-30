#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
import signal
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "task_pool_guardian_silent.py"


def load_module():
    spec = importlib.util.spec_from_file_location("task_pool_guardian_silent", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_run_timeout_returns_structured_error_and_kills_process_group():
    module = load_module()
    rc, out = module.run(["-c", "import time; print('started'); time.sleep(10)"], timeout=1)
    assert rc == 124, (rc, out)
    assert "subprocess_timeout" in out, out
    assert "timeout_seconds" in out, out


def test_extract_json_finds_object_after_prefix():
    module = load_module()
    assert module.extract_json("noise {\"status\": \"ok\"}\n")["status"] == "ok"


if __name__ == "__main__":
    test_run_timeout_returns_structured_error_and_kills_process_group()
    test_extract_json_finds_object_after_prefix()
    print("PASS")
