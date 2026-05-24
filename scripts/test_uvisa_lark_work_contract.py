import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import uvisa_lark_work_contract as c


def test_data_correctness_generates_source_to_sink_atom():
    contract = c.generate_acceptance_atoms(
        "t1",
        "业绩统计 tab 总数要与 Dena 列表 total 一致",
        "管理端页面统计/KPI count 必须等于列表筛选后的 total",
        "08235149",
    )
    assert contract.task_type == "data_correctness"
    atom_ids = {a["id"] for a in contract.acceptance_atoms}
    assert "A-source-to-sink-equality" in atom_ids
    equality = next(a for a in contract.acceptance_atoms if a["id"] == "A-source-to-sink-equality")
    assert equality["proof_type"] == "source_to_sink_equality"
    assert "network" in equality["required_runtime_kinds"]
    assert contract.viewport == {"width": 1512, "height": 982, "label": "14-inch-admin"}


def test_closeout_bundle_fails_closed_without_tg_or_atom_mapping(tmp_path):
    contract = c.generate_acceptance_atoms("t2", "管理端列表页面展示对齐", "", "guid2")
    bundle = {
        "pr_url": "https://github.example/pr/1",
        "merge_commit": "abc123",
        "online_regression_dir": str(tmp_path),
        "online_ui_evidence": [str(tmp_path / "shot.png")],
        "lark_close_response": {"code": 0},
        "viewport": {"width": 1512, "height": 982},
        "evidence_dir": str(tmp_path),
        "runtime_proofs": [],
    }
    result = c.evaluate_closeout_bundle(json.loads(json.dumps(contract, default=lambda o: o.__dict__)), bundle)
    assert result["allowed"] is False
    assert any(b.startswith("unmapped_acceptance_atoms:") for b in result["blockers"])
    assert "missing_tg_notification" in result["blockers"]


def test_closeout_bundle_passes_when_all_required_handles_present(tmp_path):
    contract = c.generate_acceptance_atoms("t3", "管理端列表页面展示对齐", "", "guid3")
    proofs = [{"atom_id": a["id"], "kind": "dom", "status": "pass"} for a in contract.acceptance_atoms]
    bundle = {
        "pr_url": "https://github.example/pr/1",
        "merge_commit": "abc123",
        "online_regression_dir": str(tmp_path),
        "online_ui_evidence": [str(tmp_path / "shot.png")],
        "lark_close_response": {"code": 0},
        "tg_notification": {"target": "telegram:he cheng", "evidence_dir": str(tmp_path)},
        "viewport": {"width": 1512, "height": 982},
        "evidence_dir": str(tmp_path),
        "runtime_proofs": proofs,
    }
    result = c.evaluate_closeout_bundle(json.loads(json.dumps(contract, default=lambda o: o.__dict__)), bundle)
    assert result["allowed"] is True
    assert result["state"] == "done"


def test_cli_generate_writes_contract(tmp_path):
    out = tmp_path / "contract.json"
    rc = c.main(["generate", "--task-id", "t4", "--lark-task-guid", "g4", "--title", "接口字段返回修复", "--out", str(out)])
    assert rc == 0
    data = json.loads(out.read_text())
    assert data["schema"] == "uvisa_lark_work_contract_v1"
    assert data["task_type"] == "api_contract"


def test_ingest_task_rows_generates_manifest_and_contract_files(tmp_path):
    rows = [
        {
            "id": "t-lark-1",
            "title": "业绩统计 tab 总数要与 Dena 列表 total 一致",
            "body": "UVISA-2.0新版开发 管理端 KPI count 与列表 total 对齐",
            "project": "uvisa-admin",
            "lark_task_guid": "guid-1",
            "lark_task_url": "https://example.larksuite.com/task/guid-1",
        },
        {"id": "non-lark", "title": "普通 Hermes evolution", "project": "hermes"},
    ]
    result = c.ingest_task_rows(rows, tmp_path)
    assert result["created_count"] == 1
    assert result["skipped_count"] == 1
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["created_count"] == 1
    contract_path = Path(result["created"][0]["contract_path"])
    contract = json.loads(contract_path.read_text())
    assert contract["task_id"] == "t-lark-1"
    assert contract["lark_task_guid"] == "guid-1"
    assert contract["task_type"] == "data_correctness"
    assert any(a["id"] == "A-source-to-sink-equality" for a in contract["acceptance_atoms"])


def test_ingest_task_rows_extracts_lark_guid_from_title(tmp_path):
    rows = [{"id": "task-from-title", "title": "Task - [Lark 8fe2c6cd] Admin 管理端币种打通｜work自动闭环", "project": "uvisa-admin"}]
    result = c.ingest_task_rows(rows, tmp_path)
    assert result["created_count"] == 1
    assert result["created"][0]["lark_task_guid"] == "8fe2c6cd"
    contract = json.loads(Path(result["created"][0]["contract_path"]).read_text())
    assert contract["lark_task_guid"] == "8fe2c6cd"


def test_cli_ingest_tasks_json_writes_contract_manifest(tmp_path):
    rows_path = tmp_path / "rows.json"
    rows_path.write_text(json.dumps({"rows": [{"id": "t2", "title": "管理端筛选下拉对齐", "project": "uvisa-admin", "lark_task_guid": "g2"}]}, ensure_ascii=False))
    out_dir = tmp_path / "contracts"
    rc = c.main(["ingest-tasks", "--tasks-json", "@" + str(rows_path), "--out-dir", str(out_dir)])
    assert rc == 0
    manifest = json.loads((out_dir / "manifest.json").read_text())
    assert manifest["created_count"] == 1
    assert Path(manifest["created"][0]["contract_path"]).exists()
