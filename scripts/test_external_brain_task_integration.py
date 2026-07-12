import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT_DIR = Path(__file__).resolve().parent
ORCHESTRATOR = SCRIPT_DIR / "brain_task_orchestrator.py"
spec = importlib.util.spec_from_file_location("brain_task_orchestrator_semantic_test", ORCHESTRATOR)
assert spec is not None and spec.loader is not None
orchestrator = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = orchestrator
spec.loader.exec_module(orchestrator)


class StructuredSemanticTaskIntegrationTest(unittest.TestCase):
    def task(self, envelope, title="知识 方案 workflow 闭环"):
        return orchestrator.Task(
            Path("semantic-task.md"),
            {
                "status": "pending",
                "priority": "P1",
                "project": "hermes-agent-os-control-plane",
                "semantic_intent": envelope,
            },
            f"# {title}\n",
        )

    def envelope(self, **overrides):
        value = {
            "schema_version": "external_brain_semantic_intent_v1",
            "intent_class": "govern",
            "domain_capabilities": ["workflow_governance"],
            "requested_outcome": "governed lifecycle",
            "risk_dimensions": ["authority"],
            "evidence_requirements": ["proof_ref"],
            "learning_scope": "ratchet_candidate",
            "side_effect_class": "none",
            "confidence": 0.92,
            "source_refs": ["artifact:request"],
            "routing": {"lane": "evolution", "task_class": "governance", "brain_profile": "workflow"},
            "multimodel": {"mode": "required", "purpose": "certification", "triggers": ["governed_change"]},
        }
        value.update(overrides)
        return value

    def test_semantic_knowledge_queries_depend_only_on_validated_envelope(self):
        envelope = self.envelope()
        queries = orchestrator.semantic_knowledge_queries(envelope)
        self.assertEqual(
            queries,
            ["governed lifecycle", "workflow_governance", "workflow governance"],
        )
        self.assertNotIn("知识", " ".join(queries))

    def test_concept_refs_bridge_brain_frontmatter_tags_into_recall_queries(self):
        envelope = self.envelope(
            concept_refs=[
                "theory-impact-propagation",
                "architecture-ratchet",
                "same-theory-scan",
            ]
        )
        queries = orchestrator.semantic_knowledge_queries(envelope)
        self.assertEqual(
            queries[:3],
            ["theory-impact-propagation", "architecture-ratchet", "same-theory-scan"],
        )
        changed = dict(envelope, concept_refs=["impact-smoothing"])
        self.assertNotEqual(queries, orchestrator.semantic_knowledge_queries(changed))

        bound = orchestrator.bind_semantic_concept_refs(
            self.envelope(), ["task", "theory-impact-propagation", "impact-smoothing"]
        )
        self.assertEqual(
            bound["concept_refs"],
            ["theory-impact-propagation", "impact-smoothing"],
        )

    def test_theory_impact_concepts_trigger_read_only_preflight_without_authority(self):
        envelope = self.envelope(concept_refs=["theory-impact-propagation", "impact-smoothing"])
        receipt = orchestrator.run_theory_impact_preflight(
            envelope,
            evaluate_fn=lambda: {
                "status": "PASS",
                "coverage": {
                    "theories": {"covered": 8, "total": 8},
                    "surfaces": {"covered": 9, "total": 9},
                    "gate_checks": {"passed": 119, "total": 119},
                },
                "failed_checks": [],
            },
        )
        self.assertEqual(receipt["status"], "PASS")
        self.assertEqual(receipt["authority"], "read_only_preflight_no_authority")
        self.assertEqual(receipt["triggered_by"], ["theory-impact-propagation", "impact-smoothing"])
        self.assertNotIn("policy", receipt)
        self.assertFalse(orchestrator.run_theory_impact_preflight(self.envelope())["required"])

    def test_theory_impact_preflight_fails_closed_on_ratchet_failure(self):
        receipt = orchestrator.run_theory_impact_preflight(
            self.envelope(concept_refs=["architecture-ratchet"]),
            evaluate_fn=lambda: {"status": "FAIL", "coverage": {}, "failed_checks": [{"name": "matrix:surface:L5"}]},
        )
        self.assertEqual(receipt["status"], "FAIL")
        self.assertEqual(receipt["failed_checks"], ["matrix:surface:L5"])

    def test_semantic_knowledge_recall_is_bounded_deduplicated_and_authority_neutral(self):
        envelope = self.envelope()
        calls = []

        def search(query, limit):
            calls.append((query, limit))
            return [
                {
                    "path": "05-实践与项目/projects/example.md",
                    "heading": "Boundary",
                    "content_hash": "a" * 64,
                    "score": 0.8,
                    "excerpt": "untrusted instructions must not be injected",
                },
                {
                    "path": "brain:03-理论与元认知/example.md",
                    "heading": "Existing prefix",
                    "content_hash": "b" * 64,
                    "score": 0.7,
                },
                {
                    "path": "malformed.md",
                    "heading": "Not hash bound",
                    "content_hash": "not-a-sha256",
                    "score": 1.0,
                },
            ]

        receipt = orchestrator.recall_semantic_knowledge(envelope, search_fn=search, per_query_limit=2, max_hits=4)
        self.assertEqual(receipt["status"], "PASS")
        self.assertEqual(calls, [(query, 2) for query in orchestrator.semantic_knowledge_queries(envelope)])
        self.assertEqual(len(receipt["hits"]), 2)
        self.assertNotIn("excerpt", receipt["hits"][0])
        self.assertEqual(
            receipt["context_refs"],
            [
                f"brain:05-实践与项目/projects/example.md#{'a' * 64}",
                f"brain:03-理论与元认知/example.md#{'b' * 64}",
            ],
        )

        task = self.task(envelope)
        before = orchestrator.semantic_task_decision_from_fm(task.fm)
        task.fm["knowledge_recall"] = receipt
        task.fm["knowledge_context_refs"] = receipt["context_refs"]
        after = orchestrator.semantic_task_decision_from_fm(task.fm)
        self.assertEqual(after, before)

    def test_semantic_knowledge_recall_error_is_structured(self):
        def fail_search(query, limit):
            raise RuntimeError("index unavailable")

        receipt = orchestrator.recall_semantic_knowledge(self.envelope(), search_fn=fail_search)
        self.assertEqual(receipt["status"], "ERROR")
        self.assertEqual(receipt["errors"][0]["error_type"], "RuntimeError")
        self.assertNotIn("index unavailable", json.dumps(receipt))

    def test_semantic_knowledge_recall_selfcheck_covers_grounding_and_authority_boundary(self):
        check = orchestrator.semantic_knowledge_recall_selfcheck()
        self.assertEqual(check["status"], "PASS")
        self.assertTrue(check["bounded"])
        self.assertTrue(check["deduplicated"])
        self.assertTrue(check["excerpt_excluded"])
        self.assertTrue(check["authority_neutral"])
        self.assertTrue(check["sources_verified"])
        self.assertEqual(check["validation_failures"], [])

    def test_command_add_persists_automatic_knowledge_recall_and_blocks_recall_error(self):
        envelope = self.envelope(
            intent_class="deliver",
            domain_capabilities=["software_delivery"],
            requested_outcome="local verified implementation",
            routing={"lane": "work", "task_class": "delivery", "brain_profile": "engineering"},
            learning_scope="task",
            side_effect_class="local_write",
            multimodel={"mode": "forbidden", "purpose": "advisory", "triggers": []},
        )
        args = orchestrator.build_parser().parse_args([
            "add", "surface words must not drive recall",
            "--project", "test",
            "--priority-layer", "P1",
            "--dependency-order", "0",
            "--multimodel-triage-result", "not-required",
            "--semantic-intent-json", json.dumps(envelope),
        ])
        receipt = {
            "schema": "semantic_knowledge_recall_v1",
            "status": "PASS",
            "authority": "context_only_no_authority",
            "semantic_envelope_hash": orchestrator.semantic_envelope_hash(envelope),
            "queries": orchestrator.semantic_knowledge_queries(envelope),
            "hits": [{"path": "project.md", "heading": "Rule", "content_hash": "d" * 64, "score": 0.9}],
            "context_refs": [f"brain:project.md#{'d' * 64}"],
            "errors": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            tasks = Path(tmp) / "tasks"
            tasks.mkdir()
            registry = json.loads((SCRIPT_DIR.parent / "brains" / "semantic-capabilities.json").read_text(encoding="utf-8"))
            registry["enforcement"]["strict_task_roots"] = [str(tasks)]
            common = [
                patch.object(orchestrator, "TASKS_DIR", tasks),
                patch.object(orchestrator, "VAULT", Path(tmp)),
                patch.object(orchestrator, "task_brain_semantic_registry", return_value=registry),
                patch.object(orchestrator, "refresh_derived_task_views", return_value={"status": "SKIPPED"}),
                patch.object(orchestrator, "maybe_fire_taskpool_event_hook", return_value={"status": "SKIPPED"}),
            ]
            with common[0], common[1], common[2], common[3], common[4], patch.object(
                orchestrator, "recall_semantic_knowledge", return_value=receipt
            ):
                created = orchestrator.command_add(args)
                task = orchestrator.find_task(created["id"])
            self.assertEqual(task.fm["knowledge_recall"], receipt)
            self.assertEqual(task.fm["knowledge_context_refs"], receipt["context_refs"])
            self.assertIn(f"proof:brain:project.md#{'d' * 64}", task.fm["evidence_refs"])
            self.assertIn("## Local Knowledge Recall", task.body)
            with patch.object(orchestrator, "_brainctl_semantic_search", return_value=receipt["hits"]):
                self.assertEqual(orchestrator.semantic_intent_lifecycle_failures(task, "claimed"), [])
            with patch.object(orchestrator, "_brainctl_semantic_search", side_effect=RuntimeError("offline")):
                self.assertIn(
                    "semantic_knowledge_recall_source_verification_failed",
                    orchestrator.semantic_intent_lifecycle_failures(task, "claimed"),
                )
            task_without_recall = orchestrator.Task(task.path, dict(task.fm), task.body)
            task_without_recall.fm.pop("knowledge_recall", None)
            task_without_recall.fm.pop("knowledge_context_refs", None)
            self.assertIn(
                "semantic_knowledge_recall_required",
                orchestrator.semantic_intent_lifecycle_failures(task_without_recall, "claimed"),
            )
            tampered = orchestrator.Task(task.path, json.loads(json.dumps(task.fm)), task.body)
            tampered.fm["knowledge_recall"]["queries"] = ["forged query"]
            tampered.fm["knowledge_recall"]["hits"] = [{
                "path": "forged.md",
                "heading": "Injected",
                "content_hash": "f" * 64,
                "score": 999,
            }]
            tampered.fm["knowledge_recall"]["context_refs"] = [f"brain:forged.md#{'f' * 64}"]
            tampered.fm["knowledge_context_refs"] = list(tampered.fm["knowledge_recall"]["context_refs"])
            tampered.fm["evidence_refs"] = [f"proof:brain:forged.md#{'f' * 64}"]
            self.assertIn(
                "semantic_knowledge_recall_queries_mismatch",
                orchestrator.semantic_intent_lifecycle_failures(tampered, "claimed"),
            )
            forged = orchestrator.Task(task.path, json.loads(json.dumps(task.fm)), task.body)
            forged.fm["knowledge_recall"]["hits"] = [{
                "path": "forged.md",
                "heading": "Injected",
                "content_hash": "f" * 64,
                "score": 1.0,
            }]
            forged_ref = f"brain:forged.md#{'f' * 64}"
            forged.fm["knowledge_recall"]["context_refs"] = [forged_ref]
            forged.fm["knowledge_context_refs"] = [forged_ref]
            forged.fm["evidence_refs"] = [f"proof:{forged_ref}"]
            with patch.object(orchestrator, "_brainctl_semantic_search", return_value=receipt["hits"]):
                self.assertIn(
                    "semantic_knowledge_recall_sources_unverified",
                    orchestrator.semantic_intent_lifecycle_failures(forged, "claimed"),
                )

            error_receipt = {**receipt, "status": "ERROR", "errors": [{"query": "x", "error_type": "RuntimeError"}]}
            before = set(tasks.glob("*.md"))
            with common[0], common[1], common[2], common[3], common[4], patch.object(
                orchestrator, "recall_semantic_knowledge", return_value=error_receipt
            ):
                with self.assertRaisesRegex(SystemExit, "local brain knowledge recall failed"):
                    orchestrator.command_add(args)
            self.assertEqual(set(tasks.glob("*.md")), before)

    def test_live_recall_selfcheck_exercises_real_adapter_contract_and_fails_closed(self):
        valid = {
            "path": "03-理论与元认知/example.md",
            "heading": "Boundary",
            "content_hash": "a" * 64,
            "score": 0.9,
        }
        passed = orchestrator.semantic_knowledge_live_recall_selfcheck(
            search_fn=lambda query, limit: [valid]
        )
        self.assertEqual(passed["status"], "PASS")
        self.assertEqual(passed["adapter"], "brainctl_search")
        self.assertEqual(passed["hit_count"], 1)
        self.assertTrue(passed["hash_bound"])
        self.assertTrue(passed["authority_neutral"])

        failed = orchestrator.semantic_knowledge_live_recall_selfcheck(
            search_fn=lambda query, limit: (_ for _ in ()).throw(RuntimeError("offline secret detail"))
        )
        self.assertEqual(failed["status"], "FAIL")
        self.assertEqual(failed["errors"], [{"query": "hermes local brain", "error_type": "RuntimeError"}])
        self.assertNotIn("offline secret detail", json.dumps(failed))

    def test_live_recall_canonical_hash_verifier_recomputes_block_hash(self):
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            note = vault / "03-理论与元认知" / "example.md"
            note.parent.mkdir(parents=True)
            note.write_text("# Boundary\n\nCanonical text.\n", encoding="utf-8")
            with patch.object(orchestrator, "VAULT", vault):
                blocks, _ = orchestrator._brainctl_blocks_from_file_for_hash(note)
                self.assertEqual(len(blocks), 1)
                hit = dict(blocks[0])
                self.assertTrue(orchestrator._canonical_brain_hit_hash_matches(hit))
                hit["content_hash"] = "f" * 64
                self.assertFalse(orchestrator._canonical_brain_hit_hash_matches(hit))

    def test_live_recall_selfcheck_fails_closed_on_canonical_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            note = vault / "03-理论与元认知" / "example.md"
            note.parent.mkdir(parents=True)
            note.write_text("# Boundary\n\nCanonical text.\n", encoding="utf-8")
            with patch.object(orchestrator, "VAULT", vault):
                blocks, _ = orchestrator._brainctl_blocks_from_file_for_hash(note)
                hit = {**blocks[0], "score": 0.9}
                with patch.object(orchestrator, "_brainctl_semantic_search", return_value=[hit]):
                    passed = orchestrator.semantic_knowledge_live_recall_selfcheck()
                self.assertTrue(passed["canonical_hash_verified"])
                self.assertEqual(passed["status"], "PASS")
                forged = {**hit, "content_hash": "f" * 64}
                with patch.object(orchestrator, "_brainctl_semantic_search", return_value=[forged]):
                    failed = orchestrator.semantic_knowledge_live_recall_selfcheck()
                self.assertFalse(failed["canonical_hash_verified"])
                self.assertEqual(failed["status"], "FAIL")

    def test_live_recall_hash_verifier_rejects_secret_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            note = vault / "03-理论与元认知" / "secret.md"
            note.parent.mkdir(parents=True)
            note.write_text("# Secret\n\napi_key: sk-abcdefghijklmnop\n", encoding="utf-8")
            with patch.object(orchestrator, "VAULT", vault):
                raw_hash = __import__("hashlib").sha256(
                    "03-理论与元认知/secret.md\nSecret\n1\n3\n# Secret\n\napi_key: sk-abcdefghijklmnop".encode("utf-8")
                ).hexdigest()
                hit = {"path": "03-理论与元认知/secret.md", "heading": "Secret", "line_start": 1, "line_end": 3, "content_hash": raw_hash}
                self.assertFalse(orchestrator._canonical_brain_hit_hash_matches(hit))

    def test_live_recall_hash_verifier_rejects_malformed_line_range(self):
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td)
            note = vault / "03-理论与元认知" / "example.md"
            note.parent.mkdir(parents=True)
            note.write_text("# Boundary\n\nCanonical text.\n", encoding="utf-8")
            with patch.object(orchestrator, "VAULT", vault):
                blocks, _ = orchestrator._brainctl_blocks_from_file_for_hash(note)
                valid = dict(blocks[0])
                self.assertTrue(orchestrator._canonical_brain_hit_hash_matches(valid))
                malformed_ranges = (
                    {"line_start": "not-an-int"},
                    {"line_start": True},
                    {"line_start": False},
                    {"line_start": 1.0},
                    {"line_start": 1.2},
                    {"line_start": None},
                    {"line_start": 0},
                    {"line_start": -1},
                    {"line_end": "3"},
                    {"line_end": True},
                    {"line_end": 3.0},
                    {"line_end": None},
                    {"line_end": 0},
                    {"line_start": 3, "line_end": 2},
                )
                for replacement in malformed_ranges:
                    with self.subTest(replacement=replacement):
                        hit = {**valid, **replacement}
                        self.assertFalse(orchestrator._canonical_brain_hit_hash_matches(hit))

    def test_profile_classifier_uses_structured_semantics_as_authority(self):
        registry = {"schema_version": "external_brain_capability_registry_v1", "capabilities": {"workflow_governance": {"brain": "workflow", "allowed_intents": ["govern"], "lane": "evolution", "task_classes": ["governance"], "brain_profiles": ["workflow"]}}}
        with patch.object(orchestrator, "task_brain_semantic_registry", return_value=registry):
            result = orchestrator.classify_task_with_profile_policy(self.task(self.envelope()), {})
        self.assertEqual(result["semantic_authority"], "structured_envelope_only")
        self.assertEqual(result["brain"], "workflow")
        self.assertEqual(result["task_class"], "governance")
        self.assertEqual(result["intent_class"], "govern")
        self.assertEqual(result["risk_dimensions"], ["authority"])
        self.assertEqual(result["enforcement"], "fail_closed_structured_semantics")
        self.assertFalse(result["may_write_learning"])

    def test_title_words_cannot_override_observe_no_write_envelope(self):
        registry = {"schema_version": "external_brain_capability_registry_v1", "capabilities": {"workflow_governance": {"brain": "workflow", "allowed_intents": ["observe"], "lane": "evolution", "task_classes": ["governance"], "brain_profiles": ["workflow"]}}}
        with patch.object(orchestrator, "task_brain_semantic_registry", return_value=registry):
            result = orchestrator.classify_task_with_profile_policy(
                self.task(self.envelope(intent_class="observe", learning_scope="none")), {}
            )
        self.assertFalse(result["may_execute"])
        self.assertFalse(result["may_write_learning"])
        self.assertEqual(result["content_processing"], "evidence_observation")
    def test_structured_envelope_is_single_ssot_for_lane_brain_profile_and_multimodel(self):
        registry = {"schema_version": "external_brain_capability_registry_v1", "capabilities": {"workflow_governance": {"brain": "workflow", "allowed_intents": ["govern"], "lane": "evolution", "task_classes": ["governance"], "brain_profiles": ["workflow"]}}}
        task = self.task(self.envelope(), title="API 文档 CSS status，不需要后端，不部署")
        with patch.object(orchestrator, "task_brain_semantic_registry", return_value=registry):
            self.assertEqual(orchestrator.infer_lane(task.fm), "evolution")
            self.assertEqual(orchestrator.infer_task_brain(task), "workflow")
            self.assertEqual(orchestrator.infer_task_brain_profile(task), "workflow")
            reasons = orchestrator.task_multimodel_intervention_reasons(task)
        self.assertEqual(reasons, ["semantic:governed_change"])

    def test_multimodel_forbidden_blocks_even_strong_runtime_triggers(self):
        registry = {"schema_version": "external_brain_capability_registry_v1", "capabilities": {"workflow_governance": {"brain": "workflow", "allowed_intents": ["govern"], "lane": "evolution", "task_classes": ["governance"], "brain_profiles": ["workflow"]}}}
        task = self.task(self.envelope(multimodel={"mode": "forbidden", "purpose": "advisory", "triggers": []}))
        task.fm["retry_count"] = 3
        with patch.object(orchestrator, "task_brain_semantic_registry", return_value=registry):
            self.assertEqual(orchestrator.task_multimodel_intervention_reasons(task), [])

    def test_invalid_semantic_envelope_fails_to_needs_review(self):
        task = self.task(self.envelope(routing={"lane": "work", "task_class": "delivery", "brain_profile": "dev"}))
        self.assertEqual(orchestrator.infer_lane(task.fm), "advisory")
        self.assertEqual(orchestrator.infer_task_brain(task), "main")

    def test_strict_root_blocks_missing_or_invalid_semantics_at_dispatch_and_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = {
                "schema_version": "external_brain_capability_registry_v1",
                "capabilities": {
                    "workflow_governance": {
                        "brain": "workflow",
                        "allowed_intents": ["govern"],
                        "lane": "evolution",
                        "task_classes": ["governance"],
                        "brain_profiles": ["workflow"],
                    }
                },
                "enforcement": {"mode": "strict_active_tasks", "strict_task_roots": [tmp]},
            }
            missing = self.task(None)
            invalid = self.task(self.envelope(domain_capabilities=["unknown"]))
            with patch.object(orchestrator, "TASKS_DIR", Path(tmp)), patch.object(
                orchestrator, "task_brain_semantic_registry", return_value=registry
            ):
                for task, expected in (
                    (missing, "semantic_intent_missing_needs_review"),
                    (invalid, "semantic_intent_invalid_needs_review"),
                ):
                    with self.subTest(expected=expected):
                        self.assertFalse(task.is_dispatchable())
                        failures, _ = orchestrator.lifecycle_gate(task, "claimed", "worker")
                        self.assertTrue(any(item.startswith(expected) for item in failures), failures)
                        force_failures, _ = orchestrator.lifecycle_gate(task, "claimed", "worker", force=True)
                        self.assertTrue(any(item.startswith(expected) for item in force_failures), force_failures)

    def test_route_authority_does_not_imply_execute_authority(self):
        registry = {
            "schema_version": "external_brain_capability_registry_v1",
            "capabilities": {
                "workflow_governance": {
                    "brain": "workflow",
                    "allowed_intents": ["observe", "investigate", "decide", "govern", "evolve", "deliver"],
                    "lane": "evolution",
                    "task_classes": ["governance"],
                    "brain_profiles": ["workflow"],
                }
            },
            "enforcement": {"mode": "strict_active_tasks", "strict_task_roots": []},
        }
        with tempfile.TemporaryDirectory() as tmp:
            registry["enforcement"]["strict_task_roots"] = [tmp]
            with patch.object(orchestrator, "TASKS_DIR", Path(tmp)), patch.object(orchestrator, "task_brain_semantic_registry", return_value=registry):
                for intent in ("observe", "investigate", "decide", "govern", "evolve"):
                    with self.subTest(intent=intent):
                        task = self.task(self.envelope(intent_class=intent, side_effect_class="none"))
                        decision = orchestrator.semantic_task_decision(task)
                        self.assertEqual(decision["decision"], "route")
                        self.assertFalse(decision["policy"]["may_execute"])
                        self.assertFalse(task.is_dispatchable())
                        for status in ("claimed", "running", "review", "certified", "done"):
                            failures, _ = orchestrator.lifecycle_gate(task, status, "worker", force=True)
                            self.assertIn("semantic_intent_execute_authority_required", failures)
                delivery = self.task(self.envelope(intent_class="deliver", side_effect_class="local_write"))
                delivery_decision = orchestrator.semantic_task_decision(delivery)
                self.assertTrue(delivery_decision["policy"]["may_execute"])
                self.assertEqual(orchestrator.semantic_intent_lifecycle_failures(delivery, "claimed"), [])

    def test_nonempty_live_queue_observation_covers_valid_missing_and_invalid(self):
        registry = {"schema_version": "external_brain_capability_registry_v1", "capabilities": {"workflow_governance": {"brain": "workflow", "allowed_intents": ["govern"], "lane": "evolution", "task_classes": ["governance"], "brain_profiles": ["workflow"]}}}
        valid = self.task(self.envelope())
        valid.fm["id"] = "EBP-valid"
        missing = self.task(None)
        missing.fm["id"] = "EBP-missing"
        invalid_envelope = self.envelope()
        invalid_envelope["domain_capabilities"] = ["unknown"]
        invalid = self.task(invalid_envelope)
        invalid.fm["id"] = "EBP-invalid"
        with patch.object(orchestrator, "task_brain_semantic_registry", return_value=registry):
            passing = orchestrator.semantic_live_queue_observation([valid], strict=True)
            failing = orchestrator.semantic_live_queue_observation([valid, missing, invalid], strict=True)
        self.assertEqual(passing, {"status": "PASS", "active": 1, "missing": [], "invalid": []})
        self.assertEqual(failing["status"], "FAIL")
        self.assertEqual(failing["active"], 3)
        self.assertEqual(failing["missing"], ["semantic-task"])
        self.assertEqual(failing["invalid"], ["semantic-task"])

    def test_idle_readiness_is_neutral_but_unsafe_errors_fail(self):
        counts = {"active": 0, "dispatchable": 0, "by_lane": {"work": 218}}
        self.assertTrue(orchestrator.priority_preemption_ready(counts, set(), "work"))
        self.assertTrue(orchestrator.autorun_bridge_ready({"status": "PASS", "eligible": False, "reasons": ["no_dispatchable_task"]}))
        self.assertFalse(orchestrator.autorun_bridge_ready({"status": "FAIL", "eligible": False, "reasons": ["internal_error"]}))

    def test_specialized_intake_wrappers_forward_semantic_envelope(self):
        repo_raw = json.dumps(self.envelope(), ensure_ascii=False)
        repo_args = orchestrator.build_parser().parse_args([
            "add-repo-capability-absorption",
            "--source-url", "https://example.invalid/repo",
            "--capability-name", "example",
            "--capability-claim", "example claim",
            "--semantic-intent-json", repo_raw,
            "--dry-run",
        ])
        repo_result = orchestrator.command_add_repo_capability_absorption(repo_args)
        self.assertEqual(repo_result["delegated_add_args"]["semantic_intent_json"], repo_raw)

        work_raw = json.dumps(self.envelope(
            intent_class="deliver",
            domain_capabilities=["software_delivery"],
            routing={"lane": "work", "task_class": "delivery", "brain_profile": "engineering"},
            learning_scope="task",
            side_effect_class="local_write",
            multimodel={"mode": "forbidden", "purpose": "advisory", "triggers": []},
        ), ensure_ascii=False)
        work_args = orchestrator.build_parser().parse_args([
            "add-work-closeout-pair", "example closeout",
            "--semantic-intent-json", work_raw,
        ])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tasks = root / "tasks"
            tasks.mkdir()
            registry = json.loads((SCRIPT_DIR.parent / "brains" / "semantic-capabilities.json").read_text(encoding="utf-8"))
            registry["enforcement"]["strict_task_roots"] = [str(tasks)]
            with patch.object(orchestrator, "VAULT", root), patch.object(
                orchestrator, "TASKS_DIR", tasks
            ), patch.object(
                orchestrator, "task_brain_semantic_registry", return_value=registry
            ), patch.object(
                orchestrator, "refresh_derived_task_views", return_value={"status": "SKIPPED"}
            ), patch.object(
                orchestrator, "maybe_fire_taskpool_event_hook", return_value={"status": "SKIPPED"}
            ):
                result = orchestrator.command_add_work_closeout_pair(work_args)
                loaded_tasks = [
                    orchestrator.find_task(result["implementation_task"]["id"]),
                    orchestrator.find_task(result["ui_retest_task"]["id"]),
                ]
            self.assertEqual(result["status"], "OK")
            self.assertEqual(len(loaded_tasks), 2)
            for task in loaded_tasks:
                expected_intent = orchestrator.bind_semantic_concept_refs(
                    json.loads(work_raw), task.fm["concepts"]
                )
                self.assertEqual(task.fm["semantic_intent"], expected_intent)
                self.assertEqual(task.fm["semantic_contract_status"], "validated")
                decision = orchestrator.semantic_task_decision_from_fm(task.fm)
                self.assertEqual(decision["decision"], "route")

            malformed_fm, _ = orchestrator.split_frontmatter(
                orchestrator.render_frontmatter({
                    "semantic_intent": "{not-json}",
                    "semantic_contract_status": "validated",
                }) + "\n---\n"
            )
            self.assertIsInstance(malformed_fm["semantic_intent"], str)
            self.assertIsNone(orchestrator.semantic_task_decision_from_fm(malformed_fm))

    def test_inbox_write_forwards_only_explicit_semantic_envelope(self):
        raw = json.dumps(self.envelope(
            intent_class="deliver",
            domain_capabilities=["software_delivery"],
            routing={"lane": "work", "task_class": "delivery", "brain_profile": "engineering"},
            side_effect_class="local_write",
        ), ensure_ascii=False)
        args = orchestrator.build_parser().parse_args([
            "ingest-inbox", "--write", "--semantic-intent-json", raw,
        ])
        captured = []
        with tempfile.TemporaryDirectory() as tmp:
            inbox = Path(tmp) / "任务收件箱.md"
            inbox.write_text(
                "## Inbox Drafts\n- [ ] explicit envelope only | priority:P2 | project:test\n\n## Ingested Log\n",
                encoding="utf-8",
            )

            def capture_add(ns):
                captured.append(ns)
                return {"id": "captured", "link": "captured"}

            with patch.object(orchestrator, "INBOX", inbox), patch.object(
                orchestrator, "ensure_inbox", return_value=None
            ), patch.object(
                orchestrator, "command_add", side_effect=capture_add
            ), patch.object(
                orchestrator, "refresh_derived_task_views", return_value={"status": "SKIPPED"}
            ):
                result = orchestrator.command_ingest_inbox(args)
        self.assertEqual(result["created_count"], 1)
        self.assertEqual(captured[0].semantic_intent_json, raw)

    def test_review_gap_child_inherits_validated_parent_semantic_envelope(self):
        envelope = self.envelope(
            intent_class="deliver",
            domain_capabilities=["software_delivery"],
            routing={"lane": "work", "task_class": "delivery", "brain_profile": "engineering"},
            side_effect_class="local_write",
        )
        parent = orchestrator.Task(
            path=Path("/tmp/parent.md"),
            fm={
                "title": "parent",
                "status": "review",
                "priority": "P1",
                "project": "test",
                "lane": "work",
                "semantic_intent": envelope,
                "semantic_contract_status": "validated",
            },
            body="# parent\n",
        )
        gap = {
            "gap_types": ["missing_final_landed_evidence"],
            "required_evidence": ["artifact:proof"],
        }
        captured = []
        child = orchestrator.Task(
            path=Path("/tmp/child.md"),
            fm={"title": "child", "status": "pending", "project": "test", "lane": "work"},
            body="# child\n",
        )

        def capture_add(ns):
            captured.append(ns)
            return {"id": "child"}

        with patch.object(orchestrator, "command_add", side_effect=capture_add), patch.object(
            orchestrator, "find_task", return_value=child
        ), patch.object(
            orchestrator, "save_task", return_value=None
        ), patch.object(
            orchestrator, "maybe_fire_taskpool_event_hook", return_value={"status": "SKIPPED"}
        ):
            result = orchestrator.create_review_gap_repair_child(parent, gap, actor="test")
        self.assertEqual(result["action"], "created")
        self.assertEqual(json.loads(captured[0].semantic_intent_json), envelope)

    def test_internal_producers_fail_closed_without_validated_semantics_in_strict_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tasks = root / "tasks"
            tasks.mkdir()
            inbox = tasks / "任务收件箱.md"
            inbox.write_text(
                "## Inbox Drafts\n- [ ] no semantic authority | priority:P2 | project:test\n\n## Ingested Log\n",
                encoding="utf-8",
            )
            registry = json.loads((SCRIPT_DIR.parent / "brains" / "semantic-capabilities.json").read_text(encoding="utf-8"))
            registry["enforcement"]["strict_task_roots"] = [str(tasks)]
            inbox_args = orchestrator.build_parser().parse_args(["ingest-inbox", "--write"])
            with patch.object(orchestrator, "VAULT", root), patch.object(
                orchestrator, "TASKS_DIR", tasks
            ), patch.object(
                orchestrator, "INBOX", inbox
            ), patch.object(
                orchestrator, "ensure_inbox", return_value=None
            ), patch.object(
                orchestrator, "task_brain_semantic_registry", return_value=registry
            ):
                with self.assertRaisesRegex(SystemExit, "requires --semantic-intent-json"):
                    orchestrator.command_ingest_inbox(inbox_args)

                parent = orchestrator.Task(
                    path=tasks / "parent.md",
                    fm={
                        "title": "legacy parent",
                        "status": "review",
                        "priority": "P1",
                        "project": "test",
                        "lane": "work",
                    },
                    body="# parent\n",
                )
                gap = {
                    "gap_types": ["missing_final_landed_evidence"],
                    "required_evidence": ["artifact:proof"],
                }
                with self.assertRaisesRegex(SystemExit, "requires --semantic-intent-json"):
                    orchestrator.create_review_gap_repair_child(parent, gap, actor="test")
            self.assertEqual(list(tasks.glob("*.md")), [inbox])


if __name__ == "__main__":
    unittest.main()
