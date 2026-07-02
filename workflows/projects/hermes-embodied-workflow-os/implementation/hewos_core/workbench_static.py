from html import escape
from pathlib import Path

from .ledger import EvidenceLedger
from .projections import build_dashboard_projection, action_intent_projection


def _fixture_data():
    capabilities = [
        {
            "capability_id": "cap.web.text_observation",
            "actor_id": "actor.web.mock",
            "adapter_id": "adapter.web.mock",
            "capability_type": "observation",
            "risk_class": "none",
            "dry_run_default": True,
        },
        {
            "capability_id": "cap.robot.dry_run",
            "actor_id": "actor.robot.mock",
            "adapter_id": "adapter.robot.mock",
            "capability_type": "physical_action",
            "risk_class": "physical_action",
            "dry_run_default": True,
        },
    ]
    ledger = EvidenceLedger()
    ledger.append(
        kind="observation",
        subject_id="obs.fixture.1",
        source="adapter.web.mock",
        claims=[{"claim": "fixture part visible"}],
        evidence_refs=["sha256:fixture"],
        payload={"session_id": "fixture", "derived_facts": {"visible_parts": ["fixture-part"]}},
    )
    action = action_intent_projection(
        {
            "intent_id": "ai.fixture.blocked",
            "capability_id": "cap.robot.dry_run",
            "risk_level": "physical_action",
            "preview": "dry-run preview only",
            "required_gates": ["SafetyGate", "ExternalControlGate", "OnsiteHumanGate"],
            "evidence_refs": ["ev.1"],
        }
    )
    dashboard = build_dashboard_projection(capabilities, ledger.entries(), [action])
    return dashboard, action


def render_workbench_html():
    dashboard, action = _fixture_data()
    caps = "".join(
        f"<li>{escape(item['capability_id'])} — {escape(item['capability_type'])} — {escape(item['status'])}</li>"
        for item in dashboard["capabilities"]
    )
    evidence = "".join(
        f"<li>{escape(item['entry_id'])} — {escape(item['kind'])} — {escape(item['source'])}</li>"
        for item in dashboard["latest_evidence_entries"]
    )
    visible = ", ".join(escape(part) for part in dashboard["world_state"].get("visible_parts", [])) or "none"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>HEWOS Workbench Static Fixture</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 2rem; background: #101418; color: #f4f7fb; }}
    section {{ border: 1px solid #2d3a46; border-radius: 12px; padding: 1rem; margin: 1rem 0; background: #161d24; }}
    .badge {{ display: inline-block; padding: .2rem .5rem; border-radius: 999px; background: #2a533a; color: #b8ffd2; }}
    .blocked {{ background: #55302f; color: #ffd1cf; }}
  </style>
</head>
<body>
  <h1>HEWOS Workbench</h1>
  <p class="badge">Simulation-only static fixture</p>
  <section>
    <h2>Dashboard</h2>
    <p>Capabilities: {dashboard['capability_count']}</p>
    <p>Ledger entries: {dashboard['ledger_entry_count']}</p>
    <p>Visible parts from replay: {visible}</p>
    <ul>{caps}</ul>
  </section>
  <section>
    <h2>ActionIntent Review</h2>
    <p>Intent: {escape(action['intent_id'])}</p>
    <p>Risk: {escape(action['risk_level'])}</p>
    <p class="badge blocked">Status: {escape(action['status'])}</p>
    <p>No real execution path is present in this artifact.</p>
  </section>
  <section>
    <h2>EvidenceLedger</h2>
    <ul>{evidence}</ul>
  </section>
</body>
</html>
"""


def write_workbench_html_fixture(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_workbench_html(), encoding="utf-8")
    return path
