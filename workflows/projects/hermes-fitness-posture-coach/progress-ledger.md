# Progress Ledger — Hermes Fitness Posture Coach

Updated: 2026-07-03T12:30:38+08:00

## Current truth

- Project/profile/SSOT created for self-use `fitness_posture` capability.
- External source absorbed as metadata seed only: `hasaneyldrm/exercises-dataset`.
- Runtime posture analysis has a first deterministic low-risk bodyweight squat phase/rule pilot; pose adapter spike remains fail-closed on deterministic frame and no coaching-quality claim is made yet.
- Commercial/media reuse is closed.

## Components

| Component | State | Evidence |
|---|---|---|
| Project profile | created | `/Users/charles/.hermes/project-profiles/hermes-fitness-posture-coach.json` |
| SSOT | created | `00-model/fitness-posture-coach-ssot.md` |
| Contract | created | `01-contract/fitness-posture-interaction-contract.md` |
| Roadmap | created | `02-roadmap/self-use-landing-roadmap.md` |
| Source evidence | created | `03-evidence/source-evidence-index.json` |
| Exercise seed | built | `/Users/charles/.hermes/workflows/projects/hermes-fitness-posture-coach/04-implementation/data/derived/exercise_seed_report.md` |
| Pose adapter spike | smoke receipt written; fail-closed no-pose result on deterministic frame | `/Users/charles/.hermes/workflows/projects/hermes-fitness-posture-coach/04-implementation/data/derived/pose_adapter_spike_receipt.json` |
| Squat pilot contract | deterministic phase/rule replay + safety stop tests | `/Users/charles/.hermes/workflows/projects/hermes-fitness-posture-coach/04-implementation/data/derived/squat_pilot_replay_receipt.json` |
| Local review UI | static self-use review surface, camera-default-off | `/Users/charles/.hermes/workflows/projects/hermes-fitness-posture-coach/04-implementation/ui/review.html` |

## Open gates

1. Add a real human-frame/self-use capture smoke before claiming posture/coaching quality; deterministic frame only proves adapter execution and no-stub fail-closed behavior.
2. Add at least one real low-risk movement pilot before claiming coaching.
3. Keep raw camera/video privacy local-first.
4. Re-check ExerciseDB/data terms before any non-self-use path.

## Taskpool intake

Created governed implementation cards:

1. `2026-07-03-fitness-posture-p1-local-pose-adapter-spike-with-no-stub-receipt` — local pose adapter spike.
2. `2026-07-03-fitness-posture-p1-low-risk-squat-pilot-phase-rule-contract` — squat pilot phase/rule contract.
3. `2026-07-03-fitness-posture-p2-local-self-use-review-ui-for-exercise-seed-and-pose-evidence` — local review UI.

Readback boundary: all are `pending`; event hooks OK; autorun did not execute because allowlist/autorun gates remain closed.

## 2026-07-03T12:45+08:00 — P1 squat pilot contract implemented

- Added deterministic low-risk bodyweight squat phase/rule contract.
- Evidence: `04-implementation/scripts/squat_pilot_contract.py`
- Test: `04-implementation/tests/test_squat_pilot_contract.py` => 3 passed.
- Replay receipt: `04-implementation/data/derived/squat_pilot_replay_receipt.json`
- Safety: pain/heavy-load/low-visibility all stop; no diagnosis, no heavy-load coaching, no cloud upload.

## 2026-07-03T12:52+08:00 — P2 local review UI static surface

- Added static local review UI for exercise seed filtering, camera setup checklist, evidence ledger, and posture result display.
- UI: `04-implementation/ui/review.html`
- Test: `04-implementation/tests/test_review_ui_static_contract.py` => 3 passed.
- Readback: `04-implementation/data/derived/review_ui_static_readback.json`
- Safety: camera/mic default off; no media capture API call in this slice.
