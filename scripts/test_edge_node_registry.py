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

    def test_register_local_preserves_existing_dispatch_state(self):
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
  allowed_commands: ["date"]
  max_timeout: 300
""".strip(),
                encoding="utf-8",
            )
            registry.parent.mkdir(parents=True)
            registry.write_text(json.dumps({"schema": "edge_node_registry_v1", "dispatch_enabled": True, "nodes": []}), encoding="utf-8")
            with patch.object(edge_node_registry, "EDGE_CONFIG_PATH", cfg):
                result = edge_node_registry.register_local(path=registry)
            saved = json.loads(registry.read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "OK")
        self.assertTrue(result["dispatch_enabled"])
        self.assertTrue(saved["dispatch_enabled"])
        self.assertEqual(len(saved["nodes"]), 1)
        self.assertTrue(saved["nodes"][0]["dispatch_enabled"])
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
        checked = edge_node_registry.classify_node(node, now=__import__("time").time(), probe=False, registry_dispatch_enabled=True)
        self.assertIn("0.0.0.0 endpoint without token is unsafe", checked["errors"])
        self.assertFalse(checked["dispatch_eligible"])

    def test_readonly_standalone_node_can_be_dispatch_eligible_when_enabled(self):
        node = {
            "worker_id": "w1",
            "name": "node-a",
            "endpoint": "http://127.0.0.1:9001",
            "bind_host": "127.0.0.1",
            "brain_url": "",
            "standalone_mode": True,
            "capabilities": ["run_command", "read_file", "list_dir"],
            "token_configured": True,
            "allowed_commands_configured": True,
            "lease_policy": "local-readonly-smoke-allowlist",
            "dispatch_enabled": True,
            "last_seen_at": edge_node_registry.utc_now_iso(),
        }
        checked = edge_node_registry.classify_node(node, now=__import__("time").time(), probe=False, registry_dispatch_enabled=True)
        self.assertTrue(checked["dispatch_eligible"])
        self.assertFalse(checked["warnings"])

    def test_successful_probe_clears_stale_heartbeat_warning(self):
        node = {
            "worker_id": "w1",
            "name": "node-a",
            "endpoint": "http://127.0.0.1:9001",
            "bind_host": "127.0.0.1",
            "brain_url": "http://brain",
            "capabilities": ["read_file"],
            "token_configured": True,
            "allowed_commands_configured": True,
            "dispatch_enabled": True,
            "last_seen_at": "2026-01-01T00:00:00+00:00",
        }
        with patch.object(edge_node_registry, "probe_endpoint", return_value={"probe_status": "ok", "health": {"status": "ok"}, "info": {}}):
            checked = edge_node_registry.classify_node(node, now=__import__("time").time(), probe=True, registry_dispatch_enabled=True)
        self.assertEqual(checked["heartbeat_age_s"], 0)
        self.assertFalse(any("heartbeat stale" in item for item in checked["warnings"]))


if __name__ == "__main__":
    unittest.main()
