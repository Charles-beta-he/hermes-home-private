# Read-only control-console projections over agent ledgers

Use when turning Hermes/taskpool/Mission/control-plane ledgers into a user-facing dashboard/control console.

## Pattern

1. Treat the ledger as the only fact source.
   - Mission/taskpool/cron DBs remain canonical.
   - Console snapshots are projections, not a second truth.
   - UI actions start as proposals/decision drafts until a governed write boundary exists.

2. Keep first integration read-only.
   - Open SQLite ledgers with `file:<db>?mode=ro` and `uri=True`.
   - Set `PRAGMA query_only = ON`.
   - Avoid importing store classes whose constructors may initialize/migrate/write schemas.
   - Mark snapshot safety explicitly, e.g. `writesAllowed=false`, `controlActionsAllowed=false`, `missionStoreReadOnly=true`.

3. Redact static/public snapshots.
   - A file under `public/` or static web assets must be treated as shareable, even if intended for localhost.
   - Do not dump raw `payload_json`, evidence bodies, paths, command transcripts, secrets, model context, or full adapter responses.
   - Whitelist only fields needed for operation: status/counts, truncated direction/summary, next_step, needs_user, compact risks/evidence references.
   - Truncate long user/domain strings before writing JSON.

4. Quote generated shell commands.
   - If the UI displays a CLI command derived from ledger/user data, shell-quote every dynamic token with `shlex.quote` or equivalent.
   - Prefer structured fields plus a command draft; never execute from the UI in the read-only phase.

5. Human-inbox integration.
   - Map open decisions into approval-request cards with: question, options, recommended option, evidence summary, multi-model advice, and exact decide command draft.
   - Button clicks in the read-only phase should create local/draft feedback only, not mutate the ledger.

6. Visual verification must not hide the product.
   - Do not satisfy browser harness overlap checks by globally hiding important labels/cards.
   - Fix layout/avoidance or apply viewport-specific degradation while preserving desktop/spacious information density.
   - Add contract tests for both safety behavior and visual affordances.

## Verification

Run both data and UI gates before claiming the console is usable:

```bash
python3 -m py_compile scripts/generate_hermes_dashboard.py scripts/test_ui_contract.py
pnpm test:graph
pnpm test:ui
pnpm snapshot
pnpm lint
pnpm build
pnpm test:browser
```

Then open the console and verify:

- Mission/control-plane section is visible.
- Real ledger counts/status/direction/next step are shown.
- Browser console has no JavaScript errors.
- Snapshot safety flags reflect read-only behavior.
- Any event payload keys are in the explicit whitelist.

## Failure modes

- Raw ledger payload leakage into static JSON while claiming `redacted=true`.
- CLI command injection via unquoted decision option/recommendation text.
- UI writes ledger state before the event-governed write boundary exists.
- Browser harness passes only because major labels were hidden.
