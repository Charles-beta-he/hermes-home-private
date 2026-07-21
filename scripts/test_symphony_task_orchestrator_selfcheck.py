#!/usr/bin/env python3
import importlib.util
import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parent


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_selfcheck_accepts_done_task_log_in_archive(tmp_path, monkeypatch):
    selfcheck = load_module(
        SCRIPTS_DIR / "symphony_task_orchestrator_selfcheck.py",
        "symphony_selfcheck_archive_test",
    )
    archived = (
        tmp_path
        / "05-实践与项目"
        / "tasks-archived"
        / "2026-05-08-symphony-inspired-task-orchestrator-landing-log.md"
    )
    archived.parent.mkdir(parents=True)
    archived.write_text("---\nstatus: done\n---\nlanding proof\n", encoding="utf-8")

    monkeypatch.setattr(selfcheck, "VAULT", tmp_path)
    monkeypatch.setattr(
        selfcheck,
        "REQUIRED_FILES",
        {
            "task_log": "05-实践与项目/tasks/2026-05-08-symphony-inspired-task-orchestrator-landing-log.md"
        },
    )
    monkeypatch.setattr(selfcheck, "REQUIRED_PHRASES", {"task_log": ["landing proof"]})
    monkeypatch.setattr(selfcheck, "MOC_MARKERS", {})

    result = selfcheck.check()

    assert result["status"] == "PASS"
    assert result["files"]["task_log"]["path"] == str(archived)
    assert result["files"]["task_log"]["archived"] is True


def test_rendered_control_center_preserves_documented_multimodel_trigger(monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_BRAIN_VAULT", str(tmp_path))
    orchestrator = load_module(
        SCRIPTS_DIR / "brain_task_orchestrator.py",
        "brain_task_orchestrator_control_center_test",
    )

    rendered = orchestrator.render_control_center()

    assert "多模型分解本地大脑任务池并排序" in rendered
