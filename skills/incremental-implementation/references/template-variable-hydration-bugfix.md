# Template-variable hydration bugfix reference

Use this as a compact checklist when a delivered notification/email/document shows raw placeholders.

## Symptom pattern

- User-visible output contains placeholder syntax such as `{{field}}`.
- Some fields render correctly while neighboring fields stay raw.
- A sibling channel for the same business event may render better because it receives a fuller variable map.

## Investigation chain

1. Locate the template source.
   - Database seed/migration, admin template editor defaults, CMS row, or static template file.
   - Extract the complete variable set from subject/title/body/html.

2. Locate the event caller.
   - Find the code path that emits the notification/email/document.
   - Capture what variable map it passes to the dispatcher or renderer.
   - Compare with sibling fanout paths for the same event.

3. Locate dispatcher/enrichment behavior.
   - Check whether common user-context variables are injected automatically.
   - Confirm caller-provided values win over defaults.
   - Mask identity fields before adding them to templates.

4. Locate renderer missing-variable behavior.
   - Missing variables may be retained as `{{field}}`, blanked, or fail the send.
   - For security-sensitive outbound messages, raw placeholders should be a send-blocking condition or at least a high-priority error.

## Fix pattern

- Caller owns event-specific variables: IP/address/location/device/timestamp/amount/reference id/etc.
- Dispatcher/enricher may own common user-context variables: generic display-name fallback and masked email.
- Apply null/blank fallbacks before building maps; avoid map factories that reject nulls when input data can be absent.
- Prefer stable user-facing titles that do not depend on unreliable enrichments like IP geolocation.

## Regression tests

- Caller test: capture vars passed to dispatcher and assert every template-required event field exists with fallback values.
- Dispatcher test: capture vars passed to renderer and assert shared identity defaults/masking are added without overwriting caller values.
- Renderer/integration test: final rendered output must not contain unresolved placeholder syntax.
- Negative case: missing required variables in security-sensitive templates should fail closed or be logged with an explicit error path.
