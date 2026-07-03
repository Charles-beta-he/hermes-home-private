#!/usr/bin/env python3
"""Tests for brain_task_orchestrator.py.
Run with: python3 ~/.hermes/scripts/test_brain_task_orchestrator.py
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

SCRIPT = Path.home() / ".hermes" / "scripts" / "brain_task_orchestrator.py"
RAILWAY_GATE_SCRIPT = Path.home() / ".hermes" / "scripts" / "railway_deploy_gate.py"


def load_railway_gate_module():
    spec = importlib.util.spec_from_file_location("railway_deploy_gate_under_test", RAILWAY_GATE_SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def load_orchestrator_module():
    old_quorum = os.environ.get("HERMES_QUORUM_CONFIG")
    if old_quorum is None:
        os.environ["HERMES_QUORUM_CONFIG"] = str(Path(tempfile.gettempdir()) / "hermes-test-no-quorum.yaml")
    spec = importlib.util.spec_from_file_location("brain_task_orchestrator_under_test", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    try:
        spec.loader.exec_module(mod)
    finally:
        if old_quorum is None:
            os.environ.pop("HERMES_QUORUM_CONFIG", None)
        else:
            os.environ["HERMES_QUORUM_CONFIG"] = old_quorum
    return mod


def run(env, *args, check=True):
    args = list(args)
    if args and args[0] == "add":
        defaults = [
            ("--priority-layer", "P2"),
            ("--dependency-order", "1"),
            ("--multimodel-triage-result", "P3"),
        ]
        insert_at = args.index("--json") if "--json" in args else len(args)
        injected = []
        for flag, value in defaults:
            if flag not in args:
                injected.extend([flag, value])
        if injected:
            args[insert_at:insert_at] = injected
    cmd = [sys.executable, str(SCRIPT), *args]
    proc_env = env.copy()
    # Unit tests exercise orchestrator behavior inside isolated temporary vaults.
    # Disable real taskpool event hooks for subprocess-based CLI calls so tests
    # cannot race against background multimodel/autorun side effects; direct
    # hook-specific tests monkeypatch maybe_fire_taskpool_event_hook in-process.
    proc_env.setdefault("HERMES_TASKPOOL_EVENT_HOOK_DISABLED", "1")
    r = subprocess.run(cmd, capture_output=True, text=True, env=proc_env)
    if check and r.returncode != 0:
        raise AssertionError(f"command failed {cmd}\nstdout={r.stdout}\nstderr={r.stderr}")
    return r


def _git(repo: Path, *args: str) -> str:
    r = subprocess.run(["git", *args], cwd=str(repo), capture_output=True, text=True, check=True)
    return r.stdout.strip()


def test_railway_deploy_gate_accepts_exact_prefix_and_ancestor_commits():
    mod = load_railway_gate_module()
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        repo.mkdir()
        _git(repo, "init", "-q")
        _git(repo, "config", "user.email", "hermes-test@example.local")
        _git(repo, "config", "user.name", "Hermes Test")
        (repo / "a.txt").write_text("a\n", encoding="utf-8")
        _git(repo, "add", "a.txt")
        _git(repo, "commit", "-q", "-m", "first")
        first_branch = _git(repo, "rev-parse", "--abbrev-ref", "HEAD")
        first = _git(repo, "rev-parse", "HEAD")
        (repo / "a.txt").write_text("a\nb\n", encoding="utf-8")
        _git(repo, "commit", "-q", "-am", "second")
        second = _git(repo, "rev-parse", "HEAD")
        _git(repo, "checkout", "-q", "--orphan", "other")
        (repo / "a.txt").write_text("other\n", encoding="utf-8")
        _git(repo, "add", "a.txt")
        _git(repo, "commit", "-q", "-m", "other")
        other = _git(repo, "rev-parse", "HEAD")
        _git(repo, "checkout", "-q", "-f", first_branch)

        exact = mod.deployment_contains_expected_commit(second, second, workdir=str(repo))
        assert exact["ok"] is True and exact["relation"] == "exact_or_prefix", exact
        prefix = mod.deployment_contains_expected_commit(second[:8], second, workdir=str(repo))
        assert prefix["ok"] is True and prefix["relation"] == "exact_or_prefix", prefix
        ancestor = mod.deployment_contains_expected_commit(first, second, workdir=str(repo))
        assert ancestor["ok"] is True and ancestor["relation"] == "ancestor", ancestor
        mismatch = mod.deployment_contains_expected_commit(other, second, workdir=str(repo))
        assert mismatch["ok"] is False and mismatch["relation"] == "not_ancestor", mismatch
        old_default_workdirs = mod.DEFAULT_WORKDIRS
        try:
            setattr(mod, "DEFAULT_WORKDIRS", [])
            missing = mod.deployment_contains_expected_commit(first, second, workdir=str(repo / "missing"))
            assert missing["ok"] is False and missing["relation"] == "git_workdir_unavailable", missing
        finally:
            setattr(mod, "DEFAULT_WORKDIRS", old_default_workdirs)


def test_railway_deploy_gate_evaluate_uses_ancestor_relation():
    mod = load_railway_gate_module()
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        repo.mkdir()
        _git(repo, "init", "-q")
        _git(repo, "config", "user.email", "hermes-test@example.local")
        _git(repo, "config", "user.name", "Hermes Test")
        (repo / "a.txt").write_text("a\n", encoding="utf-8")
        _git(repo, "add", "a.txt")
        _git(repo, "commit", "-q", "-m", "first")
        first = _git(repo, "rev-parse", "HEAD")
        (repo / "a.txt").write_text("a\nb\n", encoding="utf-8")
        _git(repo, "commit", "-q", "-am", "second")
        second = _git(repo, "rev-parse", "HEAD")

        old_status = mod.current_service_status
        old_latest = mod.latest_deployment
        try:
            setattr(mod, "current_service_status", lambda service, workdir="": {
                "ok": True,
                "allowed": True,
                "service": service,
                "deployment_id": "dep-current",
                "status": "SUCCESS",
                "stopped": False,
                "blockers": [],
                "workdir": str(repo),
            })
            setattr(mod, "latest_deployment", lambda service, workdir="", limit=5: {
                "ok": True,
                "service": service,
                "deployment_id": "dep-1",
                "deployment_status": "SUCCESS",
                "branch": "main",
                "commit_hash": second,
                "repo": "unknown/repo",
                "workdir": str(repo),
            })
            result = mod.evaluate_gate(project="test-project", service="test-service", expected_commit=first, workdir=str(repo))
            assert result["allowed"] is True, result
            assert result["commit_match"]["relation"] == "ancestor", result
            assert result["safe_evidence"]["expected_commit"] == first, result
            assert result["safe_evidence"]["commit_hash"] == second, result
        finally:
            setattr(mod, "current_service_status", old_status)
            setattr(mod, "latest_deployment", old_latest)


def make_env_and_vault():
    td = tempfile.TemporaryDirectory()
    vault = Path(td.name) / "brain"
    (vault / "05-实践与项目" / "tasks").mkdir(parents=True)
    (vault / "07-仪表盘").mkdir(parents=True)
    env = os.environ.copy()
    env["HERMES_BRAIN_VAULT"] = str(vault)
    env["HERMES_BRAIN_AUTORUN_STATE_DIR"] = str(Path(td.name) / "state")
    env["HERMES_AUTONOMY_WRITE_ALLOWLIST"] = str(Path(td.name) / "autonomy-write-allowlist.json")
    env["HERMES_CRON_JOBS_PATH"] = str(Path(td.name) / "cron" / "jobs.json")
    env["HERMES_PROJECT_PROFILES_DIR"] = str(Path(td.name) / "project-profiles")
    env.setdefault("HERMES_QUORUM_CONFIG", str(Path(td.name) / "missing-quorum.yaml"))
    p10_fixture = Path(td.name) / "p10-health-pass.json"
    p10_fixture.write_text(json.dumps({"grade": "A", "components": {"self_test": 1.0}}, ensure_ascii=False), encoding="utf-8")
    env["HERMES_AUTONOMY_PRECONDITION_P10_FIXTURE"] = str(p10_fixture)
    env.pop("HERMES_LOCAL_BRAIN_AUTORUN", None)
    env.pop("HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL", None)
    seed_project_profile(env)
    return td, vault, env



def seed_project_profile(env, *, aliases=None, project="hermes"):
    aliases = aliases if aliases is not None else ["hermes", "hermes-agent", "local-brain"]
    profiles_dir = Path(env["HERMES_PROJECT_PROFILES_DIR"])
    profiles_dir.mkdir(parents=True, exist_ok=True)
    (profiles_dir / "hermes.json").write_text(json.dumps({
        "project": project,
        "display_name": "Hermes fallback test profile",
        "aliases": aliases,
        "paths": {"root": "/tmp/hermes-test"},
        "test_cmd": "python3 -m unittest",
        "build_cmd": "python3 -m compileall .",
        "acceptance": ["tests pass"],
        "source_weighting_policy": {
            "applies_to": "Hermes test work-lane tasks",
            "weights": [{"source": "runtime evidence", "weight": 1.0}],
        },
        "lark_task_execution_policy": {},
        "lark_evidence_policy": {},
        "backend_contract_policy": {},
        "regression_coverage_policy": {},
    }, ensure_ascii=False, indent=2), encoding="utf-8")



def add_task(env, title="完成本地大脑任务控制台", priority="P1", project="local-brain"):
    r = run(
        env,
        "add",
        title,
        "--priority",
        priority,
        "--project",
        project,
        "--expires-at",
        "2099-01-01",
        "--json",
    )
    created = json.loads(r.stdout)
    assert created["status"] == "OK"
    created_path = Path(created["created"])
    # Work-lane tasks are intentionally fail-closed without an evidence/source
    # policy. Most unit-test fixtures use add_task() to create dispatchable work,
    # so seed a deterministic test source policy unless a specific test edits it.
    text = created_path.read_text(encoding="utf-8")
    if "lane: work" in text and "source_weighting_policy_ref:" not in text:
        text = text.replace("workflow_contract:", f"source_weighting_policy_ref: project-profile:{project}:test\nworkflow_contract:", 1)
        created_path.write_text(text, encoding="utf-8")
    return created["id"], created_path


def _autorun_proof_record(mod, *, prev_hash="", **event):
    record = {
        "schema": "local_brain_autorun_proof_v1",
        "generated_at": "2099-01-01T00:00:00+08:00",
        "prev_hash": prev_hash,
        **event,
    }
    record["event_hash"] = mod.proof_payload_hash(record)
    return record


def test_verify_autorun_proof_hash_reuses_chain_readback_for_multiple_hashes():
    mod = load_orchestrator_module()
    with tempfile.TemporaryDirectory() as td:
        proof_log = Path(td) / "auto_run_proof.jsonl"
        prev = ""
        events = []
        for i in range(20):
            record = _autorun_proof_record(mod, prev_hash=prev, event="proof", seq=i)
            prev = record["event_hash"]
            events.append(record)
        proof_log.write_text("\n".join(json.dumps(e, ensure_ascii=False, sort_keys=True) for e in events) + "\n", encoding="utf-8")

        old_log = getattr(mod, "AUTORUN_PROOF_LOG")
        original_read = getattr(mod, "read_autorun_proof_events")
        reads = {"count": 0}

        def counted_read():
            reads["count"] += 1
            return original_read()

        try:
            setattr(mod, "AUTORUN_PROOF_LOG", proof_log)
            setattr(mod, "read_autorun_proof_events", counted_read)
            for event in events[:5]:
                assert mod.verify_autorun_proof_hash(str(event["event_hash"])) is True
        finally:
            setattr(mod, "AUTORUN_PROOF_LOG", old_log)
            setattr(mod, "read_autorun_proof_events", original_read)

        assert reads["count"] <= 2


def test_execution_flow_dry_run_cli_projects_enterprise_gate_without_mutating_task():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id, task_path = add_task(env, title="Implement backend API and browser UI", priority="P1", project="hermes")
        before = task_path.read_text(encoding="utf-8")

        result = run(env, "execution-flow-dry-run", "--task", task_id, "--json")
        payload = json.loads(result.stdout)

        assert payload["status"] == "OK"
        assert payload["schema_version"] == "execution-flow/v1"
        assert payload["mode"] == "read_only"
        assert payload["enterprise_gate"]["status"] == "BLOCKED"
        assert payload["summary"]["evaluated"] == 1
        assert payload["evaluations"][0]["task_id"] == task_id
        assert "browser_or_ui_surface_proof" in payload["evaluations"][0]["missing_evidence"]
        assert task_path.read_text(encoding="utf-8") == before

        blocked = run(env, "execution-flow-dry-run", "--task", task_id, "--json", "--fail-on-blocked", check=False)
        assert blocked.returncode == 2
        blocked_payload = json.loads(blocked.stdout)
        assert blocked_payload["status"] == "FAIL"
        assert blocked_payload["enterprise_gate"]["status"] == "BLOCKED"


def test_dispatch_dry_run_consumes_execution_flow_without_stopping_safe_execution():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id, task_path = add_task(env, title="Implement backend API and browser UI", priority="P1", project="hermes")
        before = task_path.read_text(encoding="utf-8")

        dry = json.loads(run(env, "dispatch-dry-run", "--json").stdout)

        assert dry["status"] == "OK"
        assert dry["dry_run"] is True
        assert dry["dispatchable"] is True
        assert dry["next"]["id"] == task_id
        assert dry["execution_flow"]["schema_version"] == "execution-flow/v1"
        assert dry["execution_flow"]["enterprise_gate"]["status"] == "BLOCKED"
        assert dry["execution_flow_dispatch_decision"]["allowed_to_dispatch"] is True
        assert dry["execution_flow_dispatch_decision"]["reason"] == "pre_closeout_evidence_gap_safe_to_execute"
        assert "browser_or_ui_surface_proof" in dry["execution_flow"]["evaluations"][0]["missing_evidence"]
        assert "execution_flow" in dry["execution_prompt"]
        assert task_path.read_text(encoding="utf-8") == before


def test_reconcile_requeues_false_running_multimodel_claim_without_retry_penalty():
    td, _vault, env = make_env_and_vault()
    with td:
        env["HERMES_HOME"] = str(Path(td.name) / "hermes-home")
        task_id, task_path = add_task(env, title="Multimodel certification target", priority="P1", project="hermes")
        text = task_path.read_text(encoding="utf-8")
        text = text.replace("status: pending", "status: running", 1)
        text = text.replace("claimed_by: ", "claimed_by: hermes-multimodel", 1)
        text = text.replace("run_id: ", "run_id: hermes-multimodel-test", 1)
        task_path.write_text(text, encoding="utf-8")

        jobs_dir = Path(env["HERMES_HOME"]) / "state" / "taskpool-multimodel" / "jobs"
        jobs_dir.mkdir(parents=True)
        (jobs_dir / "dead-job.json").write_text(json.dumps({
            "schema": "taskpool_multimodel_async_job_v1",
            "job_id": "dead-job",
            "task_id": task_id,
            "pid": 99999999,
            "cmd": [sys.executable, str(SCRIPT), "multimodel-intervention-step", "--task", task_id, "--json"],
            "log_path": str(Path(env["HERMES_HOME"]) / "logs" / "taskpool-multimodel" / "dead-job.jsonl"),
        }, ensure_ascii=False), encoding="utf-8")

        dry = json.loads(run(env, "reconcile", "--json").stdout)
        assert any(a["action"] == "false_running_multimodel_requeued" for a in dry["actions"])
        assert "status: running" in task_path.read_text(encoding="utf-8")

        written = json.loads(run(env, "reconcile", "--write", "--json").stdout)
        assert any(a["action"] == "false_running_multimodel_requeued" for a in written["actions"])
        updated = task_path.read_text(encoding="utf-8")
        assert "status: pending" in updated
        assert "claimed_by: " in updated
        assert "claimed_by: hermes-multimodel" not in updated
        assert "retry_count: 1" not in updated


def test_dispatch_dry_run_hard_execution_flow_boundary_has_no_actionable_prompt():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id, task_path = add_task(env, title="Publish external writeback", priority="P1", project="hermes")
        text = task_path.read_text(encoding="utf-8")
        text = text.replace("status: pending", "status: pending\nworkflow_stage: human_gate", 1)
        task_path.write_text(text, encoding="utf-8")
        before = task_path.read_text(encoding="utf-8")

        dry = json.loads(run(env, "dispatch-dry-run", "--json").stdout)

        assert dry["status"] == "OK"
        assert dry["dry_run"] is True
        assert dry["dispatchable"] is False
        assert dry["blocked_by_execution_flow"] is True
        assert "claim_command" not in dry
        assert "execution_prompt" not in dry
        assert "multimodel_intervention" not in dry
        assert dry["blocked_actions"] == ["dispatch_claim_and_execute"]
        assert dry["execution_flow_dispatch_decision"]["allowed_to_dispatch"] is False
        assert dry["execution_flow_dispatch_decision"]["reason"] == "stage_boundary:human_gate"
        assert task_path.read_text(encoding="utf-8") == before


def test_execution_flow_dispatch_decision_normalizes_hard_boundaries():
    mod = load_orchestrator_module()
    payload = {
        "enterprise_gate": {"status": "PASS"},
        "evaluations": [
            {"workflow_stage": " Pending ", "boundary_class": " External_Side_Effect "},
        ],
    }

    decision = mod.execution_flow_dispatch_decision(payload)

    assert decision == {"allowed_to_dispatch": False, "reason": "hard_boundary:external_side_effect"}


def test_execution_flow_dispatch_decision_blocks_review_writeback_and_done_boundaries():
    mod = load_orchestrator_module()
    for stage in [" Review ", "writeback", "DONE"]:
        payload = {
            "enterprise_gate": {"status": "PASS"},
            "evaluations": [
                {"workflow_stage": stage, "boundary_class": "Evidence"},
            ],
        }

        decision = mod.execution_flow_dispatch_decision(payload)

        assert decision == {"allowed_to_dispatch": False, "reason": f"stage_boundary:{stage.strip().lower()}:evidence"}


def test_command_add_work_task_binds_source_weighting_policy_before_dispatch_hook():
    td, _vault, env = make_env_and_vault()
    with td:
        seed_project_profile(env, aliases=["hermes-agent"], project="hermes")
        created = json.loads(run(
            env,
            "add",
            "production add-created Hermes work task regression",
            "--priority",
            "P1",
            "--project",
            "hermes-agent",
            "--lane",
            "work",
            "--expires-at",
            "2099-01-01",
            "--json",
        ).stdout)
        task_path = Path(created["created"])
        task_text = task_path.read_text(encoding="utf-8")
        assert "lane: work" in task_text
        assert "project: hermes-agent" in task_text
        assert "source_weighting_policy_ref:" in task_text
        assert "hermes.json#source_weighting_policy" in task_text

        rows = json.loads(run(env, "list", "--json").stdout)["rows"]
        row = next(r for r in rows if r["id"] == created["id"])
        assert row["project"] == "hermes-agent"
        assert row["project_profile_missing"] is False
        assert row["project_profile_path"].endswith("/project-profiles/hermes.json")
        assert row["dispatchable"] is True
        nxt = json.loads(run(env, "next", "--json").stdout)["next"]
        assert nxt and nxt["id"] == created["id"]


def test_command_add_work_task_fails_closed_without_source_weighting_policy():
    td, _vault, env = make_env_and_vault()
    with td:
        profile_path = Path(env["HERMES_PROJECT_PROFILES_DIR"]) / "hermes.json"
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        profile.pop("source_weighting_policy", None)
        profile_path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
        r = run(
            env,
            "add",
            "malformed work task must not be created dispatch-dead",
            "--priority",
            "P1",
            "--project",
            "hermes",
            "--lane",
            "work",
            "--expires-at",
            "2099-01-01",
            "--json",
            check=False,
        )
        assert r.returncode != 0
        assert "source_weighting_policy" in r.stderr
        rows = json.loads(run(env, "list", "--json").stdout)["rows"]
        assert not any(r["title"] == "malformed work task must not be created dispatch-dead" for r in rows)


def test_add_repo_capability_absorption_creates_governed_capability_task():
    td, _vault, env = make_env_and_vault()
    with td:
        created = json.loads(run(
            env,
            "add-repo-capability-absorption",
            "--source-url",
            "https://github.com/example/capability-tool",
            "--capability-name",
            "Document Extractor",
            "--capability-claim",
            "Convert PDFs and office docs into structured Markdown",
            "--target-surface",
            "cli_wrapper",
            "--integration-level",
            "wrap",
            "--expires-at",
            "2099-01-01",
            "--json",
        ).stdout)
        assert created["status"] == "OK", created
        assert created["absorption_type"] == "repo_capability_absorption"
        assert created["target_surface"] == "cli_wrapper"
        task_path = Path(created["created"])
        text = task_path.read_text(encoding="utf-8")
        assert "absorption_type: repo_capability_absorption" in text
        assert "source_url: https://github.com/example/capability-tool" in text
        assert "capability_name: Document Extractor" in text
        assert "target_surface: cli_wrapper" in text
        assert "integration_level: wrap" in text
        assert "completion_boundary: taskpool_candidate" in text
        assert "## Capability Intake Gates" in text
        assert "Real reproduction" in text
        assert "no runtime integration opened by creation command" in text
        listed = json.loads(run(env, "list", "--json").stdout)
        assert listed["task_count"] == 1
        assert listed["rows"][0]["id"] == created["id"]


def add_work_closeout_pair(env, title="Lark 修复闭环"):
    r = run(
        env,
        "add-work-closeout-pair",
        title,
        "--priority",
        "P1",
        "--project",
        "uvisa-app-2.0",
        "--objective",
        "完成 Lark 已发补闭环，并等待用户派发线上 UI 回测闭环。",
        "--accept",
        "已发补闭环本地验收完成；线上 UI 回测在用户授权后执行。",
        "--expires-at",
        "2099-01-01",
        "--json",
    )
    result = json.loads(r.stdout)
    assert result["status"] == "OK", result
    for task_key in ("implementation_task", "ui_retest_task"):
        task_path = Path(result[task_key]["path"])
        text = task_path.read_text(encoding="utf-8")
        if "lane: work" in text and "source_weighting_policy_ref:" not in text:
            text = text.replace("workflow_contract:", f"source_weighting_policy_ref: project-profile:{result[task_key].get('project') or 'work'}:test\nworkflow_contract:", 1)
            task_path.write_text(text, encoding="utf-8")
    return result


def add_evolution_task(env, title="优化本地任务池自进化", priority="P0"):
    r = run(
        env,
        "add",
        title,
        "--priority",
        priority,
        "--project",
        "self-improvement",
        "--lane",
        "evolution",
        "--architecture-target",
        "taskpool",
        "--capability-delta",
        "bounded autorun safety",
        "--anti-drift-check",
        "work lane must not be preempted",
        "--acceptance-evidence",
        "eligibility-check blocks evolution while work is available",
        "--expires-at",
        "2099-01-01",
        "--json",
    )
    created = json.loads(r.stdout)
    assert created["status"] == "OK"
    return created["id"], Path(created["created"])


def add_review_evolution_task(env, title="验证 final landed 证据门"):
    task_id, task_path = add_evolution_task(env, title=title, priority="P1")
    text = task_path.read_text(encoding="utf-8")
    for status in ("pending", "claimed", "running", "retry", "blocked", "done"):
        if f"status: {status}" in text:
            text = text.replace(f"status: {status}", "status: review", 1)
            break
    for prefix in ("claimed_by:", "claim_expires_at:", "run_id:"):
        lines = []
        for line in text.splitlines():
            if line.startswith(prefix):
                lines.append(prefix + " ")
            else:
                lines.append(line)
        text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    text = text.replace("evidence: []", "evidence:\n  - command:selfcheck PASS", 1)
    task_path.write_text(text, encoding="utf-8")
    return task_id, task_path


def annotate_manual_review(task_path, *, action="approve_reopen", final_landed=False, reason="needs real final landed evidence"):
    text = task_path.read_text(encoding="utf-8")
    fields = (
        f'manual_review_decided_at: "2026-05-27T16:00:00+08:00"\n'
        'manual_review_decided_by: "user-approved-multimodel-review"\n'
        'manual_review_classification: "REOPEN_FOR_TASKPOOL"\n'
        f'manual_review_approval_action: "{action}"\n'
        f'manual_review_final_landed: {str(final_landed).lower()}\n'
        'manual_review_result_ref: "/tmp/manual-review.json"\n'
        f'manual_review_reason: "{reason}"\n'
    )
    text = text.replace("claimed_by: ", fields + "claimed_by: ", 1)
    task_path.write_text(text, encoding="utf-8")


def add_mission_envelope_fields(task_path, *, valid=True):
    text = task_path.read_text(encoding="utf-8")
    marker = "evidence: []"
    fields = """
mission_schema_version: v1
mission_id: mission-test-envelope
mission_title: Mission test envelope
mission_objective: Prove mission envelope schema is enforced by taskpool gates
mission_constraints: [\"no-markdown-execution\", \"work-lane-priority\"]
red_lines: [\"do-not-bypass-review\"]
non_goals: [\"broad-autonomous-runner\"]
evidence_refs: [\"file:/tmp/mission-evidence.json\"]
acceptance_criteria: [\"selfcheck-pass\", \"proof-check-pass\"]
dag_nodes: [\"schema\", \"validator\", \"verification\"]
checkpoint_states: [\"schema_added\", \"tests_pass\"]
permission_gates: [\"selfcheck_pass\", \"proof_check_pass\", \"dispatch_dry_run_parse\"]
handoff_artifacts: [\"artifact:mission-handoff\"]
proof_artifacts: [\"artifact:mission-proof\"]
rollback_signal: revert scoped orchestrator mission-envelope patch
certification_status: advisory
ratification_artifact: artifact:mission-incident-mm-advisory
""".lstrip()
    if not valid:
        # add_evolution_task may synthesize a default mission_id before this
        # helper overlays test-specific mission fields. Remove all mission_id
        # lines so the fail-closed missing-field assertion remains meaningful.
        fields = fields.replace("mission_id: mission-test-envelope\n", "", 1)
        text = "\n".join(line for line in text.splitlines() if not line.startswith("mission_id:")) + "\n"
    text = text.replace("concepts: [\"task\"]", "concepts: [\"missions\", \"mission-envelope\", \"proof-gate\"]", 1)
    text = text.replace(marker, fields + marker, 1)
    task_path.write_text(text, encoding="utf-8")


def add_non_blocking_auto_subtask_parent_fields(task_path, child_id):
    text = task_path.read_text(encoding="utf-8")
    text = text.replace("status: pending", "status: blocked", 1)
    marker = "evidence: []"
    fields = f"""
auto_subtask_kind: non_convergence_narrowing
auto_subtask_children: [\"{child_id}\"]
auto_subtask_open_children: []
auto_subtask_missing_children: []
auto_subtask_ready_for_parent: false
""".lstrip()
    text = text.replace(marker, fields + marker, 1)
    task_path.write_text(text, encoding="utf-8")


def add_mission_node_fields(task_path, *, mission_id="mission-alpha", node_id="node-a", depends_on=None, gates=None):
    depends_on = depends_on or []
    gates = gates if gates is not None else ["fixture-mission-node-gate"]
    text = task_path.read_text(encoding="utf-8")
    marker = "evidence: []"
    fields = (
        f"mission_id: {mission_id}\n"
        f"mission_node_id: {node_id}\n"
        f"mission_node_depends_on: {json.dumps(depends_on, ensure_ascii=False)}\n"
        f"permission_gates: {json.dumps(gates, ensure_ascii=False)}\n"
    )
    text = text.replace('concepts: ["task"]', 'concepts: ["missions", "mission-node"]', 1)
    text = text.replace(marker, fields + marker, 1)
    task_path.write_text(text, encoding="utf-8")


def mark_task_done_directly(task_path):
    text = task_path.read_text(encoding="utf-8")
    text = text.replace("status: pending", "status: done", 1)
    text = text.replace("evidence: []", "evidence:\n  - command: fixture done PASS", 1)
    task_path.write_text(text, encoding="utf-8")



def test_mission_envelope_create_boundary_synthesizes_complete_envelope():
    td, _vault, env = make_env_and_vault()
    old_env = os.environ.copy()
    with td:
        try:
            os.environ.update(env)
            mod = load_orchestrator_module()
            setattr(mod, "maybe_fire_taskpool_event_hook", lambda *a, **k: {"status": "FAKE"})
            created = mod.command_add(SimpleNamespace(
                title="Mission envelope producer guard",
                priority="P1",
                project="hermes-evolution",
                status="pending",
                expires_at="2099-01-01",
                expires_days=30,
                concepts="task,mission-envelope",
                lane="evolution",
                architecture_target="taskpool",
                capability_delta="prevent partial mission envelopes",
                anti_drift_check="selfcheck must remain fail-closed",
                acceptance_evidence="mission_envelope_missing returns empty",
                priority_layer="P1",
                dependency_order="1",
                multimodel_triage_result="P2",
                requires_multimodel=False,
                multimodel_reason="",
                expected_participants="",
                truth_gate="",
                evidence_bundle="",
                layer="L3",
                workflow_contract=mod.DEFAULT_WORKFLOW,
                workspace="",
                parallel_boundary="",
                objective="Create a mission envelope task without partial structure.",
                accept="selfcheck can parse the created note.",
                red_line=[],
                non_goal=[],
                evidence_ref=[],
            ))
            task = mod.find_task(created["id"])
            assert task is not None
            assert mod.is_mission_envelope_fm(task.fm) is True
            assert mod.mission_envelope_missing(task.fm) == []
            assert task.fm["mission_schema_version"] == "mission_envelope_v1"
            assert task.fm["certification_status"] == "not_certified"
            assert task.fm["ratification_artifact"] == "proof:ratification-pending"
            assert "proof:task-add-boundary" in task.fm["evidence_refs"]
            assert "do not treat synthesized envelope structure as implementation proof" in task.fm["non_goals"]
        finally:
            os.environ.clear()
            os.environ.update(old_env)



def test_mission_envelope_certified_requires_structured_ratification_ref():
    td, vault, env = make_env_and_vault()
    old_env = os.environ.copy()
    with td:
        try:
            os.environ.update(env)
            mod = load_orchestrator_module()
            artifact = vault / "certification.json"
            artifact.write_text('{"status":"certified"}', encoding="utf-8")
            fm = {
                "concepts": ["task", "mission-envelope"],
                "mission_schema_version": "mission_envelope_v1",
                "mission_id": "mission-absolute-ratification",
                "mission_title": "absolute ratification fixture",
                "mission_objective": "prove absolute path compatibility",
                "mission_constraints": ["constraint"],
                "architecture_target": "taskpool",
                "capability_delta": "compatibility",
                "anti_drift_check": "fail closed",
                "red_lines": ["safe"],
                "non_goals": ["none"],
                "evidence_refs": [f"artifact:{artifact}"],
                "acceptance_criteria": ["accepted"],
                "dag_nodes": ["node:absolute"],
                "checkpoint_states": ["checkpoint:created"],
                "permission_gates": ["authority:budget-handoff"],
                "handoff_artifacts": [f"artifact:{artifact}"],
                "proof_artifacts": [f"artifact:{artifact}"],
                "rollback_signal": "revert fixture",
                "certification_status": "certified",
                "ratification_artifact": f"artifact:{artifact}",
            }
            assert mod.evidence_is_structured(str(artifact)) is False
            assert mod.evidence_is_structured(f"artifact:{artifact}") is True
            assert mod.mission_envelope_missing(fm) == []

            fm["ratification_artifact"] = str(artifact)
            assert "ratification_artifact:structured_ref" in mod.mission_envelope_missing(fm)
            assert "certified_requires_ratification_artifact" in mod.mission_envelope_missing(fm)
        finally:
            os.environ.clear()
            os.environ.update(old_env)


def test_mission_structured_ref_canonicalizes_absolute_paths_even_when_present():
    td, vault, env = make_env_and_vault()
    old_env = os.environ.copy()
    with td:
        try:
            os.environ.update(env)
            mod = load_orchestrator_module()
            artifact = vault / "present.json"
            artifact.write_text("{}", encoding="utf-8")
            missing_artifact = vault / "missing.json"

            assert mod._mission_structured_ref(str(artifact)) == f"artifact:{artifact}"
            assert mod._mission_structured_ref(str(missing_artifact)) == f"artifact:{missing_artifact}"
            assert mod._mission_structured_ref("https://web-check.xyz/") == "url:https://web-check.xyz/"
            assert mod._mission_structured_ref(f"artifact:{artifact}") == f"artifact:{artifact}"
        finally:
            os.environ.clear()
            os.environ.update(old_env)


def test_multimodel_writeback_completes_partial_mission_envelope_without_certifying_failure():
    td, _vault, env = make_env_and_vault()
    old_env = os.environ.copy()
    with td:
        try:
            os.environ.update(env)
            mod = load_orchestrator_module()
            setattr(mod, "refresh_derived_task_views", lambda *a, **k: {"status": "SKIPPED"})
            created = mod.create_task_note(
                title="Mission envelope writeback guard",
                priority="P1",
                project="hermes-evolution",
                status="pending",
                expires_at="2099-01-01",
                concepts=["task", "mission-envelope"],
                lane="evolution",
                architecture_target="taskpool",
                capability_delta="repair writeback boundary",
                anti_drift_check="failed multimodel round must not certify task",
                acceptance_evidence="mission_envelope_missing returns empty after writeback",
                priority_layer="P1",
                dependency_order=["1"],
                multimodel_triage_result="P2",
                objective="Keep mission envelope complete after multimodel writeback.",
                extra_frontmatter={"ratification_artifact": ""},
            )
            task = mod.find_task(created["id"])
            assert task is not None
            for field in mod.MISSION_ENVELOPE_REQUIRED_FIELDS:
                task.fm.pop(field, None)
            task.fm["concepts"] = ["task", "mission-envelope"]
            task.fm["mission_title"] = "Partial writeback fixture"
            assert "mission_schema_version" in mod.mission_envelope_missing(task.fm)

            result = mod.write_multimodel_result_to_task(
                task,
                {"status": "FAIL", "decision": "CONTINUE_LOOP", "failures": ["fixture_failure"]},
                "/tmp/discussion_result.json",
                "/tmp/state.json",
            )
            fresh = mod.find_task(created["id"])
            assert result["passed"] is False
            assert fresh is not None
            assert mod.mission_envelope_missing(fresh.fm) == []
            assert fresh.fm["certification_status"] == "not_certified"
            assert fresh.fm["ratification_artifact"] == "artifact:/tmp/discussion_result.json"
            assert "multimodel_ratification_artifact" not in fresh.fm
            assert "proof:multimodel-writeback-boundary" in fresh.fm["evidence_refs"]
        finally:
            os.environ.clear()
            os.environ.update(old_env)



def test_add_persists_explicit_multimodel_contract_and_triggers_without_heuristics():
    td, _vault, env = make_env_and_vault()
    with td:
        created = json.loads(run(
            env,
            "add",
            "普通外部仓库分析",
            "--priority",
            "P2",
            "--project",
            "research",
            "--requires-multimodel",
            "--multimodel-reason",
            "external repo priority analysis requires independent model agreement",
            "--expected-participants",
            "claude-fable-5,gpt-5.5,deepseek-v4-pro",
            "--truth-gate",
            "evidence-first ratification with canonical participant IDs",
            "--evidence-bundle",
            "repo-analysis.md",
            "--json",
        ).stdout)
        assert created["status"] == "OK", created
        task_text = Path(created["created"]).read_text(encoding="utf-8")
        assert "requires_multimodel: true" in task_text
        assert "multimodel_reason:" in task_text
        assert "expected_participants:" in task_text
        rows = json.loads(run(env, "list", "--json").stdout)["tasks"]
        row = next(r for r in rows if r["id"] == created["id"])
        assert row["requires_multimodel"] is True, row
        assert row["multimodel_intervention_required"] is True, row
        assert "explicit_requires_multimodel" in row["multimodel_intervention_reasons"], row
        assert row["expected_participants"] == ["claude-fable-5", "gpt-5.5", "deepseek-v4-pro"], row
        assert row["truth_gate"], row
        assert row["evidence_bundle"] == "repo-analysis.md", row


def test_ingest_inbox_preserves_explicit_multimodel_contract_metadata():
    td, vault, env = make_env_and_vault()
    with td:
        run(env, "ingest-inbox", "--json")
        inbox = vault / "05-实践与项目" / "tasks" / "任务收件箱.md"
        inbox_text = inbox.read_text(encoding="utf-8")
        inbox_text = inbox_text.replace(
            "## Ingested Log",
            "- [ ] 外部文章任务 | priority:P2 | project:research | priority_layer:P2 | dependency_order:1 | multimodel_triage_result:P2-explicit-multimodel | requires_multimodel:true | multimodel_reason:external article priority analysis | expected_participants:claude-fable-5,gpt-5.5 | truth_gate:evidence-first | evidence_bundle:article-notes.md\n\n## Ingested Log",
        )
        inbox.write_text(inbox_text, encoding="utf-8")
        ing = json.loads(run(env, "ingest-inbox", "--write", "--json").stdout)
        assert ing["created_count"] >= 1, ing
        created = ing["created"][0]
        task_text = Path(created["created"]).read_text(encoding="utf-8")
        assert "requires_multimodel: true" in task_text
        assert "expected_participants:" in task_text
        rows = json.loads(run(env, "list", "--json").stdout)["tasks"]
        row = next(r for r in rows if r["id"] == created["id"])
        assert row["requires_multimodel"] is True, row
        assert "explicit_requires_multimodel" in row["multimodel_intervention_reasons"], row
        assert row["expected_participants"] == ["claude-fable-5", "gpt-5.5"], row


def test_ingest_inbox_derives_preadd_triage_metadata_from_priority_when_missing():
    td, vault, env = make_env_and_vault()
    with td:
        run(env, "ingest-inbox", "--json")
        inbox = vault / "05-实践与项目" / "tasks" / "任务收件箱.md"
        inbox_text = inbox.read_text(encoding="utf-8")
        inbox_text = inbox_text.replace(
            "## Ingested Log",
            "- [ ] 新外部仓库分析 | priority:P1 | project:research | concepts:repo,external | objective:inspect repo and classify taskpool priority\n\n## Ingested Log",
        )
        inbox.write_text(inbox_text, encoding="utf-8")
        ing = json.loads(run(env, "ingest-inbox", "--write", "--json").stdout)
        assert ing["created_count"] >= 1, ing
        created = ing["created"][0]
        task_text = Path(created["created"]).read_text(encoding="utf-8")
        assert "priority: P1" in task_text
        assert "priority_layer: P1" in task_text
        assert "dependency_order:" in task_text and "\"1\"" in task_text
        assert "multimodel_triage_result: P1-preadd-intake-triage:research:repo-external" in task_text
        rows = json.loads(run(env, "list", "--json").stdout)["rows"]
        row = next(r for r in rows if r["id"] == created["id"])
        assert row["priority"] == "P1", row
        assert row["priority_layer"] == "P1", row
        assert row["multimodel_triage_result"] == "P1-preadd-intake-triage:research:repo-external", row


def test_mission_envelope_schema_is_enforced_fail_closed():
    td, _vault, env = make_env_and_vault()
    with td:
        mission_id, mission_path = add_evolution_task(env, title="Mission envelope schema gate", priority="P0")
        add_mission_envelope_fields(mission_path, valid=False)

        rows = json.loads(run(env, "list", "--json").stdout)["rows"]
        mission_row = next(r for r in rows if r["id"] == mission_id)
        assert mission_row["mission_envelope_valid"] is False
        assert "mission_id" in mission_row["mission_envelope_missing"]
        assert mission_row["dispatchable"] is False

        selfcheck = json.loads(run(env, "selfcheck", "--json", check=False).stdout)
        assert selfcheck["status"] == "FAIL", selfcheck
        assert any(("mission envelope missing" in f or "mission_envelope_missing" in f) and "mission" in f for f in selfcheck["failures"]), selfcheck

        proof = json.loads(run(env, "proof-check", "--include-active", "--json", check=False).stdout)
        assert proof["status"] == "FAIL", proof
        assert any("mission envelope missing" in f and "mission_id" in f for f in proof["failures"]), proof


def test_valid_mission_envelope_preserves_work_priority_and_lifecycle_closeout_gate():
    td, _vault, env = make_env_and_vault()
    with td:
        seed_project_profile(env, aliases=["self-improvement", "client-work"])
        mission_id, mission_path = add_evolution_task(env, title="Mission envelope valid", priority="P0")
        add_mission_envelope_fields(mission_path, valid=True)
        work_id, work_path = add_task(env, title="客户 work P0 不能被 mission 抢占", priority="P0", project="client-work")
        work_text = work_path.read_text(encoding="utf-8")
        work_text = work_text.replace("workflow_contract:", "source_weighting_policy_ref: project-profile:client-work:test\nworkflow_contract:", 1)
        work_path.write_text(work_text, encoding="utf-8")

        rows = json.loads(run(env, "list", "--json").stdout)["rows"]
        mission_row = next(r for r in rows if r["id"] == mission_id)
        assert mission_row["mission_envelope_valid"] is True
        assert mission_row["dispatchable"] is True
        assert mission_row["mission_id"] == "mission-test-envelope"
        assert json.loads(run(env, "dispatch-dry-run", "--json").stdout)["next"]["id"] == work_id

        run(env, "claim", mission_id, "--actor", "tester", "--ttl-minutes", "10", "--json")
        claimed_to_review = run(env, "transition", mission_id, "--to", "review", "--actor", "tester", "--evidence", "command: direct review", "--json", check=False)
        assert claimed_to_review.returncode != 0
        assert "illegal lifecycle transition: claimed -> review" in claimed_to_review.stderr

        running = json.loads(run(env, "transition", mission_id, "--to", "running", "--actor", "tester", "--json").stdout)
        assert running["to_status"] == "running"
        review = json.loads(run(env, "transition", mission_id, "--to", "review", "--actor", "tester", "--evidence", "command: mission verifier PASS", "--json").stdout)
        assert review["to_status"] == "review"

        discussion = mission_path.parent / "mission-envelope-ratification-pass.json"
        discussion.write_text(json.dumps({
            "status": "certified",
            "task_id": mission_id,
            "context": {"task_id": mission_id, "task_path": str(mission_path)},
            "issue_ledger": [{"id": "I-001", "severity": 2, "status": "resolved"}],
            "ratification_votes": [
                {"model": "claude-fable-5", "vote": "approve", "best_within_constraints": True},
                {"model": "gpt-5.5", "vote": "approve", "best_within_constraints": True},
                {"model": "deepseek-v4-pro", "vote": "approve", "best_within_constraints": True},
                {"model": "mimo-v2.5-pro", "vote": "approve", "best_within_constraints": True},
            ],
            "agreement_matrix": {"framing": 0.9, "approach": 0.9, "implementation_order": 0.9},
            "truth_status": "certified",
            "criteria_satisfied": {"accuracy": True, "long_term_goal": True, "one_shot_landing": True},
            "final_design": {
                "long_term_goal_alignment": True,
                "next_slice": "mission envelope lifecycle closeout",
                "acceptance_evidence": ["command:mission verifier PASS"],
                "rollback_boundary": "revert scoped mission-envelope patch"
            },
        }, ensure_ascii=False), encoding="utf-8")
        gate_pass = json.loads(run(env, "ratification-gate", "--task", mission_id, "--discussion-result", str(discussion), "--json").stdout)
        assert gate_pass["status"] == "PASS", gate_pass
        text = mission_path.read_text(encoding="utf-8")
        text = text.replace("certification_status: advisory", "certification_status: certified", 1)
        if "multimodel_status:" not in text:
            marker = "\nevidence:"
            assert marker in text, text
            text = text.replace(
                marker,
                f"\nmultimodel_status: certified\nmultimodel_ratification_artifact: {discussion}{marker}",
                1,
            )
        else:
            text = text.replace("multimodel_status: advisory", "multimodel_status: certified", 1)
        mission_path.write_text(text, encoding="utf-8")
        passed_row = next(r for r in json.loads(run(env, "list", "--json").stdout)["rows"] if r["id"] == mission_id)
        assert passed_row["multimodel_passed"] is True, passed_row

        done = json.loads(run(
            env,
            "done",
            mission_id,
            "--actor",
            "tester",
            "--evidence",
            "command: mission verifier PASS; proof:browser mission dashboard readback PASS; proof:api mission ledger readback PASS; artifact:mission-proof",
            "--json",
        ).stdout)
        assert done["status"] == "OK", done

        dash = json.loads(run(env, "dashboard", "--write", "--json").stdout)
        assert Path(dash["dashboard"]).exists()
        selfcheck = json.loads(run(env, "selfcheck", "--json").stdout)
        assert selfcheck["status"] == "PASS", selfcheck
        proof = json.loads(run(env, "proof-check", "--include-active", "--json").stdout)
        assert proof["status"] == "PASS", proof


def test_add_list_claim_release_dashboard_inbox_selfcheck():
    td, vault, env = make_env_and_vault()
    with td:
        task_id, _ = add_task(env)

        rows = json.loads(run(env, "list", "--json").stdout)["rows"]
        assert rows and rows[0]["id"] == task_id
        assert rows[0]["priority"] == "P1"
        assert rows[0]["lifecycle_next"] == ["claimed", "blocked", "archived", "expired"]
        nxt = json.loads(run(env, "next", "--json").stdout)["next"]
        assert nxt and nxt["id"] == task_id and nxt["dispatchable"] is True

        lifecycle = json.loads(run(env, "lifecycle", "--json").stdout)
        assert lifecycle["status"] == "PASS", lifecycle
        assert lifecycle["schema"] == "local_brain_task_lifecycle_v1"
        assert lifecycle["transitions"]["pending"] == ["claimed", "blocked", "archived", "expired"]

        claim = json.loads(run(env, "claim", task_id, "--actor", "tester", "--ttl-minutes", "10", "--json").stdout)
        assert claim["claimed_by"] == "tester"

        denied = run(env, "release", task_id, "--actor", "other", "--json", check=False)
        assert denied.returncode != 0

        # A claimed task is not dispatchable until released.
        assert json.loads(run(env, "next", "--json").stdout)["next"] is None

        rel = json.loads(run(env, "release", task_id, "--actor", "tester", "--to-status", "pending", "--json").stdout)
        assert rel["to_status"] == "pending"

        dash = json.loads(run(env, "dashboard", "--write", "--json").stdout)
        assert Path(dash["dashboard"]).exists()
        assert Path(dash["control_center"]).exists()
        assert Path(dash["sorted_pool"]).exists()
        control_center = Path(dash["control_center"]).read_text(encoding="utf-8")
        assert "处理本地大脑任务收件箱" in control_center
        assert "lifecycle --json" in control_center
        assert "dispatch lane order" in control_center
        assert "transition TASK_ID" in control_center
        dashboard_text = Path(dash["dashboard"]).read_text(encoding="utf-8")
        assert "lifecycle_transitions" in dashboard_text
        assert "Lane" in dashboard_text
        assert "Architecture" in dashboard_text
        sorted_pool_text = Path(dash["sorted_pool"]).read_text(encoding="utf-8")
        assert "owner: brain_task_orchestrator.py" in sorted_pool_text
        assert "lifecycle_policy: generated_view_not_actionable" in sorted_pool_text
        assert "Execution is fail-closed from this note" in sorted_pool_text
        assert "each source note must carry its own owner/status/next step before dispatch" in sorted_pool_text

        inbox = vault / "05-实践与项目" / "tasks" / "任务收件箱.md"
        inbox_text = inbox.read_text(encoding="utf-8")
        inbox_text = inbox_text.replace(
            "## Ingested Log",
            "- [ ] 新增收件箱任务 | priority:P0 | project:inbox-test | due:2099-02-01 | concepts:task,test\n\n## Ingested Log",
        )
        inbox.write_text(inbox_text, encoding="utf-8")
        ing = json.loads(run(env, "ingest-inbox", "--write", "--json").stdout)
        assert ing["created_count"] >= 1
        assert "<!-- ingested:" in inbox.read_text(encoding="utf-8")

        no_proof = run(env, "done", task_id, "--actor", "tester", "--json", check=False)
        assert no_proof.returncode != 0

        claim2 = json.loads(run(env, "claim", task_id, "--actor", "tester", "--ttl-minutes", "10", "--json").stdout)
        assert claim2["claimed_by"] == "tester"
        running2 = json.loads(run(env, "transition", task_id, "--to", "running", "--actor", "tester", "--json").stdout)
        assert running2["to_status"] == "running"
        review2 = json.loads(run(env, "transition", task_id, "--to", "review", "--actor", "tester", "--evidence", "command: unit-test PASS", "--json").stdout)
        assert review2["to_status"] == "review"
        done = json.loads(run(
            env,
            "done",
            task_id,
            "--actor",
            "tester",
            "--evidence",
            "command: final unit-test PASS; proof:browser local task console readback PASS; proof:api task ledger readback PASS",
            "--json",
        ).stdout)
        assert done["status"] == "OK"
        proof = json.loads(run(env, "proof-check", "--json").stdout)
        assert proof["status"] == "PASS", proof

        selfcheck = json.loads(run(env, "selfcheck", "--json").stdout)
        assert selfcheck["status"] == "PASS", selfcheck


def test_work_closeout_pair_blocks_ui_retest_until_parent_done_and_user_dispatch_release():
    td, _vault, env = make_env_and_vault()
    with td:
        pair = add_work_closeout_pair(env)
        implementation_id = pair["implementation_task"]["id"]
        retest_id = pair["ui_retest_task"]["id"]

        rows = json.loads(run(env, "list", "--json").stdout)["rows"]
        impl = next(r for r in rows if r["id"] == implementation_id)
        retest = next(r for r in rows if r["id"] == retest_id)
        assert impl["work_closeout_phase"] == "implementation"
        assert impl["dispatchable"] is True
        assert retest["work_closeout_phase"] == "online_ui_retest"
        assert retest["depends_on_task"] == [implementation_id]
        assert retest["manual_dispatch_gate"] == "awaiting_user_ui_retest_dispatch"
        assert retest["manual_dispatch_released"] is False
        assert retest["dispatchable"] is False
        assert any(b.startswith(f"waiting_for_dependency:{implementation_id}") for b in retest["manual_dispatch_blockers"]), retest
        assert "manual_dispatch_gate:awaiting_user_ui_retest_dispatch" in retest["manual_dispatch_blockers"]
        assert "railway_deploy_gate:uvisa-app-tRnN:not_released" in retest["manual_dispatch_blockers"]

        run(env, "claim", implementation_id, "--actor", "tester", "--ttl-minutes", "10", "--json")
        run(env, "transition", implementation_id, "--to", "running", "--actor", "tester", "--json")
        run(env, "transition", implementation_id, "--to", "review", "--actor", "tester", "--evidence", "command: implementation local verification PASS", "--json")
        run(env, "done", implementation_id, "--actor", "tester", "--evidence", "command: implementation closeout PASS test build browser curl commit project-verification", "--json")

        rows_after_parent = json.loads(run(env, "list", "--json").stdout)["rows"]
        retest_after_parent = next(r for r in rows_after_parent if r["id"] == retest_id)
        assert retest_after_parent["dispatchable"] is False
        assert retest_after_parent["dependency_status"][implementation_id] == "done"
        assert retest_after_parent["manual_dispatch_blockers"] == [
            "manual_dispatch_gate:awaiting_user_ui_retest_dispatch",
            "railway_deploy_gate:uvisa-app-tRnN:not_released",
        ]

        release = json.loads(run(env, "authorize-dispatch", retest_id, "--actor", "tester", "--reason", "user explicitly dispatched UI retest", "--json").stdout)
        assert release["status"] == "OK"
        assert release["manual_dispatch_released"] is True

        rows_released = json.loads(run(env, "list", "--json").stdout)["rows"]
        retest_released = next(r for r in rows_released if r["id"] == retest_id)
        assert retest_released["dispatchable"] is False
        assert retest_released["manual_dispatch_blockers"] == ["railway_deploy_gate:uvisa-app-tRnN:not_released"]


def test_authorize_railway_deploy_releases_online_ui_retest_gate_with_matching_commit():
    td, _vault, env = make_env_and_vault()
    old_env = os.environ.copy()
    old_module = sys.modules.get("railway_deploy_gate")
    with td:
        try:
            os.environ.update(env)
            mod = load_orchestrator_module()
            setattr(mod, "maybe_fire_taskpool_event_hook", lambda *a, **k: {"status": "FAKE"})
            pair = mod.command_add_work_closeout_pair(SimpleNamespace(
                title="Railway gated Lark UI retest",
                priority="P1",
                project="uvisa-admin",
                expires_at="2099-01-01",
                expires_days=30,
                objective="完成实现闭环，等待线上 UI 回测。",
                accept="本地验收完成；线上 UI 回测需 Railway 发布绿色。",
            ))
            impl_id = pair["implementation_task"]["id"]
            retest_id = pair["ui_retest_task"]["id"]
            impl = mod.find_task(impl_id)
            impl.fm["status"] = "done"
            mod.save_task(impl)
            retest = mod.find_task(retest_id)
            retest.fm["manual_dispatch_released"] = "true"
            mod.save_task(retest)

            fake_gate = type(sys)("railway_deploy_gate")
            fake_gate.evaluate_gate = lambda **kwargs: {
                "allowed": True,
                "blockers": [],
                "safe_evidence": {
                    "service": "uvisa-admin",
                    "service_status": "SUCCESS",
                    "deployment_id": "dep-1",
                    "branch": "main",
                    "commit_hash": "abc123def",
                    "repo": "cryptolxd/uvisa-admin",
                },
            }
            sys.modules["railway_deploy_gate"] = fake_gate
            release = mod.command_authorize_railway_deploy(SimpleNamespace(
                task=retest_id,
                actor="tester",
                service="",
                expected_commit="abc123",
                workdir="/tmp/linked-railway",
                json=True,
            ))
            assert release["status"] == "OK", release
            assert release["dispatchable"] is True
            assert release["manual_dispatch_blockers"] == []
            fresh = mod.find_task(retest_id)
            assert fresh.fm["railway_deploy_released"] == "true"
            assert fresh.fm["railway_service"] == "uvisa-admin"
            assert fresh.fm["railway_deployment_id"] == "dep-1"
            assert fresh.fm["railway_deployment_commit"] == "abc123def"
        finally:
            if old_module is None:
                sys.modules.pop("railway_deploy_gate", None)
            else:
                sys.modules["railway_deploy_gate"] = old_module
            os.environ.clear()
            os.environ.update(old_env)


def test_release_railway_published_retests_derives_task_a_commit_and_makes_task_b_dispatchable():
    td, _vault, env = make_env_and_vault()
    old_env = os.environ.copy()
    old_module = sys.modules.get("railway_deploy_gate")
    with td:
        try:
            os.environ.update(env)
            mod = load_orchestrator_module()
            setattr(mod, "maybe_fire_taskpool_event_hook", lambda *a, **k: {"status": "FAKE"})
            pair = mod.command_add_work_closeout_pair(SimpleNamespace(
                title="Railway auto Task B trigger",
                priority="P1",
                project="uvisa-admin",
                expires_at="2099-01-01",
                expires_days=30,
                objective="完成实现闭环；PR 合并发布后自动触发线上 UI 回测。",
                accept="Task A commit 发布后 Task B 进入 work 池。",
            ))
            impl_id = pair["implementation_task"]["id"]
            retest_id = pair["ui_retest_task"]["id"]
            impl = mod.find_task(impl_id)
            impl.fm["status"] = "done"
            impl.fm["evidence"] = ["command:npm_run_build PASS", "artifact:git_commit:abc123def4567890"]
            mod.save_task(impl)

            fake_gate = type(sys)("railway_deploy_gate")
            seen = {}
            def fake_evaluate_gate(**kwargs):
                seen.update(kwargs)
                return {
                    "allowed": True,
                    "blockers": [],
                    "safe_evidence": {
                        "service": "uvisa-admin",
                        "service_status": "SUCCESS",
                        "deployment_id": "dep-auto",
                        "branch": "main",
                        "commit_hash": "abc123def4567890",
                    },
                }
            fake_gate.evaluate_gate = fake_evaluate_gate
            sys.modules["railway_deploy_gate"] = fake_gate

            release = mod.command_release_railway_published_retests(SimpleNamespace(
                actor="tester",
                project="uvisa-admin",
                service="",
                workdir="/tmp/railway-linked",
                max_tasks=5,
                dry_run=False,
                json=True,
            ))
            assert release["status"] == "OK", release
            assert release["released_count"] == 1, release
            assert release["released"][0]["task"] == retest_id
            assert release["released"][0]["dispatchable"] is True
            assert seen["expected_commit"] == "abc123def4567890"
            fresh = mod.find_task(retest_id)
            assert fresh.fm["manual_dispatch_released"] == "true"
            assert fresh.fm["railway_deploy_released"] == "true"
            assert fresh.fm["railway_expected_commit"] == "abc123def4567890"
            assert fresh.fm["railway_deployment_id"] == "dep-auto"
            assert mod.work_dispatch_blockers(fresh) == []
        finally:
            if old_module is None:
                sys.modules.pop("railway_deploy_gate", None)
            else:
                sys.modules["railway_deploy_gate"] = old_module
            os.environ.clear()
            os.environ.update(old_env)


def test_work_closeout_pair_fires_event_hook_only_after_metadata_is_persisted():
    td, _vault, env = make_env_and_vault()
    old_env = os.environ.copy()
    with td:
        try:
            os.environ.update(env)
            mod = load_orchestrator_module()
            calls = []

            def fake_event_hook(event, *, task_id="", reason=""):
                task = mod.find_task(task_id)
                calls.append({
                    "event": event,
                    "task_id": task_id,
                    "disabled": os.environ.get("HERMES_TASKPOOL_EVENT_HOOK_DISABLED"),
                    "phase": mod.work_closeout_phase(task),
                    "dispatchable": task.is_dispatchable(),
                    "blockers": mod.work_dispatch_blockers(task),
                })
                return {"status": "FAKE", "task_id": task_id}

            setattr(mod, "maybe_fire_taskpool_event_hook", fake_event_hook)
            result = mod.command_add_work_closeout_pair(SimpleNamespace(
                title="Lark hook race guard",
                priority="P1",
                project="uvisa-app-2.0",
                expires_at="2099-01-01",
                expires_days=30,
                objective="完成实现闭环，等待用户派发线上 UI 回测。",
                accept="本地验收完成；线上 UI 回测用户授权后执行。",
            ))
            impl_id = result["implementation_task"]["id"]
            retest_id = result["ui_retest_task"]["id"]

            assert calls == [
                {
                    "event": "task_added",
                    "task_id": impl_id,
                    "disabled": "1",
                    "phase": "generic",
                    "dispatchable": True,
                    "blockers": [],
                },
                {
                    "event": "task_added",
                    "task_id": retest_id,
                    "disabled": "1",
                    "phase": "generic",
                    "dispatchable": True,
                    "blockers": [],
                },
                {
                    "event": "task_added",
                    "task_id": impl_id,
                    "disabled": None,
                    "phase": "implementation",
                    "dispatchable": True,
                    "blockers": [],
                },
            ]
            retest = mod.find_task(retest_id)
            assert mod.work_closeout_phase(retest) == "online_ui_retest"
            assert mod.work_dispatch_blockers(retest) == [
                f"waiting_for_dependency:{impl_id}:pending",
                "manual_dispatch_gate:awaiting_user_ui_retest_dispatch",
                "railway_deploy_gate:uvisa-app-tRnN:not_released",
            ]
        finally:
            os.environ.clear()
            os.environ.update(old_env)


def test_generic_work_task_remains_dispatchable_without_work_closeout_fields():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id, _ = add_task(env, title="普通 work 任务不带双闭环字段", priority="P1", project="uvisa-app-2.0")
        row = next(r for r in json.loads(run(env, "list", "--json").stdout)["rows"] if r["id"] == task_id)
        assert row["work_closeout_phase"] == "generic"
        assert row["depends_on_task"] == []
        assert row["manual_dispatch_gate"] == ""
        assert row["manual_dispatch_released"] is False
        assert row["manual_dispatch_blockers"] == []
        assert row["dispatchable"] is True


def test_lifecycle_transition_gate_and_audit():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id, task_path = add_task(env, title="验证任务生命周期状态机", project="test-harness")

        pending_to_running = run(env, "transition", task_id, "--to", "running", "--actor", "tester", "--json", check=False)
        assert pending_to_running.returncode != 0
        assert "illegal lifecycle transition" in pending_to_running.stderr or "active claim" in pending_to_running.stderr

        blocked_without_reason = run(env, "transition", task_id, "--to", "blocked", "--actor", "tester", "--json", check=False)
        assert blocked_without_reason.returncode != 0
        assert "requires --reason" in blocked_without_reason.stderr

        blocked = json.loads(run(env, "transition", task_id, "--to", "blocked", "--actor", "tester", "--reason", "external dependency", "--json").stdout)
        assert blocked["from_status"] == "pending"
        assert blocked["to_status"] == "blocked"

        back_to_pending = json.loads(run(env, "transition", task_id, "--to", "pending", "--actor", "tester", "--json").stdout)
        assert back_to_pending["from_status"] == "blocked"
        assert back_to_pending["to_status"] == "pending"

        claim = json.loads(run(env, "claim", task_id, "--actor", "tester", "--ttl-minutes", "10", "--json").stdout)
        assert claim["claimed_by"] == "tester"

        running = json.loads(run(env, "transition", task_id, "--to", "running", "--actor", "tester", "--json").stdout)
        assert running["from_status"] == "claimed"
        assert running["to_status"] == "running"

        review_without_evidence = run(env, "transition", task_id, "--to", "review", "--actor", "tester", "--json", check=False)
        assert review_without_evidence.returncode != 0
        assert "requires structured --evidence" in review_without_evidence.stderr

        review = json.loads(run(env, "transition", task_id, "--to", "review", "--actor", "tester", "--evidence", "command: lifecycle regression PASS", "--json").stdout)
        assert review["from_status"] == "running"
        assert review["to_status"] == "review"

        done_without_evidence = run(env, "transition", task_id, "--to", "done", "--actor", "tester", "--json", check=False)
        assert done_without_evidence.returncode != 0
        assert "requires structured --evidence" in done_without_evidence.stderr

        done = json.loads(run(env, "transition", task_id, "--to", "done", "--actor", "tester", "--evidence", "command: final lifecycle PASS test build browser curl commit verification", "--json").stdout)
        assert done["from_status"] == "review"
        assert done["to_status"] == "done"
        assert done["next_allowed"] == ["archived"]

        note = task_path.read_text(encoding="utf-8")
        assert "Lifecycle transition `pending` -> `blocked`" in note
        assert "Lifecycle transition `review` -> `done`" in note

        task_path.write_text(note.replace('run_id: \n', 'run_id: legacy-run\n', 1), encoding="utf-8")
        lifecycle_dirty = json.loads(run(env, "lifecycle", "--json", check=False).stdout)
        assert lifecycle_dirty["status"] == "FAIL", lifecycle_dirty
        rec = json.loads(run(env, "reconcile", "--write", "--actor", "tester", "--json").stdout)
        assert any(a["action"] == "orphan_claim_metadata_cleared" for a in rec["actions"]), rec

        lifecycle = json.loads(run(env, "lifecycle", "--json").stdout)
        assert lifecycle["status"] == "PASS", lifecycle
        proof = json.loads(run(env, "proof-check", "--json").stdout)
        assert proof["status"] == "PASS", proof


def test_certified_lifecycle_state_can_close_to_done_without_dispatch():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id, task_path = add_task(env, title="认证后关闭任务", project="test-harness")
        note = task_path.read_text(encoding="utf-8")
        task_path.write_text(
            note.replace("status: pending", "status: certified", 1).replace(
                "multimodel_status: ", "multimodel_status: certified", 1
            ).replace(
                "multimodel_ratification_artifact: ", "multimodel_ratification_artifact: artifact:/tmp/certification.json", 1
            ).replace(
                "multimodel_last_gate_status: ", "multimodel_last_gate_status: PASS", 1
            ).replace(
                "multimodel_last_decision: ", "multimodel_last_decision: LOOP_DONE", 1
            ),
            encoding="utf-8",
        )

        rows = json.loads(run(env, "list", "--json").stdout)["rows"]
        row = next(r for r in rows if r["id"] == task_id)
        assert row["status"] == "certified"
        assert row["dispatchable"] is False

        done = json.loads(
            run(
                env,
                "transition",
                task_id,
                "--to",
                "done",
                "--actor",
                "tester",
                "--evidence",
                "command: final lifecycle PASS test build commit verification",
                "--json",
            ).stdout
        )
        assert done["from_status"] == "certified"
        assert done["to_status"] == "done"
        assert done["next_allowed"] == ["archived"]

        lifecycle = json.loads(run(env, "lifecycle", "--json").stdout)
        assert lifecycle["status"] == "PASS", lifecycle


def test_done_closeout_blocks_work_task_missing_execution_flow_harness_proof():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id, task_path = add_task(env, title="Implement backend API and browser UI", priority="P1", project="hermes")
        run(env, "claim", task_id, "--actor", "tester", "--ttl-minutes", "10", "--json")
        run(env, "transition", task_id, "--to", "running", "--actor", "tester", "--json")
        run(env, "transition", task_id, "--to", "review", "--actor", "tester", "--evidence", "command: implementation build test PASS", "--json")
        before = task_path.read_text(encoding="utf-8")

        blocked = run(
            env,
            "transition",
            task_id,
            "--to",
            "done",
            "--actor",
            "tester",
            "--evidence",
            "command: final build test commit verification PASS",
            "--json",
            check=False,
        )

        assert blocked.returncode != 0
        assert "execution_flow_closeout_blocked" in blocked.stderr
        assert "browser_or_ui_surface_proof" in blocked.stderr
        assert "api_or_backend_readback_proof" in blocked.stderr
        assert task_path.read_text(encoding="utf-8") == before


def test_closeout_surface_obligation_classifies_source_vs_implementation():
    mod = load_orchestrator_module()

    class FakeTask:
        def __init__(self, *, lane, title, body="", fm=None, status="review"):
            self.lane = lane
            self.title = title
            self.body = body
            self.status = status
            self.fm = fm or {}

    source_task = FakeTask(
        lane="evolution",
        title="Analyze public browser preview and verify source",
        body="No install, execution, scanning, SaaS upload. Source-identification only.",
        fm={
            "workflow_stage": "evidence",
            "completion_boundary": "taskpool_candidate",
            "harness_surfaces": ["public-preview", "browser", "no-execution"],
            "completion_gate": "ratification-or-selfcheck-review-done",
        },
    )
    source_obligation = mod.closeout_surface_obligation(source_task)
    assert source_obligation["class"] == "source_intake_no_execution"
    assert source_obligation["requires_execution_flow_proof"] is False
    assert source_obligation["reasons"]

    work_task = FakeTask(
        lane="work",
        title="Implement backend API and browser UI",
        fm={"completion_gate": "project-evidence-review-done"},
    )
    work_obligation = mod.closeout_surface_obligation(work_task)
    assert work_obligation["class"] == "implementation"
    assert work_obligation["requires_execution_flow_proof"] is True
    assert work_obligation["requires_ui_proof"] is True
    assert work_obligation["requires_api_proof"] is True


def test_done_closeout_allows_no_execution_evidence_intake_that_mentions_browser_source():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id, task_path = add_task(env, title="Analyze public browser preview and verify source", priority="P2", project="hermes")
        text = task_path.read_text(encoding="utf-8")
        text = text.replace("lane: work", "lane: evolution", 1)
        text = text.replace("completion_gate: project-evidence-review-done", "completion_gate: ratification-or-selfcheck-review-done", 1)
        text = text.replace("workflow_contract:", "architecture_target: taskpool\ncapability_delta: read-only source identification\nanti_drift_check: no install or UI implementation\nacceptance_evidence: source-identification note and recommendation matrix\nworkflow_stage: evidence\ncompletion_boundary: taskpool_candidate\nharness_surfaces: [\"public-preview\", \"browser\", \"no-execution\"]\nrequired_artifacts: [\"source-identification-note\", \"recommendation-matrix\"]\nworkflow_contract:", 1)
        text += "\n## Objective\nVerify source from public browser preview only; no install, execution, UI build, or scanning.\n"
        task_path.write_text(text, encoding="utf-8")
        run(env, "claim", task_id, "--actor", "tester", "--ttl-minutes", "10", "--json")
        run(env, "transition", task_id, "--to", "running", "--actor", "tester", "--json")
        run(env, "transition", task_id, "--to", "review", "--actor", "tester", "--evidence", "artifact:/tmp/source-identification.md", "--json")

        done = json.loads(
            run(
                env,
                "transition",
                task_id,
                "--to",
                "done",
                "--actor",
                "tester",
                "--evidence",
                "artifact:/tmp/source-identification.md recommendation matrix complete no-execution boundary preserved proof-check PASS",
                "--json",
            ).stdout
        )

        assert done["from_status"] == "review"
        assert done["to_status"] == "done"


def test_done_closeout_allows_work_task_with_execution_flow_harness_proof():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id, _task_path = add_task(env, title="Implement backend API and browser UI", priority="P1", project="hermes")
        run(env, "claim", task_id, "--actor", "tester", "--ttl-minutes", "10", "--json")
        run(env, "transition", task_id, "--to", "running", "--actor", "tester", "--json")
        run(env, "transition", task_id, "--to", "review", "--actor", "tester", "--evidence", "command: implementation build test PASS", "--json")

        done = json.loads(
            run(
                env,
                "transition",
                task_id,
                "--to",
                "done",
                "--actor",
                "tester",
                "--evidence",
                "command: final build test commit verification PASS",
                "--evidence",
                "proof:browser route=/wallet viewport=desktop screenshot=/tmp/wallet.png console_errors=0",
                "--evidence",
                "proof:api_readback endpoint=/api/wallet status=200 fields=balance",
                "--json",
            ).stdout
        )

        assert done["from_status"] == "review"
        assert done["to_status"] == "done"


def test_done_closeout_allows_tui_ui_surface_proof_without_browser():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id, _task_path = add_task(env, title="Implement backend API and TUI surface", priority="P1", project="hermes")
        run(env, "claim", task_id, "--actor", "tester", "--ttl-minutes", "10", "--json")
        run(env, "transition", task_id, "--to", "running", "--actor", "tester", "--json")
        run(env, "transition", task_id, "--to", "review", "--actor", "tester", "--evidence", "command: implementation build test PASS", "--json")

        done = json.loads(
            run(
                env,
                "transition",
                task_id,
                "--to",
                "done",
                "--actor",
                "tester",
                "--evidence",
                "command: final build test commit verification PASS",
                "--evidence",
                "proof:ui_surface tui voice.toggle status readback PASS",
                "--evidence",
                "proof:api_readback endpoint=tui_gateway.voice.toggle status=200 fields=record_key",
                "--json",
            ).stdout
        )

        assert done["from_status"] == "review"
        assert done["to_status"] == "done"


def test_done_closeout_ignores_body_placeholders_for_execution_flow_proof():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id, task_path = add_task(env, title="Implement backend API and browser UI", priority="P1", project="hermes")
        note = task_path.read_text(encoding="utf-8")
        task_path.write_text(
            note + "\n## Acceptance placeholders\n- command: run tests before closeout\n- proof:browser required before done\n- proof:api_readback required before done\n",
            encoding="utf-8",
        )
        run(env, "claim", task_id, "--actor", "tester", "--ttl-minutes", "10", "--json")
        run(env, "transition", task_id, "--to", "running", "--actor", "tester", "--json")
        run(env, "transition", task_id, "--to", "review", "--actor", "tester", "--evidence", "command: implementation build test PASS", "--json")
        before = task_path.read_text(encoding="utf-8")

        blocked = run(
            env,
            "transition",
            task_id,
            "--to",
            "done",
            "--actor",
            "tester",
            "--evidence",
            "command: final build test commit verification PASS",
            "--json",
            check=False,
        )

        assert blocked.returncode != 0
        assert "execution_flow_closeout_blocked" in blocked.stderr
        assert "browser_or_ui_surface_proof" in blocked.stderr
        assert "api_or_backend_readback_proof" in blocked.stderr
        assert task_path.read_text(encoding="utf-8") == before


def test_lifecycle_transition_retry_sets_delay_and_count():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id, task_path = add_task(env, title="验证 retry 生命周期")
        run(env, "claim", task_id, "--actor", "tester", "--ttl-minutes", "10", "--json")

        retry_without_reason = run(env, "transition", task_id, "--to", "retry", "--actor", "tester", "--json", check=False)
        assert retry_without_reason.returncode != 0
        assert "requires --reason" in retry_without_reason.stderr

        retry = json.loads(
            run(
                env,
                "transition",
                task_id,
                "--to",
                "retry",
                "--actor",
                "tester",
                "--reason",
                "test flaky external dependency",
                "--delay-minutes",
                "5",
                "--json",
            ).stdout
        )
        assert retry["from_status"] == "claimed"
        assert retry["to_status"] == "retry"

        note = task_path.read_text(encoding="utf-8")
        rows = json.loads(run(env, "list", "--json").stdout)["rows"]
        row = next(r for r in rows if r["id"] == task_id)
        assert row["status"] == "retry"
        assert str(row["retry_count"]) == "1"
        assert row["next_attempt_at"]
        assert row["claimed_by"] == ""
        assert "Reason: test flaky external dependency" in note


def test_lifecycle_fail_closed_edges():
    td, _vault, env = make_env_and_vault()
    with td:
        illegal_add = run(env, "add", "非法完成态任务", "--status", "done", "--json", check=False)
        assert illegal_add.returncode != 0
        assert "add can only create initial statuses" in illegal_add.stderr
        proposed_path = Path(json.loads(run(env, "add", "验证 proposed 不直接派发", "--status", "proposed", "--json").stdout)["created"])
        proposed_rows = json.loads(run(env, "list", "--json").stdout)["rows"]
        proposed_row = next(r for r in proposed_rows if r["id"] == proposed_path.stem)
        assert proposed_row["status"] == "proposed"
        assert proposed_row["dispatchable"] is False
        proposed_next = json.loads(run(env, "next", "--json").stdout)
        assert proposed_next["next"] is None
        assert "claim_command" not in proposed_next

        task_id, task_path = add_task(env, title="验证生命周期失败关闭边界")
        bad_force = run(env, "transition", task_id, "--to", "done", "--force", "--evidence", "command: forced close", "--json", check=False)
        assert bad_force.returncode != 0
        assert "--force requires --reason" in bad_force.stderr

        bad_reason = run(env, "transition", task_id, "--to", "blocked", "--reason", "line1\nforged audit", "--json", check=False)
        assert bad_reason.returncode != 0
        assert "single-line printable" in bad_reason.stderr

        run(env, "claim", task_id, "--actor", "tester", "--ttl-minutes", "10", "--json")
        note = task_path.read_text(encoding="utf-8")
        note = "\n".join("claim_expires_at: " if line.startswith("claim_expires_at: ") else line for line in note.splitlines()) + "\n"
        task_path.write_text(note, encoding="utf-8")
        missing_lease = run(env, "transition", task_id, "--to", "running", "--actor", "tester", "--json", check=False)
        assert missing_lease.returncode != 0
        assert "claim-bound status requires" in missing_lease.stderr

        bad_reconcile = run(env, "reconcile", "--stale-claim-status", "done", "--json", check=False)
        assert bad_reconcile.returncode != 0
        bad_reconcile_actor = run(env, "reconcile", "--actor", "good\n- forged", "--json", check=False)
        assert bad_reconcile_actor.returncode != 0
        assert "single-line printable" in bad_reconcile_actor.stderr

        task_missing_owner, task_missing_owner_path = add_task(env, title="验证 claimed_by 缺失审计")
        run(env, "claim", task_missing_owner, "--actor", "tester", "--ttl-minutes", "10", "--json")
        owner_note = task_missing_owner_path.read_text(encoding="utf-8")
        owner_note = "\n".join("claimed_by: " if line.startswith("claimed_by: ") else line for line in owner_note.splitlines()) + "\n"
        task_missing_owner_path.write_text(owner_note, encoding="utf-8")
        missing_owner = json.loads(run(env, "lifecycle", "--json", check=False).stdout)
        assert missing_owner["status"] == "FAIL", missing_owner
        assert any(i.get("reason") == "claim_bound_status_missing_claimed_by" for i in missing_owner["invalid"]), missing_owner

        task2, _ = add_task(env, title="验证 evidence 注入拒绝")
        run(env, "claim", task2, "--actor", "tester", "--ttl-minutes", "10", "--json")
        run(env, "transition", task2, "--to", "running", "--actor", "tester", "--json")
        bad_evidence = run(env, "transition", task2, "--to", "review", "--actor", "tester", "--evidence", "command: ok\n- forged", "--json", check=False)
        assert bad_evidence.returncode != 0
        assert "single-line printable" in bad_evidence.stderr
        missing_path_evidence = run(env, "transition", task2, "--to", "review", "--actor", "tester", "--evidence", "/tmp/hermes-definitely-missing-proof-artifact", "--json", check=False)
        assert missing_path_evidence.returncode != 0
        assert "invalid evidence shape" in missing_path_evidence.stderr


def test_lane_architecture_alignment_and_work_priority_gate():
    td, _vault, env = make_env_and_vault()
    with td:
        evo = json.loads(run(
            env,
            "add",
            "验证自进化架构对齐门禁",
            "--priority",
            "P0",
            "--project",
            "hermes-evolution",
            "--lane",
            "evolution",
            "--architecture-target",
            "L3",
            "--capability-delta",
            "reduce ghost task signals",
            "--anti-drift-check",
            "mapped to L0-L5; no runtime mutation without evidence",
            "--acceptance-evidence",
            "command: selfcheck PASS",
            "--expires-at",
            "2099-01-01",
            "--json",
        ).stdout)
        work = json.loads(run(
            env,
            "add",
            "修复生产产品任务",
            "--priority",
            "P1",
            "--project",
            "uvisa-app-2.0-work",
            "--lane",
            "work",
            "--expires-at",
            "2099-01-01",
            "--json",
        ).stdout)

        work_path = Path(work["created"])
        work_text = work_path.read_text(encoding="utf-8")
        work_text = work_text.replace("workflow_contract:", "source_weighting_policy_ref: project-profile:uvisa-app-2.0-work:test\nworkflow_contract:", 1)
        work_path.write_text(work_text, encoding="utf-8")

        rows = json.loads(run(env, "list", "--json").stdout)["rows"]
        evo_row = next(r for r in rows if r["id"] == evo["id"])
        work_row = next(r for r in rows if r["id"] == work["id"])
        assert evo_row["lane"] == "evolution"
        assert evo_row["architecture_target"] == "L3"
        assert evo_row["architecture_aligned"] is True
        assert evo_row["dispatchable"] is True
        assert work_row["lane"] == "work"

        nxt = json.loads(run(env, "next", "--json").stdout)["next"]
        assert nxt["id"] == work["id"], nxt
        assert nxt["lane"] == "work"

        bad = run(
            env,
            "add",
            "缺少架构对齐字段的自进化任务",
            "--priority",
            "P1",
            "--project",
            "hermes-evolution",
            "--lane",
            "evolution",
            "--priority-layer",
            "P1",
            "--dependency-order",
            "1",
            "--multimodel-triage-result",
            "P2",
            "--json",
            check=False,
        )
        assert bad.returncode != 0
        assert "evolution tasks require architecture alignment" in bad.stderr

        blank = run(
            env,
            "add",
            "空白字段绕过自进化门禁",
            "--priority",
            "P1",
            "--project",
            "hermes-evolution",
            "--lane",
            "evolution",
            "--architecture-target",
            "L3",
            "--capability-delta",
            "   ",
            "--anti-drift-check",
            "mapped to L0-L5",
            "--acceptance-evidence",
            "command: selfcheck PASS",
            "--priority-layer",
            "P1",
            "--dependency-order",
            "1",
            "--multimodel-triage-result",
            "P2",
            "--json",
            check=False,
        )
        assert blank.returncode != 0
        assert "capability_delta" in blank.stderr

        bad_lane = run(
            env,
            "add",
            "非法 lane 不得静默降级",
            "--priority",
            "P1",
            "--project",
            "local-brain",
            "--lane",
            "not-a-lane",
            "--json",
            check=False,
        )
        assert bad_lane.returncode != 0

        legacy_id, legacy_path = add_task(env, title="手工遗留自进化任务缺少架构字段", priority="P1", project="manual-work")
        legacy_text = legacy_path.read_text(encoding="utf-8")
        legacy_text = legacy_text.replace("lane: work", "lane: evolution", 1)
        legacy_text = legacy_text.replace("architecture_target: ", "architecture_target: ", 1)
        legacy_path.write_text(legacy_text, encoding="utf-8")

        legacy_rows = json.loads(run(env, "list", "--json").stdout)["rows"]
        legacy_row = next(r for r in legacy_rows if r["id"] == legacy_id)
        assert legacy_row["architecture_aligned"] is False
        assert legacy_row["dispatchable"] is False

        legacy_claim = run(env, "claim", legacy_id, "--actor", "tester", "--json", check=False)
        assert legacy_claim.returncode != 0
        assert "evolution_architecture_alignment_missing" in legacy_claim.stderr

        lifecycle = json.loads(run(env, "lifecycle", "--json", check=False).stdout)
        assert lifecycle["status"] == "FAIL", lifecycle
        assert any(i.get("reason") == "evolution_architecture_alignment_missing" for i in lifecycle["invalid"]), lifecycle

        selfcheck = json.loads(run(env, "selfcheck", "--json", check=False).stdout)
        assert selfcheck["status"] == "FAIL", selfcheck
        assert any("evolution architecture alignment missing" in f for f in selfcheck["failures"]), selfcheck


def test_mission_dag_dashboard_progress_and_ready_nodes():
    td, _vault, env = make_env_and_vault()
    with td:
        a_id, a_path = add_task(env, title="Mission DAG A done", priority="P1", project="mission-project")
        b_id, b_path = add_task(env, title="Mission DAG B ready", priority="P1", project="mission-project")
        c_id, c_path = add_task(env, title="Mission DAG C blocked", priority="P1", project="mission-project")
        add_mission_node_fields(a_path, node_id="node-a")
        add_mission_node_fields(b_path, node_id="node-b", depends_on=["node-a"])
        add_mission_node_fields(c_path, node_id="node-c", depends_on=["node-b"])
        mark_task_done_directly(a_path)

        rows = json.loads(run(env, "list", "--include-done", "--json").stdout)["rows"]
        row_b = next(r for r in rows if r["id"] == b_id)
        row_c = next(r for r in rows if r["id"] == c_id)
        assert row_b["mission_node_ready"] is True, row_b
        assert row_c["mission_node_ready"] is False, row_c
        assert any("waiting_for_dependency:node-b" in x for x in row_c["mission_node_blockers"]), row_c

        dry = json.loads(run(env, "dispatch-dry-run", "--json").stdout)
        assert dry["dispatchable"] is True, dry
        assert dry["next"]["id"] == b_id, dry

        dash = json.loads(run(env, "dashboard", "--write", "--json").stdout)
        summary = next(s for s in dash["mission_summaries"] if s["mission_id"] == "mission-alpha")
        assert summary["total_nodes"] == 3, summary
        assert summary["done_nodes"] == 1, summary
        assert summary["ready_nodes"] == ["node-b"], summary
        assert any(b["node"] == "node-c" and "waiting_for_dependency:node-b" in b["blockers"] for b in summary["blocked_nodes"]), summary
        dashboard_text = Path(dash["dashboard"]).read_text(encoding="utf-8")
        assert "## Mission DAG Progress" in dashboard_text
        assert "mission-alpha" in dashboard_text


def test_mission_dag_cycle_fails_boundary_and_dispatch():
    td, _vault, env = make_env_and_vault()
    with td:
        a_id, a_path = add_task(env, title="Mission DAG cycle A", priority="P1", project="mission-cycle")
        b_id, b_path = add_task(env, title="Mission DAG cycle B", priority="P1", project="mission-cycle")
        add_mission_node_fields(a_path, mission_id="mission-cycle", node_id="node-a", depends_on=["node-b"])
        add_mission_node_fields(b_path, mission_id="mission-cycle", node_id="node-b", depends_on=["node-a"])

        boundary = json.loads(run(env, "boundary-check", "--json", check=False).stdout)
        assert boundary["status"] == "FAIL", boundary
        assert any(i.get("reason") == "mission_dag_cycle" for i in boundary["invalid"]), boundary

        rows = json.loads(run(env, "list", "--json").stdout)["rows"]
        assert next(r for r in rows if r["id"] == a_id)["dispatchable"] is False
        assert next(r for r in rows if r["id"] == b_id)["dispatchable"] is False


def test_multimodel_intervention_and_pua_loop_gate_are_automatic_and_read_only():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id, task_path = add_evolution_task(env, title="pua-loop 自动触发介入与多模型任务池分解", priority="P0")
        intervention = json.loads(run(env, "multimodel-intervention-dry-run", "--json").stdout)
        assert intervention["status"] == "OK", intervention
        assert intervention["intervention_required"] is True, intervention
        assert intervention["selected_task_id"] == task_id, intervention
        selected = intervention["selected"]
        assert selected["pua_loop"]["mode"] == "continue_until_multimodel_pass", selected
        assert selected["criteria"]["accuracy"], selected
        assert selected["criteria"]["long_term_goal"], selected
        assert selected["criteria"]["one_shot_landing"], selected
        assert "consult_models.py run" in selected["run_discussion_command"], selected
        assert "--tier T3" in selected["run_discussion_command"], selected
        assert "--quorum 5" in selected["run_discussion_command"], selected
        assert "target-bound" in selected["pua_loop"]["completion_signal"], selected
        assert "core ratification-gate PASS" in selected["pua_loop"]["completion_signal"], selected
        assert "--max-rounds 3" in selected["run_discussion_command"], selected
        assert "ratification-gate" in selected["gate_command_template"], selected
        assert "status: pending" in task_path.read_text(encoding="utf-8")

        rows = json.loads(run(env, "list", "--json").stdout)["rows"]
        row = next(r for r in rows if r["id"] == task_id)
        assert row["multimodel_intervention_required"] is True, row
        assert "p0_evolution_blast_radius" in row["multimodel_intervention_reasons"], row

        advisory_id, advisory_path = add_evolution_task(
            env,
            title="advisory accuracy architecture closeout ratification slice",
            priority="P2",
        )
        advisory_text = advisory_path.read_text(encoding="utf-8")
        advisory_text = advisory_text.replace("retry_count: 0", "retry_count: 2", 1)
        advisory_text = advisory_text.replace(
            "retry_count: 2",
            "retry_count: 2\nmultimodel_advisory_only: true\nmultimodel_certification_authority: false",
            1,
        )
        advisory_path.write_text(advisory_text, encoding="utf-8")
        advisory = json.loads(run(env, "multimodel-intervention-dry-run", "--task", advisory_id, "--json").stdout)
        assert advisory["status"] == "OK", advisory
        advisory_selected = advisory["selected"]
        assert advisory_selected["advisory_only"] is True, advisory_selected
        assert advisory_selected["recommended_tier"] in {"T1_advisory", "T2_advisory"}, advisory_selected
        assert "--max-rounds 1" in advisory_selected["run_discussion_command"], advisory_selected
        assert "--quorum" not in advisory_selected["run_discussion_command"], advisory_selected

        good = task_path.parent / "discussion-good.json"
        good.write_text(json.dumps({
            "status": "certified",
            "task_id": task_id,
            "context": {"task_id": task_id, "task_path": str(task_path)},
            "issue_ledger": [{"id": "I-001", "severity": 3, "status": "resolved"}],
            "ratification_votes": [
                {"model": "claude-fable-5", "vote": "approve", "best_within_constraints": True},
                {"model": "gpt-5.5", "vote": "approve", "best_within_constraints": True},
                {"model": "deepseek-v4-pro", "vote": "approve", "best_within_constraints": True},
                {"model": "mimo-v2.5-pro", "vote": "approve", "best_within_constraints": True},
            ],
            "agreement_matrix": {"framing": 0.9, "approach": 0.92, "implementation_order": 0.88},
            "truth_status": "certified",
            "criteria_satisfied": {"accuracy": True, "long_term_goal": True, "one_shot_landing": True},
            "final_design": {
                "long_term_goal_alignment": True,
                "next_slice": "patch taskpool intervention gate",
                "acceptance_evidence": ["command:test PASS"],
                "rollback_boundary": "revert scoped orchestrator patch"
            },
        }, ensure_ascii=False), encoding="utf-8")
        gate_pass = json.loads(run(env, "ratification-gate", "--task", task_id, "--discussion-result", str(good), "--json").stdout)
        assert gate_pass["status"] == "PASS", gate_pass
        assert gate_pass["decision"] == "LOOP_DONE", gate_pass

        optional_gemini = task_path.parent / "discussion-optional-gemini.json"
        optional_payload = json.loads(good.read_text(encoding="utf-8"))
        optional_payload["models_consulted"] = [
            "claude-fable-5", "gpt-5.5", "deepseek-v4-pro", "mimo-v2.5-pro", "gemini-3.1-pro-preview"
        ]
        optional_payload["ratification_votes"].append({"model": "gemini-3.1-pro-preview", "vote": "approve", "best_within_constraints": True})
        optional_gemini.write_text(json.dumps(optional_payload, ensure_ascii=False), encoding="utf-8")
        gate_optional_gemini = json.loads(run(env, "ratification-gate", "--task", task_id, "--discussion-result", str(optional_gemini), "--json").stdout)
        assert gate_optional_gemini["status"] == "PASS", gate_optional_gemini
        assert not any("unexpected_consulted_model:gemini-3.1-pro-preview" in f for f in gate_optional_gemini["failures"]), gate_optional_gemini
        assert not any("unexpected_vote_model:gemini-3.1-pro-preview" in f for f in gate_optional_gemini["failures"]), gate_optional_gemini

        text = task_path.read_text(encoding="utf-8")
        text = text.replace(
            "evidence: []",
            f"multimodel_status: certified\nmultimodel_ratification_artifact: {good}\nevidence: []",
            1,
        )
        task_path.write_text(text, encoding="utf-8")
        passed_row = next(r for r in json.loads(run(env, "list", "--json").stdout)["rows"] if r["id"] == task_id)
        assert passed_row["multimodel_passed"] is True, passed_row
        assert passed_row["multimodel_intervention_required"] is False, passed_row

        legacy_text = task_path.read_text(encoding="utf-8")
        legacy_text = legacy_text.replace("multimodel_ratification_artifact", "multimodel_last_discussion_artifact", 1)
        task_path.write_text(legacy_text, encoding="utf-8")
        legacy_row = next(r for r in json.loads(run(env, "list", "--json").stdout)["rows"] if r["id"] == task_id)
        assert legacy_row["multimodel_passed"] is True, legacy_row
        assert legacy_row["multimodel_intervention_required"] is False, legacy_row

        legacy_packet = task_path.parent / "discussion-legacy-packet.json"
        legacy_packet.write_text(json.dumps({
            "schema": "multimodel_certification_packet_v1",
            "target_task_id": task_id,
            "status": "PASS",
            "decision": "LOOP_DONE",
            "truth_gate": {"can_certify_truth": True, "verified_claim_count": 4, "claim_count": 4},
        }, ensure_ascii=False), encoding="utf-8")
        task_path.write_text(task_path.read_text(encoding="utf-8").replace(str(good), str(legacy_packet), 1), encoding="utf-8")
        legacy_packet_row = next(r for r in json.loads(run(env, "list", "--json").stdout)["rows"] if r["id"] == task_id)
        assert legacy_packet_row["multimodel_passed"] is True, legacy_packet_row

        repair_child_id = f"{task_id}-missing-multimodel-certification"
        repair_child = task_path.parent / f"{repair_child_id}.md"
        repair_child.write_text(
            "---\n"
            "type: task\n"
            "lane: evolution\n"
            "status: blocked\n"
            "priority: P2\n"
            "project: hermes\n"
            "completion_gate: ratification-or-selfcheck-review-done\n"
            "truth_gate: parent_done_gate_rechecked_after_repair_evidence\n"
            f"review_gap_parent: {task_id}\n"
            "review_gap_type:\n"
            "  - missing_multimodel_certification\n"
            "review_gap_required_evidence:\n"
            "  - PASS + LOOP_DONE multimodel ratification artifact for the parent task\n"
            f"ratification_artifact: {legacy_packet}\n"
            "retry_count: 3\n"
            "evidence:\n"
            f"  - artifact:{legacy_packet}\n"
            "---\n"
            f"# Task - Repair {task_id}\n",
            encoding="utf-8",
        )
        repair_child_row = next(r for r in json.loads(run(env, "list", "--json").stdout)["rows"] if r["id"] == repair_child_id)
        assert repair_child_row["multimodel_passed"] is True, repair_child_row
        assert repair_child_row["multimodel_intervention_required"] is False, repair_child_row

        ratification_v1 = task_path.parent / "multimodel-ratification-v1.json"
        ratification_v1.write_text(json.dumps({
            "schema": "multimodel_ratification_v1",
            "parent_task_id": task_id,
            "repair_child_task_id": repair_child_id,
            "certification_result": "PASS",
            "loop_done": True,
            "certification_status": "certified",
            "vote": "approve",
            "truth_gate": {"can_certify_truth": True},
            "no_red_line_violations": True,
            "acceptance_criteria_coverage": [{"status": "covered"}],
        }, ensure_ascii=False), encoding="utf-8")
        repair_child.write_text(repair_child.read_text(encoding="utf-8").replace(str(legacy_packet), str(ratification_v1), 1), encoding="utf-8")
        repair_child_v1_row = next(r for r in json.loads(run(env, "list", "--json").stdout)["rows"] if r["id"] == repair_child_id)
        assert repair_child_v1_row["multimodel_passed"] is True, repair_child_v1_row
        assert repair_child_v1_row["multimodel_intervention_required"] is False, repair_child_v1_row

        task_path.write_text(task_path.read_text(encoding="utf-8").replace(str(legacy_packet), str(good), 1), encoding="utf-8")

        mismatched_target = task_path.parent / "discussion-mismatched-target.json"
        mismatched_target.write_text(good.read_text(encoding="utf-8").replace(task_id, "2026-05-10-other-task", 1), encoding="utf-8")
        gate_mismatched = json.loads(run(env, "ratification-gate", "--task", task_id, "--discussion-result", str(mismatched_target), "--json", check=False).stdout)
        assert gate_mismatched["status"] == "FAIL", gate_mismatched
        assert "target_task_mismatch:2026-05-10-other-task" in gate_mismatched["failures"], gate_mismatched

        partial_models = task_path.parent / "discussion-partial-models.json"
        partial = json.loads(good.read_text(encoding="utf-8"))
        partial["models_consulted"] = ["claude-fable-5", "gpt-5.5"]
        partial["ratification_votes"] = partial["ratification_votes"][:2]
        partial_models.write_text(json.dumps(partial, ensure_ascii=False), encoding="utf-8")
        gate_partial_models = json.loads(run(env, "ratification-gate", "--task", task_id, "--discussion-result", str(partial_models), "--json", check=False).stdout)
        assert gate_partial_models["status"] == "FAIL", gate_partial_models
        assert any(f.startswith("model_count_below_required:") for f in gate_partial_models["failures"]), gate_partial_models
        assert "missing_required_model_vote:deepseek-v4-pro" in gate_partial_models["failures"], gate_partial_models
        assert "missing_required_model_vote:mimo-v2.5-pro" in gate_partial_models["failures"], gate_partial_models
        task_path.write_text(task_path.read_text(encoding="utf-8").replace(str(good), str(partial_models), 1), encoding="utf-8")
        failed_row = next(r for r in json.loads(run(env, "list", "--json").stdout)["rows"] if r["id"] == task_id)
        assert failed_row["multimodel_passed"] is False, failed_row
        assert failed_row["multimodel_intervention_required"] is True, failed_row

        bad = task_path.parent / "discussion-bad.json"
        bad.write_text(json.dumps({
            "status": "certified",
            "issue_ledger": [{"id": "I-002", "severity": 4, "status": "unresolved"}],
            "ratification_votes": [{"model": "claude-fable-5", "vote": "approve", "best_within_constraints": True}],
            "agreement_matrix": {"framing": 0.9, "approach": 0.7, "implementation_order": 0.9},
        }, ensure_ascii=False), encoding="utf-8")
        gate_fail = json.loads(run(env, "ratification-gate", "--task", task_id, "--discussion-result", str(bad), "--json", check=False).stdout)
        assert gate_fail["status"] == "FAIL", gate_fail
        assert gate_fail["decision"] == "continue_loop", gate_fail
        assert any("unresolved_severity_4" in f for f in gate_fail["failures"]), gate_fail
        assert any("missing_required_model_vote" in f for f in gate_fail["failures"]), gate_fail

        weak_shell = task_path.parent / "discussion-weak-shell.json"
        weak_shell.write_text(json.dumps({
            "status": "certified",
            "issue_ledger": [],
            "ratification_votes": [
                {"model": "claude", "vote": "approve", "best_within_constraints": True},
                {"model": "gpt-5.5", "vote": "approve", "best_within_constraints": True},
                {"model": "deepseek-v4-pro", "vote": "approve", "best_within_constraints": True},
                {"model": "mimo-v2.5-pro", "vote": "approve", "best_within_constraints": True},
            ],
            "agreement_matrix": {"framing": 0.9, "approach": 0.9, "implementation_order": 0.9},
            "truth_status": "certified",
        }, ensure_ascii=False), encoding="utf-8")
        gate_weak = json.loads(run(env, "ratification-gate", "--task", task_id, "--discussion-result", str(weak_shell), "--json", check=False).stdout)
        assert gate_weak["status"] == "FAIL", gate_weak
        assert gate_weak["decision"] == "continue_loop", gate_weak
        assert any("missing_required_model_vote:claude-fable-5" in f for f in gate_weak["failures"]), gate_weak
        assert any("unexpected_vote_model:claude" in f for f in gate_weak["failures"]), gate_weak
        assert "one_shot_plan_missing" in gate_weak["failures"], gate_weak
        # Shape B: no evidence_bundle -> accuracy_criterion_missing; no final_design -> final_design_missing
        assert "accuracy_criterion_missing" in gate_weak["failures"], gate_weak
        assert "final_design_missing" in gate_weak["failures"], gate_weak
        assert "failure_taxonomy" in gate_weak, gate_weak
        assert "model_vote_missing" in gate_weak["failure_taxonomy"]["active_categories"], gate_weak
        assert "criteria_missing" in gate_weak["failure_taxonomy"]["active_categories"], gate_weak

        malformed = task_path.parent / "discussion-malformed-final-design.json"
        malformed.write_text(json.dumps({
            "status": "certified",
            "final_design": "oops-not-a-dict",
            "ratification_votes": [{"model": "fake", "vote": "approve", "best_within_constraints": True}],
        }, ensure_ascii=False), encoding="utf-8")
        gate_malformed = json.loads(run(env, "ratification-gate", "--task", task_id, "--discussion-result", str(malformed), "--json", check=False).stdout)
        assert gate_malformed["status"] == "FAIL", gate_malformed
        assert gate_malformed["decision"] == "continue_loop", gate_malformed
        assert "failure_taxonomy" in gate_malformed, gate_malformed

        malformed_votes = task_path.parent / "discussion-malformed-votes.json"
        malformed_votes.write_text(json.dumps({
            "status": "certified",
            "models_consulted": 1,
            "ratification_votes": 1,
            "final_design": "oops-not-a-dict",
        }, ensure_ascii=False), encoding="utf-8")
        gate_bad_votes = json.loads(run(env, "ratification-gate", "--task", task_id, "--discussion-result", str(malformed_votes), "--json", check=False).stdout)
        assert gate_bad_votes["status"] == "FAIL", gate_bad_votes
        assert gate_bad_votes["decision"] == "continue_loop", gate_bad_votes
        assert "models_consulted_not_list" in gate_bad_votes["failures"], gate_bad_votes
        assert "provider_parse_error" in gate_bad_votes["failure_taxonomy"]["active_categories"], gate_bad_votes

        malformed_models = task_path.parent / "discussion-malformed-models.json"
        malformed_models.write_text(json.dumps({
            "status": "certified",
            "models_consulted": [{"model": "claude-fable-5"}],
            "ratification_votes": [{"model": "claude-fable-5", "vote": "approve", "best_within_constraints": True}],
            "final_design": "oops-not-a-dict",
        }, ensure_ascii=False), encoding="utf-8")
        gate_bad_models = json.loads(run(env, "ratification-gate", "--task", task_id, "--discussion-result", str(malformed_models), "--json", check=False).stdout)
        assert gate_bad_models["status"] == "FAIL", gate_bad_models
        assert gate_bad_models["decision"] == "continue_loop", gate_bad_models
        assert "models_consulted_invalid" in gate_bad_models["failures"], gate_bad_models


def test_passed_advisory_only_review_task_does_not_rerun_weak_multimodel_loop():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id, task_path = add_task(env, title="Browser replay evidence advisory closeout", priority="P2", project="hermes-agent")
        discussion = task_path.parent / "discussion-advisory.json"
        discussion.write_text(json.dumps({"status": "certified", "task_id": task_id}), encoding="utf-8")
        text = task_path.read_text(encoding="utf-8")
        text = text.replace("status: pending", "status: review", 1)
        text = text.replace(
            "evidence: []",
            "multimodel_status: advisory_completed\n"
            "multimodel_last_gate_status: PASS_ADVISORY_ONLY\n"
            "multimodel_last_decision: CONTINUE_LOOP\n"
            f"multimodel_last_discussion_artifact: {discussion}\n"
            "multimodel_advisory_only: true\n"
            "multimodel_reason: weak advisory already consumed\n"
            "expected_participants: [\"hermes-agent\"]\n"
            "truth_gate: report-evidence-present\n"
            "evidence_bundle: bounded browser evidence\n"
            "architecture_target: taskpool\n"
            "evidence: []",
            1,
        )
        task_path.write_text(text, encoding="utf-8")

        row = next(r for r in json.loads(run(env, "list", "--json").stdout)["rows"] if r["id"] == task_id)
        assert row["status"] == "review", row
        assert row["multimodel_intervention_required"] is False, row
        assert row["multimodel_intervention_reasons"] == [], row

        dry = json.loads(run(env, "multimodel-intervention-dry-run", "--json").stdout)
        assert dry["intervention_required"] is False, dry
        assert dry.get("selected_task_id", "") != task_id, dry


def test_manual_review_final_landed_false_blocks_weak_done_transition():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id, task_path = add_review_evolution_task(env, title="manual review reopen must not auto-close from selfcheck")
        annotate_manual_review(task_path, action="approve_reopen", final_landed=False)

        weak_done = run(
            env,
            "transition",
            task_id,
            "--to",
            "done",
            "--actor",
            "tester",
            "--evidence",
            "command:selfcheck PASS",
            "--json",
            check=False,
        )
        assert weak_done.returncode != 0
        assert "manual_review_final_landed=false requires final landed evidence" in weak_done.stderr


def test_manual_review_final_landed_false_blocks_auto_close_review_without_real_landing_evidence():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id, task_path = add_review_evolution_task(env, title="auto-close review must not treat weak evidence as final landed")
        annotate_manual_review(task_path, action="needs_more_evidence", final_landed=False)

        payload = json.loads(run(env, "auto-close-review", "--task", task_id, "--json").stdout)
        assert payload["closed_count"] == 0, payload
        assert payload["skipped_count"] == 1, payload
        assert payload["skipped"][0]["task_id"] == task_id, payload
        assert payload["skipped"][0]["action"] in {"skip", "return_to_retry", "block_after_certification"}, payload
        row = next(r for r in json.loads(run(env, "list", "--include-done", "--json").stdout)["rows"] if r["id"] == task_id)
        assert row["status"] != "done", row

def test_manual_review_partial_closeout_can_still_close_without_final_landed_gate():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id, task_path = add_review_evolution_task(env, title="approved close_as_partial should remain closable")
        annotate_manual_review(task_path, action="approve_close_as_partial", final_landed=False, reason="partial closeout is explicitly allowed")

        allowed_done = run(
            env,
            "transition",
            task_id,
            "--to",
            "done",
            "--actor",
            "tester",
            "--evidence",
            "command:selfcheck PASS",
            "--json",
        )
        payload = json.loads(allowed_done.stdout)
        assert payload["status"] == "OK", payload
        row = next(r for r in json.loads(run(env, "list", "--include-done", "--json").stdout)["rows"] if r["id"] == task_id)
        assert row["status"] == "done", row


def test_manual_review_reopen_rejects_verification_only_final_landed_evidence():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id, task_path = add_review_evolution_task(env, title="pytest alone is not final landed")
        annotate_manual_review(task_path, action="approve_reopen", final_landed=False)

        verification_only_done = run(
            env,
            "transition",
            task_id,
            "--to",
            "done",
            "--actor",
            "tester",
            "--evidence",
            "command:selfcheck PASS",
            "--evidence",
            "command:pytest PASS",
            "--json",
            check=False,
        )
        assert verification_only_done.returncode != 0
        assert "requires final landed evidence bundle" in verification_only_done.stderr



def test_manual_review_reopen_rejects_implementation_only_final_landed_evidence():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id, task_path = add_review_evolution_task(env, title="commit alone is not final landed")
        annotate_manual_review(task_path, action="approve_reopen", final_landed=False)

        implementation_only_done = run(
            env,
            "transition",
            task_id,
            "--to",
            "done",
            "--actor",
            "tester",
            "--evidence",
            "command:selfcheck PASS",
            "--evidence",
            "command:git commit abc123",
            "--json",
            check=False,
        )
        assert implementation_only_done.returncode != 0
        assert "requires final landed evidence bundle" in implementation_only_done.stderr



def test_manual_review_reopen_accepts_real_final_landed_evidence():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id, task_path = add_review_evolution_task(env, title="real final landed evidence should allow done")
        annotate_manual_review(task_path, action="approve_reopen", final_landed=False)
        readback = task_path.parent / "readback.txt"
        readback.write_text("read-back verified", encoding="utf-8")

        landed_done = run(
            env,
            "transition",
            task_id,
            "--to",
            "done",
            "--actor",
            "tester",
            "--evidence",
            "command:selfcheck PASS",
            "--evidence",
            "command:pytest PASS",
            "--evidence",
            "command:git commit abc123",
            "--evidence",
            f"file:{readback}",
            "--json",
        )
        payload = json.loads(landed_done.stdout)
        assert payload["status"] == "OK", payload
        row = next(r for r in json.loads(run(env, "list", "--include-done", "--json").stdout)["rows"] if r["id"] == task_id)
        assert row["status"] == "done", row


def test_strong_multimodel_trigger_still_preempts_completed_advisory_state():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id, task_path = add_task(env, title="Strong certification after advisory", priority="P2", project="hermes-agent")
        discussion = task_path.parent / "discussion-advisory.json"
        discussion.write_text(json.dumps({"status": "certified", "task_id": task_id}), encoding="utf-8")
        text = task_path.read_text(encoding="utf-8")
        text = text.replace("status: pending", "status: review", 1)
        text = text.replace(
            "evidence: []",
            "requires_multimodel: true\n"
            "multimodel_status: advisory_completed\n"
            "multimodel_last_gate_status: PASS_ADVISORY_ONLY\n"
            f"multimodel_last_discussion_artifact: {discussion}\n"
            "multimodel_advisory_only: true\n"
            "evidence: []",
            1,
        )
        task_path.write_text(text, encoding="utf-8")

        row = next(r for r in json.loads(run(env, "list", "--json").stdout)["rows"] if r["id"] == task_id)
        assert row["multimodel_intervention_required"] is True, row
        assert "explicit_requires_multimodel" in row["multimodel_intervention_reasons"], row


def test_discussion_task_binding_stamp_closes_target_binding_gap():
    mod = load_orchestrator_module()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        task_path = root / "2026-05-10-score445.md"
        task_path.write_text("# Score445 task\n", encoding="utf-8")
        state_path = root / "state.json"
        state_path.write_text(json.dumps({"question": "target-bound state"}), encoding="utf-8")
        task = mod.Task(path=task_path, fm={"status": "review", "priority": "P0"}, body="# Score445 task\n")
        discussion_path = root / "discussion_result.json"
        discussion = {
            "status": "certified",
            "models_consulted": ["claude-fable-5", "gpt-5.5", "deepseek-v4-pro", "mimo-v2.5-pro"],
            "issue_ledger": [],
            "ratification_votes": [
                {"model": "claude-fable-5", "vote": "approve", "best_within_constraints": True},
                {"model": "gpt-5.5", "vote": "approve", "best_within_constraints": True},
                {"model": "deepseek-v4-pro", "vote": "approve", "best_within_constraints": True},
                {"model": "mimo-v2.5-pro", "vote": "approve", "best_within_constraints": True},
            ],
            "agreement_matrix": {"framing": 0.9, "approach": 0.9, "implementation_order": 0.9},
            "truth_status": "grounded",
            "criteria_satisfied": {"accuracy": True, "long_term_goal": True, "one_shot_landing": True},
            "final_design": {
                "next_slice": "land task-bound ratification",
                "acceptance_evidence": ["command:test PASS"],
                "rollback_boundary": "revert orchestrator stamp patch",
            },
        }
        discussion_path.write_text(json.dumps(discussion, ensure_ascii=False), encoding="utf-8")
        before = mod.ratification_gate_result(discussion, expected_task=task)
        assert before["status"] == "FAIL", before
        assert "target_task_binding_missing" in before["failures"], before

        stamp = mod.stamp_discussion_task_binding(discussion_path, task, str(state_path))
        stamped = json.loads(discussion_path.read_text(encoding="utf-8"))
        assert stamp["task_id"] == task.id, stamp
        assert stamped["target_task_id"] == task.id, stamped
        assert stamped["context"]["target_task_path"] == str(task_path), stamped
        assert stamped["taskpool_binding"]["state_sha256"], stamped
        after = mod.ratification_gate_result(stamped, expected_task=task)
        assert after["status"] == "PASS", after
        assert after["decision"] == "LOOP_DONE", after


def test_artifact_structured_ref_legacy_packet_preempts_failed_discussion_artifact():
    mod = load_orchestrator_module()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        task_path = root / "2026-06-05-parent-task.md"
        task_path.write_text("# Parent task\n", encoding="utf-8")
        task = mod.Task(
            path=task_path,
            fm={
                "status": "review",
                "priority": "P0",
                "multimodel_status": "certified",
            },
            body="# Parent task\n",
        )
        pass_path = root / "certification-v1.json"
        pass_packet = {
            "schema": "multimodel_certification_packet_v1",
            "status": "PASS",
            "decision": "LOOP_DONE",
            "target_task_id": task.id,
            "truth_gate": {"can_certify_truth": True},
            "certification": {"multi_model_certified": True},
            "evidence_coverage": 1.0,
        }
        pass_path.write_text(json.dumps(pass_packet, ensure_ascii=False), encoding="utf-8")
        fail_path = root / "discussion_result.json"
        fail_path.write_text(
            json.dumps(
                {
                    "status": "FAIL",
                    "decision": "continue_loop",
                    "target_task_id": task.id,
                    "issue_ledger": [{"id": "still-open", "severity": 4, "status": "open"}],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        task.fm["ratification_artifact"] = f"artifact:{pass_path}"
        task.fm["multimodel_last_discussion_artifact"] = str(fail_path)

        assert mod.resolve_local_artifact_path(f"artifact:{pass_path}") == pass_path
        assert mod.resolve_local_artifact_path("artifact:opaque-label") is None
        assert mod.resolve_local_artifact_path(f"proof:{pass_path}") is None
        assert mod.task_multimodel_artifact(task) == f"artifact:{pass_path}"
        assert mod.task_multimodel_passed(task) is True


def test_ratification_gate_cli_reports_legacy_packet_read_compat_without_relaxing_strict_gate(monkeypatch):
    mod = load_orchestrator_module()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        task_path = root / "2026-06-05-parent-task.md"
        task_path.write_text("# Parent task\n", encoding="utf-8")
        task = mod.Task(path=task_path, fm={"status": "review", "priority": "P0"}, body="# Parent task\n")
        packet_path = root / "certification-v1.json"
        packet_path.write_text(
            json.dumps(
                {
                    "schema": "multimodel_certification_packet_v1",
                    "status": "PASS",
                    "decision": "LOOP_DONE",
                    "target_task_id": task.id,
                    "truth_gate": {"can_certify_truth": True},
                    "certification": {"multi_model_certified": True},
                    "evidence_coverage": 1.0,
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(mod, "find_task", lambda task_id: task if task_id == task.id else None)

        strict = mod.ratification_gate_result(json.loads(packet_path.read_text(encoding="utf-8")), expected_task=task)
        assert strict["status"] == "FAIL", strict
        assert "ratification_votes_missing" in strict["failures"], strict

        result = mod.command_ratification_gate(type("Args", (), {"discussion_result": str(packet_path), "task": task.id})())
        assert result["status"] == "PASS", result
        assert result["decision"] == "LOOP_DONE", result
        assert result["legacy_packet_passed"] is True, result
        assert result["strict_gate_status"] == "FAIL", result
        assert "ratification_votes_missing" in result["strict_gate_failures"], result
        assert "legacy_multimodel_certification_packet_read_compat" in result["warnings"], result



def test_economy_gate_allows_recovery_rerun_after_missing_required_model_smoke_pass():
    mod = load_orchestrator_module()
    with tempfile.TemporaryDirectory() as td:
        health_path = Path(td) / "model-health.json"
        health_path.write_text(json.dumps({
            "models": {
                "mimo-v2.5-pro": {
                    "model": "mimo-v2.5-pro",
                    "provider": "xiaomi",
                    "status": "healthy",
                    "last_ok": True,
                    "last_observed_at": 2000,
                    "unhealthy_until": 0,
                }
            }
        }), encoding="utf-8")
        old_health_path = os.environ.get("HERMES_MODEL_HEALTH_FILE")
        os.environ["HERMES_MODEL_HEALTH_FILE"] = str(health_path)
        try:
            task = mod.Task(
                Path(td) / "missing-mimo.md",
                {
                    "status": "blocked",
                    "retry_count": 9,
                    "multimodel_round_status": "failed",
                    "multimodel_last_checked_at": "1970-01-01T00:00:01+00:00",
                    "multimodel_last_failures": [
                        "missing_required_model_consulted:mimo-v2.5-pro",
                        "missing_required_model_vote:mimo-v2.5-pro",
                        "model_count_below_required:2/3",
                    ],
                },
                "\n".join([f"- Multimodel PUA-loop round {i}: failed" for i in range(5)]),
            )

            gate = mod.task_multimodel_economy_gate(task)
        finally:
            if old_health_path is None:
                os.environ.pop("HERMES_MODEL_HEALTH_FILE", None)
            else:
                os.environ["HERMES_MODEL_HEALTH_FILE"] = old_health_path

        assert gate["action"] == "recovery_rerun", gate
        assert gate["allowed_tier"] == "any", gate
        assert gate["recovered_models"] == ["mimo-v2.5-pro"], gate


def test_finish_multimodel_advisory_only_pass_enters_review_without_done_authority(monkeypatch):
    mod = load_orchestrator_module()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        task_path = root / "2026-07-02-advisory-evidence-only.md"
        body = "# Advisory evidence only\n"
        task_path.write_text(body, encoding="utf-8")
        task = mod.Task(
            path=task_path,
            fm={
                "status": "running",
                "priority": "P2",
                "multimodel_status": "advisory_completed",
                "multimodel_advisory_only": True,
                "multimodel_certification_authority": False,
            },
            body=body,
        )
        monkeypatch.setattr(mod, "find_task", lambda task_id: task if task_id == task.id else None)
        monkeypatch.setattr(mod, "completion_gate_failures", lambda task, evidence: [])
        monkeypatch.setattr(mod, "refresh_derived_task_views", lambda reason: {"status": "OK", "reason": reason})

        result = mod.finish_multimodel_step_running(
            task.id,
            {
                "gate": {"status": "PASS_ADVISORY_ONLY", "decision": "CONTINUE_LOOP", "failures": []},
                "discussion_path": str(root / "discussion_result.json"),
            },
        )

        assert result["status"] == "OK", result
        assert result["to_status"] == "review", result
        assert task.fm["status"] == "review", task.fm
        assert "multimodel_advisory_pass_enter_review_without_done_authority" in task.body


def test_legacy_packet_does_not_authorize_advisory_only_task_or_mismatched_target():
    mod = load_orchestrator_module()
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        task_path = root / "2026-06-05-advisory-task.md"
        task_path.write_text("# Advisory task\n", encoding="utf-8")
        task = mod.Task(
            path=task_path,
            fm={
                "status": "review",
                "priority": "P0",
                "multimodel_status": "advisory_completed",
                "multimodel_advisory_only": True,
                "multimodel_last_gate_status": "PASS_ADVISORY_ONLY",
            },
            body="# Advisory task\n",
        )
        packet_path = root / "certification-v1.json"
        packet_path.write_text(
            json.dumps(
                {
                    "schema": "multimodel_certification_packet_v1",
                    "status": "PASS",
                    "decision": "LOOP_DONE",
                    "target_task_id": "some-other-task",
                    "truth_gate": {"can_certify_truth": True},
                    "certification": {"multi_model_certified": True},
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        task.fm["ratification_artifact"] = f"artifact:{packet_path}"

        discussion = json.loads(packet_path.read_text(encoding="utf-8"))
        assert mod.legacy_multimodel_certification_packet_passed(discussion, task) is False
        assert mod.task_multimodel_passed(task) is False



def test_evidence_spine_exports_stable_ids_and_auto_completer_blocker_semantics():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id, _task_path = add_evolution_task(env, title="pua-loop 自动触发介入与多模型任务池分解", priority="P0")
        cron_path = Path(env["HERMES_CRON_JOBS_PATH"])
        cron_path.parent.mkdir(parents=True, exist_ok=True)
        cron_jobs = [
            {"id": "guardian", "name": "task-pool-guardian-10m", "enabled": True, "schedule": "every 10m", "last_status": "ok"},
            {"id": "pipeline", "name": "pipeline-tick-hourly", "enabled": True, "schedule_display": "every 60m", "last_status": "ok"},
            {"id": "agent-team", "name": "agent-team-cycle-hourly", "enabled": True, "schedule_display": "every 60m", "last_status": "ok"},
            {"id": "envelope", "name": "envelope-executor-cycle", "enabled": True, "schedule_display": "every 60m", "last_status": "ok"},
            {"id": "multimodel", "name": "multimodel-intervention-step", "enabled": True, "schedule_display": "every 60m", "last_status": "ok"},
            {
                "id": "fixture-auto-completer",
                "name": "local-brain-taskpool-auto-completer",
                "enabled": True,
                "schedule": "every 120m",
                "last_status": "error",
                "last_error": "bounded slice completed; state changed running -> review. PASS: scoped tests. full build unrelated baseline blocker TS6133 unused symbol. token=" + "super-secret-token-123456" + " Authorization: Bearer " + "bearer...7890" + " https://example.test/hook?access_token=***",
                "last_delivery_error": "Bearer " + "delivery-secret-1234567890",
                "deliver": "telegram:" + "private-secret-target",

                "next_run_at": "2099-01-01T00:00:00+08:00",
            },
        ]
        cron_path.write_text(json.dumps({"jobs": cron_jobs}, ensure_ascii=False), encoding="utf-8")

        dry = json.loads(run(env, "multimodel-intervention-dry-run", "--json").stdout)
        assert dry["selected_task_id"] == task_id, dry
        assert "--evidence-json" in dry["selected"]["build_state_command"], dry["selected"]["build_state_command"]
        assert "E-TASK-CANONICAL" in dry["selected"]["build_state_command"], dry["selected"]["build_state_command"]
        run(env, "dashboard", "--write", "--json")

        spine = json.loads(run(env, "evidence-spine", "--json").stdout)
        assert spine["schema"] == "local_brain_taskpool_evidence_spine_v1", spine
        assert spine["read_only"] is True, spine
        evidence_ids = {e["evidence_id"] for e in spine["evidence"]}
        assert {"E-TP-COUNTS", "E-TP-GATES", "E-TP-DISPATCH", "E-TP-AUTORUN", "E-TP-AUTO-COMPLETER", "E-TP-MULTIMODEL", "E-TP-CRON"} <= evidence_ids
        auto_ev = next(e for e in spine["evidence"] if e["evidence_id"] == "E-TP-AUTO-COMPLETER")
        cron_job = auto_ev["payload"]["cron_job"]
        assert "last_error" not in cron_job, cron_job
        assert "last_delivery_error" not in cron_job, cron_job
        assert "deliver" not in cron_job, cron_job
        assert "script" not in cron_job, cron_job
        assert "super-secret-token" not in json.dumps(auto_ev, ensure_ascii=False), auto_ev
        assert "bearer-secret" not in json.dumps(auto_ev, ensure_ascii=False), auto_ev
        assert "query-secret" not in json.dumps(auto_ev, ensure_ascii=False), auto_ev
        assert "delivery-secret" not in json.dumps(auto_ev, ensure_ascii=False), auto_ev
        assert "private-secret-target" not in json.dumps(auto_ev, ensure_ascii=False), auto_ev
        assert "secret-script" not in json.dumps(auto_ev, ensure_ascii=False), auto_ev
        assert "[REDACTED]" in cron_job["last_error_tail"], cron_job
        assert "[REDACTED]" in cron_job["last_delivery_error_tail"], cron_job
        assert cron_job["schedule"] == "every 120m", cron_job
        classification = auto_ev["payload"]["classification"]
        assert classification["semantic_status"] == "ok_with_task_blocker", classification
        assert classification["task_result"] == "review_with_baseline_blocker", classification
        assert classification["safe_for_next_tick"] is True, classification
        assert spine["summary"]["auto_completer_semantic_status"] == "ok_with_task_blocker", spine

        cron_path.write_text(json.dumps({"jobs": [
            {"id": "guardian", "name": "task-pool-guardian-10m", "enabled": True, "schedule": "every 10m", "last_status": "ok"}
        ]}, ensure_ascii=False), encoding="utf-8")
        missing_cron = json.loads(run(env, "evidence-spine", "--json", check=False).stdout)
        assert missing_cron["status"] == "FAIL", missing_cron
        assert missing_cron["gate_status"] == "WARN", missing_cron
        assert "local-brain-taskpool-auto-completer" in missing_cron["summary"]["cron_required_missing"], missing_cron


def test_auto_completer_recursive_self_lock_detects_cron_wrapped_dynamic_runner_error():
    mod = load_orchestrator_module()
    tick_summary = {
        "schema": "brain_task_dispatch_tick_summary_v1",
        "status": "ERROR",
        "error_count": 1,
        "recovery_command": "python3 /Users/charles/.hermes/scripts/brain_task_dispatch_tick.py --print-always --no-state",
        "evidence_spine": {
            "status": "ERROR",
            "gate_status": "WARN",
            "summary": {
                "auto_completer_semantic_status": "error",
                "auto_completer_safe_for_next_tick": False,
            },
        },
    }
    runner_error = {
        "schema": "taskpool_dynamic_runner_v1",
        "summary": {"status": "ERROR", "error_count": 1},
        "tick": {
            "cmd": [sys.executable, "/Users/charles/.hermes/scripts/brain_task_dispatch_tick.py", "--summary", "--autorun-step", "--no-state"],
            "returncode": 2,
            "stdout": json.dumps(tick_summary),
        },
    }
    cron_wrapped = json.dumps({"last_error": json.dumps(runner_error), "ts": "2026-05-20T12:00:00Z"})
    classification = mod.classify_auto_completer_job({"last_status": "error", "last_error": cron_wrapped})
    assert classification["semantic_status"] == "recursive_evidence_spine_self_lock", classification
    assert classification["safe_for_next_tick"] is True, classification


def test_auto_completer_classifies_interrupted_dynamic_runner_as_safe_scheduler_noise():
    mod = load_orchestrator_module()
    runner_error = json.dumps({
        "schema": "taskpool_dynamic_runner_v1",
        "tick": {
            "cmd": [sys.executable, "/Users/charles/.hermes/scripts/brain_task_dispatch_tick.py", "--summary", "--parallel-autorun", "--max-agents", "24"],
            "returncode": -15,
            "stdout": "",
        },
    })
    classification = mod.classify_auto_completer_job({"last_status": "error", "last_error": runner_error})
    assert classification["semantic_status"] == "scheduler_interrupted", classification
    assert classification["task_result"] == "scheduler_retry_or_deterministic_replacement_required", classification
    assert classification["safe_for_next_tick"] is True, classification
    assert "scheduler_interrupted" in classification["blockers"], classification


def test_auto_completer_classifies_plain_script_timeout_as_retryable_safe_scheduler_noise():
    mod = load_orchestrator_module()
    classification = mod.classify_auto_completer_job({
        "last_status": "error",
        "last_error": "Script timed out after 120s: /Users/charles/.hermes/scripts/taskpool_dynamic_runner.py",
    })
    assert classification["semantic_status"] == "retryable_runtime_timeout", classification
    assert classification["task_result"] == "scheduler_retry_or_deterministic_replacement_required", classification
    assert classification["safe_for_next_tick"] is True, classification
    assert "retryable_runtime_timeout" in classification["blockers"], classification


def test_auto_completer_classifies_certification_required_tail_as_safe_task_gate():
    mod = load_orchestrator_module()
    last_error = '''... "recommended_tier": "T3_certification", "intervention_required": true,
      "gate_command_template": "python3 ~/.hermes/scripts/brain_task_orchestrator.py ratification-gate --task x --discussion-result DISCUSSION_RESULT_JSON --json",
      "trigger_reasons": ["explicit_requires_multimodel", "truth_gate_contract"],
      "schema": "brain_task_dispatch_tick_summary_v1", "status": "ERROR" ...'''
    classification = mod.classify_auto_completer_job({"last_status": "error", "last_error": last_error})
    assert classification["semantic_status"] == "certification_required_pending", classification
    assert classification["task_result"] == "task_certification_required_waiting_for_multimodel_step", classification
    assert classification["safe_for_next_tick"] is True, classification


def test_autonomy_readiness_reports_complete_fail_closed_architecture():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id, task_path = add_task(env, title="无人值守自运行 ready check work task", priority="P1", project="client-work")
        run(env, "dashboard", "--write", "--json")
        cron_path = Path(env["HERMES_CRON_JOBS_PATH"])
        cron_path.parent.mkdir(parents=True, exist_ok=True)
        cron_path.write_text(json.dumps({"jobs": [
            {"id": "guardian", "name": "task-pool-guardian-10m", "enabled": True, "schedule_display": "every 10m", "last_status": "ok"},
            {"id": "pipeline", "name": "pipeline-tick-hourly", "enabled": True, "schedule_display": "every 60m", "last_status": "ok"},
            {"id": "agent-team", "name": "agent-team-cycle-hourly", "enabled": True, "schedule_display": "every 60m", "last_status": "ok"},
            {"id": "envelope", "name": "envelope-executor-cycle", "enabled": True, "schedule_display": "every 60m", "last_status": "ok"},
            {"id": "multimodel", "name": "multimodel-intervention-step", "enabled": True, "schedule_display": "every 60m", "last_status": "ok"},
            {"id": "auto-completer", "name": "local-brain-taskpool-auto-completer", "enabled": True, "schedule_display": "every 120m", "last_status": "ok"},
        ]}, ensure_ascii=False), encoding="utf-8")

        readiness = json.loads(run(env, "autonomy-readiness", "--json").stdout)
        assert readiness["schema"] == "local_brain_unattended_autonomy_readiness_v1", readiness
        assert readiness["status"] == "PASS", readiness
        assert readiness["architecture_complete"] is True, readiness
        assert readiness["read_only"] is True, readiness
        assert readiness["unattended_runtime_enabled"] is False, readiness
        assert readiness["full_runtime_activation_ready"] is False, readiness
        assert "autorun_env_disabled" in readiness["activation_blockers"], readiness
        assert "multimodel_autorun_env_disabled" in readiness["activation_blockers"], readiness
        assert "autorun_allowlist_empty" in readiness["activation_blockers"], readiness
        assert readiness["eligibility_probe"]["task_id"] == task_id, readiness
        assert readiness["ratification_verifier_selftest"]["status"] == "PASS", readiness
        assert readiness["ratification_verifier_selftest"]["hollow_gate"]["status"] == "FAIL", readiness
        assert "truth_gate_missing_positive_status" in readiness["ratification_verifier_selftest"]["hollow_gate"]["failures"], readiness
        layer_names = set(readiness["control_plane_layers"].keys())
        assert {"scheduler", "guardian", "worker_bridge", "proof_gate", "multi_model_ratifier", "reporter"} <= layer_names, readiness
        assert "status: pending" in task_path.read_text(encoding="utf-8")


def test_autorun_runner_pauses_on_pending_permission_gate():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id, task_path = add_task(env, title="Mission runner asks human", priority="P1", project="mission-runner")
        add_mission_node_fields(task_path, mission_id="mission-runner", node_id="ask-human", gates=["ask-human:pending"])
        env["HERMES_LOCAL_BRAIN_AUTORUN"] = "1"
        state_dir = Path(env["HERMES_BRAIN_AUTORUN_STATE_DIR"])
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "auto_run_allowlist.json").write_text(json.dumps([task_id], ensure_ascii=False), encoding="utf-8")
        Path(env["HERMES_AUTONOMY_WRITE_ALLOWLIST"]).write_text(json.dumps(["taskpool"], ensure_ascii=False), encoding="utf-8")

        eligibility = json.loads(run(env, "eligibility-check", "--task", task_id, "--json").stdout)
        assert eligibility["eligible"] is False, eligibility
        assert "permission_gate_pending" in eligibility["reasons"], eligibility

        runner = json.loads(run(env, "autorun-runner", "--task", task_id, "--actor", "hermes-autorun", "--json").stdout)
        assert runner["status"] == "PASS", runner
        assert runner["runner_status"] == "paused_permission_gate", runner
        assert runner["claimed"] is False, runner
        assert "status: pending" in task_path.read_text(encoding="utf-8")


def test_autorun_eligibility_and_handoff_are_fail_closed():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id, task_path = add_task(env, title="验证 autorun 默认关闭与 allowlist")
        run(env, "dashboard", "--write", "--json")

        disabled = json.loads(run(env, "eligibility-check", "--json").stdout)
        assert disabled["status"] == "PASS", disabled
        assert disabled["eligible"] is False
        assert "autorun_disabled" in disabled["reasons"]
        assert "allowlist_empty" in disabled["reasons"]
        assert disabled["task_id"] == task_id

        no_claim = json.loads(run(env, "auto-claim-and-handoff", "--json").stdout)
        assert no_claim["status"] == "PASS", no_claim
        assert no_claim["claimed"] is False
        assert "autorun_disabled" in no_claim["reasons"]
        note = task_path.read_text(encoding="utf-8")
        assert "status: pending" in note
        assert "claimed_by: " in note

        env["HERMES_LOCAL_BRAIN_AUTORUN"] = "1"
        state_dir = Path(env["HERMES_BRAIN_AUTORUN_STATE_DIR"])
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "auto_run_allowlist.json").write_text(json.dumps([task_id], ensure_ascii=False), encoding="utf-8")

        eligible = json.loads(run(env, "eligibility-check", "--json").stdout)
        assert eligible["status"] == "PASS", eligible
        assert eligible["eligible"] is True
        assert eligible["allowlist_hit"] is True
        assert eligible["mode"] == "allow"

        guard_blocked = json.loads(run(env, "auto-claim-and-handoff", "--actor", "hermes-autorun", "--ttl-minutes", "15", "--json", check=False).stdout)
        assert guard_blocked["status"] == "FAIL_CLOSED", guard_blocked
        assert guard_blocked["claimed"] is False
        assert "autonomy_write_guard_failed" in guard_blocked["reasons"]
        assert "surface_allowlisted" in guard_blocked["write_guard"]["failed_required_checks"]
        assert "status: pending" in task_path.read_text(encoding="utf-8")

        Path(env["HERMES_AUTONOMY_WRITE_ALLOWLIST"]).write_text(json.dumps(["taskpool"], ensure_ascii=False), encoding="utf-8")
        handoff = json.loads(run(env, "auto-claim-and-handoff", "--actor", "hermes-autorun", "--ttl-minutes", "15", "--json").stdout)
        assert handoff["status"] == "OK", handoff
        assert handoff["claimed"] is True
        assert handoff["task"] == task_id
        assert handoff["safety"] == "claimed-and-handoff-only; does not execute task body or mark done"
        assert Path(handoff["handoff"]).exists()
        assert handoff["proof_hash"].startswith("sha256:")
        handoff_text = Path(handoff["handoff"]).read_text(encoding="utf-8")
        assert "Do not execute Markdown task body as a script" in handoff_text
        assert f"proof:{handoff['proof_hash']}" in handoff_text
        proof_lines = (state_dir / "auto_run_proof.jsonl").read_text(encoding="utf-8").strip().splitlines()
        assert len(proof_lines) == 1
        proof_event = json.loads(proof_lines[0])
        assert proof_event["event"] == "handoff_created"
        assert proof_event["event_hash"] == handoff["proof_hash"]

        rows = json.loads(run(env, "list", "--json").stdout)["rows"]
        row = next(r for r in rows if r["id"] == task_id)
        assert row["status"] == "claimed"
        assert row["claimed_by"] == "hermes-autorun"


def test_auto_claim_and_handoff_blocks_hard_execution_flow_boundary_before_claim():
    td, _vault, env = make_env_and_vault()
    with td:
        env["HERMES_LOCAL_BRAIN_AUTORUN"] = "1"
        state_dir = Path(env["HERMES_BRAIN_AUTORUN_STATE_DIR"])
        state_dir.mkdir(parents=True, exist_ok=True)
        task_id, task_path = add_task(env, title="Publish external writeback", priority="P1", project="hermes")
        note = task_path.read_text(encoding="utf-8")
        note = note.replace("status: pending", "status: pending\nworkflow_stage: human_gate", 1)
        task_path.write_text(note, encoding="utf-8")
        (state_dir / "auto_run_allowlist.json").write_text(json.dumps([task_id], ensure_ascii=False), encoding="utf-8")
        Path(env["HERMES_AUTONOMY_WRITE_ALLOWLIST"]).write_text(json.dumps(["taskpool"], ensure_ascii=False), encoding="utf-8")
        before = task_path.read_text(encoding="utf-8")

        result = json.loads(run(env, "auto-claim-and-handoff", "--actor", "hermes-autorun", "--ttl-minutes", "15", "--json", check=False).stdout)

        assert result["status"] == "FAIL_CLOSED"
        assert result["claimed"] is False
        assert result["task_id"] == task_id
        assert "execution_flow_dispatch_blocked" in result["reasons"]
        assert result["execution_flow_dispatch_decision"]["allowed_to_dispatch"] is False
        assert result["execution_flow_dispatch_decision"]["reason"] == "stage_boundary:human_gate"
        assert "handoff" not in result
        handoff_dir = state_dir / "auto_run_handoffs"
        assert not handoff_dir.exists() or not list(handoff_dir.glob("*.md"))
        assert not (state_dir / "auto_run_proof.jsonl").exists()
        assert task_path.read_text(encoding="utf-8") == before



def test_autorun_eligibility_skips_unallowlisted_raw_next_for_allowlisted_fallback():
    td, _vault, env = make_env_and_vault()
    with td:
        env["HERMES_LOCAL_BRAIN_AUTORUN"] = "1"
        env["HERMES_TASKPOOL_EVENT_HOOK_DISABLED"] = "1"
        state_dir = Path(env["HERMES_BRAIN_AUTORUN_STATE_DIR"])
        state_dir.mkdir(parents=True, exist_ok=True)
        Path(env["HERMES_AUTONOMY_WRITE_ALLOWLIST"]).write_text(json.dumps(["taskpool"], ensure_ascii=False), encoding="utf-8")
        raw = run(env, "add", "AAA unallowlisted advisory", "--priority", "P1", "--project", "outside-project", "--lane", "advisory", "--architecture-target", "provider-quota", "--expires-at", "2099-01-01", "--json")
        raw_id = json.loads(raw.stdout)["id"]
        fallback = run(env, "add", "ZZZ allowlisted advisory", "--priority", "P1", "--project", "reading-programming-books", "--lane", "advisory", "--architecture-target", "skill-graph", "--expires-at", "2099-01-01", "--json")
        fallback_id = json.loads(fallback.stdout)["id"]
        (state_dir / "auto_run_allowlist.json").write_text(json.dumps([{
            "project": "reading-programming-books",
            "architecture_target": "skill-graph",
            "lane": "advisory",
            "required_authority": "dispatch-hint",
        }], ensure_ascii=False), encoding="utf-8")
        run(env, "dashboard", "--write", "--json")

        nxt = json.loads(run(env, "next", "--json").stdout)
        assert nxt["next"]["id"] == raw_id, nxt
        eligible = json.loads(run(env, "eligibility-check", "--json").stdout)
        assert eligible["status"] == "PASS", eligible
        assert eligible["eligible"] is True, eligible
        assert eligible["task_id"] == fallback_id, eligible
        assert eligible["raw_task_id"] == raw_id, eligible
        assert eligible["raw_allowlist_hit"] is False, eligible
        assert eligible["allowlist_hit"] is True, eligible
        assert any("raw_next_allowlist_miss" in w for w in eligible["warnings"]), eligible


def test_autorun_allowlist_dict_constraints_are_conjunctive_for_advisory_scope():
    td, _vault, env = make_env_and_vault()
    with td:
        env["HERMES_LOCAL_BRAIN_AUTORUN"] = "1"
        env["HERMES_TASKPOOL_EVENT_HOOK_DISABLED"] = "1"
        state_dir = Path(env["HERMES_BRAIN_AUTORUN_STATE_DIR"])
        state_dir.mkdir(parents=True, exist_ok=True)
        bad = run(env, "add", "Constrained advisory wrong architecture", "--priority", "P1", "--project", "reading-programming-books", "--lane", "advisory", "--architecture-target", "provider-quota", "--expires-at", "2099-01-01", "--json")
        bad_id = json.loads(bad.stdout)["id"]
        (state_dir / "auto_run_allowlist.json").write_text(json.dumps([{
            "project": "reading-programming-books",
            "architecture_target": "skill-graph",
            "lane": "advisory",
        }], ensure_ascii=False), encoding="utf-8")
        run(env, "dashboard", "--write", "--json")

        eligible = json.loads(run(env, "eligibility-check", "--json").stdout)
        assert eligible["task_id"] == bad_id, eligible
        assert eligible["eligible"] is False, eligible
        assert "allowlist_miss" in eligible["reasons"], eligible



def test_non_blocking_auto_subtask_reconcile_actions_do_not_block_next_or_eligibility():
    td, _vault, env = make_env_and_vault()
    with td:
        seed_project_profile(env, aliases=["client-work"])
        parent_id, parent_path = add_task(env, title="Parent blocked by child progress", priority="P1", project="client-work")
        child_id, _child_path = add_task(env, title="Dispatchable child task", priority="P1", project="client-work")
        add_non_blocking_auto_subtask_parent_fields(parent_path, child_id)
        run(env, "dashboard", "--write", "--json")

        nxt = json.loads(run(env, "next", "--json").stdout)
        assert nxt["status"] == "OK", nxt
        assert nxt["next"]["id"] == child_id, nxt
        assert nxt["reconcile"]["action_count"] >= 1, nxt
        assert any(action["action"] == "auto_subtask_progress_synced" and action["task"] == parent_id for action in nxt["reconcile"]["actions"]), nxt

        env["HERMES_LOCAL_BRAIN_AUTORUN"] = "1"
        state_dir = Path(env["HERMES_BRAIN_AUTORUN_STATE_DIR"])
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "auto_run_allowlist.json").write_text(json.dumps([child_id], ensure_ascii=False), encoding="utf-8")

        eligible = json.loads(run(env, "eligibility-check", "--json").stdout)
        assert eligible["status"] == "PASS", eligible
        assert eligible["eligible"] is True, eligible
        assert eligible["task_id"] == child_id, eligible
        assert "reconcile_required" not in eligible["reasons"], eligible


def test_benign_auto_subtask_reconcile_action_without_dispatchable_task_is_not_reconcile_required():
    td, _vault, env = make_env_and_vault()
    with td:
        seed_project_profile(env, aliases=["client-work"])
        parent_id, parent_path = add_task(env, title="Parent waiting on blocked child", priority="P1", project="client-work")
        child_id, child_path = add_task(env, title="Blocked child task", priority="P1", project="client-work")
        add_non_blocking_auto_subtask_parent_fields(parent_path, child_id)
        child_text = child_path.read_text(encoding="utf-8").replace("status: pending", "status: blocked", 1)
        child_path.write_text(child_text, encoding="utf-8")
        run(env, "dashboard", "--write", "--json")

        env["HERMES_LOCAL_BRAIN_AUTORUN"] = "1"
        state_dir = Path(env["HERMES_BRAIN_AUTORUN_STATE_DIR"])
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "auto_run_allowlist.json").write_text(json.dumps([child_id], ensure_ascii=False), encoding="utf-8")

        nxt = json.loads(run(env, "next", "--json").stdout)
        assert nxt["next"] is None, nxt
        assert nxt["message"] == "No dispatchable local-brain tasks in canonical task notes.", nxt
        assert any(action["action"] == "auto_subtask_progress_synced" and action["task"] == parent_id for action in nxt["reconcile"]["actions"]), nxt

        eligible = json.loads(run(env, "eligibility-check", "--json").stdout)
        assert eligible["eligible"] is False, eligible
        assert "no_dispatchable_task" in eligible["reasons"], eligible
        assert "reconcile_required" not in eligible["reasons"], eligible


def test_blocked_resolve_missing_discussion_artifact_is_taxonomy_warning_not_fatal():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id, task_path = add_evolution_task(env, title="Blocked parent missing historical artifact", priority="P1")
        missing_artifact = task_path.parent / "missing-discussion.json"
        text = task_path.read_text(encoding="utf-8")
        text = text.replace("status: pending", "status: blocked", 1)
        text = text.replace(
            "evidence: []",
            f"multimodel_last_discussion_artifact: {missing_artifact}\n"
            "multimodel_last_gate_status: FAIL\n"
            "multimodel_last_decision: CONTINUE_LOOP\n"
            "multimodel_round_status: failed\n"
            "multimodel_status: not_certified\n"
            "multimodel_last_failures:\n"
            "  - loop_non_convergence\n"
            "evidence: []",
            1,
        )
        task_path.write_text(text, encoding="utf-8")

        result = json.loads(run(env, "blocked-resolve-step", "--task", task_id, "--json").stdout)
        assert result["status"] == "OK", result
        assert result["error_count"] == 0, result
        assert result["kept_blocked_count"] == 1, result
        row = result["kept_blocked"][0]
        assert row["action"] == "auto_split_non_convergence", result
        assert row["created_count"] >= 1, result
        assert "framing" in set(row.get("taxonomy_axes") or []), result


def test_auto_split_non_convergence_creates_axis_specific_narrowed_briefs():
    td, _vault, env = make_env_and_vault()
    with td:
        seed_project_profile(env, aliases=["self-improvement"])
        parent_id, parent_path = add_evolution_task(env, title="Parent needs non-convergence narrowing", priority="P1")
        discussion_path = parent_path.parent / "non-convergence-discussion.json"
        discussion_path.write_text(json.dumps({
            "status": "not_certified",
            "issue_ledger": [
                {"id": "I-QUOTA", "status": "unresolved", "summary": "quota observability confidence is unobservable"},
                {"id": "I-RELAY", "status": "unresolved", "summary": "continuation packet ordering remains unresolved"},
                {"id": "I-PATCH", "status": "unresolved", "summary": "minority patch normalization is still open"},
            ],
            "agreement_matrix": {"framing": 0.9, "approach": 0.82, "implementation_order": 0.61},
            "planner_patch_summary": {"certification_intent": "unresolved_noop_vs_change"},
            "merge_info": {"minority_patches": ["threshold gate tweak", "relay packet timing patch"]},
            "final_design": {
                "quota_snapshot": {
                    "openai": {"confidence": 0.1, "observability": "unknown"}
                }
            },
        }, ensure_ascii=False), encoding="utf-8")
        text = parent_path.read_text(encoding="utf-8")
        text = text.replace(
            "evidence: []",
            f"multimodel_last_discussion_artifact: {discussion_path}\nmultimodel_last_failures:\n  - loop_non_convergence\n  - agreement_below_threshold:implementation_order:0.61\n  - final_design_missing\nevidence: []",
            1,
        )
        parent_path.write_text(text, encoding="utf-8")

        result = json.loads(run(env, "auto-split-non-convergence", "--task", parent_id, "--json").stdout)
        assert result["status"] == "OK", result
        assert result["created_count"] >= 4, result
        assert {"quota_observability", "fallback_threshold", "relay_ordering", "patch_normalization"} <= set(result["taxonomy_axes"]) | set(result["all_children"]), result

        created_paths = [Path(item["created"]) for item in result["created"]]
        assert len(created_paths) == result["created_count"], result
        child_axes = set()
        quota_note = None
        for created_path in created_paths:
            note_text = created_path.read_text(encoding="utf-8")
            for line in note_text.splitlines():
                if line.startswith("auto_subtask_axis: "):
                    axis = line.split(":", 1)[1].strip()
                    child_axes.add(axis)
                    if axis == "quota_observability":
                        quota_note = note_text
                    break
        assert {"quota_observability", "fallback_threshold", "relay_ordering", "patch_normalization"} <= child_axes, child_axes
        assert quota_note is not None, child_axes
        assert "## Parent Link" in quota_note
        assert "## Narrowed Scope" in quota_note
        assert f"- Parent task: {parent_id}" in quota_note
        assert str(discussion_path) in quota_note



def test_auto_split_non_convergence_work_children_get_project_source_policy_ref():
    td, _vault, env = make_env_and_vault()
    with td:
        seed_project_profile(env, aliases=["hermes", "hermes-agent"])
        parent_id, parent_path = add_task(env, title="Work parent needs convergence narrowing", priority="P1", project="hermes-agent")
        discussion_path = parent_path.parent / "work-non-convergence-discussion.json"
        discussion_path.write_text(json.dumps({
            "status": "not_certified",
            "issue_ledger": [
                {"id": "I-FALLBACK", "status": "unresolved", "summary": "fallback threshold remains ambiguous"},
            ],
            "planner_patch_summary": {"certification_intent": "unresolved_noop_vs_change"},
        }, ensure_ascii=False), encoding="utf-8")
        text = parent_path.read_text(encoding="utf-8")
        # Exercise the production fallback path: generated work children must bind
        # the project profile source policy even when the parent note predates the
        # source_weighting_policy_ref gate.
        text = re.sub(r"^source_weighting_policy_ref:.*\n", "", text, flags=re.M)
        text = text.replace(
            "evidence: []",
            f"multimodel_last_discussion_artifact: {discussion_path}\nmultimodel_last_failures:\n  - loop_non_convergence\n  - agreement_below_threshold:framing:0.61\nevidence: []",
            1,
        )
        parent_path.write_text(text, encoding="utf-8")

        result = json.loads(run(env, "auto-split-non-convergence", "--task", parent_id, "--json").stdout)
        assert result["status"] == "OK", result
        assert result["created_count"] >= 1, result
        created_paths = [Path(item["created"]) for item in result["created"]]
        for created_path in created_paths:
            note_text = created_path.read_text(encoding="utf-8")
            assert "lane: work" in note_text
            assert "project: hermes-agent" in note_text
            assert "source_weighting_policy_ref:" in note_text
            assert "hermes.json#source_weighting_policy" in note_text


def test_auto_split_non_convergence_dedupes_existing_children_by_axis():
    td, _vault, env = make_env_and_vault()
    with td:
        seed_project_profile(env, aliases=["hermes", "hermes-agent"])
        parent_id, parent_path = add_task(env, title="Work parent with long title needs stable child axis dedupe", priority="P1", project="hermes-agent")
        discussion_path = parent_path.parent / "dedupe-non-convergence-discussion.json"
        discussion_path.write_text(json.dumps({
            "status": "not_certified",
            "issue_ledger": [
                {"id": "I-QUOTA", "status": "unresolved", "summary": "quota confidence is unobservable"},
                {"id": "I-PATCH", "status": "unresolved", "summary": "patch normalization remains ambiguous"},
                {"id": "I-FRAME", "status": "unresolved", "summary": "framing still rejected by reviewers"},
            ],
            "planner_patch_summary": {"certification_intent": "unresolved_noop_vs_change"},
            "merge_info": {"minority_patches": ["patch normalization candidate"]},
        }, ensure_ascii=False), encoding="utf-8")
        existing_ids = []
        for axis in ("quota_observability", "fallback_threshold", "relay_ordering", "patch_normalization", "framing"):
            child_id, child_path = add_task(env, title=f"Historical already closed {axis} child with non expected id", priority="P1", project="hermes-agent")
            child_text = child_path.read_text(encoding="utf-8")
            child_text = child_text.replace("status: pending", "status: done", 1)
            child_text = child_text.replace(
                "evidence: []",
                f"auto_subtask_parent: {parent_id}\nauto_subtask_kind: non_convergence_narrowing\nauto_subtask_axis: {axis}\nevidence:\n  - command: historical child proof PASS",
                1,
            )
            child_path.write_text(child_text, encoding="utf-8")
            existing_ids.append(child_id)
        text = parent_path.read_text(encoding="utf-8")
        text = text.replace(
            "evidence: []",
            f"multimodel_last_discussion_artifact: {discussion_path}\nmultimodel_last_failures:\n  - loop_non_convergence\n  - agreement_below_threshold:framing:0.61\nauto_subtask_children: {json.dumps(existing_ids, ensure_ascii=False)}\nevidence: []",
            1,
        )
        parent_path.write_text(text, encoding="utf-8")

        result = json.loads(run(env, "auto-split-non-convergence", "--task", parent_id, "--json").stdout)
        assert result["status"] == "OK", result
        assert result["created_count"] == 0, result
        assert set(result.get("existing_axes") or []) >= {"quota_observability", "fallback_threshold", "relay_ordering", "patch_normalization", "framing"}


def test_auto_split_non_convergence_backfills_taxonomy_axes_missing_from_existing_children():
    td, _vault, env = make_env_and_vault()
    with td:
        seed_project_profile(env, aliases=["hermes", "hermes-agent"])
        parent_id, parent_path = add_task(env, title="Parent with stale quota child still needs taxonomy axis children", priority="P1", project="hermes-agent")
        discussion_path = parent_path.parent / "taxonomy-axis-backfill-discussion.json"
        discussion_path.write_text(json.dumps({
            "status": "not_certified",
            "claims": [],
            "votes": {"model-a": "reject"},
            "agreement_matrix": {"implementation_order": 0.50},
        }, ensure_ascii=False), encoding="utf-8")
        child_id, child_path = add_task(env, title="Historical quota child with truncated id", priority="P1", project="hermes-agent")
        child_text = child_path.read_text(encoding="utf-8")
        child_text = child_text.replace("status: pending", "status: done", 1)
        child_text = child_text.replace(
            "evidence: []",
            f"auto_subtask_parent: {parent_id}\nauto_subtask_kind: non_convergence_narrowing\nauto_subtask_axis: quota_observability\nevidence:\n  - command: historical quota child proof PASS",
            1,
        )
        child_path.write_text(child_text, encoding="utf-8")
        text = parent_path.read_text(encoding="utf-8")
        text = text.replace(
            "evidence: []",
            f"multimodel_last_discussion_artifact: {discussion_path}\nmultimodel_last_failures:\n  - loop_non_convergence\n  - agreement_below_threshold:framing:0.61\n  - missing_required_model_vote:deepseek-v4-pro\nmultimodel_recommended_axes: [\"fallback_threshold\", \"relay_ordering\", \"framing\"]\nauto_subtask_children: [\"{child_id}\"]\nevidence: []",
            1,
        )
        parent_path.write_text(text, encoding="utf-8")

        result = json.loads(run(env, "auto-split-non-convergence", "--task", parent_id, "--json").stdout)
        assert result["status"] == "OK", result
        assert result["created_count"] >= 2, result
        created_axes = set(result.get("created_axes") or [])
        assert {"relay_ordering", "framing"} <= created_axes
        assert "quota_observability" in result.get("existing_axes", []), result



def test_auto_subtask_sync_reopens_loop_non_convergence_parent_and_backfills_child_evidence():
    td, _vault, env = make_env_and_vault()
    with td:
        seed_project_profile(env, aliases=["self-improvement"])
        parent_id, parent_path = add_evolution_task(env, title="Blocked parent waiting for child backfill", priority="P1")
        child_id, child_path = add_evolution_task(env, title="Finished narrowed brief child", priority="P1")
        mark_task_done_directly(child_path)
        child_text = child_path.read_text(encoding="utf-8")
        child_text = child_text.replace("evidence:\n  - command: fixture done PASS", "auto_subtask_axis: relay_ordering\nmultimodel_status: certified\nmultimodel_last_gate_status: PASS\nevidence:\n  - command: fixture done PASS", 1)
        child_path.write_text(child_text, encoding="utf-8")

        parent_text = parent_path.read_text(encoding="utf-8")
        parent_text = parent_text.replace("status: pending", "status: blocked", 1)
        parent_text = parent_text.replace("retry_count: 0", "retry_count: 2", 1)
        parent_text = parent_text.replace(
            "evidence: []",
            f"multimodel_last_failures:\n  - loop_non_convergence\n  - agreement_below_threshold:implementation_order:0.62\nauto_subtask_kind: non_convergence_narrowing\nauto_subtask_children: [\"{child_id}\"]\nauto_subtask_open_children: []\nauto_subtask_missing_children: []\nauto_subtask_ready_for_parent: false\nevidence: []",
            1,
        )
        parent_path.write_text(parent_text, encoding="utf-8")

        sync = json.loads(run(env, "auto-subtask-sync", "--task", parent_id, "--write", "--json").stdout)
        assert sync["status"] == "OK", sync
        assert any(action["action"] == "auto_subtask_parent_reopened" and action["task"] == parent_id for action in sync["actions"]), sync

        parent_note = parent_path.read_text(encoding="utf-8")
        assert "status: pending" in parent_note, parent_note
        assert "## Auto-subtask Backfill" in parent_note, parent_note
        assert child_id in parent_note, parent_note
        assert str(child_path) in parent_note, parent_note
        assert "All auto-generated convergence subtasks reached done; parent reopened to `pending` for ratification rerun." in parent_note, parent_note
        assert f"proof:child-task:{child_id}:status:done" in parent_note, parent_note
        assert f"proof:child-axis:relay_ordering:{child_id}" in parent_note, parent_note
        assert f"  - child-task:{child_id}:status:done" not in parent_note, parent_note
        assert f"  - child-axis:relay_ordering:{child_id}" not in parent_note, parent_note



def test_blocked_resolve_reports_parent_aggregation_when_children_done_but_certification_still_required():
    td, _vault, env = make_env_and_vault()
    with td:
        seed_project_profile(env, aliases=["self-improvement"])
        parent_id, parent_path = add_evolution_task(env, title="Blocked parent has finished children but needs cert", priority="P1")
        child_id, child_path = add_evolution_task(env, title="Finished child with evidence", priority="P1")
        mark_task_done_directly(child_path)
        child_text = child_path.read_text(encoding="utf-8")
        child_text = child_text.replace("evidence:\n  - command: fixture done PASS", "auto_subtask_parent: " + parent_id + "\nauto_subtask_axis: framing\nevidence:\n  - command: fixture done PASS", 1)
        child_path.write_text(child_text, encoding="utf-8")

        parent_text = parent_path.read_text(encoding="utf-8")
        parent_text = parent_text.replace("status: pending", "status: blocked", 1)
        parent_text = parent_text.replace(
            "evidence: []",
            "requires_multimodel: true\n"
            "multimodel_status: not_certified\n"
            "multimodel_last_gate_status: FAIL\n"
            "multimodel_last_decision: CONTINUE_LOOP\n"
            "multimodel_last_failures:\n"
            "  - loop_non_convergence\n"
            "  - missing_required_model_vote:mimo-v2.5-pro\n"
            f"auto_subtask_kind: non_convergence_narrowing\n"
            f"auto_subtask_children: [\"{child_id}\"]\n"
            "auto_subtask_open_children: []\n"
            "auto_subtask_missing_children: []\n"
            "auto_subtask_ready_for_parent: true\n"
            "evidence:\n"
            f"  - proof:child-task:{child_id}:status:pending\n"
            f"  - proof:child-task:{child_id}:status:done",
            1,
        )
        parent_path.write_text(parent_text, encoding="utf-8")

        result = json.loads(run(env, "blocked-resolve-step", "--task", parent_id, "--json").stdout)
        assert result["status"] == "OK", result
        assert result["resolved_count"] == 1, result
        row = result["resolved"][0]
        assert row["action"] == "auto_subtask_parent_reopened_for_certification_refresh", result
        assert row["to_status"] == "pending", result
        aggregation = row["parent_aggregation"]
        assert aggregation["ready_for_parent"] is True, aggregation
        assert aggregation["action"] == "keep_blocked_certification_required", aggregation
        assert aggregation["done_count"] == aggregation["child_count"] == 1, aggregation
        assert aggregation["axis_summary"] == {"framing": "done"}, aggregation
        assert aggregation["stale_evidence_count"] == 1, aggregation
        assert aggregation["suggested_next"] == "parent_ratification_refresh", aggregation


def test_loop_non_convergence_parent_uses_targeted_evidence_refresh_plan_after_children_finish():
    td, _vault, env = make_env_and_vault()
    with td:
        seed_project_profile(env, aliases=["self-improvement"])
        parent_id, parent_path = add_evolution_task(env, title="Looping parent should reratify with targeted evidence", priority="P1")
        child_id, child_path = add_evolution_task(env, title="Done child evidence for targeted reratification", priority="P1")
        mark_task_done_directly(child_path)
        child_text = child_path.read_text(encoding="utf-8")
        child_text = child_text.replace("evidence:\n  - command: fixture done PASS", "auto_subtask_axis: fallback_threshold\nmultimodel_status: certified\nmultimodel_last_gate_status: PASS\nmultimodel_ratification_artifact: /tmp/child-discussion.json\nevidence:\n  - command: fixture done PASS", 1)
        child_path.write_text(child_text, encoding="utf-8")

        parent_text = parent_path.read_text(encoding="utf-8")
        parent_text = parent_text.replace("status: pending", "status: blocked", 1)
        parent_text = parent_text.replace("retry_count: 0", "retry_count: 2", 1)
        parent_text = parent_text.replace(
            "evidence: []",
            f"multimodel_last_failures:\n  - loop_non_convergence\n  - agreement_below_threshold:implementation_order:0.62\nauto_subtask_kind: non_convergence_narrowing\nauto_subtask_children: [\"{child_id}\"]\nauto_subtask_open_children: []\nauto_subtask_missing_children: []\nauto_subtask_ready_for_parent: true\nmultimodel_recommended_axes: [fallback_threshold]\nevidence: []",
            1,
        )
        parent_path.write_text(parent_text, encoding="utf-8")

        dry = json.loads(run(env, "multimodel-intervention-dry-run", "--task", parent_id, "--json").stdout)
        assert dry["status"] == "OK", dry
        assert dry["intervention_required"] is True, dry
        selected = dry["selected"]
        assert selected["refresh_mode"] == "blocked_parent_targeted_evidence", selected
        assert selected["pua_loop"]["mode"] == "blocked_parent_targeted_evidence_refresh", selected
        assert selected["recommended_tier"] == "T3_certification", selected
        assert "Frozen parent objective is preserved" in selected["build_state_command"], selected
        assert str(parent_path) in selected["build_state_command"], selected
        assert str(child_path) in selected["build_state_command"], selected
        assert "fallback_threshold" in json.dumps(selected["criteria"], ensure_ascii=False) or "fallback_threshold" in selected["build_state_command"], selected


def test_blocked_resolve_step_keeps_paused_parent_blocked_after_child_backfill():
    td, _vault, env = make_env_and_vault()
    with td:
        seed_project_profile(env, aliases=["self-improvement"])
        parent_id, parent_path = add_evolution_task(env, title="Paused parent should stay blocked after child backfill", priority="P1")
        child_id, child_path = add_evolution_task(env, title="Done child evidence for paused parent", priority="P1")
        mark_task_done_directly(child_path)
        child_text = child_path.read_text(encoding="utf-8")
        child_text = child_text.replace(
            "evidence:\n  - command: fixture done PASS",
            "auto_subtask_axis: framing\nmultimodel_status: certified\nmultimodel_last_gate_status: PASS\nmultimodel_ratification_artifact: /tmp/child-discussion.json\nevidence:\n  - command: fixture done PASS",
            1,
        )
        child_path.write_text(child_text, encoding="utf-8")

        parent_text = parent_path.read_text(encoding="utf-8")
        parent_text = parent_text.replace("status: pending", "status: blocked", 1)
        parent_text = parent_text.replace("retry_count: 0", "retry_count: 6", 1)
        parent_text = parent_text.replace(
            "evidence: []",
            f"multimodel_round_status: failed\nmultimodel_last_decision: CONTINUE_LOOP\nmultimodel_last_failures:\n  - loop_non_convergence\n  - vote_reject\nauto_subtask_kind: non_convergence_narrowing\nauto_subtask_children: [\"{child_id}\"]\nauto_subtask_open_children: []\nauto_subtask_missing_children: []\nauto_subtask_ready_for_parent: true\nblocked_resolve_reason: task has 6 failed T3 rounds (max=5); requires human review or targeted evidence fix\nevidence: []",
            1,
        )
        parent_path.write_text(parent_text, encoding="utf-8")

        result = json.loads(run(env, "blocked-resolve-step", "--task", parent_id, "--json").stdout)
        assert result["status"] == "OK", result
        assert result["resolved_count"] == 0, result
        assert result["kept_blocked_count"] == 1, result
        row = result["kept_blocked"][0]
        assert row["action"] == "auto_subtask_parent_backfilled_paused", result
        assert "requires human review or targeted evidence fix" in row["reason"], result

        parent_after = parent_path.read_text(encoding="utf-8")
        assert "status: blocked" in parent_after, parent_after
        assert "blocked_resolve_last_action: auto_subtask_parent_backfilled_paused" in parent_after, parent_after
        assert "blocker_status: flow_paused_targeted_evidence_review" in parent_after, parent_after


def test_autorun_kill_switches_and_evolution_preemption_gate():
    td, _vault, env = make_env_and_vault()
    with td:
        work_id, _ = add_task(env, title="客户 work 任务必须优先", priority="P1", project="client-work")
        evolution_id, _ = add_evolution_task(env, priority="P0")
        state_dir = Path(env["HERMES_BRAIN_AUTORUN_STATE_DIR"])
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "auto_run_allowlist.json").write_text(json.dumps([work_id, evolution_id], ensure_ascii=False), encoding="utf-8")
        env["HERMES_LOCAL_BRAIN_AUTORUN"] = "1"

        env["HERMES_LOCAL_BRAIN_AUTORUN_KILL"] = "1"
        env_killed = json.loads(run(env, "eligibility-check", "--task", work_id, "--json").stdout)
        assert env_killed["eligible"] is False, env_killed
        assert "kill_switch_env_set" in env_killed["reasons"], env_killed
        env.pop("HERMES_LOCAL_BRAIN_AUTORUN_KILL")

        (state_dir / "auto_run_kill_switch").write_text("maintenance\n", encoding="utf-8")
        file_killed = json.loads(run(env, "eligibility-check", "--task", work_id, "--json").stdout)
        assert file_killed["eligible"] is False, file_killed
        assert "kill_switch_file_present" in file_killed["reasons"], file_killed
        (state_dir / "auto_run_kill_switch").unlink()

        blocked_evolution = json.loads(run(env, "eligibility-check", "--task", evolution_id, "--json").stdout)
        assert blocked_evolution["eligible"] is False, blocked_evolution
        assert "work_lane_available" in blocked_evolution["reasons"], blocked_evolution
        rows = json.loads(run(env, "list", "--json").stdout)["rows"]
        assert next(r for r in rows if r["id"] == work_id)["status"] == "pending"
        assert next(r for r in rows if r["id"] == evolution_id)["status"] == "pending"


def test_boundary_check_and_parallel_dispatch_dry_run_are_fail_closed():
    td, _vault, env = make_env_and_vault()
    with td:
        first_id, first_path = add_task(env, title="并行任务 A", priority="P1", project="client-a")
        second_id, second_path = add_task(env, title="并行任务 B 同 workspace", priority="P1", project="client-b")
        third_id, third_path = add_task(env, title="并行任务 C", priority="P2", project="client-c")
        evolution_id, evolution_path = add_evolution_task(env, priority="P0")
        for p in (first_path, second_path):
            text = p.read_text(encoding="utf-8")
            text = text.replace("workspace: ", "workspace: /tmp/shared-client-workspace", 1)
            p.write_text(text, encoding="utf-8")
        third_text = third_path.read_text(encoding="utf-8").replace("workspace: ", "workspace: /tmp/independent-client-workspace", 1)
        third_path.write_text(third_text, encoding="utf-8")
        run(env, "dashboard", "--write", "--json")

        boundary = json.loads(run(env, "boundary-check", "--json").stdout)
        assert boundary["status"] == "PASS", boundary
        assert boundary["schema"] == "local_brain_task_boundary_v1"
        assert boundary["dispatchable_by_lane"]["work"] == 3, boundary
        assert boundary["dispatchable_by_lane"]["evolution"] == 1, boundary
        assert boundary["gates"]["work_lane_available"] is True, boundary

        dry = json.loads(run(env, "parallel-dispatch-dry-run", "--max-agents", "3", "--json").stdout)
        assert dry["status"] == "OK", dry
        assert dry["dry_run"] is True
        assert dry["selected_count"] == 2, dry
        selected_ids = [row["id"] for row in dry["selected"]]
        assert first_id in selected_ids
        assert third_id in selected_ids
        assert second_id not in selected_ids
        assert evolution_id not in selected_ids
        assert all(row["lane"] == "work" for row in dry["selected"])
        assert any(s["id"] == second_id and s["reason"] == "parallel_boundary_conflict" for s in dry["skipped"]), dry
        assert any(s["id"] == evolution_id and s["reason"] == "lane_preempted_by_work" for s in dry["skipped"]), dry
        assert all("claim_command" in item and "execution_prompt" in item for item in dry["dispatch_plan"]), dry
        rows = json.loads(run(env, "list", "--json").stdout)["rows"]
        assert next(r for r in rows if r["id"] == first_id)["status"] == "pending"
        assert next(r for r in rows if r["id"] == second_id)["status"] == "pending"
        assert next(r for r in rows if r["id"] == third_id)["status"] == "pending"
        assert next(r for r in rows if r["id"] == evolution_id)["status"] == "pending"

        first_text = first_path.read_text(encoding="utf-8")
        first_text = first_text.replace(
            "workspace: /tmp/shared-client-workspace",
            "workspace: /tmp/shared-client-workspace\nallowed_globs: [\"src/**\"]\nforbidden_globs: [\"secrets/**\"]\nloc_budget: 5",
            1,
        )
        first_path.write_text(first_text, encoding="utf-8")
        bd_ok = json.loads(run(env, "boundary-diff-check", first_id, "--file", "src/app.py", "--diff-lines", "5", "--json").stdout)
        assert bd_ok["status"] == "OK", bd_ok
        bd_forbidden = json.loads(run(env, "boundary-diff-check", first_id, "--file", "secrets/key.txt", "--json", check=False).stdout)
        assert bd_forbidden["status"] == "FAIL", bd_forbidden
        assert any("forbidden_match" in v for v in bd_forbidden["boundary_diff"]["violations"]), bd_forbidden
        bd_over_budget = json.loads(run(env, "boundary-diff-check", first_id, "--file", "src/app.py", "--diff-lines", "6", "--json", check=False).stdout)
        assert bd_over_budget["status"] == "FAIL", bd_over_budget
        assert bd_over_budget["loc_budget"]["over_budget"] == 1, bd_over_budget
        bd_negative = json.loads(run(env, "boundary-diff-check", first_id, "--file", "src/app.py", "--diff-lines", "-1", "--json", check=False).stdout)
        assert bd_negative["status"] == "FAIL", bd_negative
        assert bd_negative["loc_budget"]["reason"] == "invalid_diff_line_count", bd_negative
        first_path.write_text(first_path.read_text(encoding="utf-8").replace("loc_budget: 5", "loc_budget: many", 1), encoding="utf-8")
        bd_bad_budget = json.loads(run(env, "boundary-diff-check", first_id, "--file", "src/app.py", "--diff-lines", "1", "--json", check=False).stdout)
        assert bd_bad_budget["status"] == "FAIL", bd_bad_budget
        assert "invalid_loc_budget:many" in bd_bad_budget["boundary_diff"]["violations"], bd_bad_budget

        bad_text = evolution_path.read_text(encoding="utf-8").replace("capability_delta: bounded autorun safety", "capability_delta: ", 1)
        evolution_path.write_text(bad_text, encoding="utf-8")
        bad_boundary = json.loads(run(env, "boundary-check", "--json", check=False).stdout)
        assert bad_boundary["status"] == "FAIL", bad_boundary
        assert any(i.get("reason") == "evolution_architecture_alignment_missing" for i in bad_boundary["invalid"]), bad_boundary


def test_autorun_done_requires_valid_proof_hash():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id, _task_path = add_task(env, title="验证 autorun done proof gate")
        run(env, "dashboard", "--write", "--json")
        env["HERMES_LOCAL_BRAIN_AUTORUN"] = "1"
        state_dir = Path(env["HERMES_BRAIN_AUTORUN_STATE_DIR"])
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "auto_run_allowlist.json").write_text(json.dumps([task_id], ensure_ascii=False), encoding="utf-8")
        Path(env["HERMES_AUTONOMY_WRITE_ALLOWLIST"]).write_text(json.dumps(["taskpool"], ensure_ascii=False), encoding="utf-8")
        handoff = json.loads(run(env, "auto-claim-and-handoff", "--actor", "hermes-autorun", "--json").stdout)
        proof_hash = handoff["proof_hash"]

        run(env, "transition", task_id, "--to", "running", "--actor", "hermes-autorun", "--json")
        run(env, "transition", task_id, "--to", "review", "--actor", "hermes-autorun", "--evidence", "command: bounded runner PASS", "--json")

        missing_proof = run(env, "done", task_id, "--actor", "hermes-autorun", "--evidence", "command: final PASS", "--json", check=False)
        assert missing_proof.returncode != 0
        assert "autorun closure requires proof:<sha256:" in missing_proof.stderr

        bad_proof = run(env, "done", task_id, "--actor", "hermes-autorun", "--evidence", "proof:sha256:deadbeef", "--json", check=False)
        assert bad_proof.returncode != 0
        assert "autorun proof hash not found or chain verification failed" in bad_proof.stderr

        done = json.loads(run(env, "done", task_id, "--actor", "hermes-autorun", "--evidence", f"proof:{proof_hash}", "--evidence", "command: final PASS test build browser curl commit verification", "--json").stdout)
        assert done["status"] == "OK", done
        proof_check = json.loads(run(env, "proof-check", "--json").stdout)
        assert proof_check["status"] == "PASS", proof_check


def test_proof_check_flags_persisted_autorun_done_without_proof_hash():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id, task_path = add_task(env, title="验证 persisted autorun done proof audit")
        text = task_path.read_text(encoding="utf-8")
        text = text.replace("status: pending", "status: done", 1)
        text = text.replace("evidence: []", "evidence:\n  - command: persisted autorun closure", 1)
        text += "\n- 2099-01-01T00:00:00+08:00: Lifecycle transition `review` -> `done` by `hermes-autorun`. Evidence: command: persisted autorun closure\n"
        task_path.write_text(text, encoding="utf-8")
        proof = json.loads(run(env, "proof-check", "--json", check=False).stdout)
        assert proof["status"] == "FAIL", proof
        assert any("autorun done task missing proof evidence" in f for f in proof["failures"]), proof


def test_proof_check_include_active_does_not_fail_historical_autorun_hashes():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id, task_path = add_task(env, title="验证 active proof hash 历史证据不阻断")
        text = task_path.read_text(encoding="utf-8")
        text = text.replace("status: pending", "status: review", 1)
        text = text.replace("evidence: []", "evidence:\n  - proof:sha256:deadbeef", 1)
        text += "\n## Proof Log\n- historical active handoff proof hash retained for traceability.\n\n## Final Handoff\n- active review, not autorun done closeout.\n"
        task_path.write_text(text, encoding="utf-8")
        proof = json.loads(run(env, "proof-check", "--include-active", "--json").stdout)
        assert proof["status"] == "PASS", proof


def test_proof_check_does_not_warn_for_non_autorun_done_hash_artifact_labels():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id, task_path = add_task(env, title="验证 non-autorun labeled proof hash artifact")
        text = task_path.read_text(encoding="utf-8")
        text = text.replace("status: pending", "status: done", 1)
        text = text.replace(
            "evidence: []",
            "evidence:\n  - proof:sha256:artifact_bundle=deadbeef\n  - command: deterministic closeout PASS",
            1,
        )
        text += "\n## Proof Log\n- non-autorun deterministic artifact bundle hash retained.\n\n## Final Handoff\n- closed by bounded non-autorun worker.\n"
        task_path.write_text(text, encoding="utf-8")
        proof = json.loads(run(env, "proof-check", "--json").stdout)
        assert proof["status"] == "PASS", proof
        assert not any("terminal invalid autorun proof hash debt" in w for w in proof["warnings"]), proof


def test_multimodel_step_marks_task_running_while_external_process_is_inflight_then_review():
    td, _vault, env = make_env_and_vault()
    with td:
        old_env = os.environ.copy()
        original_subprocess_run = None
        mod = None
        try:
            os.environ.update(env)
            os.environ["HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL"] = "1"
            state_dir = Path(env["HERMES_BRAIN_AUTORUN_STATE_DIR"])
            state_dir.mkdir(parents=True, exist_ok=True)
            (state_dir / "multimodel_intervention_allowlist.json").write_text(json.dumps(["project:taskpool"], ensure_ascii=False), encoding="utf-8")
            mod = load_orchestrator_module()
            created = mod.create_task_note(
                title="多模型执行中应映射 taskpool running",
                priority="P0",
                project="self-improvement",
                lane="evolution",
                concepts=["task"],
                expires_days=30,
                expires_at="2099-01-01",
                workflow_contract="[[08-模板/task-workflow-contract-template]]",
                priority_layer="P2",
                dependency_order=["1"],
                multimodel_triage_result="P2",
                architecture_target="taskpool",
                capability_delta="external multimodel inflight state is visible",
                anti_drift_check="dashboard running must reflect external process",
                acceptance_evidence="task status is running while subprocess executes",
            )
            task_path = Path(created["created"])
            task_id = created["id"]
            task = mod.find_task(task_id)
            discussion_path = Path(td.name) / "discussion_result.json"
            state_path = Path(td.name) / "state.json"
            discussion_path.write_text(json.dumps({"status": "certified", "task_id": task_id}, ensure_ascii=False), encoding="utf-8")
            state_path.write_text("{}", encoding="utf-8")

            def fake_dry_run(_args):
                return {
                    "intervention_required": True,
                    "selected": {
                        "task": {"id": task_id, "project": "self-improvement", "title": task.title},
                        "build_state_command": "fake-build-state",
                        "run_discussion_command": "fake-run-discussion",
                        "state_path": str(state_path),
                        "recommended_tier": "T3_certification",
                        "advisory_only": False,
                    },
                }

            class FakeProc:
                def __init__(self, stdout=""):
                    self.returncode = 0
                    self.stdout = stdout
                    self.stderr = ""

            observed_statuses = []

            def fake_run(cmd, **_kwargs):
                current = mod.find_task(task_id)
                observed_statuses.append(current.status)
                if cmd == "fake-run-discussion":
                    return FakeProc(json.dumps({"result_file": str(discussion_path)}, ensure_ascii=False))
                return FakeProc()

            setattr(mod, "command_multimodel_intervention_dry_run", fake_dry_run)
            setattr(mod, "ratification_gate_result", lambda _discussion, expected_task=None: {"status": "PASS", "decision": "LOOP_DONE", "failures": []})
            original_subprocess_run = mod.subprocess.run
            mod.subprocess.run = fake_run

            result = mod.command_multimodel_intervention_step(type("Args", (), {"task": task_id, "json": True})())
            assert result["status"] == "OK", result
            assert observed_statuses == ["running", "running"], observed_statuses
            final_task = mod.find_task(task_id)
            assert final_task.status == "review", final_task.fm
            assert not final_task.fm.get("claimed_by"), final_task.fm
            assert any(str(e).startswith("command: multimodel-intervention-step") for e in final_task.fm.get("evidence", [])), final_task.fm
        finally:
            if original_subprocess_run is not None and mod is not None:
                mod.subprocess.run = original_subprocess_run
            os.environ.clear()
            os.environ.update(old_env)


def test_multimodel_step_background_spawns_durable_job_without_waiting_for_models():
    td, _vault, env = make_env_and_vault()
    with td:
        old_env = os.environ.copy()
        original_subprocess_run = None
        original_subprocess_popen = None
        mod = None
        try:
            os.environ.clear()
            os.environ.update(env)
            os.environ["HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL"] = "1"
            mod = load_orchestrator_module()
            setattr(mod, "MULTIMODEL_ASYNC_JOB_DIR", Path(td.name) / "jobs")
            setattr(mod, "MULTIMODEL_ASYNC_LOG_DIR", Path(td.name) / "logs")
            created = mod.create_task_note(
                title="后台多模型 fanout 不阻塞 tick",
                priority="P0",
                project="self-improvement",
                lane="evolution",
                concepts=["task"],
                expires_days=30,
                expires_at="2099-01-01",
                workflow_contract="[[08-模板/task-workflow-contract-template]]",
                priority_layer="P1",
                dependency_order=["1"],
                multimodel_triage_result="P1",
                architecture_target="taskpool",
                capability_delta="background multimodel receipt exists",
                anti_drift_check="parent command must not synchronously wait for consult_models fanout",
                acceptance_evidence="async job json written and task marked running",
            )
            task = mod.find_task(created["id"])
            plan = {
                "task": task.row(),
                "build_state_command": "fake-build-state",
                "run_discussion_command": "fake-run-discussion-that-would-be-long",
                "state_path": str(Path(td.name) / "state.json"),
                "recommended_tier": "T3_certification",
                "advisory_only": False,
                "intervention_required": True,
            }
            setattr(
                mod,
                "command_multimodel_intervention_dry_run",
                lambda _args: {"intervention_required": True, "selected": plan, "convergence": {"total_active": 1}},
            )

            class FakePopen:
                def __init__(self, cmd, **kwargs):
                    self.pid = 424242
                    self.cmd = cmd
                    self.kwargs = kwargs

            calls = {"popen": 0, "run": 0}
            def fake_popen(cmd, **kwargs):
                calls["popen"] += 1
                return FakePopen(cmd, **kwargs)
            def fake_run(*_args, **_kwargs):
                calls["run"] += 1
                raise AssertionError("background start must not run consult_models synchronously")
            original_subprocess_popen = mod.subprocess.Popen
            original_subprocess_run = mod.subprocess.run
            mod.subprocess.Popen = fake_popen
            mod.subprocess.run = fake_run

            result = mod.command_multimodel_intervention_step(type("Args", (), {"task": task.id, "background": True, "json": True})())
            assert result["status"] == "OK", result
            assert result["action"] == "background_start", result
            assert result["async_job"]["action"] == "spawned", result
            assert calls == {"popen": 1, "run": 0}, calls
            assert list(mod.MULTIMODEL_ASYNC_JOB_DIR.glob("*.json")), result
            assert mod.find_task(task.id).status == "running"
        finally:
            if original_subprocess_popen is not None and mod is not None:
                mod.subprocess.Popen = original_subprocess_popen
            if original_subprocess_run is not None and mod is not None:
                mod.subprocess.run = original_subprocess_run
            os.environ.clear()
            os.environ.update(old_env)


def test_multimodel_parallel_allowlist_matches_architecture_target_local_brain():
    td, _vault, env = make_env_and_vault()
    with td:
        old_env = os.environ.copy()
        try:
            os.environ.clear()
            os.environ.update(env)
            os.environ["HERMES_LOCAL_BRAIN_AUTORUN_MULTIMODEL"] = "1"
            state_dir = Path(env["HERMES_BRAIN_AUTORUN_STATE_DIR"])
            state_dir.mkdir(parents=True, exist_ok=True)
            (state_dir / "multimodel_intervention_allowlist.json").write_text(
                json.dumps(["project:local-brain"], ensure_ascii=False),
                encoding="utf-8",
            )
            mod = load_orchestrator_module()
            created = mod.create_task_note(
                title="Rokid local-brain parallel multimodel allowlist regression",
                priority="P1",
                project="hermes",
                lane="evolution",
                concepts=["rokid"],
                expires_days=30,
                expires_at="2099-01-01",
                workflow_contract="[[08-模板/task-workflow-contract-template]]",
                priority_layer="P1",
                dependency_order=["1"],
                multimodel_triage_result="P1",
                architecture_target="local-brain",
                capability_delta="parallel multimodel worker accepts architecture-target allowlist",
                anti_drift_check="project:local-brain allowlist must match project=hermes architecture_target=local-brain",
                acceptance_evidence="parallel step processes one selected task instead of no_eligible_tasks",
            )
            task = mod.find_task(created["id"])
            plan = {
                "task": task.row(),
                "build_state_command": "fake-build-state",
                "run_discussion_command": "fake-run-discussion",
                "state_path": str(Path(td.name) / "state.json"),
                "recommended_tier": "T3_certification",
                "advisory_only": False,
                "intervention_required": True,
            }
            setattr(
                mod,
                "command_multimodel_intervention_dry_run",
                lambda _args: {
                    "intervention_required": True,
                    "plans": [plan],
                    "convergence": {"total_active": 1},
                },
            )
            setattr(
                mod,
                "_run_single_task_pipeline",
                lambda selected_plan, allowlist_active: {
                    "task_id": selected_plan["task"]["id"],
                    "gate": {"status": "PASS"},
                },
            )

            result = mod.command_multimodel_intervention_parallel_step(
                type("Args", (), {"max_workers": 2, "json": True})()
            )
            assert result["status"] == "OK", result
            assert result.get("action") != "no_eligible_tasks", result
            assert result["tasks_processed"] == 1, result
            assert result["tasks_passed"] == 1, result
        finally:
            os.environ.clear()
            os.environ.update(old_env)


def test_ratification_policy_is_loaded_from_quorum_config_not_code_literals():
    td, _vault, env = make_env_and_vault()
    with td:
        old_env = os.environ.copy()
        try:
            quorum_path = Path(td.name) / "quorum.yaml"
            quorum_path.write_text("""
ratification:
  required_models: [alpha-core, beta-core]
  optional_models: [gamma-optional, delta-optional]
tiers:
  T3:
    quorum: 4
    min_quorum: 2
    planners: [alpha-core, beta-core, gamma-optional, delta-optional]
""".strip(), encoding="utf-8")
            os.environ.clear()
            os.environ.update(env)
            os.environ["HERMES_QUORUM_CONFIG"] = str(quorum_path)
            mod = load_orchestrator_module()
            assert mod.REQUIRED_RATIFICATION_MODELS == ("alpha-core", "beta-core")
            assert mod.OPTIONAL_RATIFICATION_MODELS == ("gamma-optional", "delta-optional")
            assert mod.RATIFICATION_CORE_COUNT == 2
            assert mod.RATIFICATION_FULL_QUORUM == 4
            discussion = {
                "status": "certified",
                "task_id": "config-policy-task",
                "models_consulted": ["alpha-core", "beta-core", "gamma-optional"],
                "issue_ledger": [],
                "ratification_votes": [
                    {"model": "alpha-core", "vote": "approve", "best_within_constraints": True},
                    {"model": "beta-core", "vote": "approve", "best_within_constraints": True},
                    {"model": "gamma-optional", "vote": "approve", "best_within_constraints": True},
                ],
                "agreement_matrix": {"framing": 0.95, "approach": 0.95, "implementation_order": 0.95},
                "truth_status": "certified",
                "criteria_satisfied": {"accuracy": True, "long_term_goal": True, "one_shot_landing": True},
                "final_design": {
                    "long_term_goal_alignment": True,
                    "next_slice": "configured policy next slice",
                    "acceptance_evidence": ["configured policy gate PASS"],
                    "rollback_boundary": "revert configured policy change",
                },
            }
            gate = mod.ratification_gate_result(discussion)
            assert gate["status"] == "PASS", gate
            assert not any("gamma-optional" in f and "unexpected" in f for f in gate["failures"]), gate
        finally:
            os.environ.clear()
            os.environ.update(old_env)


def test_terminal_boundary_debt_does_not_block_active_dispatch_boundary():
    td, vault, env = make_env_and_vault()
    with td:
        tasks_dir = vault / "05-实践与项目" / "tasks"
        (tasks_dir / "historical-mission-debt.md").write_text("""---
type: task
status: done
priority: P1
project: hermes-agent
lane: evolution
architecture_target: taskpool
capability_delta: historical debt fixture
anti_drift_check: boundary debt remains visible
acceptance_evidence: command:fixture
mission_schema_version: mission_task_v1
mission_objective: historical terminal task with incomplete mission envelope
expires_at: 2099-01-01
---
# Historical mission debt

## Proof Log
- command: fixture

## Final Handoff
- done fixture
""", encoding="utf-8")
        (tasks_dir / "active-mission-debt.md").write_text("""---
type: task
status: pending
priority: P1
project: hermes-agent
lane: evolution
architecture_target: taskpool
capability_delta: active debt fixture
anti_drift_check: active boundary remains fail-closed
acceptance_evidence: command:fixture
mission_schema_version: mission_task_v1
mission_objective: active task with incomplete mission envelope
expires_at: 2099-01-01
---
# Active mission debt
""", encoding="utf-8")
        boundary = json.loads(run(env, "boundary-check", "--json", check=False).stdout)
        assert boundary["status"] == "FAIL", boundary
        assert any(item.get("task") == "active-mission-debt" for item in boundary["invalid"]), boundary
        assert any(item.get("task") == "historical-mission-debt" for item in boundary.get("debt_invalid", [])), boundary

        (tasks_dir / "active-mission-debt.md").unlink()
        boundary = json.loads(run(env, "boundary-check", "--json").stdout)
        assert boundary["status"] == "PASS", boundary
        assert boundary.get("debt_invalid_count", 0) == 1, boundary
        assert boundary["debt_invalid"][0]["task"] == "historical-mission-debt", boundary


def test_review_gap_scan_classifies_done_gate_failures_without_mutating_review_task():
    td, vault, env = make_env_and_vault()
    try:
        task_id, task_path = add_review_evolution_task(env, title="验证 review 缺自愈分类")
        text = task_path.read_text(encoding="utf-8")
        text = text.replace("ratification-or-selfcheck-review-done", "project-evidence-review-done")
        text = text.replace("lane: evolution", "lane: work")
        text = text.replace("project: self-improvement", "project: hermes")
        if "source_weighting_policy_ref:" not in text:
            text = text.replace("project: hermes\n", "project: hermes\nsource_weighting_policy_ref: profile:hermes:lark_evidence_policy\n", 1)
        task_path.write_text(text, encoding="utf-8")

        result = json.loads(run(env, "review-gap-scan", "--task", task_id, "--json").stdout)
        assert result["status"] == "OK", result
        assert result["gap_count"] == 1, result
        gap = result["gaps"][0]
        assert gap["task_id"] == task_id, gap
        assert gap["gap_types"] == ["missing_project_verification"], gap
        assert gap["repairable"] is True, gap
        assert "project-evidence-review-done requires" in gap["failures"][0], gap
        assert find_task_status(task_path) == "review"
    finally:
        td.cleanup()


def test_auto_close_review_fails_closed_on_negative_closeout_proof_marker():
    td, vault, env = make_env_and_vault()
    try:
        task_id, task_path = add_review_evolution_task(env, title="验证 negative proof 不会自动 done")
        text = task_path.read_text(encoding="utf-8")
        text = text.replace(
            "evidence:\n  - command:selfcheck PASS",
            "evidence:\n  - command:selfcheck PASS\n  - proof:closeout-gap/do-not-mark-done",
            1,
        )
        task_path.write_text(text, encoding="utf-8")

        result = json.loads(run(env, "auto-close-review", "--task", task_id, "--json").stdout)
        assert result["status"] == "OK", result
        assert result["closed_count"] == 0, result
        assert result["skipped_count"] == 1, result
        skipped = result["skipped"][0]
        assert skipped["task_id"] == task_id, skipped
        assert any("negative_closeout_evidence_present" in failure for failure in skipped["failures"]), skipped
        assert "proof:closeout-gap/do-not-mark-done" in skipped["evidence"], skipped
        assert find_task_status(task_path) == "review"
    finally:
        td.cleanup()


def test_review_gap_scan_write_creates_idempotent_bounded_repair_child_task():
    td, vault, env = make_env_and_vault()
    try:
        task_id, task_path = add_review_evolution_task(env, title="验证 review 自动补证任务")
        annotate_manual_review(task_path, final_landed=False)

        first = json.loads(run(env, "review-gap-scan", "--task", task_id, "--write", "--json").stdout)
        assert first["created_count"] == 1, first
        created = first["created"][0]
        child = Path(created["path"])
        child_text = child.read_text(encoding="utf-8")
        assert any(f"status: {status}" in child_text for status in ("pending", "claimed", "running")), child_text
        assert f"review_gap_parent: {task_id}" in child_text
        assert "review_gap_type:" in child_text and "missing_final_landed_evidence" in child_text
        assert "no direct done permission" in child_text
        assert "requires_multimodel: " in child_text
        parent_text = task_path.read_text(encoding="utf-8")
        assert "review_gap_children:" in parent_text
        assert created["task_id"] in parent_text

        second = json.loads(run(env, "review-gap-scan", "--task", task_id, "--write", "--json").stdout)
        assert second["created_count"] == 0, second
        assert second["gaps"][0]["existing_child_task"] == created["task_id"], second
    finally:
        td.cleanup()


def find_task_status(task_path: Path) -> str:
    for line in task_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("status:"):
            return line.split(":", 1)[1].strip()
    raise AssertionError(f"missing status in {task_path}")


def test_event_hook_no_multimodel_spawn_env_gate_overrides_force_and_auto_routes():
    old_env = os.environ.copy()
    try:
        os.environ.clear()
        os.environ.update(old_env)
        os.environ["HERMES_TASKPOOL_EVENT_HOOK_NO_MULTIMODEL_SPAWN"] = "1"
        os.environ["HERMES_TASKPOOL_EVENT_HOOK_MULTIMODEL"] = "force"
        mod = load_orchestrator_module()

        forced = mod.event_hook_multimodel_route("task_transitioned", "forced-task")
        assert forced["enabled"] is False, forced
        assert forced["reason"] == "multimodel_spawn_disabled_by_env", forced
        assert forced["env_flag"] == "HERMES_TASKPOOL_EVENT_HOOK_NO_MULTIMODEL_SPAWN", forced

        os.environ["HERMES_TASKPOOL_EVENT_HOOK_MULTIMODEL"] = "auto"
        original_find_task = mod.find_task
        original_reasons = mod.task_multimodel_intervention_reasons
        original_cert_reasons = mod.task_multimodel_certification_reasons
        original_advisory_reasons = mod.task_multimodel_advisory_reasons
        try:
            setattr(mod, "find_task", lambda task_id: SimpleNamespace(
                id=task_id,
                status="running",
                priority="P2",
                lane="evolution",
                project="hermes-agent",
                fm={},
            ))
            setattr(mod, "task_multimodel_intervention_reasons", lambda task: ["fixture_reason"])
            setattr(mod, "task_multimodel_certification_reasons", lambda task: [])
            setattr(mod, "task_multimodel_advisory_reasons", lambda task: ["fixture_reason"])
            auto = mod.event_hook_multimodel_route("task_transitioned", "auto-task")
        finally:
            setattr(mod, "find_task", original_find_task)
            setattr(mod, "task_multimodel_intervention_reasons", original_reasons)
            setattr(mod, "task_multimodel_certification_reasons", original_cert_reasons)
            setattr(mod, "task_multimodel_advisory_reasons", original_advisory_reasons)

        assert auto["enabled"] is False, auto
        assert auto["reason"] == "multimodel_spawn_disabled_by_env", auto
    finally:
        os.environ.clear()
        os.environ.update(old_env)


def test_event_hook_auto_route_enables_multimodel_for_p1_evolution_control_plane_task():
    old_env = os.environ.copy()
    try:
        os.environ.clear()
        os.environ.update(old_env)
        os.environ["HERMES_TASKPOOL_EVENT_HOOK_MULTIMODEL"] = "auto"
        mod = load_orchestrator_module()

        original_find_task = mod.find_task
        original_reasons = mod.task_multimodel_intervention_reasons
        original_cert_reasons = mod.task_multimodel_certification_reasons
        original_advisory_reasons = mod.task_multimodel_advisory_reasons
        try:
            setattr(mod, "find_task", lambda task_id: SimpleNamespace(
                id=task_id,
                status="pending",
                priority="P1",
                lane="evolution",
                project="hermes-agent",
                fm={"architecture_target": "taskpool"},
            ))
            setattr(mod, "task_multimodel_intervention_reasons", lambda task: ["architecture_target", "evolution_lane"])
            setattr(mod, "task_multimodel_certification_reasons", lambda task: [])
            setattr(mod, "task_multimodel_advisory_reasons", lambda task: ["architecture_target", "evolution_lane"])
            route = mod.event_hook_multimodel_route("task_added", "selector-fix-task")
        finally:
            setattr(mod, "find_task", original_find_task)
            setattr(mod, "task_multimodel_intervention_reasons", original_reasons)
            setattr(mod, "task_multimodel_certification_reasons", original_cert_reasons)
            setattr(mod, "task_multimodel_advisory_reasons", original_advisory_reasons)

        assert route["enabled"] is True, route
        assert route["reason"] == "smart_route_matched", route
        assert route["priority"] == "P1", route
        assert route["lane"] == "evolution", route
        assert route["project"] == "hermes-agent", route
        assert route["reasons"] == ["architecture_target", "evolution_lane"], route
        assert route["advisory_reasons"] == ["architecture_target", "evolution_lane"], route
        assert route["certification_reasons"] == [], route
    finally:
        os.environ.clear()
        os.environ.update(old_env)


def test_event_hook_dream_audit_gate_blocks_blocked_candidate(tmp_path):
    old_env = os.environ.copy()
    try:
        state_path = tmp_path / "confidence-db.json"
        state_path.write_text(json.dumps({"skills": {"apple": {
            "darwin_score": 80,
            "audit_cooldown_until": "2099-01-15T00:00:00+08:00",
            "audit_blocked_reason": "repeated_no_state_change",
        }}}, ensure_ascii=False), encoding="utf-8")
        os.environ["HERMES_EVOLUTION_CONFIDENCE_DB_PATH"] = str(state_path)
        os.environ["HERMES_TASKPOOL_EVENT_HOOK_MULTIMODEL"] = "auto"
        mod = load_orchestrator_module()

        original_find_task = mod.find_task
        try:
            setattr(mod, "find_task", lambda task_id: SimpleNamespace(
                id=task_id,
                status="pending",
                priority="P1",
                lane="evolution",
                project="hermes-agent",
                fm={
                    "architecture_target": "taskpool",
                    "dream_audit_advancement": True,
                    "dream_audit_skill": "apple",
                    "proof_artifacts": ["artifact:/tmp/apple-audit-proof.json"],
                },
            ))
            route = mod.event_hook_multimodel_route("task_added", "dream-audit-task")
        finally:
            setattr(mod, "find_task", original_find_task)

        assert route["enabled"] is False, route
        assert route["reason"] == "dream_audit_blocked", route
        assert route["dream_audit_gate"]["decision"] == "block", route
        assert route["dream_audit_gate"]["blocked_reason"] == "repeated_no_state_change", route
    finally:
        os.environ.clear()
        os.environ.update(old_env)


def test_event_hook_dream_audit_gate_holds_cooling_candidate(tmp_path):
    old_env = os.environ.copy()
    try:
        state_path = tmp_path / "confidence-db.json"
        state_path.write_text(json.dumps({"skills": {"apple": {
            "darwin_score": 80,
            "audit_cooldown_until": "2099-01-15T00:00:00+08:00",
        }}}, ensure_ascii=False), encoding="utf-8")
        os.environ["HERMES_EVOLUTION_CONFIDENCE_DB_PATH"] = str(state_path)
        os.environ["HERMES_TASKPOOL_EVENT_HOOK_MULTIMODEL"] = "auto"
        mod = load_orchestrator_module()

        original_find_task = mod.find_task
        try:
            setattr(mod, "find_task", lambda task_id: SimpleNamespace(
                id=task_id,
                status="pending",
                priority="P1",
                lane="evolution",
                project="hermes-agent",
                fm={
                    "architecture_target": "taskpool",
                    "dream_audit_advancement": True,
                    "dream_audit_skill": "apple",
                    "proof_artifacts": ["artifact:/tmp/apple-audit-proof.json"],
                },
            ))
            route = mod.event_hook_multimodel_route("task_added", "dream-audit-task")
        finally:
            setattr(mod, "find_task", original_find_task)

        assert route["enabled"] is False, route
        assert route["reason"] == "dream_audit_cooling_down", route
        assert route["dream_audit_gate"]["decision"] == "hold_for_cooldown", route
    finally:
        os.environ.clear()
        os.environ.update(old_env)


def test_event_hook_dream_audit_gate_advances_eligible_candidate(tmp_path):
    old_env = os.environ.copy()
    try:
        state_path = tmp_path / "confidence-db.json"
        state_path.write_text(json.dumps({"skills": {"research": {
            "darwin_score": 72,
            "last_audit_attempt": "2026-06-01T00:00:00+08:00",
            "consecutive_no_change": 0,
        }}}, ensure_ascii=False), encoding="utf-8")
        os.environ["HERMES_EVOLUTION_CONFIDENCE_DB_PATH"] = str(state_path)
        os.environ["HERMES_TASKPOOL_EVENT_HOOK_MULTIMODEL"] = "auto"
        mod = load_orchestrator_module()

        original_find_task = mod.find_task
        original_reasons = mod.task_multimodel_intervention_reasons
        original_cert_reasons = mod.task_multimodel_certification_reasons
        original_advisory_reasons = mod.task_multimodel_advisory_reasons
        try:
            setattr(mod, "find_task", lambda task_id: SimpleNamespace(
                id=task_id,
                status="pending",
                priority="P1",
                lane="evolution",
                project="hermes-agent",
                fm={
                    "architecture_target": "taskpool",
                    "dream_audit_advancement": True,
                    "dream_audit_skill": "research",
                    "proof_artifacts": ["artifact:/tmp/research-audit-proof.json"],
                },
            ))
            setattr(mod, "task_multimodel_intervention_reasons", lambda task: ["architecture_target", "evolution_lane"])
            setattr(mod, "task_multimodel_certification_reasons", lambda task: [])
            setattr(mod, "task_multimodel_advisory_reasons", lambda task: ["architecture_target", "evolution_lane"])
            route = mod.event_hook_multimodel_route("task_added", "dream-audit-task")
        finally:
            setattr(mod, "find_task", original_find_task)
            setattr(mod, "task_multimodel_intervention_reasons", original_reasons)
            setattr(mod, "task_multimodel_certification_reasons", original_cert_reasons)
            setattr(mod, "task_multimodel_advisory_reasons", original_advisory_reasons)

        assert route["enabled"] is True, route
        assert route["reason"] == "smart_route_matched", route
        assert route["dream_audit_gate"]["decision"] == "advance", route
        assert route["dream_audit_gate"]["skill"] == "research", route
    finally:
        os.environ.clear()
        os.environ.update(old_env)


def test_event_hook_dream_audit_gate_retries_missing_or_invalid_state(tmp_path):
    old_env = os.environ.copy()
    try:
        state_path = tmp_path / "confidence-db.json"
        state_path.write_text(json.dumps({"skills": {}}, ensure_ascii=False), encoding="utf-8")
        os.environ["HERMES_EVOLUTION_CONFIDENCE_DB_PATH"] = str(state_path)
        os.environ["HERMES_TASKPOOL_EVENT_HOOK_MULTIMODEL"] = "auto"
        mod = load_orchestrator_module()

        original_find_task = mod.find_task
        try:
            setattr(mod, "find_task", lambda task_id: SimpleNamespace(
                id=task_id,
                status="pending",
                priority="P1",
                lane="evolution",
                project="hermes-agent",
                fm={
                    "architecture_target": "taskpool",
                    "dream_audit_advancement": True,
                    "dream_audit_skill": "missing-skill",
                    "proof_artifacts": ["artifact:/tmp/missing-audit-proof.json"],
                },
            ))
            route = mod.event_hook_multimodel_route("task_added", "dream-audit-task")
        finally:
            setattr(mod, "find_task", original_find_task)

        assert route["enabled"] is False, route
        assert route["reason"] == "dream_audit_missing_selector_state", route
        assert route["dream_audit_gate"]["decision"] == "retry_later", route
    finally:
        os.environ.clear()
        os.environ.update(old_env)


def test_boundary_readiness_exposes_diversity_diagnostics_for_advisory_8_deficit():
    mod = load_orchestrator_module()
    readiness = mod.boundary_readiness_summary(
        requested_agents=8,
        selected=[
            {"id": "a1", "lane": "advisory", "boundary_key": "repo:a"},
            {"id": "b1", "lane": "advisory", "boundary_key": "repo:b"},
            {"id": "c1", "lane": "advisory", "boundary_key": "repo:c"},
            {"id": "d1", "lane": "advisory", "boundary_key": "repo:d"},
        ],
        skipped=[
            {"id": "a2", "lane": "advisory", "reason": "parallel_boundary_conflict", "boundary_key": "repo:a"},
            {"id": "a3", "lane": "advisory", "reason": "parallel_boundary_conflict", "boundary_key": "repo:a"},
            {"id": "b2", "lane": "advisory", "reason": "parallel_boundary_conflict", "boundary_key": "repo:b"},
        ],
        dispatchable_count=7,
    )
    diagnostics = readiness["capacity_diagnostics"]
    assert diagnostics["slot_deficit"] == 4, readiness
    assert diagnostics["unique_selected_boundary_count"] == 4, readiness
    assert diagnostics["top_limiting_boundaries"][0]["boundary_key"] == "repo:a", readiness
    assert "increase_boundary_diversity_or_split_conflict_group" in diagnostics["recommended_actions"], readiness


def test_boundary_reclassification_groups_repair_by_parent_and_gap():
    mod = load_orchestrator_module()
    task = mod.Task(
        Path("/tmp/repair.md"),
        {
            "type": "task",
            "id": "repair-1",
            "title": "Task - 补证闭环 missing_advisory_artifact",
            "status": "pending",
            "lane": "advisory",
            "project": "hermes-agent-infrastructure",
            "parallel_boundary": "hermes-agent-infrastructure",
            "objective": "For parent review task `parent-task-1`, repair the done-gate gap `missing_advisory_artifact` without marking the parent done.",
            "acceptance_evidence": "artifact:/file:/url evidence artifact; does not directly transition the parent to done",
        },
        "body says evidence artifact and does not directly transition the parent to done",
    )
    prop = mod.boundary_reclassification_proposal(task)
    assert prop is not None
    assert prop["basis"] == "parent_gap_repair"
    assert prop["proposed_parallel_boundary"] == "advisory-repair:parent-task-1:missing-advisory-artifact"
    assert prop["rollback"]["parallel_boundary"] == "hermes-agent-infrastructure"


def test_boundary_reclassification_refuses_workspace_or_non_advisory_tasks():
    mod = load_orchestrator_module()
    workspace_task = mod.Task(
        Path("/tmp/write.md"),
        {
            "type": "task",
            "id": "write-1",
            "title": "Task - code write",
            "status": "pending",
            "lane": "advisory",
            "project": "hermes-agent-infrastructure",
            "parallel_boundary": "hermes-agent-infrastructure",
            "workspace": "/tmp/repo",
            "objective": "read-only advisory evidence artifact without marking the parent done",
        },
        "does not directly transition",
    )
    work_task = mod.Task(
        Path("/tmp/work.md"),
        {
            "type": "task",
            "id": "work-1",
            "title": "Task - work",
            "status": "pending",
            "lane": "work",
            "project": "hermes-agent-infrastructure",
            "parallel_boundary": "hermes-agent-infrastructure",
            "objective": "read-only advisory evidence artifact without marking the parent done",
        },
        "does not directly transition",
    )
    assert mod.boundary_reclassification_proposal(workspace_task) is None
    assert mod.boundary_reclassification_proposal(work_task) is None


def main():
    test_railway_deploy_gate_accepts_exact_prefix_and_ancestor_commits()
    test_railway_deploy_gate_evaluate_uses_ancestor_relation()
    test_mission_envelope_create_boundary_synthesizes_complete_envelope()
    test_multimodel_writeback_completes_partial_mission_envelope_without_certifying_failure()
    test_mission_envelope_schema_is_enforced_fail_closed()
    test_valid_mission_envelope_preserves_work_priority_and_lifecycle_closeout_gate()
    test_add_list_claim_release_dashboard_inbox_selfcheck()
    test_work_closeout_pair_blocks_ui_retest_until_parent_done_and_user_dispatch_release()
    test_authorize_railway_deploy_releases_online_ui_retest_gate_with_matching_commit()
    test_work_closeout_pair_fires_event_hook_only_after_metadata_is_persisted()
    test_generic_work_task_remains_dispatchable_without_work_closeout_fields()
    test_lifecycle_transition_gate_and_audit()
    test_lifecycle_transition_retry_sets_delay_and_count()
    test_lifecycle_fail_closed_edges()
    test_lane_architecture_alignment_and_work_priority_gate()
    test_mission_dag_dashboard_progress_and_ready_nodes()
    test_mission_dag_cycle_fails_boundary_and_dispatch()
    test_multimodel_intervention_and_pua_loop_gate_are_automatic_and_read_only()
    test_discussion_task_binding_stamp_closes_target_binding_gap()
    test_evidence_spine_exports_stable_ids_and_auto_completer_blocker_semantics()
    test_autonomy_readiness_reports_complete_fail_closed_architecture()
    test_autorun_runner_pauses_on_pending_permission_gate()
    test_autorun_eligibility_and_handoff_are_fail_closed()
    test_non_blocking_auto_subtask_reconcile_actions_do_not_block_next_or_eligibility()
    test_auto_split_non_convergence_creates_axis_specific_narrowed_briefs()
    test_auto_subtask_sync_reopens_loop_non_convergence_parent_and_backfills_child_evidence()
    test_loop_non_convergence_parent_uses_targeted_evidence_refresh_plan_after_children_finish()
    test_autorun_kill_switches_and_evolution_preemption_gate()
    test_boundary_check_and_parallel_dispatch_dry_run_are_fail_closed()
    test_autorun_done_requires_valid_proof_hash()
    test_proof_check_flags_persisted_autorun_done_without_proof_hash()
    test_proof_check_include_active_does_not_fail_historical_autorun_hashes()
    test_multimodel_step_marks_task_running_while_external_process_is_inflight_then_review()
    test_multimodel_step_background_spawns_durable_job_without_waiting_for_models()
    test_economy_gate_allows_recovery_rerun_after_missing_required_model_smoke_pass()
    test_ratification_policy_is_loaded_from_quorum_config_not_code_literals()
    test_terminal_boundary_debt_does_not_block_active_dispatch_boundary()
    test_review_gap_scan_classifies_done_gate_failures_without_mutating_review_task()
    test_auto_close_review_fails_closed_on_negative_closeout_proof_marker()
    test_review_gap_scan_write_creates_idempotent_bounded_repair_child_task()
    test_event_hook_no_multimodel_spawn_env_gate_overrides_force_and_auto_routes()
    test_boundary_readiness_exposes_diversity_diagnostics_for_advisory_8_deficit()
    test_boundary_reclassification_groups_repair_by_parent_and_gap()
    test_boundary_reclassification_refuses_workspace_or_non_advisory_tasks()
    print("PASS")


if __name__ == "__main__":
    main()


def test_retry_classification_detects_escape_timeout_and_hot_retry():
    mod = load_orchestrator_module()

    escape = SimpleNamespace(status="retry", fm={"retry_count": 2, "evidence": ["command:agent_team_controller consume-claimed human_escape_release"]}, body="")
    timeout = SimpleNamespace(status="retry", fm={"retry_count": 1, "evidence": ["command:agent_team_controller consume-claimed worker timeout"]}, body="")
    timeout_stub = SimpleNamespace(status="retry", fm={"retry_count": 1, "last_error": "timeout_with_proof_stub proof_stub_path=/tmp/proof.json"}, body="")
    hot = SimpleNamespace(status="retry", fm={"retry_count": 4, "evidence": []}, body="")
    clean = SimpleNamespace(status="pending", fm={}, body="")

    assert mod.retry_lane_for_task(escape)["lane"] == "escape_quarantine"
    assert mod.retry_lane_for_task(timeout)["lane"] == "timeout_debug"
    assert mod.retry_lane_for_task(timeout_stub)["lane"] == "timeout_debug"
    assert mod.retry_lane_for_task(hot)["lane"] == "escape_quarantine"
    assert mod.retry_lane_for_task(clean)["lane"] == "clean_pending"


def test_select_parallel_dispatch_caps_retry_lanes_and_preserves_clean_headroom():
    mod = load_orchestrator_module()

    class FakeTask:
        def __init__(self, task_id, status, boundary, retry_count=0, evidence=None):
            self.id = task_id
            self.status = status
            self.lane = "work"
            self.path = Path(f"/tmp/{task_id}.md")
            self.fm = {
                "status": status,
                "parallel_boundary": boundary,
                "retry_count": retry_count,
                "evidence": evidence or [],
            }
            self.body = ""
        def row(self):
            return {"id": self.id, "status": self.status, "retry_count": self.fm.get("retry_count"), "parallel_boundary": self.fm.get("parallel_boundary")}

    tasks = [
        FakeTask("escape-1", "retry", "b-escape-1", 2, ["command:agent_team_controller consume-claimed human_escape_release"]),
        FakeTask("escape-2", "retry", "b-escape-2", 2, ["command:agent_team_controller consume-claimed human_escape_release"]),
        FakeTask("timeout-1", "retry", "b-timeout-1", 1, ["command:agent_team_controller consume-claimed worker timeout"]),
        FakeTask("timeout-2", "retry", "b-timeout-2", 1, ["command:agent_team_controller consume-claimed worker timeout"]),
        FakeTask("timeout-3", "retry", "b-timeout-3", 1, ["command:agent_team_controller consume-claimed worker timeout"]),
        FakeTask("clean-1", "pending", "b-clean-1"),
        FakeTask("clean-2", "pending", "b-clean-2"),
        FakeTask("clean-3", "pending", "b-clean-3"),
    ]
    old_dispatchable = mod.dispatchable_tasks
    old_iter = mod.iter_tasks
    old_mode = mod.taskpool_priority_mode
    try:
        mod.dispatchable_tasks = lambda: tasks
        mod.iter_tasks = lambda: []
        mod.taskpool_priority_mode = lambda: "work-first"
        selected, skipped = mod.select_parallel_dispatch(6)
    finally:
        mod.dispatchable_tasks = old_dispatchable
        mod.iter_tasks = old_iter
        mod.taskpool_priority_mode = old_mode

    selected_ids = [t.id for t in selected]
    assert selected_ids.count("escape-1") == 1
    assert "escape-2" not in selected_ids
    assert {"timeout-1", "timeout-2"}.issubset(set(selected_ids))
    assert "timeout-3" not in selected_ids
    assert any(i.startswith("clean-") for i in selected_ids), selected_ids
    assert any(s.get("reason") == "retry_lane_cap_exceeded" and s.get("retry_lane") == "escape_quarantine" for s in skipped)
    assert any(s.get("reason") == "retry_lane_cap_exceeded" and s.get("retry_lane") == "timeout_debug" for s in skipped)
