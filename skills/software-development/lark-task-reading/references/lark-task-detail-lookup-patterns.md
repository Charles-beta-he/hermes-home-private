# Lark Task Detail Lookup Patterns

## Quick lookup via local matrix snapshot files

When you need task details for a specific GUID and the `lark_task_reader.py` CLI doesn't support `--task-guid` direct fetch, use the local matrix snapshot files as a fast lookup:

### Matrix snapshot locations
- `/tmp/c端-fasttrack-test/matrix.latest.json` — full JSON with all fields (guid, title, tier, fasttrack_status, page_batch, atoms, lark_final_close_status, escalation_required, shared_evidence_allowed)
- `/tmp/c端-fasttrack-test/matrix.latest.csv` — CSV format (guid, tier, page_batch, fasttrack_status, evidence_status, title)
- `/tmp/admin-old/matrix.latest.json` / `.csv` — older snapshot copy (same structure)

### Lookup by GUID
```bash
# JSON: search for GUID and read surrounding context (~20 lines)
grep -n '<GUID>' /tmp/c端-fasttrack-test/matrix.latest.json | head -5
# Then read_file with offset/limit to get the full task block

# CSV: one-liner with context
grep '<GUID>' /tmp/c端-fasttrack-test/matrix.latest.csv
```

### What matrix snapshots contain
Each JSON entry has:
- `guid` — Lark task GUID (same as lark_task_guid in taskpool)
- `title` — full task title/description
- `page_batch` — e.g. `admin-misc`, `wealth`, `user-detail`
- `tier` — `S`/`F`/`L`/`B` classification
- `fasttrack_status` — e.g. `blocked_missing_prototype_or_access`, `requires_backend_or_contract`
- `lark_final_close_status` — `not_closed`, `completed`, etc.
- `escalation_required` — boolean
- `shared_evidence_allowed` — boolean

### When to use this pattern
1. User shares a Lark task GUID/URL and wants quick task details
2. `lark_task_reader.py` CLI args don't support direct GUID fetch
3. Live Lark API auth is blocked (NO_TOKEN) but matrix snapshots exist
4. Need to classify/assess a task before deciding on implementation approach

### When NOT to use
- Need live comments or attached images → must use Lark API directly
- Need to check real-time status (may have changed since snapshot) → use API
- Snapshot files don't exist at the expected path → fall back to API

## Single task fetch via Lark API

When you need live data, use the Task API v2 single-task endpoint:

```
GET /task/v2/tasks/{guid}
```

Returns `data.task` directly. Use when:
- Paginated fetch times out
- Task is not in the incomplete task list
- Need real-time comments/attachments

See also: `references/lark-direct-task-fetch-by-guid.md`

## Prototype comparison workflow

For UI/UX tasks that reference prototype screenshots:
1. Look up task in matrix to get tier/status/title
2. Check the prototype data layer for matching templates:
   - `uvdemo2.0/uvisa-app/src/data/inAppTemplates.ts` — notification templates
   - `uvdemo2.0/uvisa-app/src/data/inAppMessages.ts` — mock messages
   - `uvdemo2.0/uvisa-app/src/data/mock.ts` — general mock data
3. Search the implementation codebase for the matching feature
4. Compare implementation vs prototype to identify gaps
5. If task is `blocked_missing_prototype_or_access` — the blocker is likely that prototype screenshots are in Lark comments (which may be `[Image]` placeholders in the API)
