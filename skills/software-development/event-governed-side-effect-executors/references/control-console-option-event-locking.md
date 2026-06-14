# Control console option event locking

Use this reference when localhost/operator console cards offer choices such as Mission direction options or capability strategy buttons.

## Problem pattern

A UI can look interactive and even call a handler while still failing the governance model:

- Unauthorized clicks update React/local state and show “已选择”, even though no ledger event exists.
- Refresh clears the draft, so the user can select again and cannot tell what is canonical.
- The backend idempotency key only covers `(kind, targetId, option)`, so `(same targetId, different option)` appends a new row and silently turns the UI into “latest wins”.
- Snapshot readback exists, but alternate choices remain enabled after a recorded event.

This is not event-driven; it is local-draft-driven UI with a ledger bolted on.

## Correct event-driven shape

1. Treat the ledger/snapshot as the source of truth.
   - UI effective state should prefer `snapshot.optionDecisions.latestByTarget[targetKey]` over local pending state.
   - Local pending state is only allowed while an authorized record request is in flight.

2. Unauthorized clicks must not render as selected.
   - Show a global/status explanation such as “未授权，未记录选择”.
   - Do not add an inline “已选择” receipt for an unrecorded click.

3. Recorded choices lock the target by default.
   - After readback, render “已记录: <option>” and “已读回: <closedLoop> · <readbackSource>”.
   - Disable alternate buttons and expose a title/tooltip explaining that switching requires an explicit override event.

4. Backend conflict rule:
   - Idempotent replay of the same `(kind, targetId, option)` returns the existing record.
   - A different option for the same `(kind, targetId)` returns `409 option_already_recorded` with the existing record.
   - Do not allow silent append-and-latest-wins semantics.

5. Override is a new event type, not a button re-enable.
   - Future override should require exact `targetId`, existing `recordKey`, old option, new option, actor, reason, and confirm phrase.
   - Snapshot should expose superseded vs active record explicitly.

## Minimal test matrix

- Unauthorized option click/record is rejected and does not create local “selected” UI state.
- Authorized first option records successfully and appears in ledger + snapshot.
- Exact replay is idempotent and does not duplicate ledger rows.
- Same target with a different option is rejected with `option_already_recorded`.
- UI renders recorded choice from snapshot and disables alternate choices.
- Full verify plus browser/resident probe confirms readback and unarmed final state.
