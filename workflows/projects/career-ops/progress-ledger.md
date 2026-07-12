# Progress Ledger — career-ops

Created: 2026-07-06T17:33:11.521568+00:00

## Current truth

- Portfolio metadata seed created to reconcile registry/profile/SSOT paths.
- Status is evidence-gated; do not promote beyond the status recorded in the project profile without current proof/readback.

## 2026-07-08 Product MVP landing

Status: `local_product_mvp_certified`

Local product root: `/Users/charles/.hermes/career-ops/product`

Implemented surfaces:

- `career_ops_cli.py init` — creates/verifies local workspace directories and profile template.
- `career_ops_cli.py import-jd` — imports local JD text into `jds/`; URL reading stays disabled unless `--allow-url-read` is explicit.
- `career_ops_cli.py evaluate` — deterministic local JD/CV/profile scoring, markdown+JSON report generation, optional tracker append.
- `career_ops_cli.py rank` — ranks local JD markdown files against supplied CV/profile.
- Product README, fixtures, and unit tests under `/Users/charles/.hermes/career-ops/product`.

Evidence:

- `command: cd /Users/charles/.hermes/career-ops/product && python3 -m py_compile career_ops_cli.py` → PASS.
- `command: python3 -m unittest discover -s tests -v` → 4 tests, OK.
- `command: python3 career_ops_cli.py init && import-jd && evaluate --update-tracker` → PASS; sample report `/Users/charles/.hermes/career-ops/reports/20260708-201153-Example-Fintech-Labs-evaluation.md`; score 74 / `good_fit`; side effects limited to `local_report_write` and `tracker_append`.
- `command: python3 /Users/charles/.hermes/scripts/career_ops_privacy_check.py` → PASS; `private_sentinel_hits_in_skill=[]`, `problems=[]`.
- `artifact: /Users/charles/.hermes/career-ops/artifacts/career_ops_product_multimodel_state_v2.json`.
- `artifact: /Users/charles/.hermes/tick-20260708-121719-141871-p2693-ae6aa0d0-a5a0f6d7/final/certification_manifest.json`.
- Multi-model gate: `claude-opus-4-8` + `mimo-v2.5-pro`, T1 quorum 2/2, discussion `certified`, truth `grounded`, evidence coverage 1.0, `can_claim_complete_certification=true` for the local MVP scope.

Hard boundaries still closed:

- No auto-apply.
- No recruiter/employer contact.
- No credentialed scraping.
- No production/external dispatch.
- No claim that LinkedIn/public global sourcing is reliable; current product supports local JD import/evaluation/ranking and explicit opt-in URL reads only.
