# Mecha voice generation session notes

Applicability: generated speech for Hermes boot/readiness sounds, cockpit/LOCCENT/mecha-status announcements, tactical warning sounds, and comparison against game/film mecha references.

Anti-conditions: do not treat this as permission to clone copyrighted game/film voices. Use abstraction and licensed/self-owned reference audio by default. Direct game/film reference cloning requires an explicit local-experiment boundary and a user-provided or otherwise lawful sample.

## User-corrected direction

For Chinese mecha boot voice, avoid mixed Chinese/English target text unless intentionally making an English variant. In MiMo/Chinese TTS, embedded English technical terms can pull the whole delivery toward an English intonation and reduce natural Chinese cadence. Convert architecture terms into concise Chinese spoken labels for the target script, while preserving the underlying meaning in prompts/docs.

Preferred default style for this user:

- LOCCENT / mission-control style over slow cinematic Jaeger AI.
- Mature female control-room report voice.
- Short, professional, restrained, tactical cadence.
- Use pauses and firm sentence endings to create restrained "pre-launch heat"; do not shout or become anime/exaggerated.
- Avoid one-word-per-line status reading; use short fluent Chinese sentences with deliberate pauses.

Example preferred script shape:

```text
（严肃，干练，坚定）赫尔墨斯启动自检开始。
核心运行时上线，记忆矩阵同步完成。
（停顿）
通信网关在线，指挥频道稳定。
推理核心正常，工具总线待命。
（短暂停顿，语气上扬）
定时调度器已装填，任务池进入巡航。
风险扫描完成，关键链路全绿。
（停顿，坚定）
赫尔墨斯已进入作战待命。
指挥官，请下达任务。
```

## MiMo paths that worked

MiMo Token Plan exposed speech models through the OpenAI-compatible `/models` endpoint:

- `mimo-v2.5-tts`
- `mimo-v2.5-tts-voicedesign`
- `mimo-v2.5-tts-voiceclone`
- `mimo-v2.5-asr`

Observed practical defaults:

- For controllable Chinese mecha speech, start with `mimo-v2.5-tts-voicedesign`.
- For a preset female voice with usable pauses, `mimo-v2.5-tts` voice `冰糖` is a good comparison candidate.
- For direct voiceclone demos, `mimo-v2.5-tts-voiceclone` accepts `data:audio/wav;base64,...` or mp3/wav reference audio under the documented size limit.

Keep style prompt in `messages[0]` as `role: user`, and target spoken script in `messages[1]` as `role: assistant`.

## Game/mecha reference directions

Use these as abstract comparison axes, not direct clone prompts:

1. LOCCENT + MechWarrior/BattleTech Betty
   - Default OK candidate.
   - Control-room female report plus military cockpit warning computer cadence.
   - Short, clear, calm, professional.

2. Z.O.E. / ADA Clean AI
   - Clean cockpit AI candidate.
   - More internal machine intelligence, less military control room.
   - Good for OK / standby.

3. Titanfall BT Unit Ready
   - Reliable unit/partner AI.
   - Better for assistant personality or task readiness than control-room boot.

4. Armored Core Warning
   - WARN/FAIL only.
   - Hard, short, pressure-heavy combat HUD warning.

## Loudness normalization

Generated candidates varied in perceived volume. Before comparing, normalize to a fixed loudness target so selection is not biased by louder files.

Recommended ffmpeg target:

```bash
ffmpeg -y -i input.m4a \
  -af "loudnorm=I=-16:TP=-1.5:LRA=11" \
  -ar 24000 -ac 1 -c:a aac output_norm-16lufs_24k.m4a
```

Use normalized outputs for A/B decisions, then preserve the source/raw files separately.

## Post-processing presets

Control room: light processing, preserve naturalness.

```text
highpass=f=80,lowpass=f=7200,acompressor=threshold=-17dB:ratio=1.8:attack=18:release=180,volume=1.22
```

LOCCENT cockpit: slightly more cockpit/metallic but still professional.

```text
highpass=f=95,lowpass=f=6200,acompressor=threshold=-18dB:ratio=2.2:attack=14:release=155,volume=1.30,aecho=0.30:0.16:22:0.045
```

Combat HUD / warning: only for warning/failure sounds.

```text
highpass=f=180,lowpass=f=3900,acompressor=threshold=-20dB:ratio=3.6:attack=8:release=110,volume=1.48,aecho=0.20:0.10:14:0.035
```

## Reference-audio search and cloning boundary

Prefer licensed/self-owned reference audio over game/film extraction. Good places to search:

- Freesound search: `robot voice warning system`, then filter CC0 / Attribution and verify each sound's license page.
- YouTube/game examples are useful for listening and direction setting, but not default clone sources.

If the user explicitly wants game-original clone comparison:

1. Ask for/confirm the exact URL and 10-30 second segment.
2. State local personal experiment boundary; no public release/commercial use/impersonation.
3. Extract the cleanest possible single-speaker/system voice segment.
4. Run voiceclone plus the same control-room/cockpit/combat-HUD post-processing.
5. Report reference path, target script, output paths, and that the source was user-authorized for local comparison.
