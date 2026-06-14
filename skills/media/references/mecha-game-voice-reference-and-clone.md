# Mecha game voice references and voiceclone boundary

Use when a sci-fi/mecha TTS task needs game-side comparison references beyond Pacific Rim / cockpit film style. This is for abstract sound direction unless the user provides lawful reference audio and explicitly asks for local voiceclone comparison.

## Abstract game voice directions

- **Armored Core / combat HUD**: short, hard, cold, high-pressure warning. Use for WARN/FAIL only; not a default OK boot voice.
- **Titanfall / reliable unit AI**: low, stable, protective machine partner. Use for personal-assistant identity or task-ready confirmations.
- **MechWarrior / BattleTech Betty**: military cockpit warning computer; clear female warning voice, terse status categories. Use for resource pressure, gateway failures, model failures, and other operational alerts.
- **Zone of the Enders / ADA clean AI**: clean female sci-fi onboard AI; professional, not too cold. Good default OK/readiness candidate.
- **Front Mission tactical brief**: military briefing / command tone; useful for taskpool, mission, dispatch reports.
- **DAEMON X MACHINA**: brighter and more anime/launch-energy; reserve for success/cel­ebratory variants, not serious fault reports.

## User-preferred current default

For Hermes boot voice, the user converged toward:

- mature female LOCCENT/control-room reporting timbre;
- short professional Mandarin script;
- pauses to add restrained energy;
- light `control_room` post-processing rather than heavy radio/HUD crush;
- no Chinese-English mixed script for Mandarin TTS because it creates English intonation.

## Recommended A/B set

Generate these four candidates before pulling local models:

1. `loccent_betty_ok` — LOCCENT control-room timbre + MechWarrior/BattleTech Betty short status cadence. Default OK candidate.
2. `ada_clean_ok` — clean onboard AI, more internal/cockpit and less control-center.
3. `bt_unit_ready` — reliable unit/partner AI, good for task-ready or assistant-persona lines.
4. `ac_warning_fail` — Armored-Core-like combat HUD alert; WARN/FAIL only.

Keep OK, WARN, and FAIL voice packs separate. A default OK boot voice should not sound like a failure siren.

## Voiceclone boundary

Do not clone real game/film audio by default. Direct voiceclone requires one of:

- user-provided authorized reference audio;
- user-created reference audio;
- a clearly licensed reusable sample;
- explicit local-only personal experiment authorization with no public/commercial use.

Avoid prompts such as “imitate <specific actor/character>”. Prefer “military cockpit warning computer”, “clean onboard AI”, “reliable unit AI”, etc.

## MiMo voiceclone pattern

MiMo `mimo-v2.5-tts-voiceclone` accepts mp3/wav reference audio (docs mention max 10 MB before base64). Use:

- `messages.user`: style guard such as “保持参考音频的战斗系统警告质感，但目标文本清晰可懂；不要喊叫。”
- `messages.assistant`: target script.
- `audio.format`: `wav` for raw output.
- `audio.voice`: `data:audio/wav;base64,...` or `data:audio/mpeg;base64,...`.

Then generate at least:

- raw clone;
- `control_room` post-process (light compression/EQ, preserve naturalness);
- `combat_hud` or `cockpit` post-process depending on target state.

## Post-processing naming

- `control_room`: light highpass/lowpass + gentle compressor + small gain; best for default boot.
- `cockpit_ai`: mild band-limit + short echo; use for internal AI feel.
- `unit_comms`: lower, stable, slight room; use for partner/unit confirmations.
- `combat_hud`: narrow band, stronger compression, short echo; WARN/FAIL only.
