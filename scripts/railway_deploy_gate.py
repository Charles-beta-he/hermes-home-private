#!/usr/bin/env python3
"""Railway deployment gate helper for UVISA/Lark online UI retest tasks.

Reads Railway CLI JSON, validates auth/linkage, service terminal status, and
optionally that the active deployment commit matches an expected commit.
No secrets are printed; only safe status/metadata fields are returned.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

GOOD_STATUSES = {"SUCCESS", "SUCCEEDED", "DEPLOYED", "READY"}
BLOCKING_STATUSES = {"NEEDS_APPROVAL", "FAILED", "CRASHED", "REMOVED", "CANCELED", "CANCELLED", "ERROR"}
DEFAULT_WORKDIRS = [
    Path("/Users/charles/Desktop/folder/work/uvisa-backend"),
    Path("/Users/charles/Desktop/folder/work/uvisa-app-2.0"),
    Path("/Users/charles/Desktop/folder/work/uvisa-admin"),
]
PROJECT_SERVICE_DEFAULTS = {
    "uvisa-admin": "uvisa-admin",
    "uvisa-backend": "uvisa-backend",
    "uvisa-app-2.0": "uvisa-app-tRnN",
    "uvisa-app": "uvisa-app-tRnN",
    "uvisa-h5": "uvisa-app-tRnN",
}
REPO_WORKDIR_DEFAULTS = {
    "cryptolxd/uvisa-admin": Path("/Users/charles/Desktop/folder/work/uvisa-admin"),
    "uvisa-admin": Path("/Users/charles/Desktop/folder/work/uvisa-admin"),
    "cryptolxd/uvisa-backend": Path("/Users/charles/Desktop/folder/work/uvisa-backend"),
    "uvisa-backend": Path("/Users/charles/Desktop/folder/work/uvisa-backend"),
    "cryptolxd/uvisa-app": Path("/Users/charles/Desktop/folder/work/uvisa-app-2.0"),
    "uvisa-app-tRnN": Path("/Users/charles/Desktop/folder/work/uvisa-app-2.0"),
}


def _run_railway(args: list[str], *, cwd: Path, timeout: int = 45) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["railway", *args],
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _json_loads(text: str) -> Any:
    return json.loads(text)


def resolve_service(project: str, service: str = "") -> str:
    if service:
        return service
    key = str(project or "").strip()
    return PROJECT_SERVICE_DEFAULTS.get(key, key)


def find_usable_workdir(preferred: str = "") -> dict[str, Any]:
    candidates = []
    if preferred:
        candidates.append(Path(preferred).expanduser())
    candidates.extend(p for p in DEFAULT_WORKDIRS if p not in candidates)
    errors: list[str] = []
    for cwd in candidates:
        if not cwd.exists():
            errors.append(f"missing_workdir:{cwd}")
            continue
        try:
            code, out, err = _run_railway(["status"], cwd=cwd, timeout=20)
        except FileNotFoundError:
            return {"ok": False, "workdir": "", "errors": ["railway_cli_not_found"]}
        except Exception as exc:
            errors.append(f"status_exception:{cwd}:{exc}")
            continue
        combined = (out + err).strip()
        if code == 0 and "Project:" in out and "Environment:" in out:
            return {"ok": True, "workdir": str(cwd), "status_text": out.strip(), "errors": errors}
        if "Unauthorized" in combined or "railway login" in combined or "invalid_grant" in combined:
            errors.append(f"railway_auth_required:{cwd}")
        elif "No linked project found" in combined:
            errors.append(f"railway_project_not_linked:{cwd}")
        else:
            errors.append(f"railway_status_failed:{cwd}:{combined[:240]}")
    return {"ok": False, "workdir": "", "errors": errors}


def current_service_status(service: str, *, workdir: str = "") -> dict[str, Any]:
    wd = find_usable_workdir(workdir)
    if not wd.get("ok"):
        return {"ok": False, "allowed": False, "service": service, "blockers": wd.get("errors", []), "workdir": wd.get("workdir", "")}
    cwd = Path(wd["workdir"])
    code, out, err = _run_railway(["service", "status", "--all", "--json"], cwd=cwd)
    if code != 0:
        combined = (out + err).strip()
        blockers = ["railway_service_status_failed"]
        if "Unauthorized" in combined or "railway login" in combined or "invalid_grant" in combined:
            blockers.append("railway_auth_required")
        return {"ok": False, "allowed": False, "service": service, "blockers": blockers, "error": combined[:500], "workdir": str(cwd)}
    services = _json_loads(out)
    match = next((item for item in services if str(item.get("name")) == service or str(item.get("id")) == service), None)
    if not match:
        return {"ok": False, "allowed": False, "service": service, "blockers": ["railway_service_not_found"], "available_services": [s.get("name") for s in services], "workdir": str(cwd)}
    status = str(match.get("status") or "").upper()
    stopped = bool(match.get("stopped"))
    blockers: list[str] = []
    if status not in GOOD_STATUSES:
        blockers.append(f"railway_status_not_green:{status or 'UNKNOWN'}")
    if stopped:
        blockers.append("railway_service_stopped")
    return {
        "ok": True,
        "allowed": not blockers,
        "service": str(match.get("name") or service),
        "service_id": str(match.get("id") or ""),
        "deployment_id": str(match.get("deploymentId") or ""),
        "status": status,
        "stopped": stopped,
        "blockers": blockers,
        "workdir": str(cwd),
    }


def latest_deployment(service: str, *, workdir: str = "", limit: int = 5) -> dict[str, Any]:
    wd = find_usable_workdir(workdir)
    if not wd.get("ok"):
        return {"ok": False, "service": service, "blockers": wd.get("errors", []), "workdir": wd.get("workdir", "")}
    cwd = Path(wd["workdir"])
    code, out, err = _run_railway(["deployment", "list", "--service", service, "--limit", str(limit), "--json"], cwd=cwd)
    if code != 0:
        return {"ok": False, "service": service, "blockers": ["railway_deployment_list_failed"], "error": (out + err).strip()[:500], "workdir": str(cwd)}
    deployments = _json_loads(out)
    if not deployments:
        return {"ok": False, "service": service, "blockers": ["railway_no_deployments"], "workdir": str(cwd)}
    dep = deployments[0]
    meta = dep.get("meta") or {}
    return {
        "ok": True,
        "service": service,
        "deployment_id": str(dep.get("id") or ""),
        "deployment_status": str(dep.get("status") or "").upper(),
        "created_at": str(dep.get("createdAt") or ""),
        "branch": str(meta.get("branch") or ""),
        "commit_hash": str(meta.get("commitHash") or ""),
        "commit_message": str(meta.get("commitMessage") or ""),
        "repo": str(meta.get("repo") or ""),
        "workdir": str(cwd),
    }


def _git_is_repo(path: Path) -> bool:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=str(path),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
        )
    except Exception:
        return False
    return proc.returncode == 0 and proc.stdout.strip() == "true"


def resolve_repo_workdir(*, repo: str = "", service: str = "", fallback_workdir: str = "") -> str:
    """Resolve the git checkout that corresponds to a Railway deployment.

    The Railway CLI may be linked from any UVISA checkout, while deployment
    metadata points at the repository that produced the service.  Ancestor checks
    must run in that producer repo, not necessarily the linked Railway cwd.
    """
    candidates: list[Path] = []
    for key in (repo, service):
        mapped = REPO_WORKDIR_DEFAULTS.get(str(key or "").strip())
        if mapped:
            candidates.append(mapped)
    if fallback_workdir:
        candidates.append(Path(fallback_workdir).expanduser())
    for p in DEFAULT_WORKDIRS:
        if p not in candidates:
            candidates.append(p)
    for path in candidates:
        if path.exists() and _git_is_repo(path):
            return str(path)
    return ""


def _git_commit_exists(workdir: Path, commit: str) -> bool:
    proc = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"{commit}^{{commit}}"],
        cwd=str(workdir),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
    )
    return proc.returncode == 0


def deployment_contains_expected_commit(expected: str, actual: str, *, repo: str = "", service: str = "", workdir: str = "") -> dict[str, Any]:
    """Return whether Railway's active deployment commit publishes expected.

    Exact/prefix match remains a fast pass.  Otherwise, use git ancestry:
    expected must be an ancestor of the latest deployed commit.  If the relevant
    checkout or commits are unavailable, fail closed; do not infer publication.
    """
    expected = (expected or "").strip()
    actual = (actual or "").strip()
    if not expected:
        return {"ok": False, "relation": "missing_expected_commit", "workdir": ""}
    if not actual:
        return {"ok": False, "relation": "missing_actual_commit", "workdir": ""}
    if actual.startswith(expected) or expected.startswith(actual):
        return {"ok": True, "relation": "exact_or_prefix", "workdir": ""}
    repo_workdir = resolve_repo_workdir(repo=repo, service=service, fallback_workdir=workdir)
    if not repo_workdir:
        return {"ok": False, "relation": "git_workdir_unavailable", "workdir": ""}
    cwd = Path(repo_workdir)
    if not _git_commit_exists(cwd, expected):
        return {"ok": False, "relation": "expected_commit_not_in_repo", "workdir": repo_workdir}
    if not _git_commit_exists(cwd, actual):
        return {"ok": False, "relation": "deployment_commit_not_in_repo", "workdir": repo_workdir}
    proc = subprocess.run(
        ["git", "merge-base", "--is-ancestor", expected, actual],
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=15,
    )
    if proc.returncode == 0:
        return {"ok": True, "relation": "ancestor", "workdir": repo_workdir}
    if proc.returncode == 1:
        return {"ok": False, "relation": "not_ancestor", "workdir": repo_workdir}
    return {"ok": False, "relation": "git_ancestor_check_failed", "workdir": repo_workdir, "error": proc.stderr.strip()[:240]}


def evaluate_gate(project: str = "", service: str = "", expected_commit: str = "", workdir: str = "") -> dict[str, Any]:
    service_name = resolve_service(project, service)
    if not service_name:
        return {"allowed": False, "service": "", "blockers": ["missing_railway_service"]}
    status = current_service_status(service_name, workdir=workdir)
    deployment = latest_deployment(service_name, workdir=workdir) if status.get("ok") else {"ok": False, "blockers": []}
    blockers = list(status.get("blockers") or []) + list(deployment.get("blockers") or [])
    expected = (expected_commit or "").strip()
    actual = str(deployment.get("commit_hash") or "").strip()
    commit_match = deployment_contains_expected_commit(
        expected,
        actual,
        repo=str(deployment.get("repo") or ""),
        service=service_name,
        workdir=status.get("workdir") or deployment.get("workdir", "") or workdir,
    )
    if expected:
        if not actual:
            blockers.append("railway_missing_deployment_commit")
        elif not commit_match.get("ok"):
            blockers.append("railway_commit_mismatch")
            relation = str(commit_match.get("relation") or "")
            if relation and relation not in {"not_ancestor", "missing_actual_commit"}:
                blockers.append(f"railway_commit_match_unverified:{relation}")
    else:
        blockers.append("missing_expected_commit")
    return {
        "allowed": not blockers,
        "service": service_name,
        "project": project,
        "expected_commit": expected,
        "blockers": blockers,
        "status": status,
        "deployment": deployment,
        "commit_match": commit_match,
        "safe_evidence": {
            "service": service_name,
            "service_status": status.get("status", ""),
            "stopped": status.get("stopped", ""),
            "deployment_id": status.get("deployment_id") or deployment.get("deployment_id", ""),
            "deployment_status": deployment.get("deployment_status", ""),
            "branch": deployment.get("branch", ""),
            "commit_hash": actual,
            "expected_commit": expected,
            "commit_match_relation": commit_match.get("relation", ""),
            "repo": deployment.get("repo", ""),
            "workdir": status.get("workdir") or deployment.get("workdir", ""),
            "repo_workdir": commit_match.get("workdir", ""),
        },
        "policy": "Railway gate passes when service is green/running and the active deployment commit exactly matches or contains the expected task commit by git ancestry.",
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Evaluate Railway deploy status and commit gate")
    p.add_argument("--project", default="")
    p.add_argument("--service", default="")
    p.add_argument("--expected-commit", default="")
    p.add_argument("--workdir", default=os.environ.get("HERMES_RAILWAY_WORKDIR", ""))
    p.add_argument("--json", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = evaluate_gate(project=args.project, service=args.service, expected_commit=args.expected_commit, workdir=args.workdir)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("ALLOWED" if result["allowed"] else "BLOCKED")
        if result.get("blockers"):
            print("blockers: " + ", ".join(result["blockers"]))
        print(json.dumps(result.get("safe_evidence", {}), ensure_ascii=False))
    return 0 if result["allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
