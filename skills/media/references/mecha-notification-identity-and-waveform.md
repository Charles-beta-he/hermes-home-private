# Mecha notification identity and desktop waveform

Use this reference when the user wants Hermes/system notification sounds, a fixed sonic identity, or a desktop sound-wave visual derived from generated audio. This is a notification-identity workflow, not a long boot-sequence workflow.

## Applicability

- Short Hermes notification sounds: task received, acknowledgement, completion, warning.
- Mecha/BT Unit Ready style identity: low, reliable machine-partner voice rather than LOCCENT operator or high-pressure warning HUD.
- Fixed-loudness comparisons where generated TTS volumes vary.
- Desktop/wallpaper waveform images derived from the selected notification audio.

Anti-conditions:
- Do not use this for full 20-40s boot narration unless the user explicitly asks for a boot sequence; use the sci-fi/mecha boot voice workflow instead.
- Do not auto-change macOS system sound settings. Export to `~/Library/Sounds/` and report the path unless the user explicitly asks to set it.
- Do not clone copyrighted game/film voices by default; keep game references abstract or require user-provided/authorized reference audio.

## User-preferred notification direction

Current preferred Hermes notification identity:

- Style: BT Unit Ready / reliable heavy-mech unit, like a machine partner responding to the commander.
- Voice: low, steady, protective, concise; Chinese only unless explicitly requested otherwise.
- Prosody: semantic rhythm. Slow slightly on `指挥官`; short confirmation for received/linked/stable; firm final closure for `待命` / `稳定` / `完成`.
- Avoid: shouty anime delivery, generic announcer tone, mixed Chinese-English text that pulls Mandarin into English prosody, and long boot-sequence pacing.
- Loudness: normalize user-facing comparison and notification files to `-16 LUFS`, `TP=-1.5`, `LRA=11`, typically 24kHz mono AAC for listening; AIFF is useful for macOS sound library.

Good short texts:

```text
指挥官，任务已接入。赫尔墨斯待命。
```

```text
赫尔墨斯收到。链路稳定。
```

```text
任务完成。关键链路保持稳定。
```

## Generation pattern

Use a voice-design prompt like:

```text
低沉可靠的机体 AI 声线，中性偏男性，稳定、克制、带保护性，像重型机甲本体在回应驾驶员。这是短通知音，不要拖长，不要播音腔。根据语义调整节奏：称呼“指挥官”放慢半拍；确认状态短促；最后“待命/稳定/完成”坚定收束。全程标准中文，不要英文腔。
```

Generate several short variants, then choose one primary sound yourself if the user grants that agency. Preferred default is the BT Unit Ready-style task-received sound.

## Post-processing and loudness

For a subtle unit-comms texture before loudness normalization:

```bash
ffmpeg -y -i input.wav \
  -af "highpass=f=70,lowpass=f=6200,acompressor=threshold=-18dB:ratio=2.4:attack=16:release=170,volume=1.32,aecho=0.22:0.12:24:0.04,loudnorm=I=-16:TP=-1.5:LRA=11" \
  -ar 24000 -ac 1 -c:a aac output_norm-16lufs.m4a
```

For macOS sound library export:

```bash
mkdir -p "$HOME/Library/Sounds"
ffmpeg -y -i output_norm-16lufs.m4a -ar 44100 -ac 1 "$HOME/Library/Sounds/Hermes BT Unit Ready.aiff"
```

Report the path; do not change system preferences unless explicitly asked.

## Desktop waveform image workflow

1. Convert the selected final notification audio to 16-bit mono WAV at 24kHz.
2. Read samples and downsample into per-pixel peak/RMS hybrid values.
3. Render a dark Hermes/mecha HUD wallpaper with:
   - 3840×2160 canvas;
   - dark grid background;
   - cyan glowing waveform;
   - `HERMES` and `BT UNIT READY` title;
   - status box such as `LINK: STABLE` / `MODE: STANDBY`;
   - Chinese notification text using a CJK-capable font such as `/System/Library/Fonts/Hiragino Sans GB.ttc` or `/System/Library/Fonts/STHeiti Medium.ttc`.
4. Verify visually that Chinese does not render as square boxes.
5. Copy the PNG to the user's Desktop only if useful; otherwise leave it under audio cache and report the path.

Pitfall: Pillow's default or Arial fonts may not render Chinese on macOS and can produce □□□□ boxes. Explicitly load a CJK font for Chinese overlay text.

## Verification checklist

- [ ] Notification audio is short enough for real notifications, usually 2-5 seconds.
- [ ] Final listening file is fixed-loudness normalized (`-16 LUFS`) before comparison.
- [ ] macOS AIFF export exists if the user wants a selectable system sound.
- [ ] Waveform PNG dimensions and format were verified.
- [ ] Visual inspection confirms readable title, waveform, and Chinese text.
- [ ] Paths are reported plainly; no `MEDIA:` tags in CLI mode.
