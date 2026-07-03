#!/usr/bin/env python3
"""Local pose-adapter spike for Hermes Fitness Posture Coach.

This script is intentionally no-stub: it only reports keypoints when a real
local adapter returns them. Missing dependencies or missing pose evidence are
serialized as fail-closed receipts, not fabricated landmarks.
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np


IMPLEMENTATION_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = IMPLEMENTATION_ROOT / "data" / "derived" / "pose_adapter_spike_receipt.json"
DEFAULT_FRAME = IMPLEMENTATION_ROOT / "data" / "derived" / "pose_adapter_smoke_frame.png"
DEFAULT_MODEL = IMPLEMENTATION_ROOT / "models" / "pose_landmarker_lite.task"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def make_smoke_frame(path: Path) -> None:
    """Create a deterministic local frame for adapter execution smoke.

    The frame is not claimed as a real human-pose benchmark. It exercises the
    adapter path and should usually produce `no_pose_detected`, proving the
    no-stub/fail-closed path is wired.
    """
    img = np.full((480, 320, 3), 255, dtype=np.uint8)
    # Draw a simple non-photorealistic stick figure; this is execution smoke,
    # not positive domain-quality evidence.
    cv2.circle(img, (160, 80), 28, (0, 0, 0), 3)
    cv2.line(img, (160, 108), (160, 255), (0, 0, 0), 5)
    cv2.line(img, (160, 145), (95, 205), (0, 0, 0), 5)
    cv2.line(img, (160, 145), (225, 205), (0, 0, 0), 5)
    cv2.line(img, (160, 255), (115, 375), (0, 0, 0), 5)
    cv2.line(img, (160, 255), (205, 375), (0, 0, 0), 5)
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), img)


def run_mediapipe(frame_path: Path, model_path: Path) -> dict:
    try:
        import mediapipe as mp  # type: ignore
    except Exception as exc:  # pragma: no cover - environment receipt path
        return {
            "status": "adapter_unavailable",
            "fail_closed": True,
            "reason": f"mediapipe import failed: {type(exc).__name__}: {exc}",
            "landmarks_count": 0,
            "keypoints": [],
        }

    image_bgr = cv2.imread(str(frame_path))
    if image_bgr is None:
        return {
            "status": "frame_unreadable",
            "fail_closed": True,
            "reason": f"cv2.imread returned None for {frame_path}",
            "landmarks_count": 0,
            "keypoints": [],
        }

    # MediaPipe 0.10.35 exposes the Tasks API (not the legacy `solutions` API).
    # Prefer Tasks with an explicit local model file; fall back to the legacy
    # API only if this runtime provides it. Both paths are real adapter calls.
    if model_path.exists():
        try:
            from mediapipe.tasks import python as mp_python  # type: ignore
            from mediapipe.tasks.python import vision  # type: ignore

            image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image_rgb)
            options = vision.PoseLandmarkerOptions(
                base_options=mp_python.BaseOptions(model_asset_path=str(model_path)),
                running_mode=vision.RunningMode.IMAGE,
                num_poses=1,
            )
            with vision.PoseLandmarker.create_from_options(options) as landmarker:
                detection = landmarker.detect(mp_image)
            landmarks = detection.pose_landmarks[0] if detection.pose_landmarks else []
            if not landmarks:
                return {
                    "status": "no_pose_detected",
                    "fail_closed": True,
                    "reason": "real MediaPipe Tasks PoseLandmarker executed but returned no landmarks for deterministic smoke frame; no keypoints fabricated",
                    "landmarks_count": 0,
                    "keypoints": [],
                    "model_asset": str(model_path),
                }
            keypoints = []
            for idx, lm in enumerate(landmarks):
                keypoints.append({
                    "index": idx,
                    "x": round(float(lm.x), 6),
                    "y": round(float(lm.y), 6),
                    "z": round(float(lm.z), 6),
                    "visibility": round(float(lm.visibility), 6),
                })
            return {
                "status": "pose_detected",
                "fail_closed": False,
                "reason": "real MediaPipe Tasks PoseLandmarker returned landmarks",
                "landmarks_count": len(keypoints),
                "keypoints": keypoints,
                "model_asset": str(model_path),
            }
        except Exception as exc:
            return {
                "status": "adapter_runtime_error",
                "fail_closed": True,
                "reason": f"MediaPipe Tasks PoseLandmarker failed: {type(exc).__name__}: {exc}",
                "landmarks_count": 0,
                "keypoints": [],
                "model_asset": str(model_path),
            }

    if hasattr(mp, "solutions"):
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        pose = mp.solutions.pose.Pose(static_image_mode=True, model_complexity=1)
        try:
            result = pose.process(image_rgb)
        finally:
            pose.close()

        if not result.pose_landmarks:
            return {
                "status": "no_pose_detected",
                "fail_closed": True,
                "reason": "real MediaPipe legacy Pose executed but returned no landmarks for deterministic smoke frame; no keypoints fabricated",
                "landmarks_count": 0,
                "keypoints": [],
            }

        keypoints = []
        for idx, lm in enumerate(result.pose_landmarks.landmark):
            keypoints.append({
                "index": idx,
                "x": round(float(lm.x), 6),
                "y": round(float(lm.y), 6),
                "z": round(float(lm.z), 6),
                "visibility": round(float(lm.visibility), 6),
            })
        return {
            "status": "pose_detected",
            "fail_closed": False,
            "reason": "real MediaPipe legacy Pose returned landmarks",
            "landmarks_count": len(keypoints),
            "keypoints": keypoints,
        }

    return {
        "status": "adapter_unavailable",
        "fail_closed": True,
        "reason": f"mediapipe {getattr(mp, '__version__', 'unknown')} has neither local model at {model_path} nor legacy solutions API",
        "landmarks_count": 0,
        "keypoints": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--frame", default=str(DEFAULT_FRAME))
    parser.add_argument("--model", default=str(DEFAULT_MODEL))
    args = parser.parse_args()

    out = Path(args.out)
    frame = Path(args.frame)
    model = Path(args.model)
    make_smoke_frame(frame)
    adapter_result = run_mediapipe(frame, model)

    receipt = {
        "schema": "fitness_posture_pose_adapter_spike_v1",
        "generated_at": utc_now(),
        "project": "hermes-fitness-posture-coach",
        "selected_adapter": "mediapipe_pose_local",
        "adapter_comparison": [
            {
                "adapter": "MediaPipe Pose",
                "decision": "selected_for_initial_local_spike",
                "rationale": "pip-installable local CPU path on macOS; returns explicit landmark visibility; adequate for fail-closed smoke before product quality claims",
            },
            {
                "adapter": "MoveNet/TF.js or TFLite",
                "decision": "defer",
                "rationale": "good mobile/web target, but needs model packaging and separate runtime contract",
            },
            {
                "adapter": "RTMPose/MMPose",
                "decision": "defer",
                "rationale": "stronger research stack, higher dependency/runtime cost for first local self-use spike",
            },
        ],
        "runtime": {
            "python": sys.version,
            "platform": platform.platform(),
            "opencv_version": cv2.__version__,
        },
        "frame": {
            "path": str(frame),
            "boundary": "deterministic local smoke frame; not a real form-quality benchmark",
        },
        "adapter_result": adapter_result,
        "contract_mapping": {
            "pose_evidence_ref": f"artifact:{out}",
            "raw_frame_ref": f"artifact:{frame}",
            "missing_pose_policy": "return camera/adapter failure receipt; do not judge posture and do not synthesize keypoints",
        },
        "safety": {
            "raw_cloud_upload": False,
            "medical_or_injury_claim": False,
            "coaching_quality_claim": False,
            "no_stub_fallback": True,
        },
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if adapter_result["status"] in {"pose_detected", "no_pose_detected"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
