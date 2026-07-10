#!/usr/bin/env python3
"""Tests for local_brain_precommit_hook.py."""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parent / "local_brain_precommit_hook.py"
spec = importlib.util.spec_from_file_location("local_brain_precommit_hook", SCRIPT)
hook = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(hook)


class LocalBrainPrecommitHookTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init"], cwd=self.repo, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_install_writes_enabled_pre_commit_hook(self):
        result = hook.install(self.repo)
        self.assertTrue(result["ok"])
        self.assertTrue(result["enabled"])
        hook_path = Path(result["hook"])
        self.assertTrue(hook_path.exists())
        self.assertIn("local_brain_precommit_hook.py", hook_path.read_text(encoding="utf-8"))
        status = hook.status(self.repo)
        self.assertTrue(status["enabled"])

    def test_cli_status_json_is_parseable(self):
        hook.install(self.repo)
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--status", "--repo", str(self.repo), "--json"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertTrue(data["enabled"])

    def test_taskpool_files_collect_taskpool_tests_and_evidence(self):
        files = [
            "scripts/brain_task_autorun_step.py",
            "scripts/taskpool_dynamic_runner_cron.py",
        ]
        tests = [path.name for path in hook.relevant_tests(files)]
        self.assertIn("test_brain_task_autorun_step.py", tests)
        self.assertIn("test_brain_task_dispatch_tick.py", tests)
        self.assertIn("test_task_pool_guardian.py", tests)
        self.assertIn("test_task_pool_guardian_silent.py", tests)
        self.assertIn("test_taskpool_dynamic_runner_cron.py", tests)

        calls = []
        old_run = hook.run
        try:
            def fake_run(cmd, *, cwd=None, timeout=180):
                calls.append(list(cmd))
                return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
            hook.run = fake_run
            evidence, errors = hook.hook_evidence(self.repo, files)
        finally:
            hook.run = old_run

        self.assertEqual(errors, [])
        joined = "\n".join(evidence)
        self.assertIn("task_record:", joined)
        self.assertIn("proof_log:", joined)
        self.assertIn("lifecycle_readback:", joined)
        self.assertTrue(any("test_brain_task_autorun_step.py" in " ".join(call) for call in calls))

    def test_consult_models_and_taskpool_skill_collect_taskpool_evidence(self):
        files = [
            "scripts/consult_models.py",
            "skills/software-development/taskpool-runtime-reconciliation/SKILL.md",
        ]
        self.assertTrue(hook.is_taskpool_control_plane_change(files))

        old_run = hook.run
        try:
            def fake_run(cmd, *, cwd=None, timeout=180):
                return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
            hook.run = fake_run
            evidence, errors = hook.hook_evidence(self.repo, files)
        finally:
            hook.run = old_run

        self.assertEqual(errors, [])
        joined = "\n".join(evidence)
        self.assertIn("task_record:", joined)
        self.assertIn("proof_log:", joined)
        self.assertIn("lifecycle_readback:", joined)

    def test_procedure_governance_files_collect_exact_tests_and_t3_evidence(self):
        files = [
            "scripts/dynamic_selfcheck_coverage.py",
            "scripts/lark_oauth_guard.py",
            "scripts/lark_task_flow.py",
            "scripts/experience_ratchet_lifecycle.py",
            "scripts/procedure_rehearsals.py",
            "scripts/workflow_kernel_loop_v2.py",
            "scripts/workflow_loop_evaluator.py",
            "scripts/workflow_validation_registry.py",
            "workflows/projects/hermes-agent-os-control-plane/14-workflow-loop-engineering-coverage/procedure-definitions.json",
        ]
        self.assertTrue(hook.is_procedure_governance_change(files))
        tests = {path.name for path in hook.relevant_tests(files)}
        self.assertEqual(
            tests,
            {
                "test_dynamic_selfcheck_coverage.py",
                "test_lark_oauth_guard.py",
                "test_lark_task_flow.py",
                "test_experience_ratchet_lifecycle.py",
                "test_procedure_rehearsals.py",
                "test_workflow_kernel_loop.py",
                "test_workflow_loop_evaluator.py",
                "test_workflow_validation_registry.py",
            },
        )

        old_run = hook.run
        try:
            def fake_run(cmd, *, cwd=None, timeout=180):
                return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
            hook.run = fake_run
            evidence, errors = hook.hook_evidence(self.repo, files)
        finally:
            hook.run = old_run

        self.assertEqual(errors, [])
        joined = "\n".join(evidence)
        for label in ("design_doc:", "gate_readback:", "task_record:", "proof_log:", "lifecycle_readback:"):
            self.assertIn(label, joined)
        self.assertIn("tests:targeted procedure-governance tests OK", joined)

    def test_architecture_and_research_project_files_collect_design_and_source_evidence(self):
        files = [
            "project-profiles/hermes-embodied-workflow-os.json",
            "workflows/projects/hermes-embodied-workflow-os/01-architecture/stable-core-and-adapter-architecture.md",
            "workflows/projects/hermes-embodied-workflow-os/02-research/competitor-source-samples-20260702.json",
            "workflows/projects/hermes-embodied-workflow-os/07-product/workflow-state.yaml.md",
        ]
        old_run = hook.run
        try:
            def fake_run(cmd, *, cwd=None, timeout=180):
                return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
            hook.run = fake_run
            evidence, errors = hook.hook_evidence(self.repo, files)
        finally:
            hook.run = old_run

        self.assertEqual(errors, [])
        joined = "\n".join(evidence)
        self.assertIn("design_doc:", joined)
        self.assertIn("gate_readback:", joined)
        self.assertIn("source_packet:", joined)
        self.assertIn("timestamped_source:", joined)
    def test_hewos_implementation_files_collect_project_test_evidence(self):
        files = [
            "workflows/projects/hermes-embodied-workflow-os/implementation/hewos_core/workbench_runtime.py",
            "workflows/projects/hermes-embodied-workflow-os/implementation/tests/test_workbench_runtime.py",
        ]
        old_run = hook.run
        try:
            def fake_run(cmd, *, cwd=None, timeout=180):
                return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
            hook.run = fake_run
            evidence, errors = hook.hook_evidence(self.repo, files)
        finally:
            hook.run = old_run

        self.assertEqual(errors, [])
        joined = "\n".join(evidence)
        self.assertIn("tests:HEWOS implementation unittest suite OK", joined)
    def test_authority_ledger_files_collect_authority_and_readback_evidence(self):
        files = [
            "workflows/projects/hermes-agent-os-control-plane/12-personal-ai-os/11-authority-ledger-projection.jsonl",
            "workflows/projects/hermes-agent-os-control-plane/12-personal-ai-os/11-authority-ledger-report.json",
            "workflows/projects/hermes-agent-os-control-plane/12-personal-ai-os/06-non-human-interface-boundary.md",
        ]
        evidence, errors = hook.hook_evidence(self.repo, files)

        self.assertEqual(errors, [])
        joined = "\n".join(evidence)
        self.assertIn("authority:", joined)
        self.assertIn("readback:", joined)

    def test_uimax_visual_files_collect_screenshot_and_console_evidence(self):
        files = [
            "workflows/projects/hermes-embodied-workflow-os/06-verification/UIMAX_REPORT_20260702.md",
            "workflows/projects/hermes-embodied-workflow-os/06-verification/uimax-metrics-20260702.json",
            "workflows/projects/hermes-embodied-workflow-os/artifacts/workbench-static-fixture.html",
            "workflows/projects/hermes-embodied-workflow-os/implementation/hewos_core/workbench_static.py",
            "workflows/projects/hermes-embodied-workflow-os/implementation/tests/test_workbench_uimax_static.py",
        ]
        old_run = hook.run
        try:
            def fake_run(cmd, *, cwd=None, timeout=180):
                return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
            hook.run = fake_run
            evidence, errors = hook.hook_evidence(self.repo, files)
        finally:
            hook.run = old_run

        self.assertEqual(errors, [])
        joined = "\n".join(evidence)
        self.assertIn("screenshot:", joined)
        self.assertIn("browser_console:", joined)
        self.assertIn("tests:HEWOS implementation unittest suite OK", joined)

    def test_browser_readback_artifacts_collect_screenshot_and_console_evidence(self):
        files = [
            "workflows/projects/hermes-fitness-posture-coach/04-implementation/data/derived/review_ui_browser_readback.json",
            "workflows/projects/hermes-fitness-posture-coach/04-implementation/ui/review.html",
        ]
        evidence, errors = hook.hook_evidence(self.repo, files)

        self.assertEqual(errors, [])
        joined = "\n".join(evidence)
        self.assertIn("screenshot:", joined)
        self.assertIn("browser_console:", joined)


if __name__ == "__main__":
    unittest.main()
