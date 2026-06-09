---
name: visual-conversation-core
description: Use when designing or implementing camera/glasses/phone video assistants that converse about live visual context, including object Q&A, photo coaching, fitness posture, sports technique, assembly, repair, or AR overlay guidance.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags:
    - video-ai
    - multimodal
    - ar
    - safety
    - interaction-design
    related_skills:
    - test-driven-development
    - external-control-brain
    - assembly-assistance-workflow
    - mobile-frontend-delivery
---

# Visual Conversation Core

## Overview

Use this workflow to turn a vertical camera assistant into a reusable visual conversation runtime. The core pattern is: live visual context enters as frames or short clips, domain modes interpret it, and a normalized interaction contract decides what to say, when to interrupt, what camera move to request, what overlay to draw, and what evidence to record.

Treat VLMs as perception/explanation components, not as the process kernel. The kernel should be explicit: events, state machines, evidence, safety gates, mode policy, audit logs, and user-facing interaction contracts.

## When to Use

- Building an assistant that sees through a phone, webcam, smart glasses, or AR device.
- Adding modes such as object Q&A, photo coach, fitness posture, sports technique, assembly, repair, shopping, or travel guide.
- Converting a single-purpose visual assistant into a multi-mode platform.
- Designing AR skeleton/object overlays, camera coaching, or short spoken guidance.
- Evaluating open-source support for pose estimation, VLMs, segmentation, WebRTC, aesthetics scoring, or document/manual ingestion.

Don't use for:
- Static image generation or pure graphic design with no live visual context.
- Pure backend workflow automation with no camera/audio/visual grounding.
- Medical diagnosis or injury treatment; keep fitness/sports advice as coaching with strict safety boundaries.

## Architecture Thesis

1. **Context-aware over prompt-only.** Use device, camera pose, visible entities, user goal, mode, risk, and history as explicit state.
2. **Situated action over fixed script.** The assistant should adapt to what is actually visible, not blindly execute a plan.
3. **Common ground over one-shot answers.** If the view is ambiguous, ask for a camera move or user confirmation before claiming certainty.
4. **Short-loop feedback over long analysis.** During action, speak in short commands; after action, summarize and explain.
5. **Safety gates over silent autonomy.** Physical, health, electrical, mechanical, or high-risk contexts require stop/confirm/audit behavior.
6. **Domain packs over monolith.** Each mode owns rules, risk policy, scoring dimensions, and success criteria while sharing core media/state/overlay contracts.

## Core Components

- **Mode Router:** maps user intent and available visual context to `object_qa`, `photo_coach`, `fitness_posture`, `sports_technique`, `assembly`, or another domain mode.
- **Dialogue State:** tracks current mode, user goal, last question, visible entities, unresolved ambiguity, and interrupt state.
- **Frame/Clip Sampler:** gates camera data by cadence, motion/change, backpressure, and duplicate suppression.
- **Camera Coach:** asks for better angle, distance, lighting, full-body view, or stable fixed camera when evidence is insufficient.
- **Perception Adapters:** explicit model boundaries for VLM, pose, segmentation, detection, OCR, depth, or document/manual parsing. No silent fallback from real model to stub.
- **Evidence Ledger:** records claims with source, confidence, frame/clip refs, and timestamps.
- **Safety Gate:** blocks or interrupts high-risk guidance; never diagnoses medical conditions or directs unsafe physical acts.
- **Overlay Protocol:** returns skeletons, bounding boxes, highlights, arrows, score badges, and warnings separately from spoken text.
- **Interaction Contract:** normalized output that clients can render consistently.

## Normalized Interaction Contract

Recommended fields:

```json
{
  "mode": "fitness_posture",
  "intent": "inspect_form",
  "target": "frame_analysis",
  "speak_text": "膝盖跟着脚尖方向走。",
  "subtitle": "膝盖跟着脚尖方向走。",
  "camera_instruction": null,
  "confidence": 0.82,
  "risk_level": "medium",
  "should_interrupt": false,
  "requires_confirmation": false,
  "overlay": [
    {"type": "joint_highlight", "target": "right_knee"}
  ],
  "evidence_refs": ["frame:f1"],
  "next_action": "continue"
}
```

## Domain Mode Policies

### Object Q&A

- Prioritize identifying objects, controls, labels, and affordances.
- If uncertain, ask the user to move closer, improve lighting, or show another angle.
- Use grounding/segmentation for "which one" references.

### Photo Coach

- Evaluate subject, composition, light, background clutter, horizon, and framing.
- Give one next physical move: step left, lower camera, move closer, wait for light, remove clutter.
- Aesthetic scores are weak signals; the useful output is the next shot direction.

### Fitness Posture

- Prefer fixed camera with full body and relevant joints visible.
- Start with low-risk actions: squat, push-up, plank, lunge.
- Use pose keypoints and rep/phase segmentation before giving form feedback.
- Stop on pain, numbness, dizziness, heavy load with poor form, or missing critical joints.
- Do not diagnose injuries or prescribe treatment.

### Sports Technique

- Analyze short action events: stroke, swing, shot, jump, step, rep.
- Score timing, stance, balance, follow-through, and visual proxy for kinetic-chain sequencing.
- Avoid claiming exact force, muscle activation, or joint load from ordinary video.
- Convert analysis into one drill or one cue for the next attempt.

### Assembly / Repair

- Ground advice in manual steps, visible evidence, and safety constraints.
- If the part/tool/step is not visible, request a better view instead of guessing.
- Electrical, hot, sharp, high-place, or machine-actuation steps need stronger safety gates.

## Open-Source Support Matrix

- Realtime media: WebRTC, LiveKit, Pipecat, aiortc.
- VLM / visual Q&A: Qwen-VL, InternVL, MiniCPM-V, LLaVA-family, VILA, Video-LLaVA.
- Pose: MediaPipe, MMPose/RTMPose, OpenPose, YOLO pose.
- Action recognition: MMAction2, ST-GCN-style skeleton recognition, OpenCap for biomechanics reference, DeepLabCut for custom keypoints.
- Grounding/segmentation/tracking: GroundingDINO, SAM2, Grounded-SAM-2, Roboflow supervision.
- Photo scoring: OpenCV technical metrics, OpenCLIP/aesthetic predictors, ImageReward.
- Manual/document ingestion: Docling, Unstructured, MinerU-like PDF-to-structured pipelines.

## Implementation Sequence

1. Define or extend the interaction contract before adding model-specific code.
2. Add router tests for mode and intent decisions.
3. Keep existing vertical endpoints as compatibility wrappers while adding a shared `/interactions` endpoint.
4. Add stub/domain policies first, then swap perception adapters behind explicit capability metadata.
5. Add overlay slots even before rendering is fully implemented.
6. Add one real pilot per mode before broadening: one object scene, one photo scene, one low-risk fitness move, one sports clip, one assembly step.
7. For `auto` mode, keep first-pass mobile/client probes neutral (for example `auto_scene_classification`, `camera_quality`, `visible_subjects`). Do not include mode-specific hints like `full_body_visible` or `pose_keypoints_visible` unless the user selected that mode or a perception adapter actually detected them; otherwise the router will bias every auto session into a physical/fitness mode.
8. Require a user-visible safety acknowledgment before physical-mode frame analysis or coaching runs, while keeping an explicit override path and audit record instead of silently proceeding.
9. Promote repeated pilot rules into domain packs, not global memory.

## Common Pitfalls

1. **Treating VLM output as authoritative process state.** Always convert claims into evidence with source and confidence.
2. **Single-frame posture judgment.** Fitness and sports usually require short clips, action phases, and visible critical joints.
3. **Overpromising force or kinetic-chain measurement.** Ordinary video provides visual proxy metrics, not direct force measurement.
4. **Talking too much during action.** Use short cues during motion and longer summaries after the set/attempt.
5. **Skipping camera coaching.** If the view is bad, the correct behavior is to ask for a better angle, not to guess.
6. **Mixing domain rules globally.** Photo aesthetics, assembly correctness, and fitness safety need separate mode policies.
7. **Silent model fallback.** If a real adapter is requested and unavailable, fail explicitly.

## Verification Checklist

- [ ] Router has tests for auto mode, explicit modes, missing inputs, and unknown modes.
- [ ] Interaction contract is stable across modes and clients.
- [ ] Existing vertical endpoints remain backward compatible.
- [ ] Camera-coach behavior is tested for insufficient evidence.
- [ ] Safety-gate behavior is tested for high-risk physical/health contexts.
- [ ] Perception adapters expose explicit capability metadata and no silent fallback.
- [ ] At least one real low-risk pilot validates each new domain mode before broadening.
