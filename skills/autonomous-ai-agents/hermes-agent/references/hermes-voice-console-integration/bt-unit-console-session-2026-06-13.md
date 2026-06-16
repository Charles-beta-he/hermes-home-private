# BT Unit Ready console/audio integration — 2026-06-13

Applicability: use as an example for integrating a user-approved Hermes voice persona into console TTS, Desktop notifications, and voice conversation surfaces. Do not copy the exact local paths unless working on this same profile.

## What worked

- Treat the voice as a TTS provider boundary:
  - Create a command-style provider script that accepts `--input` and `--output`.
  - The script handles provider API call, light unit-comms/cockpit post-processing, and loudness normalization.
  - Configure `tts.provider` to the custom provider after a smoke test.
- Keep Desktop notification audio separate from conversational TTS:
  - Add `desktop.notification_sound` in config.
  - Desktop notification store reads configured sound path and plays a cached data URL.
  - Add a short cooldown to prevent repeated notification spam.
  - Avoid playing sounds for error notifications by default.
- Verify in layers:
  - Direct TTS command smoke phrase -> decodable audio metadata.
  - Hermes `text_to_speech`/Dashboard speak route -> provider reported in response.
  - Frontend type-check -> Desktop build.
  - Runtime launch -> macOS shows an Electron/Hermes window.

## Session-specific local paths

These are examples from the user's default profile, not class-level requirements:

- Custom provider script: `/Users/charles/.hermes/scripts/mimo_bt_unit_tts_command.py`
- Config: `/Users/charles/.hermes/config.yaml`
- Desktop notification code: `/Users/charles/.hermes/hermes-agent/apps/desktop/src/store/notifications.ts`
- Selected notification sound: `/Users/charles/.hermes/audio_cache/hermes_notification_bt_ready_unit_ready_norm-16lufs.m4a`
- macOS sound registration copy: `/Users/charles/Library/Sounds/Hermes BT Unit Ready.aiff`

## Config shape used

```yaml
tts:
  provider: hermes_bt_unit
  providers:
    hermes_bt_unit:
      type: command
      command: /path/to/mimo_bt_unit_tts_command.py --input {input} --output {output} --format {format}
      format: m4a

voice:
  auto_tts: true

stt:
  enabled: true

desktop:
  notification_sound: /path/to/notification.m4a
```

## Verification evidence pattern

- Provider command produced AAC/m4a or OGG/Opus with finite duration and mono channel.
- Dashboard `/api/audio/speak` returned JSON like:
  - `ok: true`
  - `provider: hermes_bt_unit`
  - `mime_type: audio/ogg`
- `npm run --workspace apps/desktop type-check` passed after dependencies were installed.
- `npm run --workspace apps/desktop build` passed and produced `dist/index.html` and assets.

## Pitfalls seen

- `hermes config get` was not a valid subcommand in this environment; use `hermes config show/check/set` or parse config directly when appropriate.
- Type-check initially failed because frontend dependencies were not installed; `npm install` fixed environment state. Do not encode that failure as a permanent limitation.
- `hermes desktop --skip-build` can fail if no packaged app exists; source mode with `--source --skip-build` can launch the source build for verification.
- macOS accessibility may list Hermes Desktop as `Electron`; verify by window title rather than assuming app bundle name.

## Anti-conditions

Do not use this as a reason to:

- Hardcode BT Unit Ready paths into reusable upstream code.
- Click microphone permission dialogs for the user.
- Treat one provider's transient API behavior as a durable Hermes limitation.
- Store generated audio filenames or one-session progress in global memory.
