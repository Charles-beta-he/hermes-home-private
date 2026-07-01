# Template-variable hydration bugfix slice pattern

Extracted from `/Users/charles/.hermes/skills/incremental-implementation/SKILL.md` on 2026-07-01T08:55:33.664327+00:00 by generic core-body debt remediation. Root SKILL.md keeps a progressive-loading pointer; content is preserved here.

## Template-variable hydration bugfix slice pattern

Scope: any templated outbound artifact (email, notification, PDF, SMS, in-app message) where delivered output exposes raw placeholder syntax or a field renders in one channel but not another.

Applicability:
- The template is persisted or editable separately from the code that supplies variables.
- The same business event can fan out through multiple renderers or channels.
- Missing-variable behavior may leave placeholders visible instead of failing closed.

Anti-conditions:
- Do not encode one product's exact template codes, branch names, or migration file names in this global skill.
- Do not treat this as a license to weaken template text; preserve user-facing meaning and security intent while adding fallbacks.
- Do not expose PII as a fallback; mask identity fields before adding shared defaults.

Process:

1. Treat the screenshot/UI symptom as a contract bug, not just copy or CSS.
   - Trace the chain: template definition → event/caller vars → dispatcher/enricher → renderer missing-variable behavior → delivered artifact.
   - Compare sibling channels for the same event; one channel may pass the full variable set while another passes only a subset.

2. Fix the narrow caller first.
   - Build an explicit variable map for the affected event containing every variable used by the template.
   - Add null/blank fallbacks before insertion; avoid null-rejecting map factories when any value can be absent.
   - Prefer stable subject/body wording that does not depend on unreliable enrichments such as IP geolocation.

3. Add a shared enrichment layer only for truly common user-context variables.
   - Good defaults include a generic display-name fallback and a masked email fallback when the user object is available.
   - Calling code should still own event-specific fields such as address, location, device, amount, timestamp, or reference id.
   - Caller-provided values must win over dispatcher defaults.

4. Test both levels.
   - Caller test captures the map passed to the dispatcher and asserts template-required event variables plus fallbacks.
   - Dispatcher test captures the map passed to the renderer and asserts shared identity fallbacks/masking.
   - If available, keep or add renderer-level tests that fail when final output still contains raw placeholder syntax.

See also: `references/template-variable-hydration-bugfix.md`.
