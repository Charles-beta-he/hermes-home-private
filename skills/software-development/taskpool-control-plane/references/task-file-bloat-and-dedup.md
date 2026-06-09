# Task File Bloat and Dedup Patterns

## YAML Frontmatter Escaping Explosion

**Symptom:** Task files grow from ~10KB to 7-60MB unexpectedly.

**Root cause:** The `evidence_bundle` field in YAML frontmatter stores URLs and references. When YAML serialization layers compound backslash escaping, a 50-char URL becomes several KB:
- Layer 1: `https://example.com/path` → `https://example.com/path`
- Layer 2: `https://example.com/path` → `https:\\example.com\\path`
- Layer 3: `https://example.com/path` → `https:\\\\example.com\\\\path`
- Layer 4+: exponential growth

**Detection:**
```bash
find ~/Documents/brain/05-实践与项目/tasks -name "*.md" -size +100k -exec ls -lh {} \;
```

**Fix approach:**
1. Read the file, strip excess escaping from `evidence_bundle`
2. Use `yaml.safe_load` to verify the field roundtrips correctly
3. Consider storing URLs as a YAML list of plain strings instead of a single escaped blob

**Example of bad field:**
```yaml
evidence_bundle: "https\\\\\\\\example.com\\\\\\\\path"
```

**Example of fixed field:**
```yaml
evidence_bundle:
  - "https://example.com/path"
  - "https://example.com/other"
```

## Brain Mirror Duplicate Creation

**Symptom:** Multiple task files with same title but numbered suffixes (`-2`, `-3`, `-4`, `-5`).

**Root cause:** Brain mirror script triggered multiple times (repeated cron, manual re-run) without checking if a file already exists for that task. The file naming uses title slugs without hash-based dedup.

**Detection:**
```bash
ls ~/Documents/brain/05-实践与项目/tasks/ | grep -E "(-[0-9]+\.md$)" | head -20
```

**Cleanup:**
```bash
# For each group of duplicates, keep the largest file
for base in $(ls *.md | sed 's/-[0-9]*\.md$//' | sort -u); do
    largest=$(ls -S ${base}*.md 2>/dev/null | head -1)
    for f in ${base}*.md; do
        [ "$f" != "$largest" ] && echo "Archive: $f"
    done
done
```

**Prevention:** Mirror script should check `existing_files_with_normalized_title` before creating new files. Enrich existing notes in-place.

## Kanban Worker Crash Loops

**Symptom:** Worker crashes 50-100+ times with repeated error message.

**Common causes:**
- Missing CLI credentials (`hermes auth` not configured)
- Required skill disabled in config (`kanban-worker` under `skills.disabled`)
- External service unavailable

**Detection:**
```bash
hermes kanban log t_XXXXXXXX | grep -c "not alive\|No.*credentials\|Unknown skill"
hermes kanban list --json | jq '.tasks[] | select(.consecutive_crashes > 10)'
```

**Fix:** Address the root cause (auth, config, service). Do NOT auto-enable expensive workarounds.
