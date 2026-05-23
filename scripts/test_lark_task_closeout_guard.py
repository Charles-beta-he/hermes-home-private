import importlib.util
import json
import subprocess
import sys
from pathlib import Path

MODULE_PATH = Path.home() / ".hermes" / "scripts" / "lark_task_closeout_guard.py"


def load_module():
    spec = importlib.util.spec_from_file_location("lark_task_closeout_guard", MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_local_implementation_regression_must_not_complete_lark_task():
    mod = load_module()
    result = mod.evaluate_closeout_gate({
        "phase": "implementation",
        "local_verification": ["npm run build PASS", "browser-harness local PASS"],
        "commit": "abc1234",
        "remote_build_status": "success",
    })
    assert result["allowed"] is False
    assert result["classification"] == "implementation_sendback_only"
    assert "online_ui_retest_required" in result["blockers"]
    assert result["lark_completed_at_allowed"] is False


def test_implementation_phase_requires_non_main_task_branch():
    mod = load_module()
    main_result = mod.evaluate_closeout_gate({
        "phase": "implementation",
        "current_branch": "main",
        "base_branch": "main",
    })
    assert main_result["lark_completed_at_allowed"] is False
    assert main_result["implementation_branch_gate"]["allowed"] is False
    assert "local_implementation_on_protected_base_branch" in main_result["implementation_branch_gate"]["blockers"]
    assert "fetch_and_checkout_task_branch" in main_result["implementation_branch_gate"]["required_action"]

    feature_result = mod.evaluate_closeout_gate({
        "phase": "implementation",
        "current_branch": "lark-task-loop",
        "base_branch": "main",
    })
    assert feature_result["lark_completed_at_allowed"] is False
    assert feature_result["implementation_branch_gate"]["allowed"] is True
    assert feature_result["implementation_branch_gate"]["blockers"] == []


def test_cli_reports_current_branch_gate_for_implementation_phase():
    proc = subprocess.run(
        [
            sys.executable,
            str(MODULE_PATH),
            "--phase",
            "implementation",
            "--current-branch",
            "main",
            "--base-branch",
            "main",
            "--json",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.returncode == 2
    payload = json.loads(proc.stdout)
    assert payload["implementation_branch_gate"]["allowed"] is False
    assert "local_implementation_on_protected_base_branch" in payload["implementation_branch_gate"]["blockers"]


def test_online_ui_retest_requires_user_dispatch_and_online_evidence():
    mod = load_module()
    result = mod.evaluate_closeout_gate({
        "phase": "online-ui-retest",
        "local_verification": ["npm run build PASS"],
        "remote_build_status": "success",
        "online_url": "https://uvisa-admin-production.example/users",
        "ui_regression_status": "pass",
    })
    assert result["allowed"] is False
    assert "missing_user_dispatch_evidence" in result["blockers"]
    assert "missing_online_ui_screenshot_or_report" in result["blockers"]


def test_complete_online_ui_retest_allows_lark_completed_at():
    mod = load_module()
    result = mod.evaluate_closeout_gate({
        "phase": "online-ui-retest",
        "user_dispatch_evidence": "user said dispatch online UI retest",
        "remote_build_status": "deployed",
        "online_url": "https://uvisa-admin-production.example/users/UA888001/wallet",
        "online_ui_evidence": ["/tmp/uvisa-admin-online-user-detail-wallet-1512x982.png"],
        "ui_regression_status": "pass",
        "lark_final_evidence": "description contains online UI evidence",
        "task_target_surface": "用户列表>用户详情>钱包流水",
        "code_target_surface": "用户详情钱包流水",
        "evidence_target_surface": "用户详情钱包流水",
        "required_evidence_keyword": ["TXN_ID", "查看详情"],
        "observed_evidence_keyword": ["TXN_ID", "查看详情", "状态"],
        "acceptance_atoms": [
            {"id": "nav-wallet-owner", "type": "nav", "target_surface": "用户详情钱包流水用户姓名跳转", "requires_a11y": True},
        ],
        "runtime_proofs": [
            {"atom_id": "nav-wallet-owner", "kind": "interaction", "action": "click", "visible": True, "hit_tested": True, "href": "https://uvisa-admin-production.example/users/UB888002", "url_before": "https://uvisa-admin-production.example/users/UA888001/wallet"},
            {"atom_id": "nav-wallet-owner", "kind": "navigation", "url_before": "https://uvisa-admin-production.example/users/UA888001/wallet", "url_after": "https://uvisa-admin-production.example/users/UB888002", "target_content_refreshed": True},
            {"atom_id": "nav-wallet-owner", "kind": "a11y", "keyboard_reachable": True, "focus_visible": True, "semantic_ok": True},
        ],
    })
    assert result["allowed"] is True
    assert result["classification"] == "final_lark_closeout_allowed"
    assert result["lark_completed_at_allowed"] is True


def test_online_ui_retest_blocks_mismatched_page_evidence():
    mod = load_module()
    result = mod.evaluate_closeout_gate({
        "phase": "online-ui-retest",
        "user_dispatch_evidence": "user said dispatch online UI retest",
        "remote_build_status": "deployed",
        "online_url": "https://uvisa-admin-production.example/users",
        "online_ui_evidence": ["/tmp/uvisa-admin-online-users-list-1512x982.png"],
        "ui_regression_status": "pass",
        "lark_final_evidence": "description contains online UI evidence",
        "task_target_surface": "用户列表>用户详情>钱包流水",
        "code_target_surface": "用户详情钱包流水",
        "evidence_target_surface": "用户列表",
        "required_evidence_keyword": ["TXN_ID", "查看详情"],
        "observed_evidence_keyword": ["用户列表", "UID"],
    })
    assert result["allowed"] is False
    assert result["lark_completed_at_allowed"] is False
    assert "evidence_target_surface_mismatch" in result["blockers"]
    assert "missing_required_evidence_keywords" in result["blockers"]


def test_online_ui_retest_blocks_permission_denied_page():
    mod = load_module()
    result = mod.evaluate_closeout_gate({
        "phase": "online-ui-retest",
        "user_dispatch_evidence": "user said dispatch online UI retest",
        "remote_build_status": "deployed",
        "online_url": "https://uvisa-admin-production.example/channel-payouts",
        "online_ui_evidence": ["/tmp/uvisa-admin-channel-payout-permission-denied.png"],
        "ui_regression_status": "pass",
        "lark_final_evidence": "description contains online UI evidence",
        "task_target_surface": "通道代付记录",
        "code_target_surface": "通道代付记录",
        "evidence_target_surface": "通道代付记录",
        "evidence_access_status": "denied",
        "required_evidence_keyword": ["GSalary", "通道状态"],
        "observed_evidence_keyword": ["无权限"],
    })
    assert result["allowed"] is False
    assert "target_page_access_not_verified" in result["blockers"]


def test_acceptance_atom_blocks_screenshot_or_code_only_nav_proof():
    mod = load_module()
    result = mod.evaluate_acceptance_atom_gate({
        "acceptance_atoms": [
            {"id": "nav-owner", "type": "nav", "target_surface": "用户详情钱包流水用户姓名跳转"},
        ],
        "runtime_proofs": [
            {"atom_id": "nav-owner", "kind": "screenshot", "path": "/tmp/red-box.png"},
            {"atom_id": "nav-owner", "kind": "code", "file": "src/components/TxnDetailDrawer.tsx"},
        ],
    })
    assert result["allowed"] is False
    assert "non_runtime_proof_used:nav-owner:screenshot" in result["blockers"]
    assert "non_runtime_proof_used:nav-owner:code" in result["blockers"]
    assert "acceptance_atom_missing_runtime_proof:nav-owner" in result["blockers"]


def test_acceptance_atom_blocks_nav_href_equal_current_url_even_if_clicked():
    mod = load_module()
    result = mod.evaluate_acceptance_atom_gate({
        "acceptance_atoms": [
            {"id": "nav-owner", "type": "link", "target_surface": "用户详情钱包流水用户姓名跳转"},
        ],
        "runtime_proofs": [
            {"atom_id": "nav-owner", "kind": "interaction", "action": "click", "visible": True, "hit_tested": True, "href": "https://admin/users/UA1", "current_url": "https://admin/users/UA1"},
            {"atom_id": "nav-owner", "kind": "navigation", "url_before": "https://admin/users/UA1", "url_after": "https://admin/users/UA1", "target_content_refreshed": False},
        ],
    })
    assert result["allowed"] is False
    assert "nav_atom_href_equals_current_url:nav-owner" in result["blockers"]
    assert "nav_atom_missing_route_delta:nav-owner" in result["blockers"]
    assert "nav_atom_missing_target_content_refresh:nav-owner" in result["blockers"]


def test_cli_blocks_local_phase_before_any_writeback():
    proc = subprocess.run(
        [
            sys.executable,
            str(MODULE_PATH),
            "--phase",
            "implementation",
            "--local-verification",
            "npm run build PASS",
            "--commit",
            "abc1234",
            "--json",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.returncode == 2
    payload = json.loads(proc.stdout)
    assert payload["lark_completed_at_allowed"] is False
    assert "online_ui_retest_required" in payload["blockers"]


def test_cli_blocks_missing_acceptance_atoms_for_final_closeout():
    proc = subprocess.run(
        [
            sys.executable,
            str(MODULE_PATH),
            "--phase",
            "online-ui-retest",
            "--user-dispatch-evidence",
            "user dispatched online retest",
            "--remote-build-status",
            "deployed",
            "--online-url",
            "https://admin/users/UA1/wallet",
            "--online-ui-evidence",
            "/tmp/uvisa-admin-user-wallet-1512x982.png",
            "--ui-regression-status",
            "pass",
            "--lark-final-evidence",
            "prepared",
            "--task-target-surface",
            "用户详情>钱包流水",
            "--code-target-surface",
            "用户详情钱包流水",
            "--evidence-target-surface",
            "用户详情钱包流水",
            "--json",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.returncode == 2
    payload = json.loads(proc.stdout)
    assert payload["lark_completed_at_allowed"] is False
    assert "missing_acceptance_atoms" in payload["blockers"]
