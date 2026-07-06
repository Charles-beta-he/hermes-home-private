---
name: lark-task-reading
description: Use when adding, debugging, or operating Lark task collection, including diagnosing taskpool runtime state, blocked tasks, hook/autorun routing, multimodel advisory statuses, and clearing Lark-derived tasks from the local-brain taskpool regardless of status. For taskpool runtime diagnosis, see references/taskpool-runtime-debugging.md, references/taskpool-lark-removal-and-flow-tolerance.md, and references/taskpool-hook-autorun-routing.md.
version: 1.0.0
author: Hermes Agent
license: MIT
skill_tier: molecule
related_skills: hermes-workflow-orchestrator, taskpool-control-plane, multi-model-thinking
dependencies:
- hermes-workflow-orchestrator
- taskpool-control-plane
- multi-model-thinking
metadata:
  hermes:
    tags:
    - lark
    - feishu
    - task-center
    - dispatch
    - automation
    - workflow
    related_skills: hermes-workflow-orchestrator, taskpool-control-plane, multi-model-thinking
---

# Lark Task Reading

Reference addendum: `references/uvisa-lark-taskflow-single-source-of-truth.md` is the current canonical UVISA Lark/work flow. For `uvisa-app-2.0`, because the project has an online address and a complete publishing flow, implementation merge/current-code proof plus deterministic verification is only an implementation-sendback gate; Lark final completion must wait for online-address UI 回收/验收 evidence. `references/uvisa-admin-lark-fasttrack-closeout.md` remains background guidance for admin-tier tiering, atom mapping, and upgrade triggers via regex matrix, but does not override the SSOT. `references/uvisa-c端-iceberg-classifier.md` is the C端 task scope classifier: semantic signal extraction with weight-based decision tree, no regex matching. Use for C端 task intake tier assignment. Script: `~/.hermes/scripts/uvisa_c端_lark_classifier.py`. **Superseded for new work** by `references/uvisa-unified-iceberg-multimodel-consensus.md` which covers the unified classifier + multimodel consensus + control plane integration.

## Taskpool quarantine behavior

When the user asks to temporarily remove Lark/Feishu tasks from the Hermes taskpool, include every lifecycle state (`pending`, `blocked`, `review`, `done`, etc.). Move matching task files to a timestamped quarantine directory with a manifest instead of deleting them. Match explicit Lark markers (`lark`, `lark-reopened`, `feishu`, `飞书`, `larksuite`, Lark URLs/IDs/source fields), refresh the taskpool dashboard, and verify `dispatch-dry-run --json` after removal.

## Overview


Use this skill when working on Lark/Feishu Task Center collection for `arc-dispatch`, `github-dispatch`, or any Hermes pipeline that does:

```
Lark Task Center -> collector -> envelope -> router -> confirmer/executor -> reporter
```

The goal is not to copy one project's code into another. The goal is to preserve the best reusable patterns from both projects in the Hermes skill tree so future Lark-task work starts from the same proven playbook.

## When to Use

- Adding, debugging, or operating Lark task collection
- Reading Lark/Feishu tasks into Hermes/taskpool or reconciling Lark-derived task state

Don't use for:
- generic taskpool work with no Lark/Feishu source boundary;
- mutating Lark status/comments or external dispatch without exact authorization and readback;
- scanning old project/archive copies when the live Lark API/helper already provides the source of truth.

## Default behavior

- Prefer tasks visibly under `UVISA-2.0新版开发`.
- If no UVISA-2.0 scoped tasks are visible in the fetched incomplete-task list, fall back to all incomplete tasks.
- Use `LARK_TASK_SCOPE_MODE=only` only when you want a hard filter.
- Use `LARK_TASK_SCOPE_MODE=off` to disable scope preference.
- Override scopes with comma-separated `LARK_TASK_PREFERRED_SCOPES`, e.g. `UVISA-2.0新版开发,OtherProject`.
- Preserve read-only collection during dry runs: no Lark comments, no status writes, no task mutation.

## Operational boundary: skill knowledge vs project runtime

A Hermes skill is a playbook, not an executable adapter. Loading this skill must not by itself imply that `arc-dispatch` or `github-dispatch` source files should be opened, imported, symlinked, or executed.

For user-facing requests such as "读取 Lark 任务", "看一下 UVISA-2.0 新版开发分类下关于我的任务", "列出我的任务", or "查询 Lark 任务并添加至任务池，仅添加负责人为我的任务":

1. Treat the source of truth as the Lark/Feishu Task API or an explicitly configured Hermes-native helper.
2. Do **not** scan old Desktop/archive duplicates looking for `run.sh`, `collector.py`, `orchestrator.py`, or `lark_task_reader.py`.
3. Do **not** execute a project pipeline from a copied or archived path, especially paths under desktop cleanup folders.
4. Only inspect or run `arc-dispatch` / `github-dispatch` code when the user explicitly asks to debug, migrate, compare, or operate that dispatch project.
5. For "负责人为我" filters, first identify the current user's `open_id` from `/authen/v1/user_info`, then include only tasks whose `members` contain `role == "assignee"` and that exact `id`. Do not treat follower/member presence as ownership.
6. When adding live Lark tasks into the local taskpool, deduplicate by both Lark GUID/URL and normalized title. Older taskpool notes may lack `lark_task_guid`; if a title match exists, enrich that existing note with Lark metadata instead of creating a duplicate.
7. If a second broad/all-scope read fails because the token expires after a successful scoped read, do not discard the fresh successful payload. Use it as the live snapshot already obtained, explicitly label any failed follow-up as an auth freshness blocker, and avoid retry loops that burn closeout budget.

The project files are reference implementations for pattern extraction. Normal task reading should be read-only and should not depend on whichever historical project copy happens to be discoverable first.

## Fusion map: arc-dispatch + github-dispatch

Detailed arc-dispatch/github-dispatch fusion mapping was moved to `references/fusion-map-arc-github-dispatch.md`.

Load it when using Lark as an intake surface that projects into taskpool/GitHub-style execution lanes.

Minimum in-root rule: keep source-of-truth and projection surfaces separate; do not treat projection success as task completion.

## Implementation pattern

The detailed Lark task reading implementation pattern was moved to `references/implementation-pattern.md`.

Load it when editing/operating the Lark reader, OAuth/token handling, task projection, or auto-authorize behavior.

Minimum in-root rule: preserve token-mode and reader auto-auth boundaries; do not conflate skill notes with project runtime code.

## Lark API shape notes

Detailed Lark API response shape notes were moved to `references/lark-api-shape-notes.md`.

Load it when parsing Lark tasks, comments, due dates, assignees, custom fields, or projection metadata.

Minimum in-root rule: inspect the live/API response shape before assuming field names or mutating state.

## UVISA routing

Add UVISA mappings before legacy/default projects:

- `uvisa_backend` -> `/Users/charles/Desktop/folder/work/uvisa-backend`
- `uvisa_app_2_0` -> `/Users/charles/Desktop/folder/work/uvisa-app-2.0`

Backend-specific keywords must appear before generic UVISA frontend keywords so `UVISA-2.0后端` routes to backend instead of frontend.

Recommended ordering:

1. Explicit backend lane: `UVISA-2.0后端`, `后端`, `API`, `接口`, `uvisa-backend`.
2. Explicit frontend lane: `uvisa-app-2.0`, `H5`, `移动端`, `用户端`, screen names.
3. Cross-project/fan-out lanes.
4. Default lane last.

## Loop implementation

Detailed loop implementation guidance was moved to `references/loop-implementation.md`.

Load it when building/running the repeated task-reader loop, paging, filtering, or evidence emission.

Minimum in-root rule: preserve fail-closed behavior and readback; do not turn reader failures into silent task absence.

## Executing a Lark task: closeout before exploration

The detailed Lark-task execution/closeout workflow was moved to `references/executing-lark-task-closeout-before-exploration.md`.

Load it when executing a specific Lark task, reconciling taskpool/Lark status, or deciding closeout before creating exploratory work.

Minimum in-root rule: finish or explicitly gate the current task with evidence before branching into broad exploration.

## Lark comment and completion closeout

Detailed Lark task evidence comment, completion gating, GUID-based task identification, safe comment format, API/CLI writeback, and readback requirements live in `references/lark-task-comment-complete-closeout.md`.

Load it only after a concrete Lark/Feishu task or GUID/URL is in scope and the user intends writeback, closeout, or completion. Do not use it for simple task listing or generic code submission without a Lark task boundary.

## Multi-model routing

Use multi-model thinking by risk level, not by habit:

- T0: deterministic checks for small doc wording changes.
- T1: one reviewer when adding a new collector pattern or changing routing semantics.
- T2: 3-model advisory when fusing patterns across `arc-dispatch` and `github-dispatch`.
- T3: 4-model ratification only for write-back automation, autonomous execution, or state-machine changes that can mutate external systems.

If the multi-model artifact says `not_certified`, treat it as advisory provenance. Do not claim ratification; resolve the issue ledger with deterministic evidence and rerun only if certification is required for the decision.

## Verification Checklist

For `github-dispatch`:

```bash
cd /tmp/github-dispatch
.venv/bin/python -m pytest tests/test_collector.py tests/test_pipeline.py -q
.venv/bin/python -m compileall -q collector.py lark_task_reader.py router.py orchestrator.py
```

For `arc-dispatch`:

```bash
cd /tmp/arc-dispatch
python3 -m unittest tests.test_lark_task_reader -v
python3 tests/test_basic.py
python3 -m compileall -q collector.py lark_task_reader.py router.py tests/test_lark_task_reader.py
```

For skill-tree-only changes:

```bash
python3 - <<'PY'
from pathlib import Path
import re, yaml
p = Path.home()/'.hermes/skills/software-development/lark-task-reading/SKILL.md'
s = p.read_text()
assert s.startswith('---')
m = re.search(r'\n---\s*\n', s[3:])
assert m
fm = yaml.safe_load(s[3:m.start()+3])
assert fm['name'] == 'lark-task-reading'
assert len(fm['description']) <= 1024
assert len(s) <= 120000
print('skill frontmatter ok')
PY
python3 ~/.hermes/scripts/skill-steward.py --graph-check --json
```

After Python compile checks, delete generated `__pycache__/*.pyc` if the repo tracks/deletes pyc files, so commits do not include bytecode churn.
- [ ] Preconditions, scope, and tool availability were checked before following this workflow.
- [ ] The key output artifacts, commands, or side-effects were verified by read-back or direct inspection.
- [ ] The final result still matches the trigger and acceptance shape of this skill.
## Project-pipeline commands

Use these only after intentionally choosing a live dispatch project as the runtime target, and run them from that project's canonical git root. They are **not** the default way to answer a normal "read my Lark tasks" request.

```bash
# First prove the runtime target is the intended project, not an archive/duplicate copy
pwd
git rev-parse --show-toplevel 2>/dev/null || true
git status --short

# Default: prefer UVISA-2.0新版开发, fall back to all incomplete tasks
./run.sh --mode collect-only --dry-run

# Hard filter to UVISA-2.0新版开发
LARK_TASK_SCOPE_MODE=only ./run.sh --mode collect-only --dry-run

# Custom preferred scope list
LARK_TASK_PREFERRED_SCOPES=UVISA-2.0新版开发 ./run.sh --mode collect-only --dry-run

# Disable scope preference for a broad audit
LARK_TASK_SCOPE_MODE=off ./run.sh --mode collect-only --dry-run
```

- Detailed larksuite/cli auth + dry-run oracle notes: `references/larksuite-cli-auth-and-dryrun.md`.
- Task detail lookup patterns (matrix snapshot fallback, prototype comparison): `references/lark-task-detail-lookup-patterns.md`.
- Lark MCP user-auth recovery notes: `references/lark-mcp-user-auth-recovery.md`.
- Lark OAuth duplicate-login / fixed-port single-flight guard notes: `references/lark-oauth-single-flight-guard.md`.
- UVISA live auth + stale snapshot triage notes: `references/uvisa-live-auth-and-stale-snapshot-triage.md`.
- Taskpool Lark cleanup + flow-tolerance notes: `references/taskpool-lark-removal-and-flow-tolerance.md`.

## Task classification: unified iceberg system

Three-layer classification for all UVISA Lark tasks (admin + C端 unified):

### Layer 1: Deterministic iceberg analysis (free, instant)

**Script:** `~/.hermes/scripts/uvisa_lark_unified_classifier.py`
```bash
python3 ~/.hermes/scripts/uvisa_lark_unified_classifier.py \
  --input ~/.hermes/evidence/lark-sync/uvisa-app-2.0/live-tasks.json \
  --write-back --json
```
Replaces both the old admin regex matrix and the C端-only iceberg classifier with a single unified system. Extracts semantic signals (amount/UI/status/nav/backend/human/security) with weight-based decision tree. Outputs `tier + scope + domain + confidence`. No regex matching for classification decisions.

**Why regex fails for C端:** C端任务标题描述的是用户操作路径（"点击底部导航栏→资产→转出→跨境汇款→输入金额→下一步"），不是技术实现。正则看到"跨境汇款"就判定"需后端"，但实际任务可能是纯前端 UI 对齐。

### Layer 2: Multimodel consensus (on-demand, 3 models)

For low-confidence or needs-triage tasks from Layer 1, real model consensus replaces guesswork:

```bash
# Review queue generation (dry-run)
python3 ~/.hermes/scripts/uvisa_lark_multimodel_classifier.py \
  --input ~/.hermes/evidence/lark-sync/uvisa-app-2.0/live-tasks.json \
  --dry-run --json
```

**IMPORTANT:** The script cannot call models directly from Python — `consult_models.py` requires a state_file and subcommands (`run state_file`), not `--model X --prompt Y`. Instead:
1. Run the classifier with `--dry-run` to output the review queue
2. Use `delegate_task(tasks=[...], toolsets=[])` with empty toolsets for real model calls
3. Aggregate votes and write back results

Pattern for real multimodel consensus:
```python
# delegate_task with 2-3 tasks in parallel, each a different "model perspective"
delegate_task(tasks=[
    {"goal": "Classify these tasks: ...", "toolsets": []},
    {"goal": "Classify these tasks: ...", "toolsets": []},
], toolsets=[])
# Each task returns JSON with tier/scope/domain per task
# Majority vote wins; agreement = matching_votes / total_votes
```

Results write back to taskpool frontmatter:
```yaml
iceberg_tier: S0
iceberg_confidence: multimodel_consensus
iceberg_multimodel_consensus: agreement=100%; deterministic=M; final=S0; models=mimo-v2.5-pro×2
```

### Layer 3: Control plane integration

- **Dispatch score**: S0=+12, S1=+10, F=+8, L=-3, B=-15 → quick fixes float to top
- **Preflight gate**: lane=work + project has value but missing `source_weighting_policy_ref` → blocked
- **Work contract**: L tasks auto-add `A-backend-contract` acceptance atom, B tasks add `A-human-confirmation`
- **Dashboard**: Iceberg Tier Distribution block in `brain_task_orchestrator.py dashboard --write`

### Legacy scripts (still available, narrower scope)

| Script | Scope | Method |
|---|---|---|
| `uvisa-admin-lark-fasttrack-closeout.py` | admin only | regex keyword matrix |
| `uvisa_c端_lark_classifier.py` | C端 only | semantic signal + weight tree |

Prefer the unified classifier for new work. Legacy scripts remain as reference implementations.

### When to use which layer

- **All tasks** → Layer 1 (deterministic) runs first automatically
- **confidence=low / tier=M / scope=inferred** → Layer 2 (multimodel consensus) for validation
- **Dispatch/preclose** → Layer 3 (control plane) handles sorting and gates

## Common Pitfalls

Detailed Lark-task pitfalls were moved to `references/pitfalls-and-verification.md`.

Load it when authentication, project routing, MCP token mode, taskpool quarantine, or Lark/brain projection behavior is surprising.

Minimum in-root rule: read the live Lark/taskpool source and preserve auto-authorize/token-mode boundaries before mutating state.

When absorbing a draft Lark closeout workflow, do not create a narrow one-session sibling skill by default. Prefer a scoped reference under this umbrella plus a root pointer; keep routing in `lark-task-reading`, and put comment/complete details behind the reference so ordinary task listing does not load closeout-specific writeback rules.

## Verification checklist

- [ ] Auth preflight distinguishes current live readiness from stale snapshots (`CURRENT_READY`, `CURRENT_BLOCKED_NO_TOKEN`, `CLI_UNBOUND`, `HERMES_APP_CREDENTIALS_MISSING`, `PREVIOUS_SNAPSHOT_AVAILABLE`).
- [ ] For assigned-only requests, current user `open_id` is proven from `/authen/v1/user_info`, and ownership is `members[].role == "assignee"` with matching `id` (not follower-only membership).
- [ ] Taskpool insertion dedups by GUID/URL and normalized title; existing title matches are enriched rather than duplicated.
- [ ] After taskpool insertion/enrichment, selfcheck/evidence-spine pass, dashboards are refreshed, and every accepted live GUID appears in a task note.
- [ ] OAuth recovery uses a single-flight guard before raw login when duplicate auth URLs, stale background output, or port 3010 conflicts are present.
- [ ] Scoped tasks are preferred by default and fallback remains intact.
- [ ] `only` and `off` modes work.
- [ ] Payload includes scope metadata.
- [ ] Comments, URLs, doc/wiki links, image/file placeholders, and image keys are preserved when present.
- [ ] Dedup checks all local statuses; fan-out dedups siblings.
- [ ] Dry-run performs no external writes.
- [ ] Backend routes are checked before generic frontend routes.
- [ ] Relevant tests and compile checks pass.
- [ ] Skill graph strict check passes after skill edits.
