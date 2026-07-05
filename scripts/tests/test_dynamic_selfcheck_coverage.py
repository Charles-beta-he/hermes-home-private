import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import dynamic_selfcheck_coverage as dsc


def make_home(tmp_path: Path) -> Path:
    home = tmp_path
    hermes = home / ".hermes"
    (hermes / "cron").mkdir(parents=True)
    (hermes / "project-profiles").mkdir(parents=True)
    (hermes / "scripts").mkdir(parents=True)
    (hermes / "cron" / "jobs.json").write_text(json.dumps({
        "jobs": [
            {
                "id": "job1",
                "name": "telegram delivery job",
                "enabled": True,
                "deliver": "telegram:-100:1",
                "no_agent": True,
                "script": "daily.py",
                "last_status": "error",
                "last_delivery_error": "ProxyError 503",
            },
            {
                "id": "job2",
                "name": "local health",
                "enabled": True,
                "deliver": "local",
                "no_agent": True,
                "script": "health.py",
                "last_status": "ok",
            },
            {
                "id": "job3",
                "name": "model quorum job",
                "enabled": True,
                "deliver": "local",
                "script": "consult_models.py",
                "last_status": "error",
                "last_error": "RuntimeError: Connection error: rate limit 429",
            },
        ]
    }), encoding="utf-8")
    (hermes / "project-profiles" / "lark.json").write_text('{"name":"lark"}', encoding="utf-8")
    return home


def test_discovers_user_system_profile_from_cron_and_profiles(tmp_path):
    home = make_home(tmp_path)

    profile = dsc.discover_user_system_profile(home=home)

    system_ids = {s["system_id"] for s in profile["systems"]}
    assert "cron" in system_ids
    assert "delivery:telegram" in system_ids
    assert "profile:lark" in system_ids
    assert profile["summary"]["enabled_cron_jobs"] == 3
    assert profile["summary"]["delivery_error_jobs"] == 1


def test_registry_marks_missing_delivery_failure_coverage(tmp_path):
    home = make_home(tmp_path)
    profile = dsc.discover_user_system_profile(home=home)

    registry = dsc.build_coverage_registry(profile)

    telegram = next(s for s in registry["systems"] if s["system_id"] == "delivery:telegram")
    assert telegram["risk_level"] in {"high", "medium"}
    assert "delivery_failure_watch" in telegram["missing_checks"]
    assert telegram["evidence_refs"]


def test_change_aware_planner_maps_doctor_and_provider_changes():
    plan = dsc.plan_from_events([
        {"kind": "changed_file", "path": "hermes_cli/doctor.py"},
        {"kind": "changed_file", "path": "agent/openai_adapter.py"},
    ])

    check_ids = {c["check_id"] for c in plan["checks"]}
    assert "doctor_cli_smoke" in check_ids
    assert "doctor_fix_smoke" in check_ids
    assert "provider_runtime_smoke" in check_ids
    assert all(c["side_effects"] in {"none", "local_read", "local_write"} for c in plan["checks"])


def test_proposals_are_local_only_and_gated_for_delivery_failures(tmp_path):
    home = make_home(tmp_path)
    profile = dsc.discover_user_system_profile(home=home)
    registry = dsc.build_coverage_registry(profile)

    proposals = dsc.generate_proposals(registry)

    proposal = next(p for p in proposals if p["id"] == "proposal.delivery_failure_watch")
    assert proposal["deliver"] == "local"
    assert proposal["no_agent"] is True
    assert proposal["success_behavior"] == "silent"
    assert proposal["side_effects"] == "local_read"
    assert proposal["promotion"]["auto_promotable"] is True
    assert proposal["promotion"]["forbidden_without_authority"]


def test_cron_errors_are_clustered_into_actionable_local_groups(tmp_path):
    home = make_home(tmp_path)
    jobs = json.loads((home / ".hermes" / "cron" / "jobs.json").read_text(encoding="utf-8"))["jobs"]

    clusters = dsc.cluster_cron_errors(jobs)

    cluster_ids = {c["cluster_id"] for c in clusters["clusters"]}
    assert "delivery_proxy" in cluster_ids
    assert "model_provider_or_quota" in cluster_ids
    assert all(c["side_effects"] == "local_read" for c in clusters["clusters"])
    assert clusters["summary"]["error_jobs"] == 2


def test_provider_health_snapshot_is_fail_closed_without_certification_claim(tmp_path):
    home = make_home(tmp_path)
    snapshot = dsc.build_provider_health_snapshot(home=home, runner=lambda cmd: {"exit_code": 1, "output": "no planners available after quota gate"})

    assert snapshot["certification_status"] == "not_certified"
    assert snapshot["routing_safety"] == "fail_closed_for_model_quorum_automation"
    assert snapshot["side_effects"] == "local_read"
    assert snapshot["commands"][0]["exit_code"] == 1


def test_repair_packets_are_local_only_and_do_not_send(tmp_path):
    home = make_home(tmp_path)
    profile = dsc.discover_user_system_profile(home=home)
    registry = dsc.build_coverage_registry(profile)
    jobs = json.loads((home / ".hermes" / "cron" / "jobs.json").read_text(encoding="utf-8"))["jobs"]
    clusters = dsc.cluster_cron_errors(jobs)

    packets = dsc.generate_repair_packets(registry, clusters)

    packet = next(p for p in packets["packets"] if p["packet_id"] == "repair.delivery_proxy")
    assert packet["deliver"] == "local"
    assert packet["may_send_external"] is False
    assert "external_send" in packet["requires_authority_for"]
    assert packet["next_local_actions"]


def test_delivery_proxy_diagnostics_reads_latest_outputs_without_sending(tmp_path):
    home = make_home(tmp_path)
    out_dir = home / ".hermes" / "cron" / "output" / "job1"
    out_dir.mkdir(parents=True)
    (out_dir / "2026-07-05_09-00-00.md").write_text("old", encoding="utf-8")
    (out_dir / "2026-07-05_10-00-00.md").write_text("Telegram send failed: ProxyError 503", encoding="utf-8")
    jobs = json.loads((home / ".hermes" / "cron" / "jobs.json").read_text(encoding="utf-8"))["jobs"]
    clusters = dsc.cluster_cron_errors(jobs)

    diag = dsc.build_delivery_proxy_diagnostics(home, clusters, runner=lambda cmd: {"exit_code": 0, "output": "gateway run --replace\nNO_PROXY=example"})

    assert diag["may_send_external"] is False
    assert diag["side_effects"] == "local_read"
    assert diag["summary"]["diagnosed_jobs"] == 1
    assert diag["jobs"][0]["latest_output_excerpt"].endswith("ProxyError 503")


def test_lifecycle_marks_new_persistent_and_resolved_coverage_items(tmp_path):
    home = make_home(tmp_path)
    profile = dsc.discover_user_system_profile(home=home)
    registry = dsc.build_coverage_registry(profile)

    first = dsc.update_coverage_lifecycle(registry, previous=None, now="2026-07-06T00:00:00Z")
    delivery_key = "delivery:telegram::delivery_failure_watch"
    assert first["items"][delivery_key]["status"] == "active"
    assert first["items"][delivery_key]["first_seen_at"] == "2026-07-06T00:00:00Z"
    assert first["items"][delivery_key]["seen_count"] == 1
    assert first["items"][delivery_key]["retention_policy"]["severity"] == "high"

    second = dsc.update_coverage_lifecycle(registry, previous=first, now="2026-07-06T01:00:00Z")
    assert second["items"][delivery_key]["status"] == "active"
    assert second["items"][delivery_key]["first_seen_at"] == "2026-07-06T00:00:00Z"
    assert second["items"][delivery_key]["seen_count"] == 2

    resolved_registry = {**registry, "systems": [s for s in registry["systems"] if s["system_id"] != "delivery:telegram"]}
    third = dsc.update_coverage_lifecycle(resolved_registry, previous=second, now="2026-07-06T02:00:00Z")
    assert third["items"][delivery_key]["status"] == "resolved"
    assert third["items"][delivery_key]["resolved_at"] == "2026-07-06T02:00:00Z"
    assert third["items"][delivery_key]["absent_count"] == 1


def test_lifecycle_prunes_retired_resolved_items_after_retention():
    previous = {
        "schema": "hermes_coverage_lifecycle_v1",
        "items": {
            "old::gap": {
                "key": "old::gap",
                "system_id": "old",
                "check_id": "gap",
                "status": "resolved",
                "first_seen_at": "2026-07-01T00:00:00Z",
                "last_seen_at": "2026-07-01T00:00:00Z",
                "resolved_at": "2026-07-01T00:00:00Z",
                "seen_count": 1,
                "absent_count": 99,
                "retention_policy": {"resolved_retention_runs": 2, "severity": "low"},
            }
        },
    }
    registry = {"systems": []}

    lifecycle = dsc.update_coverage_lifecycle(registry, previous=previous, now="2026-07-06T00:00:00Z")

    assert "old::gap" not in lifecycle["items"]
    assert lifecycle["retired"][0]["key"] == "old::gap"


def test_cli_writes_registry_plan_proposals_and_operational_artifacts(tmp_path):
    home = make_home(tmp_path)
    out = home / ".hermes" / "state" / "selfcheck"

    result = dsc.run_once(home=home, output_dir=out, events=[{"kind": "changed_file", "path": "hermes_cli/doctor.py"}])

    assert Path(result["registry_path"]).exists()
    assert Path(result["plan_path"]).exists()
    assert Path(result["proposals_path"]).exists()
    assert Path(result["cron_error_clusters_path"]).exists()
    assert Path(result["provider_health_path"]).exists()
    assert Path(result["repair_packets_path"]).exists()
    assert Path(result["coverage_lifecycle_path"]).exists()
    loaded = json.loads(Path(result["registry_path"]).read_text(encoding="utf-8"))
    assert loaded["schema"] == "hermes_dynamic_selfcheck_coverage_v1"
    lifecycle = json.loads(Path(result["coverage_lifecycle_path"]).read_text(encoding="utf-8"))
    assert lifecycle["schema"] == "hermes_coverage_lifecycle_v1"
