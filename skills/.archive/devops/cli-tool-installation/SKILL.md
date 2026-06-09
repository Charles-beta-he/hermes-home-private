---
name: cli-tool-installation
description: Use when creating install scripts for CLI tools, handling upgrades, version management, configuration preservation, and rollback mechanisms. Covers bash install scripts that need to work on both fresh installs and existing installations.
triggers:
  - creating install scripts
  - CLI tool packaging
  - upgrade mechanisms
  - version management
  - install script with backup
  - rollback functionality
---

# CLI Tool Installation Patterns

## When to Use

Use this skill when the user's request matches `cli-tool-installation` and requires external tools, APIs, CLIs, platforms, or other side-effecting capability surfaces.

Do not use it for:
- generic one-off questions that do not need this workflow;
- neighboring specialist workflows with a narrower matching skill;
- durable memory or project-profile writes unless this skill explicitly governs that landing zone.

## Overview

When creating install scripts for CLI tools, always design for BOTH fresh install AND upgrade scenarios. The naive `curl | sh` pattern that overwrites files destroys user configuration.

## Core Principles

1. **Detect before overwriting** — check if installation exists
2. **Backup before upgrading** — timestamped backups
3. **Preserve user config** — never overwrite config.yaml blindly
4. **Version-aware upgrades** — skip if already latest
5. **Provide rollback** — users need escape hatches
6. **Verify after installing** — create verification script

## Install Script Template

```bash
#!/bin/bash
set -e

INSTALL_DIR="$HOME/.your-tool"
VERSION_FILE="$INSTALL_DIR/version.txt"
BACKUP_DIR="$INSTALL_DIR/backups"
REPO_URL="https://raw.githubusercontent.com/user/repo/main"

# 1. Detect existing installation
EXISTING_INSTALL=false
CURRENT_VERSION=""
if [ -d "$INSTALL_DIR" ] && [ -f "$INSTALL_DIR/main.py" ]; then
    EXISTING_INSTALL=true
    CURRENT_VERSION=$(cat "$VERSION_FILE" 2>/dev/null || echo "unknown")
fi

# 2. Create directories
mkdir -p "$INSTALL_DIR"/{logs,backups}

# 3. Backup if upgrading
if [ "$EXISTING_INSTALL" = true ]; then
    BACKUP_PATH="$BACKUP_DIR/backup-$(date '+%Y%m%d%H%M%S')"
    mkdir -p "$BACKUP_PATH"
    # Backup critical files
    [ -f "$INSTALL_DIR/main.py" ] && cp "$INSTALL_DIR/main.py" "$BACKUP_PATH/"
    [ -f "$INSTALL_DIR/config.yaml" ] && cp "$INSTALL_DIR/config.yaml" "$BACKUP_PATH/"
fi

# 4. Version check
LATEST_VERSION=$(curl -sSL "$REPO_URL/version.txt")
if [ "$EXISTING_INSTALL" = true ] && [ "$CURRENT_VERSION" = "$LATEST_VERSION" ]; then
    echo "Already latest version, skipping"
    exit 0
fi

# 5. Download files
curl -sSL "$REPO_URL/main.py" -o "$INSTALL_DIR/main.py"

# 6. Config preservation (KEY PATTERN)
if [ "$EXISTING_INSTALL" = true ] && [ -f "$INSTALL_DIR/config.yaml" ]; then
    curl -sSL "$REPO_URL/config.yaml" -o "$INSTALL_DIR/config.yaml.new"
    if ! diff -q "$INSTALL_DIR/config.yaml" "$INSTALL_DIR/config.yaml.new" >/dev/null 2>&1; then
        echo "Config update available: config.yaml.new"
        echo "Existing config preserved"
    fi
    rm -f "$INSTALL_DIR/config.yaml.new"
else
    curl -sSL "$REPO_URL/config.yaml" -o "$INSTALL_DIR/config.yaml"
fi

# 7. Update version
echo "$LATEST_VERSION" > "$VERSION_FILE"
```

## CLI Wrapper Pattern

The CLI wrapper must handle symbolic links correctly:

```bash
#!/bin/bash
# Get actual script directory (not symlink location)
get_script_dir() {
    local source="${BASH_SOURCE[0]}"
    while [ -L "$source" ]; do
        local dir
        dir="$(cd -P "$(dirname "$source")" && pwd)"
        source="$(readlink "$source")"
        [[ $source != /* ]] && source="$dir/$source"
    done
    cd -P "$(dirname "$source")" && pwd
}

SCRIPT_DIR="$(get_script_dir)"
```

## CLI Commands to Include

```bash
case "${1:-help}" in
    start)      # Start service (foreground or --daemon)
    stop)       # Stop service (PID file based)
    restart)    # Stop + start
    status)     # Show version, PID, uptime
    logs)       # Tail log file
    config)     # Open config in $EDITOR
    update)     # Re-run install script (version-aware)
    rollback)   # Restore from backup
    uninstall)  # Confirm + remove
    help)       # Usage info
esac
```

## Verification Script

Always create a companion verification script:

```bash
#!/bin/bash
# Checks:
# 1. Installation directory exists
# 2. Core files present
# 3. CLI command in PATH
# 4. Configuration correct
# 5. Network connectivity (if applicable)
# 6. Port availability
# 7. Dependencies installed

ERRORS=0
pass() { echo "[✓] $1"; }
fail() { echo "[✗] $1"; ERRORS=$((ERRORS + 1)); }

# ... checks ...

if [ $ERRORS -eq 0 ]; then
    echo "✓ Installation verified"
else
    echo "✗ Found $ERRORS issues"
fi
```
- [ ] Wrapper safety: any side effect is followed by target-state read-back before reporting completion.
## Pitfalls

1. **Symbolic links**: `dirname $0` gives wrong path for symlinked scripts. Use the `get_script_dir` pattern.

2. **Config overwrite**: Never blindly `curl -o config.yaml`. Always check if file exists and preserve.

3. **No version file**: First version won't have version.txt. Handle gracefully with fallback.

4. **SSL issues / insecure fallback UX**: Some environments have cert problems, but never silently switch to `curl -k` / `--insecure`. Use safe defaults plus explicit escape hatches:
   - First try normal TLS verification.
   - If verification fails, explain likely causes (corporate proxy, self-signed CA, stale system CA, possible interception) and recommend fixing CA/proxy or switching to a trusted network.
   - In an interactive TTY, allow a one-time insecure fallback only after the user types an explicit confirmation such as `yes`.
   - In non-interactive environments, fail closed unless a clearly named env var is set, e.g. `HERMES_EDGE_ALLOW_INSECURE_SSL=1`.
   - Never document `curl -k | bash` as the default path; put insecure usage only in troubleshooting and prefer “download script, then run with explicit env”.
   - Add tests for TLS OK, TLS fail + no TTY, TLS fail + explicit env, and static docs that prevent insecure defaults.

5. **PID file stale**: Process may have crashed without cleanup. Check if PID is actually running.

6. **PATH not updated**: After install, remind user to add install dir to PATH if needed.

7. **CJK/full-width parentheses in heredocs**: When generating a CLI script inside a heredoc (`cat > script.sh << 'EOF'`), avoid mixing CJK full-width parentheses（）with bash command substitution `$(...)` inside the same echo string. Bash's parser can choke on the combination even inside single-quoted heredoc delimiters (which prevent variable expansion but still parse syntactic elements). Example that breaks:

   ```bash
   # BAD — full-width（）confuses bash parser around $(cat ...)
   cat > script.sh << 'EOF'
   echo "已在运行 (PID: $(cat $SCRIPT_DIR/worker.pid))"
   EOF
   ```

   Fix: extract the substitution to a variable first, then echo it:

   ```bash
   # GOOD — no $(...) inside the parenthesized echo string
   cat > script.sh << 'EOF'
   PID=$(cat "$SCRIPT_DIR/worker.pid")
   echo "已在运行 PID: $PID"
   EOF
   ```

   Alternatively, avoid CJK punctuation entirely in generated scripts — use plain ASCII parentheses or colon-separated labels (`PID: 1234`) instead.

## File Structure

```
project/
├── install.sh              # Main install script
├── install-insecure.sh     # SSL-issues variant
├── verify-installation.sh  # Verification script
├── version.txt             # Semantic version
├── src/
│   ├── main.py             # Core program
│   └── config.yaml         # Default config
└── docs/
    ├── VERIFY-GUIDE.md     # Manual verification steps
    └── MANUAL-INSTALL.md   # Manual install instructions
```
