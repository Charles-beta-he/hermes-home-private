---
name: hermes-voice-console-integration
description: Use when integrating or troubleshooting Hermes voice conversation, custom TTS providers, desktop notification sounds, or console audio UX. Covers class-level workflow for connecting a user-approved voice persona to Hermes Desktop/Dashboard without hardcoding one-session artifacts.
---

# Hermes voice console integration

Use this skill when the user asks to connect a Hermes voice identity, notification sound, speech output, or voice conversation mode to the console/dashboard/desktop UI.

## Landing-zone rules

- Stable voice/persona preference -> memory/user profile, and encode the implementation approach here.
- Concrete audio file paths, provider keys, local ports, and generated sample names -> scoped reference only, never global instructions.
- Hermes bundled docs/skills remain authoritative for CLI/config details; if they are protected, do not patch them directly.
- Do not click macOS microphone/privacy prompts for the user. Stop and ask them to grant permissions manually.

## Procedure

1. Establish the voice objective compactly.
   - Desired persona and language/prosody constraints.
   - Which surfaces need audio: CLI voice mode, Dashboard `/api/audio/speak`, Desktop notifications, or system notification sounds.
   - Whether the task requires live mic input, TTS output, or both.

2. Inspect existing Hermes voice configuration before editing.
   - Check `~/.hermes/config.yaml` for `tts`, `stt`, `voice`, `desktop`, and provider sections.
   - Prefer Hermes config semantics over ad-hoc app patches where available.
   - Back up config before mutation.

3. Implement TTS as a provider boundary, not a one-off script call.
   - For custom voice personas, add a `tts.providers.<name>` command provider that reads text from `--input` and writes audio to `--output`.
   - Keep the command provider deterministic: read env/config, synthesize, post-process, normalize, and exit non-zero on hard failures.
   - Set `tts.provider` to the custom provider only after a smoke test succeeds.

4. Verify real audio output.
   - Synthesize a short Chinese smoke phrase through the exact configured provider.
   - Probe the generated file/container with an audio inspector if available.
   - Exercise the Dashboard speak endpoint when the Dashboard is part of the requested surface.
   - Do not report success from file creation alone; verify decode/playable metadata or endpoint response.

5. Wire Desktop notification sound separately from TTS.
   - Notification sounds should load from config, with a safe fallback and a cooldown to prevent repeated toast spam.
   - Avoid playing sound for error loops unless explicitly requested.
   - Use app-level audio playback for Desktop toasts; keep OS-level sound registration optional and manual.

6. Verify build/runtime in layers.
   - Type-check the touched UI code.
   - Build the Desktop app or source bundle.
   - Start Desktop/Dashboard and confirm the window/API is live.
   - If dependencies are missing, install/repair the project environment, then rerun verification; do not encode the transient failure as a durable rule.

## Pitfalls

- Mixed English inside Chinese TTS prompts can pull the whole sentence into English prosody. Prefer all-Chinese scripts or embed technical terms in Chinese syntax.
- Do not hardcode session-specific paths in reusable UI code if config can carry the path. If a fallback is necessary, document it as local/session-scoped.
- Hermes Desktop may run under Electron in macOS accessibility listings; use the actual app name reported by macOS when verifying via computer-use.
- `hermes config` may support `show/set/check` rather than `get`; inspect the current CLI instead of assuming subcommands.
- A type-check failure caused by missing frontend dependencies is setup state, not proof the code is wrong. Fix installation and rerun.

## Verification checklist

- Config backup exists before modification.
- `tts.provider` points to the intended provider.
- `voice.auto_tts` and `stt.enabled` match the requested voice conversation behavior.
- Custom TTS command produces a decodable file from a short smoke phrase.
- Dashboard `/api/audio/speak` returns success when used.
- Desktop notification code type-checks and builds.
- User is told that macOS mic permission may require manual approval.

## References

- `references/bt-unit-console-session-2026-06-13.md` — concrete implementation notes from the BT Unit Ready console/audio integration session; use only as an example, not as universal paths.
