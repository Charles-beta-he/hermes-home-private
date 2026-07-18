from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

PLUGINS_DIR = Path(__file__).resolve().parents[2]
if str(PLUGINS_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGINS_DIR))

from neural_modular_memory.store import MemoryStore  # noqa: E402
from neural_modular_memory.provider import NeuralModularMemoryProvider  # noqa: E402


UTC = timezone.utc


class MemoryStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "memory.sqlite3"
        self.store = MemoryStore(self.db)

    def tearDown(self) -> None:
        self.store.close()
        self.tmp.cleanup()

    def test_one_source_creates_multiple_contract_driven_projections(self) -> None:
        result = self.store.ingest_turn(
            session_id="s1",
            user_text="请设计长期方案，必须本地运行，不要发送外部数据。",
            assistant_text="决定采用事件溯源，并保留来源证据。尚未完成独立验证。",
            scope="session:s1",
        )
        projections = self.store.list_projections(source_event_id=result["user_event_id"])
        modules = {item["module"] for item in projections}
        levels = {item["abstraction_level"] for item in projections}
        self.assertIn("episodic", modules)
        self.assertIn("intent", modules)
        self.assertIn("constraint", modules)
        self.assertGreaterEqual(len(modules), 3)
        self.assertIn("L1", levels)
        self.assertIn("L2", levels)
        self.assertTrue(all(item["source_hash"] for item in projections))
        self.assertTrue(all(item["reference_only"] == 1 for item in projections))

    def test_ingest_is_idempotent_for_same_session_and_turn(self) -> None:
        kwargs = dict(
            session_id="s1",
            user_text="请记录事实。",
            assistant_text="已记录。",
            scope="session:s1",
            turn_key="turn-001",
        )
        self.store.ingest_turn(**kwargs)
        first = self.store.stats()
        self.store.ingest_turn(**kwargs)
        second = self.store.stats()
        self.assertEqual(first["events"], 2)
        self.assertEqual(first, second)
        unique = {
            (p["source_event_id"], p["module"], p["semantic_key"], p["claim"])
            for p in self.store.list_projections()
        }
        self.assertEqual(len(unique), self.store.stats()["projections"])

    def test_l0_events_reject_update_and_delete(self) -> None:
        self.store.ingest_turn("s1", "原始证据。", "确认。", turn_key="immutable-1")
        event_id = self.store.list_events()[0]["id"]
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.conn.execute("UPDATE events SET text_redacted='tampered' WHERE id=?", (event_id,))
        self.store.conn.rollback()
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.conn.execute("DELETE FROM events WHERE id=?", (event_id,))
        self.store.conn.rollback()
        self.assertEqual(len(self.store.list_events()), 2)

    def test_secrets_are_redacted_before_events_and_projections_are_persisted(self) -> None:
        secret = "sk-abcdefghijklmnopqrstuvwxyz123456"
        key_body = "QUJD" * 32
        private_key = f"-----BEGIN PRIVATE KEY-----\n{key_body}\n-----END PRIVATE KEY-----"
        self.store.ingest_turn(
            session_id="s1",
            user_text=f"api_key={secret}，必须不要泄露。 Authorization: Bearer {secret}\n{private_key}",
            assistant_text="收到。",
            scope="session:s1",
        )
        serialized = json.dumps(
            {"events": self.store.list_events(), "projections": self.store.list_projections()},
            ensure_ascii=False,
        )
        self.assertNotIn(secret, serialized)
        self.assertNotIn(key_body, serialized)
        self.assertIn("[REDACTED", serialized)

    def test_recall_enforces_scope_and_budget(self) -> None:
        self.store.ingest_turn("s1", "项目火星必须保留来源。", "确认。", scope="project:mars")
        self.store.ingest_turn("s2", "项目金星必须保留来源。", "确认。", scope="project:venus")
        packet = self.store.recall("保留来源", current_scope="project:mars", limit=10, max_chars=420)
        text = json.dumps(packet, ensure_ascii=False)
        self.assertIn("火星", text)
        self.assertNotIn("金星", text)
        self.assertLessEqual(len(self.store.render_packet(packet, max_chars=420)), 420)

    def test_explicit_correction_preserves_old_projection_and_adds_supersession_edge(self) -> None:
        self.store.ingest_turn(
            "s1", "我偏好蓝色主题。必须本地运行。", "记录为候选。", scope="user:u1", turn_key="1"
        )
        before = self.store.stats()["projections"]
        self.store.ingest_turn(
            "s1",
            "纠正：不要蓝色主题，改用黑色主题。",
            "已按新要求处理。",
            scope="user:u1",
            turn_key="2",
        )
        projections = self.store.list_projections()
        old_theme = [p for p in projections if "蓝色主题" in p["claim"] and p["module"] == "preference"]
        unrelated = [p for p in projections if "本地运行" in p["claim"] and p["module"] == "constraint"]
        self.assertTrue(old_theme)
        self.assertTrue(all(p["status"] == "contradicted" for p in old_theme))
        self.assertTrue(unrelated)
        self.assertTrue(all(p["status"] != "contradicted" for p in unrelated))
        edges = self.store.list_edges()
        self.assertTrue(any(edge["relation"] in {"supersedes", "contradicts"} for edge in edges))
        self.assertGreater(self.store.stats()["projections"], before)

    def test_consolidation_requires_same_claim_from_two_independent_sessions(self) -> None:
        self.store.ingest_turn("s1", "必须保留来源。", "收到。", scope="project:x", turn_key="1")
        first = self.store.consolidate(min_sessions=2)
        self.assertEqual(0, first["consolidated"])
        self.store.ingest_turn("s2", "必须保留来源。", "收到。", scope="project:x", turn_key="1")
        second = self.store.consolidate(min_sessions=2)
        self.assertGreaterEqual(second["consolidated"], 1)
        matching = [p for p in self.store.list_projections() if p["module"] == "constraint"]
        self.assertTrue(any(p["status"] == "consolidated" for p in matching))

    def test_decay_archives_weak_projection_without_deleting_l0_events(self) -> None:
        old = datetime(2025, 1, 1, tzinfo=UTC)
        self.store.ingest_turn(
            "s1", "请临时记录普通事项。", "普通响应。", scope="session:s1", turn_key="1", observed_at=old
        )
        events_before = self.store.stats()["events"]
        result = self.store.decay(
            now=old + timedelta(days=365), half_life_days=7, archive_threshold=0.2
        )
        self.assertGreater(result["archived"], 0)
        self.assertEqual(events_before, self.store.stats()["events"])
        self.assertTrue(any(p["status"] == "archived" for p in self.store.list_projections()))

    def test_pattern_completion_only_adds_bounded_same_source_siblings(self) -> None:
        result = self.store.ingest_turn(
            "s1",
            "请设计方案，必须本地运行。",
            "采用事件存储。",
            scope="session:s1",
            turn_key="1",
        )
        packet = self.store.recall(
            "本地运行",
            current_scope="session:s1",
            limit=6,
            max_chars=1200,
            complete_siblings=True,
        )
        source_ids = {item["source_event_id"] for item in packet}
        self.assertIn(result["user_event_id"], source_ids)
        self.assertLessEqual(len(packet), 6)
        self.assertTrue(all(item["scope"] == "session:s1" for item in packet))


class ProviderTests(unittest.TestCase):
    def test_provider_wraps_brainctl_and_modular_recall_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            script = home / "brainctl.py"
            hit = {
                "path": "05-project/canonical.md",
                "line_start": 3,
                "line_end": 4,
                "content_hash": "a" * 64,
                "excerpt": "canonical source",
            }
            script.write_text(
                "import json\nprint(json.dumps([" + repr(hit) + "]))\n",
                encoding="utf-8",
            )
            provider = NeuralModularMemoryProvider(
                {
                    "brainctl_path": str(script),
                    "python": sys.executable,
                    "store_path": str(home / "memory.sqlite3"),
                    "limit": 4,
                }
            )
            provider.initialize("s1", hermes_home=str(home))
            provider.sync_turn(
                "必须保留本地来源。",
                "决定使用事件溯源。",
                session_id="s1",
            )
            recalled = provider.prefetch("保留本地来源", session_id="s1")
            self.assertIn("authority-neutral", recalled)
            self.assertIn("canonical.md:3-4", recalled)
            self.assertIn("Neural modular memory", recalled)
            self.assertIn("source_event=", recalled)
            provider.shutdown()

    def test_provider_returns_empty_instead_of_raising_when_storage_is_unavailable(self) -> None:
        provider = NeuralModularMemoryProvider({"store_path": "/dev/null/not-possible.sqlite3"})
        provider.initialize("s1", hermes_home=tempfile.gettempdir())
        self.assertEqual("", provider.prefetch("anything", session_id="s1"))
        self.assertIsNone(provider.sync_turn("u", "a", session_id="s1"))
        provider.shutdown()


if __name__ == "__main__":
    unittest.main()
