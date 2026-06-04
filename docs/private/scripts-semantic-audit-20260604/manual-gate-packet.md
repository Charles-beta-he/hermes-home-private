# Scripts local-control-plane semantic audit — 2026-06-04

Scope: read-only semantic clustering of `scripts/local-control-plane` bucket from dirty inventory. No script source files were modified, staged, deleted, restored, or committed.

## Summary

- total scripts bucket entries: 239
- status counts: {' M': 38, '??': 201}
- family counts: {'other-scripts': 108, 'multimodel': 18, 'dashboard-observability': 17, 'cron-runtime': 6, 'taskpool': 41, 'utilities': 6, 'tests': 29, 'provider-routing': 5, 'evolution-dreaming': 9}
- tracked diff complexity: {'small_delta': 9, 'no_text_delta': 8, 'large_delta': 8, 'medium_delta': 13}

## Candidate batch order

1. `tests` — count 29 — gate `low_risk_test_artifact_review`
   - Review coherent family; do not mix unrelated script clusters in one commit.
2. `utilities` — count 6 — gate `scripted_with_review`
   - Review coherent family; do not mix unrelated script clusters in one commit.
3. `dashboard-observability` — count 17 — gate `scripted_with_review`
   - Review coherent family; do not mix unrelated script clusters in one commit.
4. `provider-routing` — count 5 — gate `manual_high_context_review`
   - Review coherent family; do not mix unrelated script clusters in one commit.
5. `cron-runtime` — count 6 — gate `manual_semantic_review`
   - Review coherent family; do not mix unrelated script clusters in one commit.
6. `evolution-dreaming` — count 9 — gate `manual_high_context_review`
   - Review coherent family; do not mix unrelated script clusters in one commit.
7. `multimodel` — count 18 — gate `manual_high_context_review`
   - Review coherent family; do not mix unrelated script clusters in one commit.
8. `taskpool` — count 41 — gate `manual_high_context_review`
   - Review coherent family; do not mix unrelated script clusters in one commit.
9. `other-scripts` — count 108 — gate `manual_semantic_review`
   - Review coherent family; do not mix unrelated script clusters in one commit.

## Manual intervention boundary

The next side-effect would be staging or editing script source. That requires explicit selection of one candidate batch and acceptance criteria for that family. Do not bulk commit all scripts together.

Recommended next safe step: start with `tests` or `utilities` if the goal is low-risk cleanup; start with `taskpool` only if the goal is control-plane correctness and the user accepts high-context review.
