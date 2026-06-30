#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "task_pool_guardian.py"


def load_module():
    spec = importlib.util.spec_from_file_location("task_pool_guardian", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_run_command_timeout_returns_structured_error():
    module = load_module()
    result = module.run_command(["-c", "import time; time.sleep(10)"], timeout=1)
    assert result["returncode"] == 124, result
    assert result["reason"] == "subprocess_timeout", result
    assert result["timeout_seconds"] == 1, result


def test_parse_json_or_error_reports_command_failure():
    module = load_module()
    payload, err = module.parse_json_or_error({"returncode": 124, "reason": "subprocess_timeout", "stderr": ""}, "health_check")
    assert payload is None
    assert err["error"] == "subprocess_timeout", err
    assert err["returncode"] == 124, err


if __name__ == "__main__":
    test_run_command_timeout_returns_structured_error()
    test_parse_json_or_error_reports_command_failure()
    print("PASS")
