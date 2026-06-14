# Mecha game voice comparison for Hermes boot/status audio

Applicability: use this reference when the user wants Hermes boot/status audio compared against mecha-game system voices, or asks for a more game-like mecha tone after the base sci-fi/mecha voice pipeline is working.

Anti-conditions: do not clone copyrighted game voices, actors, or exact lines. Use these as abstract direction labels for prompt design, A/B comparison, and audio post-processing choices.

## Evidence/search anchors from the session

Representative mech-game ranking/search surfaces repeatedly point to `Armored Core`, `Titanfall`, `MechWarrior`, `Front Mission`, `Zone of the Enders`, and `DAEMON X MACHINA` as useful comparison classes. YouTube search anchors for sound references included:

- `Ranking Mech Video Games (Front Mission VS Armored Core Vs MechWarrior)`
- `TOP 15 ACTION-PACKED MECHA Games like Armored Core and Titanfall...`
- `Armored Core 6 Warning Sound`
- `All BT-7274 Voicelines | Compilation`
- `Mechwarrior 5 - MW2 Betty Voice Ultimate Mod + More`
- `ANUBIS ZONE OF THE ENDERS : M∀RS ADA -Talk Log Extra-`
- `Daemon X Machina: Titanic Scion Voice Comparison`

Treat these as discovery anchors, not as source material to reproduce verbatim.

## Comparison matrix

### Armored Core / AC-style warning

Use for: WARN/FAIL states, lock-on/error style alerts, urgent fault reports.

Traits:
- short, hard, cold;
- high information density;
- warning pressure comes from cadence and beeps, not emotional acting;
- not ideal for default OK boot audio.

Prompt abstraction:
> 冷峻的战斗系统提示音，语速短促，状态词快速明确，带轻微警告压迫感，但不要喊叫。

### Titanfall / BT-style reliable unit AI

Use for: assistant persona, task acceptance, unit-ready acknowledgements.

Traits:
- low, reliable, protective, restrained;
- feels like the machine itself responding to the pilot;
- more companion-like than control-room/LOCCENT.

Prompt abstraction:
> 稳定可靠的机体 AI 声线，低沉、克制、带保护性，不夸张、不热血，用短句确认任务状态。

### MechWarrior / BattleTech “Betty”-style cockpit computer

Use for: WARN/FAIL, resources/heat/pressure alerts, gateway/model/tool failures.

Traits:
- female cockpit warning computer;
- military/aviation-industrial readability;
- calm, clear, clipped status lines;
- less cinematic, more instrument-panel useful.

Prompt abstraction:
> 军用驾驶舱告警电脑，女性声线，冷静、清晰、短句，状态级别明确；不要甜美，不要情绪表演。

### Zone of the Enders / ADA-style clean AI

Use for: OK boot, daily standby, clean system-readiness notifications.

Traits:
- clean female AI;
- precise and readable;
- more in-unit than LOCCENT, less harsh than Betty;
- professional but not emotionally flat.

Prompt abstraction:
> 冷静、清晰、干净的日式科幻机体 AI 声线，语气专业但不冰冷，短句汇报系统上线。

### Front Mission-style tactical brief

Use for: taskpool, mission, dispatch, and operational briefings rather than audio-alert UI.

Traits:
- military brief, command cadence;
- less electronic processing;
- more procedure/report than cockpit AI.

Prompt abstraction:
> 战术简报员，语气干练，像行动前下达状态确认，不做影视化电子音。

### DAEMON X MACHINA-style energetic sortie cue

Use for: celebratory OK/success variants, not serious health/failure reports.

Traits:
- younger, brighter, faster;
- more anime/sortie energy;
- can become too cute or gamey for the user's default professional Hermes identity.

Prompt abstraction:
> 年轻但克制的机甲出击提示，节奏明快，带一点热血上扬，但不要二次元夸张。

## Current preferred direction from user correction

The user selected the `LOCCENT` direction over Jaeger AI and radio-comms variants:

- shorter, more professional control-center reporting;
- Chinese body text only, because mixed Chinese/English can pull Chinese TTS into an English accent/prosody;
- use pauses and cadence to create restrained heat/出击感 rather than shouting or exaggerated acting;
- preferred voice target: the `loccent_female_director` direction, with the pause structure from the `preset_bingtang pause_tags control_room` experiment;
- for final boot audio, preserve a control-room voice first, then apply only light cockpit/control-room processing.

A good current script shape:

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

## Recommended A/B set

When asked to continue from the current state, generate only a small A/B set:

1. `loccent_betty_ok` — current LOCCENT voice + Betty-like clipped status cadence; default OK candidate.
2. `ada_clean_ok` — cleaner in-unit AI; alternate OK candidate.
3. `bt_unit_ready` — reliable companion/unit voice; assistant-persona candidate.
4. `ac_warning_fail` — short warning-only voice for WARN/FAIL.

Do not spend time on broad model search before testing these, because MiMo V2.5 TTS already covers preset voices, voice design, and style prompts in this environment.
