# Continuation closure after tool-budget or async-review interruption

## Applicability

Use when a user requested continuous local advancement or full closeout, but a turn stopped because of tool-iteration limits, context compression, an async verifier, or a required evidence readback.

## Anti-conditions

- Do not bypass credentials, external writes, production changes, publish/push, destructive operations, or missing-source truth boundaries.
- Do not force `done` merely to remove the last active task.
- Do not broaden a scoped PASS into whole-system certification.

## Resume protocol

1. Treat the interruption as an execution boundary, not a completion criterion.
2. Re-read canonical task state, lifecycle status, changed files, latest tests, and verifier vote; do not trust the prior summary as fresh proof.
3. Reconstruct a compact Converge Matrix: each material claim maps to current code/test/readback; negative requirements need negative evidence.
4. While an independent verifier runs, continue other safe, independent slices. Do not idle or publish a closure summary solely because review is pending.
5. Classify every remaining item as one of:
   - executable now — implement/test/read back;
   - evidence debt — repair or explicitly inventory;
   - missing external input/authority — terminalize honestly as blocked/expired where lifecycle semantics permit;
   - out-of-scope neighboring claim — name the boundary without upgrading it.
6. For missing source artifacts, distinguish runtime capability from task-specific completion. A healthy pipeline never proves that an absent historical input was processed.
7. Before closure, rerun official validators, focused/full relevant suites, proof/selfcheck, derived projections, and exact lifecycle readback.
8. Accept PASS only from a verifier that inspected the latest bytes/evidence. On AMEND, re-enter the loop; on NO_VERDICT, fill the evidence gap.

## Historical proof-debt rule

A proof checker may PASS active lifecycle gates while warning about terminal-only legacy proof formats. Count and classify those warnings explicitly. Do not rewrite old proof hashes merely to produce a clean dashboard; migrate them only under a dedicated evidence-preserving contract.

## Verification checklist

- [ ] No active task was silently omitted.
- [ ] Missing-input tasks are not marked done.
- [ ] Current-task proof warnings are zero or explicitly blocking.
- [ ] Historical terminal warnings are counted and scoped.
- [ ] Derived dashboards/inventories reflect the latest lifecycle state.
- [ ] Async review/tool-budget interruption is not described as natural closure.
