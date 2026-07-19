# Routing Baseline

## Contract

- Positive cases load this skill when material uncertainty must be resolved through competing hypotheses, discriminating probes, evidence updates, and reproducible closure.
- `systematic-debugging` remains the primary route for an ordinary observed software bug; this kernel is added when competing explanations or confidence updates are materially contested.
- `research` / `last30days` remains primary for source discovery; this kernel governs claim testing after sources are gathered.
- `objective-model-path-verification` remains primary for comparing execution paths; this kernel resolves uncertain assumptions inside the situation model.
- External side-effect requests do not gain authority from this skill.

## Accessory load policy

- `templates/inquiry-packet.json`: conditionally-read for Standard or stronger mode, or when a durable packet is requested.
- `scripts/validate_inquiry_packet.py`: conditionally-run after creating or editing a JSON inquiry packet.
- `references/theory-to-engineering-map.md`: defer-safe; load only for theoretical provenance, method selection, or core-work questions.
- `assets/example-inquiry-packet.json`: example/evaluator-only; normal inquiry must not load it.
- `scripts/test_validate_inquiry_packet.py`: maintainer-only; run after validator or schema changes.
- `evals/prompts.csv`: evaluator-only; not part of normal execution.

## Expected counts

- Positive: 4/4 route to this skill.
- Neighbor: 3/3 remain with the narrower neighbor unless a disputed-assumption subproblem appears.
- Forbidden: 2/2 do not route here.
- No-load: 1/1 remains general.

This baseline records expected routing. Actual cross-model routing remains advisory until exercised by a fresh skill-loader/model harness.
