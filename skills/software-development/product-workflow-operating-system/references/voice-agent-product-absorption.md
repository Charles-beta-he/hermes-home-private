# Voice Agent Product Absorption Reference

Scope: use when a mobile/assistant product includes voice input, realtime transcription, speech-to-speech UX, PM-agent routing, or product workflow absorption from external repositories.

Applicability:
- The task involves voice assistant UX, mobile voice capture, realtime/streaming speech, or voice-to-task routing.
- The user asks to absorb product logic from open-source voice agents or product-manager agents.
- The product should behave like an assistant/workflow system, not a text chat with a microphone button.

Anti-conditions:
- Pure UI copy changes with no voice/session/product workflow behavior.
- One-off research summaries where no implementation or workflow artifact is requested.
- Credential/provider setup issues; store provider-specific setup elsewhere, not here.

## Pitfall: placeholder transcript is false acceptance

Do not accept a fake or default transcript such as "voice short command" as a successful voice turn. If the speech recognizer returns an empty transcript, fail closed with a user-visible retry state. Never append a fabricated user utterance to the conversation ledger.

Correct minimum behavior:

```text
start listening
→ stream partial transcript into the visible intent surface
→ stop listening
→ final transcript becomes candidate intent
→ empty final transcript fails closed
→ only real transcript enters the durable ledger
```

## Realtime voice product model

A mature voice assistant is not:

```text
tap mic → record → stop → append text message
```

It is closer to:

```text
presence
→ permission / availability
→ listening
→ partial transcript
→ intent candidate
→ domain interpretation
→ confirmation or execution routing
→ readback / spoken response
→ interruption / barge-in handling
```

Recommended state vocabulary:

```ts
type VoiceSessionPhase =
  | 'idle'
  | 'permission_needed'
  | 'listening'
  | 'partial_transcript'
  | 'intent_candidate'
  | 'pm_interpreting'
  | 'tool_confirming'
  | 'executing'
  | 'readback'
  | 'speaking'
  | 'interrupted'
  | 'error';
```

## Implementation checklist

- [ ] Permission prompts are explicit and not treated as execution authority.
- [ ] Partial transcript events update the visible intent surface while the user speaks.
- [ ] Empty transcript fails closed; no dummy user messages.
- [ ] Final transcript is stored in the same durable ledger as typed input, with `inputMode: 'voice'` or equivalent metadata.
- [ ] Risky/external intents require confirmation before side effects.
- [ ] Spoken playback requires explicit user authorization if the user's workflow requires it.
- [ ] Simulator screenshots do not prove real microphone input; use real-device/manual permission + spoken transcript evidence when closure depends on voice capture.
- [ ] Tests cover the wrapper/state machine and the transcript-to-ledger path.

## Open-source patterns worth absorbing

Voice assistant references:

- `fluxions-ai/vui`: WebRTC/WebSocket ASR→LLM→TTS streaming, VAD turn-taking, barge-in, OpenAI Realtime compatibility, tool-routing thought stream.
- `kirill-markin/meta-glasses-ios-openai`: iOS SwiftUI voice assistant, realtime client, conversation history/threads as first-class product objects.
- `ahmad2b/langgraph-voice-call-agent`: LiveKit + LangGraph voice transport with VAD/STT/TTS/turn detection.
- `den-vasyliev/voice-mcp-agent`: voice assistant routing into MCP tools; reinforces confirmation boundaries for external actions.
- `gruuubcioo/Neuro-Lingo`: React Native/Expo audio chunk streaming through a backend proxy; useful pattern for true realtime beyond OS speech APIs.

Product-manager agent references:

- `FoundationAgents/MetaGPT`: one-line requirement becomes user stories, competitive analysis, requirements, APIs, docs, and execution roles.
- `wwwazzz/senior-pm-prompt`: PM interview flow that generates agent-ready PRDs.
- `kakuka/icemark`: PM modes such as PRD and product analysis.
- `CPsean/ai-prd-agent`: product background/strategy/personas plus story-card/PRD layers.
- `vishalmdi/ai-native-pm-os`: PM agent registry patterns such as competitive intelligence, PRD-to-Jira, customer voice synthesis, and prototyping.

## Product workflow absorption rule

When a user says the product logic was not absorbed, do not respond with visual polish alone. Add or update the product workflow layer:

```text
voice/text intent
→ intent classifier
→ PM/product router when the request is feature/design/strategy/research
→ artifact such as story card, PRD slice, competitor matrix, interaction model, or acceptance criteria
→ execution router only after the artifact and confirmation boundary are clear
```

This prevents voice assistant work from degrading into a generic chat UI with a microphone button.
