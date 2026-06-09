# Agent Reliability Harness full-stage landing — 2026-06-09

schema: hermes_self_optimization_landing_v1
id: agent-eval-harness-full-landing-20260609
status: implemented_verified_committed
source_request: 用户要求“继续推进直至落地所有阶段”。

## Objective & cost

Success criteria:
- Land a production-shaped but safe/default-off implementation of all previously defined stages:
  1. eval case registry;
  2. trajectory/evidence artifact shape;
  3. isolated harness runner;
  4. hybrid code/tool/LLM/human grader contracts;
  5. shadow workflow router;
  6. feedback/improvement ledger;
  7. regression SQLite + dashboard/report;
  8. limited-enforcement scaffold with explicit escape hatch.
- Add tests first and verify them against real code.
- Make a scoped commit in the Hermes repo/submodule and record evidence.

Hard constraints:
- Do not alter live gateway, cron, taskpool, memory, model config, or active provider settings.
- Do not enable enforcement by default.
- Do not send messages or mutate external systems during eval runs.
- Do not claim full production runtime rollout if only safe scaffolds are landed; label default-off and shadow behavior honestly.

Cost function:
- Maximize regression value, reversibility, and future extensibility.
- Minimize hot-path latency, blast radius, prompt bloat, and persistent-state pollution.

## Situation model

Known facts:
- SSOT exists at `/Users/charles/.hermes/docs/private/agent-eval-dynamic-workflow-longterm-20260609.md`.
- Skill exists: `agent-eval-dynamic-workflow-harness`.
- Hermes code checkout: `/Users/charles/.hermes/hermes-agent`.
- Existing related code includes `agent/trajectory.py` and `agent/task_router.py`.
- No existing `eval_harness.py` was found before this implementation.

Assumptions to verify:
- Hermes CLI can accept a new subcommand or standalone module without large blast radius.
- Existing tests can run through `uv run --extra dev pytest`.

## Candidate paths

A. Runtime-first integration
- Directly route live conversations through workflow router and harness checks.
- Risk: high blast radius, gateway latency, accidental taskpool/memory side effects.
- Rejected for this pass.

B. Safe full-stage scaffold
- Implement all components as offline/default-off CLI/module with tests and sample cases.
- Router enforcement is implemented as a pure decision function with explicit mode, not wired into live gateway.
- Selected.

C. Docs-only taskpool backlog
- Low risk, but fails user request to land implementation.
- Rejected.

## Selected path

Implement B: safe full-stage scaffold.

Definition of “all stages landed” in this pass:
- All architectural components exist as executable/tested code paths.
- Runtime enforcement remains scaffolded/default-off; not connected to live gateway until a later explicitly authorized runtime integration pass.

## Evidence log

Implementation artifacts:
- `/Users/charles/.hermes/hermes-agent/agent/reliability_harness.py`
  - Eval case registry.
  - Sandbox side-effect policy.
  - Shadow/suggest/limited-enforce workflow router.
  - Tool/code, rubric-contract, and human-review grader contracts.
  - Feedback ledger JSONL.
  - Regression SQLite database.
  - Dashboard/report artifact generation.
  - `python -m agent.reliability_harness` CLI with `list` and `run`.
- `/Users/charles/.hermes/hermes-agent/tests/agent/test_reliability_harness.py`
  - 7 tests covering registry, sandbox, shadow routing, limited enforcement scaffold, deterministic grading, run artifacts, regression DB, feedback ledger, and CLI JSON output.
- Seed eval cases:
  - `/Users/charles/.hermes/hermes-agent/evals/cases/direct-basic-answer.json`
  - `/Users/charles/.hermes/hermes-agent/evals/cases/research-evidence-summary.json`
  - `/Users/charles/.hermes/hermes-agent/evals/cases/objective-gated-change.json`

RED evidence:
- `uv run --extra dev pytest tests/agent/test_reliability_harness.py -q`
- Initial result before implementation: `ModuleNotFoundError: No module named 'agent.reliability_harness'`.

GREEN evidence:
- Targeted: `uv run --extra dev pytest tests/agent/test_reliability_harness.py -q` → `7 passed in 0.13s`.
- Compile: `uv run --extra dev python -m compileall agent/reliability_harness.py tests/agent/test_reliability_harness.py` → success.
- Related trajectory suite: `uv run --extra dev pytest tests/agent/test_reliability_harness.py tests/test_trajectory_compressor.py tests/test_trajectory_compressor_async.py -q` → `50 passed in 0.92s`.
- Real CLI smoke:
  - `python -m agent.reliability_harness list --cases-dir evals/cases --json` listed 3 seed cases.
  - `python -m agent.reliability_harness run --cases-dir evals/cases --runs-dir /tmp/hermes-eval-smoke --case direct-basic-answer --response-text OK --json` returned `passed: true`, `score: 1.0`.
  - Artifacts created under `/tmp/hermes-eval-smoke/`: `dashboard.md`, `regression.sqlite`, `report.json`, `trajectory.json`.

Boundary statement:
- All stages are landed as executable/default-off/off-hot-path scaffolding.
- Live gateway/taskpool/memory/cron routing was intentionally not mutated.
- Runtime enforcement is represented by the pure `limited-enforce` router mode and is not wired into live user conversations.
