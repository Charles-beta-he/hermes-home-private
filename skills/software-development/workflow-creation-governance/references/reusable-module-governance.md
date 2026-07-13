# Reusable Runtime Module Lifecycle

## Purpose and boundary

Applicability: use when a Hermes capability combines a reusable Skill with executable code, a provider/runtime dependency, credential handling, or workflow routing. Examples include travel providers, email adapters, device bridges, API clients, and local inference runtimes.

Anti-conditions:
- A prose-only checklist belongs in a Skill and does not need a runtime-module manifest.
- Project-only facts belong in project SSOT/profile, not this lifecycle.
- A one-off script with no stable reuse contract should remain session/project scoped.
- This process does not authorize external dispatch, purchases, production writes, credential entry, global routing, push, publish, or deployment.

A module is not complete because it has a `SKILL.md`, because one query succeeded, or because files were committed. Completion is the conjunction of contract, artifacts, security, deterministic tests, fresh smoke evidence, route boundaries, lifecycle policy, and a scoped commit.

## Canonical lifecycle

```text
seed
  -> classified
  -> specified
  -> threat-modeled
  -> candidate
  -> locally-validated
  -> workflow-bound
  -> committed
  -> operational
  -> upgraded | deprecated | quarantined | revoked | archived
```

Maturity is evidence-driven:

- `draft`: contract may change; no routing claim.
- `candidate`: artifacts exist; deterministic gates incomplete.
- `validated`: static gate, unit tests, readiness, fresh smoke, negative cases, and scoped commit pass.
- `common`: repeated successful reuse with stable output and low route collisions.
- `canonical`: promoted only after regression history, rollback, independent review when warranted, and supersession policy.
- `quarantine` / `revoked`: unsafe, credential-exposing, or provider-incompatible; routes must stop.
- `deprecated` / `archived`: replaced or unused; preserve redirect/migration evidence before removal.

## Phase gates

### G0 — Assetization and landing-zone gate

Evidence:
- reuse value, complexity, risk, evidence gap, long-termity, governability, route-collision risk;
- search of existing skills/modules to prevent duplication;
- decision to patch an umbrella/reference or create a new runtime module.

Pass: a real reusable capability gap exists.
Fail: one-off task, raw user wording, duplicate module, or project-only data.
Recovery: keep session/project scoped or patch the nearest umbrella.

### G1 — Module contract gate

Write `modules/<id>/module-governance.json` using `templates/module-governance.template.json`.

Required contract:
- stable module id, kind, scope, maturity, semantic version;
- exact artifact paths;
- credential mode and plaintext prohibition;
- daemon policy and side-effect class;
- exact dependency pins;
- verification commands and fresh-smoke requirement;
- owner, rollback, upgrade, deprecation;
- scoped-commit and push-authority policy.

Pass: manifest is complete and paths/contracts are reviewable.
Blocked: scope, owner, or side-effect class cannot be resolved.

### G2 — Authority and credential gate

Classify every side effect before code:

- `local_read`: inspect local files/config.
- `local_write`: create module/skill/tests/manifest.
- `external_read`: provider search/read-only query.
- `external_write`: send/book/update/create.
- `credential`: human-only entry; module may check presence and inject at subprocess boundary but must not reveal the value.
- `publish/deploy/push/destructive/payment`: separate exact authority, target, rollback, receipt, and readback.

Credentials:
- use OS Keychain or approved secret store;
- never store values in manifest, Skill, cron prompt, fixtures, logs, Git, command arguments, or evidence summaries;
- `--check` verifies presence/readiness only and must not query externally;
- inject credentials only into the shortest-lived child process that needs them;
- distinguish `credential_missing` from provider/runtime failure.

Pass: least-privilege path exists and secret exposure paths are closed.
Fail: plaintext credential, logging leak, broad environment persistence, or human secret entry attempted by the agent.

### G3 — RED test gate

Before production code, create failing behavior tests for at least:
- missing credential fails closed;
- readiness does not execute external work;
- credential is only injected into the intended child boundary;
- managed/pinned runtime is preferred;
- failure states are distinguishable;
- manifest gate rejects missing sections, floating versions, and plaintext secret fields.

Pass: tests fail for the expected missing behavior, not syntax/import mistakes.

### G4 — Implementation and dependency gate

Implement the smallest adapter/runtime boundary that passes the tests.

Rules:
- exact dependency versions only (`1.2.3`, not `latest`, `^`, `~`, `*`, or ranges);
- managed local runtime preferred over transient network resolution;
- `node_modules`, caches, raw outputs, credentials, and provider responses excluded from Git;
- no daemon unless the contract justifies it and lifecycle supervision is defined;
- preserve explicit status semantics: ready/fresh, credential missing, provider failed, stale fallback;
- do not silently fall back from fresh provider data to stale project data.

Pass: deterministic tests green and package lock/readback proves the exact runtime.

### G5 — Skill and route-boundary gate

Create or patch a Skill that defines:
- positive trigger class;
- anti-conditions and neighboring skills;
- invocation contract;
- evidence labels and fallbacks;
- prohibited operations;
- Definition of Done.

Minimum route evals:
- 3 positive prompts;
- 2 neighbor prompts;
- 2 forbidden prompts;
- 1 no-load prompt.

Pass: `skill_view` readback succeeds and route-eval fixture meets the minimum buckets.
Warn: module can be invoked explicitly but has not been bound to an umbrella workflow.
Fail: broad description steals neighboring workflows or implies unsupported automatic routing.

### G6 — Static lifecycle gate

Run:

```bash
python3 ~/.hermes/skills/software-development/workflow-creation-governance/scripts/module_governance_gate.py \
  --root ~/.hermes \
  --manifest ~/.hermes/modules/<id>/module-governance.json
```

Pass: `ok=true` and `failed_gates=[]`.
Fail: missing artifact, floating dependency, plaintext secret field, incomplete lifecycle, missing test/eval declarations, or unsafe Git policy.

This is a static contract gate. It does not claim tests, provider health, route behavior, or Git commit have run.

### G7 — Dynamic verification gate

Required evidence:
1. targeted unit tests;
2. syntax/compile/build check;
3. readiness `--check` with no external query;
4. fresh non-mutating provider/runtime smoke when authorized;
5. negative failure smoke where feasible;
6. secret-output scan over stdout/stderr and staged artifacts;
7. package/runtime version readback;
8. exact artifact and Skill readback.

Pass: commands exit successfully, output is fresh, secret-free, and evidence labels are correct.
Blocked: provider unavailable or credential missing; do not substitute stale prior output.

### G8 — Scoped Git commit gate

Before staging:
- parse complete porcelain status;
- inventory pre-existing staged files;
- define the exact module manifest;
- exclude runtime output, credentials, caches, `node_modules`, unrelated projects, cron state, and broad Skill-tree changes;
- run `git diff --check` and targeted tests.

If the repository already has unrelated staged files, do not clear or absorb them. Stage only exact paths and commit with a pathspec:

```bash
git add -- <exact-module-paths>
git commit --only -m 'feat: add reusable <module> module' -- <exact-module-paths>
```

Then verify:

```bash
git diff-tree --no-commit-id --name-status -r HEAD
git show --stat --oneline HEAD
git diff --cached --name-status   # pre-existing staged work must remain
```

Pass: commit contains only declared module files; hooks pass; unrelated staged/worktree state remains untouched.
Fail: hook bypass, `git add .`, credentials/runtime outputs in commit, or unrelated files absorbed.

Push is a separate authority gate.

### G9 — Workflow binding and operational gate

A module in the library is reusable, but not automatically selected everywhere.

Binding options:
- explicit `skills: [<module>]` on a workflow/job;
- umbrella Skill route to load the module for its trigger class;
- native Tool/MCP/global router registration, only as a separate governed change.

Verify the exact consumer with a dry run or safe smoke. Label:
- module discovered;
- module explicitly bound;
- runtime ready;
- provider fresh;
- external mutation disabled.

Do not claim global automatic routing from Skill creation alone.

### G10 — Upgrade, monitoring, and retirement gate

Upgrade loop:
1. inspect upstream release and compatibility notes;
2. change exact pin and lockfile;
3. RED compatibility test if behavior changes;
4. unit/build/readiness/fresh-smoke/secret scan;
5. static lifecycle gate;
6. scoped upgrade commit;
7. rollback readback.

Monitor:
- credential readiness without value exposure;
- runtime/provider failures;
- route false positives/false negatives;
- stale fallback rate;
- intervention rate and repeated module combinations.

Retire:
- disable routes first;
- publish `superseded_by`/migration guidance locally;
- prove no active workflow/cron depends on it;
- archive or delete only with exact authority;
- revoke credentials separately when appropriate.

## Verdict semantics

- `pass`: all required evidence for the current maturity exists.
- `warn`: safe to invoke explicitly, but a non-critical binding/monitoring item is absent.
- `fail`: deterministic contract or verification violation; repair locally.
- `blocked`: exact authority, credential, provider, or external target is missing; stop rather than downgrade.

## Complete Definition of Done

A new runtime module is complete only when:

- [ ] G0–G8 pass.
- [ ] `module-governance.json` passes the static gate.
- [ ] TDD evidence includes observed RED and GREEN.
- [ ] Exact dependencies and managed runtime are read back.
- [ ] Credential handling is fail-closed and secret-free.
- [ ] Skill routing has positive, neighbor, forbidden, and no-load cases.
- [ ] Readiness and fresh non-mutating smoke are distinct and pass when authorized.
- [ ] Secret scans cover output and commit scope.
- [ ] Scoped commit contains only declared module files and hooks pass.
- [ ] Workflow binding state is stated precisely; no global-routing overclaim.
- [ ] Rollback, upgrade, deprecation, owner, and supersession policy exist.
- [ ] Push/publish/deploy/external writes remain separate authority gates.

## Accessory contract

- `templates/module-governance.template.json`: copy when starting a runtime module; always-read during G1.
- `scripts/module_governance_gate.py`: run at G6 and before every module/upgrade commit.
- `scripts/tests/test_module_governance_gate.py`: run after modifying the gate itself; not needed for normal module use.
