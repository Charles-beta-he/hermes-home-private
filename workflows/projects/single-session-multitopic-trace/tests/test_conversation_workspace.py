#!/usr/bin/env python3
from __future__ import annotations

import fcntl
import json
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

    def test_doctor_rejects_done_without_evidence(self) -> None:
        tasks = self.project / "02-ledger" / "tasks.json"
        tasks.write_text(json.dumps([{"task_id": "t1", "status": "done", "evidence_refs": []}]), encoding="utf-8")
        report = self.call("doctor", "--root", str(self.project), expect=1)
        self.assertFalse(report["ok"])
        self.assertIn("done_requires_evidence", {item["check"] for item in report["findings"]})

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

    def test_expired_active_claim_is_error(self) -> None:
        self.acquire("c1", "frontend", "src/frontend/**", self.worktree_a)
        claims_path = self.project / "05-runtime" / "active-claims.json"
        claims = json.loads(claims_path.read_text(encoding="utf-8"))
        claims[0]["expires_at"] = "2000-01-01T00:00:00Z"
        claims_path.write_text(json.dumps(claims), encoding="utf-8")
        report = self.call("doctor", "--root", str(self.project), expect=1)
        self.assertIn("claim_expired", {item["check"] for item in report["findings"]})


if __name__ == "__main__":
    unittest.main()
