#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

INGEST = Path("/Users/charles/.hermes/scripts/daily_report_task_ingest.py")
ORCH = Path("/Users/charles/.hermes/scripts/brain_task_orchestrator.py")
PH_DIGEST = Path("/Users/charles/.hermes/scripts/producthunt_daily_digest.py")


def load_ph_digest_module():
    spec = importlib.util.spec_from_file_location("producthunt_daily_digest_test", PH_DIGEST)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def make_vault(root: Path) -> Path:
    vault = root / "brain"
    (vault / "05-实践与项目" / "tasks").mkdir(parents=True, exist_ok=True)
    (vault / "07-仪表盘").mkdir(parents=True, exist_ok=True)
    return vault


def run_ingest(proposal_path: Path, vault: Path, state_path: Path, write: bool) -> dict:
    env = os.environ.copy()
    env["HERMES_BRAIN_VAULT"] = str(vault)
    env["HERMES_DAILY_REPORT_INGEST_STATE"] = str(state_path)
    env["HERMES_DAILY_REPORT_ORCH"] = str(ORCH)
    env["HERMES_DAILY_REPORT_MANUAL_REQUESTS"] = str(state_path.with_name("manual_requests.jsonl"))
    env["HERMES_TASKPOOL_EVENT_HOOK_DISABLED"] = "1"
    cmd = [sys.executable, str(INGEST), "--proposal-json", str(proposal_path), "--json"]
    if write:
        cmd.append("--write")
    result = subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
    return json.loads(result.stdout)


def build_payload(report_path: Path) -> dict:
    return {
        "schema": "daily_report_task_candidates_v1",
        "generated_at": "2026-05-19T12:00:00",
        "report_kind": "pa-daily-report",
        "report_id": "pa-daily:2026-05-19",
        "report_path": str(report_path),
        "summary": {"sessions": 8, "v_pa": 0.42, "vdot_pa": -0.08, "task_types": {"code-review": 5}},
        "candidates": [
            {
                "dedupe_key": "pa-health-regression",
                "title": "复盘 PA 健康度退化并收敛修复方案",
                "priority": "P1",
                "project": "hermes-agent",
                "concepts": ["task", "daily-report", "pa-report"],
                "priority_layer": "daily-report:p1:health-regression",
                "dependency_order": ["1"],
                "multimodel_triage_result": "P1-daily-health-regression",
                "architecture_target": "taskpool",
                "objective": "基于日报复盘 PA 健康度退化并确定修复顺序。",
                "capability_delta": "把日报退化信号转成带证据的治理任务。",
                "anti_drift_check": "禁止只记录告警；必须给出根因假设与回退策略。",
                "acceptance_evidence": "日报证据、健康对比、修复切片与回退方案。",
                "parallel_boundary": "先核对健康历史，再定位根因，最后落地修复。",
                "evidence_bundle": str(report_path),
                "truth_gate": "report-evidence-present",
                "lane": "auto",
                "expires_days": 14,
                "requires_multimodel": False,
                "expected_participants": [],
                "multimodel_reason": "",
            }
        ],
    }


def test_ingest_creates_task_and_is_idempotent_per_report():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        vault = make_vault(root)
        report_path = root / "pa-daily-2026-05-19.md"
        report_path.write_text("demo report", encoding="utf-8")
        proposal_path = root / "pa-daily-2026-05-19.tasks.json"
        proposal_path.write_text(json.dumps(build_payload(report_path), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        state_path = root / "daily_report_ingest_state.json"

        first = run_ingest(proposal_path, vault, state_path, write=True)
        assert first["created_count"] == 1, first
        created_path = Path(first["actions"][0]["task_path"])
        assert created_path.exists(), first
        created_text = created_path.read_text(encoding="utf-8")
        assert "priority_layer: daily-report:p1:health-regression" in created_text
        assert "dependency_order: [\"1\"]" in created_text
        assert "requires_multimodel: true" in created_text
        assert "expected_participants:" in created_text and "claude-code" in created_text

        second = run_ingest(proposal_path, vault, state_path, write=True)
        assert second["created_count"] == 0, second
        assert second["actions"][0]["reason"] == "already_emitted_for_report", second


def test_ingest_fail_closed_on_missing_governance_fields():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        vault = make_vault(root)
        report_path = root / "pa-daily-2026-05-19.md"
        report_path.write_text("demo report", encoding="utf-8")
        proposal = build_payload(report_path)
        del proposal["candidates"][0]["priority_layer"]
        proposal_path = root / "invalid.tasks.json"
        proposal_path.write_text(json.dumps(proposal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        state_path = root / "daily_report_ingest_state.json"

        result = run_ingest(proposal_path, vault, state_path, write=False)
        assert result["invalid_count"] == 1, result
        assert "missing required governance fields" in result["actions"][0]["reason"], result


def test_ingest_accepts_external_aihot_sidecar_when_contract_is_present():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        vault = make_vault(root)
        report_path = root / "aihot-daily-2026-05-19.md"
        report_path.write_text("# AIHOT Daily\n\n- signal\n", encoding="utf-8")
        proposal = {
            "schema": "daily_report_task_candidates_v1",
            "generated_at": "2026-05-19T09:10:00",
            "report_kind": "aihot-daily-report",
            "report_id": "aihot-daily:2026-05-19",
            "report_path": str(report_path),
            "summary": {"aihot_issue_date": "2026-05-19", "trending_count": 3},
            "candidates": [
                {
                    "report_id": "aihot-daily:2026-05-19",
                    "dedupe_key": "aihot:browser-evidence-to-taskpool",
                    "title": "将 AIHOT/Trending 日报高价值信号转成受治理 taskpool 任务",
                    "priority": "P1",
                    "project": "hermes-agent",
                    "concepts": ["task", "daily-report", "aihot-report"],
                    "priority_layer": "daily-report:p1:external-signal-ingest",
                    "dependency_order": ["ingestion-contract", "prioritization-and-dedup", "verification-and-fallback"],
                    "multimodel_triage_result": "P1-external-signal-ingest",
                    "architecture_target": "taskpool",
                    "objective": "基于 AIHOT 与 GitHub Trending 当日报告，验证高价值 Hermes 相关发现是否应该进入受治理 taskpool 主链。",
                    "capability_delta": "把外部日报中的高价值发现转成带优先级、依赖、证据与去重保护的任务，而不是停留在消息摘要。",
                    "anti_drift_check": "禁止把普通资讯批量塞进任务池；只有与 Hermes 控制面、taskpool、记忆、提示词、provider quota 等直接相关的高价值发现才允许入池。",
                    "acceptance_evidence": "AIHOT/Trending 报告、候选任务治理字段、验证步骤与回退策略。",
                    "parallel_boundary": "先固化日报→任务治理契约，再判断优先级与重复，最后执行正式入池与验证。",
                    "evidence_bundle": str(report_path),
                    "truth_gate": "report-evidence-present",
                    "lane": "auto",
                    "expires_days": 14,
                    "requires_multimodel": False,
                    "expected_participants": [],
                    "multimodel_reason": "",
                }
            ],
        }
        proposal_path = root / "aihot-daily-2026-05-19.tasks.json"
        proposal_path.write_text(json.dumps(proposal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        state_path = root / "daily_report_ingest_state.json"

        result = run_ingest(proposal_path, vault, state_path, write=True)
        assert result["created_count"] == 1, result
        created_path = Path(result["actions"][0]["task_path"])
        created_text = created_path.read_text(encoding="utf-8")
        assert "priority_layer: daily-report:p1:external-signal-ingest" in created_text
        assert str(report_path) in created_text
        assert "requires_multimodel: true" in created_text
        assert "expected_participants:" in created_text and "claude-code" in created_text


def test_ingest_suppresses_product_task_sidecar_self_asserted_multimodel_contract():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        vault = make_vault(root)
        report_path = root / "work-daily.md"
        report_path.write_text("# work report", encoding="utf-8")
        proposal = build_payload(report_path)
        candidate = proposal["candidates"][0]
        candidate.update({
            "dedupe_key": "uvisa-product-ui-fix",
            "title": "修复 UVISA 产品页面交互问题",
            "priority": "P1",
            "project": "uvisa-app-2.0",
            "architecture_target": "",
            "priority_layer": "work:p1:product-fix",
            "concepts": ["task", "uvisa", "frontend"],
            "requires_multimodel": True,
            "expected_participants": ["gpt-5.5", "deepseek-v4-pro"],
            "multimodel_reason": "sidecar asserted but product work should not spend multimodel by default",
        })
        proposal_path = root / "work.tasks.json"
        proposal_path.write_text(json.dumps(proposal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        state_path = root / "daily_report_ingest_state.json"

        result = run_ingest(proposal_path, vault, state_path, write=True)
        assert result["created_count"] == 1, result
        created_text = Path(result["actions"][0]["task_path"]).read_text(encoding="utf-8")
        assert "requires_multimodel: true" not in created_text
        assert "gpt-5.5" not in created_text
        assert "deepseek-v4-pro" not in created_text
        assert "sidecar asserted" not in created_text


def test_ingest_blocks_eligible_multimodel_candidate_with_missing_local_evidence_bundle():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        vault = make_vault(root)
        missing_report = root / "missing-report.md"
        proposal = build_payload(missing_report)
        proposal["candidates"][0]["evidence_bundle"] = str(missing_report)
        proposal_path = root / "missing-evidence.tasks.json"
        proposal_path.write_text(json.dumps(proposal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        state_path = root / "daily_report_ingest_state.json"

        result = run_ingest(proposal_path, vault, state_path, write=True)
        assert result["created_count"] == 0, result
        assert result["actions"][0]["status"] == "blocked_evidence_request", result
        request_path = state_path.with_name("manual_requests.jsonl")
        assert request_path.exists(), result
        request = json.loads(request_path.read_text(encoding="utf-8").splitlines()[0])
        assert request["manual_dispatch_gate"] == "tg:evidence_request"
        assert request["dedupe_key"] == "pa-health-regression"


def test_ingest_accepts_list_and_object_fields_from_browser_sidecar():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        vault = make_vault(root)
        report_path = root / "aihot-daily-2026-05-27.md"
        report_path.write_text("# AIHOT Daily\n", encoding="utf-8")
        proposal = build_payload(report_path)
        candidate = proposal["candidates"][0]
        candidate.update({
            "dedupe_key": "aihot-object-fields",
            "title": "Validate browser daily sidecar structured fields",
            "acceptance_evidence": ["report exists", "sidecar has schema", "ingest succeeds"],
            "evidence_bundle": {"report_path": str(report_path), "source_urls": ["https://aihot.virxact.com/daily"]},
        })
        proposal_path = root / "aihot-object-fields.tasks.json"
        proposal_path.write_text(json.dumps(proposal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        state_path = root / "daily_report_ingest_state.json"

        result = run_ingest(proposal_path, vault, state_path, write=True)
        assert result["created_count"] == 1, result
        created_text = Path(result["actions"][0]["task_path"]).read_text(encoding="utf-8")
        assert "report exists" in created_text
        assert "https://aihot.virxact.com/daily" in created_text


def test_ingest_dedupes_same_repo_signal_across_reports():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        vault = make_vault(root)
        report_a = root / "report-a.md"
        report_b = root / "report-b.md"
        report_a.write_text("A", encoding="utf-8")
        report_b.write_text("B", encoding="utf-8")
        proposal_a = build_payload(report_a)
        proposal_b = build_payload(report_b)
        proposal_b["report_id"] = "pa-daily:2026-05-20"
        proposal_b["candidates"][0]["evidence_bundle"] = str(report_b)
        path_a = root / "a.tasks.json"
        path_b = root / "b.tasks.json"
        path_a.write_text(json.dumps(proposal_a, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        path_b.write_text(json.dumps(proposal_b, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        state_path = root / "daily_report_ingest_state.json"

        first = run_ingest(path_a, vault, state_path, write=True)
        second = run_ingest(path_b, vault, state_path, write=True)
        assert first["created_count"] == 1, first
        assert second["created_count"] == 0, second
        assert second["actions"][0]["reason"] == "repo_already_analyzed", second


def test_ingest_carries_product_workflow_execution_flow_fields():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        vault = make_vault(root)
        report_path = root / "product-workflow.md"
        report_path.write_text("# product workflow evidence", encoding="utf-8")
        proposal = build_payload(report_path)
        candidate = proposal["candidates"][0]
        candidate.update({
            "dedupe_key": "product-workflow-execution-flow-fields",
            "title": "发布 Product Workflow GTM writeback gate",
            "priority": "P2",
            "priority_layer": "product-workflow:p2:launch-writeback",
            "concepts": ["product-workflow", "execution-flow"],
            "workflow_stage": "writeback",
            "completion_boundary": "launched_observing",
            "harness_surfaces": ["command", "metrics"],
            "required_artifacts": ["command_output", "metric_readback"],
            "external_side_effects": True,
            "lane": "auto",
            "requires_multimodel": False,
            "expected_participants": [],
            "multimodel_reason": "",
        })
        proposal_path = root / "product-workflow.tasks.json"
        proposal_path.write_text(json.dumps(proposal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        state_path = root / "daily_report_ingest_state.json"

        result = run_ingest(proposal_path, vault, state_path, write=True)
        assert result["created_count"] == 1, result
        created_text = Path(result["actions"][0]["task_path"]).read_text(encoding="utf-8")
        assert "workflow_stage: writeback" in created_text
        assert "completion_boundary: launched_observing" in created_text
        assert "harness_surfaces:" in created_text and "command" in created_text and "metrics" in created_text
        assert "required_artifacts:" in created_text and "metric_readback" in created_text
        assert "external_side_effects: true" in created_text


def test_producthunt_supplemental_landing_repo_scan_upgrades_blocked_redirect():
    ph = load_ph_digest_module()
    original_audit = ph._candidate_link_audit
    original_enrich = ph.enrich_repo
    try:
        def fake_audit(link_type: str, url: str, *, resolve_redirects: bool):
            audit = ph.ExternalLinkAudit(source_url=url, link_type=link_type)
            if "producthunt.com/r/blocked" in url:
                audit.resolved_url = url
                audit.http_status = 403
                audit.state = "ph_redirect_cloudflare_blocked"
                audit.ingest_decision = "needs_supplemental_repo_link"
                audit.detail = "http_403:cloudflare"
            elif url == "https://example.test/landing":
                audit.resolved_url = url
                audit.github_urls = ["https://github.com/acme/clinepass"]
            return audit

        setattr(ph, "_candidate_link_audit", fake_audit)
        setattr(ph, "enrich_repo", lambda repo, url: ph.RepoMeta(repo=repo, url=url, stars=7, license="MIT"))
        item = ph.ProductItem(
            name="ClinePass",
            url="https://www.producthunt.com/products/clinepass",
            links=[
                {"type": "Github", "url": "https://www.producthunt.com/r/blocked"},
                {"type": "Website", "url": "https://example.test/landing"},
            ],
        )
        ph.detect_and_enrich([item], resolve_redirects=True)
        assert item.open_source_status == "github_repo_verified"
        assert item.taskpool_ingest_judgement == "poolable_only_after_hermes_mapping"
        assert [repo.repo for repo in item.repos] == ["acme/clinepass"]
        assert any(a.link_type == "supplemental:Website" and a.state == "github_repo_verified" for a in item.external_link_audit)
    finally:
        setattr(ph, "_candidate_link_audit", original_audit)
        setattr(ph, "enrich_repo", original_enrich)


def test_producthunt_supplemental_landing_scan_stays_fail_closed_without_repo():
    ph = load_ph_digest_module()
    original_audit = ph._candidate_link_audit
    try:
        def fake_audit(link_type: str, url: str, *, resolve_redirects: bool):
            audit = ph.ExternalLinkAudit(source_url=url, link_type=link_type)
            if "producthunt.com/r/blocked" in url:
                audit.resolved_url = url
                audit.http_status = 403
                audit.state = "ph_redirect_cloudflare_blocked"
                audit.ingest_decision = "needs_supplemental_repo_link"
                audit.detail = "http_403:cloudflare"
            elif url == "https://example.test/landing":
                audit.resolved_url = url
                audit.state = "github_link_detected_redirect_to_landing"
                audit.ingest_decision = "needs_supplemental_repo_link"
                audit.detail = "landing_page_no_repo"
            return audit

        setattr(ph, "_candidate_link_audit", fake_audit)
        item = ph.ProductItem(
            name="PMB",
            url="https://www.producthunt.com/products/pmb",
            links=[
                {"type": "Github", "url": "https://www.producthunt.com/r/blocked"},
                {"type": "Website", "url": "https://example.test/landing"},
            ],
        )
        ph.detect_and_enrich([item], resolve_redirects=True)
        assert item.open_source_status == "ph_redirect_cloudflare_blocked"
        assert item.taskpool_ingest_judgement == "not_poolable_needs_repo_link"
        assert item.repos == []
        assert any(a.state == "supplemental_landing_no_repo" for a in item.external_link_audit)
    finally:
        setattr(ph, "_candidate_link_audit", original_audit)


def main() -> int:
    test_ingest_creates_task_and_is_idempotent_per_report()
    test_ingest_fail_closed_on_missing_governance_fields()
    test_ingest_accepts_external_aihot_sidecar_when_contract_is_present()
    test_ingest_suppresses_product_task_sidecar_self_asserted_multimodel_contract()
    test_ingest_blocks_eligible_multimodel_candidate_with_missing_local_evidence_bundle()
    test_ingest_accepts_list_and_object_fields_from_browser_sidecar()
    test_ingest_dedupes_same_repo_signal_across_reports()
    test_ingest_carries_product_workflow_execution_flow_fields()
    test_producthunt_supplemental_landing_repo_scan_upgrades_blocked_redirect()
    test_producthunt_supplemental_landing_scan_stays_fail_closed_without_repo()
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
