#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path('/Users/charles/.hermes/workflows/workflow-kernel-loop')
CORE = ROOT / 'core' / 'four_core_kernels.py'


def load_core():
    spec = importlib.util.spec_from_file_location('four_core_kernels', CORE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FourCoreKernelDecouplingTests(unittest.TestCase):
    def setUp(self):
        self.core = load_core()

    def test_intent_normalizer_has_stable_seed_and_no_persistence_effect(self):
        seed = self.core.normalize_intent('固化意图归一化模块，禁止外部执行和memory污染')
        self.assertEqual(seed['schema'], 'hermes_four_core_kernel_workflow_seed_v1')
        self.assertIn('do not persist to memory/skill/project state from normalization', seed['non_goals'])
        self.assertEqual(seed['authority_boundary'], 'local_only')
        self.assertEqual(seed['expected_artifact'], 'reusable_kernel_candidate')

    def test_landing_zone_routes_reusable_kernel_to_skill_or_workflow_candidate(self):
        seed = self.core.normalize_intent('固化四个内核模块')
        landing = self.core.classify_landing_zone(seed, [{'claim': '四个内核模块可复用流程', 'scope': 'workflow-kernel-loop'}])
        row = landing['decisions'][0]
        self.assertEqual(row['target'], 'skill_or_workflow_candidate')
        self.assertIn('global_memory_body', row['forbidden_targets'])

    def test_landing_zone_keeps_progress_out_of_global_memory_and_skill(self):
        seed = self.core.normalize_intent('记录这个PR已完成')
        landing = self.core.classify_landing_zone(seed, [{'claim': 'PR 123 已完成', 'scope': 'project'}])
        row = landing['decisions'][0]
        self.assertEqual(row['target'], 'session_or_project_progress_only')
        self.assertIn('global_memory', row['forbidden_targets'])
        self.assertIn('global_skill', row['forbidden_targets'])

    def test_authority_gate_fails_closed_for_external_write_without_exact_grant(self):
        decision = self.core.authority_evidence_gate('send message', 'telegram:abc', 'external_write', {})
        self.assertEqual(decision['status'], 'needs_exact_authority')
        self.assertTrue(decision['required_receipt'])
        self.assertTrue(decision['required_readback'])

    def test_authority_gate_allows_local_write_but_not_completion_without_readback(self):
        decision = self.core.authority_evidence_gate('write local candidate', 'workflow-kernel-loop', 'local_write', {})
        self.assertEqual(decision['status'], 'allowed')
        self.assertTrue(decision['evidence_contract']['fresh_current_task_evidence_required'])
        self.assertTrue(decision['evidence_contract']['command_or_api_exit_is_not_enough'])

    def test_lifecycle_promotes_one_step_only_with_quality_and_cleanup_evidence(self):
        transition = self.core.lifecycle_transition(
            'four_core_kernel_candidate',
            'candidate',
            [{'status': 'PASS'}, {'status': 'PASS'}, {'status': 'PASS'}],
            {'false_trigger_count': 0, 'neighbor_collision_count': 0, 'cleanup_policy_exists': True, 'negative_cases_pass': True},
        )
        self.assertEqual(transition['action'], 'promote_one_step')
        self.assertEqual(transition['next_maturity'], 'validated')
        self.assertIn('never_promote_to_canonical_from_one_local_success', transition['canonical_guard'])

    def test_lifecycle_quarantines_false_trigger_before_promotion(self):
        transition = self.core.lifecycle_transition(
            'four_core_kernel_candidate',
            'candidate',
            [{'status': 'PASS'}, {'status': 'PASS'}, {'status': 'PASS'}],
            {'false_trigger_count': 1, 'neighbor_collision_count': 0, 'cleanup_policy_exists': True, 'negative_cases_pass': True},
        )
        self.assertEqual(transition['action'], 'quarantine')
        self.assertEqual(transition['next_maturity'], 'quarantined')

    def test_pipeline_is_decoupled_local_only_and_cli_readback_writes_only_requested_output(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / 'receipt.json'
            cmd = [sys.executable, str(CORE), '--seed', 'loop推进四个内核解耦完成', '--out', str(out)]
            proc = subprocess.run(cmd, text=True, capture_output=True, timeout=30)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            data = json.loads(out.read_text(encoding='utf-8'))
            self.assertEqual(data['schema'], 'hermes_four_core_kernel_pipeline_receipt_v1')
            self.assertEqual(data['authority_evidence']['status'], 'allowed')
            self.assertIn('local_transform_only', data['side_effect_boundary'])

    def test_cli_blocks_external_write_without_grant(self):
        cmd = [sys.executable, str(CORE), '--seed', '发送到外部', '--side-effect-class', 'external_write']
        proc = subprocess.run(cmd, text=True, capture_output=True, timeout=30)
        self.assertEqual(proc.returncode, 1)
        data = json.loads(proc.stdout)
        self.assertEqual(data['status'], 'blocked_or_waiting_authority')
        self.assertEqual(data['authority_evidence']['status'], 'needs_exact_authority')


if __name__ == '__main__':
    unittest.main()
