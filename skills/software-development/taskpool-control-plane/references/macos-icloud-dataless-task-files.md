# macOS/iCloud dataless duplicate task files

Applicability: taskpool/local-brain control-plane operations on macOS where task iteration or selfcheck crashes while reading Markdown task files with `OSError: [Errno 11] Resource deadlock avoided`.

Anti-condition: do not use this to ignore arbitrary parse/read errors, missing task files, corrupted canonical tasks, or non-macOS storage issues. Only fail-soft the specific dataless-placeholder `errno == 11` case, and preserve originals/receipts.

## Diagnosis

On macOS, cloud-backed storage can leave duplicate task files as compressed/dataless placeholders, often with a suffix like ` 2.md`. The canonical non-duplicated task file may still be readable, but a broad task iterator can crash when it reaches the placeholder.

Quick scan pattern:

```bash
python3 - <<'PY'
from pathlib import Path
TASKS_DIR=Path('/path/to/taskpool/tasks')
bad=[]
for path in sorted(TASKS_DIR.glob('*.md')):
    if path.name in {'00-tasks索引.md','任务收件箱.md','任务池-排序.md'}:
        continue
    try:
        path.read_text(encoding='utf-8')
    except OSError as e:
        if getattr(e, 'errno', None) == 11:
            bad.append(path)
print('\n'.join(map(str,bad)))
PY
```

## Safe repair pattern

- Do not delete original readable task files.
- If the filesystem allows it, move unreadable placeholders to a quarantine directory and write a receipt.
- If move/rename itself fails with Errno 11, patch the task iterator to skip only `OSError errno == 11` placeholders. This is fail-soft for unusable placeholders, not a general exception swallow.

Patch shape in the task iterator:

```python
try:
    text = path.read_text(encoding='utf-8')
except OSError as exc:
    if getattr(exc, 'errno', None) == 11:
        continue
    raise
```

## Verification

```bash
python3 -m py_compile /path/to/brain_task_orchestrator.py
python3 /path/to/brain_task_orchestrator.py selfcheck --json
```

Expected: selfcheck reaches PASS/FAIL normally instead of crashing. Existing semantic warnings may remain and should be handled separately.
