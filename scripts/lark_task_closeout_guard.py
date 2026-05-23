#!/usr/bin/env python3
"""Fail-closed guard for Lark task final closeout.

This module intentionally does not call the Lark API.  It validates whether a
caller is allowed to perform the external side effect (`PATCH /task/v2/tasks/*`
with `completed_at`).  Local implementation / regression proof is not enough:
final Lark completion requires a user-dispatched online UI retest with online
evidence.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

FINAL_PHASES = {"online-ui-retest", "online_ui_retest", "online"}
IMPLEMENTATION_PHASES = {"implementation", "impl", "local-regression", "local_regression", "sendback"}
GOOD_REMOTE_STATUSES = {"success", "succeeded", "pass", "passed", "deployed", "ready", "green"}
GOOD_UI_STATUSES = {"pass", "passed", "success", "succeeded", "green"}
PROTECTED_BASE_BRANCHES = {"main", "master"}


def _git_current_branch(repo_path: str | None) -> str:
    if not repo_path:
        return ""
    try:
        proc = subprocess.run(
            ["git", "-C", str(Path(repo_path).expanduser()), "branch", "--show-current"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
        )
    except Exception:
        return ""
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def evaluate_implementation_branch_gate(evidence: dict[str, Any]) -> dict[str, Any]:
    """Fail closed unless local implementation work is on a non-main task branch."""
    current_branch = str(evidence.get("current_branch") or "").strip()
    if not current_branch:
        current_branch = _git_current_branch(str(evidence.get("repo_path") or "").strip() or None)
    base_branch = str(evidence.get("base_branch") or "main").strip() or "main"
    protected = sorted(set(PROTECTED_BASE_BRANCHES) | {base_branch})
    blockers: list[str] = []
    if not current_branch:
        blockers.append("missing_current_branch")
    elif current_branch in protected:
        blockers.append("local_implementation_on_protected_base_branch")
    return {
        "allowed": not blockers,
        "current_branch": current_branch,
        "base_branch": base_branch,
        "protected_base_branches": protected,
        "blockers": blockers,
        "required_action": "ok" if not blockers else "fetch_and_checkout_task_branch_before_local_fix",
        "policy": "Local implementation fixes must run on a non-main task branch. If currently on main after a PR merge/deleted branch, fetch the latest base and checkout/create the shared task-loop branch before editing.",
    }


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return bool(value)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return list(value)
    return [value]


def _norm(value: Any) -> str:
    return str(value or "").strip().lower().replace("_", "-")


def _surface_token(value: Any) -> str:
    """Normalize page/module labels for conservative target binding checks."""
    text = _norm(value)
    for ch in ['“', '”', '"', "'", " ", "　", "/", "_", "·", "-", "—", "–", ">", "＞", "：", ":", "，", ",", "。", ".", "（", "）", "(", ")"]:
        text = text.replace(ch, "")
    return text


def _surface_parts(value: str) -> list[str]:
    raw = str(value or "")
    for sep in ["＞", "/", "\\", "|", "→", "-", "—", "–"]:
        raw = raw.replace(sep, ">")
    return [part.strip() for part in raw.split(">") if part.strip()]


def _has_surface_match(expected: str, actual: str) -> bool:
    exp = _surface_token(expected)
    act = _surface_token(actual)
    if not exp or not act:
        return False
    parts = _surface_parts(expected)
    # For hierarchical task targets, require the evidence/code to reach the leaf
    # surface (detail tab/modal), not merely the parent list page.
    if len(parts) > 1:
        leaf = _surface_token(parts[-1])
        parent_leaf = _surface_token("".join(parts[-2:]))
        return bool(leaf and leaf in act) or bool(parent_leaf and parent_leaf in act)
    return exp in act or act in exp


def evaluate_target_binding_gate(evidence: dict[str, Any]) -> dict[str, Any]:
    """Fail closed unless task, code, and UI evidence are bound to the same target surface.

    This catches the class of mistakes where a Lark task targets e.g. 用户详情/钱包流水,
    but the closeout screenshot is only 用户列表, or where the target page is inaccessible
    and a generic screenshot is attached anyway.
    """
    blockers: list[str] = []
    warnings: list[str] = []
    task_surface = str(evidence.get("task_target_surface") or "").strip()
    evidence_surface = str(evidence.get("evidence_target_surface") or "").strip()
    code_surface = str(evidence.get("code_target_surface") or "").strip()
    access_status = _norm(evidence.get("evidence_access_status") or "pass")
    required_keywords = [str(x).strip() for x in _as_list(evidence.get("required_evidence_keyword")) if str(x).strip()]
    observed_keywords = [str(x).strip() for x in _as_list(evidence.get("observed_evidence_keyword")) if str(x).strip()]

    if not task_surface:
        blockers.append("missing_task_target_surface")
    if not evidence_surface:
        blockers.append("missing_evidence_target_surface")
    if task_surface and evidence_surface and not _has_surface_match(task_surface, evidence_surface):
        blockers.append("evidence_target_surface_mismatch")
    if code_surface and task_surface and not _has_surface_match(task_surface, code_surface):
        blockers.append("code_target_surface_mismatch")
    if access_status in {"denied", "forbidden", "unauthorized", "no-permission", "permission-denied", "blocked"}:
        blockers.append("target_page_access_not_verified")
    if required_keywords:
        observed_blob = _surface_token(" ".join(observed_keywords))
        missing = [kw for kw in required_keywords if _surface_token(kw) not in observed_blob]
        if missing:
            blockers.append("missing_required_evidence_keywords")
            warnings.append("missing_keywords:" + ",".join(missing[:10]))

    return {
        "allowed": not blockers,
        "task_target_surface": task_surface,
        "evidence_target_surface": evidence_surface,
        "code_target_surface": code_surface,
        "evidence_access_status": access_status,
        "required_evidence_keywords": required_keywords,
        "observed_evidence_keywords": observed_keywords,
        "blockers": blockers,
        "warnings": warnings,
        "policy": "Final UVISA/admin UI closeout requires target-bound evidence: task page/module, code surface, and screenshot/DOM surface must match; inaccessible pages cannot be closed with generic screenshots.",
    }


def evaluate_closeout_gate(evidence: dict[str, Any]) -> dict[str, Any]:
    """Return a fail-closed decision for external Lark completion.

    Required for `allowed=True`:
    - phase is online-ui-retest, not implementation/local regression
    - explicit user dispatch evidence exists
    - remote build/deploy is terminal green
    - online URL is recorded
    - online UI screenshot/report evidence exists
    - UI regression status is terminal green
    - final Lark evidence/comment/description text is prepared
    """
    phase = _norm(evidence.get("phase"))
    blockers: list[str] = []
    warnings: list[str] = []

    if phase in IMPLEMENTATION_PHASES or phase not in FINAL_PHASES:
        classification = "implementation_sendback_only" if phase in IMPLEMENTATION_PHASES else "unknown_phase"
        blockers.append("online_ui_retest_required")
        if phase not in IMPLEMENTATION_PHASES and phase not in FINAL_PHASES:
            blockers.append("unknown_or_missing_closeout_phase")
        result = {
            "allowed": False,
            "classification": classification,
            "phase": phase or "",
            "blockers": blockers,
            "warnings": warnings,
            "lark_completed_at_allowed": False,
            "policy": "Local implementation/regression evidence may update implementation notes/TG, but must not PATCH Lark completed_at.",
        }
        if phase in IMPLEMENTATION_PHASES:
            result["implementation_branch_gate"] = evaluate_implementation_branch_gate(evidence)
        return result

    classification = "final_lark_closeout_candidate"
    if not _present(evidence.get("user_dispatch_evidence")):
        blockers.append("missing_user_dispatch_evidence")

    remote_status = _norm(evidence.get("remote_build_status"))
    if remote_status not in GOOD_REMOTE_STATUSES:
        blockers.append("missing_or_non_green_remote_build_status")

    if not _present(evidence.get("online_url")):
        blockers.append("missing_online_url")

    online_evidence = _as_list(evidence.get("online_ui_evidence") or evidence.get("screenshot") or evidence.get("report"))
    if not any(_present(item) for item in online_evidence):
        blockers.append("missing_online_ui_screenshot_or_report")

    ui_status = _norm(evidence.get("ui_regression_status"))
    if ui_status not in GOOD_UI_STATUSES:
        blockers.append("missing_or_non_green_ui_regression_status")

    if not _present(evidence.get("lark_final_evidence")):
        blockers.append("missing_lark_final_evidence_text")

    target_binding = evaluate_target_binding_gate(evidence)
    blockers.extend(target_binding["blockers"])
    warnings.extend(target_binding["warnings"])

    allowed = not blockers
    if allowed:
        classification = "final_lark_closeout_allowed"

    return {
        "allowed": allowed,
        "classification": classification,
        "phase": phase,
        "blockers": blockers,
        "warnings": warnings,
        "target_binding_gate": target_binding,
        "lark_completed_at_allowed": allowed,
        "policy": "Only a user-dispatched online UI retest with target-bound online evidence may drive final Lark description + completed_at writeback.",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate whether Lark task final completion is allowed.")
    parser.add_argument("--phase", required=True, help="implementation or online-ui-retest")
    parser.add_argument("--user-dispatch-evidence", default="")
    parser.add_argument("--remote-build-status", default="")
    parser.add_argument("--online-url", default="")
    parser.add_argument("--online-ui-evidence", action="append", default=[])
    parser.add_argument("--screenshot", action="append", default=[])
    parser.add_argument("--report", action="append", default=[])
    parser.add_argument("--ui-regression-status", default="")
    parser.add_argument("--lark-final-evidence", default="")
    parser.add_argument("--task-target-surface", default="", help="Exact page/module named by the Lark task, e.g. 用户列表>用户详情>钱包流水")
    parser.add_argument("--code-target-surface", default="", help="Page/module represented by the changed code surface")
    parser.add_argument("--evidence-target-surface", default="", help="Page/module actually shown by screenshot/DOM evidence")
    parser.add_argument("--evidence-access-status", default="pass", help="pass/denied/forbidden/unauthorized/etc for the target page")
    parser.add_argument("--required-evidence-keyword", action="append", default=[], help="Keyword/field that must be visible in the evidence for this task")
    parser.add_argument("--observed-evidence-keyword", action="append", default=[], help="Keyword/field actually visible in screenshot/DOM evidence")
    parser.add_argument("--local-verification", action="append", default=[])
    parser.add_argument("--commit", default="")
    parser.add_argument("--repo-path", default="", help="Git repo to inspect for implementation branch safety")
    parser.add_argument("--current-branch", default="", help="Override detected git branch for implementation branch safety")
    parser.add_argument("--base-branch", default="main", help="Protected deployment/base branch; implementation must not run here")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    evidence = {
        "phase": args.phase,
        "user_dispatch_evidence": args.user_dispatch_evidence,
        "remote_build_status": args.remote_build_status,
        "online_url": args.online_url,
        "online_ui_evidence": [*args.online_ui_evidence, *args.screenshot, *args.report],
        "ui_regression_status": args.ui_regression_status,
        "lark_final_evidence": args.lark_final_evidence,
        "task_target_surface": args.task_target_surface,
        "code_target_surface": args.code_target_surface,
        "evidence_target_surface": args.evidence_target_surface,
        "evidence_access_status": args.evidence_access_status,
        "required_evidence_keyword": args.required_evidence_keyword,
        "observed_evidence_keyword": args.observed_evidence_keyword,
        "local_verification": args.local_verification,
        "commit": args.commit,
        "repo_path": args.repo_path,
        "current_branch": args.current_branch,
        "base_branch": args.base_branch,
    }
    result = evaluate_closeout_gate(evidence)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("ALLOWED" if result["allowed"] else "BLOCKED")
        if result["blockers"]:
            print("blockers: " + ", ".join(result["blockers"]))
        print(result["policy"])
    return 0 if result["allowed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
