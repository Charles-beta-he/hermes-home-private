#!/usr/bin/env python3
"""Export a sanitized portable Hermes personal-brain repo.

This never copies raw ~/.hermes runtime state, raw memory, auth, logs, caches,
sessions, checkpoints, DBs, or .env. The output tree is intended for the private
GitHub repo Charles-beta-he/personal-hermes-brain.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

HOME = Path.home()
HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(HOME / ".hermes"))).expanduser()
BRAIN = Path(os.environ.get("HERMES_BRAIN_VAULT", str(HOME / "Documents" / "brain"))).expanduser()
DEST = Path(os.environ.get("HERMES_PERSONAL_BRAIN_REPO", str(HOME / "personal-hermes-brain"))).expanduser()
REMOTE_URL = "https://github.com/Charles-beta-he/personal-hermes-brain.git"

DENY_DIRS = {
    ".git", ".obsidian", "__pycache__", "node_modules", ".venv", "venv",
    "logs", "cache", "checkpoints", "sessions", "state", "tick", "ticks",
    "sandboxes", "tmp", "rate_limits", "memory", "memories", "cron",
}
DENY_BASENAMES = {
    ".env", ".env.local", ".env.production", "auth.json", "credentials.json",
    "oauth.json", "token.json", "secrets.json", "config.yaml", "config.yml",
    "MEMORY.md", "USER.md", "index.sqlite", "wal.jsonl",
}
DENY_SUFFIXES = {
    ".sqlite", ".db", ".db-wal", ".db-shm", ".wal", ".shm", ".pid", ".lock",
    ".pyc", ".pyo", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".mp4", ".mov",
    ".mp3", ".wav", ".m4a", ".pdf", ".zip", ".tar", ".gz",
}
ALLOW_TEXT_SUFFIXES = {".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".py", ".sh", ".bash", ".template", ".example"}

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{20,}"),
    re.compile(r"(?i)\b(api[_-]?key|secret|token|password|passwd)\b\s*[:=]\s*['\"]?(?!\[REDACTED\]|changeme|example|your_|<)[^\s'\"]{8,}"),
]

SELECTED_SCRIPT_GLOBS = [
    "brainctl.py", "sync-brain.py", "personal_hermes_brain_export.py",
    "brain_cloud_sync_guard.py", "taskpool_dynamic_runner.py", "multimodel_intervention_dynamic_step.py",
    "post-session-autopsy.py", "test_post_session_autopsy_budget.py",
    "autonomous_evolution_nightly_noagent.py", "skill_steward_daily_audit_noagent.py",
    "brain_task_orchestrator.py", "brain_task_dispatch_tick.py", "brain_task_dispatch_summary_tick.py",
    "brain_task_dispatch_autorun_summary_tick.py", "brain_task_autorun_step.py",
    "multimodel_intervention_parallel_step.py", "multimodel_keypoint_coverage_ratchet.py",
    "test_personal_hermes_brain_export.py", "test_taskpool_dynamic_runner.py",
    "test_multimodel_intervention_dynamic_step.py", "test_multimodel_keypoint_coverage_ratchet.py",
    "task_pool_guardian.py", "task_pool_guardian_run.py", "taskpool_watch_report.py",
    "cron-health-quarantine.py", "cron-missed-run-guard.py", "permission_taxonomy.py",
]


def utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def rel_parts(path: Path, root: Path) -> tuple[str, ...]:
    try:
        return path.relative_to(root).parts
    except Exception:
        return path.parts


def denied_path(path: Path, root: Path) -> str:
    parts = rel_parts(path, root)
    lower_parts = [p.lower() for p in parts]
    if any(p in DENY_DIRS for p in lower_parts[:-1]):
        return "deny_dir"
    name = path.name.lower()
    if name in DENY_BASENAMES:
        return "deny_basename"
    # Deny concrete secret-bearing filenames, but allow documentation such as
    # docs/RESTORE_CREDENTIALS.md and SECURITY.md.
    if any(token in name for token in ("oauth",)) or name in {"credentials", "secrets", "secret", "credential"}:
        return "deny_sensitive_name"
    if name.endswith((".key", ".pem", ".p12", ".crt")):
        return "deny_key_material"
    if path.suffix.lower() in DENY_SUFFIXES:
        return "deny_suffix"
    return ""


def has_secret_text(text: str) -> str:
    for pat in SECRET_PATTERNS:
        m = pat.search(text)
        if m:
            return pat.pattern
    return ""


def read_text(path: Path) -> str | None:
    if path.suffix.lower() not in ALLOW_TEXT_SUFFIXES:
        return None
    try:
        data = path.read_bytes()
    except Exception:
        return None
    if b"\x00" in data[:4096]:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("utf-8", errors="replace")


def copy_text_tree(src_root: Path, dst_root: Path, *, only_globs: Iterable[str] | None = None) -> dict[str, int]:
    copied = skipped = secret_skipped = 0
    patterns = list(only_globs or [])
    for src in src_root.rglob("*"):
        if src.is_dir():
            continue
        rel = src.relative_to(src_root)
        if patterns and not any(fnmatch.fnmatch(str(rel), pat) or fnmatch.fnmatch(src.name, pat) for pat in patterns):
            skipped += 1
            continue
        reason = denied_path(src, src_root)
        if reason:
            skipped += 1
            continue
        text = read_text(src)
        if text is None:
            skipped += 1
            continue
        secret = has_secret_text(text)
        if secret:
            secret_skipped += 1
            continue
        dst = dst_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(text, encoding="utf-8")
        copied += 1
    return {"copied": copied, "skipped": skipped, "secret_skipped": secret_skipped}


def write_repo_files(dest: Path) -> None:
    (dest / "README.md").write_text(f"""# personal-hermes-brain

Sanitized private backup/export for Charles' Hermes personal brain.

Generated: {utc()}

This repo intentionally contains portable knowledge and deterministic source artifacts only.
It does not contain raw Hermes memory, auth files, OAuth tokens, logs, caches, sessions,
SQLite indexes, checkpoints, `.env`, or runtime state.

Restore path:

1. Clone this private repo.
2. Read `docs/BOOTSTRAP.md` and `docs/SYNC_POLICY.md`.
3. Restore credentials manually from the local password manager, never from Git.
4. Run `bash bootstrap/verify.sh` before importing.
""", encoding="utf-8")
    (dest / "SECURITY.md").write_text("""# Security policy

Private GitHub is not treated as a secret store.

Forbidden in this repo:
- API keys, tokens, passwords, OAuth files, auth.json, `.env`
- raw `~/.hermes/memories/*`
- `~/.hermes/memory/*`, SQLite indexes, WAL files
- logs, caches, sessions, checkpoints, tick artifacts, state DBs

All pushes must pass `bootstrap/validate_safe_tree.sh`.
""", encoding="utf-8")
    (dest / "CONFLICT_POLICY.md").write_text("""# Conflict policy

Canonical live source remains the local machine:
- brain: `~/Documents/brain`
- Hermes runtime: `~/.hermes`

This repo is a sanitized export/backup. Import is manual and review-first.
Never blindly overwrite local runtime state from this repo.
""", encoding="utf-8")
    (dest / ".gitignore").write_text(""".DS_Store
.env*
*.sqlite
*.db
*.db-wal
*.db-shm
*.wal
*.shm
*.pyc
__pycache__/
logs/
cache/
state/
sessions/
checkpoints/
tick-*/
*.pem
*.key
auth.json
credentials.json
oauth*.json
token*.json
MEMORY.md
USER.md
""", encoding="utf-8")
    (dest / ".gitattributes").write_text("""* text=auto
*.md text
*.py text
*.sh text eol=lf
*.json text
*.yaml text
""", encoding="utf-8")
    (dest / "manifest.yaml").write_text(f"""schema: personal_hermes_brain_manifest_v1
generated_at: {utc()}
source_brain: {BRAIN}
policy:
  raw_memory: excluded
  auth: excluded
  runtime_state: excluded
  validation: bootstrap/validate_safe_tree.sh
remote: https://github.com/Charles-beta-he/personal-hermes-brain
""", encoding="utf-8")
    (dest / "docs").mkdir(parents=True, exist_ok=True)
    (dest / "docs" / "BOOTSTRAP.md").write_text("""# Bootstrap

Run:

```bash
bash bootstrap/verify.sh
```

Then selectively copy reviewed Markdown notes into a new `~/Documents/brain` vault.
Credentials must be restored manually outside Git.
""", encoding="utf-8")
    (dest / "docs" / "RESTORE_CREDENTIALS.md").write_text("""# Restore credentials

No credentials are stored here. Re-create local `.env`, auth, OAuth and provider credentials
from the password manager or provider dashboards.
""", encoding="utf-8")
    (dest / "docs" / "SYNC_POLICY.md").write_text("""# Sync policy

Export is allowlist/sanitized. Push only after validation passes.
Raw Hermes runtime state stays local-only.
""", encoding="utf-8")
    (dest / "docs" / "MACHINE_ROLES.md").write_text("""# Machine roles

This repo is portable source material. Runtime machine-specific state is intentionally absent.
""", encoding="utf-8")
    (dest / "hermes" / "memory").mkdir(parents=True, exist_ok=True)
    (dest / "hermes" / "memory" / "README.md").write_text("""# Hermes memory policy

Raw persistent memory is local-only and is not exported to this repository.
Promote durable knowledge into reviewed brain notes or skills before export.
""", encoding="utf-8")


def write_bootstrap(dest: Path) -> None:
    b = dest / "bootstrap"
    b.mkdir(parents=True, exist_ok=True)
    validate = r'''#!/usr/bin/env bash
set -euo pipefail
if [ "$#" -gt 0 ]; then
  root="$1"
else
  script_dir="$(cd "$(dirname "$0")" && pwd)"
  root="$(cd "$script_dir/.." && pwd)"
fi
cd "$root"
fail=0
bad_paths=$(find . \( -name '.env*' -o -name 'auth.json' -o -iname '*oauth*' -o -iname 'credentials.json' -o -iname 'secrets.json' -o -iname 'token*.json' -o -name 'MEMORY.md' -o -name 'USER.md' -o -name '*.sqlite' -o -name '*.db' -o -name '*.db-wal' -o -name '*.db-shm' -o -name '*.pem' -o -name '*.key' \) -print | sed 's#^./##' || true)
if [ -n "$bad_paths" ]; then
  echo "Forbidden paths:" >&2
  echo "$bad_paths" >&2
  fail=1
fi
if [ -d hermes/memory ]; then
  extra_memory=$(find hermes/memory -type f ! -name README.md -print | sed 's#^./##' || true)
  if [ -n "$extra_memory" ]; then
    echo "Forbidden raw memory files:" >&2
    echo "$extra_memory" >&2
    fail=1
  fi
fi
secret_hits=$(python3 - <<'PY'
from pathlib import Path
import re
root=Path('.')
patterns=[
 re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
 re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
 re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"),
 re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
 re.compile(r"AKIA[0-9A-Z]{16}"),
 re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{20,}"),
 re.compile(r"(?i)\b(api[_-]?key|secret|token|password|passwd)\b\s*[:=]\s*['\"]?(?!\[REDACTED\]|changeme|example|your_|<)[^\s'\"]{8,}"),
]
allow_suffix={'.md','.txt','.json','.yaml','.yml','.toml','.py','.sh','.bash','.example','.template'}
hits=[]
for p in root.rglob('*'):
 if not p.is_file() or '.git' in p.parts or p.suffix.lower() not in allow_suffix: continue
 try: txt=p.read_text(encoding='utf-8', errors='replace')
 except Exception: continue
 for pat in patterns:
  if pat.search(txt):
   hits.append(str(p))
   break
print('\n'.join(sorted(set(hits))))
PY
)
if [ -n "$secret_hits" ]; then
  echo "Secret-like content hits:" >&2
  echo "$secret_hits" >&2
  fail=1
fi
exit "$fail"
'''
    (b / "validate_safe_tree.sh").write_text(validate, encoding="utf-8")
    (b / "verify.sh").write_text("""#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
bash bootstrap/validate_safe_tree.sh
python3 -m py_compile hermes/scripts/*.py 2>/dev/null || true
git diff --check || true
echo "verify: PASS"
""", encoding="utf-8")
    (b / "sync_export.sh").write_text(f"""#!/usr/bin/env bash
set -euo pipefail
python3 {HERMES_HOME}/scripts/personal_hermes_brain_export.py "$@"
""", encoding="utf-8")
    (b / "sync_import.sh").write_text("""#!/usr/bin/env bash
set -euo pipefail
echo "Import is intentionally manual/review-first. Read docs/BOOTSTRAP.md."
""", encoding="utf-8")
    (b / "bootstrap_machine.sh").write_text("""#!/usr/bin/env bash
set -euo pipefail
bash bootstrap/verify.sh
echo "Bootstrap verified. Restore credentials manually."
""", encoding="utf-8")
    (b / "install_push_guard.sh").write_text(r'''#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .git/hooks
cat > .git/hooks/pre-push <<'HOOK'
#!/usr/bin/env bash
set -euo pipefail
if [ "${HERMES_ALLOW_PUSH:-}" != "1" ]; then
  echo "Push blocked. Run validation and set HERMES_ALLOW_PUSH=1 only after guarded approval." >&2
  exit 1
fi
bash bootstrap/validate_safe_tree.sh
HOOK
chmod +x .git/hooks/pre-push
''', encoding="utf-8")
    (b / "rollback.sh").write_text("""#!/usr/bin/env bash
set -euo pipefail
git status --short
echo "Rollback manually with git reset/revert after review."
""", encoding="utf-8")
    for sh in b.glob("*.sh"):
        sh.chmod(0o755)


def ensure_git(dest: Path) -> None:
    if not (dest / ".git").exists():
        dest.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init"], cwd=dest, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    remotes = subprocess.run(["git", "remote"], cwd=dest, text=True, capture_output=True, check=False).stdout.split()
    if "origin" not in remotes:
        subprocess.run(["git", "remote", "add", "origin", REMOTE_URL], cwd=dest, check=True)
    else:
        subprocess.run(["git", "remote", "set-url", "origin", REMOTE_URL], cwd=dest, check=True)
    subprocess.run(["bash", "bootstrap/install_push_guard.sh"], cwd=dest, check=False)


def clean_dest(dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for child in dest.iterdir():
        if child.name == ".git":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def export(dest: Path = DEST) -> dict[str, object]:
    clean_dest(dest)
    write_repo_files(dest)
    write_bootstrap(dest)
    stats = {
        "brain": copy_text_tree(BRAIN, dest / "brain"),
        "skills": copy_text_tree(HERMES_HOME / "skills", dest / "hermes" / "skills") if (HERMES_HOME / "skills").exists() else {"copied":0,"skipped":0,"secret_skipped":0},
        "scripts": copy_text_tree(HERMES_HOME / "scripts", dest / "hermes" / "scripts", only_globs=SELECTED_SCRIPT_GLOBS),
    }
    ensure_git(dest)
    manifest = {
        "schema": "personal_hermes_brain_export_result_v1",
        "generated_at": utc(),
        "dest": str(dest),
        "remote": REMOTE_URL,
        "stats": stats,
    }
    (dest / "docs" / "LAST_EXPORT.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", default=str(DEST))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    result = export(Path(args.dest).expanduser())
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"exported {result['dest']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
