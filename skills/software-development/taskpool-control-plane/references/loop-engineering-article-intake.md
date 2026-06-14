# Loop Engineering / AI-trend article intake for taskpool

Use this when the user shares a WeChat/InfoQ/blog/social article about agent loops, autonomous coding agents, Claude Code/Codex automation, or "prompt engineering is dead" style claims and asks to analyze, absorb, or add it to the taskpool.

## Class-level interpretation

Treat the article as an external direction signal, not an implementation spec or official product fact. The durable value is usually the control-plane pattern underneath the hype:

- objective/OKR definition before looping;
- feedback gates that can say no: tests, type checks, real logs/errors, proof/evidence, regression harness;
- bounded continuation state instead of cold-start cron-only loops;
- audit trail, rollback condition, stop condition, and human handoff;
- cost/context-bloat governance: iteration budget, token/cost estimate, dedupe, non-convergence stop.

## Intake sequence

1. Extract only concrete signals from the page: title/source/date, named products/features, described workflow, feedback/stopping/cost risks.
2. Write a short evidence note under `docs/private/` with:
   - extracted signals;
   - Hermes interpretation;
   - explicit anti-drift boundaries;
   - proposed taskpool metadata.
3. Add one rich P2 `evolution` task unless the user marks it urgent:
   - `project=hermes-agent`
   - `architecture_target=taskpool` for event-governed loops/control-plane work;
   - `multimodel_triage_result=advisory` unless the task will mutate runtime/core;
   - `parallel_boundary` names the architectural class, e.g. `hermes-loop-engineering-control-plane`.
4. Include evidence refs to both the URL and the `docs/private/` note.
5. After `add --json`, inspect the event-hook result separately from creation success. `status: OK` + `created` means intake succeeded even if autorun is disabled or a background advisory job owns the task.

## Good task shape

Objective wording:

> Map the Loop Engineering pattern into Hermes event-governed taskpool loops with bounded feedback, budget controls, stop/rollback conditions, and human handoff gates.

Acceptance evidence:

- source evidence note;
- minimal deterministic loop fixture or reliability-harness/taskpool dynamic-runner integration plan;
- selfcheck/proof evidence;
- explicit proof that the change does not silently enable expensive live autorun.

## Anti-drift

Reject vague tasks like "make agents loop forever" or "replace prompt engineering". The landing must be a bounded control-plane design/fixture with verifiable gates. Do not auto-enable live loops, do not treat social-media claims as authoritative product docs, and do not create prompt-only tasks with no feedback harness.
