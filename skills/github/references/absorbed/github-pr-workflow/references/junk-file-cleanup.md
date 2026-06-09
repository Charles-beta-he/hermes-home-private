# Junk File Cleanup Before Commit

macOS Finder's "Duplicate" action creates files with ` 2` suffix (space + number). These are common in long-lived dev directories and can silently contaminate commits if staged.

## Detection

```bash
# Find all " 2" Finder duplicates in the repo
find . -name "* 2.*" -not -path "./.git/*" -print

# Find .tmp/ directories (often from ad-hoc scripts/probes)
find . -name ".tmp" -type d -not -path "./.git/*" -print

# Find other common junk patterns
find . -name "*.bak" -o -name "*~" -o -name ".DS_Store" | grep -v .git
```

## Cleanup

```bash
# Remove " 2" duplicates (confirm first!)
find . -name "* 2.*" -not -path "./.git/*" -delete -print

# Remove .tmp directories
rm -rf .tmp/

# Unstage any junk that was accidentally staged
git reset HEAD -- .tmp/ "* 2.*" "*.bak" "*~"
```

## Prevention

Add to `.gitignore`:
```gitignore
# macOS Finder duplicates
* 2.*
* 3.*
* 4.*

# Temp/ad-hoc
.tmp/
*.bak
*~
.DS_Store
```

## Pitfall: `git add` with explicit files does NOT unstage prior junk

When you call `git add specific-file.ts`, it stages that file — but any files already staged from prior operations remain staged. A subsequent `git commit` commits EVERYTHING in the staging area, not just what you just added.

**Safe pattern after staging:**
```bash
# 1. Stage your target file
git add src/stores/notification.store.ts

# 2. Verify ONLY your file is staged
git diff --cached --stat

# 3. If junk appears, unstage it
git reset HEAD -- .tmp/ "* 2.*"

# 4. Then commit
git commit -m "fix: ..."
```

With MCP `git_add`, the tool may stage files differently than CLI `git add`. Always verify `git diff --cached --stat` before `git_commit`.
