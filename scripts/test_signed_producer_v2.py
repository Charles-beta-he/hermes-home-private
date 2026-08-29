#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REAL_SUBPROCESS_RUN = subprocess.run

HERE = Path(__file__).resolve().parent
ORCHESTRATOR = HERE / "brain_task_orchestrator.py"
RUNNER = HERE / "taskpool_dynamic_runner.py"
OBSERVER = Path("/Users/charles/.hermes/workflows/projects/hermes-cron-portfolio-governance/e5-shadow/taskpool_shadow_observer.py")


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def partial_summary() -> dict:
    return {"status": "OK", "next_task_id": "task-7", "dispatchable": True}


def complete_summary() -> dict:
    return {
        "status": "OK",
        "next_task_id": "task-7",
        "dispatchable": True,
        "error_count": 0,
        "reconcile_action_count": 2,
        "ingested_count": 3,
        "multimodel_intervention": {"task_id": "mm-4", "queued_count": 5},
        "auto_close_review": {"closed_count": 6, "error_count": 7},
    }


def test_event_v2_normalizes_complete_defaults_and_matches_strict_observer_signature():
    producer = load(ORCHESTRATOR, "event_v2_producer_defaults")
    observer = load(OBSERVER, "strict_observer_event_signature")

    receipt = producer.build_event_hook_v2_receipt(
        event="task_created",
        task_id="task-7",
        started_at="2026-08-29T01:02:03+00:00",
        finished_at="2026-08-29T01:02:04+00:00",
        returncode=0,
        summary=partial_summary(),
    )

    assert receipt["schema"] == "taskpool_event_hook_receipt_v2"
    assert receipt["summary"] == {
        "status": "OK",
        "next_task_id": "task-7",
        "dispatchable": True,
        "error_count": 0,
        "reconcile_action_count": 0,
        "ingested_count": 0,
        "multimodel_intervention": {"task_id": "", "queued_count": 0},
        "auto_close_review": {"closed_count": 0, "error_count": 0},
    }
    assert receipt["signature"] == observer.event_signature(receipt)
    assert observer.normalize_event_receipt(receipt, source="memory")["producer_signature_verifiable"] is True


def test_event_v2_tamper_is_rejected_by_strict_observer():
    producer = load(ORCHESTRATOR, "event_v2_producer_tamper")
    observer = load(OBSERVER, "strict_observer_event_tamper")
    receipt = producer.build_event_hook_v2_receipt(
        event="task_created", task_id="task-7",
        started_at="2026-08-29T01:02:03+00:00", finished_at="2026-08-29T01:02:04+00:00",
        returncode=0, summary=complete_summary(),
    )
    receipt["summary"]["ingested_count"] += 1

    with pytest.raises(ValueError, match="signature mismatch"):
        observer.normalize_event_receipt(receipt, source="memory")


def test_event_v2_atomic_sidecar_is_distinct_and_preserves_legacy_bytes(tmp_path: Path):
    producer = load(ORCHESTRATOR, "event_v2_producer_atomic")
    legacy = tmp_path / "event-20260829010203-task-7.json"
    legacy_bytes = b'{"legacy":true}\n'
    legacy.write_bytes(legacy_bytes)
    payload = {
        "status": "OK", "event": "task_created", "task_id": "task-7",
        "started_at": "2026-08-29T01:02:03+00:00", "finished_at": "2026-08-29T01:02:04+00:00",
        "returncode": 0, "summary": partial_summary(),
    }

    sidecar = producer.publish_event_hook_v2_receipt(payload, legacy)

    assert sidecar == tmp_path / "event-v2-20260829010203-task-7.json"
    assert legacy.read_bytes() == legacy_bytes
    assert json.loads(sidecar.read_text(encoding="utf-8"))["schema"] == "taskpool_event_hook_receipt_v2"
    assert sorted(path.name for path in tmp_path.iterdir()) == [legacy.name, sidecar.name]


def test_event_v2_error_timeout_and_invalid_summary_publish_nothing(tmp_path: Path):
    producer = load(ORCHESTRATOR, "event_v2_producer_fail_closed")
    legacy = tmp_path / "event-20260829010203-task-7.json"
    cases = [
        {"status": "ERROR", "returncode": 2, "summary": complete_summary()},
        {"status": "TIMEOUT", "returncode": "timeout", "summary": complete_summary()},
        {"status": "OK", "returncode": 0, "summary": {}},
        {"status": "OK", "returncode": 0, "summary": "not-an-object"},
    ]
    for payload in cases:
        payload.update({
            "event": "task_created", "task_id": "task-7",
            "started_at": "2026-08-29T01:02:03+00:00", "finished_at": "2026-08-29T01:02:04+00:00",
        })
        assert producer.publish_event_hook_v2_receipt(payload, legacy) is None
    assert list(tmp_path.iterdir()) == []


def test_event_hook_success_writes_legacy_and_v2_but_failed_process_writes_only_legacy(tmp_path: Path):
    producer = load(ORCHESTRATOR, "event_v2_hook_integration")
    producer.AUTORUN_STATE_DIR = tmp_path
    producer.maybe_append_taskpool_mission_signal = lambda *args, **kwargs: {"status": "SKIPPED"}
    producer.event_hook_multimodel_route = lambda *args, **kwargs: {"enabled": False}
    producer.event_hook_agent_layer_route = lambda *args, **kwargs: {"enabled": False}
    producer.subprocess.run = lambda *args, **kwargs: SimpleNamespace(
        returncode=0, stdout=json.dumps(partial_summary()), stderr="",
    )

    ok = producer.maybe_fire_taskpool_event_hook("task_created", task_id="task-7")
    event_dir = tmp_path / "taskpool_event_hooks"
    assert Path(ok["log"]).exists()
    assert Path(ok["v2_log"]).exists()
    assert len(list(event_dir.glob("event-*.json"))) == 2
    assert len(list(event_dir.glob("event-v2-*.json"))) == 1

    producer.subprocess.run = lambda *args, **kwargs: SimpleNamespace(
        returncode=2, stdout=json.dumps(complete_summary()), stderr="failed",
    )
    failed = producer.maybe_fire_taskpool_event_hook("task_failed", task_id="task-8")
    assert failed["status"] == "ERROR"
    assert failed["v2_log"] is None
    assert len(list(event_dir.glob("event-v2-*.json"))) == 1


def test_cron_v2_complete_record_matches_distinct_strict_observer_contract_and_rejects_tamper():
    producer = load(RUNNER, "cron_v2_producer_signature")
    observer = load(OBSERVER, "strict_observer_cron_signature")

    record = producer.build_dynamic_runner_v2_record("2026-08-29T01:02:03Z", partial_summary())

    assert record["schema"] == "taskpool_dynamic_runner_v2"
    assert record["summary"]["auto_close_review"] == {"closed_count": 0, "error_count": 0}
    assert record["signature"] == observer.runner_signature(record["summary"])
    assert observer.normalize_cron_record(record, source="memory")["producer_signature_verifiable"] is True
    record["summary"]["auto_close_review"]["closed_count"] = 99
    with pytest.raises(ValueError, match="signature mismatch"):
        observer.normalize_cron_record(record, source="memory")


def test_cron_v2_append_is_distinct_and_legacy_append_is_unchanged(tmp_path: Path):
    producer = load(RUNNER, "cron_v2_producer_append")
    legacy = tmp_path / "taskpool_dynamic_runner.jsonl"
    v2 = tmp_path / "taskpool_dynamic_runner_v2.jsonl"
    producer.LOG = legacy
    producer.V2_LOG = v2
    old = {"schema": "taskpool_dynamic_runner_v1", "ts": "2026-08-29T01:02:03Z", "summary": partial_summary()}

    producer.append(old)
    assert producer.append_dynamic_runner_v2("2026-08-29T01:02:03Z", partial_summary()) is True

    assert json.loads(legacy.read_text(encoding="utf-8"))["schema"] == "taskpool_dynamic_runner_v1"
    row = json.loads(v2.read_text(encoding="utf-8"))
    assert row["schema"] == "taskpool_dynamic_runner_v2"
    assert set(row["summary"]) == {
        "status", "next_task_id", "dispatchable", "error_count", "reconcile_action_count",
        "ingested_count", "multimodel_intervention", "auto_close_review",
    }
    assert producer.append_dynamic_runner_v2("2026-08-29T01:02:04Z", {}) is False
    assert len(v2.read_text(encoding="utf-8").splitlines()) == 1


def test_event_v2_sidecar_failure_does_not_change_legacy_hook_result(tmp_path: Path):
    producer = load(ORCHESTRATOR, "event_v2_sidecar_failure")
    producer.AUTORUN_STATE_DIR = tmp_path
    producer.maybe_append_taskpool_mission_signal = lambda *args, **kwargs: {"status": "SKIPPED"}
    producer.event_hook_multimodel_route = lambda *args, **kwargs: {"enabled": False}
    producer.event_hook_agent_layer_route = lambda *args, **kwargs: {"enabled": False}
    producer.subprocess.run = lambda *args, **kwargs: SimpleNamespace(
        returncode=0, stdout=json.dumps(partial_summary()), stderr="",
    )
    producer.publish_event_hook_v2_receipt = lambda *args, **kwargs: (_ for _ in ()).throw(OSError("v2 unavailable"))

    result = producer.maybe_fire_taskpool_event_hook("task_created", task_id="task-7")

    assert result["status"] == "OK"
    assert Path(result["log"]).exists()
    assert result["v2_log"] is None


def test_cron_main_preserves_v1_when_v2_lane_write_fails(tmp_path: Path):
    producer = load(RUNNER, "cron_v2_write_failure")
    producer.STATE = tmp_path / "state.json"
    producer.LOG = tmp_path / "taskpool_dynamic_runner.jsonl"
    producer.V2_LOG = tmp_path / "missing" / "taskpool_dynamic_runner_v2.jsonl"
    producer.LOCK = tmp_path / "runner.pid"
    producer.load_taskpool_dispatch_mode = lambda: "single"
    producer.human_escape_status = lambda: {"status": "OK", "triggered": True, "info": {}}
    producer.append_dynamic_runner_v2 = lambda *args, **kwargs: (_ for _ in ()).throw(OSError("v2 unavailable"))

    assert producer.main() == 0
    assert json.loads(producer.LOG.read_text(encoding="utf-8"))["schema"] == "taskpool_dynamic_runner_v1"


def test_v2_rejects_error_and_type_confused_summaries():
    event_producer = load(ORCHESTRATOR, "event_v2_reject_bad_summary")
    cron_producer = load(RUNNER, "cron_v2_reject_bad_summary")
    bad = [
        {**complete_summary(), "status": "ERROR"},
        {**complete_summary(), "error_count": 1},
        {**complete_summary(), "dispatchable": "false"},
        {**complete_summary(), "next_task_id": 7},
        {**complete_summary(), "reconcile_action_count": -1},
        {**complete_summary(), "ingested_count": True},
        {**complete_summary(), "auto_close_review": "malformed"},
        {**complete_summary(), "multimodel_intervention": []},
    ]
    for summary_value in bad:
        with pytest.raises(ValueError):
            event_producer.build_event_hook_v2_receipt(
                event="task_created", task_id="task-7", started_at="2026-08-29T01:02:03+00:00",
                finished_at="2026-08-29T01:02:04+00:00", returncode=0, summary=summary_value,
            )
        with pytest.raises(ValueError):
            cron_producer.build_dynamic_runner_v2_record("2026-08-29T01:02:03Z", summary_value)


def test_cron_signature_covers_auto_close_error_count():
    producer = load(RUNNER, "cron_v2_complete_signature")
    observer = load(OBSERVER, "strict_observer_complete_signature")
    record = producer.build_dynamic_runner_v2_record("2026-08-29T01:02:03Z", complete_summary())
    record["summary"]["auto_close_review"]["error_count"] += 1
    with pytest.raises(ValueError, match="signature mismatch"):
        observer.normalize_cron_record(record, source="memory")


def test_observer_rejects_re_signed_type_confusion():
    producer = load(RUNNER, "cron_v2_resigned_type_confusion")
    observer = load(OBSERVER, "strict_observer_resigned_type_confusion")
    record = producer.build_dynamic_runner_v2_record("2026-08-29T01:02:03Z", complete_summary())
    for field, bad_value in (("dispatchable", "false"), ("error_count", True), ("next_task_id", 7)):
        tampered = json.loads(json.dumps(record))
        tampered["summary"][field] = bad_value
        tampered["signature"] = producer.dynamic_runner_v2_signature(tampered["summary"])
        with pytest.raises(ValueError, match="invalid summary"):
            observer.normalize_cron_record(tampered, source="memory")


def test_event_v2_requires_distinct_nonexistent_sidecar(tmp_path: Path):
    producer = load(ORCHESTRATOR, "event_v2_distinct_path")
    payload = {
        "status": "OK", "event": "task_created", "task_id": "task-7", "returncode": 0,
        "started_at": "2026-08-29T01:02:03+00:00", "finished_at": "2026-08-29T01:02:04+00:00",
        "summary": partial_summary(),
    }
    malformed = tmp_path / "legacy.json"
    malformed.write_text("legacy", encoding="utf-8")
    with pytest.raises(ValueError, match="event-"):
        producer.publish_event_hook_v2_receipt(payload, malformed)
    legacy = tmp_path / "event-20260829010203-task-7.json"
    legacy.write_text("legacy", encoding="utf-8")
    sidecar = tmp_path / "event-v2-20260829010203-task-7.json"
    sidecar.symlink_to(malformed)
    with pytest.raises(FileExistsError):
        producer.publish_event_hook_v2_receipt(payload, legacy)
    assert malformed.read_text(encoding="utf-8") == "legacy"


def test_cron_v2_partial_write_rolls_back_and_symlink_is_rejected(tmp_path: Path, monkeypatch):
    producer = load(RUNNER, "cron_v2_atomic_append")
    producer.V2_LOG = tmp_path / "taskpool_dynamic_runner_v2.jsonl"
    real_write = producer.os.write
    calls = {"count": 0}
    def partial_then_fail(fd, data):
        calls["count"] += 1
        if calls["count"] == 1:
            real_write(fd, data[:19])
            raise OSError("injected partial write")
        return real_write(fd, data)
    monkeypatch.setattr(producer.os, "write", partial_then_fail)
    with pytest.raises(OSError, match="partial"):
        producer.append_dynamic_runner_v2("2026-08-29T01:02:03Z", partial_summary())
    assert producer.V2_LOG.read_bytes() == b""
    victim = tmp_path / "victim"
    victim.write_bytes(b"safe")
    producer.V2_LOG.unlink()
    producer.V2_LOG.symlink_to(victim)
    with pytest.raises(OSError):
        producer.append_dynamic_runner_v2("2026-08-29T01:02:03Z", partial_summary())
    assert victim.read_bytes() == b"safe"


def test_cron_lock_survives_canonical_file_replacement(tmp_path: Path):
    producer = load(RUNNER, "cron_v2_lock_owner")
    producer.LOCK = tmp_path / "runner.lock"
    assert producer.acquire_lock() is True
    try:
        producer.LOCK.rename(tmp_path / "runner.lock.moved")
        producer.LOCK.write_text("replacement", encoding="utf-8")
        code = (
            "import importlib.util,sys; from pathlib import Path; "
            f"p=Path({str(RUNNER)!r}); s=importlib.util.spec_from_file_location('contender',p); "
            "m=importlib.util.module_from_spec(s); sys.modules['contender']=m; s.loader.exec_module(m); "
            f"m.LOCK=Path({str(tmp_path / 'runner.lock')!r}); "
            "print('ACQUIRED' if m.acquire_lock() else 'BLOCKED')"
        )
        result = REAL_SUBPROCESS_RUN([sys.executable, "-c", code], capture_output=True, text=True, timeout=10)
        assert result.returncode == 0
        assert result.stdout.strip() == "BLOCKED"
    finally:
        producer.release_lock()


def test_cron_main_preserves_v1_and_adds_v2_on_valid_preclaim_summary(tmp_path: Path):
    producer = load(RUNNER, "cron_v2_main_integration")
    producer.STATE = tmp_path / "state.json"
    producer.LOG = tmp_path / "taskpool_dynamic_runner.jsonl"
    producer.V2_LOG = tmp_path / "taskpool_dynamic_runner_v2.jsonl"
    producer.LOCK = tmp_path / "runner.pid"
    producer.load_taskpool_dispatch_mode = lambda: "single"
    producer.human_escape_status = lambda: {"status": "OK", "triggered": True, "info": {}}

    assert producer.main() == 0

    legacy = json.loads(producer.LOG.read_text(encoding="utf-8"))
    v2 = json.loads(producer.V2_LOG.read_text(encoding="utf-8"))
    assert legacy["schema"] == "taskpool_dynamic_runner_v1"
    assert v2["schema"] == "taskpool_dynamic_runner_v2"
    assert v2["summary"]["auto_close_review"] == {"closed_count": 0, "error_count": 0}
