# Hermes root dirty-state governance report — 2026-06-04

Scope: `/Users/charles/.hermes` root repository dirty/untracked state after the scoped dreaming/evolution-store commit.

Controlling rule: do not blanket reset, clean, or commit because this worktree mixes Hermes source overlays, runtime state, taskpool/brain SSOT files, cross-profile config, memory, logs, and generated artifacts.

## Actions taken

1. Added a reusable classifier script:
   - `/Users/charles/.hermes/scripts/hermes_dirty_inventory.py`
2. Captured initial observed dirty-state summary from the first classifier run before cache cleanup.
3. Updated `.gitignore` for low-risk generated artifacts:
   - `__pycache__/`
   - `*.py[cod]`
   - `*.log.*`
   - Python cache dirs
   - `cron/output/`
4. Removed only Python bytecode/cache directories/files (`__pycache__`, `.pyc`, `.pyo`) under `/Users/charles/.hermes`.
5. Generated after-clean inventory:
   - `/Users/charles/.hermes/docs/private/dirty-inventory-20260604-after-cache-clean/summary.json`
   - `/Users/charles/.hermes/docs/private/dirty-inventory-20260604-after-cache-clean/inventory.csv`

## Initial observed summary

Captured from the first classifier run before cache cleanup:

- total: 4463
- untracked: 3965
- modified: 288
- deleted: 210
- high risk: 2215
- critical: 4
- medium: 414
- low: 1830

Top buckets:

- runtime/cron-output: 1337
- profiles/cross-profile: 994
- skills/active: 620
- media/generated: 338
- brain/workpad: 312
- scripts/local-control-plane: 240
- other: 227
- cache/pycache: 115

## After-cache-clean summary

From `dirty-inventory-20260604-after-cache-clean/summary.json` after committing this governance artifact:

- total: 3004
- untracked: 2507
- modified: 288
- deleted: 209
- high risk: 2213
- critical: 4
- medium: 414
- low: 373

Top buckets:

- profiles/cross-profile: 993
- skills/active: 620
- media/generated: 338
- brain/workpad: 312
- scripts/local-control-plane: 240
- other: 228
- notes/generated-reports: 107
- runtime/state: 48
- runtime/db-lock: 38
- runtime/logs: 35

## Impact

- Visible dirty/untracked count reduced from 4463 to 3004 entries after committing this governance artifact, primarily by ignoring `cron/output/`, removing Python bytecode/cache artifacts, and committing removal of one tracked bytecode file.
- No config, memory, database, skill, brain/workpad, or script semantic changes were reset or deleted.
- Remaining dirty state is mostly high-risk or semantically meaningful and requires manual or cluster-by-cluster governance.

## Manual intervention gates reached

The following classes are intentionally left untouched:

1. Cross-profile state/config: `profiles/**`
   - Reason: active system policy says profiles are separate Hermes homes; modifying/ignoring/removing them could affect other sessions.
2. Active skills: `skills/**`
   - Reason: 620 entries include modified/deleted/new skill content; must be reviewed with skill semantics and archive intent.
3. Brain/workpad: `notes/brain/**`
   - Reason: local-brain/project/task SSOT material; cannot be reset as generic generated notes.
4. Local control-plane scripts: `scripts/**`
   - Reason: 240 entries may contain important taskpool/multimodel/diagnostic implementation work.
5. Runtime DB/locks/config/memory:
   - `config.yaml`, `config/quorum.yaml`, `cron/jobs.json`, `state.db`, `kanban.db`, `gateway_state.json`, `memories/**`
   - Reason: high blast radius and/or sensitive personal profile state.
6. Inner Hermes source repo: `/Users/charles/.hermes/hermes-agent`
   - Reason: separate git repo on branch `feat/mcp-semantic-probes-real-client`, ahead of origin, with its own untracked docs.

## Recommended next batches

1. `scripts/**` audit batch:
   - group by taskpool, multimodel, brain, lark/uvisa, diagnostics, evolution.
   - commit only coherent clusters with tests.
2. `skills/**` archive/active reconciliation batch:
   - decide which deleted tracked skills should remain archived vs restored vs committed as removals.
3. `profiles/**` policy batch:
   - decide whether root repo should ignore all cross-profile homes or track selected profile templates.
4. `runtime/db/config` protected batch:
   - inspect diffs one-by-one; never blanket commit/reset.

## Verification commands

- `python3 /Users/charles/.hermes/scripts/hermes_dirty_inventory.py --out-dir /Users/charles/.hermes/docs/private/dirty-inventory-20260604-after-cache-clean`
- `python3 -m py_compile /Users/charles/.hermes/scripts/hermes_dirty_inventory.py`
- `git -C /Users/charles/.hermes diff --check -- .gitignore scripts/hermes_dirty_inventory.py docs/private/dirty-inventory-20260604-after-cache-clean docs/private/hermes-dirty-state-governance-20260604.md`
