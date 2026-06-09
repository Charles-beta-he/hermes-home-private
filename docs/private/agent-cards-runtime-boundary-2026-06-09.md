# Hermes Agent Cards Runtime Boundary Follow-through

Date: 2026-06-09

## Scope

User authorized continuing from the Agent Cards documentation/validator layer until the overall boundary.

This follow-through advanced from default-off scaffold to default-on specialist routing, default-on Agent Card prompt context, default-on advisory multimodel conductor certification, default-on digest-bound conductor closeout for certified worker proofs, and default-on local-file external adapter write-through harness:

- Agent Card runtime helper module;
- deterministic specialist profile recommendations;
- routing decisions with `apply` as the default;
- `off` / `shadow` escape hatches for rollback or observation-only routing mode;
- worker prompt Agent Card context enabled by default;
- `HERMES_ENABLE_AGENT_CARD_CONTEXT=0/off/false/no` escape hatch for prompt rollback;
- worker subprocess profile handoff via `hermes -p <chosen_profile> chat ...`;
- profile-auth-aware worker model chain filtering so routed profiles skip known-unavailable providers such as Gemini OAuth when missing;
- default-on advisory multimodel conductor packet attached to validated worker proofs;
- `HERMES_MULTIMODEL_CONDUCTOR_MODE=off|shadow` escape hatch;
- default-on digest-bound conductor done authorization for narrow review->done closeout;
- `HERMES_CONDUCTOR_DONE_CLOSEOUT_MODE=off|shadow` escape hatch;
- default-on digest-bound local-file external adapter harness with rollback;
- `HERMES_EXTERNAL_ADAPTER_HARNESS_MODE=off|shadow` escape hatch;
- tests proving task/Kanban/lifecycle/proof gates remain bounded by routing/context/conductor/closeout/adapter harness;
- prompt budget test proving Agent Card context delta stays bounded;
- validation that coverage/classification stayed healthy.

## Landed artifacts

- `/Users/charles/.hermes/scripts/agent_cards_runtime.py`
- `/Users/charles/.hermes/scripts/test_agent_cards_runtime.py`
- `/Users/charles/.hermes/scripts/agent_team_controller.py`
- `/Users/charles/.hermes/scripts/external_adapter_harness.py`
- `/Users/charles/.hermes/scripts/test_external_adapter_harness.py`
- `/Users/charles/.hermes/docs/private/agent-cards-v1.json`

## What changed

### 1. Agent Cards now include recommendation metadata

Each architecture domain in `agent-cards-v1.json` now has:

- `recommended_runtime_profiles`
- `runtime_boundary: controlled_apply_with_escape_hatches`

This does not change any Kanban assignee. It only chooses the Hermes profile for the spawned worker subprocess.

### 2. Runtime helper module

`agent_cards_runtime.py` provides:

- `load_cards()`
- `task_domain(task)`
- `recommend_profiles(task)`
- `routing_decision(task)`
- `render_agent_card_context(task, profile, enabled=...)`

The module is deterministic and read-only for task state. `routing_decision` supports `off`, `shadow`, and `apply`; `apply` is default, while `shadow` remains observation-only rollback mode.

### 3. Optional worker context integration

`agent_team_controller.py` now has:

- `build_agent_card_context_pack(task, profile=None)`

It renders Agent Card context by default. Disable with:

```bash
HERMES_ENABLE_AGENT_CARD_CONTEXT=off
```

Accepted disable values: `0`, `false`, `off`, `no`, `disabled`.

Prompt budget probe on a representative task:

- context off: 4635 chars
- context on: 6242 chars
- delta: 1607 chars / 34.67%
- test cap: delta <= 2200 and total <= 8000

The rendered context explicitly says:

- Agent Cards do not expand permissions.
- Agent Cards do not authorize lifecycle mutation.
- Conflicts with task/policy gates must fail closed.

### 4. Controlled routing apply mode

`agent_team_controller.py` records an `agent_card_routing_decision` trace for each delegated worker. Default mode is now `apply`, so the worker subprocess is launched through the recommended specialist Hermes profile.

Rollback / observation-only modes:

```bash
HERMES_AGENT_CARD_ROUTING_MODE=shadow
```

or:

```bash
HERMES_AGENT_CARD_ROUTING_MODE=off
```

The worker command is shaped as:

```bash
hermes -p <chosen_profile> chat ...
```

and the worker subprocess environment also gets:

- `HERMES_PROFILE=<chosen_profile>`
- `HERMES_PROFILE_NAME=<chosen_profile>`

This does not mutate task notes, Kanban assignees, lifecycle state, proof gates, or model chain semantics. It only routes the spawned worker process through a specialist Hermes profile.

### 5. Profile-auth-aware model chain filtering

When routed through a named profile, the controller checks `hermes -p <profile> doctor` once per controller process and drops providers known to be unavailable for that profile.

Current known boundary handled:

- named specialist profiles have OpenAI Codex auth;
- named specialist profiles lack Google Gemini OAuth;
- advisory chains therefore skip `google-gemini-cli` under routed profiles instead of wasting the first attempt on a predictable auth miss.

### 6. Default-on advisory multimodel conductor

`agent_team_controller.py` now runs `run_multimodel_conductor(...)` after a worker returns a valid proof and after deterministic proof consistency passes.

Default mode:

```bash
HERMES_MULTIMODEL_CONDUCTOR_MODE=apply
```

Rollback/disable:

```bash
HERMES_MULTIMODEL_CONDUCTOR_MODE=off
```

The conductor packet is attached to the proof under `multimodel_conductor` and traced as `multimodel_conductor_verdict`.

Authority boundary:

- advisory only;
- does not mark done;
- does not write task lifecycle;
- does not install skills or mutate memory;
- cannot bypass proof gates or review closeout.

### 7. Default-on digest-bound conductor closeout

After the conductor is certified, `agent_team_controller.py` now builds a narrow `hermes_conductor_done_authorization_v1` packet and may execute review -> done.

Default mode:

```bash
HERMES_CONDUCTOR_DONE_CLOSEOUT_MODE=apply
```

Rollback/disable:

```bash
HERMES_CONDUCTOR_DONE_CLOSEOUT_MODE=off
```

Observation-only:

```bash
HERMES_CONDUCTOR_DONE_CLOSEOUT_MODE=shadow
```

The authorization is bound to:

- task id;
- previous status = `review`;
- target status = `done`;
- proof artifact path;
- proof digest;
- conductor digest;
- authorization digest.

The executor then:

1. appends a trace authorization event;
2. reads current task status;
3. refuses anything except `review` or idempotent already-`done`;
4. calls the existing lifecycle gate `transition_task(..., "done", ...)` with proof/conductor/authorization evidence;
5. reads back task status;
6. reports `done_write_verified` only if readback is `done`.

This is not a generic lifecycle executor. It does not authorize reopen, retry, blocked, archive, arbitrary SQL, taskpool note mutation, external adapter writes, skill writes, memory writes, sends, or deployments.

### 8. Default-on local-file external adapter harness

`external_adapter_harness.py` is the first default-on external adapter write-through executor, but it is deliberately a fixture harness:

- adapter allowlist: `local_file` only;
- operation allowlist: `set_status` only;
- target status: `done` only;
- target path: JSON file under `/Users/charles/.hermes/state/external-adapter-harness/` unless a test harness base is explicitly supplied;
- symlink and path escape rejected;
- authorization requires elevated role and evidence;
- mutation is bound to intent digest, authorization digest, and canonical done authorization id;
- execution writes the fixture file and immediately reads back;
- rollback requires exact request digest and restores the captured previous state.

Default mode:

```bash
HERMES_EXTERNAL_ADAPTER_HARNESS_MODE=apply
```

Rollback/disable:

```bash
HERMES_EXTERNAL_ADAPTER_HARNESS_MODE=off
```

Observation-only:

```bash
HERMES_EXTERNAL_ADAPTER_HARNESS_MODE=shadow
```

This is not a real external sender/deployer. It does not touch Kanban DB, taskpool notes, Lark, Telegram, memory, skills, providers, cron, shell, or network.

## Verification

Tests added:

- default routing is apply with off/shadow escape hatches;
- recommendations prefer domain card profiles;
- context can be explicitly disabled;
- default worker context includes Agent Card guidance;
- Agent Card context carries no-authority-expansion rule;
- Agent Card prompt delta stays within the configured budget cap;
- profile-provider filtering drops unavailable Gemini for routed profiles;
- multimodel conductor defaults to apply and supports off escape hatch;
- multimodel conductor attaches advisory-only certification packets;
- conductor done closeout defaults to apply and supports off/shadow escape hatch;
- closeout authorization is digest-bound to proof/conductor/task/status;
- closeout executes only from review, verifies readback, and is idempotent for already-done;
- external adapter harness defaults to apply and supports off/shadow escape hatch;
- local-file harness intent/authorization/execution is digest-bound, readback-verified, idempotent, and rollback-verified;
- local-file harness rejects path escapes, symlinks, non-elevated actors, missing evidence, and digest tampering.

## Boundary reached

This is the next safe boundary after default-on specialist routing, default-on Agent Card prompt context, default-on advisory multimodel conductor, default-on digest-bound conductor closeout, and default-on local-file external adapter harness.

Still not enabled automatically:

1. Broad lifecycle mutation authority
   - Enabled lifecycle path is only review -> done, and only with certified conductor proof.
   - Reopen/retry/blocked/archive/force transitions remain outside this executor.

2. Real external adapter writes
   - Enabled external adapter is local-file fixture only.
   - Kanban DB, taskpool notes, Lark, Telegram, deployments, providers, cron, memory, and skills remain outside this harness.

3. Canonical skill writer / external skill installation
   - Would mutate production skills.
   - Requires human review and gated writer.

4. External side-effect executors
   - Would write/send/deploy externally.
   - Requires explicit confirmation, digest-bound executor, audit event, and rollback path.

## Current verdict

Hermes has now advanced from documentation-only Google-style Agent Cards to default-on specialist worker profile routing, default-on Agent Card worker prompt guidance, default-on advisory multimodel conductor certification on valid worker proofs, default-on digest-bound conductor closeout for certified review tasks, and a default-on digest-bound local-file external adapter harness. The enabled write paths are deliberately narrow: review -> done only for lifecycle, and local-file fixture status writes only for adapter write-through, both with digest/readback boundaries. The next boundary is broad lifecycle mutation authority, real external adapters, canonical skill writers, or external send/deploy side-effect executors.
