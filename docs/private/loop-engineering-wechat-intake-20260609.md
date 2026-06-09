# Loop Engineering WeChat intake — InfoQ 2026-06-09

Source: https://mp.weixin.qq.com/s/JKrDuM4jaspm2wL-vJ1qsA
Title: 大人，AI编程又变天了！Claude Code之父、龙虾创始人同时力捧新范式，杀死提示词工程？
Publisher/author visible in page: InfoQ / 褚杏娟
Captured: 2026-06-09

## Extracted signals

- Boris Cherny and Peter Steinberger are presented as public signals for a shift from manual prompting to designing loops that prompt, schedule, judge, and continue agent work.
- The valuable concept is not mechanical repetition or cron-only automation; the article repeatedly frames useful loops as feedback systems with goals, context, tools, audit logs, stop conditions, rollback, and human handoff.
- Claude Code examples include persistent Loops/Routines, scheduled tasks, retained session context/tool permissions/MCP connections, and example workflows such as checking PR build status, reading logs, fixing failures, and pushing commits.
- The article highlights cost and context-bloat risks: every iteration can be a full model call; high-frequency loops can quickly create hundreds of calls; community users do not have unlimited token budgets.
- It also surfaces governance risks: loops can amplify errors, create shadow automation, bloat systems, and self-confirm without tests/type checks/real-error feedback.

## Hermes interpretation

This is a strong external direction signal for Hermes taskpool/control-plane evolution, but not a direct implementation spec and not official evidence for Claude/Codex product behavior beyond the article's report. The reusable engineering value is:

1. Convert loop hype into governed agent-loop architecture: objective -> context -> tools -> action -> feedback -> stop/rollback/human handoff.
2. Prefer event-governed taskpool loops over naive cron polling.
3. Add loop budget controls: context-growth cap, iteration budget, cost estimation, dedupe, and no-output/non-convergence stop.
4. Make feedback gates concrete: tests, type checks, real logs/errors, taskpool proof/evidence, regression harness, selfcheck.
5. Preserve persistent loop state without letting memory/prompt bloat become authority.

## Taskpool intake recommendation

Create one P2 evolution task for Hermes/taskpool:

- lane: evolution
- project: hermes-agent
- architecture_target: taskpool
- dependency_order: 0
- multimodel_triage_result: advisory
- parallel_boundary: hermes-loop-engineering-control-plane
- objective: map the Loop Engineering pattern into Hermes event-governed taskpool loops with bounded feedback, cost, stop, rollback, and human handoff gates.
- acceptance evidence: design note + minimal deterministic loop fixture + taskpool dynamic-runner or reliability-harness integration plan + proof that it does not silently enable expensive live autorun.

## Anti-drift

Reject vague "make agents loop forever" tasks. The landing must be a bounded control-plane design and/or fixture: no automatic live gateway/taskpool mutation, no unbounded cron polling, no unlimited token loop, no prompt-only solution.
