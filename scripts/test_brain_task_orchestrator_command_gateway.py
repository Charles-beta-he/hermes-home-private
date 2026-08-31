#!/usr/bin/env python3
"""Focused integration tests for canonical command-gateway task persistence."""
from __future__ import annotations

import ast
import importlib.util
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import uuid

import pytest

from taskpool_command_gateway import TaskpoolCommandGateway

SCRIPT = Path(__file__).with_name("brain_task_orchestrator.py")


def load_orchestrator(vault: Path, db_path: Path, *, initialize_gateway: bool = True):
    old_vault = os.environ.get("HERMES_BRAIN_VAULT")
    old_db = os.environ.get("HERMES_TASKPOOL_COMMAND_GATEWAY_DB")
    os.environ["HERMES_BRAIN_VAULT"] = str(vault)
    os.environ["HERMES_TASKPOOL_COMMAND_GATEWAY_DB"] = str(db_path)
    name = f"brain_task_orchestrator_gateway_test_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        if old_vault is None:
            os.environ.pop("HERMES_BRAIN_VAULT", None)
        else:
            os.environ["HERMES_BRAIN_VAULT"] = old_vault
        if old_db is None:
            os.environ.pop("HERMES_TASKPOOL_COMMAND_GATEWAY_DB", None)
        else:
            os.environ["HERMES_TASKPOOL_COMMAND_GATEWAY_DB"] = old_db
    if initialize_gateway:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        TaskpoolCommandGateway(db_path, allowed_root=db_path.parent)
    return module


def test_configured_gateway_missing_database_fails_closed_without_hiding_file_tasks():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        db_path = root / "state" / "taskpool.sqlite3"
        module = load_orchestrator(
            root / "vault", db_path, initialize_gateway=False
        )
        module.TASKS_DIR.mkdir(parents=True, exist_ok=True)
        projected = module.TASKS_DIR / "legacy.md"
        projected.write_text(
            "---\ntype: task\nstatus: pending\n---\n# Legacy\n", encoding="utf-8"
        )

        with pytest.raises(RuntimeError, match="bootstrap is required"):
            module.iter_tasks()
        assert projected.exists()
        assert not db_path.exists()


def test_projection_parent_symlink_cannot_escape_the_vault():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        db_path = root / "state" / "taskpool.sqlite3"
        module = load_orchestrator(root / "vault", db_path)
        outside = root / "outside"
        outside.mkdir()
        module.TASKS_DIR.parent.mkdir(parents=True, exist_ok=True)
        module.TASKS_DIR.symlink_to(outside, target_is_directory=True)
        escaped = module.TASKS_DIR / "task-symlink.md"

        with pytest.raises(RuntimeError, match="projection path is invalid"):
            module.save_task(
                module.Task(
                    path=escaped,
                    fm={"type": "task", "id": "task-symlink", "status": "pending"},
                    body="# Escape\n",
                )
            )
        assert not (outside / "task-symlink.md").exists()
        with sqlite3.connect(db_path) as connection:
            assert connection.execute("SELECT COUNT(*) FROM canonical_tasks").fetchone()[0] == 0


def test_projection_parent_symlink_swap_after_admission_cannot_escape_the_vault():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        vault = root / "vault"
        db_path = root / "state" / "taskpool.sqlite3"
        module = load_orchestrator(vault, db_path)
        module.TASKS_DIR.mkdir(parents=True, exist_ok=True)
        outside = root / "outside"
        outside.mkdir()
        detached = root / "detached-tasks"
        gateway = TaskpoolCommandGateway(db_path, allowed_root=db_path.parent)
        setattr(module, "_taskpool_command_gateway", lambda: gateway)
        real_publish = gateway.publish_projection

        def swap_then_publish(**kwargs):
            module.TASKS_DIR.rename(detached)
            module.TASKS_DIR.symlink_to(outside, target_is_directory=True)
            return real_publish(**kwargs)

        gateway.publish_projection = swap_then_publish
        try:
            with pytest.raises(RuntimeError, match="projection path changed"):
                module.save_task(
                    module.Task(
                        path=module.TASKS_DIR / "task-race.md",
                        fm={"type": "task", "id": "task-race", "status": "pending"},
                        body="# Race\n",
                    )
                )
            assert not (outside / "task-race.md").exists()
            with sqlite3.connect(db_path) as connection:
                assert connection.execute(
                    "SELECT status FROM projection_intents WHERE task_id='task-race'"
                ).fetchone()[0] == "pending"
        finally:
            gateway.close()


def test_canonical_projection_path_tampering_cannot_escape_the_vault():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        db_path = root / "state" / "taskpool.sqlite3"
        module = load_orchestrator(root / "vault", db_path)
        module.save_task(
            module.Task(
                path=module.TASKS_DIR / "task-escape.md",
                fm={"type": "task", "id": "task-escape", "status": "pending"},
                body="# Escape\n",
            )
        )
        with sqlite3.connect(db_path) as connection:
            connection.execute(
                "UPDATE projection_intents SET relative_path='../../escaped.md' "
                "WHERE task_id='task-escape'"
            )
            connection.commit()

        with pytest.raises(RuntimeError, match="projection path is invalid"):
            module.iter_tasks()
        assert not (root / "escaped.md").exists()


def test_save_task_admits_canonical_state_before_projection_and_retries_projection_failure():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        vault = root / "vault"
        db_path = root / "state" / "taskpool.sqlite3"
        module = load_orchestrator(vault, db_path)
        path = module.TASKS_DIR / "task-7.md"
        task = module.Task(
            path=path,
            fm={"type": "task", "id": "task-7", "status": "pending"},
            body="# Task Seven\n",
        )

        module.save_task(task)
        with sqlite3.connect(db_path) as connection:
            connection.row_factory = sqlite3.Row
            canonical = connection.execute(
                "SELECT revision,state_json FROM canonical_tasks WHERE task_id='task-7'"
            ).fetchone()
            projection = connection.execute(
                "SELECT status FROM projection_intents WHERE task_id='task-7' AND revision=1"
            ).fetchone()
            assert canonical is not None and canonical["revision"] == 1
            assert projection is not None and projection["status"] == "published"
        first_bytes = path.read_bytes()

        task.fm["status"] = "claimed"
        real_atomic_write = module.atomic_write

        def fail_projection(*_args, **_kwargs):
            raise OSError("injected projection failure")

        module.atomic_write = fail_projection
        with pytest.raises(OSError, match="injected projection failure"):
            module.save_task(task)
        assert path.read_bytes() == first_bytes
        canonical_tasks = module.iter_tasks()
        assert len(canonical_tasks) == 1
        assert canonical_tasks[0].fm["status"] == "claimed"
        with sqlite3.connect(db_path) as connection:
            assert connection.execute(
                "SELECT revision FROM canonical_tasks WHERE task_id='task-7'"
            ).fetchone()[0] == 2
            assert connection.execute(
                "SELECT status FROM projection_intents WHERE task_id='task-7' AND revision=2"
            ).fetchone()[0] == "pending"

        module.atomic_write = real_atomic_write
        module.save_task(task)
        assert "status: claimed" in path.read_text(encoding="utf-8")
        with sqlite3.connect(db_path) as connection:
            assert connection.execute("SELECT count(*) FROM canonical_tasks").fetchone()[0] == 1
            assert connection.execute("SELECT count(*) FROM command_receipts").fetchone()[0] == 2
            assert connection.execute("SELECT count(*) FROM outbox_events").fetchone()[0] == 2
            assert connection.execute(
                "SELECT status FROM projection_intents WHERE task_id='task-7' AND revision=2"
            ).fetchone()[0] == "published"


def test_create_task_note_enters_the_same_canonical_gateway_path():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        module = load_orchestrator(root / "vault", root / "state" / "taskpool.sqlite3")
        result = module.create_task_note(
            title="Gateway Creation",
            lane="advisory",
            priority_layer="P2",
            dependency_order=["1"],
            multimodel_triage_result="P3",
        )
        created = Path(result["created"])
        assert created.exists()
        canonical = module.iter_tasks()
        assert len(canonical) == 1
        assert canonical[0].id == result["id"]
        assert canonical[0].path == created


def test_dispatch_selection_uses_canonical_gateway_state_not_stale_projection_file():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        module = load_orchestrator(root / "vault", root / "state" / "taskpool.sqlite3")
        result = module.create_task_note(
            title="Gateway Dispatch Source",
            lane="advisory",
            priority_layer="P2",
            dependency_order=["1"],
            multimodel_triage_result="P3",
        )
        created = Path(result["created"])
        projected = created.read_text(encoding="utf-8")
        created.write_text(
            projected.replace("status: pending", "status: done", 1),
            encoding="utf-8",
        )

        dry_run = module.command_dispatch_dry_run(
            type("Args", (), {"json": True, "no_reconcile": True})()
        )

        assert dry_run["next"]["id"] == result["id"]
        assert dry_run["next"]["status"] == "pending"
        assert dry_run["next"]["lane"] == "advisory"


def test_execution_flow_dry_run_without_filter_uses_canonical_gateway_state_not_stale_projection_file():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        module = load_orchestrator(root / "vault", root / "state" / "taskpool.sqlite3")
        result = module.create_task_note(
            title="Gateway Flow Source",
            lane="advisory",
            priority_layer="P2",
            dependency_order=["1"],
            multimodel_triage_result="P3",
        )
        created = Path(result["created"])
        projected = created.read_text(encoding="utf-8")
        created.write_text(
            projected.replace("status: pending", "status: done", 1),
            encoding="utf-8",
        )

        payload = module.command_execution_flow_dry_run(
            type("Args", (), {"task": [], "limit": 5, "report": "", "fail_on_blocked": False})()
        )

        assert payload["summary"]["evaluated"] == 1
        assert payload["evaluations"][0]["task_id"] == result["id"]
        assert payload["evaluations"][0]["status"] == "pending"
        assert payload["evaluations"][0]["workflow_stage"] == "evidence"


def test_compound_loop_preflight_uses_canonical_gateway_state_not_stale_projection_file():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        module = load_orchestrator(root / "vault", root / "state" / "taskpool.sqlite3")
        script = root / "compound_loop_preflight.py"
        script.write_text(
            "def scan(text):\n"
            "    if 'status: done' in text:\n"
            "        return {'status': 'FAIL', 'reason': 'saw_stale_done_projection'}\n"
            "    return {'status': 'PASS', 'reason': 'canonical_pending'}\n",
            encoding="utf-8",
        )
        result = module.create_task_note(
            title="Gateway Compound Source",
            lane="advisory",
            priority_layer="P2",
            dependency_order=["1"],
            multimodel_triage_result="P3",
            concepts=["compound-agent-loop"],
        )
        created = Path(result["created"])
        projected = created.read_text(encoding="utf-8")
        created.write_text(
            projected.replace("status: pending", "status: done", 1),
            encoding="utf-8",
        )
        old_flag = os.environ.get(module.COMPOUND_LOOP_PREFLIGHT_ENV_FLAG)
        os.environ[module.COMPOUND_LOOP_PREFLIGHT_ENV_FLAG] = "1"
        old_script = getattr(module, "COMPOUND_LOOP_PREFLIGHT_SCRIPT")
        setattr(module, "COMPOUND_LOOP_PREFLIGHT_SCRIPT", script)
        try:
            payload = module.evaluate_compound_loop_preflight(module.find_task(result["id"]))
        finally:
            setattr(module, "COMPOUND_LOOP_PREFLIGHT_SCRIPT", old_script)
            if old_flag is None:
                os.environ.pop(module.COMPOUND_LOOP_PREFLIGHT_ENV_FLAG, None)
            else:
                os.environ[module.COMPOUND_LOOP_PREFLIGHT_ENV_FLAG] = old_flag

        assert payload["status"] == "PASS"
        assert payload["reason"] == "canonical_pending"


def test_task_frontmatter_writes_have_no_direct_atomic_write_bypass():
    source = SCRIPT.read_text(encoding="utf-8")
    tree = ast.parse(source)
    bypasses = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "atomic_write":
            continue
        if any(
            isinstance(child, ast.Call)
            and isinstance(child.func, ast.Name)
            and child.func.id == "render_frontmatter"
            for argument in node.args
            for child in ast.walk(argument)
        ):
            bypasses.append(node.lineno)
    assert bypasses == []
