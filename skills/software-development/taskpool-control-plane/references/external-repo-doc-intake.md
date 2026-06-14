# External repo / doc intake for taskpool

Use this when the user wants a GitHub repository, subdirectory, article, or docs site added to the Hermes taskpool.

## Why this matters

For this user, external-material tasks should be triaged **before** they enter the pool. The task note should already carry lane/priority/architecture_target and evidence expectations, instead of relying on a later cleanup pass.

## Proven pattern

### 1) Inspect the live source first

For GitHub inputs:
- Open the live repo/path.
- Confirm the path exists.
- Inspect top-level structure via browser or GitHub contents API.
- Read at least one architectural file (`README.md`, `ARCHITECTURE.md`, package manifest, etc.).
- For long READMEs, use `browser_vision` to get a comprehensive overview without scrolling through the entire page. This is faster than multiple `browser_scroll` + `browser_snapshot` calls.

For docs inputs:
- Open the live documentation page.
- Extract concrete signals: architecture, data flow, integration model, runtime/storage assumptions, install path, APIs/tools.

### 2) Convert inspection into task classification

Map the material to taskpool fields immediately:
- `lane`: usually `evolution` for Hermes self-improvement / repo-analysis tasks.
- `priority`: default P2 unless the user marks the work urgent or blocking.
- `project`: usually `hermes-agent` for self-evolution tasks.
- `architecture_target`:
  - `local-brain` for memory systems, control plane, orchestration, runtime, skills, taskpool, local plugin integration.
  - `provider-quota` for routing, cost controls, model pools, budget handoff, account/quota governance.

### 3) Write stronger task metadata up front

Populate these fields during `brain_task_orchestrator.py add`:
- `capability_delta`
- `anti_drift_check`
- `acceptance_evidence`
- `objective`
- `parallel_boundary`
- `concepts`

**Required but non-obvious fields** (will fail without them):
- `--priority-layer` (e.g. `P2`) — separate from `--priority`; both are needed
- `--dependency-order` (e.g. `0`) — integer, position in dependency chain
- `--multimodel-triage-result` (e.g. `advisory`, `certify`, `skip`) — controls multimodel routing behavior

Error if missing:
```
task creation requires explicit priority/dependency/triage metadata; missing=['priority_layer', 'dependency_order', 'multimodel_triage_result']
```

Example complete add command:
```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py add "Title" \
  --lane evolution --priority P2 --project hermes-agent \
  --architecture-target local-brain \
  --capability-delta "..." --anti-drift-check "..." \
  --acceptance-evidence "..." --parallel-boundary "..." \
  --objective "..." \
  --priority-layer P2 --dependency-order 0 \
  --multimodel-triage-result advisory --json
```

Good wording pattern:
- analysis surface → Hermes gap mapping → smallest verifiable integration slice

This makes the task dispatchable and self-describing without a second classification round.

### 4) Check event-hook output after add

The `add --json` payload can show:
- `multimodel_route.reason = smart_route_matched`
- `autorun.reasons = ["autorun_disabled"]`

Interpretation:
- smart routing worked
- the task was classified for multimodel advisory
- but the add event itself did not execute bounded autorun

This is **not** a scheduler failure.

### 5) If the user asked to "全盘推进", run a real tick

After adding the task, run:

```bash
HERMES_LOCAL_BRAIN_AUTORUN=1 python3 ~/.hermes/scripts/brain_task_dispatch_tick.py --print-always --autorun-step --no-state
```

This lets the newly-added task actually participate in the claim → review → auto-close loop.

## Example signals from the MemOS / Hermes local plugin intake

Source observations that justified `architecture_target=local-brain`:
- repo folders: `agent-contract`, `core`, `bridge`, `server`, `tests`, `viewer`, `templates`
- docs emphasized:
  - local SQLite memory
  - task summarization and skill evolution
  - Hermes MemoryProvider integration
  - bridge daemon
  - automatic recall and memory search
  - multi-agent memory sharing

Those are local-brain / memory-system concerns, not provider-quota concerns.

## Taskpool-native adoption lifecycle

When the external material claims a runnable **main capability** (not only an idea), prefer the dedicated capability intake command instead of a vague analysis task:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py add-repo-capability-absorption \
  --source-url "https://github.com/org/repo" \
  --source-type repo \
  --capability-name "Short capability name" \
  --capability-claim "What the source claims it can do" \
  --target-surface cli_wrapper \
  --integration-level evaluate \
  --json
```

Use `--target-surface` to encode the lowest-coupling landing surface: `skill`, `cli_wrapper`, `mcp`, `sidecar`, `adapter`, `core`, or `taskpool`. Use `--integration-level` to encode the current ambition: `evaluate`, `reproduce`, `wrap`, `integrate`, or `productionize`.

The command creates `absorption_type: repo_capability_absorption` tasks with evidence gates for capability definition, real reproduction, risk boundary, integration surface, harness acceptance, and maintenance/rollback strategy. Creation itself **does not** authorize vendoring, external side effects, runtime integration, or taskpool automation; later workers must pass the reproduction and risk gates first.

This workflow is generic for external repositories/docs, not a one-off chat plan. After intake, the remaining work must live in taskpool tasks with explicit progress and evidence.

Use these stage gates when the material may be absorbed into Hermes:

1. `source-review`: repo identity, license, README/CLAUDE/manifest/source paths verified.
2. `gap-mapping`: source mechanisms mapped to Hermes landing zones and overlaps/rejections recorded.
3. `minimal-prototype`: one bounded, reversible slice chosen and validated against real Hermes surfaces.
4. `effectiveness-benchmark`: compare against current Hermes workflow; record recall/cost/quality signal, not just subjective value.
5. `adopt-update-or-reject`: if effective, create/update the concrete integration task/skill/script; if ineffective, close with rejection/watch evidence.

Progress reporting must distinguish:
- `landed`: committed script/skill/taskpool rule or verified artifact exists.
- `queued`: taskpool item exists but work not implemented.
- `certified/intake`: model or proof gate says the task is well-framed; this is not implementation completion.
- `rejected/watch`: evidence says no adoption now; preserve why.

If an event hook or proof-only bounded step auto-closes an external-repo task before the requested source review/gap mapping/prototype exists, correct the lifecycle state and record the reason. Do not report it as done.

## Pitfalls

- **GitHub repo name verification**: When the user provides a repo name verbally or from memory, the actual GitHub URL may differ in punctuation (dots vs hyphens, underscores, capitalization). Always confirm the live repo URL via GitHub search or API before committing to browser navigation. Example: user said "architecture-of-internet-product" but the real repo was `architecture.of.internet-product`. The initial wrong-URL navigation wastes a round trip.
- Do not add a vague "analyze repo X" task without checking the actual repo/doc shape.
- Do not defer priority/classification until after the task is already in the pool when the user explicitly wants intake triaged up front.
- Do not present later-stage adoption gates as a chat-only plan; create taskpool artifacts or report them as not yet landed.
- Do not treat `task_added`, multimodel certification, py_compile proof, or proof-only auto-close as source-review/prototype completion.
- Do not misread `autorun_disabled` in the add hook as a broken control plane; verify by running a real dispatch tick.
- Do not classify memory/plugin/runtime integration work as `provider-quota` just because it touches models.
- Do not forget `--priority-layer`, `--dependency-order`, and `--multimodel-triage-result` — these are required even though the help text doesn't highlight them prominently. The add will fail with `task creation requires explicit priority/dependency/triage metadata`.
- Evolution lane tasks with `architecture_target=local-brain` are auto-claimed by `hermes-multimodel` immediately after creation. The task transitions `pending → claimed → running` automatically. This is expected smart-routing behavior, not a control-plane fault. After creation, `eligibility-check` may show `no_dispatchable_task` because the task is already being processed.
