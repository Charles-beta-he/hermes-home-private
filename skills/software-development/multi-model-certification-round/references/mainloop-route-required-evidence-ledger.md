# Mainloop route-required evidence ledger

Use this when certifying Hermes mainloop completion/T3 claims with the model capability router and evidence gate.

## Problem this prevents

A certification packet can have `truth_gate.can_certify_truth=true` and `evidence_coverage=1.0` for claim-to-evidence linkage while still missing evidence classes required by the selected verification route. That can create a false acceptance: the claim is grounded, but the route contract was not fully satisfied.

Example: `hermes_self_modification` may require `focused_pytest`, `py_compile`, `post_update_check`, `config_readback`, and `git_status`. If only tests/compile/post-update are present, the claim may look grounded while the route is still missing config/git-status readback.

## Required pattern

For each chunk/claim:

1. Route by verification surfaces first, not only by task complexity.
2. Capture the route output as evidence, including `required_evidence`.
3. Attach normalized evidence classes to each evidence item, e.g.:
   - `focused_pytest`
   - `test_output`
   - `py_compile`
   - `post_update_check`
   - `git_diff`
   - `git_status`
   - `config_readback`
   - `build_output`
   - `runtime_smoke`
4. Compute and persist a route ledger:

```json
{
  "required": ["focused_pytest", "py_compile", "post_update_check", "config_readback", "git_status"],
  "present": ["focused_pytest", "py_compile", "post_update_check", "config_readback", "git_status"],
  "missing": [],
  "coverage": 1.0
}
```

5. For T3/blocking tiers, any non-empty `missing` list must prevent `certified` even if claim-level truth coverage is 1.0. Report a failure like `route_required_evidence_missing:<classes>`.
6. Re-run the affected chunk after adding missing evidence; do not close from the previous claim-level truth gate alone.

## consult_models evidence-link pitfall

When using `consult_models.py state --claim`, the evidence bundle may normalize the single claim id to `C-001` internally even if the claim text contains a chunk id such as `C2-mainloop-integration`. Evidence items must support the normalized claim id consumed by the truth gate. If evidence supports the chunk label instead, the bundle can degrade to `evidence_coverage=0.0` / unsupported despite valid raw evidence.

Safe approach for single-claim chunks:

- Put the chunk id in the claim text.
- Use `supports: ["C-001"]` in each `--evidence-json` item, or inspect the generated state/bundle and match the normalized claim id before running the round.

## Background/async self-check pitfall

For multi-chunk self-checks, do not run all chunks in one long opaque background process unless each chunk writes a result file immediately after it finishes. A killed background batch can lose partial progress and hide which chunk failed. Prefer per-chunk foreground runs or a resumable manifest with per-chunk output files and artifact paths.

## Acceptance checklist

- [ ] Surface route captured and linked as evidence.
- [ ] Each evidence item has either `evidence_class` or `evidence_classes`.
- [ ] Route ledger has required/present/missing/coverage.
- [ ] T3 `missing != []` downgrades or blocks certification.
- [ ] Claim-level truth gate and route-required evidence ledger are both green.
- [ ] Any model `verifier_gap` asking for config/git-status/ledger readback is answered with linked evidence and a recheck.
