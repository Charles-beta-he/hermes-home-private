#!/usr/bin/env python3

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).with_name("wechat_export_doctor.py")
SPEC = importlib.util.spec_from_file_location("wechat_export_doctor", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def test_known_local_version_fails_closed():
    report = MODULE.build_report(
        app_present=True,
        app_version="4.1.11",
        sqlcipher_path=None,
        brew_path="/opt/homebrew/bin/brew",
        python_version="3.9.6",
    )
    assert report["ready_for_export"] is False
    assert "exact_version_key_extraction_unsupported" in report["blockers"]
    assert "bulk_export_implementation_unavailable" in report["blockers"]
    assert report["data_access_attempted"] is False
    assert report["writes_attempted"] is False
    assert report["mcp_registration_attempted"] is False


def test_unknown_version_requires_compatibility_review():
    report = MODULE.build_report(
        app_present=True,
        app_version="99.0.0",
        sqlcipher_path="/opt/homebrew/bin/sqlcipher",
        brew_path="/opt/homebrew/bin/brew",
        python_version="3.13.0",
    )
    assert report["ready_for_export"] is False
    assert "exact_version_compatibility_unverified" in report["blockers"]


def test_absent_app_is_typed_blocker():
    report = MODULE.build_report(
        app_present=False,
        app_version=None,
        sqlcipher_path=None,
        brew_path=None,
        python_version="3.9.6",
    )
    assert report["blockers"][0] == "wechat_app_absent"


def test_script_contains_no_real_data_container_path():
    source = SCRIPT.read_text(encoding="utf-8")
    forbidden = ["Library/Containers", "xwechat_files", "message_0.db", "key.txt", "all_keys.json"]
    assert all(token not in source for token in forbidden)


def test_cli_json_is_machine_readable_and_zero_access():
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(proc.stdout)
    assert report["schema"] == "hermes.wechat_local_export.doctor.v1"
    assert report["data_access_attempted"] is False
    assert report["network_access_attempted"] is False
    assert report["writes_attempted"] is False
    assert report["mcp_registration_attempted"] is False
