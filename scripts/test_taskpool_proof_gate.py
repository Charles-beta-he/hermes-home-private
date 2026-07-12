import taskpool_proof_gate as gate


def write_task(path, *, status="review", allowed='["src/**"]', forbidden='["secrets/**"]', loc_budget="2", evidence=None):
    evidence = evidence or []
    evidence_rows = "\n".join(f"  - artifact: {item}" for item in evidence)
    path.write_text(
        f"""---
status: {status}
allowed_globs: {allowed}
forbidden_globs: {forbidden}
loc_budget: {loc_budget}
evidence:
{evidence_rows}
---
# Task
""",
        encoding="utf-8",
    )


def test_verify_proof_accepts_existing_artifact(tmp_path):
    artifact = tmp_path / "proof.json"
    artifact.write_text("{}", encoding="utf-8")
    task = tmp_path / "task.md"
    write_task(task, evidence=[artifact])

    result = gate.verify_proof(str(task))

    assert result["status"] == "PASS", result
    assert result["evidence_valid"][0]["path"] == str(artifact)


def test_boundary_parses_yaml_style_glob_lists(tmp_path):
    task = tmp_path / "task.md"
    write_task(task)

    ok = gate.verify_proof_boundary(str(task), {"files_changed": ["src/app.py"]})
    denied = gate.verify_proof_boundary(str(task), {"files_changed": ["secrets/key.txt"]})

    assert ok["status"] == "PASS", ok
    assert denied["status"] == "FAIL", denied
    assert any(v.startswith("forbidden_match:") for v in denied["violations"])


def test_boundary_invalid_files_changed_type_fails_closed(tmp_path):
    task = tmp_path / "task.md"
    write_task(task)

    result = gate.verify_proof_boundary(str(task), {"files_changed": "src/app.py"})

    assert result["status"] == "FAIL", result
    assert "invalid_files_changed_type" in result["violations"]


def test_boundary_invalid_proof_json_type_fails_closed(tmp_path):
    task = tmp_path / "task.md"
    write_task(task)

    result = gate.verify_proof_boundary(str(task), ["not", "an", "object"])

    assert result["status"] == "FAIL", result
    assert result["violations"] == ["invalid_proof_json_type"]


def test_boundary_invalid_files_changed_entry_fails_closed(tmp_path):
    task = tmp_path / "task.md"
    write_task(task)

    result = gate.verify_proof_boundary(str(task), {"files_changed": ["src/app.py", {"path": "secrets/key.txt"}, ""]})

    assert result["status"] == "FAIL", result
    assert "invalid_files_changed_entry" in result["violations"]


def test_boundary_malformed_forbidden_glob_list_fails_closed(tmp_path):
    task = tmp_path / "task.md"
    write_task(task, forbidden='["secrets/**"')

    result = gate.verify_proof_boundary(str(task), {"files_changed": ["secrets/key.txt"]})

    assert result["status"] == "FAIL", result
    assert "invalid_forbidden_globs:malformed_inline_glob_list" in result["violations"]


def test_boundary_malformed_allowed_glob_list_fails_closed_without_changed_files(tmp_path):
    task = tmp_path / "task.md"
    write_task(task, allowed="[invalid", forbidden="", loc_budget="")

    result = gate.verify_proof_boundary(str(task), {"files_changed": []})

    assert result["status"] == "FAIL", result
    assert "invalid_allowed_globs:malformed_inline_glob_list" in result["violations"]


def test_boundary_legacy_comma_globs_remain_supported(tmp_path):
    task = tmp_path / "task.md"
    write_task(task, allowed="src/**,tests/**", forbidden="secrets/**")

    result = gate.verify_proof_boundary(str(task), {"files_changed": ["src/app.py", "tests/test_app.py"]})

    assert result["status"] == "PASS", result


def test_boundary_negative_loc_budget_fails_closed(tmp_path):
    task = tmp_path / "task.md"
    write_task(task, allowed="", forbidden="", loc_budget="-1")

    result = gate.verify_proof_boundary(str(task), {"files_changed": []})

    assert result["status"] == "FAIL", result
    assert "invalid_loc_budget:-1" in result["violations"]


def test_boundary_zero_loc_budget_enforces_zero_changed_files(tmp_path):
    task = tmp_path / "task.md"
    write_task(task, allowed="", forbidden="", loc_budget="0")

    ok = gate.verify_proof_boundary(str(task), {"files_changed": []})
    denied = gate.verify_proof_boundary(str(task), {"files_changed": ["src/app.py"]})

    assert ok["status"] == "PASS", ok
    assert denied["status"] == "FAIL", denied
    assert "loc_budget_exceeded:1>0" in denied["violations"]


def test_boundary_invalid_loc_budget_fails_closed(tmp_path):
    task = tmp_path / "task.md"
    write_task(task, allowed="", forbidden="", loc_budget="many")

    result = gate.verify_proof_boundary(str(task), {"files_changed": []})

    assert result["status"] == "FAIL", result
    assert "invalid_loc_budget:many" in result["violations"]
