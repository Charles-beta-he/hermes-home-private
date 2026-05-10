#!/usr/bin/env python3
"""Tests for brain_task_orchestrator.py.
Run with: python3 ~/.hermes/scripts/test_brain_task_orchestrator.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path.home() / ".hermes" / "scripts" / "brain_task_orchestrator.py"


def run(env, *args, check=True):
    cmd = [sys.executable, str(SCRIPT), *args]
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if check and r.returncode != 0:
        raise AssertionError(f"command failed {cmd}\nstdout={r.stdout}\nstderr={r.stderr}")
    return r


def make_env_and_vault():
    td = tempfile.TemporaryDirectory()
    vault = Path(td.name) / "brain"
    (vault / "05-实践与项目" / "tasks").mkdir(parents=True)
    (vault / "07-仪表盘").mkdir(parents=True)
    env = os.environ.copy()
    env["HERMES_BRAIN_VAULT"] = str(vault)
    env["HERMES_BRAIN_AUTORUN_STATE_DIR"] = str(Path(td.name) / "state")
    env["HERMES_AUTONOMY_WRITE_ALLOWLIST"] = str(Path(td.name) / "autonomy-write-allowlist.json")
    env.pop("HERMES_LOCAL_BRAIN_AUTORUN", None)
    return td, vault, env


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
    return created["id"], Path(created["created"])


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
        fields = fields.replace("mission_id: mission-test-envelope\n", "", 1)
    text = text.replace("concepts: [\"task\"]", "concepts: [\"missions\", \"mission-envelope\", \"proof-gate\"]", 1)
    text = text.replace(marker, fields + marker, 1)
    task_path.write_text(text, encoding="utf-8")


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
        mission_id, mission_path = add_evolution_task(env, title="Mission envelope valid", priority="P0")
        add_mission_envelope_fields(mission_path, valid=True)
        work_id, _ = add_task(env, title="客户 work P0 不能被 mission 抢占", priority="P0", project="client-work")

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
        done = json.loads(run(env, "done", mission_id, "--actor", "tester", "--evidence", "artifact:mission-proof", "--json").stdout)
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
        done = json.loads(run(env, "done", task_id, "--actor", "tester", "--evidence", "command: final unit-test PASS", "--json").stdout)
        assert done["status"] == "OK"
        proof = json.loads(run(env, "proof-check", "--json").stdout)
        assert proof["status"] == "PASS", proof

        selfcheck = json.loads(run(env, "selfcheck", "--json").stdout)
        assert selfcheck["status"] == "PASS", selfcheck


def test_lifecycle_transition_gate_and_audit():
    td, _vault, env = make_env_and_vault()
    with td:
        task_id, task_path = add_task(env, title="验证任务生命周期状态机")

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

        done = json.loads(run(env, "transition", task_id, "--to", "done", "--actor", "tester", "--evidence", "command: final lifecycle PASS", "--json").stdout)
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

        Path(env["HERMES_AUTONOMY_WRITE_ALLOWLIST"]).write_text(json.dumps(["kanban-worker"], ensure_ascii=False), encoding="utf-8")
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
        Path(env["HERMES_AUTONOMY_WRITE_ALLOWLIST"]).write_text(json.dumps(["kanban-worker"], ensure_ascii=False), encoding="utf-8")
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

        done = json.loads(run(env, "done", task_id, "--actor", "hermes-autorun", "--evidence", f"proof:{proof_hash}", "--evidence", "command: final PASS", "--json").stdout)
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


def main():
    test_mission_envelope_schema_is_enforced_fail_closed()
    test_valid_mission_envelope_preserves_work_priority_and_lifecycle_closeout_gate()
    test_add_list_claim_release_dashboard_inbox_selfcheck()
    test_lifecycle_transition_gate_and_audit()
    test_lifecycle_transition_retry_sets_delay_and_count()
    test_lifecycle_fail_closed_edges()
    test_lane_architecture_alignment_and_work_priority_gate()
    test_autorun_eligibility_and_handoff_are_fail_closed()
    test_autorun_kill_switches_and_evolution_preemption_gate()
    test_boundary_check_and_parallel_dispatch_dry_run_are_fail_closed()
    test_autorun_done_requires_valid_proof_hash()
    test_proof_check_flags_persisted_autorun_done_without_proof_hash()
    print("PASS")


if __name__ == "__main__":
    main()
