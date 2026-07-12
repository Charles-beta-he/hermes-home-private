# WorkspaceProjection → taskpool bridge boundary

Applicability:
- Use when connecting external workspace-projection packets, evidence DAGs, reflection readbacks, or Global Workspace/J-space-inspired gates to taskpool lifecycle, review, done, dashboard, or event-bridge surfaces.
- Use for class-level bridge design before opening any real lifecycle write-through.

Anti-conditions:
- Do not let a workspace projection replace the canonical taskpool/mission SSOT.
- Do not treat dashboard aggregate history as proof of the current task's effects.
- Do not open broad taskpool lifecycle writes from a packet validator alone.
- Do not use model judgment, reflection text, or multi-model consensus as completion-critical proof without objective evidence.
- Do not open external dispatch, publish/deploy/push, credentials/payment, destructive actions, worker spawn, or broad fan-out in the same slice.

## Required preflight before bridge work

1. Read the current task card and its mission envelope.
2. Read the workspace-projection source packet/schema/validator.
3. Identify exact event source(s): e.g. `task.status_changed`, `task.review_requested`, or a local projection-only ledger event.
4. Identify exact write surfaces:
   - read-only dashboard summary;
   - local workspace/event ledger;
   - exact taskpool lifecycle write-through only if separately authorized.
5. Define rollback/readback before editing:
   - file paths or task ids to read back;
   - command that proves no external side effect happened;
   - command that proves lifecycle write, if any, touched only the exact task.
6. Keep red lines in the card: no hidden-state access claim, no model-only proof, no external/deploy/credential/destructive/fan-out boundary crossing.

## Minimal safe progression

```text
projection packet validates
→ local workspace event ledger records current event
→ before_review / before_done gate checks objective evidence
→ read-only dashboard summarizes projection/gate/evidence health
→ only then consider exact taskpool write-through with receipt + readback
```

## When broad authorization is granted

Treat broad wording such as “authorize, advance everything blocked by permission” as permission to consume only already-scoped local/exact bridge rungs, not to infer external targets. For a WorkspaceProjection→taskpool bridge, a valid exact rung has all of:

- a current workspace id;
- one exact task id;
- accepted evidence refs or deterministic command evidence;
- no external dispatch/deploy/credential/payment/destructive/fan-out effect in the same slice;
- receipt events for every lifecycle transition;
- readback from both the task card and the workspace/event ledger.

Recommended exact local sequence:

```text
attach-task <workspace_id> --task-id <task_id>
→ taskpool-transition pending/claimed/running/review as appropriate
→ record current-workspace dashboard readback
→ close with deterministic selfcheck/test evidence if the task's done gate accepts it
→ on-event task.done to project workspace state closed
→ closure-packet and final selfcheck readback
```

If an artifact evidence ref is semantically correct but the taskpool `done` gate rejects it, do not force-close. Provide a recognized deterministic `command:` proof (tests/selfcheck/gate PASS) while retaining the artifact path in the Proof Log.

## Dashboard-history pitfall

Some local dashboards summarize all workspaces. A field such as `runtime_mutation=true` or `taskpool_lifecycle_write_executed=true` may describe a historical smoke workspace, not the current task.

When reporting dashboard readback, always include:
- current workspace id;
- current event refs or task id;
- whether `external_side_effects_executed` is true for the current slice;
- explicit negative evidence for boundaries not crossed;
- excluded claims for historical/aggregate fields.

## Completion claim checklist

Before moving a bridge task to review/done:
- [ ] Task card contains exact event source, write surface, rollback, and readback.
- [ ] Validator/unit tests prove model-only evidence cannot close completion-critical claims.
- [ ] Dangerous authority remains blocked unless exact target + rollback + readback is present.
- [ ] Dashboard output is read-only or clearly labels any historical mutation flags.
- [ ] Selfcheck has `failures: []` or blockers are recorded.
- [ ] Proof Log records real command output, not paraphrased intent.
