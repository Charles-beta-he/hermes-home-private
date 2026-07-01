# Smart routing coverage audit

Use this reference when a user asks whether an agent/workflow system's "smart routing" covers current conversations, existing project progression, taskpool execution, or multi-model verification.

## Landing-zone classification

This is a reusable audit/debugging procedure, not a project-progress record. Store project-specific config paths, model names, branches, or runtime findings in the relevant project profile or report. Keep this reference focused on the coverage model and verification checklist.

## Core distinction

Do not collapse all routing into one claim. Separate these layers:

1. Conversation main model
   - The active chat model may still answer ordinary turns directly.
   - A smart router being enabled does not prove every response is dynamically model-selected or multi-model.

2. Pre-turn intent/workflow router
   - Classifies the request, detects control-plane/workflow lanes, and may decide whether to load skills, project profiles, taskpool, verification, or specialist flows.
   - This is routing into a workflow, not necessarily fan-out execution.

3. Task classification and tier routing
   - Maps work into low/medium/high-risk tiers using explicit flags, keywords, project rules, file count, domain risk, or acceptance criteria.
   - Typical examples: quick/T0, ordinary implementation/T1, production/security/migration/payment/T2, architecture/system-design/T3.

4. Multi-model execution/verification
   - Applies only when the route/tier/explicit instruction requires it.
   - Distinguish producer, reviewer, arbiter, scout/triage, and verifier roles.
   - Do not imply simple reads, logs, tests, screenshots, or deterministic fixes are multi-model unless a multi-model step actually ran.

5. Taskpool/event-hook smart routing
   - Event hooks should decide whether to skip or invoke expensive model steps using deterministic task signals.
   - If invoked from an event, route to the triggering task id rather than selecting a global task.

6. Project-profile / SSOT routing for existing projects
   - Existing project progression should first resolve the project profile, SSOT, red lines, acceptance gates, and current evidence.
   - Only then choose direct execution, taskpool, delegation, cron/mission, browser/UI verification, or multi-model certification.

## Existing project progression default answer

When the user asks whether an existing project will use smart/multi-model routing, answer with this shape:

- Yes: project progression should enter project-profile/SSOT workflow routing instead of raw chat.
- Conditional: multi-model routing is used when risk, complexity, project rules, explicit flags, or taskpool metadata require T2/T3/certification.
- No overclaim: ordinary deterministic steps still run on the current main model plus tools.
- Evidence: cite the actual config/probe/test/log output if claiming a route is enabled.

## Verification checklist

Before claiming smart routing coverage, verify at least the relevant subset:

- [ ] Config shows the router/tier/taskpool hook is enabled.
- [ ] Candidate model/provider availability is checked or explicitly out of scope.
- [ ] Role/tier mapping is visible: producer/reviewer/arbiter/triage/verifier.
- [ ] Existing-project route resolves a project profile/SSOT before execution.
- [ ] Taskpool route distinguishes advisory/light tasks from P0/P1/P2/evolution/certification tasks.
- [ ] A focused test, compile check, probe, selfcheck, or log readback backs the claim.
- [ ] The response distinguishes architecture/spec coverage from runtime execution coverage.

## Common pitfalls

1. Saying "smart routing is enabled" when only the model candidate list exists.
2. Saying "this conversation uses multi-model" when only the main model answered.
3. Treating intent classification as multi-model verification.
4. Treating skill/workflow coverage as proof of taskpool/runtime integration.
5. Skipping project profile/SSOT resolution for existing-project progression.
6. Fan-outing every small project step; this increases latency/cost and can add noise without improving correctness.
