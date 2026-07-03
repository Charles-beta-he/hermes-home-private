#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "ui" / "review.html"
SEED = ROOT / "data" / "derived" / "exercise_seed_index.json"
LEDGER = ROOT.parents[0] / "progress-ledger.md"


def test_review_ui_exists_and_binds_seed_and_evidence_paths():
    html = UI.read_text(encoding="utf-8")
    assert "exercise_seed_index.json" in html
    assert "progress-ledger.md" in html
    assert "pose_adapter_spike_receipt.json" in html
    assert "squat_pilot_replay_receipt.json" in html
    assert SEED.exists()
    assert LEDGER.exists()


def test_review_ui_has_camera_checklist_but_no_default_media_start():
    html = UI.read_text(encoding="utf-8")
    assert "Camera setup checklist" in html
    assert "Full-body side view" in html
    assert "Start camera" in html
    assert "autoplay" not in html.lower()
    assert "getUserMedia" not in html
    assert "navigator.mediaDevices" not in html
    assert "camera-default-off" in html


def test_review_ui_has_posture_result_surface():
    html = UI.read_text(encoding="utf-8")
    assert "Posture result" in html
    assert "risk_level" in html
    assert "should_interrupt" in html
    assert "Local-only" in html
