#!/usr/bin/env python3
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path.home() / ".hermes" / "scripts"
sys.path.insert(0, str(SCRIPTS))
SCRIPT = SCRIPTS / "agent_team_controller.py"


def load_module():
    spec = importlib.util.spec_from_file_location("agent_team_controller_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeCompleted:
    def __init__(self, stdout="", returncode=0, stderr=""):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


class AgentTeamControllerSafetyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ctrl = load_module()
        self.ctrl.PROOF_DIR = Path(self.tmp.name) / "proofs"

    def tearDown(self):
        self.tmp.cleanup()

    def test_verify_with_models_rejects_non_string_worker_output_without_crashing(self):
        result = self.ctrl.verify_with_models(
            "task title",
            {"status": "done", "summary": "dict proof is not worker output text"},
            {"display_name": "Test", "acceptance": []},
        )

        self.assertFalse(result["passed"])
        self.assertEqual(result["models_checked"], 0)
        self.assertTrue(any("worker_output" in issue for issue in result["issues"]))

    def test_verify_with_models_accepts_project_name_by_loading_profile(self):
        with patch.object(self.ctrl, "load_project_profile", return_value={"display_name": "Loaded", "acceptance": []}) as load_profile:
            with patch("subprocess.run", return_value=FakeCompleted('{"verified": true, "issues": [], "reasoning": "ok"}')):
                with patch.dict("os.environ", {}, clear=True):
                    result = self.ctrl.verify_with_models("task", "worker output", "some-project")

        load_profile.assert_called_once_with("some-project")
        # Only GPT/Claude were mocked as available; DeepSeek/MiMo missing keys keep
        # the 4-model gate fail-closed rather than certifying with a partial quorum.
        self.assertFalse(result["passed"])
        self.assertEqual(result["models_checked"], 4)
        self.assertTrue(any("XIAOMI_API_KEY missing" in e for e in result.get("model_errors", [])))
        self.assertTrue(any("DEEPSEEK_API_KEY missing" in e for e in result.get("model_errors", [])))

    def test_delegate_worker_invalid_proof_falls_back_before_failing_closed(self):
        bad_output = "work happened\nPROOF_JSON: {not json}\n"
        good_output = 'done\nPROOF_JSON: {"status":"done","summary":"ok","files_changed":[],"tests_passed":0,"proof_sha":"sha256:test","acceptance_criteria_covered":[],"red_lines_status":{},"no_red_line_violations":true,"blockers":[],"evidence":["artifact:/tmp/proof.md"]}'
        with patch.object(self.ctrl, "can_continue", return_value=(False, 0)), \
             patch.object(self.ctrl, "append_trace") as append_trace, \
             patch("subprocess.run", side_effect=[FakeCompleted(bad_output), FakeCompleted(good_output)]) as run:
            result = self.ctrl.delegate_to_worker(
                {"title": "task", "id": "task-1", "project": "p", "parallel_boundary": "b"},
                "group",
                "envelope-id",
            )

        self.assertEqual(result["status"], "done")
        self.assertEqual(run.call_count, 2)
        self.assertTrue(any(call.args[1].get("event") == "proof_contract_fallback" and call.args[1].get("proof_reason") == "invalid_proof" for call in append_trace.call_args_list))

    def test_delegate_worker_missing_proof_falls_back_before_failing_closed(self):
        output = "I think this is complete but forgot the required proof."
        good_output = 'done\nPROOF_JSON: {"status":"done","summary":"ok","files_changed":[],"tests_passed":0,"proof_sha":"sha256:test","acceptance_criteria_covered":[],"red_lines_status":{},"no_red_line_violations":true,"blockers":[],"evidence":["artifact:/tmp/proof.md"]}'
        with patch.object(self.ctrl, "can_continue", return_value=(False, 0)), \
             patch.object(self.ctrl, "append_trace") as append_trace, \
             patch("subprocess.run", side_effect=[FakeCompleted(output), FakeCompleted(good_output)]) as run:
            result = self.ctrl.delegate_to_worker(
                {"title": "task", "id": "task-1", "project": "p", "parallel_boundary": "b"},
                "group",
                "envelope-id",
            )

        self.assertEqual(result["status"], "done")
        self.assertEqual(run.call_count, 2)
        self.assertTrue(any(call.args[1].get("event") == "proof_contract_fallback" and call.args[1].get("proof_reason") == "missing_proof" for call in append_trace.call_args_list))

    def test_delegate_worker_missing_proof_still_fails_closed_after_chain_exhausted(self):
        output = "I think this is complete but forgot the required proof."
        with patch.object(self.ctrl, "can_continue", return_value=(False, 0)):
            with patch("subprocess.run", return_value=FakeCompleted(output)):
                result = self.ctrl.delegate_to_worker(
                    {"title": "task", "id": "task-1", "project": "p", "parallel_boundary": "b"},
                    "group",
                    "envelope-id",
                )

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["reason"], "missing_proof")
        self.assertIn("output", result)

    def test_delegate_worker_no_output_timeout_falls_back_to_next_provider(self):
        good_output = 'done\nPROOF_JSON: {"status":"done","summary":"ok","files_changed":[],"tests_passed":0,"proof_sha":"sha256:test","acceptance_criteria_covered":[],"red_lines_status":{},"no_red_line_violations":true,"blockers":[],"evidence":["artifact:/tmp/proof.md"]}'
        timeout = subprocess.TimeoutExpired(cmd=["hermes"], timeout=1)
        with patch.object(self.ctrl, "can_continue", return_value=(False, 0)), \
             patch.object(self.ctrl, "append_trace") as append_trace, \
             patch.object(self.ctrl, "record_worker_timeout_checkpoint") as timeout_checkpoint, \
             patch("subprocess.run", side_effect=[timeout, FakeCompleted(good_output)]) as run:
            result = self.ctrl.delegate_to_worker(
                {"title": "task", "id": "task-1", "project": "p", "parallel_boundary": "b"},
                "group",
                "envelope-id",
            )

        self.assertEqual(result["status"], "done")
        self.assertEqual(run.call_count, 2)
        timeout_checkpoint.assert_not_called()
        self.assertTrue(any(call.args[1].get("event") == "provider_no_output_timeout" for call in append_trace.call_args_list))

    def test_delegate_worker_all_providers_no_output_timeout_blocks_not_requeues(self):
        def raise_timeout(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd=["hermes"], timeout=kwargs.get("timeout", 1))

        with patch.object(self.ctrl, "append_trace") as append_trace, \
             patch.object(self.ctrl, "record_worker_timeout_checkpoint") as timeout_checkpoint, \
             patch("subprocess.run", side_effect=raise_timeout) as run:
            result = self.ctrl.delegate_to_worker(
                {"title": "task", "id": "task-1", "project": "p", "parallel_boundary": "b"},
                "group",
                "envelope-id",
            )

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason"], "provider_no_output_circuit_open")
        self.assertEqual(result["infra_category"], "all_models_provider_no_output_timeout")
        self.assertEqual(run.call_count, 4)
        timeout_checkpoint.assert_not_called()
        self.assertTrue(any(call.args[1].get("event") == "provider_no_output_timeout" for call in append_trace.call_args_list))

    def test_delegate_worker_timeout_with_rate_limit_stderr_uses_infra_fallback(self):
        good_output = 'done\nPROOF_JSON: {"status":"done","summary":"ok","files_changed":[],"tests_passed":0,"proof_sha":"sha256:test","acceptance_criteria_covered":[],"red_lines_status":{},"no_red_line_violations":true,"blockers":[],"evidence":["artifact:/tmp/proof.md"]}'
        timeout = subprocess.TimeoutExpired(cmd=["hermes"], timeout=1, output="", stderr="HTTP 429: Too many requests")
        with patch.object(self.ctrl, "can_continue", return_value=(False, 0)), \
             patch.object(self.ctrl, "append_trace") as append_trace, \
             patch("subprocess.run", side_effect=[timeout, FakeCompleted(good_output)]) as run:
            result = self.ctrl.delegate_to_worker(
                {"title": "task", "id": "task-1", "project": "p", "parallel_boundary": "b"},
                "group",
                "envelope-id",
            )

        self.assertEqual(result["status"], "done")
        self.assertEqual(run.call_count, 2)
        self.assertTrue(any(call.args[1].get("event") == "timeout_infra_fallback" and call.args[1].get("infra_category") == "provider_rate_limit_or_quota" for call in append_trace.call_args_list))

    def test_uvisa_lark_worker_context_injects_acceptance_contract(self):
        self.ctrl.STATE_DIR = Path(self.tmp.name) / "state"
        task = {
            "id": "2026-05-24-lark-abc123-admin-total",
            "title": "Task - [Lark abc123] Admin 管理端业绩统计总数不正确｜work自动闭环",
            "project": "uvisa-admin",
        }
        context = self.ctrl.build_worker_context(task, "admin:data")

        self.assertIn("UVISA LARK WORK CONTRACT", context)
        self.assertIn("A-source-to-sink-equality", context)
        self.assertIn("1512x982", context)
        self.assertTrue(Path(task["uvisa_contract_path"]).exists())

    def test_handoff_artifact_carries_uvisa_contract_path(self):
        self.ctrl.STATE_DIR = Path(self.tmp.name) / "state"
        task = {
            "id": "2026-05-24-lark-def456-admin-ui",
            "title": "Task - [Lark def456] Admin 管理端筛选下拉对齐｜work自动闭环",
            "project": "uvisa-admin",
        }
        artifact = self.ctrl.build_handoff_artifact(task, "admin:ui", "env-12345678")

        self.assertIn("uvisa_lark_contract", artifact)
        self.assertTrue(Path(artifact["uvisa_lark_contract"]["contract_path"]).exists())
        self.assertEqual(artifact["safety"]["uvisa_closeout_contract_required"], True)

    def test_consume_claimed_batch_treats_max_agents_as_concurrency_not_claim_limit(self):
        rows = {
            "t1": {"id": "t1", "status": "claimed", "title": "one", "project": "proj", "parallel_boundary": "b1", "claimed_by": "hermes-parallel"},
            "t2": {"id": "t2", "status": "claimed", "title": "two", "project": "proj", "parallel_boundary": "b2", "claimed_by": "hermes-parallel"},
        }
        claimed = [{"task_id": "t1", "handoff": "/tmp/t1.md"}, {"task_id": "t2", "handoff": "/tmp/t2.md"}]
        with patch.object(self.ctrl, "is_disabled", return_value=False), \
             patch.object(self.ctrl, "human_escape_check", return_value=(False, {})), \
             patch.object(self.ctrl, "rows_by_id", return_value=rows), \
             patch.object(self.ctrl, "create", side_effect=["env-1", "env-2"]) as create, \
             patch.object(self.ctrl, "transition_task", return_value={"ok": True}) as transition, \
             patch.object(self.ctrl, "delegate_to_worker", return_value={"status": "blocked", "blockers": ["synthetic"]}) as delegate, \
             patch.object(self.ctrl, "update_status") as update_status, \
             patch.object(self.ctrl, "append_trace"):
            result = self.ctrl.consume_claimed_batch(claimed, max_agents=1)

        self.assertEqual(result["requested_count"], 2)
        self.assertEqual(result["launched_count"], 2)
        self.assertEqual(result["consumed_count"], 2)
        self.assertEqual(create.call_count, 2)
        self.assertEqual(delegate.call_count, 2)
        running = [call for call in transition.call_args_list if call.args[:2] in [("t1", "running"), ("t2", "running")]]
        self.assertEqual(len(running), 2)
        blocked = [call for call in transition.call_args_list if call.args[:2] in [("t1", "blocked"), ("t2", "blocked")]]
        self.assertEqual(len(blocked), 2)
        self.assertTrue(any(call.args[0] == "env-1" and call.args[1] == "RUNNING" for call in update_status.call_args_list))
        self.assertTrue(any(call.args[0] == "env-2" and call.args[1] == "RUNNING" for call in update_status.call_args_list))
        self.assertTrue(any(call.args[0] == "env-1" and call.args[1] == "SKIPPED" and call.kwargs.get("error") == "task_blocked_released" for call in update_status.call_args_list))
        self.assertTrue(any(call.args[0] == "env-2" and call.args[1] == "SKIPPED" and call.kwargs.get("error") == "task_blocked_released" for call in update_status.call_args_list))
        self.assertFalse(any(call.args[1] == "BLOCKED" for call in update_status.call_args_list))

    def test_consume_claimed_batch_strips_task_id_before_lookup(self):
        row = {"id": "t-strip", "status": "claimed", "title": "strip", "project": "proj", "parallel_boundary": "b", "claimed_by": "hermes-parallel"}
        with patch.object(self.ctrl, "is_disabled", return_value=False), \
             patch.object(self.ctrl, "human_escape_check", return_value=(False, {})), \
             patch.object(self.ctrl, "rows_by_id", return_value={"t-strip": row}) as rows_by_id, \
             patch.object(self.ctrl, "create", return_value="env-strip"), \
             patch.object(self.ctrl, "transition_task", return_value={"ok": True}) as transition, \
             patch.object(self.ctrl, "delegate_to_worker", return_value={"status": "blocked", "blockers": ["synthetic"]}), \
             patch.object(self.ctrl, "update_status"), \
             patch.object(self.ctrl, "append_trace"):
            result = self.ctrl.consume_claimed_batch([{"task_id": "t-strip\n"}], max_agents=1)

        rows_by_id.assert_called_with(["t-strip"])
        self.assertEqual(result["launched_count"], 1)
        self.assertTrue(any(call.args[:2] == ("t-strip", "running") for call in transition.call_args_list))

    def test_process_worker_result_failed_requeues_brain_task_not_false_running(self):
        row = {"id": "t-failed", "status": "running", "title": "failed", "project": "proj"}
        with patch.object(self.ctrl, "transition_task", return_value={"ok": True}) as transition, \
             patch.object(self.ctrl, "update_status") as update_status:
            result = self.ctrl._process_worker_result(
                row,
                "hermes-parallel",
                "env-failed",
                {"status": "failed", "reason": "missing_proof", "output": "no proof"},
            )

        self.assertEqual(result["to_status"], "retry")
        transition.assert_called_once()
        self.assertEqual(transition.call_args.args[:2], ("t-failed", "retry"))
        self.assertTrue(any(call.args[0] == "env-failed" and call.args[1] == "FAILED" for call in update_status.call_args_list))

    def test_process_worker_result_blocked_blocks_brain_task_not_false_running(self):
        row = {"id": "t-blocked", "status": "running", "title": "blocked", "project": "proj"}
        with patch.object(self.ctrl, "transition_task", return_value={"ok": True}) as transition, \
             patch.object(self.ctrl, "update_status") as update_status:
            result = self.ctrl._process_worker_result(
                row,
                "hermes-parallel",
                "env-blocked",
                {"status": "blocked", "output": "BLOCKED: needs auth"},
            )

        self.assertEqual(result["to_status"], "blocked")
        self.assertEqual(result["envelope_status"], "SKIPPED")
        transition.assert_called_once()
        self.assertEqual(transition.call_args.args[:2], ("t-blocked", "blocked"))
        self.assertTrue(any(call.args[0] == "env-blocked" and call.args[1] == "SKIPPED" and call.kwargs.get("error") == "task_blocked_released" for call in update_status.call_args_list))
        self.assertFalse(any(call.args[0] == "env-blocked" and call.args[1] == "BLOCKED" for call in update_status.call_args_list))

    def test_consume_claimed_batch_late_timeout_does_not_demote_review(self):
        claimed_row = {"id": "t-late", "status": "claimed", "title": "late", "project": "proj", "parallel_boundary": "b", "claimed_by": "hermes-parallel"}
        reviewed_row = dict(claimed_row, status="review")
        claimed = [{"task_id": "t-late", "handoff": "/tmp/t-late.md"}]
        with patch.object(self.ctrl, "is_disabled", return_value=False), \
             patch.object(self.ctrl, "human_escape_check", return_value=(False, {})), \
             patch.object(self.ctrl, "rows_by_id", side_effect=[{"t-late": claimed_row}, {"t-late": reviewed_row}]), \
             patch.object(self.ctrl, "create", return_value="env-late"), \
             patch.object(self.ctrl, "transition_task", return_value={"ok": True}) as transition, \
             patch.object(self.ctrl, "delegate_to_worker", return_value={"status": "timeout"}), \
             patch.object(self.ctrl, "update_status") as update_status, \
             patch.object(self.ctrl, "append_trace"):
            result = self.ctrl.consume_claimed_batch(claimed, max_agents=1)

        self.assertEqual(result["claimed"][0]["to_status"], "review")
        running = [call for call in transition.call_args_list if call.args[:2] == ("t-late", "running")]
        retry = [call for call in transition.call_args_list if call.args[:2] == ("t-late", "retry")]
        self.assertEqual(len(running), 1)
        self.assertEqual(len(retry), 0)
        self.assertTrue(any(call.args[0] == "env-late" and call.args[1] == "SKIPPED" and "worker_result_ignored_current_status_review" in str(call.kwargs.get("error", "")) for call in update_status.call_args_list))

    def test_consume_claimed_batch_stale_claim_transition_is_skipped_not_failed(self):
        row = {"id": "t-stale", "status": "claimed", "title": "stale", "project": "proj", "parallel_boundary": "b", "claimed_by": "agent-team-controller"}
        running_error = {
            "ok": False,
            "error": "claim-bound status requires claimed_by, run_id, and a valid non-expired claim_expires_at before transition; task claim is stale",
        }

        def fake_transition(task_id, to_status, actor, reason, evidence=None, ttl=60, force=False):
            if to_status == "running":
                return running_error
            if to_status == "retry" and force:
                return {"ok": True, "data": {"status": "OK"}}
            return {"ok": False, "error": "unexpected"}

        with patch.object(self.ctrl, "is_disabled", return_value=False), \
             patch.object(self.ctrl, "human_escape_check", return_value=(False, {})), \
             patch.object(self.ctrl, "rows_by_id", return_value={"t-stale": row}), \
             patch.object(self.ctrl, "create", return_value="env-stale"), \
             patch.object(self.ctrl, "transition_task", side_effect=fake_transition) as transition, \
             patch.object(self.ctrl, "delegate_to_worker") as delegate, \
             patch.object(self.ctrl, "update_status") as update_status, \
             patch.object(self.ctrl, "append_trace"):
            result = self.ctrl.consume_claimed_batch([{"task_id": "t-stale"}], max_agents=1)

        self.assertEqual(result["launched_count"], 0)
        self.assertEqual(result["skipped"][0]["reason"], "stale_claim_running_transition_released")
        delegate.assert_not_called()
        retry_calls = [call for call in transition.call_args_list if call.args[:2] == ("t-stale", "retry")]
        self.assertEqual(len(retry_calls), 1)
        self.assertTrue(retry_calls[0].kwargs.get("force"))
        self.assertTrue(any(call.args[0] == "env-stale" and call.args[1] == "SKIPPED" and call.kwargs.get("error") == "stale_claim_running_transition_skipped" for call in update_status.call_args_list))
        self.assertFalse(any(call.args[0] == "env-stale" and call.args[1] == "FAILED" for call in update_status.call_args_list))

    def test_workspace_path_is_collision_resistant_for_same_cjk_prefix(self):
        first = "2026-06-02-评估-anthropic-harness-design"
        second = "2026-06-02-评估-moso-毛竹"

        p1 = self.ctrl._workspace_path(first)
        p2 = self.ctrl._workspace_path(second)

        self.assertNotEqual(p1, p2)
        self.assertTrue(str(p1).startswith("/tmp/agent-team-"))
        self.assertTrue(str(p2).startswith("/tmp/agent-team-"))
        # The historical bug used this colliding prefix for both ids.
        self.assertNotEqual(str(p1), "/tmp/agent-team-2026-06-02-评")
        self.assertNotEqual(str(p2), "/tmp/agent-team-2026-06-02-评")

    def test_verify_workspace_ready_creates_unique_writable_workspace(self):
        task_id = "2026-06-02-评估-workspace-smoke"
        ok, path, err = self.ctrl._verify_workspace_ready(task_id)

        self.assertTrue(ok, err)
        self.assertTrue(Path(path).is_dir())
        self.assertIn(self.ctrl._workspace_path(task_id).name, path)
        self.ctrl.cleanup_worktree(task_id)
        self.assertFalse(Path(path).exists())

    def test_detect_infra_failure_recognizes_generic_provider_429(self):
        is_infra, category = self.ctrl._detect_infra_failure(
            "API call failed after 3 retries: HTTP 429: Too many requests"
        )
        self.assertTrue(is_infra)
        self.assertEqual(category, "provider_rate_limit_or_quota")

    def test_collect_proof_accepts_multiline_proof_json(self):
        output = '''analysis text
PROOF_JSON: {
  "status": "done",
  "summary": "ok",
  "files_changed": [],
  "tests_passed": 0,
  "proof_sha": "sha256:test",
  "acceptance_criteria_covered": [{"criterion":"Observable result is recorded in Proof Log.","status":"covered","evidence":["artifact:/tmp/proof.md"]}],
  "red_lines_status": {"do not weaken taskpool proof": "safe"},
  "no_red_line_violations": true,
  "blockers": [],
  "evidence": ["artifact:/tmp/proof.md"]
}
'''
        proof = self.ctrl.collect_proof('unit-test-multiline-proof', output)
        self.assertIsInstance(proof, dict)
        self.assertEqual(proof.get('status'), 'done')
        self.assertEqual(proof.get('summary'), 'ok')

if __name__ == "__main__":
    unittest.main()
