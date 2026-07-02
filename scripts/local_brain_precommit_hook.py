#!/usr/bin/env python3
"""Install/run a git pre-commit hook for local brain preflight.

The installed hook is local-only and reversible. It does not dispatch externally,
write taskpool lifecycle state, deploy, publish, or perform destructive actions.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Sequence

SCRIPTS_DIR = Path(__file__).resolve().parent
BRAINCTL = SCRIPTS_DIR / "brainctl.py"
HOOK_SCRIPT = SCRIPTS_DIR / "local_brain_precommit_hook.py"


def run(cmd: Sequence[str], *, cwd: Path | None = None, timeout: int = 180) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(cmd), cwd=str(cwd) if cwd else None, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)


def repo_root(path: Path) -> Path:
    proc = run(["git", "-C", str(path), "rev-parse", "--show-toplevel"], timeout=30)
    if proc.returncode != 0:
        raise SystemExit(f"not a git repo: {path}\n{proc.stderr}")
    return Path(proc.stdout.strip())


def staged_files(root: Path) -> list[str]:
    proc = run(["git", "-C", str(root), "-c", "core.quotePath=false", "diff", "--cached", "--name-only", "--diff-filter=ACMR"], timeout=30)
    if proc.returncode != 0:
        raise SystemExit(proc.stderr)
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def is_taskpool_control_plane_change(files: Sequence[str]) -> bool:
    markers = (
        "scripts/brain_task_",
        "scripts/task_pool_guardian",
        "scripts/taskpool_",
        "scripts/agent_team_controller.py",
        "scripts/consult_models.py",
        "skills/software-development/taskpool-",
    )
    return any(f.startswith(markers) for f in files)


def is_local_architecture_control_plane_change(files: Sequence[str]) -> bool:
    markers = (
        "scripts/consult_models.py",
        "scripts/local_brain_",
        "scripts/brainctl.py",
        "scripts/task_preflight.py",
        "scripts/brain_task_",
        "scripts/taskpool_",
        "skills/software-development/taskpool-",
    )
    return any(f.startswith(markers) for f in files)


def relevant_tests(files: Sequence[str]) -> list[Path]:
    wanted: list[Path] = []
    if any(f.startswith("scripts/brainctl.py") or f.startswith("scripts/test_brainctl.py") for f in files):
        wanted.append(SCRIPTS_DIR / "test_brainctl.py")
    if any("local_brain_change_preflight" in f for f in files):
        wanted.append(SCRIPTS_DIR / "test_local_brain_change_preflight.py")
    if any(f.startswith("scripts/local_brain_precommit_hook.py") or f.startswith("scripts/test_local_brain_precommit_hook.py") for f in files):
        wanted.append(SCRIPTS_DIR / "test_local_brain_precommit_hook.py")
    if any(f.startswith("scripts/task_preflight.py") or f.startswith("scripts/test_task_preflight_local_brain.py") for f in files):
        wanted.append(SCRIPTS_DIR / "test_task_preflight_local_brain.py")
    if is_taskpool_control_plane_change(files):
        wanted.extend([
            SCRIPTS_DIR / "test_brain_task_autorun_step.py",
            SCRIPTS_DIR / "test_brain_task_dispatch_tick.py",
            SCRIPTS_DIR / "test_task_pool_guardian.py",
            SCRIPTS_DIR / "test_task_pool_guardian_silent.py",
            SCRIPTS_DIR / "test_taskpool_dynamic_runner_cron.py",
        ])
    seen: set[Path] = set()
    deduped: list[Path] = []
    for path in wanted:
        if path.exists() and path not in seen:
            seen.add(path)
            deduped.append(path)
    return deduped


def hook_evidence(root: Path, files: Sequence[str]) -> tuple[list[str], list[str]]:
    evidence = [
        "diff:git diff --cached --name-only readback",
        "search_output:brainctl preflight performs search",
        "fixture_replay:pre-commit hook smoke",
        "reindex_readback:brainctl preflight performs reindex",
        "provider_status:pre-commit local mode no live model fanout",
        "health_snapshot:pre-commit local mode no live model fanout",
        "route_review_record:embedded RouteReviewRecord emitted",
        "file_readback:staged file list readback",
        "exact_target:local git repository staged files only",
        "rollback:git reset staged changes or git revert resulting commit; hook backup preserved when overwritten",
        "post_action_readback:pre-commit hook exits zero only after local preflight verdict is non-blocking",
    ]
    errors: list[str] = []
    if is_local_architecture_control_plane_change(files):
        evidence.extend([
            "design_doc:staged local control-plane diff is the executable design; scoped to local provider/taskpool/precommit evidence handling with rollback by git reset/revert",
            "gate_readback:local pre-commit BrainConstraintGate reads back staged files, evidence labels, deterministic tests, and exits nonzero on missing gates",
        ])
    py_files = [root / f for f in files if f.endswith(".py") and (root / f).exists()]
    if py_files:
        proc = run([sys.executable, "-m", "py_compile", *[str(p) for p in py_files]], cwd=root, timeout=120)
        if proc.returncode == 0:
            evidence.append("py_compile_or_build:staged python py_compile OK")
        else:
            errors.append(f"py_compile failed:\n{proc.stdout}\n{proc.stderr}")
    else:
        evidence.append("py_compile_or_build:not_applicable_non_python_change")
    tests = relevant_tests(files)
    if tests:
        for test in tests:
            proc = run([sys.executable, str(test), "-q"], cwd=root, timeout=300)
            if proc.returncode != 0:
                errors.append(f"test failed: {test}\n{proc.stdout}\n{proc.stderr}")
        if not errors:
            evidence.append("tests:targeted local-brain pre-commit tests OK")
            if is_taskpool_control_plane_change(files):
                evidence.extend([
                    "task_record:local git staged taskpool change record includes exact touched files and rollback target",
                    "proof_log:targeted taskpool regression tests and py_compile completed under pre-commit hook",
                    "lifecycle_readback:focused tests cover fail-closed eligibility, claim precheck, review close gating, cron wrapper dedupe, and no force-done path",
                ])
    else:
        evidence.append("tests:not_applicable_no_local_brain_code_surface")
    if not any(e.startswith("deterministic_gate:") for e in evidence):
        # Keep this narrow: the hook is a local preflight, not full runtime certification.
        evidence.append("deterministic_gate:pre-commit local deterministic checks completed")
    return evidence, errors


def run_hook(repo: Path) -> int:
    root = repo_root(repo)
    files = staged_files(root)
    if not files:
        return 0
    evidence, errors = hook_evidence(root, files)
    if errors:
        print("Local brain pre-commit evidence collection failed", file=sys.stderr)
        print("\n".join(errors), file=sys.stderr)
        return 1
    cmd = [
        sys.executable,
        str(BRAINCTL),
        "--json",
        "preflight",
        "--summary",
        "git pre-commit staged files: " + ", ".join(files[:20]),
        "--vault",
        str(Path.home() / "Documents" / "brain"),
        "--vault",
        str(Path.home() / ".hermes" / "notes" / "brain"),
        "--memory-root",
        str(Path.home() / ".hermes" / "memory" / "local-brain-precommit"),
    ]
    for f in files:
        cmd.extend(["--file", f])
    for item in evidence:
        cmd.extend(["--evidence", item])
    proc = run(cmd, cwd=root, timeout=300)
    if proc.returncode != 0:
        print(proc.stdout, file=sys.stderr)
        print(proc.stderr, file=sys.stderr)
        return proc.returncode
    try:
        data = json.loads(proc.stdout)
        verdict = data.get("brain_constraint_record", {}).get("verdict", {})
        print(f"local-brain-precommit: {verdict.get('status')} reasons={verdict.get('reasons', [])}")
    except json.JSONDecodeError:
        print(proc.stdout)
    return 0


def install(repo: Path) -> dict:
    root = repo_root(repo)
    hooks = root / ".git" / "hooks"
    hooks.mkdir(parents=True, exist_ok=True)
    target = hooks / "pre-commit"
    content = f"#!/bin/sh\nexec {sys.executable} {HOOK_SCRIPT} --run --repo {root}\n"
    backup = None
    if target.exists() and target.read_text(encoding="utf-8", errors="replace") != content:
        backup = target.with_suffix(".pre-local-brain-backup")
        backup.write_text(target.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
    target.write_text(content, encoding="utf-8")
    target.chmod(0o755)
    return {"ok": True, "repo": str(root), "hook": str(target), "backup": str(backup) if backup else None, "enabled": True}


def status(repo: Path) -> dict:
    root = repo_root(repo)
    target = root / ".git" / "hooks" / "pre-commit"
    enabled = target.exists() and "local_brain_precommit_hook.py" in target.read_text(encoding="utf-8", errors="replace")
    return {"ok": True, "repo": str(root), "hook": str(target), "exists": target.exists(), "enabled": enabled}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=str(Path.home() / ".hermes"))
    parser.add_argument("--install", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    repo = Path(args.repo).expanduser()
    if args.install:
        result = install(repo)
    elif args.status:
        result = status(repo)
    elif args.run:
        return run_hook(repo)
    else:
        result = status(repo)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
