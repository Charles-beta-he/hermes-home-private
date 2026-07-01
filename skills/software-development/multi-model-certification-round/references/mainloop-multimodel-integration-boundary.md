# Main conversation-loop multi-model integration boundary

Use when evaluating or designing multi-model routing/certification inside a live agent conversation loop, especially after a single-model false-acceptance incident.

## Core boundary

Do not recommend or certify "run every normal chat turn through parallel multi-model voting" as the stable default. The durable architecture is layered:

1. **Intent/risk router** before the main model call decides T0/T1/T2/T3.
2. **Main executor** remains the low-latency single-model path for ordinary chat.
3. **Evidence spine** records tool/file/API/browser/test outputs with claim links.
4. **Completion-claim gate** checks high-risk final claims (`done`, `verified`, `production-ready`, `no residual process`, `uIMax/A+ accepted`, `multi-model certified`) against fresh evidence.
5. **Multi-model advisory/certification** is invoked only for high-risk turns, lifecycle closeout, Hermes self-modification, production/external side effects, architecture decisions, or explicit user escalation.
6. **Response policy** must downgrade wording when evidence, quorum, or truth gates fail.

## Certification semantics

- Router/bootstrap calls are control-plane calls and must not count as participant model votes.
- Model agreement is advisory until claim-linked evidence passes the truth gate.
- If planner fan-out is below `min_quorum`, the result is `degraded_not_certified` even when the successful models agree.
- A `truth_status=no_claims` or empty evidence bundle is not proof of implementation correctness; it only says there were no factual claims to certify.
- For main-loop work, separate these statuses in the report:
  - router readiness
  - provider availability
  - fan-out quorum
  - truth/evidence status
  - lifecycle/closeout status

## Stable rollout pattern

1. Fix model identity drift first (profile/quorum/status must name the same canonical models).
2. Add a default-off or advisory-only `mainloop_verification` config block.
3. Wire routing trace into the conversation loop without changing output.
4. Add a turn-level evidence spine for tool results and claim links.
5. Add completion-claim gate before adding expensive multi-model calls.
6. Add background durable multi-model certification jobs for T3/high-risk cases.
7. Only then enable selective blocking for high-risk completion claims.

## Recursion and latency guards

- Never call `consult_models` recursively from a consult/certification worker or from a turn already marked as verification-active.
- Use a runtime guard such as `HERMES_MAINLOOP_VERIFICATION_ACTIVE=1` or an equivalent in-process flag.
- Bound synchronous verification time; prefer background jobs for full T2/T3 discussion.
- Enforce per-turn and per-session limits on multi-model jobs.

## Reporting pitfall

When the user asks "multi-model thinking" for this class of design, it is acceptable to run a multi-model advisory round, but if it times out, returns provider errors, or falls below quorum, the final answer must explicitly say it is advisory/degraded and not certified. Do not let the quality of the plan text overwrite the certification status.
