#!/usr/bin/env python3
"""UVISA/Lark work-loop contract: acceptance atoms + closeout state policy.

This module is intentionally side-effect free by default.  It gives the work
controller a machine-readable contract before any worker is allowed to claim a
Lark-derived UVISA task, and before any PR/Lark/TG closeout can be treated as
done.

Design goal: fail closed.  Missing atoms, missing proof mapping, unsafe branch
state, missing PR/merge/online UI proof, or missing Telegram evidence-directory
notification all block the final `done` state.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

DEFAULT_VIEWPORT = {"width": 1512, "height": 982, "label": "14-inch-admin"}
UVISA_REPOS = {
    "uvisa-admin": "/Users/charles/Desktop/folder/work/uvisa-admin",
    "uvisa-app-2.0": "/Users/charles/Desktop/folder/work/uvisa-app-2.0",
    "uvisa-backend": "/Users/charles/Desktop/folder/work/uvisa-backend",
}
PROTECTED_BRANCHES = {"main", "master", "production", "prod"}
UVISA_PROJECT_PROFILE = "/Users/charles/.hermes/project-profiles/uvisa-app-2.0.json"
SOURCE_WEIGHTING_POLICY = {
    "project_profile_ref": UVISA_PROJECT_PROFILE,
    "source_weighting_policy_ref": UVISA_PROJECT_PROFILE + "#source_weighting_policy",
    "ranked_sources": [
        {
            "rank": 1,
            "source": "latest product document / PRD / canonical project profile",
            "authority": "business semantics, money/status/accounting rules, permissions, state transitions",
            "required_evidence": "product_doc_evidence or explicit product-doc-missing marker",
        },
        {
            "rank": 2,
            "source": "prototype / PM screenshot / Lark comment image",
            "authority": "UI layout, interaction flow, visual parity, component/empty/loading/error states",
            "required_evidence": "prototype_evidence when UI/interaction parity is in scope",
        },
        {
            "rank": 3,
            "source": "live Lark task title/body/comments",
            "authority": "task symptom, reproduction example, affected surface, assignee/scope metadata",
            "required_evidence": "lark_evidence from live Lark payload, not generated summary alone",
        },
        {
            "rank": 4,
            "source": "current implementation/runtime behavior",
            "authority": "actual landing surface and regression proof",
            "required_evidence": "code/test/browser evidence; cannot redefine expected product behavior by itself",
        },
    ],
    "conflict_rule": "If product doc, prototype, Lark, or implementation disagree, record evidence and block for product confirmation unless rank-1 source clearly resolves it.",
}
FINAL_STATES = [
    "pending",
    "planned",
    "leased",
    "running",
    "worker_done_pending_proof",
    "proof_verified",
    "pr_opened",
    "merge_queued",
    "merged",
    "online_regression_verified",
    "lark_closed",
    "tg_notified",
    "done",
]

DATA_HINTS = ("总数", "合计", "统计", "count", "total", "badge", "kpi", "sum", "一致", "相等", "对等")
UI_HINTS = ("页面", "按钮", "弹窗", "下拉", "筛选", "表格", "tab", "标签", "展示", "显示", "对齐", "颜色", "文案")
NAV_HINTS = ("跳转", "返回", "进入", "导航", "链接", "详情")
FORM_HINTS = ("筛选", "搜索", "提交", "输入", "选择", "下拉", "表单")
A11Y_HINTS = ("键盘", "焦点", "无障碍", "a11y", "accessibility")
API_HINTS = ("接口", "api", "后端", "字段", "响应", "返回", "权限", "鉴权")


def _norm(s: Any) -> str:
    return str(s or "").strip()


def _lower(s: Any) -> str:
    return _norm(s).lower()


def _contains_any(text: str, hints: tuple[str, ...]) -> bool:
    low = text.lower()
    return any(h.lower() in low for h in hints)


def _json_arg(value: str | None) -> Any:
    if not value:
        return None
    value = value.strip()
    if value.startswith("@"):
        return json.loads(Path(value[1:]).expanduser().read_text())
    return json.loads(value)


def _git(repo: str, *args: str) -> tuple[int, str, str]:
    try:
        p = subprocess.run(["git", "-C", repo, *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except Exception as exc:  # pragma: no cover - defensive for missing repos
        return 99, "", str(exc)


@dataclass
class AcceptanceAtom:
    id: str
    type: str
    target_surface: str
    requirement: str
    proof_type: str
    required_runtime_kinds: list[str]
    required_artifacts: list[str]
    fail_closed_if_missing: bool = True


@dataclass
class WorkContract:
    schema: str
    task_id: str
    lark_task_guid: str
    title: str
    task_type: str
    repos: list[str]
    branch_namespace: str
    target_surface: str
    viewport: dict[str, Any]
    acceptance_atoms: list[dict[str, Any]]
    required_closeout_states: list[str]
    closeout_blockers: list[str]
    proof_policy: dict[str, Any]
    source_weighting_policy: dict[str, Any]


def infer_task_type(text: str) -> str:
    if _contains_any(text, DATA_HINTS):
        return "data_correctness"
    if _contains_any(text, API_HINTS):
        return "api_contract"
    if _contains_any(text, UI_HINTS + NAV_HINTS + FORM_HINTS + A11Y_HINTS):
        return "ui_regression"
    return "general_change"


def infer_repos(text: str) -> list[str]:
    low = text.lower()
    repos: list[str] = []
    if any(k in low for k in ["admin", "管理端", "后台", "业绩", "理财师", "用户管理"]):
        repos.append("uvisa-admin")
    if any(k in low for k in ["h5", "app", "移动端", "用户端", "钱包", "充值", "提现"]):
        repos.append("uvisa-app-2.0")
    if any(k in low for k in ["backend", "后端", "api", "接口", "权限", "数据库", "字段"]):
        repos.append("uvisa-backend")
    return repos or ["uvisa-admin"]


def infer_surface(title: str, body: str) -> str:
    text = f"{title}\n{body}"
    patterns = [
        r"(?:页面|模块|tab|标签|列表|详情|弹窗|筛选|表格)[：: ]*([^\n，,。；;]{2,40})",
        r"(用户详情[^\n，,。；;]{0,20})",
        r"(业绩统计[^\n，,。；;]{0,20})",
        r"(理财师[^\n，,。；;]{0,20})",
        r"(钱包流水[^\n，,。；;]{0,20})",
        r"(交易[^\n，,。；;]{0,20})",
    ]
    for pat in patterns:
        m = re.search(pat, text, flags=re.I)
        if m:
            return m.group(1).strip()
    return title[:80] or "unknown_surface"


def _atom(atom_id: str, typ: str, surface: str, req: str, proof_type: str, runtime: list[str], artifacts: list[str]) -> AcceptanceAtom:
    return AcceptanceAtom(atom_id, typ, surface, req, proof_type, runtime, artifacts)


def generate_acceptance_atoms(task_id: str, title: str, body: str = "", lark_task_guid: str = "", iceberg_tier: str = "") -> WorkContract:
    text = f"{title}\n{body}"
    task_type = infer_task_type(text)
    repos = infer_repos(text)
    surface = infer_surface(title, body)
    short_id = re.sub(r"[^a-zA-Z0-9_-]+", "-", (lark_task_guid or task_id or "uvisa-task"))[:40].strip("-") or "uvisa-task"
    branch_namespace = f"work/uvisa-lark-loop/{short_id}"
    atoms: list[AcceptanceAtom] = []

    atoms.append(_atom(
        "A-target-surface",
        "dom",
        surface,
        "线上证据必须命中 Lark 任务指定的页面/模块/筛选状态，不能用泛化截图替代。",
        "target_surface_binding",
        ["dom", "trace"],
        ["online_dom_snapshot", "14inch_screenshot"],
    ))

    if task_type == "data_correctness":
        atoms.append(_atom(
            "A-source-to-sink-equality",
            "data_correctness",
            surface,
            "统计/KPI/total/badge 等展示值必须与源列表/API 在同一筛选条件下相等。",
            "source_to_sink_equality",
            ["network", "dom", "trace"],
            ["captured_source_value", "captured_sink_value", "assertion_json"],
        ))
    elif task_type == "api_contract":
        atoms.append(_atom(
            "A-live-api-contract",
            "api_contract",
            surface,
            "真实登录态 API 返回字段、状态码、权限边界与 UI 消费契约一致。",
            "live_api_contract",
            ["network", "trace"],
            ["request_response_capture", "schema_assertion"],
        ))
    else:
        atoms.append(_atom(
            "A-ui-regression",
            "ui_regression",
            surface,
            "14寸真实线上 UI 回归通过，目标控件/文案/布局可见且未破坏相邻功能。",
            "online_ui_regression",
            ["interaction", "dom", "trace"],
            ["1512x982_screenshot", "browser_report"],
        ))

    if _contains_any(text, NAV_HINTS):
        atoms.append(_atom("A-navigation", "nav", surface, "导航/跳转必须由可见且命中测试通过的真实点击触发，并产生路由或内容刷新。", "browser_navigation", ["interaction", "navigation", "dom"], ["trace", "route_delta"]))
    if _contains_any(text, FORM_HINTS):
        atoms.append(_atom("A-form-flow", "form", surface, "筛选/表单必须经过填充、提交、绿色网络响应和提交后 UI 变化。", "browser_form_flow", ["form", "network", "dom"], ["trace", "network_capture"]))
    if _contains_any(text, A11Y_HINTS):
        atoms.append(_atom("A-a11y", "a11y", surface, "交互控件必须具备键盘可达、可见焦点和 role/name 语义。", "browser_a11y_runtime", ["a11y", "interaction"], ["a11y_report"]))

    # Iceberg-tier-aware atoms: L tasks need backend contract verification
    tier = iceberg_tier.upper() if iceberg_tier else ""
    if tier == "L":
        atoms.append(_atom(
            "A-backend-contract",
            "backend_contract",
            surface,
            "涉及后端/接口的任务必须验证：真实 API 返回字段与前端消费契约一致，金额/状态/币种等业务语义正确。",
            "backend_contract_verification",
            ["network", "trace"],
            ["api_request_response", "business_semantics_assertion"],
        ))
    if tier == "B":
        atoms.append(_atom(
            "A-human-confirmation",
            "human_gate",
            surface,
            "需要人工确认的任务必须在继续前获得用户明确授权/owner 归属。",
            "human_confirmation",
            ["user_input"],
            ["confirmation_record"],
        ))

    blockers = [
        "missing_acceptance_atoms",
        "missing_runtime_proofs",
        "missing_pr_url",
        "missing_merge_commit",
        "missing_online_regression_evidence",
        "missing_lark_close_response",
        "missing_tg_evidence_dir_notification",
    ]
    return WorkContract(
        schema="uvisa_lark_work_contract_v1",
        task_id=task_id,
        lark_task_guid=lark_task_guid,
        title=title,
        task_type=task_type,
        repos=repos,
        branch_namespace=branch_namespace,
        target_surface=surface,
        viewport=dict(DEFAULT_VIEWPORT),
        acceptance_atoms=[asdict(a) for a in atoms],
        required_closeout_states=list(FINAL_STATES),
        closeout_blockers=blockers,
        proof_policy={
            "worker_can_mark_done": False,
            "controller_owns_state_transitions": True,
            "same_repo_parallel_writes_require_worktree": True,
            "same_repo_merges_are_serial": True,
            "lark_close_requires_online_ui_retest": True,
            "tg_notification_requires_evidence_directory": True,
            "project_profile_preflight_required": True,
            "source_weighting_policy_required": True,
        },
        source_weighting_policy=json.loads(json.dumps(SOURCE_WEIGHTING_POLICY, ensure_ascii=False)),
    )


def evaluate_branch_governance(contract: dict[str, Any], repo_paths: dict[str, str] | None = None) -> dict[str, Any]:
    repo_paths = repo_paths or UVISA_REPOS
    blockers: list[str] = []
    repos = contract.get("repos") or []
    ns = _norm(contract.get("branch_namespace"))
    details = []
    for repo in repos:
        path = str(repo_paths.get(repo, repo))
        rc, branch, err = _git(path, "branch", "--show-current")
        dirty_rc, dirty, _ = _git(path, "status", "--short")
        wt_rc, worktrees, _ = _git(path, "worktree", "list")
        repo_blockers = []
        if rc != 0 or not branch:
            repo_blockers.append("missing_current_branch")
        elif branch in PROTECTED_BRANCHES:
            repo_blockers.append("on_protected_base_branch")
        elif ns and branch != ns:
            repo_blockers.append("branch_not_contract_namespace")
        if dirty_rc == 0 and dirty.strip():
            repo_blockers.append("dirty_primary_worktree")
        if wt_rc != 0 or not worktrees.strip():
            repo_blockers.append("missing_worktree_listing")
        blockers.extend([f"{repo}:{b}" for b in repo_blockers])
        details.append({"repo": repo, "path": path, "branch": branch, "dirty": bool(dirty.strip()), "worktrees": worktrees.splitlines(), "blockers": repo_blockers, "error": err})
    return {"allowed": not blockers, "blockers": blockers, "details": details, "required_branch_namespace": ns, "policy": "Every UVISA task contract maps to one branch namespace; worker writes must happen in isolated worktrees and merges must be serialized per repo."}


def evaluate_closeout_bundle(contract: dict[str, Any], bundle: dict[str, Any]) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    atoms = contract.get("acceptance_atoms") or []
    atom_ids = {a.get("id") for a in atoms if isinstance(a, dict)}
    proofs = bundle.get("runtime_proofs") or []
    proof_ids = {p.get("atom_id") or p.get("acceptance_atom_id") for p in proofs if isinstance(p, dict)}
    if not atoms:
        blockers.append("missing_acceptance_atoms")
    missing = sorted(str(a) for a in atom_ids if a and a not in proof_ids)
    if missing:
        blockers.append("unmapped_acceptance_atoms:" + ",".join(missing))
    for key in ["pr_url", "merge_commit", "online_regression_dir", "online_ui_evidence", "lark_close_response", "tg_notification"]:
        if not bundle.get(key):
            blockers.append(f"missing_{key}")
    vp = bundle.get("viewport") or {}
    if vp.get("width") != 1512 or vp.get("height") != 982:
        blockers.append("viewport_not_14inch_1512x982")
    if not bundle.get("evidence_dir"):
        blockers.append("missing_evidence_dir")
    elif not Path(str(bundle["evidence_dir"])).expanduser().exists():
        warnings.append("evidence_dir_not_found_on_local_disk")
    return {"allowed": not blockers, "blockers": blockers, "warnings": warnings, "atom_count": len(atoms), "proof_count": len(proofs), "state": "done" if not blockers else "blocked", "policy": "done requires PR, merge, online regression evidence, Lark close response, and Telegram evidence-directory notification."}


def _row_text(row: dict[str, Any]) -> str:
    parts = [row.get("title"), row.get("body"), row.get("description"), row.get("project"), row.get("source")]
    return "\n".join(_norm(p) for p in parts if _norm(p))


def _is_uvisa_lark_work_row(row: dict[str, Any]) -> bool:
    text = _row_text(row).lower()
    has_lark = bool(row.get("lark_task_guid") or row.get("lark_task_url") or "lark" in text or "飞书" in text)
    has_uvisa = any(k in text for k in ("uvisa", "uvisa-admin", "uvisa-app", "管理端", "uv 2.0", "uvisa-2.0"))
    return has_lark and has_uvisa


def _contract_file_name(task_id: str, lark_task_guid: str) -> str:
    raw = lark_task_guid or task_id or "uvisa-lark-task"
    safe = re.sub(r"[^a-zA-Z0-9_.-]+", "-", raw).strip("-._") or "uvisa-lark-task"
    return safe[:80] + ".contract.json"


def extract_lark_guid(*values: Any) -> str:
    text = " ".join(_norm(v) for v in values if _norm(v))
    m = re.search(r"\[\s*lark\s+([0-9a-f]{6,12})\s*\]", text, flags=re.I)
    if not m:
        m = re.search(r"\blark[-_\s:]+([0-9a-f]{6,12})\b", text, flags=re.I)
    return m.group(1) if m else ""


def ingest_task_rows(rows: list[dict[str, Any]], out_dir: str | Path) -> dict[str, Any]:
    """Generate contract files for UVISA/Lark rows and write a manifest.

    This is the deterministic intake seam used before agentTeam can claim work:
    every Lark-derived UVISA task gets machine-readable acceptance atoms, while
    unrelated Hermes/evolution rows are skipped instead of polluting the work lane.
    """
    root = Path(out_dir).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    created: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            skipped.append({"reason": "row_not_object", "row_repr": repr(row)[:200]})
            continue
        task_id = _norm(row.get("id") or row.get("task_id") or row.get("uid"))
        title = _norm(row.get("title") or row.get("summary") or task_id)
        body = _norm(row.get("body") or row.get("description") or row.get("content"))
        lark_guid = _norm(row.get("lark_task_guid") or row.get("guid") or row.get("lark_guid")) or extract_lark_guid(row.get("id"), title, body)
        if not _is_uvisa_lark_work_row(row):
            skipped.append({"task_id": task_id, "title": title, "reason": "not_uvisa_lark_work"})
            continue
        contract = generate_acceptance_atoms(task_id=task_id, title=title, body=body, lark_task_guid=lark_guid, iceberg_tier=str(row.get("iceberg_tier") or ""))
        data = asdict(contract)
        data["source_row"] = {k: row.get(k) for k in ("id", "task_id", "project", "lark_task_guid", "lark_task_url", "title") if k in row}
        path = root / _contract_file_name(task_id, lark_guid)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        created.append({
            "task_id": task_id,
            "lark_task_guid": lark_guid,
            "title": title,
            "task_type": contract.task_type,
            "repos": contract.repos,
            "contract_path": str(path),
        })
    manifest = {
        "schema": "uvisa_lark_work_contract_manifest_v1",
        "created_count": len(created),
        "skipped_count": len(skipped),
        "created": created,
        "skipped": skipped,
        "policy": "Only UVISA/Lark work rows receive contracts; claim/closeout must fail closed without a contract path.",
    }
    (root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return manifest


def _extract_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [r for r in payload if isinstance(r, dict)]
    if isinstance(payload, dict):
        for key in ("rows", "tasks", "items", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return [r for r in value if isinstance(r, dict)]
    raise ValueError("tasks JSON must be a list or an object containing rows/tasks/items/data")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="UVISA/Lark work-loop contract generator and validator")
    sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate")
    g.add_argument("--task-id", required=True)
    g.add_argument("--lark-task-guid", default="")
    g.add_argument("--title", required=True)
    g.add_argument("--body", default="")
    g.add_argument("--out", default="")
    b = sub.add_parser("branch-check")
    b.add_argument("--contract", required=True, help="JSON string or @file")
    c = sub.add_parser("closeout-check")
    c.add_argument("--contract", required=True, help="JSON string or @file")
    c.add_argument("--bundle", required=True, help="JSON string or @file")
    i = sub.add_parser("ingest-tasks")
    i.add_argument("--tasks-json", required=True, help="JSON list/object or @file containing task rows")
    i.add_argument("--out-dir", required=True, help="Directory for generated per-task contracts and manifest.json")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "generate":
        contract = generate_acceptance_atoms(args.task_id, args.title, args.body, args.lark_task_guid)
        data = asdict(contract)
        text = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)
        if args.out:
            Path(args.out).expanduser().write_text(text + "\n")
        print(text)
        return 0
    if args.cmd == "branch-check":
        result = evaluate_branch_governance(_json_arg(args.contract))
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if result["allowed"] else 2
    if args.cmd == "closeout-check":
        result = evaluate_closeout_bundle(_json_arg(args.contract), _json_arg(args.bundle))
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if result["allowed"] else 2
    if args.cmd == "ingest-tasks":
        result = ingest_task_rows(_extract_rows(_json_arg(args.tasks_json)), args.out_dir)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
