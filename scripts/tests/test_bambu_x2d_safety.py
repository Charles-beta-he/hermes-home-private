#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
BAMBU = SCRIPTS / "bambu_x2d.py"


def run_bambu(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    merged.update(env or {})
    return subprocess.run(
        [sys.executable, str(BAMBU), *args],
        text=True,
        capture_output=True,
        timeout=5,
        env=merged,
    )


def assert_external_refusal(proc: subprocess.CompletedProcess[str], action: str) -> None:
    assert proc.returncode == 2, proc.stderr + proc.stdout
    payload = json.loads(proc.stdout)
    assert payload["schema"] == "hermes_external_control_refusal_v1"
    assert payload["status"] == "refused_fail_closed"
    assert payload["action"] == action


def test_start_cli_refuses_even_with_access_code_without_network() -> None:
    proc = run_bambu(
        "start",
        "--remote",
        "smoke-box-v3.3mf",
        env={"BAMBU_ACCESS_CODE": "ABCDEFGH", "BAMBU_HOST": "127.0.0.1"},
    )
    assert_external_refusal(proc, "start")


def test_upload_cli_refuses_even_with_access_code_without_network() -> None:
    with tempfile.NamedTemporaryFile(suffix=".3mf") as fp:
        fp.write(b"fake sliced artifact for refusal test")
        fp.flush()
        proc = run_bambu(
            "upload",
            "--file",
            fp.name,
            "--remote",
            "smoke-box-v3.3mf",
            env={"BAMBU_ACCESS_CODE": "ABCDEFGH", "BAMBU_HOST": "127.0.0.1"},
        )
    assert_external_refusal(proc, "upload")


def test_capabilities_are_honest_about_mutating_cli_refusal() -> None:
    proc = run_bambu("capabilities")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    mutating = payload["mutating"]
    assert mutating["implemented"] == []
    assert "start_print" in mutating["refused_until_external_control_gate"]
    assert "upload_file" in mutating["refused_until_external_control_gate"]


def test_mutating_library_functions_require_external_control_executor() -> None:
    spec = importlib.util.spec_from_file_location("bambu_x2d_test", BAMBU)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    os.environ.pop("HERMES_EXTERNAL_CONTROL_EXECUTOR", None)
    try:
        module.require_external_control_executor("start_print")
    except RuntimeError as exc:
        assert "external_control_gate" in str(exc)
    else:
        raise AssertionError("expected mutating library guard to fail closed")


def test_status_refuses_without_access_code_before_network() -> None:
    env = {
        "BAMBU_ACCESS_CODE": "",
        "BAMBU_HOST": "127.0.0.1",
        "HERMES_BAMBU_KEYCHAIN_SERVICE": "hermes-test-missing-x2d",
        "HERMES_BAMBU_KEYCHAIN_ACCOUNT": "missing-access-code",
    }
    proc = run_bambu("status", "--timeout", "0.1", env=env)
    assert proc.returncode != 0
    output = proc.stderr + proc.stdout
    assert "Missing Bambu access code" in output
    assert "ConnectionRefusedError" not in output
