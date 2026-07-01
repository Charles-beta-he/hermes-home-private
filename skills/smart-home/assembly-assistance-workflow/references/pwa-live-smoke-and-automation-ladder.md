# PWA live smoke and automation ladder

Use when assessing or improving automation for a phone/PWA assembly assistant that bridges mobile-web, controller, and vision-node.

## Automation ladder

1. Contract/unit layer — expected first green gate:
   - controller tests for session creation, evidence ledger, guidance, SafetyGate, readiness, frame analysis, visual interaction routing, audit redaction;
   - vision-node adapter tests proving stub/real-adapter boundaries and fail-closed behavior;
   - mobile-web static/contract tests proving diagnostics, safety boundary UI, camera controls, frame upload contract, and voice controls are present;
   - TypeScript build for the mobile-web app.
2. Live API smoke — should become a one-command gate before claiming integration readiness:
   - start vision-node;
   - start controller with `VISION_NODE_URL` and local proxy bypass;
   - poll `/health/ready` until ready;
   - create a sample session from a low-risk manual;
   - POST a visual interaction frame;
   - assert safety boundary, evidence count, and a fail-closed guidance result when using stub vision.
3. Browser/PWA smoke:
   - launch mobile-web via local HTTP/HTTPS server;
   - verify page title, secure-context expectations, start/stop controls, safety acknowledgement, mode selector, diagnostics, and controller origin;
   - for true camera automation, add Playwright fake media device/fake video instead of relying on manual webcam permissions.
4. Phone/installed-PWA semi-automation:
   - generate LAN HTTPS URL / QR code;
   - guide certificate trust and camera permission;
   - require a server-side check-in/readback from the device before reporting success.
5. Real model/hardware layer:
   - keep stub tests separate from real adapter smoke;
   - mediapipe / Apple Silicon / CUDA adapters must either pass their own smoke or return explicit unavailable/503; never silently fall back to stub while claiming real perception.

## Local proxy pitfall

When the controller probes a local vision-node with `httpx`, machine proxy settings can make `http://127.0.0.1:9000` fail with symptoms like `Server disconnected without sending a response` even though `curl` to the same URL works. For local live smoke commands, set both forms:

```bash
NO_PROXY=127.0.0.1,localhost no_proxy=127.0.0.1,localhost \
VISION_NODE_URL=http://127.0.0.1:9000 \
python3 -m uvicorn services.controller.app:app --host 127.0.0.1 --port 8877
```

Capture this as a smoke-runner environment default, not as a global claim that networking or browser tools are broken.

## Minimal live smoke shape

```bash
# Start in tracked background processes or a script that cleans up on exit.
python3 -m uvicorn services.vision_node.app:app --host 127.0.0.1 --port 9000
NO_PROXY=127.0.0.1,localhost no_proxy=127.0.0.1,localhost \
VISION_NODE_URL=http://127.0.0.1:9000 \
python3 -m uvicorn services.controller.app:app --host 127.0.0.1 --port 8877

curl -fsS http://127.0.0.1:8877/health/ready
# create session with manuals/examples/p0_sample.steps.json
# POST /api/sessions/{session_id}/interactions with mode=assembly, frame_id, image_ref, safety_acknowledged=true
```

Expected stub-mode result: readiness is ready, session is created at the first manual step, interaction routes to frame analysis, evidence ledger increments, and guidance asks for a better view instead of pretending to recognize parts.

## Reporting automation degree

Distinguish these levels in closeout:

- High: unit/contract/build gates.
- Medium: live API integration, if a one-command smoke exists and is run.
- Medium-low: browser DOM/PWA smoke unless it includes fake camera/media automation.
- Low/manual: real phone camera permission, certificate trust, installed PWA mode, speech synthesis/recognition, and real hardware/model adapters.
