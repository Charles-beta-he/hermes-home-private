# Open-LLM-VTuber → Hermes absorption review

Date: 2026-06-13T19:21:11+08:00
Task: `2026-06-13-open-llm-vtuber本地语音-live2d-mcp-交互架构吸收评估`

## Evidence read-back

- Repo cloned read-only to `/Users/charles/.hermes/runs/open-llm-vtuber-20260613`.
- Repo commit: `992309c0aa19845960228f880013d4685fde93b5`.
- Frontend submodule commit: `06a659b114fff788cf0daaa86e484576db4975bf`.
- Required source surfaces read:
  - `README.md` lines 14, 40, 47-53, 63-91, 132-140.
  - `CLAUDE.md` lines 31-45, 48-65, 67-88, 109-119, 123-140.
  - `pyproject.toml` lines 1-43 and 63-68.
  - `mcp_servers.json` lines 1-12.
  - `frontend/.gitmodules` points `frontend` to `https://github.com/Open-LLM-VTuber/Open-LLM-VTuber-Web` branch `build`; checked out build artifact contained `index.html`, `assets/`, and `libs/` rather than editable source config files. Frontend runtime evidence was therefore limited to built asset read-back and Live2D/WebGL bundle strings, not source-level config.

No service was started, no dependency install was run, no model/audio/camera permission was requested.

## Architecture read-back

Open-LLM-VTuber is a FastAPI + WebSocket voice/avatar companion runtime. Its useful shape for Hermes is not “install a VTuber app”, but a set of interaction contracts:

1. **Session service context** — `ServiceContext` stores config, Live2D model, ASR, TTS, VAD, agent, translator, MCP registry/client/executor, send callback, and client uid per session.
2. **Message routing** — `WebSocketHandler` maps typed client messages such as `mic-audio-data`, `mic-audio-end`, `text-input`, `interrupt-signal`, `audio-play-start`, `fetch-configs`, and `switch-config` to handlers.
3. **Interruptible audio loop** — README highlights “voice interruption without headphones”; code exposes explicit interrupt and audio-play-start control message paths.
4. **Adapter factories** — CLAUDE.md documents factory-pattern engines for Agent, ASR, TTS, VAD, translation, and config managers.
5. **MCP registry** — `mcp_servers.json` and `src/open_llm_vtuber/mcpp/server_registry.py` show a small JSON registry for MCP command/args/env/cwd/timeout with runtime availability checks for `uvx`, `npx`, and `node`.
6. **Avatar projection** — Live2D assets and frontend bundle are projection/UI state, not canonical task or memory state.

## Hermes gap mapping

| External pattern | Hermes-compatible absorption | Boundary / reject condition |
|---|---|---|
| Per-WebSocket `ServiceContext` | Add a Hermes `voice_visual_session_context` contract that carries session id, permissions, model/provider, ASR/TTS/VAD adapter ids, tool allowlist, transcript pointer, and UI projection state. | Must not become a second taskpool/session DB. Hermes session/taskpool remain SSOT. |
| `MessageType` routing for mic/text/interrupt/config | Map to Hermes gateway/TUI event types: `voice.audio_chunk`, `voice.end`, `voice.interrupt`, `voice.playback_start`, `visual.frame_ref`, `avatar.projection_update`. | Browser/camera/mic permission is explicit opt-in; no cron/background capture. |
| ASR/TTS/VAD factories | Create adapter interfaces only: `SpeechInputAdapter`, `SpeechOutputAdapter`, `TurnBoundaryDetector`. Initial implementation should be a no-audio fake/deterministic harness. | Do not install heavy local models or download ASR/TTS weights during intake. |
| MCP server registry | Reuse Hermes MCP config governance; add read-only lint/read-back for avatar/voice MCP configs if later needed. | Do not copy Open-LLM-VTuber registry as an authority layer; avoid tilde path pitfalls already known in Hermes MCP launcher. |
| Live2D model/expression messages | Treat avatar as read-only projection subscribed to Hermes events (`thinking`, `speaking`, `tool_running`, `needs_approval`). | Avatar UI must not decide lifecycle, approvals, memory writes, or task status. |
| Chat history persistence | Link transcript artifacts to Hermes session/task evidence using existing session/task ledgers. | No parallel chat_history SSOT. |

## Minimal reversible adapter contract

Proposed next implementation slice, if authorized as a separate implementation task:

```yaml
voice_visual_session_context_v0:
  session_id: string
  surface: tui|dashboard|gateway|local_web
  permissions:
    microphone: false
    camera: false
    screen: false
  adapters:
    asr: fake_text_or_file_only
    tts: null
    vad: deterministic_end_marker
    avatar_projection: log_only
  events_in:
    - text.input
    - voice.audio_chunk_ref
    - voice.end
    - voice.interrupt
    - playback.started
  events_out:
    - transcript.delta
    - transcript.final
    - avatar.expression_hint
    - approval.required
  ssot:
    taskpool: read_only
    session_db: append_only_transcript
    tool_calls: existing Hermes tool governance
```

Verification for the first implementation task should be deterministic and local:

1. Unit test: feed text/audio-reference events into a fake voice session adapter; assert ordered Hermes event emissions.
2. Dry-run CLI: `python -m hermes_cli.voice_visual_harness --fixture tests/fixtures/voice_visual_session.json --dry-run` returns JSON without requesting mic/camera.
3. Read-back: generated transcript/projection log contains no raw camera/mic data unless explicit fixture paths are supplied.
4. Governance: proof-check/selfcheck continue PASS; no taskpool lifecycle transition is driven by avatar events.

## Absorb / reject list

Absorb now as design patterns:

- Interruptible turn-control events.
- Per-session adapter context.
- Adapter factory shape for ASR/TTS/VAD/agent, but with Hermes permission gates.
- MCP registry lint/read-back pattern, not a new MCP authority.
- Avatar/expression as operator UX projection.

Reject/defer:

- Running Open-LLM-VTuber service inside Hermes.
- Downloading local speech/vision models as part of this task.
- Microphone/camera/screen access from cron or background jobs.
- Treating Live2D frontend state, chat_history, or external MCP registry as canonical Hermes state.
- Medical/biometric inference or FacePhys coupling; that belongs to a separate safety-boundary task.

## Follow-up dependency order

1. `P2 evolution`: create a Hermes `voice_visual_session_context_v0` fixture + validator only, no runtime audio.
2. `P2 implementation`: add fake adapter harness with unit tests and dry-run JSON output.
3. `P3 UX projection`: dashboard/TUI read-only avatar event projection after the harness is proven.
4. `manual gate`: any real microphone/camera/TTS/Live2D runtime requires explicit user authorization and separate privacy red-line review.

## Closeout assessment

This tranche satisfies the source-review/gap-mapping acceptance criteria for the current task. It is not implementation proof for a Hermes voice/avatar runtime. Recommended lifecycle: move current source-review task to `review` with this artifact; do not mark `done` unless the control-plane accepts source-review closeout without additional ratification.
