# Envelope Bus Escape Triage — CLI Patterns

Supplementary to `envelope-bus-escape-triage.md`. These are direct `sqlite3` CLI
patterns that are faster than the Python snippets for ad-hoc diagnosis.

## Schema discovery

Always check the schema first — column names have drifted across controller versions:

```bash
sqlite3 ~/.hermes/state/envelope_bus.db ".schema envelopes"
```

Current schema (as of 2026-05):
```sql
CREATE TABLE envelopes (
    id TEXT PRIMARY KEY,
    type TEXT CHECK(type IN ('TASK','PLAN','RESULT','VALIDATION')),
    status TEXT CHECK(status IN ('PENDING','RUNNING','DONE','FAILED','SKIPPED','BLOCKED')),
    project TEXT,
    assignee TEXT,
    title TEXT,
    payload TEXT,
    trace TEXT,
    proof_sha TEXT,
    error TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    appetite_seconds INTEGER DEFAULT 1800,
    created_at TEXT,
    updated_at TEXT,
    started_at TEXT,
    completed_at TEXT
);
CREATE INDEX idx_status ON envelopes(status);
CREATE INDEX idx_type ON envelopes(type);
```

## Useful queries

### Status distribution (quick health overview)
```bash
sqlite3 -header -column ~/.hermes/state/envelope_bus.db \
  "SELECT status, count(*) as cnt FROM envelopes GROUP BY status;"
```

### Post-ack failures (the critical diagnostic)
Find what re-triggered escape after the last human ACK:

```bash
# Get the ack timestamp
cat ~/.hermes/state/envelope_escape_ack.json | python3 -c "import json,sys; print(json.load(sys.stdin)['acked_at'])"

# Query failures since that timestamp
sqlite3 -header -column ~/.hermes/state/envelope_bus.db \
  "SELECT id, type, status, project, title, error, retry_count, updated_at \
   FROM envelopes WHERE status='FAILED' \
   AND updated_at > '<ACKED_AT>' \
   ORDER BY updated_at DESC LIMIT 10;"
```

Replace `<ACKED_AT>` with the actual `acked_at` value.

**Important:** the escape check uses `coalesce(completed_at, updated_at)`, so a
task created before the ack but completing after it still counts as a post-ack
failure.

### Project-level failure clustering
Group post-ack failures by project to identify systemic worker issues vs random one-offs:

```bash
sqlite3 -header -column ~/.hermes/state/envelope_bus.db \
  "SELECT project, error, count(*) as cnt \
   FROM envelopes WHERE status='FAILED' \
   AND updated_at > '<ACKED_AT>' \
   GROUP BY project, error ORDER BY cnt DESC;"
```

### Diagnostic signal: project-level `missing_proof` clustering

If all post-ack failures cluster in **one project** with the **same error** (e.g.
`hermes-skill-learning` + `missing_proof`), the problem is **worker behavior for
that project**, not the controller or scheduler. Fix the worker before ACKing.

In the observed case (2026-05-28), 3 post-ack failures were all from
`hermes-skill-learning` with `missing_proof` — a systematic worker issue where
tasks executed but failed the proof gate. The controller and scheduler were
functioning correctly; the escape was legitimate worker-quality feedback.

Contrast with random failures across multiple projects, which may indicate
infrastructure issues (timeouts, network) that an ACK + retry could resolve.

## Pitfalls

- Column names have changed across versions. Always `.schema` first.
- `task_id` is NOT a column — the PK is `id` (a hash). Don't assume column names.
- The ack file is at `~/.hermes/state/envelope_escape_ack.json`, not in the DB.
- Historical FAILED rows are preserved for audit. Only the *counter* resets on ack.
