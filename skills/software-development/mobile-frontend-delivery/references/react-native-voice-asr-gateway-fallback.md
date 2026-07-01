# React Native voice ASR via Gateway + fallback

Use when a React Native/mobile avatar needs speech recognition, existing desktop/server transcription code, subscription ASR, iOS/native speech, optional local-model fallback, or post-ASR fluency repair.

## Core product model

- Subscription/server ASR is the primary accuracy path.
- iOS/native speech is a fast path and fallback/readback source.
- Embedded local ASR/model is fallback/draft only, not the product positioning.
- The user-facing UX should not expose provider names, online/local/offline jargon, Gateway, or model internals.
- Mobile app must never embed provider API keys; Gateway/server owns provider credentials.

## Migration pattern from desktop/server transcription

Before inventing a mobile ASR stack, inspect existing desktop/server transcription code for:

- provider selection and fallback order (for example Groq Whisper first, OpenAI fallback);
- maximum upload size;
- allowed audio MIME types;
- timeout;
- silence filters such as Whisper returning only `...`;
- response normalization (`text`, `segments`, `language`, `duration`, `provider`).

Migrate these as contracts into the mobile Gateway path. Do not copy secrets into RN.

## Recommended mobile pipeline

1. Native iOS/Android speech module starts listening after explicit mic/speech permission.
2. Same native audio tap can drive visual metering and write a temporary audio file.
3. On stop, native returns:
   - transcript/latest partial from OS speech;
   - duration;
   - optional audio asset `{ uri, path, name, type, byteLength }`.
4. RN tries Gateway ASR first if an audio asset exists.
5. Gateway endpoint validates device id, multipart file, MIME, and size before provider call.
6. Gateway calls provider using server-side env only.
7. RN falls back to OS transcript/latest partial if Gateway fails.
8. RN runs deterministic fluency compensation.
9. Existing risk-confirmation and ledger flow consumes the final transcript.

## Gateway endpoint contract

Typical endpoint:

```text
POST /api/mobile/speech/transcribe
x-hermes-device-id: <device id>
Content-Type: multipart/form-data
file: audio
language: zh-CN
```

Guardrails:

- require device id;
- require multipart/form-data;
- require `file` field;
- allow only audio MIME types copied from desktop/server transcription stack;
- enforce 25MB-style upload max unless product chooses otherwise;
- filter dot-only transcript (`...`) to empty string;
- return `{ text, provider, language, durationMs }`;
- return a structured unavailable error when provider credentials are not configured.

Provider adapter should be server-side only, e.g. env-driven Groq/OpenAI-compatible `/audio/transcriptions` call:

- `HERMES_SPEECH_PROVIDER=groq|openai`
- `GROQ_API_KEY` / `OPENAI_API_KEY`
- optional base URL/model/timeout env.

## Sentence fluency compensation

ASR output often lacks punctuation and has run-on command phrasing. Add deterministic, local compensation before intent routing, but do not use an unconstrained LLM rewrite for risky commands.

For Chinese, safe deterministic repairs include:

- trim whitespace;
- normalize wake word (`hermes` -> `Hermes`);
- add punctuation after wake word;
- convert connectors (`然后`, `再`, `并且`, `但是`) into comma-separated clauses;
- ensure sentence-final punctuation;
- treat dot-only transcript as silence.

Critical: prove risk/action keywords are preserved. If raw text contains `发布`, `发送`, `删除`, `提交`, `部署`, `发给`, the compensated text must still contain them so confirmation gates still trigger.

## Tests to add

RN tests:

- path selection: Gateway subscription ASR > OS speech > local fallback;
- invalid audio rejected before upload;
- Gateway request body is FormData;
- mobile request contains device id but no Authorization/Bearer/API-key provider credential;
- dot-only output becomes empty;
- fluency compensation preserves risk keywords and still triggers confirmation.

Gateway tests:

- valid mobile audio upload reaches injected server-side transcriber;
- unsupported MIME type is rejected before transcriber call;
- missing device id is rejected;
- provider-unconfigured path returns structured unavailable response.

Native/iOS verification:

- Release build compiles after AVAudioFile changes;
- temporary `.m4a` settings can create a non-empty file;
- simulator screenshot has no redbox/blank WebView;
- true mic/ASR proof is a physical-device boundary.

## Simulator/Gateway acceptance recipe

For simulator acceptance, verify layers separately and fail closed rather than inventing transcripts:

1. Start Gateway on the exact base URL compiled into or configured for the app, commonly `PORT=8797 HOST=127.0.0.1 npm run dev`.
2. Use `curl --noproxy '*' http://127.0.0.1:<port>/health`; local proxy settings can make Python/urllib or ordinary curl report misleading localhost failures.
3. Generate a deterministic fixture with macOS `say`, for example `say -o /tmp/asr-fixture.m4a --data-format aac "Hermes，帮我整理录音，然后发给团队。"`.
4. POST the fixture to the Gateway multipart endpoint with `x-hermes-device-id` and verify either a real provider transcript or a structured `TRANSCRIPTION_UNAVAILABLE` when server credentials are absent.
5. Build/install/launch the Release simulator app against the same Gateway URL and capture a screenshot; UI proof should show no redbox, blank WebView, or unexpected no-speech/error toast.
6. If simulator privacy grant fails with `Operation not permitted`, terminate the app, grant microphone permission, relaunch, and recapture. Treat physical microphone/audio-routing behavior as a real-device boundary.

## Server-side credential injection for acceptance

When the user authorizes subscription-ASR injection, inject only into the Gateway server process, never into RN/mobile code:

1. Prefer an explicit shell/private-env value (`GROQ_API_KEY`, `OPENAI_API_KEY`, or the chosen provider key) sourced outside the repo.
2. If reusing Hermes credentials, accept only direct provider API-key shapes appropriate for the ASR endpoint (for example Groq `gsk_...` or OpenAI `sk-...`). Do not treat browser/OAuth subscriptions, ChatGPT/Codex OAuth, or provider-specific session tokens as `/audio/transcriptions` API keys.
3. Use a temporary launcher or process env to pass the key to Gateway; do not print the key, write it into project files, include it in reports, or embed it in the app bundle.
4. After injection, prove `/health`, then the fixture upload. If the endpoint still returns `TRANSCRIPTION_UNAVAILABLE`, report the missing direct server-side ASR API authority/config boundary and keep the mobile fallback path as the expected behavior.
5. Keep the acceptance evidence at the contract level: HTTP status, structured error/success shape, screenshot path, and whether a transcript was returned. Redact or omit provider raw error bodies if they may echo credentials or account details.

## Pitfalls

- Do not call provider APIs directly from RN; reverse-engineering the app exposes the key.
- Do not let local embedded ASR become the default product story; keep it fallback/draft.
- Do not skip sentence compensation just because ASR returned text; raw ASR text can be awkward and unsafe to route directly.
- Do not let fluency compensation delete action words before risk classification.
- Do not claim provider ASR is verified unless Gateway was configured with server-side credentials and a real audio fixture/device was exercised.
- Do not downgrade `TRANSCRIPTION_UNAVAILABLE` to success. It is the correct fail-closed result when Gateway credentials are not configured; report the missing authority/config boundary and prove fallback/UI behavior instead.
