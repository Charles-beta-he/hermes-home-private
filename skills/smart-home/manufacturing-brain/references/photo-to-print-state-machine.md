# Photo-to-Print State Machine

Extracted from `/Users/charles/.hermes/skills/smart-home/manufacturing-brain/SKILL.md` on 2026-07-01T08:52:42.874486+00:00 to reduce root SKILL.md load while preserving detailed workflow content. The root skill keeps a progressive-loading pointer to this reference.

## Photo-to-print state machine

If the user has no model yet and wants a safe first X2D pilot package, generate a tiny calibration artifact first:

```bash
python3 ~/.hermes/scripts/manufacturing_calibration_cube.py \
  --output /path/calibration-cube-12mm.stl \
  --manifest /path/calibration-cube-manifest.json \
  --size-mm 12 \
  --json
```

Use the one-command safe runner when the user already has a local model and wants a complete dry-run proof:

```bash
python3 ~/.hermes/scripts/photo_to_print_runner.py dry-run-existing-model \
  --photo /path/input.jpg \
  --object-label "目标物" \
  --intended-use "用途" \
  --model /path/model.stl \
  --device-status-json /path/status.json \
  --output-dir /path/photo-to-print-run \
  --json
```

The runner executes the full safe path: job init, object/model approvals, candidate evidence, preflight, local 3MF export, action packet creation, and external-control dry-run gate. It never uploads or starts the printer.

Use the durable step-by-step CLI for finer-grained control:

```bash
python3 ~/.hermes/scripts/photo_to_print_job.py init --photo /path/input.jpg --object-hint "目标物" --intended-use "用途" --json
python3 ~/.hermes/scripts/photo_to_print_job.py advance <job_id> object_confirmed --object-label "..." --confidence 0.93 --approved-by-human --json
python3 ~/.hermes/scripts/photo_to_print_job.py advance <job_id> model_strategy_selected --strategy retrieval --risk-tier T1 --approved-by-human --json
python3 ~/.hermes/scripts/model_candidate_search.py plan \
  --object-label "目标物" \
  --intended-use "用途" \
  --intake-mode photo \
  --intake-mode voice \
  --intake-mode text \
  --output /path/candidates.json \
  --json
python3 ~/.hermes/scripts/model_candidate_search.py evaluate \
  --object-label "目标物" \
  --candidate-title "候选模型标题" \
  --source Printables \
  --license-status known \
  --provenance-status verified_source_page \
  --format STL \
  --dimensions "20x15x12mm" \
  --preview-evidence thumbnail_and_model_page \
  --similarity-class functional_part \
  --visual-similarity 0.88 \
  --dimension-deviation-pct 4 \
  --json
python3 ~/.hermes/scripts/photo_to_print_job.py advance <job_id> model_ready --model-path /path/model.stl --provenance "..." --license "..." --approved-by-human --json
python3 ~/.hermes/scripts/manufacturing_preflight.py model /path/model.stl --intended-use "用途" --material PLA --output /path/preflight.json --json
python3 ~/.hermes/scripts/photo_to_print_job.py advance <job_id> preflight_passed --preflight-report /path/preflight.json --approved-by-human --json
python3 ~/.hermes/scripts/manufacturing_slice.py prepare /path/model.stl --output /path/job.3mf --report /path/slice-report.json --json
python3 ~/.hermes/scripts/photo_to_print_job.py advance <job_id> slice_ready --slice-path /path/job.3mf --slice-report /path/slice-report.json --approved-by-human --json
python3 ~/.hermes/scripts/photo_to_print_job.py action-request <job_id> --intent start_print --device-status-json /path/status.json --json
python3 ~/.hermes/scripts/external_control_gate.py execute /path/action-packet.json --confirm-token TOKEN --dry-run --json
```

The CLI records state/evidence only. `action-request` creates an external-control packet and audit stub; it never executes printer actions.

Glasses / Rokid trigger policy:
- Confirmations spoken through glasses may trigger the safe runner or enqueue a print intent, but direct physical printing remains blocked until external-control validates a fresh action packet and operator confirmation.
- Photo/vision requests from glasses are treated as evidence intake only; they do not imply model selection, slicing approval, or start_print approval.
- For glasses-side visual QA, create a packet with `python3 ~/.hermes/scripts/manufacturing_visual_qa.py intake --image /path/photo.jpg --question '...' --output /path/packet.json`; use Hermes vision to inspect the photo, then store findings with `manufacturing_visual_qa.py report`. Protocol: `~/.hermes/brains/manufacturing/protocols/glasses-visual-qa.md`.
