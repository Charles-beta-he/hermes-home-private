# Agent Reliability Harness enterprise distribution landing — 2026-06-09

schema: hermes_self_optimization_landing_v1
id: agent-reliability-harness-enterprise-distribution-20260609
status: implemented_verified_committed_pushed
source_request: 用户认可“主干技能 + 关键自进化架构随私仓升级”的抽象，并要求“全盘推进直至企业产品级”。

## Objective & cost

Success criteria:
- A user installing/upgrading the private Hermes Agent repo receives the Agent Reliability Harness as a coherent product surface, not only loose source files.
- The distribution includes:
  1. core Python harness module;
  2. packaged seed eval cases;
  3. bundled trunk skill documentation;
  4. stable CLI entrypoint;
  5. tests proving packaging/distribution invariants;
  6. smoke verification from the repo checkout.
- Preserve the user-overlay boundary: personal profile skills, memory, local brain, config, cron, secrets, and runtime state do not become package defaults.

Hard constraints:
- Do not publish personal brain/memory/config/secrets.
- Do not auto-enable live gateway/taskpool enforcement.
- Do not mutate active gateway/taskpool/cron.
- Keep private-repo distribution scoped and test-backed.

Cost function:
- Maximize install/upgrade reliability, portability, and supportability.
- Minimize hidden personal-context leakage, blast radius, and packaging drift.

## Situation model

Current state before this pass:
- `agent/reliability_harness.py` exists in private repo and was pushed.
- Seed cases exist in source tree under `evals/cases/`, but `evals/` is not in `MANIFEST.in`/`setup.py` data files.
- Operational skill exists in profile-local `~/.hermes/skills/...`, not repo-bundled `hermes-agent/skills/...`.
- Console entrypoint is only `python -m agent.reliability_harness`, not an installed script.

## Selected path

Implement safe enterprise distribution pass:
- promote only the generic trunk skill into repo-bundled `skills/`;
- package generic seed eval cases;
- add `hermes-eval` console script;
- add default case discovery for source checkout and installed data-files;
- add tests for all invariants;
- commit and push private repo.

## Evidence log

Implementation artifacts:
- Bundled trunk skill copied into private repo:
  - `/Users/charles/.hermes/hermes-agent/skills/software-development/agent-eval-dynamic-workflow-harness/SKILL.md`
  - `/Users/charles/.hermes/hermes-agent/skills/software-development/agent-eval-dynamic-workflow-harness/references/local-brain-sync.md`
- Packaging updated:
  - `/Users/charles/.hermes/hermes-agent/MANIFEST.in`: `graft evals`
  - `/Users/charles/.hermes/hermes-agent/setup.py`: `_data_file_tree("evals")`
  - `/Users/charles/.hermes/hermes-agent/pyproject.toml`:
    - `hermes-eval = "agent.reliability_harness:main"`
    - wheel data-files for `evals/cases` and the trunk reliability skill.
- Harness default-case discovery updated:
  - `/Users/charles/.hermes/hermes-agent/agent/reliability_harness.py`: `bundled_cases_dir()` and optional `--cases-dir`.
- Distribution tests added:
  - `/Users/charles/.hermes/hermes-agent/tests/agent/test_reliability_harness_distribution.py`

Verification executed:
- `uv run --extra dev pytest tests/agent/test_reliability_harness_distribution.py -q` → `5 passed in 0.14s`.
- `uv run --extra dev pytest tests/agent/test_reliability_harness.py tests/agent/test_reliability_harness_distribution.py tests/test_trajectory_compressor.py tests/test_trajectory_compressor_async.py -q` → `55 passed in 0.80s`.
- Source checkout CLI:
  - `uv run --extra dev hermes-eval list --json` → 3 bundled cases.
  - `uv run --extra dev hermes-eval run --runs-dir /tmp/hermes-eval-enterprise-smoke --case direct-basic-answer --response-text OK --json` → `passed: true`, `score: 1.0`.
- Wheel build/install verification:
  - `uv build --wheel` → built `dist/hermes_agent-0.16.0-py3-none-any.whl`.
  - Wheel contents contain:
    - `hermes_agent-0.16.0.data/data/evals/cases/direct-basic-answer.json`
    - `hermes_agent-0.16.0.data/data/skills/software-development/agent-eval-dynamic-workflow-harness/SKILL.md`
  - Fresh Python 3.12 venv install with `uv pip install --no-deps dist/hermes_agent-*.whl`.
  - Installed `hermes-eval list --json` → 3 bundled cases.
  - Installed `hermes-eval run --runs-dir /tmp/hermes-wheel-eval-run --case direct-basic-answer --response-text OK --json` → `passed: true`, `score: 1.0`.
  - Installed data files present under:
    - `/tmp/hermes-agent-wheel-test/evals/cases/*.json`
    - `/tmp/hermes-agent-wheel-test/skills/software-development/agent-eval-dynamic-workflow-harness/SKILL.md`

Packaging issue discovered and fixed:
- Broad pyproject data-files globs such as `skills/**/*` included directories and broke wheel builds (`can't copy 'skills/apple'`).
- Broad `*.*` globs flattened paths under data-files, so `evals/cases` lookup failed.
- Final fix uses explicit data-file target directories to preserve runtime paths.

Commit/push:
- Hermes Agent private repo commit: `96f2f0f2a Ship reliability harness distribution assets`.
- Pushed to `origin/private/main`.
