# Visual IP H5 Handoff Pattern

Use when a visual/IP workflow absorption or mascot/product concept needs a tangible local artifact, especially when real image generation is unavailable or blocked by provider setup.

## Trigger

- User asks to continue after a visual workflow has been abstracted.
- A prompt matrix / identity lock / style lock exists.
- Image generation is unavailable, blocked by provider auth, cost, login, or missing env vars.
- The user still wants forward progress and accepts safe reversible local artifacts.

## Pattern

```text
identity/style lock
-> local vector/mock assets or supplied images
-> H5/landing/deck artifact
-> review gates rendered in page
-> provider boundary called out
-> browser + console + visual verification
-> ledger/update packet
```

## Artifact requirements

- Produce a complete local HTML file, preferably self-contained except for local assets.
- Include the actual asset pack, not just text.
- Include business context: audience, use case, output tier, platform route.
- Include workflow sections: intake, identity lock, style lock, prompt matrix/batch, review gates, delivery.
- Explicitly label if assets are local SVG/mockups rather than final AI renders.
- Include next-step boundary: what provider credential/login/upload/payment is needed for real generation.

## Review gates to render

- `identity_consistency_gate`: palette, silhouette, face, clothing/accessories, scale.
- `rights_risk_gate`: famous-IP similarity, competitor marks, unknown ownership, commercial-use risk.
- `commercial_layout_gate`: whitespace, product visibility, platform aspect ratio, typography readiness.
- `pack_completeness_gate`: required output groups and count.
- `provider_authority_gate`: image provider configured, upload permission, cost/payment boundary.

## Verification checklist

- [ ] File exists at stated path.
- [ ] Local assets exist and render.
- [ ] Browser opens the HTML.
- [ ] Console has no JS errors.
- [ ] Primary viewport is visually inspected.
- [ ] Obvious layout issues are fixed before handoff.
- [ ] Review ledger or handoff packet records the boundary and verification evidence.

## Pitfalls

- Do not say AI images were generated if a provider failed. Use explicit wording like “local SVG mockup” or “storyboard asset.”
- Do not stop at the missing provider if a reversible local H5/deck/prototype can still prove the workflow.
- Do not hide the provider boundary in small print; make it visible in the artifact and final response.
- Avoid generic SaaS filler sections; every section should support the asset-pack handoff.
