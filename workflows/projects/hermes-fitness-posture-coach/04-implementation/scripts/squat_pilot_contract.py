#!/usr/bin/env python3
"""Low-risk bodyweight squat pilot contract.

This module deliberately uses pose-derived proxy fields only. It does not claim
medical diagnosis or coaching quality; missing/low-confidence evidence stops the
flow and asks for camera adjustment.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

IMPLEMENTATION_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = IMPLEMENTATION_ROOT / "data" / "derived" / "squat_pilot_replay_receipt.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def classify_phase(frame: dict[str, Any], previous: dict[str, Any] | None = None) -> str:
    knee_angle = float(frame.get("knee_angle", 0) or 0)
    hip_y = float(frame.get("hip_y", 0) or 0)
    prev_hip_y = float(previous.get("hip_y", hip_y) if previous else hip_y)

    if knee_angle >= 160:
        return "setup"
    if knee_angle <= 95:
        return "bottom"
    if hip_y > prev_hip_y + 0.03:
        return "eccentric"
    if hip_y < prev_hip_y - 0.03:
        return "concentric"
    return "hold"


def safety_stop(frames: list[dict[str, Any]], user_flags: dict[str, Any]) -> dict[str, Any] | None:
    if user_flags.get("pain") or user_flags.get("numbness") or user_flags.get("dizziness"):
        return {
            "risk_level": "stop",
            "should_interrupt": True,
            "requires_confirmation": True,
            "camera_instruction": None,
            "speak_text": "Stop. 身体不适先停止。",
            "subtitle": "Stop because pain/numbness/dizziness was declared; no diagnosis or treatment advice is produced.",
            "next_action": "stop",
        }
    if user_flags.get("heavy_load"):
        return {
            "risk_level": "stop",
            "should_interrupt": True,
            "requires_confirmation": True,
            "camera_instruction": None,
            "speak_text": "Stop. 重负荷不在当前试点范围。",
            "subtitle": "Stop because heavy load was declared/visible; current pilot is bodyweight-only.",
            "next_action": "stop",
        }
    if not frames or min(float(f.get("visibility_min", 0) or 0) for f in frames) < 0.55:
        return {
            "risk_level": "stop",
            "should_interrupt": True,
            "requires_confirmation": False,
            "camera_instruction": "fixed_full_body_side_view",
            "speak_text": "Missing critical joints. 调整侧面全身机位。",
            "subtitle": "Missing critical joints or low pose confidence; camera adjustment required before form judgment.",
            "next_action": "adjust_camera",
        }
    return None


def evaluate_squat_sequence(frames: list[dict[str, Any]], user_flags: dict[str, Any] | None = None) -> dict[str, Any]:
    flags = dict(user_flags or {})
    stop = safety_stop(frames, flags)
    evaluated_frames: list[dict[str, Any]] = []
    previous: dict[str, Any] | None = None
    for frame in frames:
        phase = classify_phase(frame, previous)
        evaluated_frames.append({
            "frame_id": frame.get("frame_id"),
            "phase": phase,
            "knee_angle": frame.get("knee_angle"),
            "visibility_min": frame.get("visibility_min"),
            "evidence_refs": [f"frame:{frame.get('frame_id')}", f"pose:{frame.get('frame_id')}"],
        })
        previous = frame

    if stop:
        return {
            "mode": "fitness_posture",
            "intent": "inspect_form",
            "exercise_id": "bodyweight-squat",
            "exercise_name": "Bodyweight squat",
            "phase": evaluated_frames[-1]["phase"] if evaluated_frames else "unknown",
            "confidence": min(float(f.get("visibility_min", 0) or 0) for f in frames) if frames else 0.0,
            "overlay": [],
            "evidence_refs": [ref for f in evaluated_frames for ref in f["evidence_refs"]],
            "frames": evaluated_frames,
            **stop,
        }

    return {
        "mode": "fitness_posture",
        "intent": "inspect_form",
        "exercise_id": "bodyweight-squat",
        "exercise_name": "Bodyweight squat",
        "phase": evaluated_frames[-1]["phase"] if evaluated_frames else "unknown",
        "speak_text": "节奏稳定，继续。",
        "subtitle": "Low-risk bodyweight squat pilot only; proxy rules classify phase and preserve local evidence refs.",
        "camera_instruction": None,
        "confidence": round(min(float(f.get("visibility_min", 0) or 0) for f in frames), 3) if frames else 0.0,
        "risk_level": "low",
        "should_interrupt": False,
        "requires_confirmation": False,
        "overlay": [{"type": "angle", "target": "knee", "value": f.get("knee_angle")} for f in evaluated_frames],
        "evidence_refs": [ref for f in evaluated_frames for ref in f["evidence_refs"]],
        "next_action": "continue",
        "frames": evaluated_frames,
    }


def deterministic_replay() -> dict[str, Any]:
    frames = [
        {"frame_id": "f1", "hip_y": 0.42, "knee_y": 0.62, "ankle_y": 0.88, "knee_angle": 172, "visibility_min": 0.92},
        {"frame_id": "f2", "hip_y": 0.55, "knee_y": 0.63, "ankle_y": 0.88, "knee_angle": 126, "visibility_min": 0.90},
        {"frame_id": "f3", "hip_y": 0.69, "knee_y": 0.64, "ankle_y": 0.88, "knee_angle": 88, "visibility_min": 0.91},
        {"frame_id": "f4", "hip_y": 0.50, "knee_y": 0.62, "ankle_y": 0.88, "knee_angle": 142, "visibility_min": 0.90},
    ]
    return {
        "schema": "fitness_posture_squat_pilot_replay_v1",
        "generated_at": utc_now(),
        "boundary": "deterministic proxy replay; no medical diagnosis; no heavy-load coaching",
        "result": evaluate_squat_sequence(frames),
        "safety_stop_low_visibility": evaluate_squat_sequence([{**frames[0], "visibility_min": 0.25}]),
        "safety_stop_pain": evaluate_squat_sequence([frames[0]], user_flags={"pain": True}),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    args = parser.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    receipt = deterministic_replay()
    out.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "OK", "out": str(out), "schema": receipt["schema"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
