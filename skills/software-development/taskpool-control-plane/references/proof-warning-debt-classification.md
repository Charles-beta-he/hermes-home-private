# Proof warning debt classification

Applicability: `brain_task_orchestrator.py proof-check --json` returns `PASS` with many `terminal invalid autorun proof hash debt` warnings, especially after autorun proof-chain performance is already fixed. Anti-condition: do not use this to weaken `hermes-autorun review -> done` proof requirements or to mark tasks done.

## Classify before clearing warnings

1. Separate **true autorun closeout debt** from **artifact-label false positives**.
2. True autorun closeout debt has a body/audit line like:
   - `Lifecycle transition `review` -> `done` by `hermes-autorun` ...`
3. Artifact-label false positives are done tasks that merely carry `proof:sha256:<label>=<digest>` evidence from another proof system, but were not closed by `hermes-autorun`.
4. Only class (3) is safe to fix in `proof-check` logic. Class (2) must remain visible until the append-only autorun proof log/readback validates it or the task gets explicit evidence repair.

## Durable code invariant

`task_has_autorun_audit(task)` should detect the actual autorun-originated closeout audit line, not infer autorun context from any `proof:sha256:` evidence entry.

Bad heuristic:

```py
if any(str(e).startswith("proof:sha256:") for e in evidence):
    return True
```

Good heuristic:

```py
return any(
    "Lifecycle transition `review` -> `done`" in line and "by `hermes-autorun" in line
    for line in task.body.splitlines()
)
```

## Regression test pattern

Add a fixture task with:

- `status: done`
- evidence containing `proof:sha256:artifact_bundle=deadbeef`
- deterministic non-autorun evidence, e.g. `command: deterministic closeout PASS`
- `## Proof Log` and `## Final Handoff`
- no `review -> done by hermes-autorun` body line

Expected result:

```text
proof-check --json => status PASS
no warning contains "terminal invalid autorun proof hash debt"
```

Keep companion coverage that real `hermes-autorun` closeout still requires a valid `proof:<sha256:...>` from the append-only proof log.

## Verification loop

- Run the new focused regression plus existing autorun proof-gate tests.
- Run `py_compile` on orchestrator and test file.
- Run full orchestrator suite when changing proof semantics.
- Run live `proof-check --json` and record warning count before/after.

Expected safe effect: warning debt can drop by removing false positives, while real autorun proof debt remains as warnings/failures according to existing policy.
