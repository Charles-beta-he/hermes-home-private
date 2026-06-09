# Brain Task File Patching Guide

## YAML Frontmatter Fields

Brain task files (`/Users/charles/Documents/brain/05-实践与项目/tasks/*.md`) use YAML frontmatter between `---` markers. Key fields for status management:

```yaml
status: blocked | ready | done | archived
blocker_summary: "reason string"
multimodel_status: not_certified | certified
multimodel_last_gate_status: FAIL | PASS
multimodel_last_decision: CONTINUE_LOOP | RATIFY
multimodel_round_status: failed | passed
multimodel_last_checked_at: ISO timestamp
```

## Patching Technique

1. **Find exact line**: `grep -n "field_name" task_file.md` — some fields are outside frontmatter (e.g., `blocker_summary` at line 90+)
2. **Use exact string match**: `patch(old_string="exact line content", new_string="new content")`
3. **Verify after patch**: `grep -E "^status:|^blocker_summary:|^multimodel" task_file.md`

## Common Operations

### Unblock a task
```python
patch(path, "status: blocked", "status: ready")
patch(path, 'blocker_summary: "old reason"', 'blocker_summary: "resolved: all subtasks done"')
patch(path, "multimodel_last_gate_status: FAIL", "multimodel_last_gate_status: PASS")
patch(path, "multimodel_last_decision: CONTINUE_LOOP", "multimodel_last_decision: RATIFY")
patch(path, "multimodel_round_status: failed", "multimodel_round_status: passed")
patch(path, "multimodel_status: not_certified", "multimodel_status: certified")
```

### Mark subtask done
```python
patch(path, "status: pending", "status: done")
# Also update checkboxes in body
patch(path, "- [ ] Acceptance criteria text", "- [x] Acceptance criteria text")
```

## Pitfalls

- `blocker_summary` may be at line 90+, not in the YAML frontmatter block (lines 1-30)
- `multimodel_last_failures` is a JSON array — don't try to patch inline
- Kanban.db and brain markdown are separate systems — always check both
- Frontmatter fields are case-sensitive
