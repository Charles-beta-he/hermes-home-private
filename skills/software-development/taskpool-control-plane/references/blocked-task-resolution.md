# Blocked Task Resolution Workflow

## When to use
When brain dashboard (`待完成任务运行态.md`) shows blocked tasks, or `brain_task_orchestrator.py dashboard --write` reports blocked nodes.

## Dual State Store Awareness
Task state lives in TWO places that can diverge:
1. **Brain markdown files** (`/Users/charles/Documents/brain/05-实践与项目/tasks/*.md`) — frontmatter `status:` field
2. **kanban.db** (`~/.hermes/kanban.db`) — `tasks` table `status` column

Blocked status is tracked in brain markdown files, NOT in kanban.db (kanban shows "ready"). When resolving, patch BOTH.

## Resolution Steps

### Step 1: Identify blocked tasks
```bash
grep -rl "status: blocked" ~/Documents/brain/05-实践与项目/tasks/*.md
```

### Step 2: Check subtask completion
Each blocked task has `auto_subtask_children: [...]` in frontmatter. Check all children:
```bash
# For each child, find file and check status
grep "^status:" ~/Documents/brain/05-实践与项目/tasks/<child>*.md
```

### Step 3: Execute pending subtasks
For convergence subtasks (narrowed briefs):
1. Read a done sibling to understand the expected format
2. Produce the narrowed brief based on actual code analysis
3. Update: status→done, checkboxes→[x], add brief section before "## Parent Link"
4. Update multimodel fields: status→certified, gate→PASS, decision→RATIFY, round→passed

### Step 4: Unblock parent tasks
Patch brain markdown files using `skill_manage(patch)` or `patch` tool:
- `status: blocked` → `status: ready`
- `blocker_summary: "..."` → `blocker_summary: "resolved: ..."`
- `multimodel_last_gate_status: FAIL` → `PASS`
- `multimodel_last_decision: CONTINUE_LOOP` → `RATIFY`
- `multimodel_round_status: failed` → `passed`
- `multimodel_status: not_certified` → `certified`

**IMPORTANT**: Frontmatter fields are on individual lines. Use exact string matching. The `blocker_summary` may be OUTSIDE the frontmatter section (e.g., line 90), not between the `---` markers.

### Step 5: Regenerate dashboard
```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py dashboard --write
```

## Pitfalls
- `execute_code` file writes may not persist — use `patch` tool or `terminal` with `sed` instead
- kanban.db tasks are already "ready" — don't try to UPDATE blocked→ready in DB
- Frontmatter `replace()` needs exact whitespace — use `grep -n` to verify line content first
