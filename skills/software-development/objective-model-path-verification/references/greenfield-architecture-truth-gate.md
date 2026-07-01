# Greenfield Architecture Truth Gate

Use this reference when the user approves a new production-grade architecture direction and asks to `立项` / `全盘推进`, but no implementation artifacts exist yet.

## Problem pattern

Multi-model or certification gates may mark core design claims as `unsupported` even when the user has approved them. This is usually correct: the claims are requirements or architecture intent, not implementation facts. Do not treat this as a rejection of the direction, and do not bypass the gate by declaring production readiness from model agreement.

## Correct landing sequence

1. **Separate requirement truth from implementation truth**
   - Requirement/design claims may be grounded by user-approved intent and SSOT text.
   - Production/runtime claims require executable evidence: schema, code, tests, DB/API/UI readback, rollback proof.

2. **Land P0 artifacts first**
   - Project profile or scoped SSOT.
   - Objective model and architecture SSOT.
   - Multimodel prompt/state and review packet.
   - Progress ledger.
   - Taskpool candidate/slice if concrete engineering work remains.

3. **Interpret `not_certified` precisely**
   - `not_certified` because there is no schema/writer/reader/test evidence means: safe to proceed with contract/test-design/additive schema planning.
   - It does **not** authorize default-on runtime mutation.
   - It also does **not** mean the architecture direction is invalid.

4. **Define the first executable evidence surface**
   - Exact files/functions to modify.
   - Feature flag default-off or shadow mode.
   - Additive migration/rollback plan.
   - Focused tests for compatibility and new invariants.
   - Readback/rebuild proof.

5. **Only then rerun certification**
   - Convert design claims into claim-linked implementation evidence paths.
   - Certification should cite code/tests/DB readback, not just model discussion or user-approved design text.

## Anti-conditions

Do not use this reference to delay simple work, to avoid implementing an already-scoped safe slice, or to convert a real blocker into a vague planning document. If a reversible implementation/test slice exists and does not cross a hard gate, continue to land it.

## Reporting wording

Prefer:

> Direction accepted; production certification is not yet claimed because the claims are still design requirements. I landed SSOT/contract artifacts and the next safe slice is additive schema + shadow writer + tests.

Avoid:

> Multi-model rejected the plan.

unless the models actually rejected the architecture rather than the evidence/certification status.
