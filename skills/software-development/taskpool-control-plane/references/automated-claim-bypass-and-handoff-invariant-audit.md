# Automated Claim-Bypass and Handoff-Invariant Audit

## Applicability

Use when reviewing a taskpool/controller patch that claims to make every automated path converge on one eligibility/claim authority, especially after adding a required handoff/envelope field.

Anti-conditions:

- Do not treat manual/operator-only low-level lifecycle commands as automated bypasses without proving an automated caller.
- Do not mutate live task state or run a real worker canary during a read-only review.
- Do not call an older pre-existing bypass “introduced by this patch”; distinguish pre-existing root cause from newly exposed regression.

## Audit procedure

1. Pin HEAD, status, changed files, and the acceptance/spec language. If the worktree changes during review, re-read affected functions and rerun focused tests before the verdict.
2. Enumerate automated claim callers across event hooks, cron/tick runners, batch coordinators, dynamic runners, hourly controllers, retry/reconcile paths, and background worker bridges. Search both direct low-level `claim` calls and wrappers such as `auto-claim-and-handoff` / `parallel-claim-and-handoff`.
3. Classify each caller:
   - candidate selection only;
   - exact-task eligibility projection;
   - mutating claim authority;
   - worker consumption / `claimed -> running`.
4. Compare every mutating automated path against the canonical single-task bridge. Check the complete sequence, not merely a function name:
   - autorun enablement and kill switches;
   - exact task identity and allowlist;
   - dispatchability and permission/certification gates;
   - selfcheck or equivalent global gate;
   - execution-flow/contract decision;
   - autonomy write guard;
   - claim readback;
   - handoff creation/readback;
   - fail-closed release on partial success.
5. Audit compound/batch paths separately. A parallel function that calls `eligibility-check` may still bypass later canonical stages such as execution-flow or selfcheck. A preceding dry-run is not authority for a later mutation unless the mutating command itself enforces the same decision.
6. Trace the data contract into the consumer. After making handoff non-empty mandatory, inspect every producer of `claimed_items`, including old batch coordinators. A legacy producer that still emits no handoff may now cause claim/retry churn even though the consumer correctly refuses `running`.
7. Inspect outer-process success semantics. Background spawn success is not worker acceptance: a coordinator must not report `claimed_and_worker_triggered` as operational success if the asynchronous consumer immediately rejects every item.
8. Verify with negative tests for each material bypass:
   - allowlist denied;
   - execution-flow denied;
   - selfcheck failed;
   - write guard denied;
   - claim succeeded but handoff empty/write failed;
   - legacy batch producer emits no handoff;
   - consumer rejection is reflected or cleaned up by the coordinator.
9. Report findings by severity and provenance: changed-code defect, pre-existing bypass still in scope, or regression newly exposed by the patch. Passing focused tests do not override an untested automated path.
10. Run a deterministic syntax-tree caller inventory over production controller files. Report every direct low-level mutation call and literal low-level claim argv, then classify each hit as canonical-bridge internals, operator/manual CLI dispatch, or automated bypass. Text search alone is insufficient because wrappers and constructed argv can hide call sites; AST inventory alone is also insufficient because it must be paired with controller-entrypoint tracing.
11. Re-read the exact changed functions and targeted status after tests. Concurrent control-plane worktrees are often dirty; a passing run against an earlier slice does not certify later edits.

### Deterministic caller-inventory pattern

Use a read-only AST probe over the bounded production file set (or adapt the set after entrypoint discovery):

```python
import ast
from pathlib import Path

for path in map(Path, production_controller_files):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func.id if isinstance(node.func, ast.Name) else (
            node.func.attr if isinstance(node.func, ast.Attribute) else ""
        )
        if fn == "command_claim":
            print(path, node.lineno, "direct command_claim")
        for arg in node.args:
            if isinstance(arg, (ast.List, ast.Tuple)):
                values = [
                    item.value for item in arg.elts
                    if isinstance(item, ast.Constant) and isinstance(item.value, str)
                ]
                if "claim" in values:
                    print(path, node.lineno, f"literal claim argv in {fn}")
```

Interpretation rules:

- A direct low-level call inside the canonical single-task bridge is expected only after eligibility, selfcheck, execution-flow, write guard, and readback gates.
- A direct low-level call inside a parallel bridge is acceptable only when **all selected tasks are fully gated before the first mutation**, and the mutation loop still applies write guard/readback/handoff rollback.
- A CLI command dispatcher exposing a manual `claim` command is not an automated bypass unless an automated caller reaches it.
- Zero hits in outer controllers is useful negative evidence, but still trace event hooks, cron wrappers, dynamic runners, hourly controllers, and batch executors to their actual bridge.

## Subprocess denial and partial-success contract

Automated controller wrappers must parse structured stdout before reducing a child command to its process exit code. Canonical gates may intentionally exit non-zero while returning actionable JSON such as `reasons`, `warnings`, `eligible=false`, or a partial `claimed=true` result.

Safe wrapper order:

1. Attempt to parse non-empty stdout as structured JSON regardless of return code.
2. If parsing succeeds, preserve the gate's reasons and partial-success fields in the controller result.
3. If `claimed=true` but required handoff creation/readback failed, execute the explicit fail-closed release/retry path and expose whether that release succeeded.
4. Only fall back to truncated stderr/stdout text when no structured payload can be parsed.
5. Test both ordinary denial and non-zero structured denial; otherwise observability can regress while safety tests still pass.

Do not treat exit code `0` as proof of eligibility, claim, handoff, worker acceptance, or completion, and do not discard structured denial evidence solely because the child exited non-zero.

## Common failure pattern

A P0 patch can make the main controller safe while leaving a batch/tick coordinator on:

`fresh list -> dispatchable=true -> low-level claim -> consume-claimed`

If the consumer now requires a handoff, this path may no longer enter `running`, but it still violates canonical claim authority and can churn `pending/retry -> claimed -> retry`. Treat that as incomplete convergence, not as successful fail-closed completion.

## Verification checklist

- [ ] All automated low-level claim callers were enumerated, not only changed files.
- [ ] Every mutating path enforces the complete canonical gate inside the mutation boundary.
- [ ] Parallel/batch paths enforce execution-flow and selfcheck semantics, not only allowlist eligibility.
- [ ] Every claim producer emits the required handoff contract.
- [ ] Partial claim without handoff releases deterministically and exposes release failure.
- [ ] Background worker acceptance is read back rather than inferred from process spawn.
- [ ] Negative tests cover alternate controllers and legacy producers.
- [ ] Final line references and tests were refreshed after any concurrent worktree edit.
