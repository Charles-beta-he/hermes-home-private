#!/usr/bin/env python3
"""Tests for local_brain_change_preflight.py dry-run constraint gate."""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parent / "local_brain_change_preflight.py"
spec = importlib.util.spec_from_file_location("local_brain_change_preflight", SCRIPT)
preflight = importlib.util.module_from_spec(spec)
sys.modules["local_brain_change_preflight"] = preflight
spec.loader.exec_module(preflight)


class LocalBrainChangePreflightTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.default_vault = self.root / "default-brain"
        self.notes_vault = self.root / "notes-brain"
        self.default_vault.mkdir()
        self.notes_vault.mkdir()
        self.memory_root = self.root / "memory"
        self.memory_root.mkdir()
        self.write_note(
            self.default_vault,
            "05-实践与项目/projects/Old/旧项目经验.md",
            "---\nstatus: stale\n---\n\n# 旧项目经验\n\n本地大脑全量自动约束层 RouteReviewGate without tests。旧结论，completed without tests。\n",
        )
        self.write_note(
            self.notes_vault,
            "05-实践与项目/实践方案/12-本地大脑全量自动约束层长期方案.md",
            "---\nstatus: active-stable\nstability_class: long_term_canonical_plan\n---\n\n# 本地大脑全量自动约束层最终长期稳定方案\n\nCurrent source: RouteReviewGate BrainConstraintRecord route_required_evidence。\n\nHEWOS hermes embodied workflow os workbench runtime uses the same local deterministic evidence gate for scoped architecture/code/docs commits.\n",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def write_note(self, vault: Path, rel: str, text: str) -> Path:
        path = vault / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_preflight_searches_multiple_vaults_and_prefers_current_canonical_knowledge(self):
        result = preflight.run_preflight(
            summary="强化本地大脑全量自动约束层 RouteReviewGate",
            files=["scripts/local_brain_change_preflight.py"],
            vaults=[self.default_vault, self.notes_vault],
            memory_root=self.memory_root,
            evidence=["test:fixture"],
            limit=5,
        )

        self.assertEqual(result["schema"], "local_brain_change_preflight_v1")
        record = result["brain_constraint_record"]
        accepted_paths = {hit["path"] for hit in record["retrieval"]["accepted_hits"]}
        filtered_paths = {hit["path"] for hit in record["retrieval"]["filtered_hits"]}
        self.assertIn("05-实践与项目/实践方案/12-本地大脑全量自动约束层长期方案.md", accepted_paths)
        self.assertIn("05-实践与项目/projects/Old/旧项目经验.md", filtered_paths)
        self.assertEqual(record["routing"]["route_review_ref"], "embedded:route_review_record")
        self.assertIn("route_required_evidence", record["routing"])

    def test_t3_lifecycle_change_without_evidence_degrades_not_certified_and_blocks(self):
        result = preflight.run_preflight(
            summary="修改 taskpool lifecycle done transition runtime hard gate",
            files=["scripts/taskpool_lifecycle.py"],
            vaults=[self.notes_vault],
            memory_root=self.memory_root,
            evidence=[],
            limit=5,
        )

        route = result["route_review_record"]
        verdict = result["brain_constraint_record"]["verdict"]
        self.assertEqual(route["classification"]["risk_tier"], "T3")
        self.assertEqual(route["verdict"]["status"], "degraded_not_certified")
        self.assertFalse(route["verdict"]["certified"])
        self.assertEqual(verdict["status"], "block")
        self.assertIn("missing_required_evidence", verdict["reasons"])

    def test_lark_skill_reference_docs_are_local_write_not_external_dispatch(self):
        route = preflight.build_route_review_record(
            summary="git pre-commit staged files: skills/software-development/lark-task-reading/SKILL.md, skills/software-development/lark-task-reading/references/lark-task-comment-complete-closeout.md",
            files=[
                "skills/software-development/lark-task-reading/SKILL.md",
                "skills/software-development/lark-task-reading/references/lark-task-comment-complete-closeout.md",
            ],
            evidence=[
                "file_readback:skill reference read back",
                "exact_target:local git repository staged files only",
                "rollback:git reset staged changes or git revert resulting commit",
                "post_action_readback:hook readback",
            ],
        )

        self.assertEqual(route["classification"]["side_effect_class"], "local_write")
        self.assertEqual(route["classification"]["risk_tier"], "T1")
        self.assertEqual(route["verdict"]["status"], "pass")

    def test_gateway_code_path_still_classifies_as_external_dispatch(self):
        route = preflight.build_route_review_record(
            summary="git pre-commit staged files: gateway/platforms/feishu.py",
            files=["gateway/platforms/feishu.py"],
            evidence=[],
        )

        self.assertEqual(route["classification"]["side_effect_class"], "external_dispatch")
        self.assertEqual(route["classification"]["risk_tier"], "T3")

    def test_t3_precommit_with_full_deterministic_evidence_gets_local_certification_not_multimodel(self):
        evidence = [
            "diff:git diff --cached --name-only readback",
            "tests:targeted local-brain pre-commit tests OK",
            "py_compile_or_build:staged python py_compile OK",
            "search_output:brainctl preflight performs search",
            "fixture_replay:pre-commit hook smoke",
            "reindex_readback:brainctl preflight performs reindex",
            "task_record:local git staged taskpool change record includes exact touched files and rollback target",
            "proof_log:targeted taskpool regression tests and py_compile completed under pre-commit hook",
            "lifecycle_readback:focused tests cover fail-closed eligibility, claim precheck, review close gating, cron wrapper dedupe, and no force-done path",
            "deterministic_gate:pre-commit local deterministic checks completed",
            "route_review_record:embedded RouteReviewRecord emitted",
            "exact_target:local git repository staged files only",
            "rollback:git reset staged changes or git revert resulting commit",
            "post_action_readback:pre-commit hook exits zero only after local preflight verdict is non-blocking",
        ]
        result = preflight.run_preflight(
            summary="git pre-commit staged files: scripts/brain_task_autorun_step.py, scripts/taskpool_dynamic_runner_cron.py",
            files=["scripts/brain_task_autorun_step.py", "scripts/taskpool_dynamic_runner_cron.py"],
            vaults=[self.notes_vault],
            memory_root=self.memory_root,
            evidence=evidence,
            limit=5,
        )

        route = result["route_review_record"]
        verdict = result["brain_constraint_record"]["verdict"]
        self.assertEqual(route["classification"]["risk_tier"], "T3")
        self.assertEqual(route["evidence_state"]["missing_evidence"], [])
        self.assertEqual(route["verdict"]["status"], "local_deterministic_certified")
        self.assertTrue(route["verdict"]["certified"])
        self.assertFalse(route["verdict"]["multi_model_certified"])
        self.assertEqual(verdict["status"], "pass")
        self.assertNotIn("degraded_not_certified", verdict["reasons"])
    def test_t3_architecture_runtime_with_full_deterministic_evidence_gets_local_certification(self):
        evidence = [
            "diff:git diff --cached --name-only readback",
            "tests:HEWOS workbench runtime tests OK",
            "py_compile_or_build:staged python py_compile OK",
            "design_doc:staged architecture/profile docs are the scoped design document",
            "gate_readback:local pre-commit BrainConstraintGate reads staged files and evidence labels",
            "deterministic_gate:pre-commit local deterministic checks completed",
            "route_review_record:embedded RouteReviewRecord emitted",
            "exact_target:local git repository staged files only",
            "rollback:git reset staged changes or git revert resulting commit",
            "post_action_readback:pre-commit hook exits zero only after local preflight verdict is non-blocking",
        ]
        result = preflight.run_preflight(
            summary="git pre-commit staged files: project-profiles/hermes-embodied-workflow-os.json, workflows/projects/hermes-embodied-workflow-os/implementation/hewos_core/workbench_runtime.py",
            files=[
                "project-profiles/hermes-embodied-workflow-os.json",
                "workflows/projects/hermes-embodied-workflow-os/implementation/hewos_core/workbench_runtime.py",
            ],
            vaults=[self.notes_vault],
            memory_root=self.memory_root,
            evidence=evidence,
            limit=5,
        )

        route = result["route_review_record"]
        verdict = result["brain_constraint_record"]["verdict"]
        self.assertEqual(route["evidence_state"]["missing_evidence"], [])
        self.assertEqual(route["verdict"]["status"], "local_deterministic_certified")
        self.assertEqual(verdict["status"], "pass")

    def test_python_control_plane_with_required_fields_does_not_trigger_ui_visual_evidence(self):
        route = preflight.build_route_review_record(
            summary="git pre-commit staged files: workflows/projects/hermes-agent-os-control-plane/12-personal-ai-os/personal_ai_os_control.py",
            files=["workflows/projects/hermes-agent-os-control-plane/12-personal-ai-os/personal_ai_os_control.py"],
            evidence=[
                "diff:git diff --cached --name-only readback",
                "tests:read-only control surface smoke OK",
                "py_compile_or_build:staged python py_compile OK",
                "file_readback:control script read back",
                "exact_target:local git repository staged files only",
                "rollback:git reset staged changes or git revert resulting commit",
                "post_action_readback:control command exits zero",
            ],
        )

        self.assertNotIn("ui_visual", route["classification"]["surfaces"])
        self.assertNotIn("screenshot", route["evidence_state"]["required_evidence"])
        self.assertNotIn("browser_console", route["evidence_state"]["required_evidence"])


    def test_personal_ai_os_packet_mission_projection_is_local_write_not_lifecycle(self):
        route = preflight.build_route_review_record(
            summary="git pre-commit staged files: workflows/projects/hermes-agent-os-control-plane/12-personal-ai-os/13-mission-runtime-state.json, workflows/projects/hermes-agent-os-control-plane/12-personal-ai-os/build_mission_runtime_state.py",
            files=[
                "workflows/projects/hermes-agent-os-control-plane/12-personal-ai-os/13-mission-runtime-state.json",
                "workflows/projects/hermes-agent-os-control-plane/12-personal-ai-os/build_mission_runtime_state.py",
            ],
            evidence=[
                "diff:git diff --cached --name-only readback",
                "tests:projection smoke OK",
                "py_compile_or_build:staged python py_compile OK",
                "design_doc:staged packet files are scoped design/projection docs",
                "gate_readback:doctor/status readback OK",
                "file_readback:mission runtime state read back",
                "exact_target:local git repository staged files only",
                "rollback:git reset staged changes or git revert resulting commit",
                "post_action_readback:control command exits zero",
            ],
        )

        self.assertEqual(route["classification"]["side_effect_class"], "local_write")
        self.assertNotIn("task_record", route["evidence_state"]["required_evidence"])
        self.assertNotIn("proof_log", route["evidence_state"]["required_evidence"])
        self.assertNotIn("lifecycle_readback", route["evidence_state"]["required_evidence"])

    def test_cli_json_emits_parseable_record_and_never_executes_side_effects(self):
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--summary",
                "本地大脑全量自动约束层 RouteReviewGate dry-run",
                "--file",
                "scripts/local_brain_change_preflight.py",
                "--vault",
                str(self.notes_vault),
                "--memory-root",
                str(self.memory_root),
                "--evidence",
                "test:fixture",
                "--json",
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertTrue(data["dry_run"])
        self.assertEqual(data["side_effects"]["external_dispatch"], False)
        self.assertEqual(data["side_effects"]["lifecycle_write"], False)
        self.assertIn("brain_constraint_record", data)
        self.assertIn("route_review_record", data)


if __name__ == "__main__":
    unittest.main()
