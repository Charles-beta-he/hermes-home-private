# Mission budget continuation after verified closeout

Use when a governed Hermes Mission has reached its tick budget, has no open human decision, and the user authorizes bounded continuation after evidence review.

## Pattern

1. Close the current slice first.
   - Review the current repo diff and ensure it maps to the active mission objective.
   - Run focused deterministic checks.
   - Use an independent reviewer when code touched runtime/control-plane surfaces.
   - Commit only scoped files; read back a clean worktree.

2. Ask models for a bounded continuation recommendation, not blanket permission.
   - Provide evidenced facts: mission id, status, open decisions, ticks used/max, cron status, latest stage report, commit hash, verification output, repo cleanliness, pending/stale signals.
   - Ask for JSON with: continue, recommended_additional_ticks, max_total_ticks_after_authorization, must_do_next, risks, authorization_boundary.
   - Treat formal discussion `not_certified` as a gate signal, but do not discard useful fanout evidence: if all planners recommend continue and only tick count differs, choose the bounded median/majority value and record the certification caveat.

3. Authorize only the narrow budget delta.
   - Update the canonical mission budget ledger from old max to new max; append an explicit budget_authorized event with the user authorization text, model recommendations, selected tick count, and boundary.
   - Keep cadence unchanged unless the user/model evidence specifically justifies cadence change.
   - Boundary text must explicitly preserve: no push/deploy/secrets/delete/external delivery/payment/production change; value/permission/irreversible/evidence gaps still require handoff.

4. Record a stage report immediately after authorization.
   - Evidence: closeout commit, verification commands/results, model tick artifact, selected tick count.
   - Risks: certification caveats and remaining operational backlog.
   - Next step: the first bounded slice the resumed mission must perform.

5. Wake and verify the executor.
   - If event signals are pending and user authorized continuation, run the governed mission dispatch path rather than waiting blindly for cadence.
   - Read back board/doctor/cron state: ticks should move from maxed to remaining headroom, cron should still be active, and next step should be concrete.
   - If dispatch consumes a new tick and makes another commit/stage_report, include that in the final status.

## Tick sizing heuristic

For a mission that has produced verified value and is only blocked by budget:

- +2: only enough for a closeout/report; use when evidence is weak or risk is high.
- +4: one short diagnostic + report; may truncate implementation.
- +6: default bounded continuation for one governance arc: diagnose backlog, advance stage, implement/verify/report.
- +8: use when one additional implementation slice is clearly needed after diagnosis.
- +12 or more: usually over-authorization; require stronger evidence or explicit user direction.

Prefer median/majority across model recommendations, capped to the smallest value that can complete the next governance arc.

## Pitfalls

- Do not let a clean model recommendation substitute for closing the current diff first.
- Do not convert `not_certified` into a silent PASS; record it as a risk/caveat and lower the authorization size if needed.
- Do not change cadence just because signals are stale; stale signals usually indicate consumption/drain mechanics, not cadence frequency.
- Do not wake recursive/unguarded cron loops. Use the governed dispatch command and then read back doctor/board.
- Do not call the mission “healthy” if stale signal backlog remains; report it as the next bounded slice even if budget authorization succeeded.
