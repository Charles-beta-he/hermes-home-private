# Child closeout vs parent ratification

Use this note when a blocked parent task has already been split into narrowed convergence children and those children can be claimed/completed, but the taskpool still shows:
- `blocked-resolve-step --json` => `resolved_count: 0`
- `next --json` => `next: null`
- `list --json` => only the original blocked parents remain active

## Pattern

Observed durable pattern:
1. Parent is blocked on multimodel certification (`FAIL` / `CONTINUE_LOOP`).
2. New convergence children are created for axes such as:
   - `fallback_threshold`
   - `patch_normalization`
   - `quota_observability`
   - `relay_ordering`
3. Those child tasks can be manually claimed, populated with narrowed briefs, and closed out.
4. `auto-subtask-sync` may then report:
   - `ready: true`
   - `open_children: []`
   - `missing_children: []`
5. Despite that, the parent remains blocked because its own certification artifact/frontmatter still points at the old failed round.

## What this means

Closing the children proves the decomposition work is complete.
It does **not** prove the parent has a fresh ratified multimodel artifact.

If the parent still shows fields like:
- `multimodel_status: not_certified`
- `multimodel_last_gate_status: FAIL`
- `multimodel_last_decision: CONTINUE_LOOP`
- stale `multimodel_last_failures`

then the remaining work is parent-level evidence integration / re-ratification, not more child splitting.

## Operational rule

After closing narrowed children, always verify in this order:
1. `auto-subtask-sync --task <parent> --actor hermes --json`
2. `blocked-resolve-step --json`
3. `next --json`
4. `list --json`

Decision:
- If children are all closed and `next` is still null, stop producing more children.
- Move to parent refresh work: new discussion artifact, framing convergence, or explicit parent evidence reintegration.

## Reporting rule

When summarizing pool progress, distinguish:
- **evidence progress**: child tasks completed, narrowed briefs written, proof/evidence debt reduced
- **dispatch progress**: a task actually becomes dispatchable in `next --json`

Do not collapse these into one claim.

## Typical remaining parent blockers

Even after child closeout, parent blockers often reduce to:
- `framing`
- stale `non_approve_vote:*:amend`
- stale `best_within_constraints_missing:*`
- agreement thresholds still below target on the parent artifact

This is the cue to run parent-level ratification refresh, not another child-axis pass.