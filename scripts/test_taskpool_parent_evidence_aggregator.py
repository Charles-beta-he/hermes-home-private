import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import taskpool_parent_evidence_aggregator as agg


def write_task(root: Path, task_id: str, fm: dict, body: str = "") -> Path:
    path = root / f"{task_id}.md"
    lines = ["---"]
    for key, value in fm.items():
        if isinstance(value, list):
            rendered = "[" + ", ".join(json.dumps(str(x), ensure_ascii=False) for x in value) + "]"
        else:
            rendered = str(value)
        lines.append(f"{key}: {rendered}")
    lines.extend(["---", body or f"# {task_id}\n"])
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def test_certification_blocked_parent_ignores_superseded_child_status_evidence(tmp_path):
    parent_id = "parent"
    write_task(
        tmp_path,
        parent_id,
        {
            "status": "blocked",
            "priority": "P1",
            "lane": "work",
            "project": "p",
            "multimodel_last_gate_status": "FAIL",
            "blocked_resolve_reasons": ["explicit_requires_multimodel", "loop_non_convergence"],
            "auto_subtask_children": ["child-framing", "child-quota"],
            "evidence": [
                "proof:child-task:child-framing:status:pending",
                "proof:child-task:child-framing:status:done",
                "proof:child-task:child-quota:status:pending",
            ],
        },
        "# Parent\n\n## Objective\nKeep canonical objective.\n",
    )
    write_task(tmp_path, "child-framing", {"status": "done", "auto_subtask_parent": parent_id, "auto_subtask_axis": "framing", "evidence": ["artifact:/tmp/framing.md"]})
    write_task(tmp_path, "child-quota", {"status": "done", "auto_subtask_parent": parent_id, "auto_subtask_axis": "quota_observability", "evidence": ["artifact:/tmp/quota.md"]})

    report = agg.build_parent_report(parent_id, tmp_path)

    assert report["ready_for_parent"] is True
    assert report["action"] == "keep_blocked_certification_required"
    assert report["axis_summary"] == {"framing": "done", "quota_observability": "done"}
    assert report["stale_evidence"] == [
        {"child_id": "child-quota", "evidence_status": "pending", "current_status": "done"},
    ]
    assert "explicit_requires_multimodel" in report["remaining_gate_reasons"]


def test_open_or_missing_children_keep_parent_blocked_with_structured_reason(tmp_path):
    parent_id = "parent"
    write_task(tmp_path, parent_id, {"status": "blocked", "auto_subtask_children": ["done-child", "missing-child"]})
    write_task(tmp_path, "done-child", {"status": "done", "auto_subtask_parent": parent_id, "auto_subtask_axis": "framing"})

    report = agg.build_parent_report(parent_id, tmp_path)

    assert report["ready_for_parent"] is False
    assert report["action"] == "keep_blocked_children_open"
    assert report["missing_children"] == ["missing-child"]
    assert report["open_children"] == []


def test_children_can_be_discovered_from_backlinks_when_parent_child_list_is_empty(tmp_path):
    parent_id = "parent"
    write_task(tmp_path, parent_id, {"status": "blocked", "evidence": []})
    write_task(tmp_path, "b-child", {"status": "done", "auto_subtask_parent": parent_id, "auto_subtask_axis": "patch_normalization"})
    write_task(tmp_path, "a-child", {"status": "done", "auto_subtask_parent": parent_id, "auto_subtask_axis": "framing"})

    report = agg.build_parent_report(parent_id, tmp_path)

    assert [child["id"] for child in report["children"]] == ["a-child", "b-child"]
    assert report["action"] == "reopen_for_parent_ratification"
    assert report["ready_for_parent"] is True


def test_bibliography_contains_core_arguments_and_classics():
    items = agg.core_bibliography()
    titles = {item["title"] for item in items}
    arguments = {item["argument"] for item in items}

    assert "The Mythical Man-Month" in titles
    assert "The Goal" in titles
    assert "Managing the Design Factory" in titles
    assert "Design Structure Matrix Methods and Applications" in titles
    assert "limit WIP and expose blocked flow" in arguments


def test_cli_emits_json_report(tmp_path):
    write_task(tmp_path, "parent", {"status": "blocked"})
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_DIR / "taskpool_parent_evidence_aggregator.py"), "--task", "parent", "--tasks-dir", str(tmp_path), "--json"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    report = json.loads(proc.stdout)
    assert report["task_id"] == "parent"
    assert report["action"] == "no_children_found"


def test_main_emits_json_report_for_no_children(tmp_path, capsys):
    write_task(tmp_path, "parent", {"status": "blocked"})
    exit_code = agg.main(["--task", "parent", "--tasks-dir", str(tmp_path), "--json"])
    report = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert report["action"] == "no_children_found"


def test_parser_helpers_scalar_plain_text_and_non_matching_evidence(tmp_path):
    plain = tmp_path / "plain.md"
    plain.write_text("# Plain task without frontmatter\n", encoding="utf-8")
    malformed = tmp_path / "malformed.md"
    malformed.write_text(
        "---\nstatus: blocked\nlist_ok: [a, b]\nlist_bad: [broken: []\n  ignored: nested\n- ignored-seq\nnotes: unquoted: colon\n---\n# malformed\n",
        encoding="utf-8",
    )
    write_task(tmp_path, "parent", {"status": "pending", "auto_subtask_children": "child", "evidence": ["artifact:not-child-status"]})
    write_task(tmp_path, "child", {"status": "done", "auto_subtask_parent": "parent"})

    tasks = agg.load_tasks(tmp_path)
    report = agg.build_parent_report("parent", tmp_path)

    assert tasks["plain"]["fm"] == {}
    assert agg._fallback_frontmatter_parse("\n  ignored: nested\n- ignored-seq\nno colon\n") == {}
    assert tasks["malformed"]["fm"]["status"] == "blocked"
    assert tasks["malformed"]["fm"]["notes"] == "unquoted: colon"
    assert tasks["malformed"]["fm"]["list_ok"] == ["a", "b"]
    assert tasks["malformed"]["fm"]["list_bad"] == "[broken: []"
    assert report["child_count"] == 1
    assert report["action"] == "aggregate_only"
    assert report["stale_evidence"] == []


def test_missing_parent_raises_task_not_found(tmp_path):
    with pytest.raises(agg.TaskNotFound):
        agg.build_parent_report("absent", tmp_path)
