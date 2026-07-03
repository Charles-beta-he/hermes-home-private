#!/usr/bin/env python3
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "squat_pilot_contract.py"
spec = importlib.util.spec_from_file_location("squat_pilot_contract", MODULE)
squat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(squat)  # type: ignore[union-attr]


def test_classifies_squat_phase_from_pose_proxy_sequence():
    frames = [
        {"frame_id": "f1", "hip_y": 0.42, "knee_y": 0.62, "ankle_y": 0.88, "knee_angle": 172, "visibility_min": 0.92},
        {"frame_id": "f2", "hip_y": 0.55, "knee_y": 0.63, "ankle_y": 0.88, "knee_angle": 126, "visibility_min": 0.90},
        {"frame_id": "f3", "hip_y": 0.69, "knee_y": 0.64, "ankle_y": 0.88, "knee_angle": 88, "visibility_min": 0.91},
        {"frame_id": "f4", "hip_y": 0.50, "knee_y": 0.62, "ankle_y": 0.88, "knee_angle": 142, "visibility_min": 0.90},
    ]

    result = squat.evaluate_squat_sequence(frames)

    assert result["exercise_id"] == "bodyweight-squat"
    assert [step["phase"] for step in result["frames"]] == ["setup", "eccentric", "bottom", "concentric"]
    assert result["risk_level"] == "low"
    assert result["should_interrupt"] is False
    assert result["next_action"] == "continue"


def test_stops_when_critical_pose_visibility_is_low():
    frames = [
        {"frame_id": "f1", "hip_y": 0.42, "knee_y": 0.62, "ankle_y": 0.88, "knee_angle": 172, "visibility_min": 0.25},
    ]

    result = squat.evaluate_squat_sequence(frames)

    assert result["risk_level"] == "stop"
    assert result["should_interrupt"] is True
    assert result["next_action"] == "adjust_camera"
    assert result["camera_instruction"] == "fixed_full_body_side_view"
    assert "Missing critical joints" in result["speak_text"]


def test_stops_on_declared_pain_or_heavy_load():
    frames = [{"frame_id": "f1", "hip_y": 0.42, "knee_y": 0.62, "ankle_y": 0.88, "knee_angle": 172, "visibility_min": 0.95}]

    pain = squat.evaluate_squat_sequence(frames, user_flags={"pain": True})
    heavy = squat.evaluate_squat_sequence(frames, user_flags={"heavy_load": True})

    assert pain["risk_level"] == "stop"
    assert pain["should_interrupt"] is True
    assert "Stop" in pain["speak_text"]
    assert heavy["risk_level"] == "stop"
    assert heavy["should_interrupt"] is True
    assert "heavy load" in heavy["subtitle"]
