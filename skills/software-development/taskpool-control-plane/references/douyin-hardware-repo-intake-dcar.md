# Douyin hardware-repo intake example: Dcar_OpenSource

Use this as a compact reference when a Douyin/social post points to an open-source hardware, robotics, embedded, or physical-control repository.

## Trigger pattern

- User shares a Douyin short link/copy text and asks to analyze the repo inside the video/post.
- The post itself may not contain a clickable repo URL; the repo name may appear only in an OCR-able screenshot.
- Example signal: image carousel shows GitHub repo `Dcar_OpenSource`, course poster, comments asking whether code is open-source.

## Procedure

1. Resolve and preserve the social source:
   - Resolve `v.douyin.com/...` to `iesdouyin.com/share/note/...` / canonical `douyin.com/note/...`.
   - Parse `window._ROUTER_DATA` when present; save compact item JSON with desc, author, stats, image URLs.
   - Download carousel images under `~/.hermes/docs/private/<topic-id>/` and OCR each image.

2. Map OCR repo hints to canonical artifacts:
   - Search GitHub for exact visible repo names and distinctive phrases.
   - Record `full_name`, URL, description, stars/forks, language, license, created/updated/pushed dates, default branch.
   - Read README and any project-specific docs/walkthrough notes.
   - Inspect source structure at summary level; do not clone/build/flash/run for intake.

3. Classify the repo correctly:
   - Do not force-fit physical-control repos into AI-agent categories.
   - Treat social metrics as attention evidence only, not engineering quality proof.
   - If license is missing, restrict absorption to reading, architecture analysis, and original-pattern abstraction.

4. For embedded/robotics/control repos, extract reusable architecture patterns:
   - multi-rate loops (e.g. sensor loop, decision loop, telemetry loop, hardware timer loop);
   - closed-loop control (target -> feedback -> bounded actuator output -> next observation);
   - anti-windup/deadband/reset behavior;
   - protocol ingestion (frame parsing, ACK, timeout, stream recovery);
   - teaching-pack packaging (README, course page, walkthrough doc, module map).

5. Apply physical-control safety boundaries:
   - Mark the task as design-only unless the user separately authorizes hardware work.
   - Red lines: no firmware build/flash/run; no serial/device/motor/IMU/GPIO connection; no physical actuation; no unlicensed code reuse.
   - Future hardware execution requires external-control gates: emergency stop, wheel-lift/bench test, motor direction validation, current limits, thermal/current checks, calibration, and stop conditions.

## Example: Dcar_OpenSource

Canonical repo found from OCR:
- `Steven928519/Dcar_OpenSource`
- GitHub: `https://github.com/Steven928519/Dcar_OpenSource`
- Course page: `https://differ-tech.pages.dev/df-open-class-inertial-mecanum-car-control/index.html`
- Domain: STM32F407 mecanum-wheel car, IMU, encoders, PID, USART DMA+IDLE, odometry.

Reusable Hermes interpretation:
- Map 1 kHz IMU, 100 Hz control decision, 50 Hz debug, and hardware timer speed loop to Hermes sensing/decision/execution/telemetry/proof loops.
- Map PID target/feedback/bounded-output/deadband to taskpool desired-state/observed-evidence/proof-gated actuation/reconcile behavior.
- Treat IMU yaw drift warnings as an analogy for LLM/context/vector-memory drift: candidate signals need canonical evidence anchors.

## Recommended task shape

Title pattern:
`Douyin <repo>: absorb multi-rate closed-loop control and physical-execution safety gates into Hermes Workflow/External-Control`

Must include:
- `lane=evolution`, usually `priority=P2`;
- evidence refs for Douyin source, canonical repo, course/doc pages, and local evidence note;
- `parallel_boundary` like `no-build-no-flash-no-hardware`;
- acceptance evidence for a control-pattern map and physical-control checklist;
- red lines against cloning/building/flashing/running or controlling hardware during intake.
