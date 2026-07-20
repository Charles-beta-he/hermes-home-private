#!/usr/bin/env python3
from __future__ import annotations

import fcntl
import json
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts" / "conversation_workspace.py"


class ConversationWorkspaceCLITest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.project = self.base / "project"
        self.worktree_a = self.base / "worktree-a"
        self.worktree_b = self.base / "worktree-b"
        self.worktree_a.mkdir()
        self.worktree_b.mkdir()
        result = self.call("init", "--root", str(self.project), "--project-id", "demo-project", "--display-name", "Demo")
        self.assertTrue(result["ok"])

    def tearDown(self) -> None:
        self.temp.cleanup()

    def call(self, *args: str, expect: int = 0) -> dict:
        proc = subprocess.run([sys.executable, str(CLI), *args], text=True, capture_output=True, check=False)
        self.assertEqual(proc.returncode, expect, msg=f"stdout={proc.stdout}\nstderr={proc.stderr}")
        return json.loads(proc.stdout)

    def write_json(self, relative: str, payload: object) -> Path:
        path = self.base / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def acquire(self, claim: str, direction: str, scope: str, worktree: Path | None = None, expect: int = 0) -> dict:
        args = [
            "claim-acquire", "--root", str(self.project), "--claim-id", claim,
            "--direction-id", direction, "--owner-session", f"session-{claim}",
            "--scope", scope,
        ]
        if worktree is not None:
            args.extend(["--worktree", str(worktree)])
        return self.call(*args, expect=expect)

    def test_init_is_idempotent_and_preserves_existing_project(self) -> None:
        project_file = self.project / "project.json"
        original = project_file.read_bytes()
        second = self.call("init", "--root", str(self.project), "--project-id", "demo-project", "--display-name", "Changed")
        self.assertTrue(second["preserved_existing"])
        self.assertEqual(project_file.read_bytes(), original)
        project = json.loads(original)
        self.assertTrue(project["tmux_session"].startswith("hx-"))
        self.assertTrue(all(value is False for value in project["authority"].values()))
        self.assertEqual(set(project["state_domains"]), {"direction", "task", "worker_runtime", "chat_session"})

    def test_write_claim_requires_existing_worktree(self) -> None:
        result = self.acquire("c1", "frontend", "src/frontend/**", expect=2)
        self.assertFalse(result["ok"])
        self.assertIn("requires --worktree", result["error"])
        result = self.acquire("c2", "frontend", "src/frontend/**", self.base / "missing", expect=2)
        self.assertIn("does not exist", result["error"])

    def test_claim_rejects_unbounded_ttl_and_parent_scope(self) -> None:
        base = [
            "claim-acquire", "--root", str(self.project), "--claim-id", "c1",
            "--direction-id", "frontend", "--owner-session", "session-c1",
            "--mode", "write", "--worktree", str(self.worktree_a),
        ]
        ttl_low = self.call(*base, "--scope", "src/**", "--ttl-minutes", "0", expect=2)
        self.assertIn("between 1 and 1440", ttl_low["error"])
        ttl_high = self.call(*base, "--scope", "src/**", "--ttl-minutes", "1441", expect=2)
        self.assertIn("between 1 and 1440", ttl_high["error"])
        traversal = self.call(*base, "--scope", "src/../secrets/**", expect=2)
        self.assertIn("parent traversal", traversal["error"])

    def test_overlapping_write_claim_is_rejected_and_release_is_idempotent(self) -> None:
        first = self.acquire("c1", "frontend", "src/frontend/**", self.worktree_a)
        self.assertFalse(first["tmux_executed"])
        overlap = self.acquire("c2", "backend", "src/frontend/page.ts", self.worktree_b, expect=2)
        self.assertIn("overlaps active claim", overlap["error"])
        release = self.call("claim-release", "--root", str(self.project), "--claim-id", "c1")
        self.assertEqual(release["claim"]["status"], "released")
        again = self.call("claim-release", "--root", str(self.project), "--claim-id", "c1")
        self.assertTrue(again["idempotent"])
        second = self.acquire("c2", "backend", "src/frontend/page.ts", self.worktree_b)
        self.assertTrue(second["ok"])

    def test_concurrent_same_direction_write_claims_are_serialized(self) -> None:
        lock_path = self.project / "05-runtime" / ".state.lock"
        command = lambda claim, scope, worktree: [
            sys.executable, str(CLI), "claim-acquire", "--root", str(self.project),
            "--claim-id", claim, "--direction-id", "shared-direction",
            "--owner-session", f"session-{claim}", "--mode", "write",
            "--scope", scope, "--worktree", str(worktree),
        ]
        with lock_path.open("a+", encoding="utf-8") as lock_handle:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
            first = subprocess.Popen(command("race-a", "src/a/**", self.worktree_a), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            second = subprocess.Popen(command("race-b", "src/b/**", self.worktree_b), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(0.3)
            self.assertIsNone(first.poll(), "first claimant bypassed the project state lock")
            self.assertIsNone(second.poll(), "second claimant bypassed the project state lock")
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
        first_out, first_err = first.communicate(timeout=5)
        second_out, second_err = second.communicate(timeout=5)
        self.assertEqual(sorted([first.returncode, second.returncode]), [0, 2], msg=f"first={first_out!r}/{first_err!r} second={second_out!r}/{second_err!r}")
        claims = json.loads((self.project / "05-runtime" / "active-claims.json").read_text(encoding="utf-8"))
        active = [claim for claim in claims if claim.get("status") == "active" and claim.get("direction_id") == "shared-direction"]
        self.assertEqual(len(active), 1)
        manifest = json.loads((self.project / "05-runtime" / "tmux-manifest.json").read_text(encoding="utf-8"))
        windows = [window for window in manifest["windows"] if window.get("direction_id") == "shared-direction"]
        self.assertEqual(len(windows), 1)

    def test_same_direction_single_writer_is_rejected_even_for_disjoint_scopes(self) -> None:
        self.acquire("c1", "frontend", "src/a/**", self.worktree_a)
        result = self.acquire("c2", "frontend", "src/b/**", self.worktree_b, expect=2)
        self.assertIn("already owns direction", result["error"])

    def test_partial_segment_glob_overlap_is_rejected(self) -> None:
        self.acquire("c1", "frontend", "src/a*.py", self.worktree_a)
        result = self.acquire("c2", "backend", "src/ab*.py", self.worktree_b, expect=2)
        self.assertIn("overlaps active claim", result["error"])

    def test_case_variant_scope_overlap_is_rejected(self) -> None:
        self.acquire("c1", "frontend", "src/Case/**", self.worktree_a)
        result = self.acquire("c2", "backend", "src/case/**", self.worktree_b, expect=2)
        self.assertIn("overlaps active claim", result["error"])

    def test_filesystem_equivalent_scope_aliases_are_rejected(self) -> None:
        cases = [
            ("src/./case/**", "src/case/**"),
            ("src//case/**", "src/case/**"),
            ("src/café/**", "src/cafe\u0301/**"),
        ]
        for index, (left, right) in enumerate(cases):
            with self.subTest(left=left, right=right):
                if index:
                    self.call("claim-release", "--root", str(self.project), "--claim-id", f"alias-left-{index - 1}")
                self.acquire(f"alias-left-{index}", f"left-{index}", left, self.worktree_a)
                result = self.acquire(f"alias-right-{index}", f"right-{index}", right, self.worktree_b, expect=2)
                self.assertIn("overlaps active claim", result["error"])

    def test_malformed_manifest_does_not_leave_ghost_claim(self) -> None:
        manifest_path = self.project / "05-runtime" / "tmux-manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["windows"] = "bad"
        manifest_path.write_text(json.dumps(manifest))
        events_before = (self.project / "02-ledger" / "events.jsonl").read_text()
        result = self.acquire("ghost", "frontend", "src/**", self.worktree_a, expect=2)
        self.assertIn("tmux manifest windows", result["error"])
        claims = json.loads((self.project / "05-runtime" / "active-claims.json").read_text())
        self.assertEqual(claims, [])
        self.assertEqual((self.project / "02-ledger" / "events.jsonl").read_text(), events_before)

    def test_malformed_manifest_does_not_partially_release_claim(self) -> None:
        self.acquire("kept", "frontend", "src/**", self.worktree_a)
        manifest_path = self.project / "05-runtime" / "tmux-manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["windows"] = "bad"
        manifest_path.write_text(json.dumps(manifest))
        events_before = (self.project / "02-ledger" / "events.jsonl").read_text()
        result = self.call("claim-release", "--root", str(self.project), "--claim-id", "kept", expect=2)
        self.assertIn("tmux manifest windows", result["error"])
        claims = json.loads((self.project / "05-runtime" / "active-claims.json").read_text())
        self.assertEqual(claims[0]["status"], "active")
        self.assertEqual((self.project / "02-ledger" / "events.jsonl").read_text(), events_before)

    def test_authority_bearing_or_semantically_malformed_manifest_fails_before_claim_mutation(self) -> None:
        manifest_path = self.project / "05-runtime" / "tmux-manifest.json"
        baseline = json.loads(manifest_path.read_text())
        variants = []
        authority = json.loads(json.dumps(baseline)); authority["execute_commands"] = True; variants.append(authority)
        wrong_project = json.loads(json.dumps(baseline)); wrong_project["project_id"] = "other"; variants.append(wrong_project)
        bad_panes = json.loads(json.dumps(baseline)); bad_panes["windows"][0]["panes"] = "bad"; variants.append(bad_panes)
        pane_command = json.loads(json.dumps(baseline)); pane_command["windows"][0]["panes"] = [{"role": "control", "command": "echo no"}]; variants.append(pane_command)
        for index, manifest in enumerate(variants):
            with self.subTest(index=index):
                manifest_path.write_text(json.dumps(manifest))
                events_before = (self.project / "02-ledger" / "events.jsonl").read_text()
                self.acquire(f"unsafe-{index}", f"dir-{index}", "src/**", self.worktree_a, expect=2)
                self.assertEqual(json.loads((self.project / "05-runtime" / "active-claims.json").read_text()), [])
                self.assertEqual((self.project / "02-ledger" / "events.jsonl").read_text(), events_before)

    def test_concurrent_init_is_serialized_and_rejects_identity_mismatch(self) -> None:
        project = self.base / "concurrent-init"
        lock_path = project / "05-runtime" / ".state.lock"
        lock_path.parent.mkdir(parents=True)
        command = lambda project_id: [
            sys.executable, str(CLI), "init", "--root", str(project),
            "--project-id", project_id, "--display-name", project_id,
        ]
        with lock_path.open("a+", encoding="utf-8") as lock_handle:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
            alpha = subprocess.Popen(command("alpha"), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            beta = subprocess.Popen(command("beta"), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(0.3)
            self.assertIsNone(alpha.poll(), "alpha init bypassed the project state lock")
            self.assertIsNone(beta.poll(), "beta init bypassed the project state lock")
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
        alpha_out, alpha_err = alpha.communicate(timeout=5)
        beta_out, beta_err = beta.communicate(timeout=5)
        self.assertEqual(sorted([alpha.returncode, beta.returncode]), [0, 2], msg=f"alpha={alpha_out!r}/{alpha_err!r} beta={beta_out!r}/{beta_err!r}")
        project_json = json.loads((project / "project.json").read_text(encoding="utf-8"))
        manifest = json.loads((project / "05-runtime" / "tmux-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(project_json["project_id"], manifest["project_id"])

    def test_review_claim_can_coexist_with_write_claim(self) -> None:
        self.acquire("c1", "frontend", "src/**", self.worktree_a)
        result = self.call(
            "claim-acquire", "--root", str(self.project), "--claim-id", "r1",
            "--direction-id", "frontend-review", "--owner-session", "review-session",
            "--mode", "review", "--scope", "src/**",
        )
        self.assertTrue(result["ok"])

    def test_tmux_plan_is_layout_only_and_does_not_execute(self) -> None:
        self.acquire("c1", "frontend", "src/frontend/**", self.worktree_a)
        plan = self.call("tmux-plan", "--root", str(self.project))
        self.assertFalse(plan["executed"])
        self.assertEqual(plan["replay_policy"], "layout_only_no_worker_commands")
        flattened = "\n".join(item["display"] for item in plan["commands"])
        self.assertIn("tmux new-session", flattened)
        self.assertIn("tmux new-window", flattened)
        self.assertNotIn("codex", flattened)
        self.assertNotIn("claude", flattened)
        self.assertNotIn("hermes chat", flattened)

    def test_tmux_reconcile_is_non_destructive_plan_only(self) -> None:
        self.acquire("c1", "frontend", "src/frontend/**", self.worktree_a)
        result = self.call("tmux-reconcile", "--root", str(self.project))
        self.assertTrue(result["ok"])
        self.assertEqual(result["state"], "session-absent")
        self.assertFalse(result["executed"])
        self.assertFalse(result["destructive_commands"])
        self.assertIn("00-control", result["missing_windows"])
        self.assertGreaterEqual(len(result["commands"]), 2)

    def test_handoff_accepts_safe_packet_and_rejects_secret_and_authority_fields(self) -> None:
        base = {
            "handoff_id": "h1",
            "direction_id": "frontend",
            "source_session_id": "session-1",
            "objective": "continue frontend",
            "verified_current_state": ["build passed"],
            "next_safe_step": "run focused test",
            "closure_state": "handoff-ready",
        }
        safe = self.write_json("safe-handoff.json", base)
        result = self.call("handoff-add", "--root", str(self.project), "--file", str(safe))
        self.assertTrue(Path(result["path"]).is_file())
        duplicate = self.call("handoff-add", "--root", str(self.project), "--file", str(safe))
        self.assertTrue(duplicate["idempotent"])
        secret = dict(base, handoff_id="h2", password="bad")
        secret_file = self.write_json("secret-handoff.json", secret)
        rejected = self.call("handoff-add", "--root", str(self.project), "--file", str(secret_file), expect=2)
        self.assertIn("secret-like field rejected", rejected["error"])
        authority = dict(base, handoff_id="h3", mark_done=True)
        authority_file = self.write_json("authority-handoff.json", authority)
        rejected = self.call("handoff-add", "--root", str(self.project), "--file", str(authority_file), expect=2)
        self.assertIn("authority-smuggling field rejected", rejected["error"])

    def test_event_append_rejects_secret_payload(self) -> None:
        payload = self.write_json("payload.json", {"note": "safe", "api_key": "forbidden"})
        result = self.call(
            "event-append", "--root", str(self.project), "--event-type", "note.recorded",
            "--payload-file", str(payload), expect=2,
        )
        self.assertIn("secret-like field rejected", result["error"])

    def test_event_append_rejects_unicode_compatibility_authority_alias(self) -> None:
        payload = self.write_json("unicode-authority.json", {"ｅｘｔｅｒｎａｌＤｉｓｐａｔｃｈ": True})
        result = self.call(
            "event-append", "--root", str(self.project), "--event-type", "note.recorded",
            "--payload-file", str(payload), expect=2,
        )
        self.assertIn("authority-smuggling field rejected", result["error"])

    def test_payload_aliases_and_commands_are_rejected(self) -> None:
        base = {
            "handoff_id": "alias-handoff",
            "direction_id": "frontend",
            "source_session_id": "session-1",
            "objective": "continue frontend",
            "verified_current_state": ["build passed"],
            "next_safe_step": "run focused test",
            "closure_state": "handoff-ready",
        }
        cases = [
            ("mark-done", True, "authority-smuggling"),
            ("taskStatus", "done", "authority-smuggling"),
            ("command", "rm -rf /", "authority-smuggling"),
            ("auth-token", "forbidden", "secret-like"),
            ("external_dispatch", True, "authority-smuggling"),
            ("taskpoolLifecycleWrite", True, "authority-smuggling"),
            ("execute_commands", True, "authority-smuggling"),
            ("lifecycleState", "done", "authority-smuggling"),
            ("completed_at", "now", "authority-smuggling"),
            ("approved", True, "authority-smuggling"),
        ]
        for index, (key, value, message) in enumerate(cases):
            packet = dict(base, handoff_id=f"alias-{index}")
            packet[key] = value
            source = self.write_json(f"alias-{index}.json", packet)
            result = self.call("handoff-add", "--root", str(self.project), "--file", str(source), expect=2)
            self.assertIn(message, result["error"])

    def test_handoff_type_errors_return_structured_json(self) -> None:
        base = {
            "handoff_id": "bad-type",
            "direction_id": "frontend",
            "source_session_id": "session-1",
            "objective": "continue frontend",
            "verified_current_state": ["build passed"],
            "next_safe_step": "run focused test",
            "closure_state": "handoff-ready",
        }
        cases = [
            ("closure_state", []),
            ("handoff_id", 123),
            ("direction_id", 123),
            ("source_session_id", []),
            ("objective", {}),
            ("verified_current_state", "build passed"),
            ("verified_current_state", [{"fact": "build passed"}]),
            ("next_safe_step", []),
        ]
        for index, (field, value) in enumerate(cases):
            packet = dict(base, handoff_id=f"bad-type-{index}")
            packet[field] = value
            source = self.write_json(f"bad-type-{index}.json", packet)
            result = self.call("handoff-add", "--root", str(self.project), "--file", str(source), expect=2)
            self.assertIn(field, result["error"])

    def test_doctor_rejects_done_without_evidence(self) -> None:
        tasks = self.project / "02-ledger" / "tasks.json"
        tasks.write_text(json.dumps([{"task_id": "t1", "status": "done", "evidence_refs": []}]), encoding="utf-8")
        report = self.call("doctor", "--root", str(self.project), expect=1)
        self.assertFalse(report["ok"])
        self.assertIn("done_requires_evidence", {item["check"] for item in report["findings"]})

    def test_doctor_rejects_complete_event_and_claim_schema_violations(self) -> None:
        events = self.project / "02-ledger" / "events.jsonl"
        event = json.loads(events.read_text().splitlines()[0])
        event["event_type"] = "task.done"
        events.write_text(json.dumps(event) + "\n")
        claims = self.project / "05-runtime" / "active-claims.json"
        claims.write_text(json.dumps([{
            "schema_version": 1, "claim_id": "bad", "project_id": "demo-project",
            "direction_id": "frontend", "owner_type": "hermes-session", "owner_session": "s",
            "mode": "review", "scope": "src/**", "worktree": None, "status": "active",
            "created_at": "2026-07-20T00:00:00Z", "expires_at": "2099-01-01T00:00:00Z"
        }]))
        report = self.call("doctor", "--root", str(self.project), expect=1)
        checks = {finding["check"] for finding in report["findings"]}
        self.assertIn("event_schema", checks)
        self.assertIn("claim_schema", checks)

    def test_doctor_rejects_symlinked_status_root(self) -> None:
        outside = self.base / "outside-status"
        outside.mkdir()
        status = self.project / "06-status"
        shutil.rmtree(status)
        status.symlink_to(outside, target_is_directory=True)
        result = self.call("doctor", "--root", str(self.project), "--out", "report.json", expect=2)
        self.assertIn("06-status must be a real directory", result["error"])
        self.assertFalse((outside / "report.json").exists())

    def test_evidence_hash_and_task_reference_are_verified(self) -> None:
        artifact = self.base / "artifact.txt"
        artifact.write_text("PASS\n", encoding="utf-8")
        added = self.call(
            "evidence-add", "--root", str(self.project), "--evidence-id", "E-1",
            "--kind", "test", "--path", str(artifact), "--summary", "focused test passed",
            "--claim-ref", "local-cli-test",
        )
        self.assertEqual(len(added["evidence"]["sha256"]), 64)
        tasks = self.project / "02-ledger" / "tasks.json"
        tasks.write_text(json.dumps([{"task_id": "t1", "status": "done", "evidence_refs": ["E-1"]}]), encoding="utf-8")
        green = self.call("doctor", "--root", str(self.project))
        self.assertTrue(green["ok"])
        artifact.write_text("MUTATED\n", encoding="utf-8")
        red = self.call("doctor", "--root", str(self.project), expect=1)
        self.assertIn("evidence_hash", {item["check"] for item in red["findings"]})

    def test_doctor_detects_malformed_jsonl_and_command_replay(self) -> None:
        events = self.project / "02-ledger" / "events.jsonl"
        with events.open("a", encoding="utf-8") as handle:
            handle.write("{broken\n")
        manifest_path = self.project / "05-runtime" / "tmux-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["windows"][0]["panes"][0]["command"] = "rm -rf /"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        report = self.call("doctor", "--root", str(self.project), expect=1)
        checks = {item["check"] for item in report["findings"]}
        self.assertIn("events_jsonl", checks)
        self.assertIn("tmux_pane_no_command", checks)

    def test_doctor_reports_missing_tmux_as_warning_not_completion_failure(self) -> None:
        self.acquire("c1", "frontend", "src/frontend/**", self.worktree_a)
        report = self.call("doctor", "--root", str(self.project), "--inspect-tmux")
        self.assertTrue(report["ok"])
        self.assertFalse(report["side_effects"]["tmux_executed"])
        checks = {item["check"] for item in report["findings"]}
        self.assertIn("tmux_runtime_missing", checks)

    def test_doctor_rejects_empty_authority_and_domain_definitions(self) -> None:
        project_path = self.project / "project.json"
        project = json.loads(project_path.read_text(encoding="utf-8"))
        project["authority"] = {}
        project_path.write_text(json.dumps(project), encoding="utf-8")
        authority = self.call("doctor", "--root", str(self.project), expect=1)
        self.assertIn("authority_closed", {item["check"] for item in authority["findings"]})

        project["authority"] = {
            "external_dispatch": False,
            "taskpool_lifecycle_write": False,
            "mission_lifecycle_write": False,
            "tmux_execution": False,
            "worker_execution": False,
            "deploy_push": False,
            "destructive_operations": False,
            "credential_entry": False,
        }
        project["state_domains"] = {
            "direction": [], "task": [], "worker_runtime": [], "chat_session": [],
        }
        project_path.write_text(json.dumps(project), encoding="utf-8")
        domains = self.call("doctor", "--root", str(self.project), expect=1)
        self.assertIn("state_domains", {item["check"] for item in domains["findings"]})

    def test_doctor_output_is_confined_to_status_directory(self) -> None:
        outside = self.base / "outside.json"
        rejected = self.call("doctor", "--root", str(self.project), "--out", str(outside), expect=2)
        self.assertIn("06-status", rejected["error"])
        self.assertFalse(outside.exists())
        allowed = self.project / "06-status" / "custom-doctor.json"
        report = self.call("doctor", "--root", str(self.project), "--out", str(allowed))
        self.assertTrue(report["ok"])
        self.assertTrue(allowed.is_file())

    def test_expired_active_claim_is_error(self) -> None:
        self.acquire("c1", "frontend", "src/frontend/**", self.worktree_a)
        claims_path = self.project / "05-runtime" / "active-claims.json"
        claims = json.loads(claims_path.read_text(encoding="utf-8"))
        claims[0]["expires_at"] = "2000-01-01T00:00:00Z"
        claims_path.write_text(json.dumps(claims), encoding="utf-8")
        report = self.call("doctor", "--root", str(self.project), expect=1)
        self.assertIn("claim_expired", {item["check"] for item in report["findings"]})

    def test_event_and_claim_lifecycle_schemas_fail_closed(self) -> None:
        payload = self.write_json("event.json", {"observation": "safe"})
        rejected = self.call("event-append", "--root", str(self.project), "--event-type", "note.recorded", "--payload", str(payload), "--actor", "   ", expect=2)
        self.assertFalse(rejected["ok"])
        events_path = self.project / "02-ledger" / "events.jsonl"
        events_original = events_path.read_text()
        events = [json.loads(line) for line in events_original.splitlines() if line.strip()]
        events[0]["event_type"] = "claim.released"
        events_path.write_text("\n".join(json.dumps(item) for item in events) + "\n")
        event_report = self.call("doctor", "--root", str(self.project), expect=1)
        self.assertIn("event_schema", {item["check"] for item in event_report["findings"]})
        events_path.write_text(events_original)

        self.acquire("c1", "frontend", "src/**", self.worktree_a)
        claims_path = self.project / "05-runtime" / "active-claims.json"
        claims = json.loads(claims_path.read_text())
        claims[0]["released_at"] = claims[0]["created_at"]
        claims_path.write_text(json.dumps(claims))
        claim_report = self.call("doctor", "--root", str(self.project), expect=1)
        self.assertIn("claim_schema", {item["check"] for item in claim_report["findings"]})

    def test_handoff_requires_evidence_backed_state_timestamp_and_absolute_worktree(self) -> None:
        base = {
            "handoff_id": "h1", "direction_id": "frontend", "source_session_id": "s1",
            "objective": "continue safely", "verified_current_state": ["verified"],
            "completed": [{"summary": "checked", "evidence_refs": ["E1"]}],
            "next_safe_step": "review", "closure_state": "handoff-ready", "worktree": None,
        }
        variants = [
            {**base, "verified_current_state": []},
            {**base, "completed": [{"summary": "checked", "evidence_refs": []}]},
            {**base, "recorded_at": "not-a-time"},
            {**base, "worktree": {"path": "relative/path", "branch": "feature"}},
        ]
        for index, variant in enumerate(variants):
            source = self.write_json(f"handoff-{index}.json", variant)
            result = self.call("handoff-add", "--root", str(self.project), "--file", str(source), expect=2)
            self.assertFalse(result["ok"])

    def test_public_event_schema_and_secret_authority_aliases_are_strict(self) -> None:
        for index, payload in enumerate((
            {"note": "safe", "clientSecret": "x"},
            {"note": "safe", "apiToken": "x"},
            {"note": "safe", "externalDispatchRequested": True},
            {},
            {"message": "wrong-key"},
        )):
            source = self.write_json(f"public-{index}.json", payload)
            result = self.call("event-append", "--root", str(self.project), "--event-type", "note.recorded", "--payload", str(source), expect=2)
            self.assertFalse(result["ok"])
        valid = self.write_json("public-valid.json", {"note": "safe observation"})
        accepted = self.call("event-append", "--root", str(self.project), "--event-type", "note.recorded", "--payload", str(valid))
        self.assertTrue(accepted["ok"])

    def test_handoff_completed_refs_must_resolve_to_canonical_evidence(self) -> None:
        packet = {
            "handoff_id": "unknown-evidence", "direction_id": "frontend", "source_session_id": "s1",
            "objective": "continue safely", "verified_current_state": ["verified"],
            "completed": [{"summary": "claimed complete", "evidence_refs": ["E-NOT-EXIST"]}],
            "next_safe_step": "review", "closure_state": "handoff-ready", "worktree": None,
        }
        source = self.write_json("unknown-evidence.json", packet)
        result = self.call("handoff-add", "--root", str(self.project), "--file", str(source), expect=2)
        self.assertFalse(result["ok"])
        self.assertFalse((self.project / "04-handoffs" / "sessions" / "unknown-evidence.json").exists())

    def test_malformed_history_blocks_all_dependent_mutations(self) -> None:
        events_path = self.project / "02-ledger" / "events.jsonl"
        events_path.write_text(events_path.read_text() + "{broken\n", encoding="utf-8")
        before_events = events_path.read_bytes()
        payload = self.write_json("safe-event.json", {"note": "safe"})
        self.call("event-append", "--root", str(self.project), "--event-type", "note.recorded", "--payload", str(payload), expect=2)
        self.assertEqual(before_events, events_path.read_bytes())
        packet = {
            "handoff_id": "blocked-handoff", "direction_id": "frontend", "source_session_id": "s1",
            "objective": "continue", "verified_current_state": ["verified"], "completed": [],
            "next_safe_step": "review", "closure_state": "handoff-ready", "worktree": None,
        }
        source = self.write_json("blocked-handoff.json", packet)
        self.call("handoff-add", "--root", str(self.project), "--file", str(source), expect=2)
        self.assertFalse((self.project / "04-handoffs" / "sessions" / "blocked-handoff.json").exists())
        self.call("claim-acquire", "--root", str(self.project), "--claim-id", "blocked-claim", "--direction-id", "frontend", "--owner-session", "s1", "--mode", "write", "--scope", "src/**", "--worktree", str(self.worktree_a), expect=2)
        self.assertEqual([], json.loads((self.project / "05-runtime" / "active-claims.json").read_text()))

        clean_events = before_events.decode().rsplit("{broken\n", 1)[0]
        events_path.write_text(clean_events, encoding="utf-8")
        evidence_path = self.project / "03-evidence" / "evidence-index.json"
        evidence_path.write_text("[{}]\n", encoding="utf-8")
        artifact = self.write_json("artifact.json", {"ok": True})
        before_evidence = evidence_path.read_bytes()
        self.call("evidence-add", "--root", str(self.project), "--evidence-id", "E1", "--kind", "file", "--path", str(artifact), "--summary", "safe", expect=2)
        self.assertEqual(before_evidence, evidence_path.read_bytes())

    def test_released_claim_timestamp_must_be_within_lease(self) -> None:
        self.acquire("c1", "frontend", "src/**", self.worktree_a)
        claims_path = self.project / "05-runtime" / "active-claims.json"
        claims = json.loads(claims_path.read_text())
        claims[0]["status"] = "released"
        claims[0]["released_at"] = "2000-01-01T00:00:00Z"
        claims_path.write_text(json.dumps(claims), encoding="utf-8")
        report = self.call("doctor", "--root", str(self.project), expect=1)
        self.assertIn("claim_schema", {item["check"] for item in report["findings"]})

    def test_tampered_evidence_blocks_handoff_and_evidence_mutations(self) -> None:
        artifact = self.base / "proof.txt"
        artifact.write_text("PASS\n", encoding="utf-8")
        self.call("evidence-add", "--root", str(self.project), "--evidence-id", "E1", "--kind", "test", "--path", str(artifact), "--summary", "proof")
        artifact.write_text("TAMPERED\n", encoding="utf-8")
        packet = {
            "handoff_id": "tampered-proof", "direction_id": "frontend", "source_session_id": "s1",
            "objective": "continue", "verified_current_state": ["verified"],
            "completed": [{"summary": "claimed", "evidence_refs": ["E1"]}],
            "next_safe_step": "review", "closure_state": "handoff-ready", "worktree": None,
        }
        source = self.write_json("tampered-proof.json", packet)
        self.call("handoff-add", "--root", str(self.project), "--file", str(source), expect=2)
        self.assertFalse((self.project / "04-handoffs" / "sessions" / "tampered-proof.json").exists())
        index_path = self.project / "03-evidence" / "evidence-index.json"
        before = index_path.read_bytes()
        second = self.base / "second.txt"
        second.write_text("PASS\n", encoding="utf-8")
        self.call("evidence-add", "--root", str(self.project), "--evidence-id", "E2", "--kind", "test", "--path", str(second), "--summary", "second", expect=2)
        self.assertEqual(before, index_path.read_bytes())

    def test_release_reconciles_naturally_expired_claim(self) -> None:
        self.acquire("c1", "frontend", "src/**", self.worktree_a)
        claims_path = self.project / "05-runtime" / "active-claims.json"
        claims = json.loads(claims_path.read_text())
        claims[0]["created_at"] = "2000-01-01T00:00:00Z"
        claims[0]["expires_at"] = "2000-01-01T00:01:00Z"
        claims_path.write_text(json.dumps(claims), encoding="utf-8")
        result = self.call("claim-release", "--root", str(self.project), "--claim-id", "c1")
        self.assertEqual("expired", result["claim"]["status"])
        self.assertNotIn("released_at", result["claim"])
        manifest = json.loads((self.project / "05-runtime" / "tmux-manifest.json").read_text())
        self.assertNotIn("c1", {window.get("claim_id") for window in manifest["windows"]})
        events = [json.loads(line) for line in (self.project / "02-ledger" / "events.jsonl").read_text().splitlines() if line.strip()]
        self.assertEqual("claim.expired", events[-1]["event_type"])


if __name__ == "__main__":
    unittest.main()
