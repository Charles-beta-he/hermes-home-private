# Requirements-to-Design-to-Runtime Self-Circulation

Scope/applicability note: this is a class-level workflow-control pattern for projects that have requirements documents, external design artifacts, implemented UI/runtime, and local verification commands. Anti-condition: do not copy any concrete project IDs, URLs, file paths, screen names, or credentials into this reference; those belong in project-scoped config/profile records.

## Applicability

- User asks to make a design/product workflow self-advancing or self-circulating.
- A design artifact is intended to govern an implemented product, not just serve as a mockup.
- Missing requirements/UI/test coverage should be discovered automatically and converted into a safe next action.
- The project has local code/tests where deterministic gates can run.

## Anti-conditions

- Do not auto-write external design tools during a normal verification gate.
- Do not auto-change runtime behavior, route activation, upload/privacy policy, permissions, deploy, push, or publish from a self-circulation pass.
- Do not treat generated design copy as proof of runtime capability.
- Do not store one project’s design IDs, URLs, screen names, or file paths in global memory/skill root; keep them in project config/docs or scoped project records.

## Pattern

1. Establish canonical source layers:
   - Requirements/product contract: intent, scope, user flows, selector/data-field/API contracts, acceptance gates, known out-of-scope items.
   - Design SSOT: named external design target plus local non-secret screenshot/artifact evidence.
   - Runtime mapping: implemented selectors, data fields, UI blocks, controller/API contracts, semantic boundaries.
   - Automation: read-only design gate, visual-structure gate, interaction smoke, full verification.

2. Add a read-only workflow gate:
   - Check required requirements sections and contract terms.
   - Check design target identifiers/artifacts are present/configured.
   - Check runtime selectors/data fields still exist.
   - Check tests/gates cover visual blocks and real interactions.
   - Check boundary language is present: design is not runtime proof, external design gates are read-only, future-only UI is labeled, privacy/upload constraints remain explicit.

3. Add proposal mode:
   - When the gate fails, write a local proposal packet under an ignored state/proposals directory.
   - Classify each missing item by owner: requirements backlog, runtime implementation, design SSOT, automation, or manual review.
   - Mark whether each item is safe to apply automatically.

4. Add safe-apply mode:
   - Only auto-apply low-risk local requirements backlog/checklist notes.
   - Never mutate external design tools.
   - Never change implemented UI behavior, routes, upload/audio policy, permissions, deployment, or publish state.
   - Re-run the gate after apply.

5. Verify in two ways:
   - Current healthy project: gate/propose/apply-safe should pass, produce no-op proposal, and full verify/smoke should pass.
   - Broken temporary fixture: deliberately remove a requirements contract mention or similar low-risk item; assert proposal generation and safe backlog append work without touching runtime/design files.

6. Close out:
   - Clean transient test-results/screenshots/proposals or ensure proposals live under ignored state.
   - Commit only scoped local changes if project policy allows.
   - Report remaining authority gates separately (external design writes, runtime behavior changes, route activation, push/deploy/publish).

## Minimal command surface

```bash
make workflow-gate        # detect: read-only coherence gate
make workflow-propose     # propose: local intervention packet
make workflow-apply-safe  # safe local requirements backlog/checklist append only
make verify
make ui-smoke
```

## Pitfalls

- **Detector-only plateau**: A fail-closed gate is useful but not self-circulation. Add a proposal packet so the next step is explicit and machine-readable.
- **Unsafe auto-fix expansion**: Safe apply should be deliberately boring: requirements backlog/checklist notes only. Runtime and external-design changes require a normal implementation/design slice.
- **Green-path untested proposal code**: If the real project is healthy, proposal mode may be no-op. Also test a broken temp fixture to prove proposal and safe-apply paths actually work.
- **Hidden transient artifacts**: Proposal files, browser screenshots, and local design evidence can clutter commits. Put proposals under ignored state and clean test outputs before commit.
