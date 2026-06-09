import unittest

import kanban_coverage as kc


class KanbanCoverageTests(unittest.TestCase):
    def test_ready_nonspawnable_tasks_prevent_false_green_when_no_dispatchable_brain_tasks(self):
        report = kc.compute_coverage(
            brain_rows=[{"id": "brain-1", "dispatchable": False, "status": "review"}],
            kanban_stats={"by_status": {"ready": 2, "blocked": 1, "done": 3}},
            assignees=[
                {"name": "missing-a", "on_disk": False, "counts": {"ready": 1}},
                {"name": "missing-b", "on_disk": False, "counts": {"ready": 1}},
            ],
            dispatch_dry_run={"skipped_nonspawnable": ["t_a", "t_b"], "spawned": []},
            brain_notes=[{"status": "review", "text": "no kanban refs"}],
            kanban_tasks=[
                {"id": "t_a", "title": "Task - A", "status": "ready", "assignee": "missing-a", "body": ""},
                {"id": "t_b", "title": "Task - B", "status": "ready", "assignee": "missing-b", "body": ""},
            ],
        )

        self.assertEqual(report["schema_version"], "kanban_coverage_v2")
        self.assertEqual(report["counts"]["local_brain_dispatchable"], 0)
        self.assertEqual(report["counts"]["kanban_ready"], 2)
        self.assertEqual(report["counts"]["ready_nonspawnable"], 2)
        self.assertEqual(report["ids"]["skipped_nonspawnable"], ["t_a", "t_b"])
        self.assertEqual(report["coverage"]["dispatchable_mirror"], 1.0)
        self.assertEqual(report["coverage"]["kanban_ready_spawnability"], 0.0)
        self.assertLess(report["score"], 1.0)
        self.assertEqual(report["agent_coverage_v2"]["state"], "flow_profile_blocked")
        self.assertEqual(report["bottleneck"], "flow_coverage")

    def test_brain_note_provenance_counts_total_and_active_kanban_references(self):
        report = kc.compute_coverage(
            brain_rows=[{"id": "brain-1", "dispatchable": True, "status": "pending"}],
            kanban_stats={"by_status": {"ready": 1}, "by_assignee": {"brain-mirror": {"ready": 1}}},
            assignees=[{"name": "brain-mirror", "on_disk": True, "counts": {"ready": 1}}],
            dispatch_dry_run={"skipped_nonspawnable": [], "spawned": [{"task_id": "t_live"}]},
            brain_notes=[
                {"status": "pending", "text": "artifact /Users/x/.hermes/kanban/workspaces/t_1234abcd/report.md"},
                {"status": "done", "text": "old t_deadbeef reference"},
                {"status": "done", "text": "no reference"},
            ],
            kanban_tasks=[{"id": "t_live", "title": "Task - A", "status": "ready", "assignee": "brain-mirror", "body": ""}],
        )

        self.assertEqual(report["counts"]["brain_notes_total"], 3)
        self.assertEqual(report["counts"]["brain_notes_with_kanban_ref"], 2)
        self.assertEqual(report["counts"]["active_brain_notes_total"], 1)
        self.assertEqual(report["counts"]["active_brain_notes_with_kanban_ref"], 1)
        self.assertAlmostEqual(report["coverage"]["brain_note_provenance"], 2 / 3, places=3)
        self.assertEqual(report["coverage"]["active_brain_note_provenance"], 1.0)
        self.assertEqual(report["agent_coverage_v2"]["metrics"]["provenance_coverage"], 1.0)

    def test_blocked_done_source_is_stale_and_caps_score(self):
        report = kc.compute_coverage(
            brain_rows=[],
            kanban_stats={"by_status": {"blocked": 1}},
            assignees=[{"name": "brain-mirror", "on_disk": True, "counts": {"blocked": 1}}],
            dispatch_dry_run={"skipped_nonspawnable": [], "spawned": []},
            brain_notes=[{"status": "done", "title": "A", "text": "kanban ref t_aaaaaaaa"}],
            kanban_tasks=[{
                "id": "t_aaaaaaaa",
                "title": "Task - A",
                "status": "blocked",
                "assignee": "brain-mirror",
                "workspace_path": "/tmp/nope",
                "body": "Source: brain_task_orchestrator\nStatus: review",
            }],
        )

        v2 = report["agent_coverage_v2"]
        self.assertEqual(v2["state"], "flow_blocked_backlog")
        self.assertEqual(v2["stale_projection_ids"], ["t_aaaaaaaa"])
        self.assertIn("stale_projection_caps_score_at_0.75", v2["caps"])
        self.assertLessEqual(report["score"], 0.75)

    def test_review_required_blocked_card_aligns_with_brain_review_note(self):
        report = kc.compute_coverage(
            brain_rows=[],
            kanban_stats={"by_status": {"blocked": 1}},
            assignees=[{"name": "brain-mirror", "on_disk": True, "counts": {"blocked": 1}}],
            dispatch_dry_run={"skipped_nonspawnable": [], "spawned": []},
            brain_notes=[{"status": "review", "title": "A", "text": "workspace t_bbbbbbbb"}],
            kanban_tasks=[{
                "id": "t_bbbbbbbb",
                "title": "Task - A",
                "status": "blocked",
                "assignee": "brain-mirror",
                "workspace_path": "/tmp",
                "body": "Source: brain_task_orchestrator\nStatus: blocked",
                "result": "review-required: needs eyes before canonical writer promotion",
            }],
        )

        v2 = report["agent_coverage_v2"]
        self.assertEqual(v2["metrics"]["projection_coverage"], 1.0)
        self.assertEqual(v2["counts"]["projection_drift_tasks"], 0)
        self.assertEqual(v2["projection_drift"], [])

    def test_explicit_projection_exemption_counts_as_active_governed_coverage(self):
        report = kc.compute_coverage(
            brain_rows=[],
            kanban_stats={},
            assignees=[],
            dispatch_dry_run={},
            brain_notes=[{"status": "ready", "title": "No card", "text": "kanban_projection_exempt: direct-human-ui-task"}],
            kanban_tasks=[],
        )

        self.assertEqual(report["agent_coverage_v2"]["metrics"]["provenance_coverage"], 1.0)
        self.assertEqual(report["agent_coverage_v2"]["counts"]["active_notes_with_ref_or_exempt"], 1)

    def test_core_principle_map_is_present_for_operator_interpretation(self):
        report = kc.compute_coverage(
            brain_rows=[], kanban_stats={}, assignees=[], dispatch_dry_run={}, brain_notes=[]
        )

        principles = report["principles"]
        self.assertIn("toyota_lean_flow", principles)
        self.assertIn("goldratt_toc", principles)
        self.assertIn("anderson_kanban", principles)
        self.assertIn("kleppmann_ddia_event_sourcing", principles)
        self.assertIn("twelve_factor_agents", principles)


if __name__ == "__main__":
    unittest.main()
