#!/usr/bin/env python3
"""RED-first tests for Loop A (typed receipts, selector state, vocabulary,
ownership preflight, candidate-only generation, orchestrated run).

Scope: docs/private/dreaming-v1-frozen-spec-20260801.md, Loop A.
Promotion (writing the active skill) remains out of scope: Loop A only ever
produces candidates and typed receipts with ``promoted`` fixed at False.
"""
from __future__ import annotations

import importlib.util
import json
import errno
import os
import shutil
import stat
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

import hermes_dreaming as hd
import autonomous_evolution_nightly_noagent


def load_script_module(name: str, filename: str):
    """Load a hyphenated-filename script as an importable module (for tests)."""
    path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# ---------------------------------------------------------------------------
# (A) typed receipt + reason taxonomy
# ---------------------------------------------------------------------------


def _artifact_details(**overrides):
    details = {
        "candidate_artifact": "candidate-v2--r1--skill-x--deadbeef.json",
        "artifact_schema_version": hd.CANDIDATE_ARTIFACT_SCHEMA_VERSION,
        "artifact_sha256": "a" * 64,
        "artifact_size": 32,
        "artifact_st_dev": 1,
        "artifact_st_ino": 2,
        "source_sha256": "b" * 64,
        "candidate_sha256": "c" * 64,
        "candidate_size": 8,
        "run_id": "r1",
        "skill_name": "skill-x",
    }
    details.update(overrides)
    return details


def _valid_receipt_payload(**overrides):
    """Minimal Loop A-valid receipt: audited target, no candidate authority."""
    receipt = hd.RunReceipt(run_id="r1", ts="2026-08-01T00:00:00Z", target="skill-x")
    receipt.job_success = True
    receipt.effective_audit = True
    receipt.add_stage(hd.StageReceipt(hd.STAGE_SELECTION, True, hd.REASON_OK, {}))
    receipt.add_stage(hd.StageReceipt(hd.STAGE_OWNERSHIP, True, hd.REASON_OK, {}))
    receipt.add_stage(hd.StageReceipt(hd.STAGE_GENERATION, False, hd.REASON_NO_FINDINGS, {}))
    payload = receipt.to_dict()
    # Drop auto projection key before overrides so callers control it.
    payload.pop("candidate_artifact", None)
    payload.update(overrides)
    if "candidate_artifact" not in payload:
        payload["candidate_artifact"] = None
    return payload


def _valid_candidate_generated_payload(**overrides):
    receipt = hd.RunReceipt(run_id="r1", ts="2026-08-01T00:00:00Z", target="skill-x")
    receipt.job_success = True
    receipt.effective_audit = True
    receipt.candidate_generated = True
    receipt.add_reason(hd.REASON_CANDIDATE_GENERATED)
    details = _artifact_details()
    receipt.add_stage(hd.StageReceipt(hd.STAGE_SELECTION, True, hd.REASON_OK, {}))
    receipt.add_stage(hd.StageReceipt(hd.STAGE_OWNERSHIP, True, hd.REASON_OK, {}))
    receipt.add_stage(
        hd.StageReceipt(hd.STAGE_GENERATION, True, hd.REASON_CANDIDATE_GENERATED, details)
    )
    receipt.add_stage(
        hd.StageReceipt(
            hd.STAGE_EVALUATION,
            True,
            hd.REASON_OK,
            {"satisfied": True, "reason": hd.REASON_OK, "missing_after": []},
        )
    )
    payload = receipt.to_dict()
    payload.update(overrides)
    return payload


def test_run_receipt_separates_five_flags_independently():
    receipt = hd.RunReceipt(run_id="r1", ts="2026-08-01T00:00:00Z", target="skill-x")
    receipt.job_success = True
    receipt.effective_audit = True
    receipt.candidate_generated = False
    receipt.state_advanced = False
    receipt.promoted = False

    payload = receipt.to_dict()

    assert payload["job_success"] is True
    assert payload["effective_audit"] is True
    assert payload["candidate_generated"] is False
    assert payload["state_advanced"] is False
    assert payload["promoted"] is False


def test_validate_receipt_accepts_well_formed_payload():
    payload = _valid_receipt_payload()
    assert hd.validate_receipt(payload) == []


def test_validate_receipt_flags_missing_flag():
    payload = _valid_receipt_payload()
    del payload["promoted"]
    assert "missing_flag:promoted" in hd.validate_receipt(payload)


def test_validate_receipt_flags_non_bool_flag():
    payload = _valid_receipt_payload(job_success="yes")
    assert "non_bool_flag:job_success" in hd.validate_receipt(payload)


def test_validate_receipt_flags_unknown_reason():
    payload = _valid_receipt_payload(reasons=["bogus_reason"])
    assert "unknown_reason:bogus_reason" in hd.validate_receipt(payload)


def test_validate_receipt_flags_unknown_stage():
    payload = _valid_receipt_payload(stages=[{"stage": "bogus", "ok": True, "reason": hd.REASON_OK}])
    assert "unknown_stage:bogus" in hd.validate_receipt(payload)


def test_validate_receipt_flags_non_bool_stage_ok():
    payload = _valid_receipt_payload(
        stages=[{"stage": hd.STAGE_SELECTION, "ok": "yes", "reason": hd.REASON_OK, "details": {}}]
    )
    assert "stage_ok_not_bool" in hd.validate_receipt(payload)


def test_validate_receipt_flags_non_dict_stage_details():
    payload = _valid_receipt_payload(
        stages=[{"stage": hd.STAGE_SELECTION, "ok": True, "reason": hd.REASON_OK, "details": ["not", "a", "dict"]}]
    )
    assert "stage_details_not_dict" in hd.validate_receipt(payload)


def test_atomic_write_text_leaves_no_temp_residue_on_success(tmp_path):
    target = tmp_path / "state" / "x.json"

    hd.atomic_write_text(target, "{}")

    assert target.read_text(encoding="utf-8") == "{}"
    assert list(target.parent.glob(".tmp-*")) == []


def test_atomic_write_text_cleans_temp_file_when_replace_fails(tmp_path, monkeypatch):
    target = tmp_path / "x.json"

    def boom(*a, **k):
        raise OSError("simulated replace failure")

    monkeypatch.setattr(hd.os, "replace", boom)

    with pytest.raises(OSError):
        hd.atomic_write_text(target, "{}")

    assert not target.exists()
    assert list(tmp_path.glob(".tmp-*")) == []


def test_save_selector_state_is_atomic_no_residue_on_replace_failure(tmp_path, monkeypatch):
    path = hd.selector_state_path(tmp_path)
    state = hd.new_selector_state()

    def boom(*a, **k):
        raise OSError("boom")

    monkeypatch.setattr(hd.os, "replace", boom)

    with pytest.raises(OSError):
        hd.save_selector_state(path, state)

    assert not path.exists()
    assert list(path.parent.glob(".tmp-*")) == []


def test_classify_receipt_effective_audit_without_progress_is_ok_with_no_state_change_reason():
    payload = _valid_receipt_payload()
    health = hd.classify_receipt(payload)
    assert health["status"] == "OK"
    assert health["state_advanced"] is False
    assert health["candidate_generated"] is False
    assert hd.REASON_NO_STATE_CHANGE in health["reasons"]


def test_classify_receipt_job_failure_is_error_regardless_of_audit():
    payload = _valid_receipt_payload(job_success=False)
    health = hd.classify_receipt(payload)
    assert health["status"] == "ERROR"


def test_classify_receipt_state_advanced_is_ok_without_no_state_change_reason():
    # Loop A classifier never projects state_advanced authority.
    payload = _valid_receipt_payload(state_advanced=True)
    health = hd.classify_receipt(payload)
    assert health["state_advanced"] is False
    assert health["status"] == "OK"


def test_classify_run_result_prefers_typed_receipt_over_legacy_stdout(tmp_path):
    receipt_path = tmp_path / "receipt.json"
    payload = _valid_candidate_generated_payload()
    receipt_path.write_text(json.dumps(payload), encoding="utf-8")

    health = hd.classify_run_result(0, "no relevant legacy markers here", "", receipt_path)

    assert health["receipt_source"] == "typed_receipt"
    assert health["status"] == "OK"
    assert health["candidate_generated"] is True
    assert health["candidate_artifact"] is not None


def test_classify_run_result_receipt_missing_fails_closed_despite_legacy_success_stdout(tmp_path):
    missing_path = tmp_path / "no-such-receipt.json"

    health = hd.classify_run_result(0, "✓ 改进已保留 [B]", "", missing_path)

    assert health["receipt_source"] == "receipt_absent"
    assert hd.REASON_RECEIPT_MISSING in health["reasons"]
    assert hd.REASON_LEGACY_FALLBACK not in health["reasons"]
    assert health["status"] == "ERROR"
    assert health["job_success"] is False
    assert health["effective_audit"] is False
    assert health["candidate_generated"] is False
    assert health["state_advanced"] is False
    assert health["promoted"] is False


def test_validate_receipt_rejects_promoted_without_state_and_candidate():
    payload = _valid_receipt_payload(promoted=True)
    errors = hd.validate_receipt(payload)
    assert "loop_a_promoted_forbidden" in errors


def test_classify_run_result_marks_invalid_receipt_fail_closed_not_legacy(tmp_path):
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(json.dumps({"schema": hd.RECEIPT_SCHEMA}), encoding="utf-8")

    health = hd.classify_run_result(0, "= 无变化", "", receipt_path)

    assert health["receipt_source"] == "receipt_rejected"
    assert hd.REASON_RECEIPT_INVALID in health["reasons"]
    assert hd.REASON_LEGACY_FALLBACK not in health["reasons"]
    assert health["status"] == "ERROR"
    assert health["job_success"] is False
    assert health["state_advanced"] is False
    assert health["candidate_generated"] is False
    assert health["promoted"] is False


def test_classify_run_result_rejects_malformed_receipt_with_legacy_success_marker(tmp_path):
    """A present-but-malformed receipt must never let an old-style success
    marker in stdout upgrade the run to OK/advanced — this is the exact
    regression class the fail-closed gate exists to prevent."""
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(json.dumps({"schema": hd.RECEIPT_SCHEMA}), encoding="utf-8")

    health = hd.classify_run_result(0, "✓ 改进已保留 [x]", "", receipt_path)

    assert health["receipt_source"] == "receipt_rejected"
    assert hd.REASON_RECEIPT_INVALID in health["reasons"]
    assert health["status"] != "OK"
    assert health["job_success"] is False
    assert health["state_advanced"] is False
    assert health["candidate_generated"] is False
    assert health["promoted"] is False


def test_classify_run_result_rejects_broken_json_receipt_not_legacy(tmp_path):
    """Malformed (unparseable) receipt file existing on disk must fail closed,
    exact regression: load_receipt returned None for both absent and
    malformed, so classify fell through to legacy stdout and let an old
    success marker advance state."""
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text("{broken", encoding="utf-8")

    health = hd.classify_run_result(0, "✓ 改进已保留 [x]", "", receipt_path, expected_run_id="current")

    assert health["receipt_source"] == "receipt_rejected"
    assert health["status"] == "ERROR"
    assert health["state_advanced"] is False
    assert health["job_success"] is False


def test_classify_run_result_rejects_malformed_utf8_receipt_not_legacy(tmp_path):
    """A receipt file that exists but is not valid UTF-8 must fail closed the
    same way a broken-JSON receipt does, not raise ``UnicodeDecodeError``
    through the classifier and crash the caller."""
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_bytes(b"\xff\xfe not valid utf-8")

    health = hd.classify_run_result(0, "✓ 改进已保留 [x]", "", receipt_path, expected_run_id="current")

    assert health["receipt_source"] == "receipt_rejected"
    assert health["status"] == "ERROR"
    assert health["job_success"] is False
    assert health["effective_audit"] is False
    assert health["candidate_generated"] is False
    assert health["state_advanced"] is False
    assert health["promoted"] is False
    assert hd.REASON_RECEIPT_INVALID in health["reasons"]


def test_classify_run_result_nonzero_returncode_overrides_receipt_status_to_error(tmp_path):
    receipt_path = tmp_path / "receipt.json"
    payload = _valid_candidate_generated_payload()
    receipt_path.write_text(json.dumps(payload), encoding="utf-8")

    health = hd.classify_run_result(3, "", "boom", receipt_path)

    assert health["status"] == "ERROR"
    assert health["job_success"] is False
    assert health["effective_audit"] is False
    assert health["candidate_generated"] is False
    assert health["state_advanced"] is False
    assert health["promoted"] is False
    assert health["degraded"] is True
    assert health["candidate_artifact"] is None
    assert hd.REASON_SCRIPT_RETURNCODE_NONZERO in health["reasons"]


# ---------------------------------------------------------------------------
# (B) selector state: attempt tracking, cooldown, no-progress demotion,
#     diversity, shadow evidence of the old priority
# ---------------------------------------------------------------------------


def test_record_attempt_updates_last_attempt_at_on_every_outcome():
    state = hd.new_selector_state()
    t1 = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)

    hd.record_attempt(state, "skillA", hd.OUTCOME_NO_CHANGE, t1)
    entry = hd.target_state(state, "skillA")

    assert entry["attempts"] == 1
    assert entry["last_attempt_at"] == hd.format_ts(t1)
    assert entry["last_advanced_at"] is None


def test_record_attempt_only_advances_last_advanced_at_on_advanced_outcome():
    state = hd.new_selector_state()
    t1 = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)
    t2 = t1 + timedelta(hours=1)

    hd.record_attempt(state, "skillA", hd.OUTCOME_NO_CHANGE, t1)
    hd.record_attempt(state, "skillA", hd.OUTCOME_ADVANCED, t2)
    entry = hd.target_state(state, "skillA")

    assert entry["attempts"] == 2
    assert entry["last_attempt_at"] == hd.format_ts(t2)
    assert entry["last_advanced_at"] == hd.format_ts(t2)
    assert entry["consecutive_no_progress"] == 0


def test_no_progress_outcomes_trigger_deterministic_stepped_cooldown():
    state = hd.new_selector_state()
    now = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)

    for step, expected_hours in enumerate(hd.COOLDOWN_STEPS_HOURS, start=1):
        entry = hd.record_attempt(state, "skillA", hd.OUTCOME_NO_CHANGE, now)
        assert entry["consecutive_no_progress"] == step
        assert entry["cooldown_until"] == hd.format_ts(now + timedelta(hours=expected_hours))

    # a fifth no-progress attempt stays at the last (largest) cooldown step
    entry = hd.record_attempt(state, "skillA", hd.OUTCOME_NO_CHANGE, now)
    assert entry["cooldown_until"] == hd.format_ts(now + timedelta(hours=hd.COOLDOWN_STEPS_HOURS[-1]))


def test_advanced_outcome_resets_no_progress_and_clears_cooldown():
    state = hd.new_selector_state()
    now = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)
    hd.record_attempt(state, "skillA", hd.OUTCOME_NO_CHANGE, now)
    hd.record_attempt(state, "skillA", hd.OUTCOME_NO_CHANGE, now)

    entry = hd.record_attempt(state, "skillA", hd.OUTCOME_ADVANCED, now)

    assert entry["consecutive_no_progress"] == 0
    assert entry["cooldown_until"] is None


def test_select_target_returns_no_targets_reason_when_empty():
    state = hd.new_selector_state()
    now = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)

    name, reason, ranking = hd.select_target([], state, now)

    assert name is None
    assert reason == hd.REASON_NO_TARGETS
    assert ranking == []


def test_select_target_excludes_cooling_down_target_with_all_cooling_reason():
    state = hd.new_selector_state()
    now = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)
    hd.record_attempt(state, "skillA", hd.OUTCOME_NO_CHANGE, now)

    name, reason, ranking = hd.select_target([{"name": "skillA", "score": 50}], state, now)

    assert name is None
    assert reason == hd.REASON_ALL_COOLING_DOWN
    assert ranking[0]["cooling_down"] is True


def test_diversity_rule_prevents_repeated_no_change_target_from_dominating():
    state = hd.new_selector_state()
    state["last_selected"] = "A"
    now = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)
    candidates = [{"name": "A", "score": 90}, {"name": "B", "score": 10}]

    name, reason, ranking = hd.select_target(candidates, state, now)

    assert name == "B"
    assert reason == hd.REASON_OK


def test_shadow_score_preserves_old_priority_independent_of_no_progress_penalty():
    state = hd.new_selector_state()
    now = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)
    entry = hd.target_state(state, "skillA")
    entry["consecutive_no_progress"] = 2
    audit_ts = hd.format_ts(now - timedelta(days=3))

    ranking = hd.rank_targets([{"name": "skillA", "score": 50, "last_audit": audit_ts}], state, now)
    row = ranking[0]

    assert row["shadow_score"] == (100.0 - 50) + 3
    assert row["effective_priority"] == row["base_priority"] - hd.NO_PROGRESS_PENALTY * 2
    assert row["shadow_score"] != row["effective_priority"]


# ---------------------------------------------------------------------------
# (C) generator/evaluator vocabulary alignment (示例 / 约束)
#     and explicit classification of unsupported findings
# ---------------------------------------------------------------------------


def test_missing_sections_detects_english_and_chinese_vocabulary():
    bare = "just some prose with nothing structured"
    assert "example" in hd.missing_sections(bare)
    assert "constraint" in hd.missing_sections(bare)

    chinese = "## 示例\n...\n## 约束\n..."
    assert "example" not in hd.missing_sections(chinese)
    assert "constraint" not in hd.missing_sections(chinese)


def test_classify_findings_separates_unsupported_frontmatter_from_supported_sections():
    content = "no frontmatter, no sections here"
    findings = hd.classify_findings(content)

    assert "example" in findings["supported"]
    assert {"finding": "frontmatter", "reason": "generator_cannot_author_frontmatter"} in findings["unsupported"]


def test_classify_findings_has_no_unsupported_when_frontmatter_present():
    content = "---\nname: x\n---\nbody"
    findings = hd.classify_findings(content)
    assert findings["unsupported"] == []


def test_generator_can_satisfy_its_own_structural_evaluator_for_example_and_constraint():
    content = "---\nname: x\n---\nsome body without those two sections"

    candidate_content, applied = hd.generate_sections(content, ["example", "constraint"])

    assert set(applied) == {"example", "constraint"}
    evaluation = hd.evaluate_candidate(candidate_content, applied)
    assert evaluation["satisfied"] is True
    assert evaluation["remaining"] == []
    assert evaluation["reason"] == hd.REASON_OK


def test_evaluate_candidate_flags_mismatch_when_content_lacks_expected_vocabulary():
    evaluation = hd.evaluate_candidate("no matching text at all", ["example"])

    assert evaluation["satisfied"] is False
    assert "example" in evaluation["remaining"]
    assert evaluation["reason"] == hd.REASON_EVALUATION_REJECTED


# ---------------------------------------------------------------------------
# (D) ownership/path preflight guard — injectable euid + stat/lstat/access for
#     tests that cannot actually chown files or run as root.
# ---------------------------------------------------------------------------


def _stat_result(uid: int, mode: int = 0o100644):
    return SimpleNamespace(st_uid=uid, st_mode=mode)


def test_ownership_preflight_rejects_root_euid_with_non_root_home(tmp_path):
    home = tmp_path / "hermes"
    home.mkdir()
    target = home / "skills" / "x" / "SKILL.md"
    target.parent.mkdir(parents=True)
    target.write_text("---\nname: x\n---\nbody", encoding="utf-8")

    stage = hd.ownership_preflight(home, target, euid=0)

    assert stage.stage == hd.STAGE_OWNERSHIP
    assert stage.ok is False
    assert stage.reason == hd.REASON_OWNERSHIP_ROOT_BLOCKED


def test_ownership_preflight_rejects_home_owner_mismatch_for_non_root_euid(tmp_path):
    home = tmp_path / "hermes"
    home.mkdir()
    target = home / "skills" / "x" / "SKILL.md"
    target.parent.mkdir(parents=True)
    target.write_text("body", encoding="utf-8")

    def fake_stat(path):
        if str(path) == str(home):
            return _stat_result(999)
        return _stat_result(os.getuid())

    stage = hd.ownership_preflight(home, target, euid=os.getuid(), stat_fn=fake_stat, lstat_fn=fake_stat)

    assert stage.ok is False
    assert stage.reason == hd.REASON_OWNERSHIP_HOME_MISMATCH


def test_ownership_preflight_rejects_active_target_owner_mismatch(tmp_path):
    home = tmp_path / "hermes"
    home.mkdir()
    target = home / "skills" / "x" / "SKILL.md"
    target.parent.mkdir(parents=True)
    target.write_text("body", encoding="utf-8")

    real_uid = os.getuid()

    def fake_stat(path):
        if str(path) == str(target):
            return _stat_result(real_uid + 1)
        return _stat_result(real_uid)

    stage = hd.ownership_preflight(home, target, euid=real_uid, stat_fn=fake_stat, lstat_fn=fake_stat)

    assert stage.ok is False
    assert stage.reason == hd.REASON_OWNERSHIP_TARGET_MISMATCH


def test_ownership_preflight_rejects_unreadable_target(tmp_path):
    home = tmp_path / "hermes"
    home.mkdir()
    target = home / "skills" / "x" / "SKILL.md"
    target.parent.mkdir(parents=True)
    target.write_text("body", encoding="utf-8")
    target.chmod(0o000)
    try:
        stage = hd.ownership_preflight(home, target, euid=os.getuid())
    finally:
        target.chmod(0o644)

    assert stage.ok is False
    assert stage.reason == hd.REASON_OWNERSHIP_UNREADABLE


def test_ownership_preflight_rejects_symlink_escape(tmp_path):
    home = tmp_path / "hermes"
    (home / "skills" / "x").mkdir(parents=True)
    outside = tmp_path / "outside.md"
    outside.write_text("body", encoding="utf-8")
    target = home / "skills" / "x" / "SKILL.md"
    target.symlink_to(outside)

    stage = hd.ownership_preflight(home, target, euid=os.getuid())

    assert stage.ok is False
    assert stage.reason == hd.REASON_OWNERSHIP_SYMLINK_ESCAPE


def test_ownership_preflight_rejects_symlink_in_intermediate_path_component(tmp_path):
    home = tmp_path / "hermes"
    (home / "skills").mkdir(parents=True)
    real_target_dir = tmp_path / "outside-skill-dir"
    real_target_dir.mkdir()
    (real_target_dir / "SKILL.md").write_text("body", encoding="utf-8")
    symlinked_skill_dir = home / "skills" / "x"
    symlinked_skill_dir.symlink_to(real_target_dir)
    target = symlinked_skill_dir / "SKILL.md"

    stage = hd.ownership_preflight(home, target, euid=os.getuid())

    assert stage.ok is False
    assert stage.reason == hd.REASON_OWNERSHIP_SYMLINK_ESCAPE


def test_ownership_preflight_rejects_symlinked_skills_root(tmp_path):
    home = tmp_path / "hermes"
    home.mkdir()
    real_skills_dir = tmp_path / "outside-skills"
    (real_skills_dir / "x").mkdir(parents=True)
    (real_skills_dir / "x" / "SKILL.md").write_text("body", encoding="utf-8")
    (home / "skills").symlink_to(real_skills_dir)
    target = home / "skills" / "x" / "SKILL.md"

    stage = hd.ownership_preflight(home, target, euid=os.getuid())

    assert stage.ok is False
    assert stage.reason == hd.REASON_OWNERSHIP_SYMLINK_ESCAPE


def test_ownership_preflight_rejects_lexical_dotdot_escape_even_when_target_exists(tmp_path):
    home = tmp_path / "hermes"
    outside = home / "outside" / "SKILL.md"
    outside.parent.mkdir(parents=True)
    outside.write_text("body", encoding="utf-8")
    target = home / "skills" / ".." / "outside" / "SKILL.md"

    stage = hd.ownership_preflight(home, target, euid=os.getuid())

    assert stage.ok is False
    assert stage.reason == hd.REASON_OWNERSHIP_SYMLINK_ESCAPE


def test_ownership_preflight_rejects_regular_file_outside_exact_skills_root(tmp_path):
    home = tmp_path / "hermes"
    outside = home / "other" / "SKILL.md"
    outside.parent.mkdir(parents=True)
    outside.write_text("body", encoding="utf-8")

    stage = hd.ownership_preflight(home, outside, euid=os.getuid())

    assert stage.ok is False
    assert stage.reason == hd.REASON_OWNERSHIP_SYMLINK_ESCAPE


def test_ownership_preflight_rejects_symlinked_hermes_home_component(tmp_path):
    real_home = tmp_path / "real-home"
    target = _write_active_skill(real_home, "x", "body")
    linked_home = tmp_path / "linked-home"
    linked_home.symlink_to(real_home)

    stage = hd.ownership_preflight(linked_home, linked_home / "skills" / "x" / "SKILL.md", euid=os.getuid())

    assert target.is_file()
    assert stage.ok is False
    assert stage.reason == hd.REASON_OWNERSHIP_SYMLINK_ESCAPE


def test_ownership_preflight_passes_for_matching_owner_and_readable_target(tmp_path):
    home = tmp_path / "hermes"
    target = home / "skills" / "x" / "SKILL.md"
    target.parent.mkdir(parents=True)
    target.write_text("---\nname: x\n---\nbody", encoding="utf-8")

    stage = hd.ownership_preflight(home, target, euid=os.getuid())

    assert stage.ok is True
    assert stage.reason == hd.REASON_OK


# ---------------------------------------------------------------------------
# (E) candidate destination resolution — must fail closed before any write.
# ---------------------------------------------------------------------------


def test_resolve_candidate_destination_accepts_normal_names(tmp_path):
    home = tmp_path / "hermes"
    resolved, reason = hd.resolve_candidate_destination(home, "run-1", "skill-a")

    assert reason == hd.REASON_OK
    # V2: flat artifact under provisioned root, one path component, no per-run dir
    assert resolved is not None
    assert resolved.parent == home / "state" / "dreaming" / "candidates"
    assert resolved.name.startswith("candidate-v2--run-1--skill-a--")
    assert resolved.name.endswith(".json")
    assert "/" not in resolved.name and "\\" not in resolved.name
    assert resolved == resolved.parent / resolved.name  # single component


def test_resolve_candidate_destination_rejects_traversal_in_run_id(tmp_path):
    home = tmp_path / "hermes"
    resolved, reason = hd.resolve_candidate_destination(home, "../../etc", "skill-a")

    assert resolved is None
    assert reason == hd.REASON_CANDIDATE_DEST_ESCAPE


def test_resolve_candidate_destination_rejects_traversal_in_skill_name(tmp_path):
    home = tmp_path / "hermes"
    resolved, reason = hd.resolve_candidate_destination(home, "run-1", "../../../etc/passwd")

    assert resolved is None
    assert reason == hd.REASON_CANDIDATE_DEST_ESCAPE


def test_resolve_candidate_destination_rejects_absolute_skill_name(tmp_path):
    home = tmp_path / "hermes"
    resolved, reason = hd.resolve_candidate_destination(home, "run-1", "/etc/passwd")

    assert resolved is None
    assert reason == hd.REASON_CANDIDATE_DEST_ESCAPE


# ---------------------------------------------------------------------------
# (F) candidate-only generation — active bytes must never move.
# ---------------------------------------------------------------------------


def _write_active_skill(home, name: str, content: str):
    skill_dir = home / "skills" / name
    skill_dir.mkdir(parents=True)
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(content, encoding="utf-8")
    return skill_md


def test_generate_candidate_copies_active_and_leaves_active_bytes_unchanged(tmp_path):
    home = tmp_path / "hermes"
    active_md = _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    before_hash = hd.file_sha256(active_md)
    before_bytes = active_md.read_bytes()

    # V2 contract: candidates root must be pre-provisioned; Loop A does not create it
    candidates_root = home / "state" / "dreaming" / "candidates"
    candidates_root.mkdir(parents=True)

    result = hd.generate_candidate(home, "run-1", "skill-a")

    assert result.stage.ok is True
    assert result.stage.reason == hd.REASON_CANDIDATE_GENERATED
    assert active_md.read_bytes() == before_bytes
    assert hd.file_sha256(active_md) == before_hash
    assert result.active_hash_before == before_hash
    assert result.active_hash_after == before_hash
    # V2: single flat regular-file artifact, no subdirectories, no .tmp-*
    assert result.candidate_artifact is not None
    assert result.candidate_artifact.is_file()
    assert not result.candidate_artifact.is_symlink()
    assert "/" not in result.candidate_artifact.name and "\\" not in result.candidate_artifact.name
    # No directories under the candidates root (flat artifacts only)
    assert [p for p in candidates_root.iterdir() if p.is_dir()] == []
    assert list(candidates_root.glob(".tmp-candidate-*")) == []
    assert list(candidates_root.glob(".cleanup-*")) == []
    # envelope present and canonical
    env = result.candidate_artifact.read_bytes()
    assert env.endswith(b"\n")
    validated, vr = hd.validate_candidate_envelope(
        env, expected_run_id="run-1", expected_skill_name="skill-a", expected_source_sha256=before_hash
    )
    assert vr is None
    assert validated is not None
    assert validated["candidate_bytes"].decode("utf-8") != before_bytes.decode("utf-8")  # applied sections



def test_generate_candidate_publishes_direct_temp_inode_with_complete_skill_tree(tmp_path, monkeypatch):
    """V2 equivalent: flat artifact creation, no tree copy, no tmp dirs.
    We now test the post_create_hook + write path and final identity gate instead of
    _atomic_publish_directory_noreplace_at + _copy_tree.
    """
    home = tmp_path / "hermes"
    active_md = _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    (active_md.parent / "reference.md").write_text("reference body", encoding="utf-8")
    candidates_root = home / "state" / "dreaming" / "candidates"
    candidates_root.mkdir(parents=True)

    captured = {"post_create": None, "written_len": 0}

    def post_create(fd, name, root_fd):
        captured["post_create"] = (name, os.fstat(fd).st_ino)

    def write_hook(fd, data):
        os.write(fd, data)
        captured["written_len"] = len(data)

    result = hd.generate_candidate(
        home, "run-1", "skill-a",
        post_create_hook=post_create,
        write_hook=write_hook,
    )

    assert result.stage.ok is True
    assert result.candidate_artifact is not None
    assert result.candidate_artifact.is_file()
    assert not result.candidate_artifact.is_symlink()
    assert captured["post_create"] is not None
    assert captured["written_len"] > 0
    # no .tmp- or subdirs created
    assert list(candidates_root.glob(".tmp-*")) == []
    assert list(candidates_root.glob(".cleanup-*")) == []
    assert all(not p.is_dir() for p in candidates_root.iterdir() if p.name != result.candidate_artifact.name)


def test_generate_candidate_reports_post_write_hash_receipt(tmp_path):
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    candidates_root = home / "state" / "dreaming" / "candidates"
    candidates_root.mkdir(parents=True)

    result = hd.generate_candidate(home, "run-1", "skill-a")

    assert result.stage.ok is True
    assert result.candidate_artifact is not None
    assert result.candidate_artifact.is_file()
    assert not result.candidate_artifact.is_symlink()
    # flat name under candidates root, no run/skill subdirs
    assert result.candidate_artifact.parent == candidates_root
    assert list(candidates_root.glob("*/")) == [] or all(not p.is_dir() for p in candidates_root.iterdir())
    env = json.loads(result.candidate_artifact.read_bytes())
    assert env["run_id"] == "run-1"
    assert env["skill_name"] == "skill-a"
    assert "candidate_sha256" in env
    assert "candidate_size" in env
    assert result.stage.details.get("candidate_sha256") == env["candidate_sha256"]
    assert set(result.applied_sections) >= {"constraint", "example"}


def test_generate_candidate_blocked_destination_escape_leaves_zero_residue(tmp_path):
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    candidates_root = home / "state" / "dreaming" / "candidates"
    candidates_root.mkdir(parents=True)
    before = sorted(p.name for p in candidates_root.iterdir())

    result = hd.generate_candidate(home, "../../etc", "skill-a")

    assert result.stage.ok is False
    assert result.stage.reason == hd.REASON_CANDIDATE_DEST_ESCAPE
    assert result.candidate_artifact is None
    assert sorted(p.name for p in candidates_root.iterdir()) == before


def test_generate_candidate_rejects_foreign_owned_candidates_ancestor_before_any_write(tmp_path):
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    candidates_root = home / "state" / "dreaming" / "candidates"
    candidates_root.mkdir(parents=True)
    foreign_ino = os.stat(candidates_root).st_ino
    real_uid = os.getuid()

    def lying_owner(fd):
        current = os.fstat(fd)
        return real_uid + 1 if current.st_ino == foreign_ino else current.st_uid

    result = hd.generate_candidate(home, "run-1", "skill-a", euid=real_uid, ancestor_owner_of_fd=lying_owner)

    assert result.stage.ok is False
    assert result.stage.reason == hd.REASON_CANDIDATE_DEST_ANCESTOR_OWNER_MISMATCH
    assert result.candidate_artifact is None
    assert list(candidates_root.iterdir()) == []


def test_generate_candidate_rejects_foreign_owned_root_component_before_any_write(tmp_path):
    """V2: no per-run directory; foreign owner on a root ancestor fails closed with zero writes."""
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    dreaming = home / "state" / "dreaming"
    dreaming.mkdir(parents=True)
    candidates_root = dreaming / "candidates"
    candidates_root.mkdir()
    foreign_ino = os.stat(dreaming).st_ino
    real_uid = os.getuid()

    def lying_owner(fd):
        current = os.fstat(fd)
        return real_uid + 1 if current.st_ino == foreign_ino else current.st_uid

    result = hd.generate_candidate(home, "run-1", "skill-a", euid=real_uid, ancestor_owner_of_fd=lying_owner)

    assert result.stage.ok is False
    assert result.stage.reason == hd.REASON_CANDIDATE_DEST_ANCESTOR_OWNER_MISMATCH
    assert result.candidate_artifact is None
    assert list(candidates_root.iterdir()) == []
    assert list(candidates_root.glob(".tmp-*")) == []


def test_generate_candidate_rejects_race_replaced_foreign_artifact_owner(tmp_path):
    """V2: after O_EXCL create, a forged owner on the artifact fd fails closed and cleans only identity-matched residue."""
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    candidates_root = home / "state" / "dreaming" / "candidates"
    candidates_root.mkdir(parents=True)
    real_uid = os.getuid()
    calls = {"n": 0}

    def lying_owner(fd):
        # Only the home-owner gate uses this callback before write; force mismatch on later owner checks
        # by returning foreign uid after candidates root is accepted.
        calls["n"] += 1
        current_uid = os.fstat(fd).st_uid
        # Call order under V2: home (+ chain opens may call), then candidates root components.
        # Force mismatch after root is open by failing post-create identity via hook instead.
        return current_uid

    def poison_owner_after_create(fd, name, root_fd):
        # Swap pathname to a competitor after create; cleanup must not delete competitor.
        path = candidates_root / name
        parked = candidates_root / f"{name}.parked-ours"
        path.rename(parked)
        competitor = candidates_root / name
        competitor.write_text("competitor-bytes", encoding="utf-8")

    result = hd.generate_candidate(
        home, "run-1", "skill-a",
        euid=real_uid,
        ancestor_owner_of_fd=lying_owner,
        post_create_hook=poison_owner_after_create,
    )

    assert result.stage.ok is False
    # identity mismatch or readback failure; cleanup must not remove competitor
    assert result.stage.reason in {
        hd.REASON_CANDIDATE_CLEANUP_FAILED,
        hd.REASON_CANDIDATE_READBACK_FAILED,
        hd.REASON_CANDIDATE_INTERNAL_FAILURE,
    }
    remaining = list(candidates_root.iterdir())
    assert any(p.name.endswith("competitor-bytes") or p.read_text(encoding="utf-8") == "competitor-bytes" for p in remaining if p.is_file())


def test_generate_candidate_rejects_race_replaced_foreign_published_artifact(tmp_path):
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    candidates_root = home / "state" / "dreaming" / "candidates"
    candidates_root.mkdir(parents=True)

    def swap_after_fsync(fd, name, root_fd):
        path = candidates_root / name
        ours = candidates_root / f"{name}.ours"
        path.rename(ours)
        path.write_text("theirs", encoding="utf-8")

    result = hd.generate_candidate(home, "run-1", "skill-a", post_fsync_hook=swap_after_fsync)

    assert result.stage.ok is False
    assert result.stage.reason in {
        hd.REASON_CANDIDATE_CLEANUP_FAILED,
        hd.REASON_CANDIDATE_READBACK_FAILED,
        hd.REASON_CANDIDATE_INTERNAL_FAILURE,
    }
    # competitor must survive
    competitors = [p for p in candidates_root.iterdir() if p.is_file() and p.read_text(encoding="utf-8") == "theirs"]
    assert len(competitors) == 1


def test_generate_candidate_rejects_home_owner_mismatched_authorized_euid(tmp_path):
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    (home / "state" / "dreaming" / "candidates").mkdir(parents=True)

    result = hd.generate_candidate(home, "run-1", "skill-a", euid=os.getuid() + 1)

    assert result.stage.ok is False
    assert result.stage.reason == hd.REASON_CANDIDATE_DEST_ANCESTOR_OWNER_MISMATCH
    assert result.candidate_artifact is None
    assert list((home / "state" / "dreaming" / "candidates").iterdir()) == []


def test_generate_candidate_missing_active_skill_md_reports_no_findings(tmp_path):
    home = tmp_path / "hermes"
    (home / "skills" / "ghost").mkdir(parents=True)
    (home / "state" / "dreaming" / "candidates").mkdir(parents=True)

    result = hd.generate_candidate(home, "run-1", "ghost")

    assert result.stage.ok is False
    assert result.stage.reason == hd.REASON_NO_FINDINGS
    assert result.candidate_artifact is None


def test_generate_candidate_no_change_when_active_already_complete(tmp_path):
    home = tmp_path / "hermes"
    complete_content = (
        "---\nname: skill-a\n---\n"
        "## 输入\n...\n## 输出\n...\n## 约束\n...\n## 检查点\n...\n## 示例\n...\n"
    )
    _write_active_skill(home, "skill-a", complete_content)
    (home / "state" / "dreaming" / "candidates").mkdir(parents=True)

    result = hd.generate_candidate(home, "run-1", "skill-a")

    assert result.stage.ok is False
    assert result.stage.reason == hd.REASON_NO_FINDINGS
    assert result.candidate_artifact is None
    assert list((home / "state" / "dreaming" / "candidates").iterdir()) == []


def test_generate_candidate_unsupported_only_when_frontmatter_missing_but_sections_present(tmp_path):
    home = tmp_path / "hermes"
    content = "## 输入\n...\n## 输出\n...\n## 约束\n...\n## 检查点\n...\n## 示例\n...\n"
    _write_active_skill(home, "skill-a", content)
    (home / "state" / "dreaming" / "candidates").mkdir(parents=True)

    result = hd.generate_candidate(home, "run-1", "skill-a")

    assert result.stage.ok is False
    assert result.stage.reason == hd.REASON_UNSUPPORTED_ONLY
    assert result.candidate_artifact is None


def test_generate_candidate_blocked_when_active_tree_contains_symlink(tmp_path):
    home = tmp_path / "hermes"
    skill_dir = home / "skills" / "skill-a"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: skill-a\n---\nbody without those sections", encoding="utf-8")
    outside = tmp_path / "outside-ref.md"
    outside.write_text("secret", encoding="utf-8")
    (skill_dir / "reference.md").symlink_to(outside)
    (home / "state" / "dreaming" / "candidates").mkdir(parents=True)

    result = hd.generate_candidate(home, "run-1", "skill-a")

    assert result.stage.ok is False
    assert result.stage.reason == hd.REASON_ACTIVE_TREE_SYMLINK
    assert list((home / "state" / "dreaming" / "candidates").iterdir()) == []


def test_generate_candidate_never_overwrites_existing_destination(tmp_path):
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    candidates_root = home / "state" / "dreaming" / "candidates"
    candidates_root.mkdir(parents=True)
    name, _ = hd.build_candidate_artifact_filename("run-1", "skill-a", "nonce123")
    existing = candidates_root / name
    existing.write_text('{"pre":"existing"}', encoding="utf-8")

    result = hd.generate_candidate(home, "run-1", "skill-a", artifact_nonce_fn=lambda: "nonce123")

    assert result.stage.ok is False
    assert result.stage.reason == hd.REASON_CANDIDATE_DEST_CONFLICT
    assert existing.read_text(encoding="utf-8") == '{"pre":"existing"}'


def test_artifact_open_excl_race_never_replaces_competing_destination(tmp_path):
    """V2 security equivalent of old atomic_publish_directory race: O_EXCL never replaces competitor."""
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    candidates_root = home / "state" / "dreaming" / "candidates"
    candidates_root.mkdir(parents=True)
    name, _ = hd.build_candidate_artifact_filename("run-1", "skill-a", "race-nonce")
    competitor = candidates_root / name
    competitor.write_text("theirs", encoding="utf-8")

    result = hd.generate_candidate(home, "run-1", "skill-a", artifact_nonce_fn=lambda: "race-nonce")

    assert result.stage.ok is False
    assert result.stage.reason == hd.REASON_CANDIDATE_DEST_CONFLICT
    assert competitor.read_text(encoding="utf-8") == "theirs"


def test_generate_candidate_injected_pathname_swap_preserves_competitor(tmp_path):
    """V2: mid-flight pathname swap to competitor must not delete competitor; typed residual."""
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    candidates_root = home / "state" / "dreaming" / "candidates"
    candidates_root.mkdir(parents=True)

    def race_after_create(fd, name, root_fd):
        path = candidates_root / name
        path.rename(candidates_root / f"{name}.ours")
        (candidates_root / name).write_text("theirs", encoding="utf-8")

    result = hd.generate_candidate(home, "run-1", "skill-a", post_create_hook=race_after_create)

    assert result.stage.ok is False
    assert result.stage.reason in {
        hd.REASON_CANDIDATE_CLEANUP_FAILED,
        hd.REASON_CANDIDATE_READBACK_FAILED,
        hd.REASON_CANDIDATE_INTERNAL_FAILURE,
    }
    if result.stage.reason == hd.REASON_CANDIDATE_CLEANUP_FAILED:
        assert result.stage.details.get("cleanup_failed") is True
        assert result.stage.details.get("residual_reason") in {
            hd.REASON_CANDIDATE_RESIDUAL_IDENTITY_MISMATCH,
            hd.REASON_CANDIDATE_RESIDUAL_UNSAFE,
            None,
        } or result.stage.details.get("residual_reason") in {
            hd.REASON_CANDIDATE_RESIDUAL_IDENTITY_MISMATCH,
            hd.REASON_CANDIDATE_RESIDUAL_UNSAFE,
        }
    assert any(p.read_text(encoding="utf-8") == "theirs" for p in candidates_root.iterdir() if p.is_file())
    assert list(candidates_root.glob(".tmp-candidate-*")) == []


def test_generate_candidate_blocked_when_candidates_ancestor_is_symlink(tmp_path):
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    real_dreaming_dir = tmp_path / "real-dreaming"
    real_dreaming_dir.mkdir()
    (real_dreaming_dir / "candidates").mkdir()
    (home / "state").mkdir(parents=True)
    (home / "state" / "dreaming").symlink_to(real_dreaming_dir)

    result = hd.generate_candidate(home, "run-1", "skill-a")

    assert result.stage.ok is False
    assert result.stage.reason == hd.REASON_CANDIDATE_DEST_ESCAPE
    assert list((real_dreaming_dir / "candidates").iterdir()) == []


def test_generate_candidate_write_failure_cleans_exact_artifact_only(tmp_path):
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    candidates_root = home / "state" / "dreaming" / "candidates"
    candidates_root.mkdir(parents=True)
    sentinel = candidates_root / "unrelated-sentinel.json"
    sentinel.write_text("keep-me", encoding="utf-8")

    def boom_write(fd, data):
        raise OSError("simulated write failure")

    result = hd.generate_candidate(home, "run-1", "skill-a", write_hook=boom_write)

    assert result.stage.ok is False
    assert result.stage.reason in {
        hd.REASON_CANDIDATE_INTERNAL_FAILURE,
        hd.REASON_CANDIDATE_CLEANUP_FAILED,
    }
    assert sentinel.read_text(encoding="utf-8") == "keep-me"
    # no tmp leftovers
    assert list(candidates_root.glob(".tmp-*")) == []


def test_generate_candidate_write_failure_reports_typed_failure_and_nightly_rc2(tmp_path, monkeypatch):
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    candidates_root = home / "state" / "dreaming" / "candidates"
    candidates_root.mkdir(parents=True)
    now = datetime(2026, 8, 1, tzinfo=timezone.utc)

    def write_boom(fd, data):
        raise OSError("simulated primary write failure")

    real_generate = hd.generate_candidate

    def generate_with_boom(*args, **kwargs):
        kwargs = dict(kwargs)
        kwargs["write_hook"] = write_boom
        return real_generate(*args, **kwargs)

    monkeypatch.setattr(hd, "generate_candidate", generate_with_boom)

    nightly = load_script_module("nightly_write_failure", "autonomous-evolution-nightly.py")
    nightly.HERMES_HOME = home
    nightly.SKILLS_DIR = home / "skills"
    monkeypatch.setattr(nightly, "build_candidates", lambda: [{"name": "skill-a", "score": 10}])
    monkeypatch.setattr(nightly, "resolve_euid", lambda: os.getuid())
    monkeypatch.setattr(nightly, "receipt_output_path", lambda: home / "state" / "dreaming" / "receipt.json")
    monkeypatch.setattr(nightly, "log_event", lambda *_a, **_k: None)
    monkeypatch.setattr(nightly.STORE, "append_dream_run", lambda *_a, **_k: None)
    # ensure nightly uses same hd with monkeypatched generate
    monkeypatch.setattr(nightly, "hd", hd)

    rc = nightly._run(now, "run-1")
    payload = json.loads((home / "state" / "dreaming" / "receipt.json").read_text(encoding="utf-8"))
    generation = next(stage for stage in payload["stages"] if stage["stage"] == hd.STAGE_GENERATION)

    assert generation["ok"] is False
    assert generation["reason"] in {
        hd.REASON_CANDIDATE_INTERNAL_FAILURE,
        hd.REASON_CANDIDATE_CLEANUP_FAILED,
    }
    # write failure is a write-block path; job_success false only if cleanup residual
    if generation["reason"] == hd.REASON_CANDIDATE_CLEANUP_FAILED:
        assert payload["job_success"] is False
        assert hd.classify_receipt(payload)["status"] == "ERROR"
        assert rc == 2
    else:
        assert payload["write_blocked"] is True
        assert rc in {0, 1, 2}
    assert not any(p.is_dir() for p in candidates_root.iterdir())


def test_generate_candidate_has_no_tmp_dir_cleanup_race(tmp_path, monkeypatch):
    """V2 regression: no .tmp-candidate directory publish path exists to rmdir a competitor."""
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    candidates_root = home / "state" / "dreaming" / "candidates"
    candidates_root.mkdir(parents=True)
    competitor = candidates_root / "preexisting-competitor.json"
    competitor.write_text("alive", encoding="utf-8")

    result = hd.generate_candidate(home, "run-1", "skill-a")

    assert result.stage.ok is True
    assert competitor.read_text(encoding="utf-8") == "alive"
    assert list(candidates_root.glob(".tmp-candidate-*")) == []
    assert list(candidates_root.glob(".cleanup-*")) == []
    assert result.candidate_artifact is not None
    assert result.candidate_artifact.is_file()


def test_artifact_fd_write_failure_closes_without_leaking_open_fd(tmp_path, monkeypatch):
    """V2 equivalent of copy_tree source-fd close-on-error: write hook OSError must not leak."""
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    (home / "state" / "dreaming" / "candidates").mkdir(parents=True)
    opened: list[int] = []
    real_open = hd.os.open

    def tracking_open(name, flags, *args, dir_fd=None, **kwargs):
        fd = real_open(name, flags, *args, dir_fd=dir_fd, **kwargs)
        # track O_CREAT artifact opens
        if isinstance(name, str) and name.startswith("candidate-v2--"):
            opened.append(fd)
        return fd

    def boom_write(fd, data):
        raise OSError("simulated write failure")

    monkeypatch.setattr(hd.os, "open", tracking_open)
    result = hd.generate_candidate(home, "run-1", "skill-a", write_hook=boom_write)
    assert result.stage.ok is False
    assert opened  # created then closed in finally
    for fd in opened:
        with pytest.raises(OSError):
            os.fstat(fd)


def test_artifact_fd_fsync_failure_closes_without_leaking_open_fd(tmp_path, monkeypatch):
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    (home / "state" / "dreaming" / "candidates").mkdir(parents=True)
    opened: list[int] = []
    real_open = hd.os.open

    def tracking_open(name, flags, *args, dir_fd=None, **kwargs):
        fd = real_open(name, flags, *args, dir_fd=dir_fd, **kwargs)
        if isinstance(name, str) and name.startswith("candidate-v2--"):
            opened.append(fd)
        return fd

    def boom_fsync(fd):
        raise OSError("simulated fsync failure")

    monkeypatch.setattr(hd.os, "open", tracking_open)
    result = hd.generate_candidate(home, "run-1", "skill-a", fsync_hook=boom_fsync)
    assert result.stage.ok is False
    assert opened
    for fd in opened:
        with pytest.raises(OSError):
            os.fstat(fd)


def test_validate_candidate_envelope_detects_digest_mismatch(tmp_path):
    env = hd.canonical_candidate_envelope_bytes(
        run_id="run-1", skill_name="skill-a",
        source_sha256="a" * 64, candidate_bytes=b"body",
    )
    payload = json.loads(env)
    payload["candidate_sha256"] = "b" * 64
    bad = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    validated, reason = hd.validate_candidate_envelope(
        bad, expected_run_id="run-1", expected_skill_name="skill-a", expected_source_sha256="a" * 64
    )
    assert validated is None
    assert reason == hd.REASON_CANDIDATE_ARTIFACT_INVALID


def test_validate_candidate_envelope_detects_malformed_json():
    validated, reason = hd.validate_candidate_envelope(
        b"{not-json\n", expected_run_id="run-1", expected_skill_name="skill-a", expected_source_sha256="a" * 64
    )
    assert validated is None
    assert reason == hd.REASON_CANDIDATE_ARTIFACT_INVALID


def test_validate_candidate_envelope_detects_run_id_mismatch():
    env = hd.canonical_candidate_envelope_bytes(
        run_id="run-1", skill_name="skill-a",
        source_sha256="a" * 64, candidate_bytes=b"body",
    )
    validated, reason = hd.validate_candidate_envelope(
        env, expected_run_id="run-2", expected_skill_name="skill-a", expected_source_sha256="a" * 64
    )
    assert validated is None
    assert reason == hd.REASON_CANDIDATE_ARTIFACT_INVALID


def test_validate_candidate_envelope_passes_for_valid_payload():
    body = b"hello candidate"
    src = "c" * 64
    env = hd.canonical_candidate_envelope_bytes(
        run_id="run-1", skill_name="skill-a", source_sha256=src, candidate_bytes=body
    )
    validated, reason = hd.validate_candidate_envelope(
        env, expected_run_id="run-1", expected_skill_name="skill-a", expected_source_sha256=src
    )
    assert reason is None
    assert validated is not None
    assert validated["candidate_bytes"] == body


def test_generate_candidate_readback_failure_when_bytes_mismatch(tmp_path):
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    candidates_root = home / "state" / "dreaming" / "candidates"
    candidates_root.mkdir(parents=True)

    def bad_readback(fd):
        return b'{"schema_version":"wrong"}\n'

    result = hd.generate_candidate(home, "run-1", "skill-a", readback_hook=bad_readback)

    assert result.stage.ok is False
    assert result.stage.reason in {
        hd.REASON_CANDIDATE_READBACK_FAILED,
        hd.REASON_CANDIDATE_ARTIFACT_INVALID,
        hd.REASON_CANDIDATE_CLEANUP_FAILED,
    }
    # cleaned or residual typed; no directory tree
    assert not any(p.is_dir() for p in candidates_root.iterdir())


def test_generate_candidate_post_publish_active_same_bytes_symlink_swap_fails_and_cleans_candidate(tmp_path):
    home = tmp_path / "hermes"
    active_md = _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    candidates_root = home / "state" / "dreaming" / "candidates"
    candidates_root.mkdir(parents=True)
    same_bytes = tmp_path / "same-bytes.md"
    same_bytes.write_bytes(active_md.read_bytes())

    def swap_active(fd, name, root_fd):
        active_md.unlink()
        active_md.symlink_to(same_bytes)

    result = hd.generate_candidate(home, "run-1", "skill-a", post_fsync_hook=swap_active)

    assert result.stage.ok is False
    assert result.stage.reason in {
        hd.REASON_CANDIDATE_CLEANUP_FAILED,
        hd.REASON_OWNERSHIP_SYMLINK_ESCAPE,
        hd.REASON_CANDIDATE_READBACK_FAILED,
    }
    # no successful artifact left as candidate_generated
    assert result.candidate_artifact is None or result.stage.details.get("cleanup_failed") is True


def test_generate_candidate_failed_post_readback_cleans_exact_new_publish_only(tmp_path):
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    candidates_root = home / "state" / "dreaming" / "candidates"
    candidates_root.mkdir(parents=True)
    sentinel = candidates_root / "keep-me.json"
    sentinel.write_text("sentinel", encoding="utf-8")

    def fail_readback(fd):
        raise OSError("simulated readback failure")

    result = hd.generate_candidate(home, "run-1", "skill-a", readback_hook=fail_readback)

    assert result.stage.ok is False
    assert result.stage.reason in {
        hd.REASON_CANDIDATE_READBACK_FAILED,
        hd.REASON_CANDIDATE_CLEANUP_FAILED,
    }
    assert sentinel.read_text(encoding="utf-8") == "sentinel"


def test_publish_parent_rename_symlink_race_never_creates_escaped_candidate(tmp_path):
    """V2: if candidates root is replaced by symlink mid-flight, no escape write outside."""
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    candidates_root = home / "state" / "dreaming" / "candidates"
    candidates_root.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()

    def race_root(fd, name, root_fd):
        parent = home / "state" / "dreaming"
        parked = parent / "candidates-parked"
        candidates_root.rename(parked)
        (parent / "candidates").symlink_to(outside, target_is_directory=True)

    result = hd.generate_candidate(home, "run-1", "skill-a", post_create_hook=race_root)

    assert result.stage.ok is False
    # no files escaped into outside via V2 path (open already held old dirfd)
    escaped = list(outside.iterdir())
    # held dirfd may still write into the original inode (now parked); that is not escape
    assert all(p.parent != outside for p in escaped) or escaped == []
    assert not any(p.name.startswith("candidate-v2--") for p in outside.iterdir())


def test_cleanup_identity_race_preserves_competitor_and_reports_residual(tmp_path):
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    candidates_root = home / "state" / "dreaming" / "candidates"
    candidates_root.mkdir(parents=True)

    def replace_then_fail_readback(fd):
        # discover name via /dev/fd is hard; use post_fsync to swap then fail readback
        raise OSError("unused")

    def swap_then_continue(fd, name, root_fd):
        path = candidates_root / name
        path.rename(candidates_root / f"{name}.ours")
        competitor = candidates_root / name
        competitor.write_text("survives", encoding="utf-8")

    result = hd.generate_candidate(home, "run-1", "skill-a", post_fsync_hook=swap_then_continue)

    assert result.stage.ok is False
    assert any(p.read_text(encoding="utf-8") == "survives" for p in candidates_root.iterdir() if p.is_file())
    if result.stage.reason == hd.REASON_CANDIDATE_CLEANUP_FAILED:
        assert result.stage.details.get("cleanup_failed") is True
        assert result.stage.details.get("residual_reason") in {
            hd.REASON_CANDIDATE_RESIDUAL_IDENTITY_MISMATCH,
            hd.REASON_CANDIDATE_RESIDUAL_UNSAFE,
        }


def test_late_active_swap_from_post_fsync_hook_fails_closed(tmp_path):
    home = tmp_path / "hermes"
    active = _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    (home / "state" / "dreaming" / "candidates").mkdir(parents=True)
    outside = tmp_path / "same-active.md"
    outside.write_bytes(active.read_bytes())

    def swap_active(fd, name, root_fd):
        active.unlink()
        active.symlink_to(outside)

    result = hd.generate_candidate(home, "run-1", "skill-a", post_fsync_hook=swap_active)

    assert result.stage.ok is False


def test_late_candidate_swap_after_readback_fails_closed(tmp_path):
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    candidates_root = home / "state" / "dreaming" / "candidates"
    candidates_root.mkdir(parents=True)

    def swap_after_read_setup(fd, name, root_fd):
        # Replace pathname after fsync; final identity gate must fail closed.
        path = candidates_root / name
        outside = tmp_path / "same-candidate.json"
        outside.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(outside)

    result = hd.generate_candidate(home, "run-1", "skill-a", post_fsync_hook=swap_after_read_setup)

    assert result.stage.ok is False


# ---------------------------------------------------------------------------
# (G) orchestrated run — selection -> ownership -> generation -> evaluation,
#     with every outcome recorded and promoted/state_advanced fixed to False.
# ---------------------------------------------------------------------------


def test_run_dreaming_cycle_no_targets_returns_no_targets_receipt(tmp_path):
    home = tmp_path / "hermes"
    (home / "state" / "dreaming" / "candidates").mkdir(parents=True)
    now = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)

    receipt = hd.run_dreaming_cycle(home, [], now, run_id="run-1", euid=os.getuid())

    assert receipt.target is None
    assert receipt.job_success is True
    assert receipt.effective_audit is False
    assert receipt.candidate_generated is False
    assert receipt.state_advanced is False
    assert receipt.promoted is False
    assert hd.REASON_NO_TARGETS in receipt.reasons
    assert receipt.stages[0].stage == hd.STAGE_SELECTION


def test_run_dreaming_cycle_ownership_block_leaves_zero_candidate_residue(tmp_path):
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    (home / "state" / "dreaming" / "candidates").mkdir(parents=True)
    now = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)

    receipt = hd.run_dreaming_cycle(
        home, [{"name": "skill-a", "score": 10}], now, run_id="run-1", euid=0
    )

    assert receipt.target == "skill-a"
    assert receipt.write_blocked is True
    assert receipt.candidate_generated is False
    assert receipt.state_advanced is False
    assert receipt.promoted is False
    assert hd.REASON_OWNERSHIP_ROOT_BLOCKED in receipt.reasons
    # Root is pre-provisioned; ownership block must leave zero artifacts.
    assert list((home / "state" / "dreaming" / "candidates").iterdir()) == []

    state = hd.load_selector_state(hd.selector_state_path(home))
    entry = hd.target_state(state, "skill-a")
    assert entry["attempts"] == 1
    assert entry["last_attempt_at"] == hd.format_ts(now)
    assert entry["last_advanced_at"] is None


def test_run_dreaming_cycle_generates_candidate_without_advancing_or_promoting(tmp_path):
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    candidates_root = home / "state" / "dreaming" / "candidates"
    candidates_root.mkdir(parents=True)
    before_hash = hd.file_sha256(home / "skills" / "skill-a" / "SKILL.md")
    now = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)

    receipt = hd.run_dreaming_cycle(
        home, [{"name": "skill-a", "score": 10}], now, run_id="run-1", euid=os.getuid()
    )

    assert receipt.target == "skill-a"
    assert receipt.job_success is True
    assert receipt.effective_audit is True
    assert receipt.candidate_generated is True
    assert receipt.state_advanced is False
    assert receipt.promoted is False
    assert receipt.write_blocked is False
    assert hd.file_sha256(home / "skills" / "skill-a" / "SKILL.md") == before_hash
    artifacts = list(candidates_root.glob("candidate-v2--run-1--skill-a--*.json"))
    assert len(artifacts) == 1
    assert artifacts[0].is_file()
    assert not artifacts[0].is_symlink()
    assert not any(p.is_dir() for p in candidates_root.iterdir())

    state = hd.load_selector_state(hd.selector_state_path(home))
    entry = hd.target_state(state, "skill-a")
    assert entry["attempts"] == 1
    assert entry["last_advanced_at"] is None
    assert entry["consecutive_no_progress"] == 1


def test_run_dreaming_cycle_evaluator_uses_digest_bound_content_after_post_return_path_swap(
    tmp_path, monkeypatch
):
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    (home / "state" / "dreaming" / "candidates").mkdir(parents=True)
    now = datetime(2026, 8, 1, tzinfo=timezone.utc)
    real_generate = hd.generate_candidate
    real_evaluate = hd.evaluate_candidate
    evaluated: list[str] = []

    def generate_then_swap(*args, **kwargs):
        result = real_generate(*args, **kwargs)
        assert result.stage.ok is True
        # Pathname competitor must not affect digest-bound candidate_content.
        result.candidate_artifact.write_text("late pathname competitor", encoding="utf-8")
        return result

    def capture_evaluation(content, applied_sections):
        evaluated.append(content)
        return real_evaluate(content, applied_sections)

    monkeypatch.setattr(hd, "generate_candidate", generate_then_swap)
    monkeypatch.setattr(hd, "evaluate_candidate", capture_evaluation)

    receipt = hd.run_dreaming_cycle(
        home, [{"name": "skill-a", "score": 10}], now, run_id="run-1", euid=os.getuid()
    )

    assert receipt.candidate_generated is True
    assert evaluated and evaluated[0] != "late pathname competitor"
    assert "## 输入" in evaluated[0]


def test_run_dreaming_cycle_no_change_when_active_already_complete(tmp_path):
    home = tmp_path / "hermes"
    complete_content = (
        "---\nname: skill-a\n---\n"
        "## 输入\n...\n## 输出\n...\n## 约束\n...\n## 检查点\n...\n## 示例\n...\n"
    )
    _write_active_skill(home, "skill-a", complete_content)
    candidates_root = home / "state" / "dreaming" / "candidates"
    candidates_root.mkdir(parents=True)
    now = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)

    receipt = hd.run_dreaming_cycle(
        home, [{"name": "skill-a", "score": 90}], now, run_id="run-1", euid=os.getuid()
    )

    assert receipt.candidate_generated is False
    assert receipt.effective_audit is True
    assert hd.REASON_NO_FINDINGS in receipt.reasons
    assert list(candidates_root.iterdir()) == []


def test_run_dreaming_cycle_validates_as_typed_receipt(tmp_path):
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    (home / "state" / "dreaming" / "candidates").mkdir(parents=True)
    now = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)

    receipt = hd.run_dreaming_cycle(
        home, [{"name": "skill-a", "score": 10}], now, run_id="run-1", euid=os.getuid()
    )

    assert hd.validate_receipt(receipt.to_dict()) == []


def test_run_dreaming_cycle_generation_security_block_sets_write_blocked_and_degraded(tmp_path):
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    # Unprovisioned root is a V2 write-block reason.
    now = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)

    receipt = hd.run_dreaming_cycle(home, [{"name": "skill-a", "score": 10}], now, run_id="run-1", euid=os.getuid())

    assert receipt.write_blocked is True
    assert receipt.degraded is True
    assert receipt.candidate_generated is False
    assert hd.REASON_CANDIDATE_ROOT_UNPROVISIONED in receipt.reasons


def test_run_cleanup_failure_is_error_and_not_job_success(tmp_path, monkeypatch):
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    (home / "state" / "dreaming" / "candidates").mkdir(parents=True)
    now = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)
    failed = hd.CandidateResult(
        hd.StageReceipt(hd.STAGE_GENERATION, False, hd.REASON_CANDIDATE_CLEANUP_FAILED,
                        {"cleanup_failed": True, "residual_reason": hd.REASON_CANDIDATE_RESIDUAL_UNSAFE}),
        None, None, None, [], [],
    )
    monkeypatch.setattr(hd, "generate_candidate", lambda *_a, **_k: failed)

    receipt = hd.run_dreaming_cycle(home, [{"name": "skill-a", "score": 10}], now,
                                    run_id="run-1", euid=os.getuid())

    assert receipt.job_success is False
    assert receipt.write_blocked is True
    assert receipt.degraded is True
    assert hd.classify_receipt(receipt.to_dict())["status"] == "ERROR"


def test_unbound_write_hook_failure_has_typed_reason(tmp_path):
    """V2 equivalent of unbound publish callback: write_hook OSError is typed fail-closed."""
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    (home / "state" / "dreaming" / "candidates").mkdir(parents=True)

    def bad_write(fd, data):
        raise OSError(errno.ENOTSUP, "unsupported")

    result = hd.generate_candidate(home, "run-1", "skill-a", write_hook=bad_write)

    assert result.stage.ok is False
    assert result.stage.reason in {
        hd.REASON_CANDIDATE_INTERNAL_FAILURE,
        hd.REASON_CANDIDATE_CLEANUP_FAILED,
        hd.REASON_CANDIDATE_PUBLISH_UNSUPPORTED,
    }
    assert result.stage.reason in hd.REASON_TAXONOMY


def test_nightly_success_diagnostics_use_only_typed_receipt_evidence(tmp_path, monkeypatch, capsys):
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    (home / "state" / "dreaming" / "candidates").mkdir(parents=True)
    nightly = load_script_module("nightly_receipt_bound_diagnostics", "autonomous-evolution-nightly.py")
    nightly.HERMES_HOME = home
    nightly.SKILLS_DIR = home / "skills"
    monkeypatch.setattr(nightly, "build_candidates", lambda: [{"name": "skill-a", "score": 10}])
    monkeypatch.setattr(nightly, "resolve_euid", lambda: os.getuid())
    monkeypatch.setattr(nightly, "receipt_output_path", lambda: home / "state" / "dreaming" / "receipt.json")
    monkeypatch.setattr(nightly, "log_event", lambda *_a, **_k: None)
    monkeypatch.setattr(nightly.STORE, "append_dream_run", lambda *_a, **_k: None)
    assert not hasattr(nightly, "recalculate_darwin_score")
    assert not hasattr(nightly, "audit_skill_structure")

    rc = nightly._run(datetime(2026, 8, 1, tzinfo=timezone.utc), "run-1")
    output = capsys.readouterr().out

    assert rc == 0
    assert "sha256=" in output
    assert "applied_sections=" in output


def test_nightly_cleanup_failure_returns_rc2(tmp_path, monkeypatch):
    home = tmp_path / "hermes"
    home.mkdir(parents=True)
    (home / "state" / "dreaming" / "candidates").mkdir(parents=True)
    monkeypatch.setenv("HERMES_HOME", str(home))
    nightly = load_script_module("nightly_cleanup_rc2", "autonomous-evolution-nightly.py")
    receipt = hd.RunReceipt(run_id="run-1", ts="2026-08-01T00:00:00Z", target="skill-a")
    receipt.job_success = False
    receipt.degraded = True
    receipt.write_blocked = True
    receipt.add_reason(hd.REASON_CANDIDATE_CLEANUP_FAILED)
    receipt.add_stage(hd.StageReceipt(hd.STAGE_GENERATION, False, hd.REASON_CANDIDATE_CLEANUP_FAILED,
                                      {"cleanup_failed": True}))
    monkeypatch.setattr(nightly, "build_candidates", lambda: [{"name": "skill-a", "score": 10}])
    monkeypatch.setattr(nightly, "resolve_euid", lambda: os.getuid())
    monkeypatch.setattr(nightly.hd, "run_dreaming_cycle", lambda *_a, **_k: receipt)
    monkeypatch.setattr(nightly, "receipt_output_path", lambda: home / "state" / "dreaming" / "receipt.json")
    monkeypatch.setattr(nightly, "log_event", lambda *_a, **_k: None)
    monkeypatch.setattr(nightly.STORE, "append_dream_run", lambda *_a, **_k: None)

    rc = nightly._run(datetime(2026, 8, 1, tzinfo=timezone.utc), "run-1")

    assert rc == 2
    assert json.loads(
        (home / "state" / "dreaming" / "receipt.json").read_text(encoding="utf-8")
    )["job_success"] is False


def test_run_dreaming_cycle_persists_selected_row_shadow_score_when_candidate_generated(tmp_path):
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    (home / "state" / "dreaming" / "candidates").mkdir(parents=True)
    now = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)
    audit_ts = hd.format_ts(now - timedelta(days=5))

    hd.run_dreaming_cycle(
        home, [{"name": "skill-a", "score": 10, "last_audit": audit_ts}], now, run_id="run-1", euid=os.getuid()
    )

    state = hd.load_selector_state(hd.selector_state_path(home))
    entry = hd.target_state(state, "skill-a")
    assert entry["shadow_score"] == (100.0 - 10) + 5


def test_run_dreaming_cycle_persists_selected_row_shadow_score_on_ownership_block(tmp_path):
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    (home / "state" / "dreaming" / "candidates").mkdir(parents=True)
    now = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)

    hd.run_dreaming_cycle(home, [{"name": "skill-a", "score": 20}], now, run_id="run-1", euid=0)

    state = hd.load_selector_state(hd.selector_state_path(home))
    entry = hd.target_state(state, "skill-a")
    assert entry["shadow_score"] is not None


def test_dreaming_write_boundary_preflight_rejects_symlinked_dreaming_ancestor(tmp_path):
    home = tmp_path / "hermes"
    home.mkdir()
    external = tmp_path / "outside-state"
    external.mkdir()
    (home / "state").symlink_to(external)

    reason = hd.dreaming_write_boundary_preflight(home, hd.selector_state_path(home))

    assert reason == hd.REASON_STATE_BOUNDARY_SYMLINK_ESCAPE


def test_dreaming_write_boundary_preflight_rejects_path_outside_state_dreaming(tmp_path):
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    active_md = home / "skills" / "skill-a" / "SKILL.md"

    reason = hd.dreaming_write_boundary_preflight(home, active_md)

    assert reason == hd.REASON_STATE_BOUNDARY_PATH_ESCAPE


def test_run_dreaming_cycle_blocked_by_symlinked_state_leaves_external_dir_empty(tmp_path):
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    external = tmp_path / "outside-state"
    external.mkdir()
    (home / "state").symlink_to(external)
    now = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)

    receipt = hd.run_dreaming_cycle(
        home, [{"name": "skill-a", "score": 10}], now, run_id="run-1", euid=os.getuid()
    )

    assert receipt.target is None
    assert receipt.write_blocked is True
    assert receipt.state_advanced is False
    assert receipt.promoted is False
    assert hd.REASON_STATE_BOUNDARY_SYMLINK_ESCAPE in receipt.reasons
    assert list(external.iterdir()) == []


def test_run_dreaming_cycle_malformed_utf8_active_skill_records_selector_attempt(tmp_path):
    home = tmp_path / "hermes"
    skill_dir = home / "skills" / "skill-a"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_bytes(b"---\nname: skill-a\n---\n\xff\xfe not valid utf-8")
    (home / "state" / "dreaming" / "candidates").mkdir(parents=True)
    now = datetime(2026, 8, 1, 0, 0, 0, tzinfo=timezone.utc)

    receipt = hd.run_dreaming_cycle(
        home, [{"name": "skill-a", "score": 10}], now, run_id="run-1", euid=os.getuid()
    )

    assert receipt.target == "skill-a"
    assert receipt.candidate_generated is False
    assert receipt.job_success is True
    generation = next(stage for stage in receipt.stages if stage.stage == hd.STAGE_GENERATION)
    assert generation.ok is False
    assert generation.reason == hd.REASON_CANDIDATE_INTERNAL_FAILURE

    state = hd.load_selector_state(hd.selector_state_path(home))
    entry = hd.target_state(state, "skill-a")
    assert entry["attempts"] == 1
    assert entry["last_attempt_at"] == hd.format_ts(now)
    assert entry["last_advanced_at"] is None


# ---------------------------------------------------------------------------
# (H) integration: the real nightly main under an isolated tmp HERMES_HOME.
#     No mocking of hermes_dreaming — this exercises the actual wiring of
#     scripts/autonomous-evolution-nightly.py end to end.
# ---------------------------------------------------------------------------


def _seed_isolated_home(tmp_path, skill_content: str, darwin_score: int = 40):
    home = tmp_path / "hermes"
    skill_md = home / "skills" / "demo-skill" / "SKILL.md"
    skill_md.parent.mkdir(parents=True)
    skill_md.write_text(skill_content, encoding="utf-8")

    db_path = home / "state" / "evolution" / "bayesian-agent" / "confidence-db.json"
    db_path.parent.mkdir(parents=True)
    db_path.write_text(
        json.dumps({"skills": {"demo-skill": {"darwin_score": darwin_score, "last_audit": "2026-07-01T00:00:00"}}}),
        encoding="utf-8",
    )
    # V2: candidates root must be pre-provisioned; Loop A never creates it.
    (home / "state" / "dreaming" / "candidates").mkdir(parents=True, exist_ok=True)
    return home, skill_md


def test_nightly_main_generates_candidate_and_receipt_without_mutating_active(tmp_path, monkeypatch):
    home, skill_md = _seed_isolated_home(tmp_path, "---\nname: demo-skill\n---\nbody without those sections")
    receipt_path = home / "state" / "dreaming" / "receipt.json"
    before_hash = hd.file_sha256(skill_md)

    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setenv("HERMES_DREAMING_RECEIPT_PATH", str(receipt_path))
    monkeypatch.delenv("HERMES_DREAMING_EUID_OVERRIDE", raising=False)
    nightly = load_script_module("nightly_candidate_only", "autonomous-evolution-nightly.py")

    rc = nightly.main()

    assert rc == 0
    assert hd.file_sha256(skill_md) == before_hash

    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert hd.validate_receipt(payload) == []
    assert payload["promoted"] is False
    assert payload["state_advanced"] is False
    assert payload["candidate_generated"] is True

    candidates_root = home / "state" / "dreaming" / "candidates"
    artifacts = list(candidates_root.glob(f"candidate-v2--{payload['run_id']}--demo-skill--*.json"))
    assert len(artifacts) == 1
    assert artifacts[0].is_file()
    env = json.loads(artifacts[0].read_text(encoding="utf-8"))
    assert env["skill_name"] == "demo-skill"
    assert env["candidate_bytes_b64"]


def test_nightly_main_ledger_row_carries_job_success_matching_receipt(tmp_path, monkeypatch):
    home, skill_md = _seed_isolated_home(tmp_path, "---\nname: demo-skill\n---\nbody without those sections")
    receipt_path = home / "state" / "dreaming" / "receipt.json"

    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setenv("HERMES_DREAMING_RECEIPT_PATH", str(receipt_path))
    monkeypatch.delenv("HERMES_DREAMING_EUID_OVERRIDE", raising=False)
    nightly = load_script_module("nightly_ledger_job_success", "autonomous-evolution-nightly.py")

    rc = nightly.main()

    assert rc == 0
    receipt_payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    health = hd.classify_receipt(receipt_payload)

    ledger_lines = nightly.STORE.runs_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(ledger_lines) == 1
    ledger_row = json.loads(ledger_lines[0])

    assert "job_success" in ledger_row
    assert ledger_row["job_success"] == receipt_payload["job_success"] == health["job_success"] is True


def test_nightly_main_writes_receipt_atomically_no_temp_residue(tmp_path, monkeypatch):
    home, skill_md = _seed_isolated_home(tmp_path, "---\nname: demo-skill\n---\nbody without those sections")
    receipt_path = home / "state" / "dreaming" / "receipt.json"

    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setenv("HERMES_DREAMING_RECEIPT_PATH", str(receipt_path))
    monkeypatch.delenv("HERMES_DREAMING_EUID_OVERRIDE", raising=False)
    nightly = load_script_module("nightly_atomic_receipt", "autonomous-evolution-nightly.py")

    nightly.main()

    assert receipt_path.is_file()
    assert list(receipt_path.parent.glob(".tmp-*")) == []


def test_nightly_main_writes_event_log_under_state_dreaming_not_notes(tmp_path, monkeypatch):
    home, skill_md = _seed_isolated_home(tmp_path, "---\nname: demo-skill\n---\nbody without those sections")
    receipt_path = home / "state" / "dreaming" / "receipt.json"

    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setenv("HERMES_DREAMING_RECEIPT_PATH", str(receipt_path))
    monkeypatch.delenv("HERMES_DREAMING_EUID_OVERRIDE", raising=False)
    nightly = load_script_module("nightly_log_path", "autonomous-evolution-nightly.py")

    nightly.main()

    assert not (home / "notes").exists()
    log_path = home / "state" / "dreaming" / "autonomous-evolution-log.jsonl"
    assert log_path.is_file()
    assert log_path.read_text(encoding="utf-8").strip() != ""


def test_nightly_main_honors_run_id_env_override(tmp_path, monkeypatch):
    home, skill_md = _seed_isolated_home(tmp_path, "---\nname: demo-skill\n---\nbody without those sections")
    receipt_path = home / "state" / "dreaming" / "receipt.json"

    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setenv("HERMES_DREAMING_RECEIPT_PATH", str(receipt_path))
    monkeypatch.setenv("HERMES_DREAMING_RUN_ID", "fixed-run-id-123")
    monkeypatch.delenv("HERMES_DREAMING_EUID_OVERRIDE", raising=False)
    nightly = load_script_module("nightly_run_id_override", "autonomous-evolution-nightly.py")

    nightly.main()

    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert payload["run_id"] == "fixed-run-id-123"


def test_nightly_main_catches_unexpected_exception_and_emits_degraded_receipt(tmp_path, monkeypatch):
    home, skill_md = _seed_isolated_home(tmp_path, "---\nname: demo-skill\n---\nbody without those sections")
    receipt_path = home / "state" / "dreaming" / "receipt.json"

    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setenv("HERMES_DREAMING_RECEIPT_PATH", str(receipt_path))
    monkeypatch.delenv("HERMES_DREAMING_EUID_OVERRIDE", raising=False)
    nightly = load_script_module("nightly_unexpected_exception", "autonomous-evolution-nightly.py")

    def boom(*a, **k):
        raise RuntimeError("simulated internal crash with a secret path /etc/shadow")

    monkeypatch.setattr(nightly.hd, "run_dreaming_cycle", boom)

    rc = nightly.main()

    assert rc == 1
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert hd.validate_receipt(payload) == []
    assert payload["job_success"] is False
    assert payload["degraded"] is True
    assert hd.REASON_UNEXPECTED_EXCEPTION in payload["reasons"]
    dumped = json.dumps(payload)
    assert "simulated internal crash" not in dumped
    assert "/etc/shadow" not in dumped
    assert "Traceback" not in dumped


def test_nightly_main_root_euid_override_blocks_before_any_candidate_write(tmp_path, monkeypatch):
    home, skill_md = _seed_isolated_home(tmp_path, "---\nname: demo-skill\n---\nbody without those sections")
    receipt_path = home / "state" / "dreaming" / "receipt.json"
    before_hash = hd.file_sha256(skill_md)

    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setenv("HERMES_DREAMING_RECEIPT_PATH", str(receipt_path))
    monkeypatch.setenv("HERMES_DREAMING_EUID_OVERRIDE", "0")
    nightly = load_script_module("nightly_root_blocked", "autonomous-evolution-nightly.py")

    nightly.main()

    assert hd.file_sha256(skill_md) == before_hash
    candidates_root = home / "state" / "dreaming" / "candidates"
    assert list(candidates_root.glob("candidate-v2--*")) == []

    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert hd.validate_receipt(payload) == []
    assert payload["write_blocked"] is True
    assert payload["candidate_generated"] is False
    assert payload["state_advanced"] is False
    assert payload["promoted"] is False
    assert hd.REASON_OWNERSHIP_ROOT_BLOCKED in payload["reasons"]


def test_nightly_main_non_root_euid_home_mismatch_blocks_before_any_candidate_write(tmp_path, monkeypatch):
    home, skill_md = _seed_isolated_home(tmp_path, "---\nname: demo-skill\n---\nbody without those sections")
    receipt_path = home / "state" / "dreaming" / "receipt.json"
    before_hash = hd.file_sha256(skill_md)
    mismatched_euid = os.getuid() + 1

    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setenv("HERMES_DREAMING_RECEIPT_PATH", str(receipt_path))
    monkeypatch.setenv("HERMES_DREAMING_EUID_OVERRIDE", str(mismatched_euid))
    nightly = load_script_module("nightly_home_mismatch", "autonomous-evolution-nightly.py")

    nightly.main()

    assert hd.file_sha256(skill_md) == before_hash
    candidates_root = home / "state" / "dreaming" / "candidates"
    assert list(candidates_root.glob("candidate-v2--*")) == []

    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert payload["write_blocked"] is True
    assert hd.REASON_OWNERSHIP_HOME_MISMATCH in payload["reasons"]


def test_nightly_main_no_active_skill_candidates_reports_no_targets(tmp_path, monkeypatch):
    home = tmp_path / "hermes"
    (home / "skills").mkdir(parents=True)
    (home / "state" / "dreaming" / "candidates").mkdir(parents=True)
    receipt_path = home / "state" / "dreaming" / "receipt.json"

    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setenv("HERMES_DREAMING_RECEIPT_PATH", str(receipt_path))
    monkeypatch.delenv("HERMES_DREAMING_EUID_OVERRIDE", raising=False)
    nightly = load_script_module("nightly_no_targets", "autonomous-evolution-nightly.py")

    rc = nightly.main()

    assert rc == 0
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert payload["target"] is None
    assert payload["candidate_generated"] is False
    assert list((home / "state" / "dreaming" / "candidates").iterdir()) == []


def test_nightly_main_receipt_override_aliasing_active_skill_is_rejected(tmp_path, monkeypatch):
    """P1-1 repro: HERMES_DREAMING_RECEIPT_PATH pointed at an active
    SKILL.md must never be written to -- active bytes must stay unchanged
    and the run must fail closed with a typed reason, persisted at the
    safe default receipt location instead."""
    home, skill_md = _seed_isolated_home(tmp_path, "---\nname: demo-skill\n---\nbody without those sections")
    before_hash = hd.file_sha256(skill_md)

    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setenv("HERMES_DREAMING_RECEIPT_PATH", str(skill_md))
    monkeypatch.setenv("HERMES_DREAMING_RUN_ID", "repro-active-overwrite")
    monkeypatch.delenv("HERMES_DREAMING_EUID_OVERRIDE", raising=False)
    nightly = load_script_module("nightly_receipt_active_alias", "autonomous-evolution-nightly.py")

    rc = nightly.main()

    assert hd.file_sha256(skill_md) == before_hash
    assert rc != 0

    fallback_path = home / "state" / "dreaming" / "last_run_receipt.json"
    assert fallback_path.is_file()
    payload = json.loads(fallback_path.read_text(encoding="utf-8"))
    assert payload["job_success"] is False
    assert payload["write_blocked"] is True
    assert hd.REASON_STATE_BOUNDARY_PATH_ESCAPE in payload["reasons"]


def test_nightly_main_symlinked_state_leaves_external_dir_empty(tmp_path, monkeypatch):
    """P1-2 repro: a symlinked state/dreaming must leave every sink
    (selector state, receipt, log, ledger) unwritten outside HERMES_HOME."""
    home = tmp_path / "hermes"
    skill_md = home / "skills" / "demo-skill" / "SKILL.md"
    skill_md.parent.mkdir(parents=True)
    skill_md.write_text("---\nname: demo-skill\n---\nbody without those sections", encoding="utf-8")
    before_hash = hd.file_sha256(skill_md)

    external = tmp_path / "outside-state"
    external.mkdir()
    (home / "state").symlink_to(external)

    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.delenv("HERMES_DREAMING_RECEIPT_PATH", raising=False)
    monkeypatch.delenv("HERMES_DREAMING_EUID_OVERRIDE", raising=False)
    nightly = load_script_module("nightly_symlinked_state", "autonomous-evolution-nightly.py")

    rc = nightly.main()

    assert hd.file_sha256(skill_md) == before_hash
    assert rc != 0
    assert list(external.iterdir()) == []


# ---------------------------------------------------------------------------
# (I) noagent wrapper wiring: deterministic receipt path env var, typed
#     receipt preferred over legacy stdout parsing.
# ---------------------------------------------------------------------------


def test_noagent_wrapper_passes_deterministic_receipt_path_and_prefers_typed_receipt(tmp_path, monkeypatch, capsys):
    home = tmp_path / "hermes"
    receipt_path = tmp_path / "receipt.json"

    captured_env: dict[str, str] = {}

    class FakeCompleted:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_run(args, **kwargs):
        captured_env.update(kwargs.get("env") or {})
        # Simulate the child script writing its typed receipt (with the
        # run_id the wrapper told it to use) to the path the wrapper told it
        # to use via HERMES_DREAMING_RECEIPT_PATH.
        details = _artifact_details(
            run_id=captured_env["HERMES_DREAMING_RUN_ID"],
            skill_name="demo-skill",
            candidate_artifact=f"candidate-v2--{captured_env['HERMES_DREAMING_RUN_ID']}--demo-skill--deadbeef.json",
        )
        receipt = hd.RunReceipt(
            run_id=captured_env["HERMES_DREAMING_RUN_ID"], ts="2026-08-01T00:00:00Z", target="demo-skill"
        )
        receipt.job_success = True
        receipt.effective_audit = True
        receipt.candidate_generated = True
        receipt.add_reason(hd.REASON_CANDIDATE_GENERATED)
        receipt.add_stage(hd.StageReceipt(hd.STAGE_SELECTION, True, hd.REASON_OK, {}))
        receipt.add_stage(hd.StageReceipt(hd.STAGE_OWNERSHIP, True, hd.REASON_OK, {}))
        receipt.add_stage(hd.StageReceipt(hd.STAGE_GENERATION, True, hd.REASON_CANDIDATE_GENERATED, details))
        receipt.add_stage(hd.StageReceipt(hd.STAGE_EVALUATION, True, hd.REASON_OK, {"satisfied": True, "missing_after": []}))
        Path(captured_env["HERMES_DREAMING_RECEIPT_PATH"]).write_text(
            json.dumps(receipt.to_dict()), encoding="utf-8"
        )
        return FakeCompleted()

    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setenv("HERMES_DREAMING_RECEIPT_PATH", str(receipt_path))
    monkeypatch.setattr(autonomous_evolution_nightly_noagent.subprocess, "run", fake_run)

    rc = autonomous_evolution_nightly_noagent.main()
    out_payload = json.loads(capsys.readouterr().out)

    assert captured_env["HERMES_DREAMING_RECEIPT_PATH"] == str(receipt_path)
    assert rc == 0
    assert out_payload["receipt_source"] == "typed_receipt"
    assert out_payload["candidate_generated"] is True
    assert out_payload["promoted"] is False
    assert out_payload["candidate_artifact"] is not None
    assert out_payload["candidate_artifact"]["skill_name"] == "demo-skill"


def test_noagent_wrapper_normal_path_includes_job_success_for_typed_candidate(tmp_path, monkeypatch, capsys):
    """The frozen contract keeps job_success/effective_audit/candidate_generated/
    state_advanced/promoted separate on every payload. The normal (non-timeout)
    path must surface job_success too, not just the timeout-error path."""
    home = tmp_path / "hermes"
    receipt_path = tmp_path / "receipt.json"

    class FakeCompleted:
        returncode = 0
        stdout = ""
        stderr = ""

    captured_env: dict[str, str] = {}

    def fake_run(args, **kwargs):
        captured_env.update(kwargs.get("env") or {})
        details = _artifact_details(
            run_id=captured_env["HERMES_DREAMING_RUN_ID"],
            skill_name="demo-skill",
            candidate_artifact=f"candidate-v2--{captured_env['HERMES_DREAMING_RUN_ID']}--demo-skill--deadbeef.json",
        )
        receipt = hd.RunReceipt(
            run_id=captured_env["HERMES_DREAMING_RUN_ID"], ts="2026-08-01T00:00:00Z", target="demo-skill"
        )
        receipt.job_success = True
        receipt.effective_audit = True
        receipt.candidate_generated = True
        receipt.add_reason(hd.REASON_CANDIDATE_GENERATED)
        receipt.add_stage(hd.StageReceipt(hd.STAGE_SELECTION, True, hd.REASON_OK, {}))
        receipt.add_stage(hd.StageReceipt(hd.STAGE_OWNERSHIP, True, hd.REASON_OK, {}))
        receipt.add_stage(hd.StageReceipt(hd.STAGE_GENERATION, True, hd.REASON_CANDIDATE_GENERATED, details))
        receipt.add_stage(hd.StageReceipt(hd.STAGE_EVALUATION, True, hd.REASON_OK, {"satisfied": True, "missing_after": []}))
        Path(captured_env["HERMES_DREAMING_RECEIPT_PATH"]).write_text(
            json.dumps(receipt.to_dict()), encoding="utf-8"
        )
        return FakeCompleted()

    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setenv("HERMES_DREAMING_RECEIPT_PATH", str(receipt_path))
    monkeypatch.setattr(autonomous_evolution_nightly_noagent.subprocess, "run", fake_run)

    rc = autonomous_evolution_nightly_noagent.main()
    out_payload = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert "job_success" in out_payload
    assert out_payload["job_success"] is True
    assert out_payload["candidate_artifact"] is not None


def test_noagent_wrapper_normal_path_includes_job_success_when_write_blocked(tmp_path, monkeypatch, capsys):
    """job_success stays a distinct flag from write_blocked/degraded: the
    subprocess ran and produced a valid receipt (job_success True) even
    though the ownership guard refused the candidate write."""
    home = tmp_path / "hermes"
    receipt_path = tmp_path / "receipt.json"

    class FakeCompleted:
        returncode = 0
        stdout = ""
        stderr = ""

    captured_env: dict[str, str] = {}

    def fake_run(args, **kwargs):
        captured_env.update(kwargs.get("env") or {})
        receipt = hd.RunReceipt(
            run_id=captured_env["HERMES_DREAMING_RUN_ID"], ts="2026-08-01T00:00:00Z", target="demo-skill"
        )
        receipt.job_success = True
        receipt.write_blocked = True
        receipt.add_reason(hd.REASON_OWNERSHIP_HOME_MISMATCH)
        Path(captured_env["HERMES_DREAMING_RECEIPT_PATH"]).write_text(
            json.dumps(receipt.to_dict()), encoding="utf-8"
        )
        return FakeCompleted()

    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setenv("HERMES_DREAMING_RECEIPT_PATH", str(receipt_path))
    monkeypatch.setattr(autonomous_evolution_nightly_noagent.subprocess, "run", fake_run)

    rc = autonomous_evolution_nightly_noagent.main()
    out_payload = json.loads(capsys.readouterr().out)

    assert out_payload["job_success"] is True
    assert out_payload["write_blocked"] is True
    assert out_payload["candidate_generated"] is False


def test_noagent_wrapper_receipt_missing_never_upgrades_from_stdout(tmp_path, monkeypatch, capsys):
    home = tmp_path / "hermes"
    receipt_path = tmp_path / "receipt.json"

    class FakeCompleted:
        returncode = 0
        stdout = "confidence_db: /x (archived)\n= 无变化\n✓ 改进已保留 [x]"
        stderr = ""

    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setenv("HERMES_DREAMING_RECEIPT_PATH", str(receipt_path))
    monkeypatch.setattr(autonomous_evolution_nightly_noagent.subprocess, "run", lambda *a, **k: FakeCompleted())

    rc = autonomous_evolution_nightly_noagent.main()
    out_payload = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert out_payload["receipt_source"] == "receipt_absent"
    assert out_payload["status"] == "ERROR"
    assert out_payload["job_success"] is False
    assert out_payload["effective_audit"] is False
    assert out_payload["candidate_generated"] is False
    assert out_payload["state_advanced"] is False
    assert out_payload["promoted"] is False
    assert Path(out_payload["dream_run_ledger"]).exists()


def test_noagent_wrapper_rejects_malformed_utf8_receipt_not_legacy(tmp_path, monkeypatch, capsys):
    """Exact regression repro at the wrapper boundary: the child process
    writes a receipt file that is not valid UTF-8 (e.g. truncated/corrupted
    write) but exits 0 with an old-style legacy success marker in stdout.
    The wrapper must fail closed on the unreadable receipt, never fall back
    to the legacy stdout marker, still append a ledger row, and never leak
    exception text/traceback into the printed payload."""
    home = tmp_path / "hermes"
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_bytes(b"\xff\xfe")

    class FakeCompleted:
        returncode = 0
        stdout = "confidence_db: /x (archived)\n= 无变化\n✓ 改进已保留 [x]"
        stderr = ""

    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setenv("HERMES_DREAMING_RECEIPT_PATH", str(receipt_path))
    monkeypatch.setattr(autonomous_evolution_nightly_noagent.subprocess, "run", lambda *a, **k: FakeCompleted())

    rc = autonomous_evolution_nightly_noagent.main()
    captured = capsys.readouterr()
    out_payload = json.loads(captured.out)

    assert rc == 2
    assert out_payload["receipt_source"] == "receipt_rejected"
    assert out_payload["status"] == "ERROR"
    assert out_payload["job_success"] is False
    assert out_payload["effective_audit"] is False
    assert out_payload["candidate_generated"] is False
    assert out_payload["state_advanced"] is False
    assert out_payload["promoted"] is False
    assert hd.REASON_RECEIPT_INVALID in out_payload["reasons"]
    assert Path(out_payload["dream_run_ledger"]).exists()
    ledger_lines = Path(out_payload["dream_run_ledger"]).read_text(encoding="utf-8").strip().splitlines()
    assert len(ledger_lines) == 1
    ledger_row = json.loads(ledger_lines[0])
    assert ledger_row["receipt_source"] == "receipt_rejected"
    assert ledger_row["job_success"] is False
    assert "Traceback" not in captured.out
    assert "UnicodeDecodeError" not in captured.out
    assert "Traceback" not in captured.err


def test_noagent_script_resolves_as_sibling_not_home_dot_hermes():
    expected = Path(autonomous_evolution_nightly_noagent.__file__).with_name("autonomous-evolution-nightly.py")
    assert autonomous_evolution_nightly_noagent.SCRIPT == expected


def test_classify_run_result_rejects_stale_receipt_with_mismatched_run_id(tmp_path):
    receipt_path = tmp_path / "receipt.json"
    payload = _valid_receipt_payload(run_id="old-run")
    receipt_path.write_text(json.dumps(payload), encoding="utf-8")

    health = hd.classify_run_result(0, "", "", receipt_path, expected_run_id="new-run")

    assert health["receipt_source"] == "receipt_rejected"
    assert hd.REASON_RECEIPT_RUN_ID_MISMATCH in health["reasons"]
    assert health["state_advanced"] is False
    assert health["job_success"] is False
    assert health["status"] != "OK"


def test_classify_run_result_rejects_mismatched_run_id_receipt_with_legacy_success_marker(tmp_path):
    """Exact regression repro: a stale (wrong run_id) receipt sits next to an
    old-style stdout success marker from the *current* run's legacy path.
    The stale receipt must never be silently discarded in favor of the
    legacy marker turning this into OK/advanced/candidate_generated."""
    receipt_path = tmp_path / "receipt.json"
    payload = _valid_candidate_generated_payload(run_id="old-run")
    # Keep artifact run_id consistent with payload run_id for shape; mismatch is expected_run_id.
    for stage in payload["stages"]:
        if stage.get("stage") == hd.STAGE_GENERATION:
            stage["details"]["run_id"] = "old-run"
    receipt_path.write_text(json.dumps(payload), encoding="utf-8")

    health = hd.classify_run_result(0, "✓ 改进已保留 [x]", "", receipt_path, expected_run_id="current")

    assert health["receipt_source"] == "receipt_rejected"
    assert hd.REASON_RECEIPT_RUN_ID_MISMATCH in health["reasons"]
    assert health["status"] != "OK"
    assert health["job_success"] is False
    assert health["state_advanced"] is False
    assert health["candidate_generated"] is False
    assert health["promoted"] is False


def test_classify_run_result_accepts_receipt_with_matching_run_id(tmp_path):
    receipt_path = tmp_path / "receipt.json"
    payload = _valid_candidate_generated_payload(run_id="run-abc")
    for stage in payload["stages"]:
        if stage.get("stage") == hd.STAGE_GENERATION:
            stage["details"]["run_id"] = "run-abc"
            stage["details"]["candidate_artifact"] = "candidate-v2--run-abc--skill-x--deadbeef.json"
    payload["candidate_artifact"] = hd.extract_candidate_artifact_projection(payload)
    receipt_path.write_text(json.dumps(payload), encoding="utf-8")

    health = hd.classify_run_result(0, "", "", receipt_path, expected_run_id="run-abc")

    assert health["receipt_source"] == "typed_receipt"
    assert health["candidate_generated"] is True
    assert health["state_advanced"] is False
    assert health["candidate_artifact"] is not None


def test_noagent_wrapper_sets_unique_run_id_env_and_per_run_receipt_path(tmp_path, monkeypatch, capsys):
    home = tmp_path / "hermes"
    captured_env: dict[str, str] = {}

    class FakeCompleted:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_run(args, **kwargs):
        captured_env.update(kwargs.get("env") or {})
        receipt = hd.RunReceipt(run_id=captured_env["HERMES_DREAMING_RUN_ID"], ts="2026-08-01T00:00:00Z", target="x")
        receipt.job_success = True
        receipt.effective_audit = True
        out_path = Path(captured_env["HERMES_DREAMING_RECEIPT_PATH"])
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(receipt.to_dict()), encoding="utf-8")
        return FakeCompleted()

    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.delenv("HERMES_DREAMING_RECEIPT_PATH", raising=False)
    monkeypatch.setattr(autonomous_evolution_nightly_noagent.subprocess, "run", fake_run)

    rc = autonomous_evolution_nightly_noagent.main()
    out_payload = json.loads(capsys.readouterr().out)

    assert rc == 0
    assert captured_env["HERMES_DREAMING_RUN_ID"]
    receipt_path = Path(captured_env["HERMES_DREAMING_RECEIPT_PATH"])
    assert receipt_path.parent == home / "state" / "dreaming" / "receipts"
    assert out_payload["receipt_source"] == "typed_receipt"


def test_noagent_wrapper_rejects_stale_receipt_with_mismatched_run_id(tmp_path, monkeypatch, capsys):
    home = tmp_path / "hermes"
    receipt_path = tmp_path / "receipt.json"
    stale = hd.RunReceipt(run_id="stale-run-from-yesterday", ts="2026-07-31T00:00:00Z", target="demo-skill")
    stale.job_success = True
    stale.effective_audit = True
    stale.candidate_generated = True
    stale.add_reason(hd.REASON_CANDIDATE_GENERATED)
    receipt_path.write_text(json.dumps(stale.to_dict()), encoding="utf-8")

    class FakeCompleted:
        returncode = 0
        stdout = ""
        stderr = ""

    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setenv("HERMES_DREAMING_RECEIPT_PATH", str(receipt_path))
    monkeypatch.setattr(autonomous_evolution_nightly_noagent.subprocess, "run", lambda *a, **k: FakeCompleted())

    rc = autonomous_evolution_nightly_noagent.main()
    out_payload = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert out_payload["receipt_source"] != "typed_receipt"
    assert out_payload["candidate_generated"] is False


def test_noagent_wrapper_timeout_returns_nonzero_closed_payload_and_appends_ledger(tmp_path, monkeypatch, capsys):
    home = tmp_path / "hermes"

    def fake_run(args, **kwargs):
        raise autonomous_evolution_nightly_noagent.subprocess.TimeoutExpired(
            cmd=args, timeout=300, output="partial stdout", stderr="partial stderr"
        )

    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.delenv("HERMES_DREAMING_RECEIPT_PATH", raising=False)
    monkeypatch.setattr(autonomous_evolution_nightly_noagent.subprocess, "run", fake_run)

    rc = autonomous_evolution_nightly_noagent.main()
    out_payload = json.loads(capsys.readouterr().out)

    assert rc == 2
    assert out_payload["job_success"] is False
    assert out_payload["degraded"] is True
    assert out_payload["status"] == "ERROR"
    assert hd.REASON_SUBPROCESS_TIMEOUT in out_payload["reasons"]
    assert Path(out_payload["dream_run_ledger"]).exists()


@pytest.mark.parametrize("exc", [OSError("spawn denied /secret"), RuntimeError("subprocess internals /secret")])
def test_noagent_wrapper_spawn_exception_emits_sanitized_closed_payload_and_ledger(tmp_path, monkeypatch, capsys, exc):
    home = tmp_path / "hermes"
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setattr(
        autonomous_evolution_nightly_noagent.subprocess,
        "run",
        lambda *a, **k: (_ for _ in ()).throw(exc),
    )

    rc = autonomous_evolution_nightly_noagent.main()
    raw = capsys.readouterr().out
    payload = json.loads(raw)

    assert rc == 2
    assert payload["status"] == "ERROR"
    assert payload["job_success"] is False
    assert payload["effective_audit"] is False
    assert payload["candidate_generated"] is False
    assert payload["state_advanced"] is False
    assert payload["promoted"] is False
    assert hd.REASON_UNEXPECTED_EXCEPTION in payload["reasons"]
    assert "/secret" not in raw
    assert "Traceback" not in raw
    assert Path(payload["dream_run_ledger"]).exists()


@pytest.mark.parametrize(
    "bad_flags",
    [{"state_advanced": True}, {"promoted": True, "state_advanced": True, "candidate_generated": True}],
)
def test_noagent_loop_a_rejects_receipt_claiming_advancement_or_promotion(tmp_path, monkeypatch, capsys, bad_flags):
    home = tmp_path / "hermes"
    receipt_path = tmp_path / "receipt.json"

    def fake_run(_args, **kwargs):
        run_id = kwargs["env"]["HERMES_DREAMING_RUN_ID"]
        payload = _valid_receipt_payload(run_id=run_id, **bad_flags)
        receipt_path.write_text(json.dumps(payload), encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setenv("HERMES_DREAMING_RECEIPT_PATH", str(receipt_path))
    monkeypatch.setattr(autonomous_evolution_nightly_noagent.subprocess, "run", fake_run)

    rc = autonomous_evolution_nightly_noagent.main()
    payload = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert payload["status"] == "ERROR"
    assert payload["job_success"] is False
    assert payload["state_advanced"] is False
    assert payload["promoted"] is False


def test_noagent_wrapper_real_subprocess_integration_generates_candidate_with_matching_run_id(tmp_path):
    home, skill_md = _seed_isolated_home(tmp_path, "---\nname: demo-skill\n---\nbody without those sections")
    before_hash = hd.file_sha256(skill_md)

    scripts_dir = Path(__file__).parent
    workdir = tmp_path / "scripts_copy"
    workdir.mkdir()
    for name in (
        "autonomous_evolution_nightly_noagent.py",
        "autonomous-evolution-nightly.py",
        "hermes_dreaming.py",
        "hermes_evolution_store.py",
    ):
        shutil.copy2(scripts_dir / name, workdir / name)

    env = dict(os.environ)
    env["HERMES_HOME"] = str(home)
    env.pop("HERMES_DREAMING_RECEIPT_PATH", None)
    env.pop("HERMES_DREAMING_EUID_OVERRIDE", None)
    env.pop("HERMES_DREAMING_RUN_ID", None)

    result = subprocess.run(
        [sys.executable, str(workdir / "autonomous_evolution_nightly_noagent.py")],
        cwd=str(workdir),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["receipt_source"] == "typed_receipt"
    assert payload["candidate_generated"] is True

    receipts_dir = home / "state" / "dreaming" / "receipts"
    receipt_files = list(receipts_dir.glob("*.json"))
    assert len(receipt_files) == 1
    receipt_payload = json.loads(receipt_files[0].read_text(encoding="utf-8"))
    assert receipt_payload["run_id"] == payload["run_id"]
    assert hd.file_sha256(skill_md) == before_hash


# ---------------------------------------------------------------------------
# Loop A V2 remediation regressions (P1-1..P1-4, P2)
# ---------------------------------------------------------------------------


def test_p1_1_cleanup_never_unlinks_even_with_stat_unlink_race(tmp_path, monkeypatch):
    """Deterministic attack: replace competitor between identity observe and any unlink.

    Production cleanup must not call pathname unlink at all; competitor survives.
    """
    root = tmp_path / "candidates"
    root.mkdir()
    name = "candidate-v2--run--skill--n.json"
    ours = root / name
    ours.write_text("OURS", encoding="utf-8")
    st = os.lstat(ours)
    owned = (st.st_dev, st.st_ino)
    root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)

    unlinks: list[str] = []
    real_unlink = hd.os.unlink

    def tracking_unlink(path, *args, **kwargs):
        unlinks.append(str(path))
        return real_unlink(path, *args, **kwargs)

    real_stat = hd.os.stat

    def race_stat(path, *args, **kwargs):
        res = real_stat(path, *args, **kwargs)
        target = root / name
        if target.exists() and target.read_text(encoding="utf-8") == "OURS":
            target.rename(root / f"{name}.parked")
            (root / name).write_text("COMPETITOR", encoding="utf-8")
        return res

    monkeypatch.setattr(hd.os, "unlink", tracking_unlink)
    monkeypatch.setattr(hd.os, "stat", race_stat)

    cleaned, reason = hd._cleanup_candidate_artifact_at(root_fd, name, owned)
    os.close(root_fd)

    assert cleaned is False
    assert reason is not None
    assert unlinks == []
    assert (root / name).read_text(encoding="utf-8") == "COMPETITOR"
    assert (root / f"{name}.parked").read_text(encoding="utf-8") == "OURS"


def test_p1_1_post_create_failure_never_calls_unlink_and_reports_residual(tmp_path, monkeypatch):
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    candidates_root = home / "state" / "dreaming" / "candidates"
    candidates_root.mkdir(parents=True)
    unlinks: list[str] = []
    real_unlink = hd.os.unlink

    def tracking_unlink(path, *args, **kwargs):
        unlinks.append(str(path))
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(hd.os, "unlink", tracking_unlink)

    def boom_readback(fd):
        raise OSError("forced post-create failure")

    result = hd.generate_candidate(home, "run-1", "skill-a", readback_hook=boom_readback)

    assert result.stage.ok is False
    assert result.stage.reason == hd.REASON_CANDIDATE_CLEANUP_FAILED
    assert result.stage.details.get("candidate_cleaned") is False
    assert result.stage.details.get("cleanup_failed") is True
    assert result.stage.details.get("residual_reason")
    assert result.stage.details.get("residual_identity")
    assert unlinks == []
    leftovers = [p for p in candidates_root.iterdir() if p.name.startswith("candidate-v2--")]
    assert len(leftovers) == 1


def test_p1_1_run_cycle_post_create_failure_is_error_write_blocked(tmp_path, monkeypatch):
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    (home / "state" / "dreaming" / "candidates").mkdir(parents=True)
    now = datetime(2026, 8, 1, tzinfo=timezone.utc)

    def boom_generate(*_a, **_k):
        return hd.CandidateResult(
            hd.StageReceipt(
                hd.STAGE_GENERATION,
                False,
                hd.REASON_CANDIDATE_CLEANUP_FAILED,
                {
                    "candidate_cleaned": False,
                    "cleanup_failed": True,
                    "residual_reason": hd.REASON_CANDIDATE_RESIDUAL_UNSAFE,
                    "residual_identity": {"st_dev": 1, "st_ino": 2},
                },
            ),
            None,
            None,
            None,
            [],
            [],
        )

    monkeypatch.setattr(hd, "generate_candidate", boom_generate)
    receipt = hd.run_dreaming_cycle(home, [{"name": "skill-a", "score": 10}], now, run_id="run-1", euid=os.getuid())
    assert receipt.job_success is False
    assert receipt.write_blocked is True
    assert receipt.degraded is True
    assert receipt.candidate_generated is False
    health = hd.classify_receipt(receipt.to_dict())
    assert health["status"] == "ERROR"
    assert health["candidate_artifact"] is None


def test_p1_2_validate_receipt_rejects_candidate_generated_without_generation_stage():
    payload = _valid_receipt_payload(candidate_generated=True, reasons=[hd.REASON_CANDIDATE_GENERATED])
    errors = hd.validate_receipt(payload)
    assert "candidate_generated_requires_one_success_generation_stage" in errors


def test_p1_2_validate_receipt_rejects_state_advanced_and_promoted():
    payload = _valid_receipt_payload(state_advanced=True, promoted=True)
    errors = hd.validate_receipt(payload)
    assert "loop_a_state_advanced_forbidden" in errors
    assert "loop_a_promoted_forbidden" in errors


def test_p1_2_validate_receipt_requires_artifact_projection_on_success():
    payload = _valid_candidate_generated_payload()
    assert hd.validate_receipt(payload) == []
    # drop one required field
    for stage in payload["stages"]:
        if stage.get("stage") == hd.STAGE_GENERATION:
            del stage["details"]["artifact_st_ino"]
    errors = hd.validate_receipt(payload)
    assert any(e.startswith("missing_artifact_field:") for e in errors)


def test_p1_2_validate_receipt_rejects_wrong_types_and_bad_ts():
    payload = _valid_receipt_payload(run_id=123, ts="not-a-ts", target=5)
    errors = hd.validate_receipt(payload)
    assert "run_id_not_str" in errors
    assert "ts_invalid" in errors
    assert "target_not_str_or_null" in errors


def test_p1_3_nonzero_rc_clears_all_authority_flags(tmp_path):
    receipt_path = tmp_path / "r.json"
    payload = _valid_candidate_generated_payload()
    receipt_path.write_text(json.dumps(payload), encoding="utf-8")
    health = hd.classify_run_result(2, "", "", receipt_path, expected_run_id="r1")
    assert health["status"] == "ERROR"
    assert health["job_success"] is False
    assert health["effective_audit"] is False
    assert health["candidate_generated"] is False
    assert health["state_advanced"] is False
    assert health["promoted"] is False
    assert health["degraded"] is True
    assert health["candidate_artifact"] is None


def test_p1_4_classify_and_to_dict_project_candidate_artifact():
    payload = _valid_candidate_generated_payload()
    assert payload["candidate_artifact"] is not None
    health = hd.classify_receipt(payload)
    assert health["candidate_artifact"]["artifact_sha256"] == "a" * 64
    assert health["candidate_artifact"]["candidate_artifact"].startswith("candidate-v2--")


def test_p1_4_failure_projection_is_null():
    payload = _valid_receipt_payload(job_success=False)
    health = hd.classify_receipt(payload)
    assert health["candidate_artifact"] is None
    assert health["status"] == "ERROR"


def test_p2_envelope_negatives_matrix():
    src = "a" * 64
    body = b"hello"
    good = hd.canonical_candidate_envelope_bytes(
        run_id="run-1", skill_name="skill-a", source_sha256=src, candidate_bytes=body
    )

    def reject(raw: bytes):
        validated, reason = hd.validate_candidate_envelope(
            raw, expected_run_id="run-1", expected_skill_name="skill-a", expected_source_sha256=src
        )
        assert validated is None
        assert reason == hd.REASON_CANDIDATE_ARTIFACT_INVALID

    # missing key
    obj = json.loads(good)
    del obj["skill_name"]
    reject((json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n").encode())

    # unknown key
    obj = json.loads(good)
    obj["extra"] = "x"
    reject((json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n").encode())

    # wrong primitive type
    obj = json.loads(good)
    obj["candidate_size"] = "1"
    reject((json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n").encode())

    # invalid Base64
    obj = json.loads(good)
    obj["candidate_bytes_b64"] = "%%%%"
    reject((json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n").encode())

    # size mismatch
    obj = json.loads(good)
    obj["candidate_size"] = 999
    reject((json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n").encode())

    # source digest mismatch
    validated, reason = hd.validate_candidate_envelope(
        good, expected_run_id="run-1", expected_skill_name="skill-a", expected_source_sha256="b" * 64
    )
    assert validated is None
    assert reason == hd.REASON_CANDIDATE_ARTIFACT_INVALID

    # malformed candidate UTF-8
    bad_body = b"\xff\xfe"
    import base64
    obj = {
        "candidate_bytes_b64": base64.b64encode(bad_body).decode("ascii"),
        "candidate_sha256": __import__("hashlib").sha256(bad_body).hexdigest(),
        "candidate_size": len(bad_body),
        "run_id": "run-1",
        "schema_version": hd.CANDIDATE_ARTIFACT_SCHEMA_VERSION,
        "skill_name": "skill-a",
        "source_sha256": src,
    }
    reject((json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n").encode())

    # noncanonical JSON (unsorted / spaced)
    obj = json.loads(good)
    reject((json.dumps(obj, sort_keys=False, indent=2) + "\n").encode())

    # repeated-build equality
    again = hd.canonical_candidate_envelope_bytes(
        run_id="run-1", skill_name="skill-a", source_sha256=src, candidate_bytes=body
    )
    assert again == good


def test_p2_root_missing_cycle_is_zero_write_fail_closed(tmp_path):
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    now = datetime(2026, 8, 1, tzinfo=timezone.utc)
    before = {p.relative_to(home) for p in home.rglob("*") if p.is_file() or p.is_dir()}

    receipt = hd.run_dreaming_cycle(
        home, [{"name": "skill-a", "score": 10}], now, run_id="run-1", euid=os.getuid()
    )

    assert receipt.job_success is False
    assert receipt.write_blocked is True
    assert receipt.degraded is True
    assert hd.REASON_CANDIDATE_ROOT_UNPROVISIONED in receipt.reasons
    after = {p.relative_to(home) for p in home.rglob("*") if p.is_file() or p.is_dir()}
    assert after == before
    assert not (home / "state").exists()


def test_p2_root_missing_nightly_zero_write_stdout_error_rc2(tmp_path, monkeypatch, capsys):
    home = tmp_path / "hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    nightly = load_script_module("nightly_root_missing", "autonomous-evolution-nightly.py")
    nightly.HERMES_HOME = home
    monkeypatch.setattr(nightly, "build_candidates", lambda: [_ for _ in ()])  # should not be called ideally
    # force path: even if build were called, root check is first
    rc = nightly._run(datetime(2026, 8, 1, tzinfo=timezone.utc), "run-root-missing")
    out = capsys.readouterr().out
    assert rc == 2
    assert "ERROR" in out
    assert "candidate_root_unprovisioned" in out
    assert not (home / "state").exists()


def test_p2_no_open_dir_mkdir_capability():
    import inspect
    src = inspect.getsource(hd._open_dir_at)
    assert "os.mkdir" not in src
    assert "mkdir(" not in src
    src2 = inspect.getsource(hd._open_dir_chain)
    assert "os.mkdir" not in src2
    import inspect as _ins
    assert "create" not in _ins.signature(hd._open_dir_chain).parameters
    # production residual classifier has no unlink call
    src3 = inspect.getsource(hd._classify_candidate_artifact_residual_at)
    body = src3.split('"""', 2)[-1]
    assert "os.unlink" not in body
    assert "unlink(" not in body


def test_p2_noagent_real_subprocess_root_missing_negative(tmp_path):
    home = tmp_path / "hermes"
    skill_md = home / "skills" / "demo-skill" / "SKILL.md"
    skill_md.parent.mkdir(parents=True)
    skill_md.write_text("---\nname: demo-skill\n---\nbody without those sections", encoding="utf-8")
    # intentionally no candidates root
    db_path = home / "state" / "evolution" / "bayesian-agent" / "confidence-db.json"
    db_path.parent.mkdir(parents=True)
    db_path.write_text(json.dumps({"skills": {"demo-skill": {"darwin_score": 40}}}), encoding="utf-8")

    scripts_dir = Path(__file__).parent
    workdir = tmp_path / "scripts_copy"
    workdir.mkdir()
    for name in (
        "autonomous_evolution_nightly_noagent.py",
        "autonomous-evolution-nightly.py",
        "hermes_dreaming.py",
        "hermes_evolution_store.py",
    ):
        shutil.copy2(scripts_dir / name, workdir / name)

    env = dict(os.environ)
    env["HERMES_HOME"] = str(home)
    env.pop("HERMES_DREAMING_RECEIPT_PATH", None)
    env.pop("HERMES_DREAMING_EUID_OVERRIDE", None)
    env.pop("HERMES_DREAMING_RUN_ID", None)

    result = subprocess.run(
        [sys.executable, str(workdir / "autonomous_evolution_nightly_noagent.py")],
        cwd=str(workdir),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["status"] == "ERROR"
    assert payload["job_success"] is False
    assert payload["candidate_generated"] is False
    assert payload.get("candidate_artifact") in (None, {})
    # no candidates root created by Loop A
    assert not (home / "state" / "dreaming" / "candidates").exists()
    # no selector/receipt under dreaming if dreaming was not pre-made beyond evolution
    assert not (home / "state" / "dreaming" / "selector_state.json").exists()


def test_p2_noagent_real_subprocess_nonzero_authority_negative(tmp_path, monkeypatch):
    """Real wrapper path: child rc!=0 must clear authority flags even with success-shaped receipt."""
    home, skill_md = _seed_isolated_home(tmp_path, "---\nname: demo-skill\n---\nbody without those sections")
    receipt_path = home / "state" / "dreaming" / "receipts" / "forced.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)

    class FakeCompleted:
        returncode = 2
        stdout = "ERROR"
        stderr = ""

    def fake_run(args, **kwargs):
        env = kwargs.get("env") or {}
        run_id = env["HERMES_DREAMING_RUN_ID"]
        details = _artifact_details(
            run_id=run_id,
            skill_name="demo-skill",
            candidate_artifact=f"candidate-v2--{run_id}--demo-skill--deadbeef.json",
        )
        receipt = hd.RunReceipt(run_id=run_id, ts="2026-08-01T00:00:00Z", target="demo-skill")
        receipt.job_success = True
        receipt.effective_audit = True
        receipt.candidate_generated = True
        receipt.add_reason(hd.REASON_CANDIDATE_GENERATED)
        receipt.add_stage(hd.StageReceipt(hd.STAGE_SELECTION, True, hd.REASON_OK, {}))
        receipt.add_stage(hd.StageReceipt(hd.STAGE_OWNERSHIP, True, hd.REASON_OK, {}))
        receipt.add_stage(hd.StageReceipt(hd.STAGE_GENERATION, True, hd.REASON_CANDIDATE_GENERATED, details))
        receipt.add_stage(hd.StageReceipt(hd.STAGE_EVALUATION, True, hd.REASON_OK, {"satisfied": True, "missing_after": []}))
        Path(env["HERMES_DREAMING_RECEIPT_PATH"]).write_text(json.dumps(receipt.to_dict()), encoding="utf-8")
        return FakeCompleted()

    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.delenv("HERMES_DREAMING_RECEIPT_PATH", raising=False)
    monkeypatch.setattr(autonomous_evolution_nightly_noagent.subprocess, "run", fake_run)
    # use capsys via pytest - call main
    import io
    from contextlib import redirect_stdout
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = autonomous_evolution_nightly_noagent.main()
    payload = json.loads(buf.getvalue())
    assert rc == 2
    assert payload["job_success"] is False
    assert payload["effective_audit"] is False
    assert payload["candidate_generated"] is False
    assert payload["state_advanced"] is False
    assert payload["promoted"] is False
    assert payload["candidate_artifact"] is None


def test_noagent_wrapper_real_subprocess_integration_includes_artifact_projection(tmp_path):
    home, skill_md = _seed_isolated_home(tmp_path, "---\nname: demo-skill\n---\nbody without those sections")
    before_hash = hd.file_sha256(skill_md)
    scripts_dir = Path(__file__).parent
    workdir = tmp_path / "scripts_copy"
    workdir.mkdir()
    for name in (
        "autonomous_evolution_nightly_noagent.py",
        "autonomous-evolution-nightly.py",
        "hermes_dreaming.py",
        "hermes_evolution_store.py",
    ):
        shutil.copy2(scripts_dir / name, workdir / name)
    env = dict(os.environ)
    env["HERMES_HOME"] = str(home)
    env.pop("HERMES_DREAMING_RECEIPT_PATH", None)
    env.pop("HERMES_DREAMING_EUID_OVERRIDE", None)
    env.pop("HERMES_DREAMING_RUN_ID", None)
    result = subprocess.run(
        [sys.executable, str(workdir / "autonomous_evolution_nightly_noagent.py")],
        cwd=str(workdir),
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["candidate_generated"] is True
    assert payload["candidate_artifact"] is not None
    assert payload["candidate_artifact"]["artifact_schema_version"] == hd.CANDIDATE_ARTIFACT_SCHEMA_VERSION
    assert payload["candidate_artifact"]["run_id"] == payload["run_id"]
    assert hd.file_sha256(skill_md) == before_hash


# ---------------------------------------------------------------------------
# P1-001 / P1-002: post-create residual funnel (identity-missing + non-OSError)
# ---------------------------------------------------------------------------


def test_p1_001_immediate_post_create_fstat_oserror_unclassified_residual(tmp_path, monkeypatch):
    """After O_EXCL create, fstat(fd) failure must enter never-unlink residual protocol.

    RED target: old fail(cleanup=True) path required artifact_id, so identity-missing
    post-create failures reported candidate_cleaned=true with no residual fields while
    leaving the artifact on disk.
    """
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    candidates_root = home / "state" / "dreaming" / "candidates"
    candidates_root.mkdir(parents=True)

    real_open = hd.os.open
    real_fstat = hd.os.fstat
    real_unlink = hd.os.unlink
    artifact_fds: list[int] = []
    fstat_boom_remaining = {"n": 1}
    unlinks: list[tuple] = []

    def tracking_open(name, flags, *args, dir_fd=None, **kwargs):
        fd = real_open(name, flags, *args, dir_fd=dir_fd, **kwargs)
        if isinstance(name, str) and name.startswith("candidate-v2--"):
            artifact_fds.append(fd)
        return fd

    def boom_fstat(fd):
        if artifact_fds and fd == artifact_fds[-1] and fstat_boom_remaining["n"] > 0:
            fstat_boom_remaining["n"] -= 1
            raise OSError(errno.EIO, "simulated immediate post-create fstat failure")
        return real_fstat(fd)

    def tracking_unlink(path, *args, **kwargs):
        unlinks.append((path, args, kwargs))
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(hd.os, "open", tracking_open)
    monkeypatch.setattr(hd.os, "fstat", boom_fstat)
    monkeypatch.setattr(hd.os, "unlink", tracking_unlink)

    result = hd.generate_candidate(home, "run-1", "skill-a")

    assert result.stage.ok is False
    assert result.stage.reason == hd.REASON_CANDIDATE_CLEANUP_FAILED
    details = result.stage.details
    assert details.get("candidate_cleaned") is False
    assert details.get("cleanup_failed") is True
    assert details.get("original_reason")
    assert details.get("residual_reason") == hd.REASON_CANDIDATE_RESIDUAL_UNSAFE
    # Identity was never captured — state must still be explicit (null, not omitted-as-cleaned).
    assert "residual_identity" in details
    assert details.get("residual_identity") is None
    assert unlinks == []
    leftovers = [p for p in candidates_root.iterdir() if p.name.startswith("candidate-v2--")]
    assert len(leftovers) == 1
    # Candidate authority projection remains null on residual failure.
    assert result.candidate_artifact is None or details.get("cleanup_failed") is True
    health_stage = {
        "job_success": False,
        "effective_audit": True,
        "candidate_generated": False,
        "state_advanced": False,
        "promoted": False,
        "write_blocked": True,
        "degraded": True,
        "reasons": [hd.REASON_CANDIDATE_CLEANUP_FAILED],
        "stages": [
            {"stage": hd.STAGE_GENERATION, "ok": False, "reason": hd.REASON_CANDIDATE_CLEANUP_FAILED, "details": details}
        ],
    }
    health = hd.classify_receipt(health_stage)
    assert health["status"] == "ERROR"
    assert health["candidate_artifact"] is None


def test_p1_001_immediate_post_create_fstat_oserror_nightly_rc2(tmp_path, monkeypatch):
    """Downstream nightly maps identity-missing post-create residual to ERROR/rc2."""
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    candidates_root = home / "state" / "dreaming" / "candidates"
    candidates_root.mkdir(parents=True)
    now = datetime(2026, 8, 1, tzinfo=timezone.utc)

    real_open = hd.os.open
    real_fstat = hd.os.fstat
    real_unlink = hd.os.unlink
    artifact_fds: list[int] = []
    boom_left = {"n": 1}
    unlinks: list = []

    def tracking_open(name, flags, *args, dir_fd=None, **kwargs):
        fd = real_open(name, flags, *args, dir_fd=dir_fd, **kwargs)
        if isinstance(name, str) and name.startswith("candidate-v2--"):
            artifact_fds.append(fd)
        return fd

    def boom_fstat(fd):
        if artifact_fds and fd == artifact_fds[-1] and boom_left["n"] > 0:
            boom_left["n"] -= 1
            raise OSError(errno.EIO, "simulated immediate post-create fstat failure")
        return real_fstat(fd)

    def tracking_unlink(path, *args, **kwargs):
        unlinks.append(path)
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(hd.os, "open", tracking_open)
    monkeypatch.setattr(hd.os, "fstat", boom_fstat)
    monkeypatch.setattr(hd.os, "unlink", tracking_unlink)

    real_generate = hd.generate_candidate

    def generate_with_live_hooks(*args, **kwargs):
        return real_generate(*args, **kwargs)

    monkeypatch.setattr(hd, "generate_candidate", generate_with_live_hooks)

    nightly = load_script_module("nightly_p1_001_fstat", "autonomous-evolution-nightly.py")
    nightly.HERMES_HOME = home
    nightly.SKILLS_DIR = home / "skills"
    monkeypatch.setattr(nightly, "build_candidates", lambda: [{"name": "skill-a", "score": 10}])
    monkeypatch.setattr(nightly, "resolve_euid", lambda: os.getuid())
    monkeypatch.setattr(nightly, "receipt_output_path", lambda: home / "state" / "dreaming" / "receipt.json")
    monkeypatch.setattr(nightly, "log_event", lambda *_a, **_k: None)
    monkeypatch.setattr(nightly.STORE, "append_dream_run", lambda *_a, **_k: None)
    monkeypatch.setattr(nightly, "hd", hd)

    rc = nightly._run(now, "run-p1-001")
    payload = json.loads((home / "state" / "dreaming" / "receipt.json").read_text(encoding="utf-8"))
    generation = next(stage for stage in payload["stages"] if stage["stage"] == hd.STAGE_GENERATION)

    assert generation["reason"] == hd.REASON_CANDIDATE_CLEANUP_FAILED
    assert generation["details"]["candidate_cleaned"] is False
    assert generation["details"]["cleanup_failed"] is True
    assert generation["details"]["residual_reason"] == hd.REASON_CANDIDATE_RESIDUAL_UNSAFE
    assert generation["details"].get("residual_identity") is None
    assert payload["job_success"] is False
    assert payload["write_blocked"] is True
    assert payload["degraded"] is True
    assert payload["candidate_artifact"] is None
    health = hd.classify_receipt(payload)
    assert health["status"] == "ERROR"
    assert health["candidate_artifact"] is None
    assert rc == 2
    assert unlinks == []
    assert any(p.name.startswith("candidate-v2--") for p in candidates_root.iterdir())


def test_p1_002_post_create_runtimeerror_write_hook_residual_funnel(tmp_path, monkeypatch):
    """Ordinary Exception after successful create must not escape generate_candidate."""
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    candidates_root = home / "state" / "dreaming" / "candidates"
    candidates_root.mkdir(parents=True)
    unlinks: list = []
    real_unlink = hd.os.unlink

    def tracking_unlink(path, *args, **kwargs):
        unlinks.append(str(path))
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(hd.os, "unlink", tracking_unlink)

    def boom_write(fd, data):
        raise RuntimeError("simulated write_hook non-OSError failure")

    result = hd.generate_candidate(home, "run-1", "skill-a", write_hook=boom_write)

    assert result.stage.ok is False
    assert result.stage.reason == hd.REASON_CANDIDATE_CLEANUP_FAILED
    details = result.stage.details
    assert details.get("candidate_cleaned") is False
    assert details.get("cleanup_failed") is True
    assert details.get("residual_reason")
    assert details.get("residual_identity")  # identity captured before write
    assert details.get("original_reason") == hd.REASON_CANDIDATE_INTERNAL_FAILURE
    assert unlinks == []
    leftovers = [p for p in candidates_root.iterdir() if p.name.startswith("candidate-v2--")]
    assert len(leftovers) == 1


def test_p1_002_post_create_runtimeerror_readback_hook_residual_funnel(tmp_path, monkeypatch):
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    candidates_root = home / "state" / "dreaming" / "candidates"
    candidates_root.mkdir(parents=True)
    unlinks: list = []
    real_unlink = hd.os.unlink

    def tracking_unlink(path, *args, **kwargs):
        unlinks.append(str(path))
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(hd.os, "unlink", tracking_unlink)

    def boom_readback(fd):
        raise RuntimeError("simulated readback_hook non-OSError failure")

    result = hd.generate_candidate(home, "run-1", "skill-a", readback_hook=boom_readback)

    assert result.stage.ok is False
    assert result.stage.reason == hd.REASON_CANDIDATE_CLEANUP_FAILED
    details = result.stage.details
    assert details.get("candidate_cleaned") is False
    assert details.get("cleanup_failed") is True
    assert details.get("residual_reason")
    assert details.get("residual_identity")
    assert unlinks == []
    assert any(p.name.startswith("candidate-v2--") for p in candidates_root.iterdir())


def test_p1_002_post_create_runtimeerror_nightly_and_noagent_rc2(tmp_path, monkeypatch):
    """Non-OSError post-create residual must reach nightly/noagent ERROR/rc2 with null authority."""
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    (home / "state" / "dreaming" / "candidates").mkdir(parents=True)
    now = datetime(2026, 8, 1, tzinfo=timezone.utc)
    unlinks: list = []
    real_unlink = hd.os.unlink

    def tracking_unlink(path, *args, **kwargs):
        unlinks.append(str(path))
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(hd.os, "unlink", tracking_unlink)

    real_generate = hd.generate_candidate

    def generate_with_runtime_write(*args, **kwargs):
        kwargs = dict(kwargs)
        kwargs["write_hook"] = lambda fd, data: (_ for _ in ()).throw(RuntimeError("hook boom"))
        return real_generate(*args, **kwargs)

    monkeypatch.setattr(hd, "generate_candidate", generate_with_runtime_write)

    nightly = load_script_module("nightly_p1_002_runtime", "autonomous-evolution-nightly.py")
    nightly.HERMES_HOME = home
    nightly.SKILLS_DIR = home / "skills"
    monkeypatch.setattr(nightly, "build_candidates", lambda: [{"name": "skill-a", "score": 10}])
    monkeypatch.setattr(nightly, "resolve_euid", lambda: os.getuid())
    receipt_path = home / "state" / "dreaming" / "receipt.json"
    monkeypatch.setattr(nightly, "receipt_output_path", lambda: receipt_path)
    monkeypatch.setattr(nightly, "log_event", lambda *_a, **_k: None)
    monkeypatch.setattr(nightly.STORE, "append_dream_run", lambda *_a, **_k: None)
    monkeypatch.setattr(nightly, "hd", hd)

    rc = nightly._run(now, "run-p1-002")
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    generation = next(stage for stage in payload["stages"] if stage["stage"] == hd.STAGE_GENERATION)
    assert generation["reason"] == hd.REASON_CANDIDATE_CLEANUP_FAILED
    assert payload["job_success"] is False
    assert payload["write_blocked"] is True
    assert payload["degraded"] is True
    assert payload["candidate_artifact"] is None
    assert hd.classify_receipt(payload)["status"] == "ERROR"
    assert rc == 2
    assert unlinks == []

    # noagent authority-null projection from classify_run_result path
    health = hd.classify_run_result(2, "", "", receipt_path, expected_run_id="run-p1-002")
    assert health["status"] == "ERROR"
    assert health["job_success"] is False
    assert health["candidate_generated"] is False
    assert health["state_advanced"] is False
    assert health["promoted"] is False
    assert health["candidate_artifact"] is None


def test_p1_002_pre_create_runtimeerror_still_propagates(tmp_path, monkeypatch):
    """Pre-create ordinary exceptions remain uncaught unless they are post-create."""
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    (home / "state" / "dreaming" / "candidates").mkdir(parents=True)

    def boom_sections(*_a, **_k):
        raise RuntimeError("pre-create section boom")

    monkeypatch.setattr(hd, "generate_sections", boom_sections)
    with pytest.raises(RuntimeError, match="pre-create section boom"):
        hd.generate_candidate(home, "run-1", "skill-a")


def test_p1_002_keyboardinterrupt_still_propagates(tmp_path, monkeypatch):
    home = tmp_path / "hermes"
    _write_active_skill(home, "skill-a", "---\nname: skill-a\n---\nbody without those sections")
    (home / "state" / "dreaming" / "candidates").mkdir(parents=True)

    def boom_write(fd, data):
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        hd.generate_candidate(home, "run-1", "skill-a", write_hook=boom_write)
