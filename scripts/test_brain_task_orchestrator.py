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
        assert "transition TASK_ID" in control_center
        assert "lifecycle_transitions" in Path(dash["dashboard"]).read_text(encoding="utf-8")

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


def main():
    test_add_list_claim_release_dashboard_inbox_selfcheck()
    test_lifecycle_transition_gate_and_audit()
    test_lifecycle_transition_retry_sets_delay_and_count()
    test_lifecycle_fail_closed_edges()
    print("PASS")


if __name__ == "__main__":
    main()
