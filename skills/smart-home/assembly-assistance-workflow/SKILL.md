---
name: assembly-assistance-workflow
description: "Use when building or operating a phone/glasses video-driven assembly assistant: manual task graph, vision-node perception, evidence ledger, multi-brain manufacturing/electrical/inventory/safety orchestration, and mobile feedback."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [assembly, manufacturing, vision, webrtc, mobile, safety, multi-brain]
    related_skills: [manufacturing-brain, electrical-brain, external-control-brain, mlops, test-driven-development]
---

# Assembly Assistance Workflow

## Overview

Use when building or operating a phone/glasses video-driven assembly assistant: manual task graph, vision-node perception, evidence ledger, multi-brain manufacturing/electrical/inventory/safety orchestration, and mobile feedback. It is organized as a gated workflow: advance through explicit stages, preserve evidence at each boundary, and leave neighboring domains to their own skills.

## When to use

Use this skill when the user asks for:
- glasses/phone camera stream analysis for assembly guidance;
- manual-driven step monitoring and correction;
- detecting visible tools/materials plus known inventory;
- recommending safer/better assembly alternatives;
- bridging mobile Web/PWA/WebRTC capture to a Mac controller and GPU/vision node.

## Core architecture

Model the system as a workflow, not a single model or single "brain":

1. Capture: phone/glasses camera, audio, manual upload, user confirmations.
2. Perception: vision node, object grounding, OCR, frame quality, optional LocateAnything/Supervision.
3. Grounding: bind visible objects to manual BOM/current step/inventory.
4. Task Graph: compile manuals into steps with required parts/tools/visual checks/common mistakes.
5. State Estimation: current step, evidence ledger, dissent ledger, uncertainty, completion confidence.
6. Decision/Orchestration: Procedure, Manufacturing, Electrical, Inventory, Vision, Safety, External-Control verdicts.
7. Interaction: short mobile feedback, overlays, voice, confirmation prompts.

## Default implementation path

1. Start with phone PWA + Mac controller + node vision service. Do not start with full glasses integration unless requested.
2. Avoid feeding full 30fps video to a model. Use frame sampling, backpressure, duplicate suppression, and quality checks.
3. Keep P0 advisory/read-only. Store no full video by default; store only key frame refs, evidence, annotations, and step state.
4. Implement TDD for backend state and safety surfaces before production code.
5. Build these backend contracts first:
   - ManualTaskGraph
   - AssemblySession with evidence/dissent ledgers
   - SafetyGate
   - controller health/session/guidance/evidence/frame-analysis endpoints
   - vision-node health/analyze-frame stub
6. Add mobile camera capture and WebSocket feedback; use HTTPS/Tailscale/dev cert for real phone camera permissions.
7. Only then connect real WebRTC/aiortc or native mobile media pipelines.

## Safety boundaries

- High-risk or physical-world mutating actions must be blocked unless External-Control provides an action packet with fresh telemetry, confirmation token, idempotency key, and audit context.
- Electrical/thermal/kinetic/chemical/load-bearing uncertainty defaults to stop-and-confirm, not proceed.
- If visual confidence is low, ask for a closer/brighter/alternate angle instead of guessing.
- Replacement materials/tools require evidence from manual, visible state, inventory, and domain-brain risk review.
- Never log tokens, API keys, cookies, raw sensitive URLs, or credentials; redact as `[REDACTED]`.

## Node selection

- NVIDIA/CUDA node: best for large vision models such as LocateAnything-3B if CUDA is required.
- Apple Silicon node: treat as Metal/MPS/MLX/CoreML candidate; verify model support before promising large-model latency.
- If node connectivity is intermittent, record the node profile, verified commands, last passing test, and the exact network failure.

## Verification checklist

- [ ] `make verify` or equivalent backend tests + mobile TypeScript build pass.
- [ ] Controller can create a session from a sample manual.
- [ ] Vision-node `/health` responds.
- [ ] Controller frame-analysis endpoint calls vision-node and records Evidence Ledger entries.
- [ ] SafetyGate blocks physical/mutating actions without External-Control packet.
- [ ] Mobile camera can start/stop and stops tracks cleanly.
- [ ] Real phone testing has HTTPS/Tailscale/dev-cert plan.
- [ ] Real manual and first low-risk assembly scenario are identified before claiming production readiness.

## Common pitfalls

1. Treating the model as the architecture. The model is only Perception; decisions require task graph, evidence, safety, and domain verdicts.
2. Sending every frame to the model. This causes cost/latency collapse; sample frames instead.
3. Starting with dangerous electrical/mechanical tasks. Begin with low-risk desktop assembly.
4. Silent degradation when vision fails. Say the node/model is unavailable or ask for a better view.
5. Assuming Apple Silicon equals CUDA GPU. Verify MPS/MLX/CoreML support separately.
6. Letting controller imports depend on current working directory. Add `pytest.ini` / package config so remote tests import project modules consistently.
