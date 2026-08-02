#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from hermes_evolution_store import EvolutionStore, classify_nightly_result
import autonomous_evolution_nightly_noagent
import upstream_ratchet_review_noagent


def load_script_module(name: str, filename: str):
    path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


refresh_dashboard = load_script_module("refresh_dashboard", "refresh-dashboard.py")


def test_write_resolution_imports_archived_to_canonical_without_mutating_archive(tmp_path):
    home = tmp_path / "hermes"
    archived_db = home / "skills-archived" / "bayesian-agent" / "confidence-db.json"
    archived_db.parent.mkdir(parents=True)
    archived_db.write_text(json.dumps({"skills": {"apple": {"darwin_score": 75}}}), encoding="utf-8")
    before = archived_db.read_text(encoding="utf-8")

    store = EvolutionStore(home)
    resolved = store.resolve_artifact("bayesian-agent/confidence-db.json", intent="write")

    assert resolved.source == "canonical"
    assert resolved.writable is True
    assert str(resolved.path).endswith("state/evolution/bayesian-agent/confidence-db.json")
    assert resolved.path.read_text(encoding="utf-8") == before
    assert archived_db.read_text(encoding="utf-8") == before
    assert any(event["event"] == "archive_imported" for event in store.read_events())


def test_missing_write_resolution_is_canonical_and_never_archived(tmp_path):
    home = tmp_path / "hermes"
    store = EvolutionStore(home)

    resolved = store.resolve_artifact("darwin-skill/results.tsv", intent="write")

    assert resolved.source == "canonical"
    assert resolved.writable is True
    assert resolved.path == home / "state" / "evolution" / "darwin-skill" / "results.tsv"
    assert str(resolved.path).find("skills-archived") == -1


def test_read_resolution_reports_archived_as_readonly_when_no_canonical(tmp_path):
    home = tmp_path / "hermes"
    archived_results = home / "skills-archived" / "darwin-skill" / "results.tsv"
    archived_results.parent.mkdir(parents=True)
    archived_results.write_text("ts\tsource\n", encoding="utf-8")

    store = EvolutionStore(home)
    resolved = store.resolve_artifact("darwin-skill/results.tsv", intent="read", import_if_missing=False)

    assert resolved.source == "archived"
    assert resolved.writable is False
    assert resolved.degraded is True
    assert resolved.reason == "archived_readonly"


def test_noagent_classification_requires_effective_progress_not_exit_zero():
    warn = classify_nightly_result(0, "confidence_db: /x (archived)\n= 无变化", "")
    assert warn["status"] == "WARN"
    assert warn["effective_audit"] is True
    assert warn["state_advanced"] is False
    assert warn["degraded"] is True

    ok = classify_nightly_result(0, "✓ 改进已保留 [B]", "")
    assert ok["status"] == "OK"
    assert ok["effective_audit"] is True
    assert ok["state_advanced"] is True

    error = classify_nightly_result(2, "", "boom")
    assert error["status"] == "ERROR"
    assert error["effective_audit"] is False


def test_noagent_wrapper_fails_closed_and_ledgers_when_receipt_absent(tmp_path, monkeypatch, capsys):
    class FakeCompleted:
        returncode = 0
        stdout = "confidence_db: /x (archived)\n= 无变化"
        stderr = ""

    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
    monkeypatch.setattr(autonomous_evolution_nightly_noagent.subprocess, "run", lambda *a, **k: FakeCompleted())

    rc = autonomous_evolution_nightly_noagent.main()
    payload = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert payload["status"] == "ERROR"
    assert payload["job_success"] is False
    assert payload["effective_audit"] is False
    assert payload["candidate_generated"] is False
    assert payload["state_advanced"] is False
    assert payload["promoted"] is False
    assert Path(payload["dream_run_ledger"]).exists()


def test_nightly_no_change_on_canonical_source_is_ok_not_cron_error():
    result = classify_nightly_result(
        0,
        "confidence_db: /state/evolution/bayesian-agent/confidence-db.json (canonical)\n"
        "darwin_results: /state/evolution/darwin-skill/results.tsv (canonical)\n"
        "评分变化: 75 → 75\n= 无变化",
        "",
    )

    assert result["status"] == "OK"
    assert result["effective_audit"] is True
    assert result["state_advanced"] is False
    assert result["degraded"] is False
    assert result["reasons"] == ["no_state_change"]


def test_refresh_dashboard_treats_canonical_evolution_store_as_active(tmp_path, monkeypatch):
    home = tmp_path / "hermes"
    db = home / "state" / "evolution" / "bayesian-agent" / "confidence-db.json"
    results = home / "state" / "evolution" / "darwin-skill" / "results.tsv"
    health = home / "notes" / "engineering-cybernetics" / "health-history.jsonl"
    for path in (db, results, health):
        path.parent.mkdir(parents=True, exist_ok=True)
    db.write_text(json.dumps({"skills": {"apple": {"darwin_score": 75, "darwin_grade": "B"}}}), encoding="utf-8")
    results.write_text("timestamp\tsource\tskill\told\tnew\tstatus\n2026\ttest\tapple\t75\t75\taccepted\n", encoding="utf-8")
    health.write_text(json.dumps({"V": 0.9, "V_dot": 0.01}) + "\n", encoding="utf-8")
    monkeypatch.setattr(refresh_dashboard, "STORE", EvolutionStore(home))
    monkeypatch.setattr(refresh_dashboard, "HEALTH_PATH", str(health))
    monkeypatch.setattr(refresh_dashboard, "DASHBOARD_PATH", str(home / "notes" / "engineering-cybernetics" / "evolution-dashboard.md"))
    refresh_dashboard.configure_sources()

    refresh_dashboard.refresh()
    dashboard = Path(refresh_dashboard.DASHBOARD_PATH).read_text(encoding="utf-8")

    assert "Status: ✅ OK" in dashboard
    assert "降级读取" not in dashboard


def test_upstream_classification_and_redaction_helpers():
    assert upstream_ratchet_review_noagent.classify_nonzero(
        "WatchError: unexpected branch 'feat/demo'; expected private/main or integrate/*"
    ) == "skipped_unexpected_branch"
    assert upstream_ratchet_review_noagent.classify_nonzero("network failed") is None

    redacted = upstream_ratchet_review_noagent.safe_tail(
        "token=PLACEHOLDER_VALUE password:PLACEHOLDER_PASSWORD https://example.com/repo.git"
    )
    assert "PLACEHOLDER_VALUE" not in redacted
    assert "PLACEHOLDER_PASSWORD" not in redacted
    assert "[REDACTED]" in redacted


def test_upstream_noagent_skips_unexpected_work_branch_without_cron_error(tmp_path, monkeypatch, capsys):
    class FakeCompleted:
        returncode = 1
        stdout = ""
        stderr = "unexpected branch 'feat/demo'; expected private/main or integrate/*"

    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
    monkeypatch.setattr(upstream_ratchet_review_noagent.subprocess, "run", lambda *a, **k: FakeCompleted())

    rc = upstream_ratchet_review_noagent.main()

    assert rc == 0
    assert capsys.readouterr().out == ""
    log_path = tmp_path / "hermes" / "logs" / "upstream-ratchet-review-events.jsonl"
    payload = json.loads(log_path.read_text(encoding="utf-8").splitlines()[-1])
    assert payload["status"] == "skipped_unexpected_branch"
