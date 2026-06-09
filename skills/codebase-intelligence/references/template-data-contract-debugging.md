# Template/Data Contract Debugging Pattern

Use this reference when a rendered user-facing artifact (email, notification, receipt, PDF, SMS, push, in-app card) shows raw placeholders such as `{{location}}`, empty fields, wrong language text, or data that only partially renders.

## Core principle

Do not treat the visible artifact as a frontend-only display bug. Trace the full contract:

1. Artifact screenshot or delivered content: list every visible placeholder and every field that did render.
2. Template source: find where subject/title/body/preheader/HTML are authored or seeded.
3. Sender/caller: find the code path that invokes the renderer and the exact variable map passed to it.
4. Renderer semantics: verify whether missing variables become blank, keep the raw placeholder, throw, or silently fallback.
5. Data providers: trace each variable back to its source (request IP, user table, geolocation resolver, device parser, event timestamp, business object, etc.).
6. Guardrails: check whether post-render unresolved placeholder detection exists before delivery.

## Iceberg search workflow

Start with the visible symptom, then expand outward:

1. Search exact visible strings from the screenshot/content, including uncommon phrases, brand footer text, CTA text, and raw placeholders.
2. If many results appear, narrow by brand/template-specific phrases and likely repos/modules.
3. Read the template source around the matching lines and extract the declared/implicit variable set.
4. Search for the template code/key or sending API call.
5. Read the caller and compare `requiredPlaceholders(template)` vs `providedVars(caller)`.
6. Read renderer implementation to determine final behavior for missing vars.
7. Report as a data-contract mismatch with evidence: `template expects X`, `caller provides Y`, `renderer does Z`.

## Common root causes

- Admin-authored template added placeholders that the backend caller never supplies.
- Backend computes a value for one channel but does not pass it to another channel.
- Template variable name differs from caller key (`user_name` vs `username`/`name`).
- Data source can fail (e.g., geolocation lookup) but has no fallback.
- Renderer intentionally preserves missing placeholders for QA, but production send path has no residual-placeholder gate.
- Documentation says a variable is auto-injected, but implementation only injects a smaller default set.

## Fix strategy

Layer fixes from fastest to most durable:

1. Stop the bleeding: remove or replace unsupported placeholders in active templates, or revert to a template whose placeholders match the caller.
2. Restore contract: pass all required variables from the caller, with non-null fallbacks for unstable data.
3. Central defaults: where the sender already has recipient/user context, auto-inject common fields like display name, masked email, year, support URL, locale-aware labels.
4. Guardrail: after rendering, detect unresolved placeholders with a pattern like `\{\{\s*[A-Za-z_][A-Za-z0-9_]*\s*\}\}` and block security/finance/KYC messages if any remain.
5. Authoring validation: template save/preview UI should extract placeholders and compare them with declared/allowed variables for that template code/key.
6. Tests: cover complete vars, missing optional data fallback, missing required var failure, and rendered output containing no raw placeholders.

## Reporting format

- Symptom: what the user sees.
- Source chain: screenshot/content → template source → caller vars → renderer behavior → data providers.
- Mismatch: expected variables vs provided variables.
- Severity: user trust/security/financial impact.
- Fast mitigation.
- Durable fix.
- Verification cases.

## Pitfalls

- Do not claim the template is only a visual shell until you have checked the specific template code/key; some systems mix shell templates and full-copy templates.
- Do not assume successful rendering of one variable means the render pipeline is healthy; it may only prove that one caller key exists.
- Do not expose raw user identifiers in the report; mask emails, phones, tokens, and other sensitive values.
