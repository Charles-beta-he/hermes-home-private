---
name: obsidian
description: Read, search, and create notes in the Obsidian vault.
---

# Obsidian Vault

**Current canonical local brain:** `~/Documents/brain/` (override with `HERMES_BRAIN_VAULT` or `OBSIDIAN_VAULT_PATH` when needed).

Legacy/narrow-sync vault may still exist at `~/Documents/Obsidian Vault`, but do not treat it as canonical unless the user explicitly asks.

Note: Vault paths may contain spaces - always quote them.

### Current control plane

Use `brainctl.py` first; it keeps filesystem fallback available even when Obsidian is not installed/running:

```bash
python3 ~/.hermes/scripts/brainctl.py --json status
python3 ~/.hermes/scripts/brainctl.py --json reindex
python3 ~/.hermes/scripts/brainctl.py --json search "query" --limit 10
python3 ~/.hermes/scripts/brainctl.py --json evidence "query" --limit 10
python3 ~/.hermes/scripts/brainctl.py --json wal --tail 20
python3 ~/.hermes/scripts/brainctl.py --json sync
```

Derived indexes live under `~/.hermes/memory/` and are rebuildable caches; `~/Documents/brain` remains the truth source.

### Official Obsidian CLI

Obsidian has an official CLI in recent versions, but this machine may not have the `obsidian`/`obsidian-cli` binary installed. Treat it as optional: detect it first and fall back to Markdown filesystem operations.

Safe default capabilities: read/create/append/search/backlinks/tags/properties/tasks/open. Do not expose destructive or executable operations (`delete`, `eval`, arbitrary `command`, plugin install/enable/disable) without explicit scope and whitelist.

### Setting the vault path

Quick (per-session):
```bash
export HERMES_BRAIN_VAULT="$HOME/Documents/brain"
export OBSIDIAN_VAULT_PATH="$HOME/Documents/brain"
```

Persistent (save to skill directory):
```bash
cat > ~/.hermes/skills/note-taking/obsidian/env.sh << 'EOF'
export HERMES_BRAIN_VAULT="$HOME/Documents/brain"
export OBSIDIAN_VAULT_PATH="$HOME/Documents/brain"
EOF
# source ~/.hermes/skills/note-taking/obsidian/env.sh
```

## Read a note

```bash
VAULT="${HERMES_BRAIN_VAULT:-${OBSIDIAN_VAULT_PATH:-$HOME/Documents/brain}}"
cat "$VAULT/Note Name.md"
```

## List notes

```bash
VAULT="${HERMES_BRAIN_VAULT:-${OBSIDIAN_VAULT_PATH:-$HOME/Documents/brain}}"

# All notes
find "$VAULT" -name "*.md" -type f

# In a specific folder
ls "$VAULT/Subfolder/"
```

## Search

```bash
VAULT="${HERMES_BRAIN_VAULT:-${OBSIDIAN_VAULT_PATH:-$HOME/Documents/brain}}"

# By filename
find "$VAULT" -name "*.md" -iname "*keyword*"

# By content
grep -rli "keyword" "$VAULT" --include="*.md"
```

## Create a note

```bash
VAULT="${HERMES_BRAIN_VAULT:-${OBSIDIAN_VAULT_PATH:-$HOME/Documents/brain}}"
cat > "$VAULT/New Note.md" << 'ENDNOTE'
# Title

Content here.
ENDNOTE
```

## Append to a note

```bash
VAULT="${HERMES_BRAIN_VAULT:-${OBSIDIAN_VAULT_PATH:-$HOME/Documents/brain}}"
echo "
New content here." >> "$VAULT/Existing Note.md"
```

## Bidirectional Sync Workflow

For keeping Hermes notes and the canonical local brain in sync:

### Bidirectional sync (recommended)

```bash
python3 ~/.hermes/scripts/brainctl.py --json sync
# or directly:
python3 ~/.hermes/scripts/sync-brain.py
```

This mirrors `~/.hermes/notes/` ↔ `~/Documents/brain/` while keeping `~/Documents/brain` as the human-readable canonical vault and `~/.hermes/memory/index.sqlite` as a rebuildable derived index.

Before large or unfamiliar syncs, run status first and keep local git/snapshot evidence:
```bash
python3 ~/.hermes/scripts/brainctl.py --json status
python3 ~/.hermes/scripts/sync-brain.py --status
```
Treat sync output as an audit artifact; if there are unexpected pushed/pulled counts, inspect diffs before committing further local-brain changes.

### Legacy narrow sync

`sync-to-obsidian.py` and `obsidian-watch.py` still exist for the old/narrow `~/Documents/Obsidian Vault` workflow. Do not use them for canonical local-brain work unless the user explicitly asks for the legacy vault.

### Automation

Prefer a cronjob that runs the canonical brain sync:
```yaml
schedule: "0 */6 * * *"
prompt: "Run python3 ~/.hermes/scripts/brainctl.py --json sync, then python3 ~/.hermes/scripts/brainctl.py --json reindex. Always produce a non-empty final response."
```

## Wikilinks

Obsidian links notes with `[[Note Name]]` syntax. When creating notes, use these to link related content.

## Pitfalls

### System credential files are write-protected

The agent cannot write to protected system files under `~/.hermes/`. If environment persistence is needed, use `env.sh` in the skill directory instead:
```bash
cat > ~/.hermes/skills/note-taking/obsidian/env.sh << 'EOF'
export HERMES_BRAIN_VAULT="$HOME/Documents/brain"
export OBSIDIAN_VAULT_PATH="$HOME/Documents/brain"
EOF
chmod +x ~/.hermes/skills/note-taking/obsidian/env.sh
# source ~/.hermes/skills/note-taking/obsidian/env.sh
```
