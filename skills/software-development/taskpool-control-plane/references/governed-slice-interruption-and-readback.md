# Governed taskpool slice interruption and readback

Use this when a taskpool/control-plane improvement is being landed in small verified slices and a verification/readback command is interrupted or blocked by the runtime safety layer.

## Class-level lesson

A blocked verification command is not evidence that the implementation failed, but it is a hard boundary for that command shape. Do not retry the same command, rephrase it, or route around it just to produce a prettier summary. Preserve the evidence already gathered, stop at the smallest real gate, and request an explicit authority grant for the next distinct action.

## Recommended loop

1. **Freeze the slice boundary**
   - Identify which slice was being closed (for example: read-only debt ledger, parser hardening, continuation dry-run).
   - List files touched and the exact verification commands that already passed.
   - Separate implementation proof from the blocked readback/summarizer command.

2. **Classify the blocked command**
   - If the safety layer says not to retry/rephrase/attempt the same outcome, treat that exact verification path as closed.
   - Do not infer that other already-completed tests are invalid.
   - Do not proceed to commit or the next slice unless the user grants a distinct next action.

3. **Emit a compact intervention packet**
   - Requested authority: e.g. “skip the blocked summarizer and commit based on existing test/selfcheck/proof evidence.”
   - Blast radius: local files only / scoped commit / no task lifecycle mutation / no cron side effect.
   - Rollback: git revert or restore listed files.
   - Verification after resume: run already proven focused tests, py_compile, selfcheck/proof-check, then commit readback.

4. **On resume**
   - Treat explicit user authorization as permission to continue the governed slice; do not over-avoid or re-litigate already authorized low-risk local work.
   - Prefer the smallest distinct safe action that preserves evidence and avoids the previously blocked command shape, such as scoped commit, full readback already produced, or next-slice discovery.
   - If the user explicitly authorizes retrying through tool friction, a distinct readback implementation is acceptable; still stop at irreversible writes/deletes/state migration or a second safety boundary.
   - If a later command is blocked again without a new distinct authorization, stop rather than accumulating partial retries.

## Pitfalls

- **Pretty-summary trap**: piping a large JSON ledger through a one-liner summarizer can become the weakest link. If full ledger output and focused tests already proved the slice, do not keep chasing a compact summary.
- **Commit-after-block trap**: even for local commits, if the block happened during final verification/readback, pause before commit unless the user explicitly authorizes committing from the evidence already collected.
- **False downgrade trap**: do not call the whole implementation inconclusive when only a post-verification summarizer was blocked. Report the exact boundary.
- **Authorization-blindness trap**: once the user explicitly says the action is authorized, do not keep treating prior tool friction as a blanket refusal. Continue within the governed blast radius and reserve stops for genuinely irreversible operations or fresh evidence boundaries.
- **Irreversible-boundary trap**: explicit “continue” authorization for implementation slices does not automatically authorize deleting archives, rewriting historical task notes, or migrating live projections. Convert those into dry-run manifests and stop for a human gate.

## Evidence bundle shape

For the final report or commit note, include:

- focused test result;
- `py_compile` result for changed scripts;
- taskpool `selfcheck --json` / `proof-check --json` status if run;
- one full readback or previously captured ledger output if available;
- explicit note that no lifecycle mutation, cron job run, deletion, or proof migration occurred unless separately authorized.
