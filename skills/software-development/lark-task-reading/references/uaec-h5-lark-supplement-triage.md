# UAEC H5 Lark task supplement triage

Scope: read-only analysis after collecting UAEC H5 Lark tasks when the user asks whether tasks need additional clarification, screenshots, Figma, backend input, or product/security confirmation before implementation.

Applicability:
- The tasklist/section inventory is already live-read from Lark, or the user points to a visible H5 board section such as `V1.2.0版本更新计划 / h5端任务`.
- The target project is UAEC H5, with Android/mobile app as a reference implementation when Figma is missing.
- The user asks “是否需要我补充”, “哪些需要确认”, “能不能直接做”, or similar triage before coding.

Anti-conditions:
- Do not treat this as implementation completion or Lark closeout.
- Do not mutate Lark tasks/comments/status.
- Do not store task-specific GUIDs or URLs here; keep those in per-session inventory/evidence artifacts.
- Do not assume `[Image]` placeholders mean screenshots are unnecessary. They mean the Task API stripped image metadata.

## Procedure

1. Start from the live inventory JSON/Markdown, not from memory. Verify:
   - tasklist name and visible section name/count;
   - current Lark user `open_id`;
   - each listed task has `members[].role == assignee` matching the current user;
   - section count equals the visible board count, when the user supplied a screenshot.
2. For each task, classify whether user supplement is required:
   - **No supplement needed**: point fixes with explicit behavior and a local surface, e.g. disabling a clickable logo or simple layout/text fixes with existing code paths.
   - **Low supplement**: UI parity tasks where Android reference or current H5 code can serve as the source when Figma is unavailable; ask only if pixel-level acceptance or a missing asset cannot be derived.
   - **Medium supplement**: tasks asking to “整理词汇”, “AI 跑页面”, “参考移动端/PC”, or spanning a feature with no H5 page. Produce an implementation/wording proposal first, then ask the user to confirm before final closeout.
   - **High supplement**: tasks involving token propagation, security-sensitive URL behavior, new backend/admin configuration, persisted user preference semantics, payments/trading contract behavior, or missing API fields. Stop for product/security/backend confirmation instead of inventing the contract.
3. Use source priority:
   - Current H5 implementation and live API evidence first.
   - Android reference repo for parity when Figma is missing and user/project profile allows it.
   - Figma/design screenshots only when provided or when Android/current code lacks the required visual/flow anchor.
   - Backend/admin contracts only from current interfaces or explicit backend confirmation.
4. Ask for supplements in **bundles**, not one question per task:
   - Design source bundle: “No Figma → use Android reference?”
   - Backend/admin contract bundle: “Does this preference/config persist server-side or local-only? Which endpoint owns it?”
   - Security bundle: “Are tokens allowed in query strings, or should we use same-domain session / one-time jump ticket / backend redirect?”
   - Vocabulary/wording bundle: “I can draft terms; confirm before final closeout.”
5. For banner/deep-link token tasks, treat naked URL tokens as a security-sensitive design choice:
   - Prefer same-domain session/cookie, signed short-lived jump ticket, or backend redirect over appending long-lived account tokens to arbitrary external URLs.
   - If the task text says “带 token”, still ask whether only allowlisted same-domain URLs may receive auth material.
6. Record the triage as a per-task evidence artifact (Markdown + JSON) with fields:
   - `task_title`, `guid`, `suite_entity_num`, `supplement_level`, `supplement_needed`, `default_path_if_no_reply`, `blocked_decision`, `source_priority`, `image_placeholder_count`.

## Reporting pattern

Report the answer as:

- “可以直接做”: list task numbers/titles and why.
- “可先做方案、验收前确认”: list task numbers/titles, proposal source, and exact confirmation needed.
- “必须你/后端/产品先确认”: list task numbers/titles and the blocking decision.
- “图片/设计证据缺口”: count `[Image]` placeholders and specify whether Android reference can substitute.

Keep the report concise and actionable; do not paste every raw comment unless the user asks.

## Common pitfalls

- Treating every task with `[Image]` as blocked. Some UI tasks can proceed from Android reference; mark image evidence as an acceptance risk, not an automatic stop.
- Treating “外部跳转带 token” as a simple frontend concatenation. It is a security boundary and needs allowlist/ticket/redirect semantics.
- Asking the user for Figma when the project profile already authorizes Android as fallback. Ask only if Android lacks the required screen/asset or the task demands exact Figma parity.
- Calling broad backend/admin configuration tasks frontend-only because the visible symptom is in H5. If backend/admin config determines values or sections, classify as contract-confirmation needed.
