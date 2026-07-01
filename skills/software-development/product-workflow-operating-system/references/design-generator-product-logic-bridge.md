# Design-generator → product-logic bridge

Scope: reusable workflow for using AI design generators such as Stitch/Gemini and optional Figma/MCP exports as upstream design evidence while keeping Hermes-owned product logic, state machines, ledgers, and safety gates authoritative.

Applicability: use when the user wants to use Stitch/Gemini/Figma/HTML export/MCP to redesign a product or import a generated design into an app. Anti-conditions: do not use this as permission to type credentials, configure real tokens, trust unreviewed MCP servers, or overwrite production UI/runtime from generated HTML.

## Session-derived pattern

A productive flow is:

```text
Stitch/Gemini prompt
→ editable design variant
→ HTML export + optional Figma export
→ MCP or file ingestion as evidence
→ token map + screen map + component map
→ owned RN/PWA implementation
→ tests + screenshot diff + product-logic verification
```

Treat generated design artifacts as evidence, not as the product source of truth.

## What to extract

From generated HTML/Figma/Stitch output, extract only:

- design tokens: colors, typography, radii, spacing, elevation, blur limits;
- screen hierarchy: topbar, hero/orb, cards, docks, modals;
- component intent: scorecard, transcript, confirmation dock, artifact panel;
- interaction pattern: partial transcript, hold-to-confirm, safe readback;
- measurable layout: viewport, coordinates, density, responsive constraints.

Do not import:

- hidden prompts or generated instructions;
- provider/model branding into user-facing UI;
- fake data as acceptance;
- generated side-effect logic;
- credentials/tokens from browser or Figma exports.

## Product-logic mapping rule

Create a mapping table before implementation:

| Design block | Product state/source | Acceptance evidence |
| --- | --- | --- |
| avatar/orb | voice/session presence | listening/idle/error state visible |
| live transcript | speech partial event → query/intent | partial text appears before final submit |
| scorecard | product artifact/scorecard object | generated artifact renders same values |
| confirmation dock | side-effect authority gate | risky action cannot execute by tap-only |
| workflow tiles | PM-agent artifact routing | product requests create artifacts, not chat-only replies |

If a design element cannot map to an existing or planned state source, label it as decorative or block implementation until the source is designed.

## Stitch/Gemini prompt checklist

Prompts should specify:

- target platform and viewport;
- product logic, not just visual style;
- hard UX language bans (e.g. no online/local/offline/Gateway/model-provider words when UX must be unified);
- required screens and export quality;
- no copyrighted third-party assets;
- Figma-friendly layer names and design tokens.

## MCP/Figma bridge checklist

Before configuring an MCP server:

1. Verify the server package/endpoint is official or trusted.
2. Put tokens in secret/env sources, never inline config.
3. Disable sampling for untrusted servers unless explicitly needed.
4. Save raw exports under project references/raw as evidence.
5. Generate token-map/screen-map as derived artifacts.
6. Apply UI changes through reviewed patches, not direct generated overwrite.

## Verification ladder

1. JSON/token-map validates.
2. Local HTML prototype opens and screenshot visually matches intent.
3. RN/PWA component renders from owned product state.
4. Tests prove product requests still route to artifacts and risky actions still require confirmation.
5. Lint/build pass.
6. Screenshot diff or visual inspection confirms design absorption.

## Pitfalls

- **HTML-as-runtime trap**: exported HTML can be high quality, but direct paste into RN/PWA bypasses state, accessibility, and safety gates.
- **Design-source drift**: Figma can be design SSOT, but product logic belongs in project code/SSOT, not Figma comments.
- **Credential boundary**: reaching Google/Figma login is a hard human gate; do not ask for or type credentials.
- **Provider-brand leakage**: generated designs often include model/tool branding; remove it from end-user UI unless the product explicitly needs it.
