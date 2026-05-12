#!/usr/bin/env python3
"""Regression tests for replay_receipts.py.

Uses only stdlib unittest and a temporary Hermes state.db so it is safe to run
against a live Hermes install.
"""
from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

import replay_receipts as rr


class ReplayReceiptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = self.root / "state.db"
        conn = sqlite3.connect(self.db)
        conn.execute(
            "CREATE TABLE sessions (id TEXT PRIMARY KEY, title TEXT, model TEXT, started_at TEXT, ended_at TEXT, message_count INTEGER, tool_call_count INTEGER, estimated_cost_usd REAL)"
        )
        conn.execute(
            "CREATE TABLE messages (session_id TEXT, role TEXT, content TEXT, timestamp TEXT, tool_calls TEXT)"
        )
        conn.execute(
            "INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("sess_full_id_123456", "Replay fixture", "gpt-5.5", "2026-05-13T00:00:00Z", None, 2, 1, 0.0),
        )
        conn.execute(
            "INSERT INTO messages VALUES (?, ?, ?, ?, ?)",
            (
                "sess_full_id_123456",
                "user",
                "Please process TOKEN_VALUE=supersecret and /Users/example/private/path",
                "2026-05-13T00:00:01Z",
                None,
            ),
        )
        conn.execute(
            "INSERT INTO messages VALUES (?, ?, ?, ?, ?)",
            (
                "sess_full_id_123456",
                "assistant",
                "1 passed",
                "2026-05-13T00:00:02Z",
                json.dumps([{"function": {"name": "terminal", "arguments": {"command": "echo secret"}}}]),
            ),
        )
        conn.commit()
        conn.close()
        self.old_state_db = rr.STATE_DB
        self.old_keys_dir = rr.KEYS_DIR
        rr.STATE_DB = self.db
        rr.KEYS_DIR = self.root / "keys"

    def tearDown(self) -> None:
        rr.STATE_DB = self.old_state_db
        rr.KEYS_DIR = self.old_keys_dir
        self.tmp.cleanup()

    def test_generate_then_verify_full_artifact_wrapper(self) -> None:
        artifact = rr.generate_receipt("sess_full_id_123456", sign=False)
        self.assertNotIn("error", artifact)
        self.assertIn("receipt", artifact)
        self.assertGreaterEqual(len(artifact.get("redaction_findings", [])), 1)
        out = self.root / "receipt.json"
        out.write_text(json.dumps(artifact), encoding="utf-8")
        result = rr.verify_receipt(str(out))
        self.assertTrue(result.ok, result.errors)
        self.assertEqual(result.redaction_mode, "safe_share")

    def test_cli_list_keeps_full_session_id_width(self) -> None:
        sessions = rr.list_sessions(limit=1)
        self.assertEqual(sessions[0]["id"], "sess_full_id_123456")


if __name__ == "__main__":
    unittest.main(verbosity=2)
