# Manual task intake CLI pitfalls

Applicability: Hermes local brain/taskpool manual intake via `~/.hermes/scripts/brain_task_orchestrator.py add`, especially when adding one or more external-source/content-absorption tasks from a chat request.

## Required metadata gate

If `brain_task_orchestrator.py add` returns:

```text
task creation requires explicit priority/dependency/triage metadata; missing=['dependency_order', 'multimodel_triage_result']
```

Retry with explicit:

- `--dependency-order "<ordering value>"`
- `--multimodel-triage-result "single_model_ok: <reason>; verify with source/evidence when executing"`

Keep `--priority-layer` and `--dependency-order` aligned when the user supplied numeric ordering such as `0.25` / `5.61`.

## Timeout / partial-create guard

When adding multiple tasks in one shell command, a timeout can happen after an earlier task has already been created. Do not blindly retry the whole batch.

Safe sequence:

1. Run the missing-task check first:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py list --json > /tmp/taskpool_list.json
python3 - <<'PY'
import json
items=json.load(open('/tmp/taskpool_list.json')).get('tasks', [])
for t in items:
    title=str(t.get('title',''))
    if '<distinctive title substring>' in title:
        print(t.get('id'), t.get('status'), t.get('priority_layer'), t.get('dependency_order'))
PY
```

2. Retry only tasks that are absent.
3. If a duplicate was created, remove only the duplicate canonical note after checking both notes are equivalent.
4. Refresh derived taskpool views:

```bash
PYTHONPATH=~/.hermes/scripts python3 - <<'PY'
import brain_task_orchestrator as b
print(b.refresh_derived_task_views('manual-deduplicate'))
PY
```

5. Verify `任务池-排序.md` and `brain_task_orchestrator.py list --json` no longer show the duplicate.

## Anti-conditions

Do not turn transient hook/autorun warnings from the add result into durable negative claims about the taskpool. If the task file exists, derived views refresh, and `list --json` shows the expected pending task, intake succeeded even if a hook for an unrelated next task reports allowlist/safety no-op details.
