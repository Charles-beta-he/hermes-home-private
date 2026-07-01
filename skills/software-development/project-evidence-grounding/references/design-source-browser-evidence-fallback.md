# Design-source evidence without unsafe credentials

Use this reference when project work depends on a browser-only design source such as Stitch, Figma, Framer, or another authenticated design tool, and API/MCP extraction is blocked by unsafe or unavailable credentials.

## Applicability

Use when:

- A design/prototype source exists in an authenticated browser session.
- The user wants implementation to continue rather than wait for perfect API extraction.
- Figma/MCP/REST access is blocked by a credential boundary, login state, or export UI issue.
- The deliverable can be advanced from screenshot/browser evidence while preserving a later path to node-level extraction.

Anti-conditions:

- Do not use this to bypass permission, payment, admin, or secret-entry dialogs.
- Do not persist a token/API key that appeared in chat, screenshots, logs, or browser-visible text. Treat it as compromised even if the user says to proceed.
- Do not claim Figma-node parity when only screenshot/browser evidence was used.

## Workflow

1. Establish the source-of-truth chain:
   - product/project profile rule
   - browser design/prototype evidence
   - implementation target
   - verification artifacts
2. If a token is exposed in chat/screenshot/logs:
   - refuse to write it into env/config/history
   - continue with non-secret browser evidence where safe
   - document that node-level extraction is blocked until a fresh credential exists
3. Capture durable browser evidence before implementation:
   - screenshot path
   - project URL if non-secret
   - visible page/frame names
   - observed design corrections or user-authored critique
4. Try export/API/MCP only within safe boundaries:
   - use existing authenticated browser session if authorized
   - stop at token or permission prompts
   - if export UI reports no selected frames, record attempts and fall back to screenshot evidence
5. Implement the smallest grounded slice:
   - encode the durable product correction, not the tool-specific artifact
   - preserve product architecture/UX rules over design-tool-generated technical wording
   - avoid copying protected images/logos/assets; translate layout, hierarchy, token feel, and interaction intent
6. Verify with real outputs:
   - tests/lint/build
   - runtime screenshot or browser proof
   - visual check against captured evidence
7. Write a scoped evidence report under the project repo or skill reference:
   - what was captured
   - what was blocked
   - what was implemented
   - what verification returned

## Product-language pitfall

When a product is architecturally hybrid but the user experience should be unified, do not let implementation/debug language leak into UI copy. For avatar/assistant products, labels like “offline/local/hybrid/fallback/small model/Gateway” usually belong in diagnostics or architecture docs, not the primary conversation surface. Phrase the user-visible experience as one assistant with states such as ready, processed, queued for readback, or needs confirmation.

## Evidence-report skeleton

```md
# Design-source evidence and implementation — YYYY-MM-DD

## Credential / permission boundary
- What secret or permission boundary existed
- What was not done
- Safe fallback used

## Captured design evidence
- URL
- Screenshot paths
- Visible frames/pages
- User/design corrections observed

## Extraction/export attempts
- Tool/UI steps tried
- Exact blocker text
- Whether node-level evidence exists

## Implementation
- Files changed
- Product correction encoded
- Scope intentionally not changed

## Verification
- Commands
- Exit codes / pass counts
- Runtime screenshot path
- Visual findings

## Remaining blocker
- What credential/action would unlock full design-node parity
```
