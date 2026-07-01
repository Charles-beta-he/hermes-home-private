# Mobile Hybrid Avatar: Unified UX + Voice Fast Lane

## Trigger

Use this reference when designing or implementing a mobile AI companion/control-room shell where the implementation has multiple runtime lanes (server/online, device/cache fallback, queued readback, voice), but the user should experience one coherent assistant.

## Core product lesson

Runtime architecture is not the UX. If the system internally distinguishes server authority, device cache, local fallback, readback queues, or TTS providers, do not expose those as user-facing modes unless the user is in diagnostics.

The main UX should present one avatar with:

- identity / presence;
- current readiness;
- next actions;
- short receipts;
- details on demand.

Preferred vocabulary for the main flow:

- 分身
- 上下文
- 任务
- 回读
- 确认
- 安全执行
- 语音频道

Avoid in the main flow:

- online / local / offline mode choices;
- Hybrid / Local labels;
- 本地模型 / 小模型;
- 离线兜底;
- long architecture explanations;
- raw URLs, device IDs, dry-run internals.

Technical routing can remain in contracts, diagnostics, and logs.

## Interaction hierarchy

1. Main interaction layer:
   - assistant/avatar presence;
   - concise state card;
   - actionable task/readback cards;
   - text input;
   - voice entry;
   - toast receipts.

2. Secondary details page/sheet:
   - product explanation;
   - permissions/boundaries;
   - diagnostics;
   - gateway/device/runtime details.

3. Toast/voice receipt:
   - use for short transient feedback like "已收到" / "语音频道待命" / "需要确认时会回读";
   - do not keep persistent explanatory banners in the main interaction layer.

## Behance/mobile-AI product pattern

When adapting public design references (Behance, Dribbble, etc.), do not only copy visual surfaces. Extract the product model:

- AI assistant apps often start with presence (orb/avatar/character), not configuration.
- Productivity assistant apps use cards for mission state and next actions, not documentation.
- Personal assistant apps use minimal welcome/prompt surfaces and defer explanation.
- Dark mobile AI shells often combine a central assistant stage, modular state cards, and a docked composer.

Do not copy proprietary assets or exact artwork. Reuse structure, spacing logic, hierarchy, and interaction contracts.

## Voice fast lane

If a related voice/TTS project exists, treat voice as the fast lane of the same avatar, not a separate product or runtime mode.

Main-screen voice affordance:

- label: `语音` or `语音频道`;
- receipt: short toast or spoken confirmation;
- no provider/model details;
- same task/readback queue as typed input.

Recommended voice state machine:

```text
idle → listening → transcribing → queued_readback → done/error
```

Land the state machine as a tested contract before wiring microphone or playback. Useful contract fields:

```json
{
  "inputMode": "voice",
  "taskIntent": "status_readback",
  "userUtterance": "查一下最新进度",
  "assistantReplyStyle": "loccent_c_short_cn",
  "screenReceipt": "已收到；需要确认时会自动回读。",
  "spokenReceipt": "收到，正在回读。",
  "requiresConfirmation": false,
  "safetyBoundary": "none",
  "evidenceRefs": []
}
```

Voice-specific behavior:

- use short professional Chinese;
- prefer one actionable cue during motion/travel;
- keep external/high-risk actions behind confirmation (`safetyBoundary: confirm_before_external_side_effect`);
- record `input_mode: voice` in the interaction ledger;
- spoken receipt and screen receipt should describe the same task state;
- generate a local TTS smoke artifact for canonical short receipts when a TTS provider is already configured, but do not auto-play or externally send it without explicit authority.

TDD pattern:

1. RED: add tests for `idle → listening → transcribing → queued_readback`, receipt fields, and confirmation boundary for external/risky intents.
2. GREEN: implement a pure reducer/contract module independent of native microphone APIs.
3. Integrate UI button to the reducer only after the contract is green.
4. Later microphone permission, speech recognition, and in-app TTS playback are separate gated slices.

## Verification checklist

- Main screen does not expose runtime mode choices.
- Main screen has no long doctrine/explanation blocks.
- Diagnostics are behind a details affordance.
- Voice entry is present but does not reveal TTS provider/model internals.
- Screenshots confirm no truncation/overlap in the real simulator/device viewport.
- Tests cover at least render, task queue/readback, and voice-button receipt/state where implemented.
