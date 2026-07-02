import http.client
import json
import sys
import threading
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hewos_core.workbench_runtime import WorkbenchHTTPServer, create_fixture_state, main, make_handler


class WorkbenchRuntimeTest(unittest.TestCase):
    def setUp(self):
        self.state = create_fixture_state()
        self.server = WorkbenchHTTPServer(("127.0.0.1", 0), make_handler(self.state))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = self.server.server_address

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def request(self, method, path):
        conn = http.client.HTTPConnection(self.base[0], self.base[1], timeout=5)
        conn.request(method, path)
        response = conn.getresponse()
        body = response.read().decode("utf-8")
        conn.close()
        return response.status, dict(response.getheaders()), body

    def test_allowed_endpoints_return_expected_content_types(self):
        status, headers, body = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", headers["Content-Type"])
        self.assertIn("HEWOS Workbench", body)

        for path in [
            "/healthz",
            "/projection/capabilities",
            "/projection/dashboard",
            "/projection/action-intents",
            "/projection/evidence-ledger",
        ]:
            status, headers, body = self.request("GET", path)
            self.assertEqual(status, 200, path)
            self.assertIn("application/json", headers["Content-Type"])
            json.loads(body)

    def test_forbidden_execute_and_side_effect_routes_are_absent(self):
        for path in ["/execute", "/send", "/deploy", "/taskpool", "/gateway", "/credential"]:
            status, _, body = self.request("GET", path)
            self.assertEqual(status, 404, path)
            self.assertNotIn("execute", body.lower())

    def test_projection_reflects_fixture_changes_without_server_mutating_state(self):
        before_count = len(self.state.ledger.entries())
        self.state.ledger.append(
            kind="observation",
            subject_id="obs.external.test",
            source="adapter.web.mock",
            claims=[{"claim": "external fixture mutation visible"}],
            evidence_refs=["sha256:external"],
            payload={"session_id": "runtime-test", "derived_facts": {"visible_parts": ["external-part"]}},
        )

        status, _, body = self.request("GET", "/projection/dashboard")
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual(payload["ledger_entry_count"], before_count + 1)
        self.assertIn("external-part", payload["world_state"]["visible_parts"])
        self.assertEqual(len(self.state.ledger.entries()), before_count + 1)

    def test_post_and_simulation_are_not_enabled(self):
        status, _, body = self.request("POST", "/simulation/observations")
        self.assertEqual(status, 405)
        self.assertIn("method_not_allowed", body)
    def test_main_accepts_host_and_port_flags(self):
        import hewos_core.workbench_runtime as runtime
        called = []
        original = runtime.serve
        try:
            def fake_serve(host="127.0.0.1", port=8787):
                called.append((host, port))
            runtime.serve = fake_serve
            main(["--host", "127.0.0.1", "--port", "8799"])
        finally:
            runtime.serve = original
        self.assertEqual(called, [("127.0.0.1", 8799)])


if __name__ == "__main__":
    unittest.main()
