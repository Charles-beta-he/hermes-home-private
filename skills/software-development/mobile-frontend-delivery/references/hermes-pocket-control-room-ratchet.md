# Hermes Pocket Control Room Ratchet

Scope: class-level pattern for turning a mobile assistant/pocket-agent pain point into a ratcheted product slice that reuses existing Home, voice, Gateway projection, taskpool, and Agent OS/authority gates.

Applicability: use when the user states a pain such as “I can’t see the agent runtime/status/blockers/todos from my phone”, “mobile should show what needs my help”, “voice should ask what Hermes is doing”, or when a mobile/PWA/RN assistant already has Home/voice/navigation and the next feature should become a control-room progression rather than a new isolated dashboard.

Anti-conditions:
- Do not use this to justify external notifications, Apple Reminders/Lark writes, TestFlight/App Store/MDM, push/deploy, credentials, destructive operations, or broad fan-out without exact target authorization.
- Do not create a separate dashboard/app if the existing Home/voice/dock/Gateway projection can carry the pain.
- Do not expose raw engineering diagnostics as the default mobile user experience; keep diagnostics behind Settings/detail disclosure.
- Do not claim real personal-todo integration until the exact source adapter is read back and authorized.

## Core principle

Pain should enter the product as a capability gap, not as a new screen by default. First inventory existing capabilities, identify the smallest ratchet upgrade, land it through owned runtime contracts, and verify the existing UX still holds.

Example pain:

> “On the phone I can’t see your runtime status, what needs my help, or my personal todos.”

Correct product move:

```text
Existing Home + voice + dock + Gateway projection + taskpool/Agent OS
  -> Mobile Control Room summary on Home
  -> needs-human cards
  -> todo projection
  -> runtime voice intents
  -> detail surfaces and authority packets
```

Not:

```text
new standalone dashboard with disconnected status/todo mocks
```

## Ratchet workflow

1. Calibrate the pain into capability gaps.
   - Runtime visibility: status, freshness, self-advance health, last verification.
   - Human assistance: blocked_on_human, open decisions, authority gates, failed cron, stale claims.
   - Personal/project todos: local todo, taskpool user tasks, project P1/P2/P3; external adapters later.
   - Mobile actionability: read evidence, defer, local confirm, generate authorization packet.

2. Inventory existing carriers.
   - Home/orb/avatar: emotional/status center.
   - Voice: fast query/intent entry.
   - Bottom dock/detail surfaces: navigation model.
   - Gateway projection: transport/readback boundary.
   - Handoff/lifecycle summary: authority boundary.
   - Agent OS: route/permission preflight, not unrestricted executor.
   - Taskpool/mission/cron: upstream runtime sources.

3. Choose the smallest product ratchet.
   - Add a read-only operator/control-room projection endpoint first.
   - Add Home summary card and detail anchors second.
   - Add runtime voice intents as read-only/card responses.
   - Keep external notifications and personal data adapters gated.

4. Model the projection contract.

Suggested shape:

```ts
interface OperatorControlRoomProjection {
  schema: 'operator_control_room_projection_v1';
  generatedAt: string;
  runtime: { status: 'healthy' | 'needs_attention' | 'blocked'; label: string; freshness: 'live' | 'local_projection' };
  selfAdvance: { enabled: boolean; lane: 'local_safe' | 'external_gated'; dispatchableCount: number; blockedCount: number };
  needsHuman: Array<{ id: string; title: string; reason: string; risk: 'low' | 'medium' | 'high'; recommendedAction: string; authorityBoundary: string; evidenceRefs: string[] }>;
  todos: Array<{ id: string; title: string; source: 'hermes_local' | 'taskpool' | 'project_ledger'; priority: 'P0' | 'P1' | 'P2' | 'P3'; status: 'pending' | 'in_progress' | 'blocked' }>;
  voiceIntents: Array<{ utterance: string; intent: 'runtime_status_query' | 'needs_human_query' | 'todo_query' | 'safe_continue_request'; responseMode: 'read_only_card' | 'authority_packet' }>;
}
```

5. Gateway rules.
   - Endpoint is read-only and `Cache-Control: no-store`.
   - Requires device id and active device; revoked devices fail closed.
   - Static local projection is acceptable for first ratchet only if labeled `local_projection` and followed by real-source wiring.
   - Later real sources should be taskpool selfcheck/dispatch dry-run, mission state, cron last_error, Agent OS status, and project ledgers.

6. RN/PWA rules.
   - Preserve existing Home voice/orb and bottom dock.
   - Add `control-room-runtime-summary` to Home rather than replacing it.
   - Add detail anchors such as `control-room-needs-human` and `control-room-todos`.
   - Voice hints should include “你现在在干什么？”, “有什么需要我看？”, “我的待办有哪些？”, and “继续推进安全的部分”.
   - High-risk voice intents produce an authority packet, not execution.

7. Verification.
   - Gateway contract test proves schema, no-store header, needsHuman, todos, and voiceIntents.
   - RN tests prove Home and detail anchors are reachable.
   - Production gate requires the new anchors.
   - Run focused Gateway/RN tests and full production verification before claiming local-production readiness.
   - Optional live smoke: start local Gateway, `curl /v1/operator/control-room` with device id, and read back schema/counts/intents.

## Common pitfalls

1. Isolated-dashboard trap: adding a standalone status page while Home and voice remain unchanged. This creates feature sprawl instead of product evolution.
2. Diagnostics-as-UX trap: showing raw taskpool/cron/Agent OS internals on Home. Home should show conclusions and counts; raw evidence belongs in detail/diagnostics.
3. Voice-as-transcription-only trap: leaving voice as generic text input when the pain is runtime/status/todo visibility. Add runtime query intents while keeping execution gated.
4. Static projection overclaim: a first static projection can prove the contract/UI, but it is not real runtime integration until wired to live taskpool/mission/cron/Agent OS readbacks.
5. External-todo overreach: Apple Reminders, Lark Task, calendars, and notifications are separate authorization surfaces; start with local/project/taskpool read-only todos.
6. Authority collapse: “highest authorization” should open safe local self-advance, but not broad push/deploy/notifications/credential/destructive gates without exact targets.

## Acceptance checklist

- [ ] Pain was mapped to capability gaps, not directly to a new screen.
- [ ] Existing Home/voice/navigation/Gateway carriers were reused.
- [ ] Read-only projection contract exists and has tests.
- [ ] Home has a runtime/control-room summary and detail surfaces for needs-human/todos.
- [ ] Voice supports runtime/todo/needs-human query intents as read-only or authority-packet responses.
- [ ] External/personal integrations remain gated unless exact authorization exists.
- [ ] Full local verification passes before local-production claims.
