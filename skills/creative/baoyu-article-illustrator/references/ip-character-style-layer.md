# IP Character / Personal Style Layer for Article Illustration

Scope: reusable article-illustration procedure. Applicability: use when a user wants article illustrations in their own style, brand mascot, recurring IP character, or fixed visual identity. Anti-conditions: do not copy a social creator's exact mascot/design, do not import unverified third-party repos, and do not treat social-video claims as implementation proof.

## Core pattern

Add a reusable style layer between article analysis and prompt generation:

```text
article/source content
  -> semantic illustration positions
  -> visual outline
  -> IP character/style bible
  -> prompt files
  -> generated images
  -> visual verification
```

This is a workflow pattern, not a specific mascot or third-party asset import.

## IP character/style bible

Create `{output-dir}/character-bible.md` when the user provides a character, brand mascot, visual style, reference image, or verbal style description.

Recommended fields:

```yaml
---
character_name: "<name or role>"
ownership: "user-provided | user-owned | verbal-description | reference-image"
usage: recurring-character
---

## Appearance
- silhouette/body shape:
- head/face features:
- clothing/accessories:
- proportions:
- line treatment:

## Personality
- traits:
- default emotional range:
- gestures/body language:

## Color System
- primary colors:
- accent colors:
- forbidden colors:

## Scene Vocabulary
- common props:
- common environments:
- role in diagrams:

## Negative Constraints
- do not copy third-party mascots exactly
- do not use photorealistic celebrity/person likenesses
- keep identity consistent across all illustrations
- prioritize article-specific labels and facts over decoration
```

## Automatic position decision

When the user asks for automatic article illustration, choose positions by semantic value, not by paragraph count alone.

Prioritize sections that contain:

1. A core thesis or turning point.
2. A workflow/process/checklist.
3. A framework/model/architecture.
4. A before/after contrast.
5. Data, metrics, or business trade-offs.
6. A concrete scenario where the recurring character can act as guide/operator/user.

Avoid illustrating:

- filler paragraphs;
- repeated claims;
- purely decorative transitions;
- literal metaphors that obscure the underlying concept.

## Prompt integration rules

Every prompt for IP-character mode must include a compact `CHARACTER CONSISTENCY` section:

```text
CHARACTER CONSISTENCY:
- Recurring character: <name/role>
- Appearance: <stable visual traits from character-bible.md>
- Personality/action: <gesture or role for this illustration>
- Palette: <stable palette>
- Keep the same character identity across the full article set.
- Do not imitate or copy third-party mascots; use only the user-provided style contract.
```

For each image, make the character perform a content-specific role rather than standing decoratively:

| Illustration type | Character role |
|---|---|
| infographic | guide pointing at data/cards |
| flowchart | operator moving through steps |
| framework | system owner/observer beside model |
| comparison | before/after actor showing state change |
| scene | protagonist in a concrete article scenario |
| timeline | traveler/marker moving along milestones |

## Verification

Before finalizing, inspect generated images or thumbnails and check:

- character identity remains consistent;
- style/palette are consistent;
- article facts/labels are preserved;
- image locations match semantic positions;
- no third-party mascot/design is copied;
- prompt files and `character-bible.md` exist for reproducibility.

## Social-source redline

A social-video demo is evidence for a workflow idea, not authority to copy its exact visual IP, clone its repo, or treat its claims as implementation proof. Absorb the class-level pattern only.
