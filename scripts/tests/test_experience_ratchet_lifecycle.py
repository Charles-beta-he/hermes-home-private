#!/usr/bin/env python3
"""Behavior tests for explicit Experience Ratchet lifecycle reconciliation."""
from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPT = Path.home() / ".hermes" / "scripts" / "experience_ratchet_lifecycle.py"


def load_module():
    spec = importlib.util.spec_from_file_location("experience_ratchet_lifecycle", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def iso(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def atom(atom_id: str, status: str, at: str, *, failures: int = 0) -> dict:
    return {
        "schema_version": "experience_atom.v1",
        "atom_id": atom_id,
        "title": atom_id,
        "claim_text": f"claim {atom_id}",
        "source": {"project": "lifecycle-test", "captured_at": at},
        "classification": {"target_landing_zone": "noop"},
        "guards": {"applicability_conditions": [], "anti_conditions": ["test-only"], "falsifiers": ["counterexample"]},
        "evidence_refs": [{"kind": "test", "ref": "fixture"}],
        "dissent_refs": [],
        "relations": [],
        "status": status,
        "promotion": {"state": "candidate" if status == "promoted_candidate" else "promoted" if status == "promoted" else "none"},
        "rollback": {"revoked_reason": None},
        "metrics": {"failure_count": failures},
        "history": [{"at": at, "event": f"fixture:{status}", "reason": "test fixture"}],
    }


def write_atom(home: Path, payload: dict) -> Path:
    path = home / "atoms" / f"{payload['atom_id']}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def test_apply_demotes_stale_reopens_failures_and_applies_audit_retention(tmp_path):
    mod = load_module()
    now = datetime(2026, 7, 10, tzinfo=timezone.utc)
    old = iso(now - timedelta(days=45))
    stale_path = write_atom(tmp_path, atom("stale", "promoted_candidate", old))
    failed_path = write_atom(tmp_path, atom("failed", "promoted", iso(now - timedelta(days=1)), failures=2))
    retained_path = write_atom(tmp_path, atom("retained", "revoked", old))
    before = {p.name: json.loads(p.read_text(encoding="utf-8"))["history"] for p in (stale_path, failed_path, retained_path)}

    result = mod.reconcile_store(
        tmp_path,
        now=now,
        stale_days=14,
        failure_threshold=1,
        retention_days=30,
        apply=True,
    )

    assert result["ok"] is True
    assert result["mode"] == "apply"
    assert result["summary"] == {
        "atoms_checked": 3,
        "stale_demoted": 1,
        "failure_reopened": 1,
        "retention_applied": 1,
        "promotion_actions": 0,
        "history_erased": 0,
    }
    stale = json.loads(stale_path.read_text(encoding="utf-8"))
    failed = json.loads(failed_path.read_text(encoding="utf-8"))
    retained = json.loads(retained_path.read_text(encoding="utf-8"))
    assert stale["status"] == "validated"
    assert failed["status"] == "deprecated"
    assert stale["promotion"]["state"] == "none"
    assert stale["promotion"]["previous_state"] == "candidate"
    assert failed["promotion"]["state"] == "none"
    assert failed["promotion"]["previous_state"] == "promoted"
    assert failed["lifecycle"]["review_state"] == "reopened_after_failure"
    assert retained["retention"]["state"] == "retained_for_audit"
    assert retained["retention"]["deletion_permitted"] is False
    for path, payload in ((stale_path, stale), (failed_path, failed), (retained_path, retained)):
        assert payload["history"][: len(before[path.name])] == before[path.name]


def test_dry_run_is_read_only_and_reports_same_planned_actions(tmp_path):
    mod = load_module()
    now = datetime(2026, 7, 10, tzinfo=timezone.utc)
    path = write_atom(tmp_path, atom("stale", "promoted_candidate", iso(now - timedelta(days=45))))
    original = path.read_bytes()

    result = mod.reconcile_store(tmp_path, now=now, stale_days=14, apply=False)

    assert result["mode"] == "dry_run"
    assert result["summary"]["stale_demoted"] == 1
    assert path.read_bytes() == original


def test_second_apply_is_idempotent_for_retention_and_does_not_promote(tmp_path):
    mod = load_module()
    now = datetime(2026, 7, 10, tzinfo=timezone.utc)
    write_atom(tmp_path, atom("retained", "revoked", iso(now - timedelta(days=45))))

    first = mod.reconcile_store(tmp_path, now=now, retention_days=30, apply=True)
    second = mod.reconcile_store(tmp_path, now=now + timedelta(minutes=1), retention_days=30, apply=True)

    assert first["summary"]["retention_applied"] == 1
    assert second["summary"]["retention_applied"] == 0
    assert second["summary"]["promotion_actions"] == 0
    assert second["summary"]["history_erased"] == 0


def test_malformed_failure_counters_fail_closed_without_mutation(tmp_path):
    mod = load_module()
    now = datetime(2026, 7, 10, tzinfo=timezone.utc)

    for index, malformed in enumerate(("not-an-int", True, -1, [], {})):
        payload = atom(f"malformed-{index}", "promoted", iso(now - timedelta(days=1)))
        payload["metrics"]["failure_count"] = malformed
        path = write_atom(tmp_path, payload)
        original = path.read_bytes()

        actions = mod.plan_actions(
            payload,
            now=now,
            stale_days=14,
            failure_threshold=1,
            retention_days=30,
        )
        assert actions == [{
            "action": "invalid_atom",
            "from": "promoted",
            "to": "promoted",
            "reason": "failure_count must be a nonnegative non-boolean integer",
        }]

        result = mod.reconcile_store(tmp_path, now=now, apply=True)
        decision = next(item for item in result["decisions"] if item["atom_id"] == payload["atom_id"])
        assert result["ok"] is False
        assert decision["actions"] == actions
        assert path.read_bytes() == original
        assert result["side_effects_observed"] == ["local_read"]
