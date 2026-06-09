# Restoring real `running` work from a blocked evolution parent

Use this when the pool has `active>0` but `running=0`, the main P1 parent is `blocked` with `loop_non_convergence`, and advisory tasks are secondary.

## Proven sequence

1. Re-run baseline:
   - `list --json`
   - `next --json`
   - `dispatch-dry-run --json`
   - `selfcheck --json`
   - `autorun-runner --json`

2. If the root blocker is a blocked P1 evolution parent, prefer decomposition before policy surgery:
   - run `auto-split-non-convergence --task <parent> --json`
   - expect new P1 evolution children like `framing`, `quota_observability`, `patch_normalization`, `fallback_threshold`, `relay_ordering`

3. Close one bounded convergence child end-to-end to create real progress evidence.
   - Proven slice here: `fallback_threshold`
   - Move through lifecycle explicitly: `claimed -> running -> review -> done`
   - Write narrowed brief + structured evidence into the child note
   - Run deterministic syntax guard after note/code writeback

4. Freeze dependency order when the parent FAIL artifact still shows unresolved noop-vs-change disagreement.
   - Proven ordering from the session:
     `quota_observability -> patch_normalization -> fallback_threshold`
   - Interpretation: fallback logic is a valid narrowed brief, but not the first code slice to land when quota visibility and patch classification are still unresolved.

5. Re-run `autorun-runner` after one child is closed.
   - If a new evolution child becomes eligible, let autorun claim it.
   - Then promote `claimed -> running` so the pool no longer reports `0 running`.

## Why this works

- It breaks the false binary of “parent still blocked” vs “nothing can run”.
- It preserves fail-closed governance on the parent while still allowing bounded evolution children to move.
- It avoids jumping straight to allowlist/policy edits when the higher-value move is to reopen the evolution lane through decomposed children.

## Verification targets

- At least one child task reaches `done` with proof/evidence.
- `next --json` points at another evolution child rather than null/advisory-only.
- `autorun-runner --json` produces `handoff_created` for the next child.
- `list --json` shows a real `running` task, not just `claimed` or advisory `pending` work.

## Pitfalls

- Do not report success merely because children were created; verify one child actually closed and another entered `running`.
- Do not treat `fallback_threshold` as the first implementation slice when the parent FAIL artifact still says quota/patch evidence must land first.
- Do not jump to allowlist surgery if blocked evolution decomposition can restore running work first.
