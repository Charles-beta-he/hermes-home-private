# Continuation Exit Gate

Scope: global execution discipline for complex/full-landing tasks. Use when the user says any equivalent of `继续推进`, `全盘推进`, `不以阶段/人工接入为中止借口`, `直至方案全部落地`, `不要只给下一步`, or when a task has an explicit backlog/roadmap/SSOT.

## Failure mechanism this gate prevents

A model can complete one safe slice, pass tests, then switch into summary mode and present the next safe slice as a recommendation. That is a premature finalization bug when the user authorized continued safe progress. Passing verification for one slice is not an exit condition; it is a checkpoint.

## Mandatory pre-final question

Before sending a final response, answer from current evidence:

```text
Does a next local/reversible/authority-safe slice still exist?
```

If yes, do not final. Continue execution.

## Exit conditions

Final response is allowed only when at least one is true:

1. All in-scope backlog/roadmap/SSOT items are completed or explicitly classified as local-equivalent.
2. The only remaining items cross a concrete authority boundary:
   - credential/secret entry;
   - external dispatch/send/publish/deploy;
   - lifecycle mutation or scheduler/worker enablement;
   - payment/legal/signature/wallet/device physical effect;
   - destructive file/data operation;
   - production target without rollback/readback authority;
   - missing required evidence or artifact after attempted retrieval.
3. The user narrowed the task, stopped, or asked for a report only.
4. Tooling/environment is blocked and alternatives were attempted or would cross a boundary.

A roadmap phase, passing test/build/doctor, a background validation process ending, or a generic label like `human intervention` is not an exit condition by itself.

## Loop algorithm

1. Read current state: backlog/roadmap/SSOT/taskpool/git status/doctor as applicable.
2. Partition remaining work into:
   - `safe_next`: local, reversible, read-only or well-scoped implementation with existing authority;
   - `needs_authority`: concrete external/secret/destructive/production boundary;
   - `invalid_or_duplicate`: already completed, obsolete, or superseded.
3. If `safe_next` is non-empty, choose the smallest valuable slice and execute it now.
4. Verify with real evidence: tests/build/API/UI/browser/doctor/readback.
5. Commit or otherwise persist scoped artifacts if the task convention requires it.
6. Update SSOT/backlog/ledger with exact evidence.
7. Repeat from step 1.
8. Final only after `safe_next` is empty.

## Final response requirements

When finalizing a full-landing task, include:

- completed count/status readback;
- remaining items and why each is a real boundary, not a phase label;
- verification evidence;
- side-effect boundary status;
- if work stopped because of a boundary, the exact missing authority/evidence needed.

## Anti-conditions

Do not use this gate to justify unsafe escalation. Broad user trust does not authorize credentials, payments, external sends, destructive operations, production deploys, lifecycle execution, or physical device effects without exact scope and rollback/readback authority.

Do not loop mechanically on meaningless changes. If the next slice is cosmetic/no-value or would only create churn, classify it as out of scope or ask only if it changes acceptance.
