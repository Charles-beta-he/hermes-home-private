# 3D IP Extension Pack Absorption Pattern

Scope: use when absorbing public media, design demos, or client requests about 2D-to-3D IP/mascot conversion, 3D brand character extension, ecommerce visual packs, social/H5 asset packs, or “老板要看3D的IP延展和套图” style workflows. Anti-conditions: do not claim hidden/login-gated video steps, do not bypass platform login gates, do not copy protected famous IP, and do not publish or sell generated assets without rights review.

## Transferable pattern

```text
public/user IP reference + commercial brief
-> identity extraction
-> style lock
-> prompt matrix
-> generation batch manifest
-> identity/rights/commercial review gates
-> selected asset pack
-> ecommerce/social/H5/proposal delivery board
```

## Evidence tiers

```yaml
visible_media_facts:
  - resolved URL/title/tags/search text/duration when visible
  - author/metrics only when visible and not obscured
  - login/app gate status

user_or_artifact_facts:
  - uploaded reference images
  - brand kit/product photo/platform dimensions
  - user-declared rights/commercial use

unverified_or_blocked:
  - hidden video transcript/frames behind login gate
  - commercial rights if user cannot confirm ownership
  - provider output quality before generation/readback
```

## Capability graph nodes

```yaml
atomic_modules:
  - ip_asset_intake
  - visual_identity_extraction
  - style_lock_builder
  - prompt_matrix_builder

adapters:
  - generation_batch_adapter

composite_modules:
  - asset_pack_review

workflows:
  - delivery_board_builder

gates:
  - identity_evidence_gate
  - rights_risk_gate
  - prompt_completeness_gate
  - provider_authority_gate
  - identity_consistency_gate
  - commercial_layout_gate
  - pack_completeness_gate
  - delivery_readback_gate
```

## Prompt matrix contract

Every reusable pack should include at least:

- base 3D conversion prompt;
- turnaround sheet prompt: front / 45-degree / side / back;
- expression pack prompt;
- action pack prompt;
- product/ecommerce interaction prompt;
- negative prompt preserving identity and avoiding protected-IP imitation;
- output tier: quick / standard / proposal.

## Review gates

```yaml
identity_consistency_gate:
  checks: [palette, silhouette, face, clothing, accessories, scale]
  fail: regenerate_or_retouch

rights_risk_gate:
  checks: [famous_ip_similarity, competitor_logo, unknown_ownership, commercial_use]
  blocked: human/legal_gate

commercial_layout_gate:
  checks: [copy_whitespace, subject_clarity, product_visibility, platform_aspect_ratio]
  fail: regenerate_layout

pack_completeness_gate:
  checks: [required_output_groups_present, minimum_count, prompt_ledger_complete]
  warn: deliver_partial_pack_labeled
```

## Authority boundaries

Safe without additional authority:

- analyze visible public media metadata;
- produce prompt matrix/template;
- create local workflow docs and review checklists;
- review user-provided outputs locally.

Requires explicit gate:

- provider login, image upload, paid generation, batch generation cost;
- commercial usage assertion or legal clearance;
- public publishing or external channel delivery;
- using a protected brand/IP reference beyond user-owned material.

## Completion proof

Do not claim the workflow is implemented until at minimum:

- prompt matrix exists;
- identity/style locks are documented;
- gates have pass/warn/fail/blocked outcomes;
- selected asset pack is read back, or provider boundary is explicitly blocked;
- evidence ledger labels visible facts vs assumptions vs gated content.
