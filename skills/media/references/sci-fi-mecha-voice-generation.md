# Sci-fi / mecha voice generation workflow

Applicability: use this reference for media tasks where the user wants generated speech with a dramatic synthetic style such as sci-fi cockpit, mecha boot sequence, tactical comms, or operational-readiness announcements.

Anti-conditions: this is not a general TTS setup guide, not a claim that any single repository is permanently best, and not a license/commercial-use decision. Re-check repository state, models, and licenses before long-term integration.

## Core lesson

Plain system voices (`say`, generic browser/OS voices, or default cloud TTS voices) usually read the words but do not deliver the required style. Treat mecha voice as a two-stage media pipeline:

1. Generate clear speech with a language-appropriate, style-controllable TTS or reference-voice model.
2. Add the mecha/cockpit feel with audio post-processing: pitch, compression, EQ, short reverb, light distortion, radio/helmet filtering, beeps, and scan sweeps.

Do not try to solve the whole style problem by wording alone.

## Provider-first triage before pulling local models

Before downloading large local TTS models, check whether the user's existing provider entitlements already include a controllable speech model. In this environment, MiMo Token Plan exposed `mimo-v2.5-tts`, `mimo-v2.5-tts-voicedesign`, and `mimo-v2.5-tts-voiceclone` via the OpenAI-compatible `/models` endpoint, while DeepSeek exposed only chat/reasoning models and OpenAI TTS required a separate `VOICE_TOOLS_OPENAI_KEY` / `OPENAI_API_KEY`.

Preferred order for Chinese Hermes/mecha boot voice work:

1. Use MiMo V2.5 TTS if `XIAOMI_API_KEY` / `MIMO_API_KEY` is configured. It supports preset voices, text-designed voices, voice cloning, natural-language style control, labels, speed/emotion/role/dialect controls, and is a better first pass than pulling multi-GB local models.
2. If MiMo is unavailable or insufficient, use Edge Neural TTS for a fast naturalness baseline, then post-process.
3. Only then pull local candidates such as CosyVoice/Spark/Fish/GPT-SoVITS/F5-TTS, preferably on a node computer with enough disk/GPU budget.

For MiMo voice design, put the style/voice direction in the `user` message and the target script in the `assistant` message. For preset voices, known useful Chinese male voices include `白桦` (steadier) and `苏打` (more tactical/energetic). For `mimo-v2.5-tts-voicedesign`, describe the operator voice directly, for example: `三十多岁的中文男性系统 Operator 声线，低沉、磁性、克制、专业，像近未来重型机甲驾驶舱里的任务控制 AI。语速中慢，咬字清晰但自然，英文技术术语发音稳定；有战备感和压迫感，但不要像机器人逐字朗读，不要夸张表演。`

## Repository shortlist from GitHub research

Prefer Chinese/style-controllable projects first when the requested script is Chinese:

- `FunAudioLLM/CosyVoice` — strong first candidate for Chinese controllable TTS. README advertises multilingual Chinese support and instruct controls such as language, dialect, emotion, speed, and volume. Good for low, calm, mechanical broadcast prompts.
- `SparkAudio/Spark-TTS` — Chinese/English, voice cloning, controllable generation via gender, pitch, and speaking rate; Apache-2.0. Good stable fallback for boot announcements.
- `fishaudio/fish-speech` — strong expressive/prosody direction with inline/natural-language control tags and Chinese support. Check current license/model availability before long-term integration.
- `RVC-Boss/GPT-SoVITS` — good for building a fixed character voice from short reference data; less direct for prompt-only style control.
- `SWivid/F5-TTS` — good reference-audio route; style quality depends on having or making a good mecha/cockpit reference clip.
- `myshell-ai/OpenVoice` — useful as a style/voice conversion layer after another TTS generates clean speech.
- `Zyphra/Zonos` — supports Chinese plus rate/pitch/emotion controls; worth testing when local deployment budget allows.

Secondary / less suitable for a Chinese mecha first pass:
- `2noise/ChatTTS` is strong for Chinese conversational prosody but tends toward casual dialogue; AGPL-3.0 also affects integration.
- `huggingface/parler-tts`, `canopyai/Orpheus-TTS`, and `resemble-ai/chatterbox` are interesting for English/style prompts or voice cloning but not the first Chinese mecha path.

## Prompt and script pattern

Use explicit voice direction before the text, but do not rely on voice direction alone. For written planning, preserve the user's architecture semantics (`Core Runtime`, `Control Plane`, `Gateway Link`, `Taskpool Control`, `Evidence Recorder`, `Critical Path`). For synthesized Mandarin, do **not** blindly keep the English surface form: the user corrected that Chinese-English mixed scripts can pull Mandarin TTS into an English intonation. Prefer professional Chinese renderings when the target is a Chinese voice: `核心运行时`, `控制面`, `通信网关`, `指挥频道`, `推理核心`, `工具总线`, `定时调度器`, `任务池`, `证据记录器`, `关键链路`, `上线`, `待命`, `全绿`.

Avoid over-fragmented Chinese status lines when using generic TTS: many Chinese system voices become "one word at a time" if every phrase is on its own line. Prefer short fluent Chinese status sentences, then use punctuation, ellipses, or supported tags such as `（停顿）` / `（短暂停顿，语气上扬）` to create controlled energy instead of shouty/anime delivery.CCENT/control-room style in Chinese, avoid mixed Chinese/English body text: English technical terms can pull the Chinese TTS into an English accent/prosody. Translate architecture terms into concise Chinese口播 (核心运行时、通信网关、指挥频道、推理核心、工具总线、定时调度器、任务池、关键链路), and use pause tags/ellipsis plus firm sentence endings to create restrained 出击感 instead of shouting. Use English terms only when the user explicitly wants a bilingual/versioned artifact.

### Pacific Rim / Jaeger cockpit reference direction

When the user asks for “环太平洋” style, interpret the target as an abstract Jaeger cockpit / LOCCENT status-report sound, not as cloning a copyrighted actor or exact character voice. Evidence from the film reference: Gipsy Danger's A.I. is associated with Ellen McLain / GLaDOS-like cockpit A.I. texture. Translate that into voice-design constraints:

- female or androgynous cockpit A.I.; cold, precise, low-emotion, slightly synthetic;
- status-report cadence with clear English tokens: `online`, `locked`, `nominal`, `green`, `No fatal fault detected`;
- avoid cute, lively, broadcast-host, or theatrical villain delivery;
- keep the TTS natural enough to avoid character-by-character mechanical reading;
- add cockpit/radio texture in post-processing rather than asking the model to imitate a specific voice.

Useful MiMo voice-design prompt shape:

```text
女性化但不过分拟人的大型机甲 cockpit AI 声线。冷静、精密、无情绪波动，像 Jaeger 启动时的系统 A.I. 汇报。声音干净、稍低、带轻微电子质感；语速中慢，停顿短促，状态词如 online、locked、nominal、green 要清晰。不要可爱，不要播音腔，不要逐字机械蹦字，不要模仿任何具体演员或现成角色，只取“好莱坞重型机甲驾驶舱系统汇报”的抽象质感。
```

```text
以低沉、冷静、机械广播的语气朗读。语速偏慢，停顿清晰，像重型机甲启动系统提示音。不要活泼，不要日常口语化。

Hermes Activation Sequence 启动。Core Runtime 已上线，Memory Matrix 已完成同步，Evidence Recorder 进入 locked 状态，Control Plane 正在接管启动流程。

Gateway Link 已建立，Telegram Command Channel 在线，Proxy Route 稳定，Notification Bus 已进入 armed 状态。

Reasoning Core 状态 nominal，Tool Bus ready，Cron Scheduler armed，Taskpool Control 进入战备巡航。

Risk Scan 已完成，Critical Path 全线 green，No fatal fault detected。

Hermes Personal Assistant Unit 已进入 operational 状态。Commander，下一项任务，等待接入。
```

If the target is not Hermes/control-plane identity work, adapt the English terms to the user's actual domain rather than cargo-culting these labels.

For the current preferred LOCCENT/Chinese-only shape, start from a compact script like:

```text
赫尔墨斯启动自检开始。
核心运行时上线，记忆矩阵同步完成。
……
通信网关在线，指挥频道稳定。
推理核心正常，工具总线待命。
……
定时调度器已装填，任务池进入巡航。
风险扫描完成，关键链路全绿。
……
赫尔墨斯已进入作战待命。
指挥官，请下达任务。
```

MiMo `冰糖` style direction that worked well:

```text
冷静专业的中文控制中心汇报语气，带一点战前热血和坚定感。不要喊叫，不要夸张；通过停顿、重音和句尾上扬表达“启动完成、即将出击”的气势。语速中等，节奏短促，像大型机甲启动状态播报。
```

## Post-processing target

After TTS generation, create at least one processed variant:

- lower pitch slightly, not cartoonishly;
- add mild dynamic compression;
- EQ toward radio/helmet comms, but preserve intelligibility;
- add short metallic room/reverb;
- optional low-level distortion/saturation;
- optional short beep before major status lines.

Use A/B outputs: raw TTS vs processed mecha preset. Let the user pick the closest direction before investing in fine-tuning.

When falling back to macOS `say`, prefer enhanced Mandarin voices such as `Reed (中文（中国大陆）)` or `Rocko (中文（中国大陆）)` over `Tingting` for this style. Keep post-processing subtle enough to preserve prosody; excessive line breaks and heavy effects make the output sound like mechanical character-by-character reading. Note that `say` AIFF output may be 22050 Hz or 24000 Hz depending on the voice, so inspect/handle sample rate before using `asetrate` for pitch changes.

## Verification

A successful deliverable is an actual audio file path, not a model recommendation. Report:
- model/backend used;
- text prompt used;
- post-processing preset, if any;
- output path(s);
- known limitations, such as missing GPU, missing model weights, or license constraints.

For A/B comparison and short notification sounds, normalize final listening files before asking for preference. Use a fixed target such as `loudnorm=I=-16:TP=-1.5:LRA=11` and report normalized paths separately from raw outputs; otherwise the louder candidate tends to win even when its voice identity is worse. Short notification sounds should usually be around 2-5 seconds, not full boot-narration length.

When generating a desktop waveform/visual from the sound, verify it visually and use a CJK-capable font for Chinese overlay text; generic Pillow/Arial fonts can render Chinese as square boxes. Applicability: this note is for sci-fi/mecha speech artifacts with Chinese labels or captions, not a general image-generation rule. For the full notification identity + waveform procedure, see `references/mecha-notification-identity-and-waveform.md`.
