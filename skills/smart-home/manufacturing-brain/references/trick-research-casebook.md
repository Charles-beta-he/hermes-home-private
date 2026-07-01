# Manufacturing Trick Research / 邪修 Casebook

Extracted from `/Users/charles/.hermes/skills/smart-home/manufacturing-brain/SKILL.md` on 2026-07-01T08:52:42.874486+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Trick research / 邪修 casebook

When `quality_experience_review` flags risks, use bounded web research before trying unusual slicer/profile fixes:

```bash
python3 ~/.hermes/scripts/manufacturing_trick_research.py plan \
  --preflight /path/preflight.json \
  --printer "Bambu X2D" \
  --material PLA \
  --json
```

Policy:
- Web findings are candidates, not truth. Never auto-apply a hack from the internet.
- Reject unsafe machine modifications: firmware/electrical bypass, thermal-runaway disablement, sensor/interlock bypass, temperature-limit override, credential/cloud-upload tricks.
- A candidate needs at least two independent sources, before/after evidence, same-material or reasoned transfer, and operator review.
- Successful local results are remembered in the manufacturing casebook, not raw user memory:
  `~/.hermes/brains/manufacturing/knowledge/trick-casebook.jsonl`.
- Generalizable repeated successes may be promoted into this skill with `skill_manage`; unverified web claims must not be promoted.

Record a successful verified fix:

```bash
python3 ~/.hermes/scripts/manufacturing_trick_research.py record-success \
  --risk-id support_material_review \
  --title "PETG interface support reduced PLA support scars" \
  --printer "Bambu X2D" \
  --material PLA \
  --model-class "decorative miniature" \
  --settings "support interface material PETG; top z distance 0; interface layers 2" \
  --evidence-url https://example/source1 \
  --evidence-url https://example/source2 \
  --before "support scars on visible face" \
  --after "support removed cleanly; no visible scars" \
  --outcome success \
  --json
```
