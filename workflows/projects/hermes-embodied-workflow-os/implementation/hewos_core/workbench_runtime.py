"""PROJECTION-ONLY local Web Workbench runtime.

This runtime serves read-only snapshots from in-memory fixtures. It is NOT a
source of truth and MUST NOT mutate CapabilityRegistry or EvidenceLedger state
from projection routes. It contains no executor route, no external adapter path,
no credential path, and no hardware or robot control path.
"""

import argparse
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from urllib.parse import urlparse

from .ledger import EvidenceLedger
from .projections import (
    action_intent_projection,
    build_dashboard_projection,
    capability_projection,
    evidence_entry_projection,
)
from .workbench_static import render_workbench_html


@dataclass
class WorkbenchState:
    capabilities: list
    ledger: EvidenceLedger
    action_intents: list


def create_fixture_state():
    ledger = EvidenceLedger()
    ledger.append(
        kind="observation",
        subject_id="obs.runtime.fixture",
        source="adapter.web.mock",
        claims=[{"claim": "runtime fixture visible"}],
        evidence_refs=["sha256:runtime-fixture"],
        payload={"session_id": "runtime-fixture", "derived_facts": {"visible_parts": ["runtime-fixture-part"]}},
    )
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
    action_intents = [
        {
            "intent_id": "ai.runtime.blocked",
            "capability_id": "cap.robot.dry_run",
            "risk_level": "physical_action",
            "preview": "dry-run preview only",
            "required_gates": ["SafetyGate", "ExternalControlGate", "OnsiteHumanGate"],
            "evidence_refs": ["ev.1"],
        }
    ]
    return WorkbenchState(capabilities=capabilities, ledger=ledger, action_intents=action_intents)


class WorkbenchHTTPServer(HTTPServer):
    pass


def _json_snapshot(payload):
    return json.loads(json.dumps(payload, sort_keys=True, ensure_ascii=False))


def _projection_payload(state, path):
    if path == "/healthz":
        return {"ok": True, "mode": "local_projection_only", "execution_enabled": False}
    if path == "/projection/capabilities":
        return [capability_projection(item) for item in state.capabilities]
    if path == "/projection/action-intents":
        return [action_intent_projection(item) for item in state.action_intents]
    if path == "/projection/evidence-ledger":
        return [evidence_entry_projection(item) for item in state.ledger.entries()]
    if path == "/projection/dashboard":
        return build_dashboard_projection(state.capabilities, state.ledger.entries(), state.action_intents)
    raise KeyError(path)


def make_handler(state):
    class WorkbenchHandler(BaseHTTPRequestHandler):
        server_version = "HEWOSWorkbench/0.1"

        def log_message(self, format, *args):
            return

        def _write(self, status, content_type, body):
            raw = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(raw)

        def _write_json(self, status, payload):
            body = json.dumps(_json_snapshot(payload), ensure_ascii=False, indent=2, sort_keys=True)
            self._write(status, "application/json; charset=utf-8", body)

        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/":
                self._write(200, "text/html; charset=utf-8", render_workbench_html())
                return
            try:
                self._write_json(200, _projection_payload(state, path))
            except KeyError:
                self._write_json(404, {"error": "not_found"})

        def do_POST(self):
            self._write_json(405, {"error": "method_not_allowed", "mode": "projection_only"})

    return WorkbenchHandler


def serve(host="127.0.0.1", port=8787):
    server = WorkbenchHTTPServer((host, port), make_handler(create_fixture_state()))
    try:
        server.serve_forever()
    finally:
        server.server_close()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run HEWOS projection-only local Workbench runtime")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args(argv)
    serve(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
