#!/usr/bin/env python3
"""Integration tests for consult_models.py planner dispatch logic."""

import importlib.util
import json
import os
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parent / "consult_models.py"
spec = importlib.util.spec_from_file_location("consult_models", SCRIPT)
consult = importlib.util.module_from_spec(spec)
spec.loader.exec_module(consult)


class TestConsultModelsIntegration(unittest.TestCase):
    def test_model_provider_resolves_gpt55(self):
        """model_provider() should resolve gpt-5.5 to openai-codex"""
        config = {"pricing": {"models": {"gpt-5.5": {"provider": "openai-codex"}}}}
        result = consult.model_provider(config, "gpt-5.5")
        self.assertEqual(result, "openai-codex")

    def test_model_provider_resolves_mimo(self):
        """model_provider() should resolve mimo-v2.5-pro to xiaomi"""
        config = {"pricing": {"models": {"mimo-v2.5-pro": {"provider": "xiaomi"}}}}
        result = consult.model_provider(config, "mimo-v2.5-pro")
        self.assertEqual(result, "xiaomi")

    def test_model_provider_unknown_returns_empty(self):
        """model_provider() returns '' for unknown model"""
        config = {"pricing": {"models": {}}}
        result = consult.model_provider(config, "unknown-model")
        self.assertEqual(result, "")

    def test_quorum_config_loads(self):
        """quorum.yaml should load with multi_brain enabled"""
        quorum_path = Path(os.path.expanduser("~/.hermes/config/quorum.yaml"))
        if not quorum_path.exists():
            self.skipTest("quorum.yaml not found")
        import yaml
        with open(quorum_path) as f:
            q = yaml.safe_load(f)
        self.assertIn("multi_brain", q)
        self.assertTrue(q["multi_brain"].get("enabled", False))
        self.assertIn("T1", q.get("tiers", {}))

    def test_quorum_t1_has_two_planners(self):
        """T1 should have at least 2 planners for diversity"""
        quorum_path = Path(os.path.expanduser("~/.hermes/config/quorum.yaml"))
        if not quorum_path.exists():
            self.skipTest("quorum.yaml not found")
        import yaml
        with open(quorum_path) as f:
            q = yaml.safe_load(f)
        t1_planners = q.get("tiers", {}).get("T1", {}).get("planners", [])
        self.assertGreaterEqual(len(t1_planners), 2, f"T1 planners={t1_planners}, need >= 2")

    def test_quorum_t1_min_quorum_requires_two_models(self):
        """T1 should not certify with only one successful planner"""
        quorum_path = Path(os.path.expanduser("~/.hermes/config/quorum.yaml"))
        if not quorum_path.exists():
            self.skipTest("quorum.yaml not found")
        import yaml
        with open(quorum_path) as f:
            q = yaml.safe_load(f)
        t1 = q.get("tiers", {}).get("T1", {})
        self.assertGreaterEqual(t1.get("min_quorum", 0), 2, f"T1 min_quorum={t1.get('min_quorum')}, need >= 2")

    def test_fanout_below_min_quorum_is_degraded_not_certified(self):
        """A fan-out below min_quorum should be auditable as degraded_not_certified."""
        status = consult.fanout_certification_status(success_count=1, planner_count=3, min_quorum=2, fail_count=2)
        self.assertEqual(status["status"], "degraded_not_certified")
        self.assertFalse(status["certified"])
        self.assertTrue(status["below_min_quorum"])
        self.assertIn("reason", status)
        self.assertIn("below min_quorum", status["reason"])

    def test_fanout_single_planner_is_not_multi_model_certified(self):
        """T0/single-planner fan-out can be useful, but must not claim multi-model certification."""
        status = consult.fanout_certification_status(success_count=1, planner_count=1, min_quorum=1, fail_count=0)
        self.assertEqual(status["status"], "single_model_quorum_met")
        self.assertTrue(status["certified"])
        self.assertFalse(status["multi_model_certified"])
        self.assertEqual(status["certification_scope"], "single_model")
        self.assertIn("single planner", status["reason"])

    def test_fanout_certification_status_has_schema_required_fields(self):
        """Fan-out certification objects should be schema-checkable before artifact write."""
        status = consult.fanout_certification_status(success_count=2, planner_count=3, min_quorum=2, fail_count=1)
        ok, errors = consult.validate_fanout_certification_status(status)
        self.assertTrue(ok, errors)
        for key in (
            "schema_version", "status", "certified", "multi_model_certified",
            "certification_scope", "below_min_quorum", "success_count", "fail_count",
            "planner_count", "min_quorum", "reason",
        ):
            self.assertIn(key, status)

    def test_fanout_certification_schema_file_is_parseable(self):
        """The operational JSON schema for fanout_certification should exist and match code constants."""
        schema_path = Path(os.path.expanduser("~/.hermes/schemas/fanout-certification.schema.json"))
        self.assertTrue(schema_path.exists(), f"missing schema file: {schema_path}")
        schema = json.loads(schema_path.read_text())
        self.assertEqual(schema["properties"]["schema_version"]["const"], consult.FANOUT_CERTIFICATION_SCHEMA_VERSION)
        for key in consult.FANOUT_CERTIFICATION_REQUIRED_FIELDS:
            self.assertIn(key, schema["required"])

    def test_quota_observability_summary_flags_unknown_and_unobservable(self):
        """Unknown/unobservable quota should be surfaced as low-confidence, not silently healthy."""
        attached = {
            "openai-codex::gpt-5.5": {"model": "gpt-5.5", "status": "unobservable", "observability": "unobservable"},
            "deepseek::deepseek-v4-pro": {"model": "deepseek-v4-pro", "status": "unknown", "observability": "unknown"},
            "anthropic::claude-opus-4-7": {"model": "claude-opus-4-7", "status": "ok", "observability": "exact"},
        }
        summary = consult.quota_observability_summary(attached)
        self.assertEqual(summary["unknown_count"], 1)
        self.assertEqual(summary["unobservable_count"], 1)
        self.assertEqual(summary["exact_count"], 1)
        self.assertTrue(summary["has_low_confidence_quota"])
        self.assertIn("gpt-5.5", summary["low_confidence_models"])
        self.assertIn("deepseek-v4-pro", summary["low_confidence_models"])

    def test_quorum_t1_diversity_is_provider(self):
        """T1 diversity rule should be 'provider'"""
        quorum_path = Path(os.path.expanduser("~/.hermes/config/quorum.yaml"))
        if not quorum_path.exists():
            self.skipTest("quorum.yaml not found")
        import yaml
        with open(quorum_path) as f:
            q = yaml.safe_load(f)
        diversity = q.get("tiers", {}).get("T1", {}).get("diversity", "")
        self.assertEqual(diversity, "provider")

    def test_build_state_marks_state_as_facts_not_solution(self):
        """Main orchestrator state.json should define facts/bounds, not final candidate solution."""
        state = consult.build_state(
            question="Implement true multi-model discussion",
            context={"repo": "~/.hermes/scripts"},
            constraints=["use four models"],
            acceptance_criteria=["ratification gates pass"],
            implementation_target={"files": ["consult_models.py"], "verify_commands": ["python3 -m unittest"]},
        )
        self.assertEqual(state["schema"], "multi_model_state_v1")
        self.assertEqual(state["question"], "Implement true multi-model discussion")
        self.assertIn("implementation_target", state)
        self.assertFalse(state.get("is_candidate_solution"))
        self.assertIn("verify_commands", state["implementation_target"])

    def test_issue_ledger_detects_conflicting_patch_ids(self):
        """Discussion should start from an explicit disagreement ledger across model plans."""
        plans = [
            {"meta": {"planner_model": "claude"}, "patches": [{"id": "A", "target_file": "x.py", "op": "add_verifier", "rationale": "r1"}]},
            {"meta": {"planner_model": "codex"}, "patches": [{"id": "B", "target_file": "x.py", "op": "modify_router_weight", "rationale": "r2"}]},
        ]
        issues = consult.build_issue_ledger(plans)
        self.assertGreaterEqual(len(issues), 1)
        self.assertEqual(issues[0]["status"], "unresolved")
        self.assertGreaterEqual(issues[0]["severity"], 3)
        self.assertIn("claude", issues[0]["models"])
        self.assertIn("codex", issues[0]["models"])

    def test_issue_ledger_ignores_noop_patch_disagreements(self):
        """No-op certification patches are not implementation disagreements or blockers."""
        plans = [
            {"meta": {"planner_model": "claude"}, "patches": [{"id": "noop-a", "target_file": "x.py", "op": "noop", "rationale": "already verified"}]},
            {"meta": {"planner_model": "codex"}, "patches": [{"id": "noop-b", "target_file": "x.py", "op": "noop", "rationale": "no source change"}]},
            {"meta": {"planner_model": "deepseek"}, "patches": []},
            {"meta": {"planner_model": "mimo"}, "patches": [{"id": "noop-c", "target_file": "x.py", "op": "noop", "rationale": "certify"}]},
        ]
        self.assertEqual(consult.build_issue_ledger(plans), [])

    def test_issue_ledger_flags_noop_vs_real_change_disagreement(self):
        """A noop vote mixed with real implementation patches is a real disagreement."""
        plans = [
            {"meta": {"planner_model": "claude"}, "patches": [{"id": "noop-a", "op": "noop", "rationale": "already verified"}]},
            {"meta": {"planner_model": "codex"}, "patches": [{"id": "A", "target_file": "x.py", "op": "add_verifier", "rationale": "needed"}]},
        ]
        issues = consult.build_issue_ledger(plans)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["target_file"], "<mixed-noop-vs-change>")
        self.assertIn("claude", issues[0]["missing_models"])

    def test_discussion_retries_unparseable_response_with_strict_json_prompt(self):
        """Transient empty/non-JSON discussion outputs should get one strict JSON retry before failing closed."""
        plans = [
            {"meta": {"planner_model": "claude"}, "patches": []},
            {"meta": {"planner_model": "codex"}, "patches": []},
        ]
        calls = {"claude": 0, "codex": 0}

        def flaky_call(model, prompt):
            calls[model] += 1
            if calls[model] == 1:
                return ""
            self.assertIn("Return ONLY a JSON object", prompt)
            return '{"vote":"approve","best_within_constraints":true,"reasoning":"strict retry ok","critiques":[],"evidence_requests":[]}'

        result = consult.run_discussion_rounds(plans, current_best={"patches": []}, models=["claude", "codex"], max_rounds=1, call_model_fn=flaky_call)
        self.assertEqual(result["status"], "certified")
        self.assertEqual(calls, {"claude": 2, "codex": 2})

    def test_ratification_requires_no_rejects_and_no_unresolved_blockers(self):
        """Certification requires multi-party approval plus clean issue ledger."""
        votes = [
            {"model": "claude", "vote": "approve", "best_within_constraints": True},
            {"model": "codex", "vote": "approve", "best_within_constraints": True},
            {"model": "deepseek", "vote": "reject", "best_within_constraints": False},
            {"model": "mimo", "vote": "approve", "best_within_constraints": True},
        ]
        status = consult.evaluate_ratification(
            votes=votes,
            agreement_matrix={"framing": 0.9, "approach": 0.9, "implementation_order": 0.9},
            issue_ledger=[{"id": "I-1", "severity": 4, "status": "unresolved"}],
            revised_this_round=False,
            novel_redteam_blocker=False,
        )
        self.assertEqual(status["status"], "not_certified")
        self.assertIn("reject", " ".join(status["reasons"]))

    def test_run_discussion_offline_certifies_when_all_gates_clean(self):
        """Offline discussion runner should produce auditable ratification output without model calls."""
        plans = [
            {"meta": {"planner_model": "claude"}, "patches": [{"id": "A", "target_file": "x.py", "op": "add_verifier"}]},
            {"meta": {"planner_model": "codex"}, "patches": [{"id": "A", "target_file": "x.py", "op": "add_verifier"}]},
            {"meta": {"planner_model": "deepseek"}, "patches": [{"id": "A", "target_file": "x.py", "op": "add_verifier"}]},
            {"meta": {"planner_model": "mimo"}, "patches": [{"id": "A", "target_file": "x.py", "op": "add_verifier"}]},
        ]
        result = consult.run_discussion_rounds(plans, current_best={"patches": plans[0]["patches"]}, models=["claude", "codex", "deepseek", "mimo"], offline=True)
        self.assertEqual(result["status"], "certified")
        self.assertEqual(len(result["ratification_votes"]), 4)
        self.assertEqual(result["rounds_used"], 1)

    def test_filter_planners_by_quota_skips_exhausted_and_reports_snapshot(self):
        """Fan-out should gate exhausted providers and preserve quota provenance for outputs."""
        config = {"pricing": {"models": {
            "claude-opus-4-7": {"provider": "anthropic"},
            "gpt-5.5": {"provider": "openai-codex"},
        }}}
        snapshots = {
            "anthropic::claude-opus-4-7": {"model": "claude-opus-4-7", "provider": "anthropic", "status": "exhausted", "reset_at": "2026-04-28T09:00:00Z"},
            "openai-codex::gpt-5.5": {"model": "gpt-5.5", "provider": "openai-codex", "status": "unobservable"},
        }
        allowed, skipped, attached = consult.filter_planners_by_quota(
            ["claude-opus-4-7", "gpt-5.5"], config=config, quota_snapshot=snapshots
        )
        self.assertEqual(allowed, ["gpt-5.5"])
        self.assertEqual(skipped[0]["model"], "claude-opus-4-7")
        self.assertEqual(skipped[0]["reason"], "quota_exhausted")
        self.assertEqual(attached["openai-codex::gpt-5.5"]["observability"], "unobservable")

    def test_select_planners_gates_quota_before_quorum_trim(self):
        """Later healthy planners should backfill exhausted preferred planners before quorum trim."""
        config = {"pricing": {"models": {
            "claude-opus-4-7": {"provider": "anthropic"},
            "gpt-5.5": {"provider": "openai-codex"},
            "deepseek-v4-pro": {"provider": "deepseek"},
        }}}
        snapshots = {
            "anthropic::claude-opus-4-7": {"model": "claude-opus-4-7", "provider": "anthropic", "status": "exhausted"},
            "openai-codex::gpt-5.5": {"model": "gpt-5.5", "provider": "openai-codex", "status": "ok"},
            "deepseek::deepseek-v4-pro": {"model": "deepseek-v4-pro", "provider": "deepseek", "status": "ok"},
        }
        selected, skipped, attached = consult.select_planners_for_fanout(
            ["claude-opus-4-7", "gpt-5.5", "deepseek-v4-pro"],
            q_count=2,
            config=config,
            quota_snapshot=snapshots,
        )
        self.assertEqual(selected, ["gpt-5.5", "deepseek-v4-pro"])
        self.assertEqual(skipped[0]["model"], "claude-opus-4-7")
        self.assertIn("deepseek::deepseek-v4-pro", attached)

    def test_planner_prompt_truncation_preserves_truth_gate_fields(self):
        """Oversized state prompts must not silently drop claims/evidence/truth_gate."""
        state = consult.build_state(
            question="large state",
            context={"blob": "x" * (consult.MAX_PLANNER_STATE_CHARS + 1000)},
            claims=[{"id": "C-KEEP", "text": "critical claim", "severity": 4}],
            evidence=[{"id": "E-KEEP", "type": "command", "summary": "critical evidence", "supports": ["C-KEEP"]}],
        )
        bundle = consult.build_evidence_bundle(state)
        state["evidence_bundle"] = bundle
        state["truth_gate"] = consult.evaluate_truth_gate(bundle)
        prompt = consult.build_planner_prompt(state, "hash", "model", "T3")
        self.assertIn("STATE_TRUNCATION_NOTICE", prompt)
        self.assertIn("C-KEEP", prompt)
        self.assertIn("E-KEEP", prompt)
        self.assertIn('"truth_gate"', prompt)
        self.assertIn('"state_truncated": true', prompt)

    def test_evidence_bundle_marks_unsupported_claims(self):
        """Truth gate should separate model agreement from evidence-backed truth."""
        state = {
            "claims": [
                {"id": "C-001", "text": "origin/main has no commits ahead of HEAD", "severity": 4},
                {"id": "C-002", "text": "self-test passed", "severity": 3},
            ],
            "evidence": [
                {"id": "E-001", "type": "command", "summary": "git rev-list HEAD..origin/main returned 0", "supports": ["C-001"], "exit_code": 0}
            ],
        }
        bundle = consult.build_evidence_bundle(state)
        self.assertEqual(bundle["schema_version"], consult.EVIDENCE_BUNDLE_SCHEMA_VERSION)
        self.assertEqual(bundle["grounding"]["C-001"]["truth_status"], "verified_by_evidence")
        self.assertEqual(bundle["grounding"]["C-002"]["truth_status"], "unsupported")
        gate = consult.evaluate_truth_gate(bundle)
        self.assertEqual(gate["truth_status"], "partially_grounded")
        self.assertFalse(gate["can_certify_truth"])
        self.assertIn("C-002", gate["unsupported_claim_ids"])

    def test_evidence_requests_are_extracted_from_model_outputs(self):
        """Other brains should request evidence instead of claiming tool-verified truth."""
        outputs = [
            {"meta": {"planner_model": "deepseek"}, "evidence_requests": [
                {"claim_id": "C-007", "tool_needed": "terminal", "command": "git status --short", "why": "verify clean worktree"}
            ]},
            {"meta": {"planner_model": "mimo"}, "evidence_requests": [
                {"claim": "pytest passed", "tool_needed": "terminal", "command": "python3 -m pytest -q", "why": "confirm tests"}
            ]},
        ]
        requests = consult.collect_evidence_requests(outputs)
        self.assertEqual(len(requests), 2)
        self.assertEqual(requests[0]["requested_by"], "deepseek")
        self.assertEqual(requests[0]["status"], "requested")
        self.assertIn("read_only", requests[0]["safety"])

    def test_ratification_fails_closed_when_high_severity_truth_unsupported(self):
        """Multi-model approval must not certify unsupported high-severity factual claims."""
        votes = [
            {"model": "claude", "vote": "approve", "best_within_constraints": True},
            {"model": "codex", "vote": "approve", "best_within_constraints": True},
            {"model": "deepseek", "vote": "approve", "best_within_constraints": True},
        ]
        truth_gate = {
            "truth_status": "partially_grounded",
            "can_certify_truth": False,
            "unsupported_claim_ids": ["C-009"],
            "unsupported_high_severity_claim_ids": ["C-009"],
        }
        status = consult.evaluate_ratification(
            votes=votes,
            agreement_matrix={"framing": 0.95, "approach": 0.95, "implementation_order": 0.95},
            issue_ledger=[],
            revised_this_round=False,
            novel_redteam_blocker=False,
            truth_gate=truth_gate,
        )
        self.assertEqual(status["status"], "not_certified")
        self.assertIn("unsupported high-severity factual claims", " ".join(status["reasons"]))

    def test_run_discussion_output_includes_truth_assessment_and_evidence_requests(self):
        """Discussion artifacts should expose provenance, truth status, and requested missing evidence."""
        plans = [
            {"meta": {"planner_model": "claude"}, "patches": [], "evidence_requests": [{"claim_id": "C-1", "tool_needed": "terminal", "command": "git status", "why": "verify"}]},
            {"meta": {"planner_model": "codex"}, "patches": []},
        ]
        bundle = consult.build_evidence_bundle({"claims": [{"id": "C-1", "text": "worktree clean", "severity": 4}], "evidence": []})
        result = consult.run_discussion_rounds(plans, current_best={"patches": []}, models=["claude", "codex"], offline=True, evidence_bundle=bundle)
        self.assertEqual(result["status"], "not_certified")
        self.assertEqual(result["truth_assessment"]["truth_status"], "unsupported")
        self.assertEqual(result["evidence_requests"][0]["requested_by"], "claude")


if __name__ == "__main__":
    unittest.main(verbosity=2)
