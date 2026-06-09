# Event-governed agent authority ladder reference

Use this reference when extending Hermes-managed worker/external-agent authority from read-only evidence toward canonical lifecycle mutation and adapter write-through.

## Reusable invariant

Advance one authority rung per scoped slice. Each slice must have:

- RED test for the new accept/reject contract.
- GREEN implementation for only that rung.
- CLI smoke that walks the full ladder up to the new rung.
- Explicit ledger booleans such as `write_executed=false`, `fact_is_canonical=true`, or `readback_verified=true`.
- SSOT/design doc update in the same scoped commit.

Do not combine certification, fact mutation, adapter intent, authorization, write-through, read-back, and rollback into one change.

## Ladder shape

1. Start a runtime run in the ledger only.
2. Accept builtin/read-only execution results.
3. Probe external agent process/version only.
4. Send no-tool/no-write prompt dry-run.
5. Pass read-only context as artifact URI/hash.
6. Record external worker output as proposal artifact only.
7. Promote proposal through multi-model/human certification with quorum/truth-gate/evidence binding.
8. Project elevated done authorization with actor, decision, TTL, target status, and certification hash binding; do not mutate facts yet.
9. Consume the unexpired authorization in a separate ledger-local fact mutation; append canonical lifecycle fact.
10. Project adapter write intent only after canonical fact exists; require adapter allowlist, readiness check, readback plan, rollback plan, and evidence.
11. Project external write authorization only against unchanged intent/ref/status/digests and valid TTL; record `write_executed=false`.
12. Add a narrow executor last. For the first executor, prefer a local-file harness: consume one authorization, write one target status, read back, record verified/mismatch, and keep real adapters disabled.

## Local-file adapter harness pattern

Use a JSON state file shaped like:

```json
{
  "tasks": {
    "task:example": {"status": "review"}
  }
}
```

Execution request should include:

- `authorization_id`
- `intent_id`
- `adapter`
- `target_ref`
- `target_status` = `done`
- `adapter_state_path`
- optional `expected_previous_status`
- non-empty `evidence_refs`

After execution, read the same file back and require `tasks[target_ref].status == target_status` before recording `external_adapter_write_verified`.

## Required rejection coverage

Cover these as tests before merging a rung:

- Missing prior rung record.
- Expired TTL where the rung consumes an authorization.
- Adapter/ref/status/hash/digest drift.
- Worker/model payload containing authority-smuggling keys (`external_write`, `write_through_enabled`, `mark_done`, `lifecycle_status`, `task_status`, `memory_write`, `skill_patch`, `send_message`, provider/config changes).
- Missing evidence refs.
- Duplicate execution: same authorization/intent/target should be idempotent, not append another verified write.

## Boundary language

When reporting progress, distinguish these states precisely:

- Proposal recorded is not fact.
- Certification is not fact.
- Authorization is not execution.
- Intent is not execution.
- Local-file harness write-through is real state mutation, but not a real taskpool/Kanban/Lark/Telegram write.
- Real adapter write-through requires adapter-specific readiness, execution, read-back, and rollback policy slices.
