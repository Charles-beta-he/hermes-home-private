# Visual Commercialization Router-First Absorption

Scope: product/workflow absorption from social videos, design-tool demos, image-generation demos, or marketplace examples that turn visual assets into commercial outputs.

Applicability: use when a source artifact shows a visual chain such as `2D IP -> 3D render -> proposal board -> e-commerce image set`, or when the user asks to turn images/renders/products/IP into promotional or marketplace assets.

Anti-conditions:

- Do not apply when the user only wants a plain summary of a video and no reusable product/workflow output.
- Do not route production-grade CAD, mesh, 3D printing, manufacturing, legal clearance, or marketplace publishing through this visual proposal workflow.
- Do not assume a full pipeline when the requested deliverable is only a sub-capability.

## Core lesson

Do not absorb a demo chain as a monolith. Learn small reusable capability modules first, then compose by requested deliverable.

```text
Intent Router -> Asset Model -> Capability Modules -> Workflow Composition -> Agent Roles -> Evidence/Gates -> Delivery Packet
```

## Learning constraints

1. **Do not copy demo chains as default workflows**
   - A video may show A -> B -> C -> D, but future users may only need B or D.
   - Split into atomic modules, composite workflows, gates, and closure states before naming the full workflow.

2. **Route by deliverable, not source demo**
   - `一组3D图` -> concept generation.
   - `一组图生成宣传` -> existing-images-to-promo layout/copy workflow.
   - `三视图` -> orthographic/reference workflow.
   - `商品图做亚马逊A+` -> product-photo-to-commerce workflow.
   - `完整IP商业化全案` -> full composition.

3. **Treat existing assets as first-class inputs**
   - Source assets may be an IP image, product photo, finished render, logo, packaging, competitor reference, scene reference, existing poster, or copy brief.
   - Do not treat every image as a style reference or force every job to start from 2D-to-3D generation.

4. **Separate transformation from layout**
   - Asset transformation: make/enhance images (`hero_3d_render`, `product_render_enhancement`, `scene_background_generation`).
   - Asset layout: arrange existing images into posters/sets (`single_poster_generation`, `image_set_layout`, `commerce_image_set`).
   - Copy and QA are separate modules, not hidden inside generation.

5. **Use minimal agent sets**
   - Generation-only: identity analyst, prompt composer, generation adapter, visual reviewer.
   - Existing-images-to-promo: asset role clustering, promotion strategy, copy/layout, visual QA.
   - Full commerce: orchestrator plus marketplace and production-boundary reviewers.

6. **Declare closure state**
   - Use explicit states such as `prompt_pack_ready`, `visual_candidates_ready`, `promo_pack_ready`, `commerce_draft_ready`, `proposal_ready`, or `production_blocked`.
   - Never let generated proposal images imply listing-ready or manufacturing-ready status.

## Architecture levels

### A. Intent layer

```yaml
intent_card:
  primary_intent: 3d_concept_generation | orthographic_reference | character_bible | existing_images_promotion | product_render_upgrade | commerce_pack | full_ip_commercialization
  requested_deliverable: string
  non_goals: []
  closure_target: prompt_pack_ready | visual_candidates_ready | promo_pack_ready | commerce_draft_ready | proposal_ready | production_blocked
```

### B. Asset layer

```yaml
asset_model:
  assets: []
  roles:
    - source_ip
    - product_photo
    - render_candidate
    - brand_logo
    - brand_kit
    - packaging
    - style_reference
    - competitor_reference
    - scene_reference
    - existing_poster
    - copy_brief
  identity_sources: []
  style_sources: []
  layout_sources: []
  claim_sources: []
  rights_status: verified | user_provided | unknown | risky
```

### C. Module layer

Common module families:

- intake: `asset_intake`, `visual_identity_extraction`, `style_direction`
- prompt: `prompt_pack_builder`, `negative_prompt_builder`, `retry_prompt_delta_builder`
- generation: `hero_3d_render`, `hero_3d_variation_set`, `orthographic_view_sheet`, `expression_pose_sheet`, `product_render_enhancement`, `scene_background_generation`
- layout: `single_poster_generation`, `image_set_layout`, `commerce_image_set`
- copy: `promo_copy_draft`, `commerce_copy_draft`, `marketplace_title_bullets`
- review: `visual_qa`, `marketplace_qa`, `production_boundary_review`

### D. Composition layer

```yaml
ip_3d_concept_pack:
  chain: [asset_intake, visual_identity_extraction, style_direction, prompt_pack_builder, hero_3d_render, hero_3d_variation_set, visual_qa]
  closure: visual_candidates_ready

existing_images_to_promo_pack:
  chain: [asset_intake, asset_role_clustering, style_direction, promo_copy_draft, image_set_layout, visual_qa]
  closure: promo_pack_ready

product_photo_to_commerce_pack:
  chain: [asset_intake, visual_identity_extraction, product_render_enhancement, scene_background_generation, commerce_copy_draft, commerce_image_set, marketplace_qa]
  closure: commerce_draft_ready

ip_full_commercialization_pack:
  chain: [ip_3d_concept_pack, orthographic_reference_pack, expression_pose_sheet, ip_board_layout, commerce_copy_draft, commerce_image_set, marketplace_qa, production_boundary_review]
  closure: proposal_ready
```

## Pitfalls

- Every visual/IP request becomes a full IP commercialization pipeline.
- Existing user images are treated only as style references instead of layout/source assets.
- A poster/layout request triggers unnecessary image generation.
- `final_qa` is one generic step instead of separate visual, copy, marketplace, and production-boundary gates.
- All agents are activated for all requests.
- Proposal artifacts are described as listing-ready or production/manufacturing-ready.

## Verification checklist

- [ ] Requested deliverable is explicit before selecting modules.
- [ ] Source assets are role-modeled before prompting.
- [ ] The smallest sufficient workflow composition was selected.
- [ ] Required agents are minimal and tied to the selected composition.
- [ ] Evidence/gate requirements are stage-specific.
- [ ] Closure state is stated honestly.
- [ ] Production/listing/legal/manufacturing boundaries are preserved.
