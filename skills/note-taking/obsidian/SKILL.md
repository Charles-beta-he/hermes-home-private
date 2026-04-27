---
name: obsidian
description: Read, search, and create notes in the Obsidian vault.
---

# Obsidian Vault

**Location:** `~/Documents/brain/` (set via `OBSIDIAN_VAULT_PATH` env var in env.sh)

Note: Vault paths may contain spaces - always quote them.

### Setting the vault path

Quick (per-session):
```bash
export OBSIDIAN_VAULT_PATH="$HOME/Documents/Obsidian Vault"
```

Persistent (save to skill directory):
```bash
cat > ~/.hermes/skills/note-taking/obsidian/env.sh << 'EOF'
export OBSIDIAN_VAULT_PATH="$HOME/Documents/Obsidian Vault"
EOF
# source ~/.hermes/skills/note-taking/obsidian/env.sh
```

Or use the default path with no configuration.

## Read a note

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Documents/Obsidian Vault}"
cat "$VAULT/Note Name.md"
```

## List notes

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Documents/Obsidian Vault}"

# All notes
find "$VAULT" -name "*.md" -type f

# In a specific folder
ls "$VAULT/Subfolder/"
```

## Search

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Documents/Obsidian Vault}"

# By filename
find "$VAULT" -name "*.md" -iname "*keyword*"

# By content
grep -rli "keyword" "$VAULT" --include="*.md"
```

## Create a note

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Documents/Obsidian Vault}"
cat > "$VAULT/New Note.md" << 'ENDNOTE'
# Title

Content here.
ENDNOTE
```

## Append to a note

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Documents/Obsidian Vault}"
echo "
New content here." >> "$VAULT/Existing Note.md"
```

## Bidirectional Sync Workflow

For keeping Hermes notes and Obsidian Vault in sync:

### Push (Hermes → Obsidian)

```bash
python3 ~/.hermes/scripts/sync-to-obsidian.py
```

This copies files from `~/.hermes/notes/` to `~/Documents/Obsidian Vault/` according to a sync map.

### Pull (Obsidian → Hermes)

When the user edits notes in Obsidian and you need to read those changes back:

```bash
python3 ~/.hermes/scripts/obsidian-watch.py
# Or run as daemon for continuous monitoring:
# python3 ~/.hermes/scripts/obsidian-watch.py --daemon
```

The watcher tracks `mtime` of watched files and syncs changes back to `~/.hermes/notes/`.

### Automation

Register a cronjob to auto-push daily:
```yaml
schedule: "0 */6 * * *"
prompt: "Run python3 ~/.hermes/scripts/sync-to-obsidian.py"
```

## Wikilinks

Obsidian links notes with `[[Note Name]]` syntax. When creating notes, use these to link related content.

## Pitfalls

### System credential files are write-protected

The agent cannot write to protected system files under `~/.hermes/`. If environment persistence is needed, use `env.sh` in the skill directory instead:
```bash
cat > ~/.hermes/skills/note-taking/obsidian/env.sh << 'EOF'
export OBSIDIAN_VAULT_PATH="$HOME/Documents/Obsidian Vault"
EOF
chmod +x ~/.hermes/skills/note-taking/obsidian/env.sh
# source ~/.hermes/skills/note-taking/obsidian/env.sh
```
