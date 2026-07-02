#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


def load_smoke_module():
    path = Path(__file__).with_name("multi-model-smoke.py")
    spec = importlib.util.spec_from_file_location("multi_model_smoke_under_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def test_claude_smoke_records_claude_code_provider():
    module = load_smoke_module()
    assert module.MODELS["claude-fable-5"]["provider"] == "claude-code"


def test_record_health_updates_consult_models_circuit_breaker():
    module = load_smoke_module()
    calls = []
    fake = types.ModuleType("consult_models")

    def record_model_health(model, **kwargs):
        calls.append((model, kwargs))

    fake.record_model_health = record_model_health  # type: ignore[attr-defined]
    old = sys.modules.get("consult_models")
    sys.modules["consult_models"] = fake
    try:
        module.record_health("mimo-v2.5-pro", True, "xiaomi", "xiaomi-api", "")
        module.record_health("mimo-v2.5-pro", False, "xiaomi", "xiaomi-api", "timeout after 90s")
    finally:
        if old is None:
            sys.modules.pop("consult_models", None)
        else:
            sys.modules["consult_models"] = old

    assert calls[0] == (
        "mimo-v2.5-pro",
        {"ok": True, "provider": "xiaomi", "adapter": "xiaomi-api", "error": "", "reason": ""},
    )
    assert calls[1][0] == "mimo-v2.5-pro"
    assert calls[1][1]["ok"] is False
    assert calls[1][1]["reason"] == "smoke_failed"
    assert calls[1][1]["error"] == "timeout after 90s"


if __name__ == "__main__":
    test_claude_smoke_records_claude_code_provider()
    test_record_health_updates_consult_models_circuit_breaker()
    print("PASS")
