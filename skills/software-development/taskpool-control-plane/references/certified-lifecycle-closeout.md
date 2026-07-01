# Certified lifecycle closeout

Use when multimodel certification or review tooling writes a task to `status: certified` and ordinary lifecycle transition rejects it as an invalid current status.

## Durable lesson

Treat `certified` as a non-terminal lifecycle state, not as `done` and not merely as metadata, when the control plane actually writes it into the task's `status` field. It represents “ratified, still awaiting closeout evidence/audit.”

## Required state-model shape

- `VALID_STATUSES` includes `certified`.
- `ACTIVE_STATUSES` includes `certified`; `TERMINAL_STATUSES` does **not**.
- `STATUS_WEIGHT` includes `certified`, usually slightly below `review` so it does not outrank still-reviewing work.
- `LIFECYCLE_TRANSITIONS` includes:
  - `review -> certified`
  - `certified -> done|retry|blocked|archived|expired`
- `EVIDENCE_REQUIRED_TO` and profile/mission gated states include `certified` if review/certification advancement must remain proof-gated.
- `done` validation accepts `from_status in {"review", "certified"}`.
- Lifecycle history validation must also accept recorded `certified -> done` transitions; otherwise the closeout succeeds but later `lifecycle --json` reports a false invalid history.

## Regression checklist

Add or run a focused test that proves:

1. A fixture task with `status: certified` is recognized by list/read paths.
2. It is not dispatchable under normal dispatch rules unless dispatch explicitly supports certified work.
3. `transition --to done` with structured implementation/certification evidence succeeds.
4. The transition output reports `from_status=certified`, `to_status=done`, and `next_allowed=["archived"]`.
5. `lifecycle --json` passes after the recorded `certified -> done` transition.

## Commit hygiene pitfall

If a repository-wide pre-commit hook fails on an unrelated unstaged secret/config finding, first verify the staged file list is limited to the intended lifecycle files. Prefer fixing the unrelated finding separately; if the scoped lifecycle fix must land now, use an auditable `--no-verify` commit and record the exact reason in the project ledger. Do not stage or normalize unrelated config/secret files as part of lifecycle work.
