# Project Profile Dispatchability Gates

When `eligibility-check` returns `eligible=false` with `no_dispatchable_task` but tasks clearly exist and are `pending`, the cause is often a missing project-profile gate field — not a pool-empty condition.

## The `source_weighting_policy_ref` hard gate

`is_dispatchable()` in `brain_task_orchestrator.py` (~line 2396):

```python
# Source weighting policy gate: work lane + project tasks must have source_weighting_policy_ref
if self.lane == "work" and self.project and not str(self.fm.get("source_weighting_policy_ref") or "").strip():
    return False
```

This is **silent fail-closed** — no error message, no log entry, the task simply is not considered dispatchable.

### Required value

```yaml
source_weighting_policy_ref: ~/.hermes/project-profiles/<project>.json#source_weighting_policy
```

The value must point at the project profile file that defines `source_weighting_policy`. The `#source_weighting_policy` fragment anchors the reference to the specific section.

### Diagnosis sequence

1. `taskpool_dynamic_runner.py --json` → check `autorun_skipped_reason` and `summary.next_task_id`
   - If `next_task_id` is empty and `dispatchable: true`, the runner found no eligible task despite dispatchable tasks existing
2. `brain_task_orchestrator.py list --json` → check `dispatchable: false` on pending tasks
3. For each non-dispatchable pending task, check frontmatter for `source_weighting_policy_ref`
4. If missing, the gate is the cause
5. Verify the project profile exists: `~/.hermes/project-profiles/<project>.json`
6. Verify it contains `source_weighting_policy` section
7. Add the field to the task frontmatter

### Batch fix pattern

When many tasks are affected (e.g. after a project rename or bulk import):

```python
from pathlib import Path

tasks_dir = Path.home() / "Documents/brain/05-实践与项目/tasks"
ref = "~/.hermes/project-profiles/<project>.json#source_weighting_policy"

for f in tasks_dir.glob("*.md"):
    content = f.read_text()
    if "project: <project>" in content and "source_weighting_policy_ref:" not in content:
        new_content = content.replace(
            "project: <project>",
            f"project: <project>\nsource_weighting_policy_ref: {ref}"
        )
        f.write_text(new_content)
```

After batch fix, regenerate dashboard: `brain_task_orchestrator.py dashboard --write`

### Project rename cascade

When renaming a project (e.g. `uvisa-app-2.0` → `uvisa-app-2.0-work`):

1. **Update auto_run_allowlist**: `~/.hermes/state/auto_run_allowlist.json` must contain `project:<new-name>`
2. **Update task frontmatter**: all `project:` fields in task notes must match
3. **Update source_weighting_policy_ref**: must point at the correct project profile
4. **Verify project profile exists** under the new name (or an alias resolves)
5. **Regenerate dashboard**: `brain_task_orchestrator.py dashboard --write`
6. **Verify**: `eligibility-check --json` should return `eligible: true`

Missing any one of these produces a silent `no_dispatchable_task` result.

### Other `is_dispatchable()` gates

The full gate chain in `is_dispatchable()` (ordered):

1. `status in TERMINAL_STATUSES` → False
2. `is_expired(at)` → False
3. `status not in {"pending", "retry"}` → False
4. `claimed_by` / `claim_expires_at` / `run_id` set → False
5. `status == "retry"` and retry not due → False
6. `lane == "evolution"` and not architecture_aligned → False
7. `project_profile_failures(self)` → False
8. **`lane == "work"` + `project` + no `source_weighting_policy_ref` → False** ← this one
9. `mission_envelope` invalid → False
10. `mission_node_blockers` → False
11. `work_dispatch_blockers` → False

Gate 8 is the one most commonly hit after project renames or bulk imports because it has no error message and the field is not part of the basic `add` command output.
