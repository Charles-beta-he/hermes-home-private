# Safe Taskpool Smoke Verification

Scope: applies when verifying `product-workflow-operating-system` taskpool ingest, execution-flow gates, or writeback/closeout behavior with local smoke workspaces.

## Durable lesson

Hermes command safety scanning can block shell snippets that pipe dynamic data into an interpreter, even when the intent is only JSON parsing. Avoid patterns like:

```bash
printf '%s' "$JSON" | python3 -c 'import json,sys; ...'
```

The scanner may classify this as high-risk `pipe to interpreter`. For smoke tests, use file-backed JSON instead.

## Safer pattern

1. Write each tool/script JSON result to a temp file.
2. Run Python against file paths, not stdin pipes.
3. Keep `rm -rf` scoped to `/tmp/<specific-smoke-dir>` only.
4. Export test-only env vars explicitly:
   - `HERMES_BRAIN_VAULT=/tmp/<smoke>/brain`
   - `HERMES_DAILY_REPORT_INGEST_STATE=/tmp/<smoke>/state.json`
   - `HERMES_DAILY_REPORT_MANUAL_REQUESTS=/tmp/<smoke>/manual.jsonl`
   - `HERMES_TASKPOOL_EVENT_HOOK_DISABLED=1`
5. Assert both frontmatter propagation and execution-flow gate behavior.

Example parser pattern:

```bash
python3 scripts/product_workflow_taskpool_ingest.py --workspace "$WORKSPACE" --json > "$TMP/dry.json"
python3 scripts/product_workflow_taskpool_ingest.py --workspace "$WORKSPACE" --write --json > "$TMP/write.json"
python3 - "$TMP/dry.json" "$TMP/write.json" <<'PY'
import json, sys
from pathlib import Path

dry = json.loads(Path(sys.argv[1]).read_text())
write = json.loads(Path(sys.argv[2]).read_text())
assert dry["status"] == "OK"
assert write["created_count"] == 1
PY
```

## What to verify

For product workflow → taskpool → execution-flow bridge tests, verify:

- candidate fields survive ingest into task frontmatter:
  - `workflow_stage`
  - `completion_boundary`
  - `harness_surfaces`
  - `required_artifacts`
  - `external_side_effects`
- `execution-flow-dry-run` classifies writeback/external side-effect tasks as gated.
- `dispatch-dry-run` does not emit claim/execution prompts for hard boundaries.
- no real external writeback, publish, payment, or user-account mutation occurs in smoke tests.
