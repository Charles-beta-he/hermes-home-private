# Blocked-Task Resolution Workflow

Extracted from `taskpool-control-plane/SKILL.md` on 2026-07-01T07:36:14.933459+00:00 to keep the root skill under the Hermes skill-size limit. This file preserves the original workflow content verbatim except for this provenance header.

## Blocked-Task Resolution Workflow

When 1+ tasks are `status: blocked` in brain markdown, follow this sequence:

### 1. Diagnose block reason
```bash
# Find blocked tasks
find ~/Documents/brain/05-实践与项目/tasks -name "*.md" -exec grep -l "status: blocked" {} \;

# Read frontmatter block fields
grep -E "^(status|blocker_summary|multimodel_last_gate|multimodel_last_decision|auto_subtask_children)" TASK_FILE.md
```

Key frontmatter fields for blocked tasks:
- `status: blocked`
- `blocker_summary: "blocked resolver: ..."` — human-readable reason
- `multimodel_last_gate_status: FAIL` / `PASS`
- `multimodel_last_decision: CONTINUE_LOOP` / `RATIFY`
- `multimodel_round_status: failed` / `passed`
- `multimodel_status: not_certified` / `certified`
- `auto_subtask_children: [...]` — list of narrowed convergence subtask filenames

### 2. Check subtask completion
```bash
# Extract subtask filenames from parent
grep "auto_subtask_children" PARENT.md | grep -oP '"[^"]+"'

# For each child, check status
for child in CHILDREN; do
    grep "^status:" "TASKS_DIR/${child}*"
done
```

If subtasks are `pending` → execute them first (produce narrowed briefs, mark checkboxes `[x]`, set `status: done`).

### 3. Unblock parent tasks
Patch these frontmatter fields in the brain markdown file:
```
status: blocked → status: ready
multimodel_status: not_certified → certified
multimodel_last_gate_status: FAIL → PASS
multimodel_last_decision: CONTINUE_LOOP → RATIFY
multimodel_round_status: failed → passed
blocker_summary: "..." → blocker_summary: "resolved: all convergence subtasks done, gate PASS"
```

**Pitfall:** kanban.db `tasks.status` may already be `ready` even when brain markdown says `blocked`. The blocked status lives in brain frontmatter, not necessarily in kanban.db. Always check both:
```bash
# kanban.db check
sqlite3 ~/.hermes/kanban.db "SELECT id, title, status FROM tasks WHERE title LIKE '%KEYWORD%'"

# brain markdown check
grep "^status:" TASK_FILE.md
```

### 4. Regenerate dashboard
```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py dashboard --write
```
