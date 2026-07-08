#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).with_name("task_classifier.py")
spec = importlib.util.spec_from_file_location("task_classifier", SCRIPT)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_jspace_title_routes_to_jspace_conflict_group() -> None:
    task = {
        "id": "jspace-router-title",
        "title": "Runtime router改造 for J-space workspace projection",
        "workspace": str(Path.home() / ".hermes"),
    }
    assert mod.infer_conflict_group(task) == "hermes-jspace-router"
    assert mod.classify_deterministic(task) == f"conflict:{Path.home() / '.hermes'}:hermes-jspace-router"


def test_jspace_allowed_glob_routes_to_jspace_conflict_group() -> None:
    task = {
        "id": "jspace-router-file",
        "title": "local projection helper",
        "workspace": str(Path.home() / ".hermes"),
        "allowed_globs": "~/.hermes/scripts/hermes_jspace.py,~/.hermes/workflows/jspace/**",
    }
    assert mod.infer_conflict_group(task) == "hermes-jspace-router"
    assert mod.validate_boundary_consistency([task])["consistent"] is True


if __name__ == "__main__":
    test_jspace_title_routes_to_jspace_conflict_group()
    test_jspace_allowed_glob_routes_to_jspace_conflict_group()
    print("PASS")
