#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

SCRIPT = Path.home() / ".hermes" / "scripts" / "personal_hermes_brain_export.py"


def load_module():
    spec = importlib.util.spec_from_file_location("personal_hermes_brain_export", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_secret_pattern_blocks_token_assignment():
    m = load_module()
    assert m.has_secret_text("api_key = 'abcd1234abcd1234'")
    assert not m.has_secret_text("api_key = '[REDACTED]'")


def test_denies_raw_memory_and_env_paths():
    m = load_module()
    root = Path("/tmp/root")
    assert m.denied_path(root / "hermes" / "memory" / "index.sqlite", root)
    assert m.denied_path(root / ".env", root)
    assert m.denied_path(root / "auth.json", root)


def test_noagent_timeout_wrappers_are_allowlisted_for_backup():
    m = load_module()
    scripts = set(m.SELECTED_SCRIPT_GLOBS)
    assert "autonomous_evolution_nightly_noagent.py" in scripts
    assert "skill_steward_daily_audit_noagent.py" in scripts
    assert "taskpool_dynamic_runner.py" in scripts
    assert "multimodel_intervention_dynamic_step.py" in scripts


if __name__ == "__main__":
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    for test in tests:
        test()
    print(f"PASS {len(tests)} tests")
