# Manufacturing Multi-Model Chain Policy

Extracted from `/Users/charles/.hermes/skills/smart-home/manufacturing-brain/SKILL.md` on 2026-07-01T08:54:33.968451+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Multi-model chain policy

For end-to-end photo/vision-to-print or any high-risk print decision, run multi-model synthesis and keep three ledgers separate: evidence, dissent, and engineering verification. Current reference artifact:

`~/.hermes/brains/manufacturing/reviews/2026-05-21_x2d-photo-to-print-multimodel-review.md`

Canonical chain:
- Intake Brain: structured intent only; no model selection or physical action.
- Vision & Measurement Brain: object confidence, ambiguity, trusted dimension source, uncertainty.
- Retrieval / Similarity Brain: near-identical search and similarity class before generation.
- Manufacturing Brain: material/printability/slicer/quality/load-path proposal.
- Safety / Policy Brain: independent veto; conservative disagreement wins.
- External Control Brain: only layer that can execute physical action after fresh telemetry, idempotency, packet hash, runtime credential, and confirmation token.
- Human Confirmation Orchestrator: final confirmation must bind model hash, slice hash, device id, material/profile, risk tier, and real-action flag.

Implemented quantitative gates:
- `model_candidate_search.py plan --object-confidence N`: object_class_confidence must be >=0.85 before normal retrieval; otherwise fail closed and ask clarification.
- `model_candidate_search.py plan --printer "Bambu X2D" --device-status-json status.json --material MATERIAL --require-loaded-material`: matches the owned Bambu X2D profile, reads AMS/spool material types from read-only status, and can fail closed when the requested material is not loaded.
- `model_candidate_search.py evaluate --required-material MATERIAL --available-material PLA --available-material PETG`: blocks candidates whose required material/profile is not currently available or operator-approved for loading.
- `model_candidate_search.py evaluate --similarity-class exact_replacement --trusted-dimension-source ... --dimension-uncertainty-pct ...`: exact replacement requires a trusted dimension source and <=2% uncertainty/deviation.
- `model_candidate_search.py evaluate --key-dimension-deviation-mm ... --key-dimension-deviation-pct ...`: functional mating dimensions block if >0.5mm or >2% when supplied.
- `manufacturing_preflight.py model --material ... --nozzle-diameter ... --layer-height ... --nozzle-temp ... --bed-temp ... --use-environment-temp-c ...`: material/profile hard bounds block unsafe temperature/layer/environment combinations.
- `external_control_gate.py execute`: real-action telemetry target age <=5s, and optional assumptions must match device/material/nozzle/plate/AMS telemetry.
- `external_control_gate.py execute`: packet-bound confirmation rejects dry-run/final packet hash mismatch.
- `manufacturing_trick_research.py record-success`: first verified successes go to casebook; skill promotion requires 3 matching verified local successes, not one web claim.
