#!/usr/bin/env python3
"""Fix escape explosion in brain task file YAML frontmatter.

Usage:
    python3 fix-task-escape-explosion.py [--dry-run] [FILE...]

Without FILE args, scans ~/Documents/brain/05-实践与项目/tasks/ for >100KB files.
"""
import re
import sys
import os
import glob

TASK_DIR = os.path.expanduser("~/Documents/brain/05-实践与项目/tasks/")
THRESHOLD = 5000  # chars per line to trigger fix

def fix_file(path, dry_run=False):
    with open(path, 'r', errors='replace') as f:
        lines = f.readlines()

    original_size = sum(len(l) for l in lines)
    fixed_lines = []
    changed = False

    for line in lines:
        if len(line) > THRESHOLD and '\\\\' in line:
            m = re.match(r'^(\w+):\s*', line)
            if m:
                field = m.group(1)
                values = re.findall(r'(?:https?://[^\s\\"]+|proof:\w+:[^\s\\"]+)', line)
                if values:
                    fixed_lines.append(f'{field}: {values}\n')
                    changed = True
                    print(f"  Fixed {field}: {len(line)/1024:.0f}KB -> {len(fixed_lines[-1])/1024:.1f}KB ({len(values)} values)")
                    continue
                else:
                    fixed_lines.append(line[:500] + '... [TRUNCATED: escape explosion]\n')
                    changed = True
                    print(f"  Truncated {field}: {len(line)/1024:.0f}KB -> 0.5KB")
                    continue
        fixed_lines.append(line)

    if not changed:
        return False

    if dry_run:
        print(f"  [DRY RUN] Would reduce {original_size/1024/1024:.1f}MB -> {sum(len(l) for l in fixed_lines)/1024:.0f}KB")
        return True

    with open(path, 'w') as f:
        f.writelines(fixed_lines)
    new_size = sum(len(l) for l in fixed_lines)
    print(f"  Result: {original_size/1024/1024:.1f}MB -> {new_size/1024:.0f}KB")
    return True

def main():
    dry_run = '--dry-run' in sys.argv
    files = [f for f in sys.argv[1:] if not f.startswith('--')]

    if not files:
        # Auto-scan for bloated files
        result = os.popen(f"find '{TASK_DIR}' -name '*.md' -size +100k").read()
        files = [l.strip() for l in result.strip().split('\n') if l.strip()]

    if not files:
        print("No bloated task files found.")
        return

    print(f"Found {len(files)} bloated files:")
    fixed = 0
    for path in files:
        name = os.path.basename(path)[:60]
        print(f"\n{name}...")
        if fix_file(path, dry_run):
            fixed += 1

    print(f"\n=== Fixed {fixed}/{len(files)} files ===")

if __name__ == '__main__':
    main()
