# Mobile Hybrid Avatar Control-Room Redesign

Scope: mobile/PWA/RN assistant shells that risk becoming generic chatbot or offline-local-model demos. Applicability: Hermes-style companion apps where online agent/server remains authority and local evidence/model is only a fallback. Anti-conditions: do not apply to products intentionally positioned as fully offline local-AI apps, or to simple chat widgets with no gateway/task/action boundary.

## Trigger signals

- User says the product/UI feels like a toy chatbot, generic assistant, or over-emphasizes offline/local model.
- Screenshots show labels such as “offline assistant”, “local model can answer”, or “Local Offline” as the primary brand while the intended product is hybrid/online-authoritative.
- A local model or offline evidence lane is technically useful but product copy makes it look like the fact source or normal execution path.
- The UI has a large text-heavy status card, weak hierarchy, or no clear separation between authority, fallback, queue, evidence, and composer.

## Reference-repo absorption pattern

When asked to improve via GitHub references, do not cargo-cult a repo’s runtime model. Extract transferable UI/product patterns:

- Native AI chat examples such as FoundationChat: conversation persistence, model availability state, structured errors, streaming/readiness feedback.
- Hermes companion/control-room apps such as Scarf: operator visibility, capability gates, health/diagnostics, session/task/memory awareness.
- Production chat UI kits such as Sendbird UIKit: separate message list, composer, unread/queue counts, panels, reusable foundations.
- ChatGPT mobile clones: history, bottom sheets, native menus, efficient lists, streaming affordances — useful mechanics, not authority model.
- Client-only chatbot wrappers: streaming/conversation identity can transfer; client-only authority usually should not transfer to Hermes-style products.

Record the synthesis in a scoped design-reference note when useful, but implement the owned product model instead of copying visual chrome.

## Correct product model for hybrid avatar shells

Default wording and IA:

1. Identity: “混合分身” / “Hybrid avatar”, not “离线分身” unless offline is explicitly the product strategy.
2. Main authority: online Hermes/Gateway handles current facts, tools, tasks, memory, and external side effects.
3. Fallback lane: local synced evidence and local model handle offline/weak-network answer/draft only.
4. Side effects: external actions are queued for online readback/confirmation; phone does not write canonical facts or execute actions offline.
5. Evidence: local answer labels must mention evidence/source constraints; sources collapsed by default but reachable.

Preferred interaction hierarchy:

- Compact brand header with runtime pill: user-facing pill should be neutral (`就绪`, `处理中`, `需检查`) unless the user explicitly asks to expose technical routing. Avoid `Hybrid`, `Local`, `Online`, or `Fallback Local` as primary UX labels for a unified avatar.
- Keep the default interaction surface operational: current status, queue count, sync/reset actions, message thread, quick actions, and composer.
- Move explanatory material to a separate surface such as `说明`, `Guide`, `About`, a sheet, or an expandable details panel: product model, permission boundaries, fallback semantics, capability cards, Gateway URL/device diagnostics, and long safety copy belong there, not in the main turn-taking layer.
- Use toasts or inline action receipts for short transient confirmations such as queued/saved/reset/synced; do not leave persistent explanation blocks after every action.
- Capability cards are useful on onboarding/guide surfaces. On the main interaction surface, show only compact state chips if they directly help operation.
- Message/decision surface: one primary next-action or conversation message, with collapsed evidence chips.
- Composer: short placeholder that asks the hybrid avatar; mention fallback only as secondary copy.

## UI pitfalls

- Do not make “local model” the hero. It should be a fallback/adapter label, not product identity.
- Do not make online/local/offline a user-facing mode split when the product is a unified hybrid avatar. Implementation may route between server authority, synced evidence, device cache, and local adapters, but the UX should present one assistant with neutral labels such as `分身`, `上下文`, `任务`, `回读`, `确认`, and `安全执行`. Keep `online/local/offline/Hybrid/Local/小模型` wording in contracts, diagnostics, logs, or developer docs only.
- Do not put long policy, product, permission, or diagnostic paragraphs in the main interaction card if they crowd out the actual decision/action. Move them to a guide/about page, bottom sheet, details panel, or toast depending on persistence needs.
- Do not treat “more explanation” as safer UX. For mobile assistant shells, persistent explanation belongs outside the turn-taking layer; the main layer should optimize for the user's next action.
- Do not call a Chrome/PWA/mobile screenshot “good” just because tests pass; inspect for stale persisted copy, truncation, hidden composer, overcrowded cards, and status ambiguity.
- Do not let AsyncStorage/IndexedDB persisted welcome messages preserve old product copy after a positioning correction. Bump schema/key or migrate stale envelopes.
- Do not rely on image generation as the only design path. If the image tool lacks credentials or quota, proceed with a code-level redesign and real screenshot verification.

## Verification checklist

- Search implementation copy for banned/misleading terms: “offline-first”, “本机小模型可回答”, “小模型离线回答”, “我是你的离线分身”, primary “Local Offline”.
- Run unit/static tests for copy/state changes.
- Build/launch the target mobile surface when available.
- Capture an actual screenshot and inspect: product positioning, hierarchy, truncation, disabled/enabled affordances, composer visibility, bottom safe area.
- If stale copy appears only at runtime, inspect persistence keys, bootstrap seed messages, and local storage migration.
