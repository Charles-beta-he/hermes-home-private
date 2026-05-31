#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).with_name("edge_node_registry.py")
spec = importlib.util.spec_from_file_location("edge_node_registry", SCRIPT)
assert spec and spec.loader
edge_node_registry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(edge_node_registry)


class EdgeNodeRegistryTests(unittest.TestCase):
    def test_config_parser_redacts_token_and_extracts_worker_shape(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = Path(td) / "config.yaml"
            cfg.write_text(
                """
worker:
  name: "node-a"
  host: "0.0.0.0"  # LAN
  port: 9001
  brain_url: ""
  heartbeat_interval: 30
security:
  token: "secret-token-value"
  allowed_commands: []
  max_timeout: 300
""".strip(),
                encoding="utf-8",
            )
            parsed = edge_node_registry.read_edge_config(cfg)
        self.assertTrue(parsed["exists"])
        self.assertEqual(parsed["worker"]["name"], "node-a")
        self.assertEqual(parsed["worker"]["host"], "0.0.0.0")
        self.assertEqual(parsed["worker"]["port"], 9001)
        self.assertTrue(parsed["security"]["token_configured"])
        self.assertNotIn("secret-token-value", json.dumps(parsed, ensure_ascii=False))

    def test_selfcheck_is_warn_only_for_standalone_local_node(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            cfg = home / "edge-worker" / "config.yaml"
            cfg.parent.mkdir(parents=True)
            cfg.write_text(
                """
worker:
  name: "node-a"
  host: "127.0.0.1"
  port: 9001
  brain_url: ""
  heartbeat_interval: 30
security:
  token: "secret-token-value"
  allowed_commands: []
  max_timeout: 300
""".strip(),
                encoding="utf-8",
            )
            with patch.object(edge_node_registry, "HERMES_HOME", home), \
                 patch.object(edge_node_registry, "STATE_DIR", home / "state"), \
                 patch.object(edge_node_registry, "REGISTRY_PATH", home / "state" / "edge_node_registry.json"), \
                 patch.object(edge_node_registry, "EDGE_CONFIG_PATH", cfg):
                result = edge_node_registry.selfcheck(probe=False)
        self.assertEqual(result["status"], "WARN")
        self.assertEqual(result["node_count"], 1)
        self.assertEqual(result["dispatch_eligible_count"], 0)
        self.assertTrue(any("brain_url missing" in w for w in result["warnings"]))
        self.assertFalse(result["dispatch_enabled"])

    def test_register_local_persists_redacted_node_without_enabling_dispatch(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            cfg = home / "edge-worker" / "config.yaml"
            registry = home / "state" / "edge_node_registry.json"
            cfg.parent.mkdir(parents=True)
            cfg.write_text(
                """
worker:
  name: "node-a"
  host: "127.0.0.1"
  port: 9001
  brain_url: ""
  heartbeat_interval: 30
security:
  token: "secret-token-value"
  allowed_commands: []
  max_timeout: 300
""".strip(),
                encoding="utf-8",
            )
            with patch.object(edge_node_registry, "EDGE_CONFIG_PATH", cfg):
                result = edge_node_registry.register_local(path=registry)
            saved = json.loads(registry.read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "OK")
        self.assertFalse(result["dispatch_enabled"])
        self.assertFalse(saved["dispatch_enabled"])
        self.assertEqual(len(saved["nodes"]), 1)
        self.assertTrue(saved["nodes"][0]["token_configured"])
        self.assertNotIn("secret-token-value", json.dumps(saved, ensure_ascii=False))

    def test_unsafe_unauthenticated_lan_binding_is_fail_in_edge_selfcheck_only(self):
        node = {
            "worker_id": "w1",
            "name": "node-a",
            "endpoint": "http://127.0.0.1:9001",
            "bind_host": "0.0.0.0",
            "brain_url": "http://brain",
            "capabilities": ["run_command"],
            "token_configured": False,
            "allowed_commands_configured": True,
            "last_seen_at": edge_node_registry.utc_now_iso(),
        }
        checked = edge_node_registry.classify_node(node, now=__import__("time").time(), probe=False)
        self.assertIn("0.0.0.0 endpoint without token is unsafe", checked["errors"])
        self.assertFalse(checked["dispatch_eligible"])


if __name__ == "__main__":
    unittest.main()
