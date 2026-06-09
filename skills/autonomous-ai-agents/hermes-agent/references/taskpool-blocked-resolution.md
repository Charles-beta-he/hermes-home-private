# Taskpool Blocked Resolution Workflow

When evolution lane tasks get stuck in `blocked` status, follow this workflow:

## Diagnosis

1. Find blocked tasks: `grep -l "status: blocked" brain/05-实践与项目/tasks/*.md`
2. Check block_reason in frontmatter: `blocker_summary` field
3. Check multimodel state: `multimodel_last_gate_status`, `multimodel_last_decision`
4. Find subtasks: `auto_subtask_children` field in frontmatter

## Resolution Steps

### Step 1: Execute pending subtasks
```bash
# Find subtask files
grep "auto_subtask_children" <parent-task>.md
# Check each subtask status
grep "^status:" <subtask-file>.md
```

For pending subtasks:
- Read acceptance criteria
- Produce narrowed brief (code-grounded analysis)
- Mark checkboxes [x], update status to done
- Update multimodel fields: status=certified, gate=PASS, decision=RATIFY

### Step 2: Unblock parent tasks
```bash
# Patch brain task file
patch <file> "status: blocked" → "status: ready"
patch <file> "multimodel_last_gate_status: FAIL" → "PASS"
patch <file> "multimodel_last_decision: CONTINUE_LOOP" → "RATIFY"
patch <file> blocker_summary → "resolved: all convergence subtasks done, gate PASS"
```

### Step 3: Update kanban.db
```python
conn.execute("UPDATE tasks SET status='ready' WHERE title LIKE ? AND status='blocked'", (pattern,))
```

### Step 4: Regenerate dashboard
```bash
python3 scripts/brain_task_orchestrator.py dashboard --write
```

## Pitfalls

- Brain file status can revert if dashboard regen runs before patch persists — always patch THEN regen
- Kanban titles may differ from brain filenames — use LIKE patterns, not exact match
- `multimodel_status: not_certified` vs `certified` — update both fields together
- Subtask files use glob patterns with wildcards — `glob.glob(f"{base}{child}*")` not exact path
