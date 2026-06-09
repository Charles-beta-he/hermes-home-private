# Agent runtime proposal and certification ratchet

Use after an agent/control-plane architecture has already opened these boundaries: ledger-only runtime start, governed builtin read-only completion, external agent version probe, no-tool/no-write prompt dry-run, and readonly context artifact packet.

## Boundary 1: external proposal artifact intake

Purpose: let an external worker output become a review proposal, not a fact.

Requirements:
- Require a previously `started` runtime run.
- Require proposal artifact as `file://...` plus SHA-256; recompute and reject mismatches.
- Artifact must decode to a JSON object.
- Proposal must bind to the current `run_id`.
- Accept only `proposal_type="worker_review_proposal"`.
- Require non-empty `summary`, `failure_classification`, `evidence_refs`, and `claims`.
- Require each claim to carry `evidence_refs`.
- Require `lifecycle_target="review_proposed"`.
- Reject authority-smuggling keys in the request or artifact context: `task_status`, `lifecycle_status`, `mark_done`, external writes, memory/skill writes, provider config changes, outbound messages.
- Append only pointer/hash/summary/counts to the hot ledger.
- Preserve flags: `allowed_to_mutate_lifecycle=false`, `allowed_to_mark_done=false`, `external_adapter_write_through_enabled=false`, `persistent_learning_write_enabled=false`.

Tests:
- Happy path records `external_proposal_recorded` and exactly one new ledger row.
- Reject `done`, missing claim evidence, bad SHA, missing started run, non-JSON object, and CLI smoke.

## Boundary 2: multi-model certification promotion packet

Purpose: promote a recorded proposal to certified-for-review, still not done.

Requirements:
- Require a previously `started` run and an `external_proposal_recorded` row.
- Require certification artifact as `file://...` plus SHA-256; recompute and reject mismatches.
- Artifact must decode to a JSON object.
- Accept only `certification_type="multi_model_proposal_certification"`.
- Certification must bind to the recorded proposal artifact URI and SHA-256.
- Require at least two reviewers, `quorum >= 2`, `quorum <= reviewer_count`, and `truth_gate=true`.
- Require each reviewer to carry `evidence_refs`.
- Require non-empty claims and claim-level `evidence_refs`.
- Require non-empty `summary` and top-level `evidence_refs`.
- Allow only `lifecycle_target="certification_passed_for_review"`.
- Append only pointer/hash/summary/reviewer_count/quorum/truth_gate/claim_count to the hot ledger.
- Preserve flags: `allowed_to_mark_done=false`, `allowed_to_mutate_lifecycle=false`, `model_consensus_is_fact=false`, `external_adapter_write_through_enabled=false`.

Tests:
- Happy path records `certification_recorded` after start + proposal.
- Reject weak quorum, missing truth gate, reviewer without evidence, claim without evidence, proposal mismatch, done/lifecycle authority smuggling, and CLI smoke.

## Next unopened boundary

After certification promotion, stop before the human/elevated policy done authorization projection. Do not combine certification with lifecycle mutation, external adapter write-through, external tools, workspace edits, shell execution, rollback/reopen, or automatic done.
