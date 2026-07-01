# Autonomous continuation checkpoint slices

Use this reference when an autonomous/self-advance session is implementing a long chain of safe local slices and risks stopping after a checkpoint summary.

## Applicability

- The user has authorized continued local/self-advance work within clear boundaries.
- A slice completes and the agent is about to summarize progress while more safe reversible work remains.
- A background notification, tool-iteration limit, or checkpoint final response could interrupt the active objective.
- Work is being advanced as small verified commits rather than one large change.

## Anti-conditions

- Do not auto-continue across permission, credential, destructive, external publish/deploy, payment, legal/safety, or value-judgment boundaries.
- Do not treat model agreement, a checkpoint summary, or a watch notification as authority to cross a side-effect boundary.
- Do not store session progress as durable memory; progress belongs in the project ledger/SSOT or current task list.

## Procedure

1. Classify checkpoint summaries as continuation points, not terminal completion, when the active objective still has safe local next slices.
2. Before moving to the next slice, close the current slice completely:
   - run targeted verification;
   - run the project-level verification gate when available;
   - update the scoped project ledger/SSOT;
   - make an atomic scoped commit;
   - confirm the working tree is clean.
3. If a turn exhausts tool iterations after verification but before commit, the next continuation should first:
   - inspect working-tree state;
   - record the verification evidence already produced;
   - commit the verified slice;
   - only then start a new slice.
4. Keep every continuation inside the last authorized boundary. If the next useful action would require reconcile/write, lifecycle mutation, external adapter write, notification, deploy/push, credential entry, or broad fan-out, stop with a DecisionPacket and ContinuationPacket.
5. Prefer read-only projection ratchets before write-through:
   - expose live readback as bounded projection metadata;
   - render preview/authority packets locally;
   - prove no canonical fact write or lifecycle mutation occurred;
   - smoke the read-only endpoint and kill temporary smoke processes afterward.

## Verification checklist

- Targeted RED -> GREEN test for each new behavior.
- Full project verification gate when available.
- Rollback/escape-hatch artifact or git revert path recorded.
- Post-action readback for any process/port started during smoke.
- Explicit boundary statement: what was not done (no external write, no dispatch execution, no deploy/push, no credentials).

## Pitfalls

- A polished checkpoint report can accidentally become a final response and stop self-advance. Treat it as a resume gate unless a real boundary was reached.
- Watch/background notifications are telemetry, not task-switch authority. Resume the active objective after handling them unless they expose a blocking failure.
- Do not begin the next feature slice before committing a verified previous slice; otherwise later rollback and evidence become ambiguous.
