#!/usr/bin/env python3
"""Regression tests for multi-model-smoke.py runtime metadata."""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).parent / "multi-model-smoke.py"


def load_module():
    spec = importlib.util.spec_from_file_location("multi_model_smoke", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_claude_smoke_records_claude_code_provider():
    mod = load_module()
    assert mod.MODELS["claude-fable-5"]["provider"] == "claude-code"


if __name__ == "__main__":
    test_claude_smoke_records_claude_code_provider()
    print("OK")
