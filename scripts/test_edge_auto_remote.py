#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).with_name("edge_auto_remote.py")
spec = importlib.util.spec_from_file_location("edge_auto_remote", SCRIPT)
assert spec and spec.loader
edge_auto_remote = importlib.util.module_from_spec(spec)
spec.loader.exec_module(edge_auto_remote)


class EdgeAutoRemoteTests(unittest.TestCase):
    def test_dispatch_blocks_when_registry_disabled(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            registry = home / "state" / "edge_node_registry.json"
            audit = home / "logs" / "audit.jsonl"
            registry.parent.mkdir(parents=True)
            registry.write_text(json.dumps({"schema": "edge_node_registry_v1", "dispatch_enabled": False, "nodes": []}), encoding="utf-8")
            with patch.object(edge_auto_remote, "REGISTRY_PATH", registry), \
                 patch.object(edge_auto_remote, "AUDIT_PATH", audit), \
                 patch.object(edge_auto_remote, "PAUSE_PATH", home / "state" / "pause"):
                result = edge_auto_remote.dispatch("date")
                audit_exists = audit.exists()
        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "blocked")
        self.assertIn("no eligible edge node", result["reason"])
        self.assertTrue(audit_exists)

    def test_dispatch_blocks_non_readonly_command_before_network(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            registry = home / "state" / "edge_node_registry.json"
            audit = home / "logs" / "audit.jsonl"
            registry.parent.mkdir(parents=True)
            registry.write_text(json.dumps({"schema": "edge_node_registry_v1", "dispatch_enabled": True, "nodes": []}), encoding="utf-8")
            with patch.object(edge_auto_remote, "REGISTRY_PATH", registry), \
                 patch.object(edge_auto_remote, "AUDIT_PATH", audit), \
                 patch.object(edge_auto_remote, "PAUSE_PATH", home / "state" / "pause"):
                result = edge_auto_remote.dispatch("rm -rf /tmp/nope")
        self.assertFalse(result["success"])
        self.assertIn("not in automatic read-only allowlist", result["reason"])

    def test_dispatch_success_writes_readonly_lease_proof(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            registry = home / "state" / "edge_node_registry.json"
            audit = home / "logs" / "audit.jsonl"
            env = home / ".env"
            registry.parent.mkdir(parents=True)
            registry.write_text(json.dumps({
                "schema": "edge_node_registry_v1",
                "dispatch_enabled": True,
                "nodes": [{
                    "worker_id": "local:test:127.0.0.1:9001",
                    "endpoint": "http://127.0.0.1:9001",
                    "status": "healthy",
                    "dispatch_enabled": True,
                    "token_configured": True,
                    "allowed_commands_configured": True,
                    "trust_level": "local_configured",
                }],
            }), encoding="utf-8")
            env.write_text("HERMES_EDGE_WORKER_ACCESS=test-value\n", encoding="utf-8")
            with patch.object(edge_auto_remote, "REGISTRY_PATH", registry), \
                 patch.object(edge_auto_remote, "AUDIT_PATH", audit), \
                 patch.object(edge_auto_remote, "ENV_PATH", env), \
                 patch.object(edge_auto_remote, "PAUSE_PATH", home / "state" / "pause"), \
                 patch.dict(os.environ, {}, clear=True), \
                 patch.object(edge_auto_remote, "post_command", return_value={"http_status": 200, "body": {"success": True, "exit_code": 0, "stdout": "Darwin\n", "stderr": ""}}):
                result = edge_auto_remote.dispatch("uname -s", event={"event_id": "evt1", "event_type": "task.created"})
                audit_exists = audit.exists()
                audit_text = audit.read_text(encoding="utf-8") if audit_exists else ""
        self.assertTrue(result["success"])
        self.assertTrue(result["read_only"])
        self.assertTrue(result["auto_dispatch"])
        self.assertTrue(result["access_redacted"])
        self.assertEqual(result["event_id"], "evt1")
        self.assertTrue(audit_exists)
        self.assertIn("edge-lease-", audit_text)


if __name__ == "__main__":
    unittest.main()
