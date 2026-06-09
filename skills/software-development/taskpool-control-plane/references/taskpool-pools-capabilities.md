# Tenant-based taskpool governance

Use this reference when a Hermes kanban board has become a mixed pool and you need a durable separation between business/work tasks and self-evolution/validation tasks.

## Four-layer control-plane model

1. `tenant` = pool boundary
   - `work`: delivery tasks, Lark-derived tasks, prototype replication, business fixes
   - `validation`: non-work smoke tests, delegate validation, control-plane checks
   - `evolution`: Hermes self-improvement, workflow audits, control-plane hardening

2. `capability` = work contract
   - stable, small vocabulary such as `work-delivery`, `prototype-replication`, `self-evolution`, `delegate-validation`, `worker-bootstrap-validation`, `control-plane-smoke`
   - use for admission, retry policy, proof policy, and template choice

3. `assignee` / profile = execution lane
   - chooses runtime lane/profile characteristics
   - do not use assignee as the primary pool classifier

4. `skills` = execution procedures
   - reusable procedure bundles such as `kanban-worker`, `taskpool-control-plane`, `lark-task-reading`
   - do not use skills as the main routing key for pool membership

## Durable recommendation

Prefer `tenant` for pool separation before introducing new schema:
- `tenant=work`
- `tenant=validation`
- `tenant=evolution`

If `capability` is not yet a first-class DB column, keep it in task body frontmatter / template metadata first. Promote to schema only if reporting/querying pain justifies it.

## Why separate capability from skill

- capability answers: what kind of work contract is this?
- skill answers: how should the agent execute it?
- one capability can use many skills
- one skill can serve many capabilities

Conflating them causes brittle routing, naming drift, and mixed-pool contamination.

## Historical-task migration pattern

When a board already contains mixed tasks:
1. Query current counts by assignee/status and inspect a sample of titles/bodies.
2. Backfill `tenant` only with high-confidence heuristics.
3. Leave uncertain tasks as null rather than forcing a wrong classification.
4. Add audit events when retagging so migrations are reviewable.

## Operational interpretation of blocked states

Do not treat all blocked tasks as infrastructure failures.
- `Iteration budget exhausted` often indicates decomposition/replay governance, not control-plane breakage.
- `review-required` should remain blocked until the external human check is done.
- missing external prototypes/comment-thread-only inputs should be kept blocked as external-dependency tasks.

## Example high-confidence heuristics

Treat as `validation` when the task body clearly declares non-work validation/smoke intent.
Treat as `work` when the task text is dominated by product/prototype/comment-thread/UI-fix language.
Treat as `evolution` when the task is about Hermes workflow/control-plane/self-improvement.

Keep null when confidence is not high.