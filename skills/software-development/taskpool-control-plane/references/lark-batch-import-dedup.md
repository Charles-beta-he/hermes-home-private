# Lark Batch Import Deduplication

## Problem

Batch-importing Lark tasks (via `uvisa_lark_task_add_to_brain.py` or similar scripts) creates duplicate task entries when the same script is run multiple times. The file naming scheme uses title slugs with numeric suffixes (`-2`, `-3`), so repeated imports produce numbered copies of the same Lark task.

## Detection

Duplicate Lark tasks share the same `lark_task_guid` in their evidence/frontmatter but have different file suffixes:

```bash
# Find all task files with Lark GUIDs
grep -rl "lark_task_guid:" ~/Documents/brain/05-实践与项目/tasks/ | while read f; do
  guid=$(grep -oP 'lark_task_guid: \K[a-f0-9-]+' "$f" | head -1)
  echo "$guid $f"
done | sort | awk '{print $1}' | uniq -d
```

Or programmatically:

```python
from collections import Counter
guid_counter = Counter()
for f in tasks_dir.glob("*.md"):
    content = f.read_text()
    for line in content.split('\n'):
        if 'lark_task_guid' in line:
            guid = line.split('lark_task_guid:')[1].strip().split()[0].strip('"[]')
            if guid:
                guid_counter[guid] += 1

duplicates = {g: c for g, c in guid_counter.items() if c > 1}
```

## Cleanup Strategy

**Priority order for which copy to keep:**
1. `review` status (has work progress / evidence)
2. `claimed` / `running` status (active work)
3. `pending` status (most recent, or most content)

**Archive the rest** using `brain_task_orchestrator.py transition`:

```bash
python3 ~/.hermes/scripts/brain_task_orchestrator.py transition <duplicate-id> --to archived --actor hermes --reason "duplicate of <kept-id> (same lark_task_guid)" --json
```

## Prevention

The import script should check for existing task files with matching `lark_task_guid` before creating new ones. When enriching existing notes (adding Lark metadata, comments), update in-place rather than creating a new file.

If the import script cannot be fixed, add a post-import dedup step:

```python
# After import, check for GUID duplicates and archive extras
import re
from pathlib import Path

tasks_dir = Path.home() / "Documents/brain/05-实践与项目/tasks"
guid_map = {}  # guid -> [(file, status, content_length)]

for f in sorted(tasks_dir.glob("*.md")):
    content = f.read_text()
    match = re.search(r'lark_task_guid:\s*\[?"?([a-f0-9-]+)', content)
    if match:
        guid = match.group(1)
        status = "pending"
        for line in content.split('\n'):
            if line.startswith('status:'):
                status = line.split(':')[1].strip()
                break
        guid_map.setdefault(guid, []).append((f.name, status, len(content)))

# Keep best copy per GUID, archive rest
STATUS_PRIORITY = {"review": 0, "claimed": 1, "running": 1, "blocked": 2, "pending": 3}
for guid, copies in guid_map.items():
    if len(copies) <= 1:
        continue
    copies.sort(key=lambda x: (STATUS_PRIORITY.get(x[1], 99), -x[2]))
    keep = copies[0]
    for dup in copies[1:]:
        # Archive via brain_task_orchestrator.py transition
        print(f"ARCHIVE: {dup[0]} (duplicate of {keep[0]}, guid={guid})")
```

## Relationship to Other Dedup Patterns

- **Brain mirror dedup** (existing section in SKILL.md): Covers `brain_task_orchestrator.py mirror-to-kanban` creating duplicates from repeated cron triggers. Same root cause (no GUID-based dedup check) but different source.
- **Title-slug dedup** (existing): Covers tasks with identical title slugs. Lark tasks may also have title duplicates, but GUID is the canonical dedup key.
- **This pattern**: Specifically about Lark batch import where `lark_task_guid` is the authoritative identity.
