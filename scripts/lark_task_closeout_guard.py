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
RUNTIME_PROOF_KINDS = {"interaction", "navigation", "network", "overlay", "form", "a11y", "dom", "trace"}
NON_RUNTIME_PROOF_KINDS = {"screenshot", "image", "code", "diff", "static", "marker", "dom-snapshot-only", "text", "comment"}
NAV_ATOM_TYPES = {"nav", "navigation", "link", "route", "router"}
OVERLAY_ATOM_TYPES = {"popup", "overlay", "dialog", "drawer", "modal", "popover"}
FORM_ATOM_TYPES = {"form", "submit", "submission", "filter"}
A11Y_ATOM_TYPES = {"a11y", "accessibility", "keyboard", "focus"}


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


def _json_value(value: Any) -> Any:
    """Parse JSON from a raw string or @file reference; return [] on empty input."""
    if value is None or value == "":
        return []
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text:
        return []
    if text.startswith("@"):
        text = Path(text[1:]).expanduser().read_text()
    return json.loads(text)


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() in {"1", "true", "yes", "y", "pass", "passed", "ok", "success", "succeeded"}


def _status_good(value: Any) -> bool:
    if isinstance(value, int):
        return 200 <= value < 400
    text = str(value or "").strip().lower()
    if not text:
        return False
    if text.isdigit():
        return 200 <= int(text) < 400
    return text in GOOD_UI_STATUSES or text in GOOD_REMOTE_STATUSES


def _proof_atom_id(proof: dict[str, Any]) -> str:
    return str(proof.get("atom_id") or proof.get("criterion_id") or proof.get("acceptance_atom_id") or "").strip()


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


def evaluate_acceptance_atom_gate(evidence: dict[str, Any]) -> dict[str, Any]:
    """Fail closed unless intake constraints are proven by runtime acceptance atoms.

    Acceptance atoms are the machine-readable projection of the Lark task intake
    constraints. Screenshots, code markers, and static diffs are allowed only as
    supplemental evidence; they cannot satisfy an interactive UI atom.
    """
    blockers: list[str] = []
    warnings: list[str] = []
    try:
        atoms = _json_value(evidence.get("acceptance_atoms"))
        proofs = _json_value(evidence.get("runtime_proofs"))
    except Exception as exc:
        return {
            "allowed": False,
            "blockers": ["invalid_acceptance_atom_or_runtime_proof_json"],
            "warnings": [str(exc)],
            "atom_count": 0,
            "proof_count": 0,
            "policy": "Acceptance atoms and runtime proofs must be valid JSON; parser errors fail closed.",
        }

    atoms = atoms or []
    proofs = proofs or []
    if not isinstance(atoms, list) or not all(isinstance(a, dict) for a in atoms):
        blockers.append("acceptance_atoms_must_be_list_of_objects")
        atoms = []
    if not isinstance(proofs, list) or not all(isinstance(p, dict) for p in proofs):
        blockers.append("runtime_proofs_must_be_list_of_objects")
        proofs = []

    if not atoms:
        blockers.append("missing_acceptance_atoms")
    if atoms and not proofs:
        blockers.append("missing_runtime_proofs")

    atom_ids: set[str] = set()
    proofs_by_atom: dict[str, list[dict[str, Any]]] = {}
    for atom in atoms:
        atom_id = str(atom.get("id") or "").strip()
        if not atom_id:
            blockers.append("acceptance_atom_missing_id")
            continue
        if atom_id in atom_ids:
            blockers.append(f"duplicate_acceptance_atom_id:{atom_id}")
        atom_ids.add(atom_id)
        proofs_by_atom[atom_id] = []
        if not str(atom.get("type") or "").strip():
            blockers.append(f"acceptance_atom_missing_type:{atom_id}")
        if not str(atom.get("target_surface") or atom.get("target_route") or atom.get("text") or "").strip():
            blockers.append(f"acceptance_atom_missing_target:{atom_id}")

    for proof in proofs:
        atom_id = _proof_atom_id(proof)
        kind = _norm(proof.get("kind") or proof.get("type"))
        if not atom_id:
            blockers.append("runtime_proof_missing_atom_id")
            continue
        if atom_id not in atom_ids:
            blockers.append(f"runtime_proof_unknown_atom_id:{atom_id}")
            continue
        if kind in NON_RUNTIME_PROOF_KINDS:
            blockers.append(f"non_runtime_proof_used:{atom_id}:{kind}")
        elif kind not in RUNTIME_PROOF_KINDS:
            blockers.append(f"runtime_proof_unknown_kind:{atom_id}:{kind or 'missing'}")
        proofs_by_atom[atom_id].append(proof)

    for atom in atoms:
        atom_id = str(atom.get("id") or "").strip()
        if not atom_id:
            continue
        atom_type = _norm(atom.get("type"))
        atom_proofs = proofs_by_atom.get(atom_id, [])
        runtime_proofs = [p for p in atom_proofs if _norm(p.get("kind") or p.get("type")) in RUNTIME_PROOF_KINDS]
        if not runtime_proofs:
            blockers.append(f"acceptance_atom_missing_runtime_proof:{atom_id}")
            continue

        if atom_type in NAV_ATOM_TYPES:
            nav_proofs = [p for p in runtime_proofs if _norm(p.get("kind") or p.get("type")) in {"interaction", "navigation", "dom", "trace"}]
            clicked = any(_norm(p.get("action") or p.get("event")) in {"click", "tap", "enter", "space", "keyboard-activate"} for p in nav_proofs)
            if not clicked:
                blockers.append(f"nav_atom_missing_real_activation:{atom_id}")
            if not any(_boolish(p.get("visible")) and _boolish(p.get("hit_tested")) for p in nav_proofs if _norm(p.get("kind") or p.get("type")) == "interaction"):
                blockers.append(f"nav_atom_missing_visible_hit_tested_click:{atom_id}")
            href = next((str(p.get("href") or p.get("target_url") or "") for p in nav_proofs if str(p.get("href") or p.get("target_url") or "").strip()), "")
            current_url = next((str(p.get("url_before") or p.get("current_url") or "") for p in nav_proofs if str(p.get("url_before") or p.get("current_url") or "").strip()), "")
            if href and current_url and href == current_url:
                blockers.append(f"nav_atom_href_equals_current_url:{atom_id}")
            route_changed = any(str(p.get("url_before") or "") and str(p.get("url_after") or "") and str(p.get("url_before")) != str(p.get("url_after")) for p in nav_proofs)
            same_route_allowed = _boolish(atom.get("same_route_refresh_allowed"))
            content_refreshed = any(_boolish(p.get("content_refreshed")) or _boolish(p.get("target_content_refreshed")) or _boolish(p.get("dom_changed")) for p in nav_proofs)
            if not route_changed and not (same_route_allowed and content_refreshed):
                blockers.append(f"nav_atom_missing_route_delta:{atom_id}")
            if not content_refreshed:
                blockers.append(f"nav_atom_missing_target_content_refresh:{atom_id}")

        if atom_type in OVERLAY_ATOM_TYPES:
            if not any(_boolish(p.get("node_attached")) and _boolish(p.get("visible")) for p in runtime_proofs):
                blockers.append(f"overlay_atom_missing_visible_attached_node:{atom_id}")
            if not any(_boolish(p.get("dismissed")) or _boolish(p.get("closed")) or _boolish(p.get("removed")) for p in runtime_proofs):
                blockers.append(f"overlay_atom_missing_close_or_cleanup:{atom_id}")

        if atom_type in FORM_ATOM_TYPES:
            if not any(_boolish(p.get("fields_filled")) or _present(p.get("filled_fields")) for p in runtime_proofs):
                blockers.append(f"form_atom_missing_fill_event:{atom_id}")
            if not any(_boolish(p.get("submitted")) or _present(p.get("submit_request_id")) for p in runtime_proofs):
                blockers.append(f"form_atom_missing_submit_event:{atom_id}")
            if not any(_status_good(p.get("network_status") or p.get("status")) for p in runtime_proofs if _present(p.get("network_status") or p.get("status"))):
                blockers.append(f"form_atom_missing_green_network_response:{atom_id}")
            if not any(_boolish(p.get("post_submit_state_changed")) or _boolish(p.get("ui_changed")) for p in runtime_proofs):
                blockers.append(f"form_atom_missing_post_submit_ui_change:{atom_id}")

        if atom_type in A11Y_ATOM_TYPES or _boolish(atom.get("requires_a11y")):
            if not any(_boolish(p.get("keyboard_reachable")) for p in runtime_proofs):
                blockers.append(f"a11y_atom_missing_keyboard_reachable:{atom_id}")
            if not any(_boolish(p.get("focus_visible")) for p in runtime_proofs):
                blockers.append(f"a11y_atom_missing_focus_visible:{atom_id}")
            if not any(_boolish(p.get("semantic_ok")) or _boolish(p.get("role_and_name_ok")) for p in runtime_proofs):
                blockers.append(f"a11y_atom_missing_semantic_role_name:{atom_id}")

    return {
        "allowed": not blockers,
        "atom_count": len(atoms),
        "proof_count": len(proofs),
        "blockers": blockers,
        "warnings": warnings,
        "policy": "Every Lark intake constraint must map to runtime acceptance atoms. Interactive atoms require real browser events, route/DOM/content deltas, and a11y proof; screenshots/code/markers are supplemental only and never primary proof.",
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

    acceptance_atom_gate = evaluate_acceptance_atom_gate(evidence)
    blockers.extend(acceptance_atom_gate["blockers"])
    warnings.extend(acceptance_atom_gate["warnings"])

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
        "acceptance_atom_gate": acceptance_atom_gate,
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
    parser.add_argument("--acceptance-atoms-json", default="", help="JSON array or @file path: intake-derived atoms with id/type/target_surface")
    parser.add_argument("--runtime-proofs-json", default="", help="JSON array or @file path: browser runtime proofs mapped by atom_id")
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
        "acceptance_atoms": args.acceptance_atoms_json,
        "runtime_proofs": args.runtime_proofs_json,
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
