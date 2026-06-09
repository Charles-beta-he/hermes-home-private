---
type: project
layer: L2
status: active
created: 2026-06-09T21:40:00+08:00
project: hermes-agent-reliability-harness
scope: hermes-agent-self-architecture
canonical_ssot:
  - /Users/charles/.hermes/docs/private/agent-eval-dynamic-workflow-longterm-20260609.md
  - /Users/charles/.hermes/docs/private/agent-eval-harness-full-landing-20260609.md
implementation_repo: /Users/charles/.hermes/hermes-agent
implementation_commit: 628e9104c
parent_commit: e0237a1
---

# Project: Hermes Agent Reliability Harness

## Purpose

Make Hermes agent reliability measurable and regression-testable through an offline/default-off harness rather than extra prompt bloat or direct live-gateway mutation.

## Current landed structure

Implementation is intentionally **off-hot-path** and **default-off**.

Core implementation:

- `agent/reliability_harness.py`
- `tests/agent/test_reliability_harness.py`
- `evals/cases/direct-basic-answer.json`
- `evals/cases/research-evidence-summary.json`
- `evals/cases/objective-gated-change.json`

Operational skill:

- `agent-eval-dynamic-workflow-harness`

## Component map

1. **Eval Case Registry** — versioned cases with input, context, allowed tools, forbidden side effects, expected artifacts, workflow label, risk, graders, acceptance.
2. **Trajectory / Evidence artifact** — per-run `trajectory.json` records case hash, router decision, sandbox policy, tool events, response text, and expected artifacts.
3. **Isolated Eval Harness Core** — `EvalHarness.run_case()` runs cases into an isolated runs directory and writes report/dashboard/regression artifacts.
4. **SandboxPolicy** — default blocks real side-effect tools such as `send_message`, `memory`, `cronjob`, and skill/config mutation surfaces.
5. **Hybrid Grader contracts** — deterministic `ToolCodeGrader`, `LLMRubricGrader` contract placeholder, and `HumanReviewGrader` for high-risk review requirements.
6. **Shadow Workflow Router** — classifies `direct`, `research`, `plan`, `objective_gated`; `limited-enforce` is a pure marker mode, not wired into live gateway.
7. **Feedback Ledger** — failed verdicts append structured JSONL improvement records with failure type, evidence refs, and suggested fix layer.
8. **Regression DB / Dashboard** — SQLite `eval_runs` plus generated `dashboard.md`.

## Verification evidence

Commands already run from `/Users/charles/.hermes/hermes-agent`:

```bash
uv run --extra dev pytest tests/agent/test_reliability_harness.py -q
# 7 passed in 0.13s

uv run --extra dev python -m compileall agent/reliability_harness.py tests/agent/test_reliability_harness.py
# success

uv run --extra dev pytest tests/agent/test_reliability_harness.py tests/test_trajectory_compressor.py tests/test_trajectory_compressor_async.py -q
# 50 passed in 0.92s

python -m agent.reliability_harness list --cases-dir evals/cases --json
python -m agent.reliability_harness run --cases-dir evals/cases --runs-dir /tmp/hermes-eval-smoke --case direct-basic-answer --response-text OK --json
# passed: true, score: 1.0
```

Artifacts from smoke run:

- `/tmp/hermes-eval-smoke/dashboard.md`
- `/tmp/hermes-eval-smoke/regression.sqlite`
- `/tmp/hermes-eval-smoke/<run>/report.json`
- `/tmp/hermes-eval-smoke/<run>/trajectory.json`

## Git state

- Hermes Agent implementation commit: `628e9104c Add offline agent reliability harness`.
- Implementation repo remote push: pushed to `origin/private/main`.
- Parent Hermes profile commit: `e0237a1 Land agent reliability harness`.
- Parent repo has no configured remote at the time of this note, so only the submodule implementation could be pushed.

## Boundaries

This landing does **not**:

- mutate live gateway;
- mutate taskpool;
- mutate cron;
- write durable memory;
- send external messages;
- enforce router decisions in active conversations.

Live integration requires a separate SSOT + focused tests + explicit authorization.

## Related

- [[Hermes Local Brain Memory Hierarchy]]
- [[Project - Hermes Local Brain]]
- [[2026-06-09-agent-reliability-harness-landing-review]]
