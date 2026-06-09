# Skill Overlap Findings

Discovered during 2026-05-29 self-knowledge audit. 128 skill directories identified.

## Duplicate Pairs

| Skills | Overlap | Recommendation |
|--------|---------|----------------|
| `impeccable` / `impeccable-skill` | Same domain, one is copy | Merge into `impeccable` |
| `ui-ux-pro-max` / `ui-ux-pro-max-skill` | Same domain, one is copy | Merge into `ui-ux-pro-max` |

## Design Skill Cluster (4 overlapping)

| Skill | Focus | Keep? |
|-------|-------|-------|
| `design` | General design principles | Yes (umbrella) |
| `design-system` | Token architecture, component APIs | Yes (specific) |
| `ui-skills/skills` | Baseline UI, accessibility, metadata, motion | Yes (quality gates) |
| `ui-styling` | CSS/styling implementation | Yes (implementation) |

These are complementary but triggers overlap. Consider:
- `design` = umbrella for design thinking
- `design-system` = token/component architecture
- `ui-skills` = quality validation (baseline, a11y, metadata, motion)
- `ui-styling` = CSS implementation

## ML/Training Skills (likely irrelevant to frontend/blockchain career)

- `fine-tuning-with-trl`
- `peft-fine-tuning`
- `evaluating-llms-harness`
- `serving-llms-vllm`
- `audiocraft-audio-generation`
- `segment-anything-model`
- `stable-diffusion-image-generation`

## Experimental/Prototype Skills

- `bayesian-agent`
- `darwin-skill`
- `cognitive-load-agent`
- `ooda-agent`
- `idea-refine`

## Low-Frequency Skills

- `minecraft-modpack-server`
- `rokid-rizon-platform`
- `openhue`
- `ascii-art`
- `pua` / `pua-en` / `pua-ja`
- `yes`
- `taste-skill`
- `yuanbao`
- `leisure`

## Cleanup Criteria

Keep if:
1. User triggers weekly+
2. Serves UVISA/Hermes/求职 directly
3. Prevents high-frequency errors
4. Has cross-session procedural value

Archive if:
1. No trigger in last 30 sessions
2. Irrelevant to user's career goals (frontend/blockchain)
3. Superseded by newer skill
4. Never matured past prototype
