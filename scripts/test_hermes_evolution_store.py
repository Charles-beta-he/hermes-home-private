#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import pytest

from hermes_evolution_store import EvolutionStore, classify_nightly_result
import autonomous_evolution_nightly_noagent


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


def test_noagent_wrapper_emits_warn_and_ledger_when_no_effective_progress(tmp_path, monkeypatch, capsys):
    class FakeCompleted:
        returncode = 0
        stdout = "confidence_db: /x (archived)\n= 无变化"
        stderr = ""

    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
    monkeypatch.setattr(autonomous_evolution_nightly_noagent.subprocess, "run", lambda *a, **k: FakeCompleted())

    rc = autonomous_evolution_nightly_noagent.main()
    payload = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert payload["status"] == "WARN"
    assert payload["effective_audit"] is True
    assert payload["state_advanced"] is False
    assert Path(payload["dream_run_ledger"]).exists()
