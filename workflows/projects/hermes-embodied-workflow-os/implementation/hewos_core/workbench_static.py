from html import escape
from pathlib import Path

from .ledger import EvidenceLedger
from .loop_core import run_loop_core
from .projections import build_dashboard_projection, action_intent_projection, loop_receipt_projection


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
    loop_intent = {
        "intent_id": "ai.fixture.loop.review",
        "session_id": "fixture",
        "taskgraph_node_id": "node.loop.review",
        "actor_id": "hermes.local",
        "capability_id": "cap.web.text_observation",
        "verb": "advise",
        "target": {"surface": "workbench"},
        "parameters": {"text": "projection only"},
        "risk_level": "low",
        "preconditions": ["evidence_present"],
        "expected_observation_delta": {"loop_projection_visible": True},
        "verification_plan": ["receipt_readback", "static_html_readback"],
        "evidence_refs": ["ev.loop.fixture"],
        "requested_authority": ["local_projection"],
        "dry_run": True,
        "idempotency_key": "ai-fixture-loop-review",
        "rollback_or_abort": "discard projection",
    }
    human_gate_intent = dict(loop_intent)
    human_gate_intent.update(
        {
            "intent_id": "ai.fixture.loop.human_gate",
            "risk_level": "medium",
            "requested_authority": ["external_dispatch"],
            "idempotency_key": "ai-fixture-loop-human-gate",
        }
    )
    budget_intent = dict(loop_intent)
    budget_intent.update(
        {
            "intent_id": "ai.fixture.loop.budget_exhausted",
            "idempotency_key": "ai-fixture-loop-budget-exhausted",
        }
    )
    loop_receipts = [
        run_loop_core(
        {
            "state_id": "world.fixture.loop",
            "confidence": 0.65,
            "uncertainty": 0.2,
            "risk_level": "low",
            "evidence_refs": ["sha256:fixture"],
            "derived": {"visible_parts": ["fixture-part"]},
            "contradictions": [],
        },
        loop_intent,
        loop_budget=4,
        ),
        run_loop_core(
            {
                "state_id": "world.fixture.human-gate",
                "confidence": 0.42,
                "uncertainty": 0.47,
                "risk_level": "medium",
                "evidence_refs": ["sha256:fixture-authority"],
                "derived": {"visible_parts": ["operator-review-required"]},
                "contradictions": [],
            },
            human_gate_intent,
            loop_budget=4,
        ),
        run_loop_core(
            {
                "state_id": "world.fixture.budget-exhausted",
                "confidence": 0.44,
                "uncertainty": 0.72,
                "risk_level": "medium",
                "evidence_refs": ["sha256:fixture-contradiction"],
                "derived": {"visible_parts": ["conflicting-observation"]},
                "contradictions": ["fixture_conflicting_motion_signal"],
            },
            budget_intent,
            loop_budget=2,
        ),
    ]
    dashboard = build_dashboard_projection(capabilities, ledger.entries(), [action], loop_receipts)
    return dashboard, action, loop_receipts


def _li(items):
    return "".join(f"<li>{item}</li>" for item in items)


def render_workbench_html():
    dashboard, action, loop_receipts = _fixture_data()
    caps = _li(
        [
            (
                f"<span class=\"item-title\">{escape(item['capability_id'])}</span>"
                f"<span>{escape(item['capability_type'])}</span>"
                f"<strong>{escape(item['status'])}</strong>"
            )
            for item in dashboard["capabilities"]
        ]
    )
    evidence = _li(
        [
            (
                f"<span class=\"item-title\">{escape(item['entry_id'])}</span>"
                f"<span>{escape(item['kind'])}</span>"
                f"<strong>{escape(item['source'])}</strong>"
            )
            for item in dashboard["latest_evidence_entries"]
        ]
    )
    gates = _li(
        [
            "<span class=\"item-title\">SafetyGate</span><span>logic and risk</span><strong>closed</strong>",
            "<span class=\"item-title\">ExternalControlGate</span><span>identity and readback</span><strong>closed</strong>",
            "<span class=\"item-title\">OnsiteHumanGate</span><span>required for physical risk</span><strong>required</strong>",
        ]
    )
    loop_projection = loop_receipt_projection(loop_receipts[0])
    loop_gallery = _li(
        [
            (
                f"<span class=\"item-title\">{escape(item['action_intent_id'] or 'none')}</span>"
                f"<span>{escape(item['exit_reason'])} · {escape(item['risk_level'])}</span>"
                f"<strong>{item['loop_count']}/{item['loop_budget']}</strong>"
            )
            for item in [loop_receipt_projection(receipt) for receipt in loop_receipts]
        ]
    )
    loop_limits = _li([escape(item) for item in loop_projection["known_limits"]] or ["no known limits in fixture receipt"])
    loop_flags = _li(
        [
            f"<span class=\"item-title\">{escape(name.replace('credential_entry', 'secret_entry'))}</span><span>side effect flag</span><strong>{str(value).lower()}</strong>"
            for name, value in loop_projection["boundary_flags"].items()
        ]
    )
    visible = ", ".join(escape(part) for part in dashboard["world_state"].get("visible_parts", [])) or "none"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>HEWOS Workbench Static Fixture</title>
  <style>
    :root {{
      --bg: #071016;
      --surface: #0d1821;
      --surface-strong: #132534;
      --card: #111f2a;
      --card-soft: #0f1a22;
      --line: #244354;
      --line-strong: #3a6377;
      --text: #f5f9fc;
      --muted: #a9bdc8;
      --subtle: #78909d;
      --accent: #8ee7ff;
      --accent-strong: #c6f5ff;
      --good-bg: #123a2a;
      --good-text: #bff6d6;
      --warn-bg: #4b2d23;
      --warn-text: #ffd8c2;
      --blocked-bg: #4a252c;
      --blocked-text: #ffd4dc;
      --shadow: 0 22px 70px rgba(0, 0, 0, .34);
      --radius: 22px;
      color-scheme: dark;
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      min-height: 100dvh;
      font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at 15% 5%, rgba(142, 231, 255, .16), transparent 32rem),
        linear-gradient(135deg, var(--bg), #0b1218 54%, #05090d);
      color: var(--text);
      line-height: 1.55;
    }}
    a {{ color: inherit; }}
    a:focus-visible, section:focus-visible {{ outline: 3px solid var(--accent); outline-offset: 4px; }}
    .skip-link {{
      position: fixed; left: 1rem; top: .75rem; z-index: 10;
      transform: translateY(-180%); padding: .7rem 1rem; border-radius: 999px;
      background: var(--accent); color: #061017; font-weight: 800; text-decoration: none;
    }}
    .skip-link:focus {{ transform: translateY(0); }}
    .shell {{ width: min(1180px, calc(100% - 40px)); margin: 0 auto; padding: 32px 0 40px; }}
    header[role="banner"] {{
      display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(280px, .6fr); gap: 24px; align-items: stretch;
      margin-bottom: 22px;
    }}
    .hero, .status-panel, section {{
      border: 1px solid var(--line); border-radius: var(--radius); background: color-mix(in srgb, var(--surface) 88%, transparent);
      box-shadow: var(--shadow);
    }}
    .hero {{ padding: 34px; position: relative; overflow: hidden; }}
    .hero::after {{
      content: ""; position: absolute; inset: auto -8rem -10rem auto; width: 20rem; height: 20rem; border-radius: 50%;
      background: rgba(142, 231, 255, .11); filter: blur(8px); pointer-events: none;
    }}
    .eyebrow {{ margin: 0 0 12px; color: var(--accent); font-size: .82rem; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }}
    h1, h2, h3, p {{ margin-top: 0; }}
    h1 {{ margin-bottom: 14px; font-size: clamp(2.4rem, 6vw, 4.9rem); line-height: .92; letter-spacing: -.055em; text-wrap: balance; }}
    h2 {{ font-size: clamp(1.25rem, 2vw, 1.65rem); letter-spacing: -.025em; }}
    h3 {{ font-size: 1rem; color: var(--accent-strong); }}
    .lede {{ max-width: 66ch; color: var(--muted); font-size: clamp(1rem, 1.8vw, 1.18rem); text-wrap: pretty; }}
    .status-panel {{ padding: 22px; display: grid; gap: 14px; align-content: start; }}
    .badge-row {{ display: flex; flex-wrap: wrap; gap: 10px; }}
    .badge {{
      display: inline-flex; align-items: center; gap: .45rem; width: max-content;
      padding: .42rem .72rem; border-radius: 999px; font-size: .82rem; font-weight: 800;
      border: 1px solid color-mix(in srgb, currentColor 28%, transparent);
      background: var(--good-bg); color: var(--good-text);
    }}
    .badge.blocked {{ background: var(--blocked-bg); color: var(--blocked-text); }}
    .badge.warn {{ background: var(--warn-bg); color: var(--warn-text); }}
    nav[aria-label="Workbench sections"] {{
      display: flex; flex-wrap: wrap; gap: 10px; margin: 18px 0 26px;
    }}
    nav a {{
      text-decoration: none; padding: .7rem .9rem; border-radius: 999px; color: var(--muted);
      border: 1px solid var(--line); background: rgba(255,255,255,.025);
    }}
    nav a:hover {{ color: var(--text); border-color: var(--line-strong); }}
    main {{ display: grid; gap: 18px; }}
    .grid {{ display: grid; grid-template-columns: repeat(12, minmax(0, 1fr)); gap: 18px; }}
    section {{ padding: 24px; }}
    .span-7 {{ grid-column: span 7; }}
    .span-5 {{ grid-column: span 5; }}
    .span-6 {{ grid-column: span 6; }}
    .span-12 {{ grid-column: span 12; }}
    .metrics {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; margin: 18px 0; }}
    .metric {{ padding: 16px; border-radius: 18px; background: var(--card-soft); border: 1px solid var(--line); }}
    .metric strong {{ display: block; font-size: 1.8rem; line-height: 1; font-variant-numeric: tabular-nums; }}
    .metric span, .muted {{ color: var(--muted); }}
    .item-list {{ display: grid; gap: 10px; padding: 0; margin: 16px 0 0; list-style: none; }}
    .item-list li {{
      display: grid; grid-template-columns: minmax(170px, 1fr) auto auto; gap: 12px; align-items: center;
      padding: 14px; border-radius: 16px; background: var(--card); border: 1px solid var(--line);
    }}
    .item-title {{ font-weight: 850; color: var(--text); overflow-wrap: anywhere; }}
    .item-list strong {{ justify-self: end; color: var(--accent-strong); font-size: .88rem; }}
    .callout {{ border-left: 4px solid var(--accent); padding: 12px 14px; background: rgba(142, 231, 255, .07); border-radius: 14px; color: var(--muted); }}
    .review-card {{ display: grid; gap: 12px; }}
    .review-row {{ display: grid; grid-template-columns: minmax(120px, .45fr) minmax(0, 1fr); align-items: start; gap: 12px; border-bottom: 1px solid var(--line); padding-bottom: 10px; }}
    .review-row strong {{ justify-self: end; text-align: right; overflow-wrap: anywhere; min-width: 0; }}
    footer[role="contentinfo"] {{ margin-top: 24px; color: var(--subtle); font-size: .9rem; }}
    @media (max-width: 760px) {{
      .shell {{ width: min(100% - 24px, 680px); padding-top: 18px; }}
      header[role="banner"], .grid {{ grid-template-columns: 1fr; }}
      .span-7, .span-5, .span-6, .span-12 {{ grid-column: auto; }}
      .hero, .status-panel, section {{ padding: 18px; border-radius: 18px; }}
      .metrics {{ grid-template-columns: 1fr; }}
      .item-list li {{ grid-template-columns: 1fr; }}
      .item-list strong {{ justify-self: start; }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      *, *::before, *::after {{ scroll-behavior: auto !important; transition-duration: .01ms !important; animation-duration: .01ms !important; }}
    }}
  </style>
</head>
<body>
  <a class="skip-link" href="#main-content">Skip to content</a>
  <div class="shell">
    <header role="banner">
      <div class="hero">
        <p class="eyebrow">HEWOS / Projection only</p>
        <h1>Workbench for evidence-led operations.</h1>
        <p class="lede">Simulation-only static fixture for reviewing capability state, blocked ActionIntents, and EvidenceLedger replay without opening any real execution path.</p>
        <div class="badge-row" aria-label="Runtime safety summary">
          <span class="badge">Simulation-only</span>
          <span class="badge">Projection only</span>
          <span class="badge blocked">Blocked physical intent</span>
        </div>
      </div>
      <aside class="status-panel" aria-labelledby="runtime-status-title">
        <h2 id="runtime-status-title">Runtime status</h2>
        <p role="status" aria-live="polite" class="badge warn">Execution disabled</p>
        <p class="muted">Local browser view renders the same projection contract used by the static fixture. It is evidence display, not an operator actuator.</p>
      </aside>
    </header>

    <nav aria-label="Workbench sections">
      <a href="#dashboard">Dashboard</a>
      <a href="#loop-core">Ego-NeuroLoop</a>
      <a href="#action-review">Action review</a>
      <a href="#evidence-ledger">Evidence ledger</a>
      <a href="#gate-ladder">Gate ladder</a>
    </nav>

    <main id="main-content" role="main" tabindex="-1">
      <div class="grid">
        <section id="dashboard" class="span-7" aria-labelledby="dashboard-title" tabindex="-1">
          <h2 id="dashboard-title">Dashboard</h2>
          <p class="muted">Reducer-derived state from append-only evidence.</p>
          <div class="metrics" aria-label="Dashboard metrics">
            <div class="metric"><strong>{dashboard['capability_count']}</strong><span>Capabilities</span></div>
            <div class="metric"><strong>{dashboard['ledger_entry_count']}</strong><span>Ledger entries</span></div>
            <div class="metric"><strong>{dashboard['loop_receipt_count']}</strong><span>Loop receipts</span></div>
          </div>
          <p class="callout">Visible parts from replay: <strong>{visible}</strong></p>
          <ul class="item-list" aria-label="Capability projection list">{caps}</ul>
        </section>

        <section id="loop-core" class="span-5" aria-labelledby="loop-core-title" tabindex="-1">
          <p class="eyebrow">Runtime UI projection</p>
          <h2 id="loop-core-title">Ego-NeuroLoop LoopCore</h2>
          <p class="muted">Read-only projection of the local loop receipt. It shows prediction state, exit reason, and safety flags without exposing an execution control.</p>
          <div class="metrics" aria-label="Loop receipt metrics">
            <div class="metric"><strong>{loop_projection['loop_count']}/{loop_projection['loop_budget']}</strong><span>Loop depth</span></div>
            <div class="metric"><strong>{escape(loop_projection['exit_reason'])}</strong><span>Exit reason</span></div>
            <div class="metric"><strong>{escape(str(loop_projection['confidence']))}</strong><span>Confidence</span></div>
          </div>
          <div class="review-card" aria-label="LoopCore receipt details">
            <div class="review-row"><span>Receipt schema</span><strong>{escape(loop_projection['schema'])}</strong></div>
            <div class="review-row"><span>ActionIntent</span><strong>{escape(loop_projection['action_intent_id'] or 'none')}</strong></div>
            <div class="review-row"><span>Decode label</span><strong>{escape(loop_projection['deferred_decode_label'])}</strong></div>
            <div class="review-row"><span>Recommended action</span><strong>{escape(loop_projection['recommended_action'] or 'none')}</strong></div>
          </div>
          <h3>Boundary flags</h3>
          <ul class="item-list" aria-label="LoopCore side-effect flags">{loop_flags}</ul>
          <h3>Authorized local-state gallery</h3>
          <p class="muted">Safe promotable states are visible for review; closed states stay projected as blocked/read-only evidence, not controls.</p>
          <ul class="item-list" aria-label="LoopCore authorized local-state gallery">{loop_gallery}</ul>
          <h3>Known limits</h3>
          <ul class="item-list" aria-label="LoopCore known limits">{loop_limits}</ul>
        </section>

        <section id="action-review" class="span-5" aria-labelledby="action-review-title" tabindex="-1">
          <h2 id="action-review-title">ActionIntent Review</h2>
          <div class="review-card" aria-label="Blocked ActionIntent details">
            <div class="review-row"><span>Intent</span><strong>{escape(action['intent_id'])}</strong></div>
            <div class="review-row"><span>Risk</span><strong>{escape(action['risk_level'])}</strong></div>
            <div class="review-row"><span>Status</span><strong class="badge blocked">Blocked</strong></div>
          </div>
          <p class="callout">No real execution path is present in this artifact. Approval controls are intentionally absent in this local UI quality phase.</p>
        </section>

        <section id="evidence-ledger" class="span-6" aria-labelledby="evidence-ledger-title" tabindex="-1">
          <h2 id="evidence-ledger-title">EvidenceLedger</h2>
          <p class="muted">Append-only event projection with source and hash-backed evidence references.</p>
          <ul class="item-list" aria-label="Evidence ledger entries">{evidence}</ul>
        </section>

        <section id="gate-ladder" class="span-6" aria-labelledby="gate-ladder-title" tabindex="-1">
          <h2 id="gate-ladder-title">Gate ladder</h2>
          <p class="muted">Physical-risk actions remain closed until sequential gates produce exact receipts and readback.</p>
          <ul class="item-list" aria-label="Required gates">{gates}</ul>
        </section>
      </div>
    </main>
    <footer role="contentinfo">HEWOS Workbench fixture — local projection, deterministic replay, zero actuator path.</footer>
  </div>
</body>
</html>
"""


def write_workbench_html_fixture(path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_workbench_html(), encoding="utf-8")
    return path
