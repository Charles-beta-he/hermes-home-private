# Intent Card

## Objective

Land a Hermes-local product workflow operating system adapted from a verified external PM skill/workflow marketplace pattern.

## User / Segment

Primary user: Charles / Hermes operator who needs evidence-first product, workflow, PRD, shipping, launch, and ratchet processes that can become reusable skills and taskpool artifacts.

## Scenario

A social video highlighted an open-source AI product-management operating system. The desired outcome is not another analysis note, but a reusable Hermes workflow pack that can be loaded in future sessions and can scaffold durable workspaces.

## Evidence So Far

- Source: WeChat Channels preview + verified repository clone + repository validator.
- Claim: external source is a 9-plugin PM skills/workflows marketplace with a clean skill/command split.
- Confidence: high for repository structure and validator count; medium for social-post framing; source-specific facts are stored in the scoped review note.

## Non-goals

- Do not auto-install or execute third-party skills.
- Do not copy external local names/counts into global Hermes rules.
- Do not enqueue broad trend-study tasks.
- Do not claim production runtime integration beyond the local skill/templates/script landed in this session.

## Success Criteria

- Observable result: `product-workflow-operating-system` skill exists and loads through `skill_view`.
- Acceptance evidence: frontmatter/template validation, script `py_compile`, script dry-run, script real scaffold smoke test, and a real workspace under `~/.hermes/workflows/product/pm-skills-product-workflow-os/`.
- Stop condition: local reusable workflow pack is installed and verified; external side effects and third-party installation remain out of scope.

## Authority Boundary

- Local artifact writes allowed: yes
- Taskpool enqueue allowed: not needed for this landing unless user asks for runtime router integration
- Code changes allowed: no core-code changes needed for this landing
- External publishing/sending allowed: no
- Private access material needed: no
