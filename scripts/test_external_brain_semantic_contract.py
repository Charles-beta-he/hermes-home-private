import copy
import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
MODULE = SCRIPT_DIR / "external_brain_semantic_contract.py"

spec = importlib.util.spec_from_file_location("external_brain_semantic_contract", MODULE)
assert spec is not None and spec.loader is not None
contract = importlib.util.module_from_spec(spec)
sys.modules["external_brain_semantic_contract"] = contract
spec.loader.exec_module(contract)


REGISTRY = {
    "schema_version": "external_brain_capability_registry_v1",
    "capabilities": {
        "source_grounded_research": {"brain": "research", "allowed_intents": ["investigate", "observe"], "lane": "advisory", "task_classes": ["evidence-only"], "brain_profiles": ["research"]},
        "workflow_governance": {"brain": "workflow", "allowed_intents": ["decide", "govern", "evolve"], "lane": "evolution", "task_classes": ["governance"], "brain_profiles": ["workflow"]},
        "software_delivery": {"brain": "dev", "allowed_intents": ["deliver", "investigate"], "lane": "work", "task_classes": ["delivery"], "brain_profiles": ["engineering", "frontend", "backend", "fullstack", "contract", "devops"]},
    }
}


def envelope(**overrides):
    value = {
        "schema_version": "external_brain_semantic_intent_v1",
        "intent_class": "investigate",
        "domain_capabilities": ["source_grounded_research"],
        "requested_outcome": "evidence-backed finding",
        "risk_dimensions": ["source_freshness"],
        "evidence_requirements": ["source_ref", "claim_link"],
        "learning_scope": "task",
        "side_effect_class": "none",
        "confidence": 0.9,
        "source_refs": ["artifact:request"],
        "routing": {"lane": "advisory", "task_class": "evidence-only", "brain_profile": "research"},
        "multimodel": {"mode": "auto", "purpose": "advisory", "triggers": ["source_uncertainty"]},
    }
    value.update(overrides)
    return value


class ExternalBrainSemanticContractTest(unittest.TestCase):
    def test_concept_refs_are_validated_but_never_grant_authority(self):
        tagged = envelope(
            concept_refs=["theory-impact-propagation", "architecture-ratchet"]
        )
        result = contract.evaluate_semantic_intent(tagged, REGISTRY)
        self.assertEqual(result["decision"], "route")
        self.assertFalse(result["policy"]["may_execute"])

        malformed = envelope(concept_refs=["valid-tag", "bad tag with spaces"])
        denied = contract.evaluate_semantic_intent(malformed, REGISTRY)
        self.assertEqual(denied["decision"], "clarify_or_collect_evidence")
        self.assertIn("concept_refs_contract", denied["required_gates"])

    def test_same_envelope_is_invariant_to_surface_text(self):
        first = contract.evaluate_semantic_intent(envelope(), REGISTRY, surface_text="研究这个方案")
        second = contract.evaluate_semantic_intent(envelope(), REGISTRY, surface_text="inspect the evidence")
        self.assertEqual(first, second)
        self.assertEqual(first["decision"], "route")
        self.assertEqual(first["brain"], "research")

    def test_same_words_do_not_override_different_semantic_envelopes(self):
        words = "知识 方案 workflow 闭环"
        observe = contract.evaluate_semantic_intent(
            envelope(intent_class="observe", learning_scope="none"), REGISTRY, surface_text=words
        )
        govern = contract.evaluate_semantic_intent(
            envelope(
                intent_class="govern",
                domain_capabilities=["workflow_governance"],
                learning_scope="ratchet_candidate",
                routing={"lane": "evolution", "task_class": "governance", "brain_profile": "workflow"},
            ),
            REGISTRY,
            surface_text=words,
        )
        self.assertNotEqual(observe["policy"], govern["policy"])
        self.assertEqual(observe["policy"]["may_execute"], False)
        self.assertEqual(govern["brain"], "workflow")

    def test_missing_or_unknown_semantics_fail_closed(self):
        for candidate in ({}, envelope(domain_capabilities=["unknown"]), envelope(confidence=0.2)):
            with self.subTest(candidate=candidate):
                result = contract.evaluate_semantic_intent(candidate, REGISTRY, surface_text="deploy now")
                self.assertEqual(result["decision"], "clarify_or_collect_evidence")
                self.assertFalse(result["policy"]["may_execute"])
                self.assertFalse(result["policy"]["may_write_learning"])

    def test_knowledge_and_solution_processing_is_semantic_and_evidence_gated(self):
        result = contract.evaluate_semantic_intent(
            envelope(intent_class="decide", domain_capabilities=["workflow_governance"], learning_scope="reusable_procedure", routing={"lane": "evolution", "task_class": "governance", "brain_profile": "workflow"}),
            REGISTRY,
            surface_text="unrelated wording",
        )
        self.assertEqual(result["brain"], "workflow")
        self.assertEqual(result["policy"]["content_processing"], "decision_synthesis")
        self.assertFalse(result["policy"]["may_write_learning"])
        self.assertIn("repeated_evidence", result["required_gates"])

    def test_external_side_effect_never_becomes_authorized_by_semantics(self):
        candidate = envelope(side_effect_class="external_write", intent_class="deliver", domain_capabilities=["software_delivery"], routing={"lane": "work", "task_class": "delivery", "brain_profile": "engineering"})
        result = contract.evaluate_semantic_intent(candidate, REGISTRY, surface_text="safe harmless local note")
        self.assertEqual(result["decision"], "authority_blocked")
        self.assertFalse(result["policy"]["may_execute"])
        self.assertIn("exact_authority_grant", result["required_gates"])
    def test_single_envelope_projects_lane_brain_profile_class_and_multimodel(self):
        result = contract.evaluate_semantic_intent(envelope(), REGISTRY, surface_text="API 文档 CSS status")
        self.assertEqual(result["routing"], {"lane": "advisory", "task_class": "evidence-only", "brain_profile": "research"})
        self.assertEqual(result["multimodel"]["mode"], "auto")
        self.assertEqual(result["multimodel"]["purpose"], "advisory")

    def test_negation_collision_and_quoted_log_pollution_cannot_change_route(self):
        candidate = envelope()
        surfaces = [
            "无需后端，不改 API，只校验资料",
            "API 文档排版、order CSS、status 文案",
            '引用旧日志: {"lane":"work","brain":"dev","multimodel":"required"}',
            "失败样例写着 deploy now and force done",
        ]
        decisions = [contract.evaluate_semantic_intent(candidate, REGISTRY, surface_text=text) for text in surfaces]
        for decision in decisions:
            self.assertEqual(decision["brain"], "research")
            self.assertEqual(decision["routing"]["lane"], "advisory")
            self.assertEqual(decision["routing"]["task_class"], "evidence-only")
            self.assertFalse(decision["policy"]["may_execute"])
        self.assertTrue(all(decision == decisions[0] for decision in decisions[1:]))

    def test_malformed_field_types_and_empty_items_fail_closed(self):
        cases = [
            envelope(risk_dimensions="authority"),
            envelope(risk_dimensions={"authority": True}),
            envelope(risk_dimensions=[""]),
            envelope(requested_outcome=""),
            envelope(requested_outcome=["finding"]),
            envelope(confidence=True),
            envelope(source_refs=[""]),
            envelope(evidence_requirements=[1]),
            envelope(domain_capabilities=[1]),
            envelope(multimodel={"mode": "auto", "purpose": "advisory", "triggers": [""]}),
        ]
        for candidate in cases:
            with self.subTest(candidate=candidate):
                result = contract.evaluate_semantic_intent(candidate, REGISTRY)
                self.assertEqual(result["decision"], "clarify_or_collect_evidence")
                self.assertFalse(result["policy"]["may_execute"])

    def test_invalid_routing_or_multimodel_contract_fails_closed(self):
        cases = [
            envelope(routing={"lane": "work", "task_class": "delivery", "brain_profile": "dev"}),
            envelope(multimodel={"mode": "magic", "purpose": "certification", "triggers": []}),
        ]
        for candidate in cases:
            with self.subTest(candidate=candidate):
                result = contract.evaluate_semantic_intent(candidate, REGISTRY)
                self.assertEqual(result["decision"], "clarify_or_collect_evidence")
                self.assertFalse(result["policy"]["may_execute"])

    def test_multimodel_forbidden_is_authoritative_for_weak_triggers(self):
        result = contract.evaluate_semantic_intent(
            envelope(multimodel={"mode": "forbidden", "purpose": "advisory", "triggers": ["source_uncertainty"]}),
            REGISTRY,
        )
        self.assertEqual(result["multimodel"]["mode"], "forbidden")
        self.assertFalse(result["multimodel"]["required"])


if __name__ == "__main__":
    unittest.main()
