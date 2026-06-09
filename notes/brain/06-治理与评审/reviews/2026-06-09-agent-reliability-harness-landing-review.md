---
type: review
layer: L6
status: closed
created: 2026-06-09T21:42:00+08:00
review: agent-reliability-harness-landing
source: hermes_self_optimization
certification: implementation_verified_not_live_enforced
implementation_commit: 628e9104c
parent_commit: e0237a1
evidence_refs:
  - /Users/charles/.hermes/docs/private/agent-eval-dynamic-workflow-longterm-20260609.md
  - /Users/charles/.hermes/docs/private/agent-eval-harness-full-landing-20260609.md
  - /Users/charles/.hermes/hermes-agent/agent/reliability_harness.py
  - /Users/charles/.hermes/hermes-agent/tests/agent/test_reliability_harness.py
---

# 2026-06-09 Agent Reliability Harness landing review

## Decision

Accept the landing as a safe implementation of all planned stages **as offline/default-off scaffolding**.

Do not treat it as live runtime rollout. Live gateway/taskpool enforcement remains a future separately authorized integration.

## What landed

- Eval case registry.
- Isolated harness runner.
- Structured trajectory/report artifacts.
- Sandbox policy blocking real side-effect tools by default.
- Hybrid grader contracts: deterministic code/tool, LLM rubric contract, human-review gate.
- Shadow workflow router and pure `limited-enforce` marker mode.
- Feedback ledger.
- Regression SQLite DB and dashboard.
- Seed cases.
- Tests and CLI smoke path.

## Evidence

Verified commands:

```bash
uv run --extra dev pytest tests/agent/test_reliability_harness.py -q
# 7 passed in 0.13s

uv run --extra dev python -m compileall agent/reliability_harness.py tests/agent/test_reliability_harness.py
# success

uv run --extra dev pytest tests/agent/test_reliability_harness.py tests/test_trajectory_compressor.py tests/test_trajectory_compressor_async.py -q
# 50 passed in 0.92s

python -m agent.reliability_harness list --cases-dir evals/cases --json
python -m agent.reliability_harness run --cases-dir evals/cases --runs-dir /tmp/hermes-eval-smoke --case direct-basic-answer --response-text OK --json
# passed true, score 1.0, dashboard/regression/report/trajectory artifacts written
```

## Evidence Boundary

This review certifies the offline/default-off harness implementation and its tests. It does not certify live gateway/taskpool enforcement, model-backed LLM judging, or automatic trajectory capture from active conversations.

## Risks retained

- LLM grader is currently a contract placeholder, not model-backed judging.
- Trajectory capture is harness-local, not live automatic capture.
- `limited-enforce` is a pure decision marker, not wired to live conversation routing.
- Parent profile repo has no remote configured, so parent commit cannot be pushed until a remote is added.

## Follow-up integration gates

Before live integration:

1. Add SSOT for live gateway/taskpool integration.
2. Define exact hot-path budget and rollback switch.
3. Add tests for config gating and no-side-effect invariants.
4. Run harness against more real cases.
5. Only enable `limited-enforce` for low-risk paths after false-direct metrics are known.

## Local-brain placement

This review is L6. The durable project structure is mirrored as L2:

- [[Project - Hermes Agent Reliability Harness]]
