from __future__ import annotations

import json
import os
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone
from pathlib import Path

PLUGINS_DIR = Path(__file__).resolve().parents[2]
if str(PLUGINS_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGINS_DIR))

from neural_modular_memory.store import MemoryStore, _is_valid_pan, redact  # noqa: E402
from neural_modular_memory.provider import NeuralModularMemoryProvider  # noqa: E402
from agent.memory_manager import MemoryManager  # noqa: E402


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

    def test_same_turn_key_rejects_changed_content(self) -> None:
        self.store.ingest_turn(
            "s1", "原始请求。", "原始响应。", scope="session:s1", turn_key="turn-001"
        )
        with self.assertRaises(ValueError):
            self.store.ingest_turn(
                "s1", "被修改的请求。", "原始响应。", scope="session:s1", turn_key="turn-001"
            )

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

    def test_builtin_memory_write_receipts_are_redacted_append_only_and_not_recalled(self) -> None:
        secret = "«redacted:sk-…»"
        self.store.record_memory_write(
            action="add",
            target="user",
            content=f"User preference with api_key={secret}",
            metadata={"session_id": "s1", "old_text": f"old token={secret}"},
        )
        receipts = self.store.list_memory_write_receipts()
        self.assertEqual(1, len(receipts))
        serialized = json.dumps(receipts, ensure_ascii=False)
        self.assertNotIn(secret, serialized)
        self.assertIn("[REDACTED]", serialized)
        self.assertEqual(0, self.store.stats()["events"])
        self.assertEqual(0, self.store.stats()["projections"])
        self.assertEqual([], self.store.recall("preference", current_scope="session:s1"))
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.conn.execute(
                "UPDATE memory_write_receipts SET content_redacted='tampered' WHERE id=?",
                (receipts[0]["id"],),
            )
        self.store.conn.rollback()
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.conn.execute(
                "DELETE FROM memory_write_receipts WHERE id=?",
                (receipts[0]["id"],),
            )
        self.store.conn.rollback()

    def test_recursive_receipt_redaction_covers_dictionary_keys_and_nested_values(self) -> None:
        secret = "sk-metadata-key-secret-1234567890"
        self.store.record_memory_write(
            action="replace",
            target="memory",
            content="safe",
            metadata={
                f"api_key={secret}": {
                    "nested": [
                        {f"token={secret}": f"password={secret}"},
                        (f"secret={secret}",),
                    ]
                }
            },
        )
        receipts = self.store.list_memory_write_receipts()
        self.assertEqual(1, len(receipts))
        serialized = json.dumps(receipts, ensure_ascii=False)
        self.assertNotIn(secret, serialized)
        self.assertGreaterEqual(serialized.count("[REDACTED]"), 3)

    def test_v1_database_migrates_to_v3_without_losing_existing_events(self) -> None:
        self.store.ingest_turn("s1", "原始事件。", "确认。", turn_key="before-v3")
        self.assertTrue(self.store.recall("原始事件", current_scope="session:s1"))
        before_ids = {event["id"] for event in self.store.list_events()}
        before_stats = self.store.stats()
        before_fts = int(self.store.conn.execute("SELECT COUNT(*) FROM projections_fts").fetchone()[0])
        projection_id = self.store.list_projections()[0]["id"]
        strength_before = float(
            self.store.conn.execute("SELECT strength FROM projections WHERE id=?", (projection_id,)).fetchone()[0]
        )
        self.store.conn.execute("DROP TRIGGER memory_write_receipts_no_update")
        self.store.conn.execute("DROP TRIGGER memory_write_receipts_no_delete")
        self.store.conn.execute("DROP TABLE memory_write_receipts")
        self.store.conn.execute("ALTER TABLE projections DROP COLUMN last_decayed_at")
        self.store.conn.execute(
            "UPDATE metadata SET value='hermes.neural_modular_memory.v1' WHERE key='schema_version'"
        )
        self.store.conn.commit()
        self.store.close()

        self.store = MemoryStore(self.db)
        self.assertEqual(before_ids, {event["id"] for event in self.store.list_events()})
        self.assertEqual(0, self.store.stats()["memory_write_receipts"])
        after_stats = self.store.stats()
        for key in ("events", "projections", "edges", "activations"):
            self.assertEqual(before_stats[key], after_stats[key], key)
        self.assertEqual(
            before_fts,
            int(self.store.conn.execute("SELECT COUNT(*) FROM projections_fts").fetchone()[0]),
        )
        version = self.store.conn.execute(
            "SELECT value FROM metadata WHERE key='schema_version'"
        ).fetchone()[0]
        columns = {
            row["name"] for row in self.store.conn.execute("PRAGMA table_info(projections)").fetchall()
        }
        migrated = self.store.conn.execute(
            "SELECT strength,last_decayed_at FROM projections WHERE id=?", (projection_id,)
        ).fetchone()
        self.assertEqual("hermes.neural_modular_memory.v3", version)
        self.assertIn("last_decayed_at", columns)
        self.assertIsNone(migrated["last_decayed_at"])
        self.assertEqual("ok", self.store.conn.execute("PRAGMA integrity_check").fetchone()[0])
        triggers = {
            row["name"]
            for row in self.store.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='trigger'"
            ).fetchall()
        }
        self.assertTrue(
            {
                "events_no_update",
                "events_no_delete",
                "memory_write_receipts_no_update",
                "memory_write_receipts_no_delete",
            }.issubset(triggers)
        )
        self.store.decay(
            now=datetime(2030, 1, 1, tzinfo=UTC), half_life_days=1, archive_threshold=0.0
        )
        strength_after = float(
            self.store.conn.execute("SELECT strength FROM projections WHERE id=?", (projection_id,)).fetchone()[0]
        )
        self.assertEqual(strength_before, strength_after)

    def test_unknown_future_schema_fails_closed_without_rewriting_marker(self) -> None:
        self.store.conn.execute(
            "UPDATE metadata SET value='hermes.neural_modular_memory.v999' WHERE key='schema_version'"
        )
        self.store.conn.commit()
        self.store.close()

        with self.assertRaisesRegex(RuntimeError, "unsupported neural modular memory schema"):
            MemoryStore(self.db)

        conn = sqlite3.connect(self.db)
        try:
            version = conn.execute(
                "SELECT value FROM metadata WHERE key='schema_version'"
            ).fetchone()[0]
        finally:
            conn.close()
        self.assertEqual("hermes.neural_modular_memory.v999", version)

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

    def test_additional_credentials_and_payment_identifiers_are_redacted(self) -> None:
        aws_key = "AKIA" + "A" * 16
        cookie_value = "cookie-value-" + "c" * 32
        card_number = "4111" * 4
        self.store.ingest_turn(
            session_id="s1",
            user_text=(
                f"AWS_ACCESS_KEY_ID={aws_key}; "
                f"session_cookie={cookie_value}; "
                f"card_number={card_number}; 必须不要持久化这些值。"
            ),
            assistant_text="收到。",
            scope="session:s1",
            turn_key="sensitive-extensions",
        )
        serialized = json.dumps(
            {"events": self.store.list_events(), "projections": self.store.list_projections()},
            ensure_ascii=False,
        )
        self.assertNotIn(aws_key, serialized)
        self.assertNotIn(cookie_value, serialized)
        self.assertNotIn(card_number, serialized)

    def test_bare_compact_and_spaced_pan_are_redacted_before_persistence(self) -> None:
        compact = "4111111111111111"
        spaced = "4111 1111 1111 1111"
        self.store.ingest_turn(
            session_id="s1",
            user_text=f"候选卡号 {compact}，备用格式 {spaced}，必须不要持久化。",
            assistant_text="收到。",
            scope="session:s1",
            turn_key="bare-pan",
        )
        serialized = json.dumps(
            {"events": self.store.list_events(), "projections": self.store.list_projections()},
            ensure_ascii=False,
        )
        self.assertNotIn(compact, serialized)
        self.assertNotIn(spaced, serialized)
        self.assertGreaterEqual(serialized.count("[REDACTED]"), 2)

    def test_pan_length_and_separator_boundaries_do_not_partially_redact_longer_numbers(self) -> None:
        def valid_pan(length: int) -> str:
            prefix = "4" + "0" * (length - 2)
            for check_digit in "0123456789":
                candidate = prefix + check_digit
                if _is_valid_pan(candidate):
                    return candidate
            self.fail("unable to construct a valid PAN fixture")

        for length in range(13, 20):
            compact = valid_pan(length)
            variants = (compact, " ".join(compact), "-".join(compact))
            for variant in variants:
                self.assertEqual("[REDACTED]", redact(variant), (length, variant))

        short = valid_pan(13)[:12]
        long = valid_pan(19) + "7"
        outside_variants = (
            short,
            " ".join(short),
            "-".join(short),
            long,
            " ".join(long),
            "-".join(long),
        )
        for variant in outside_variants:
            self.assertEqual(variant, redact(variant), variant)

    def test_recall_updates_activation_telemetry_without_changing_strength(self) -> None:
        self.store.ingest_turn(
            "s1",
            "必须保留来源。",
            "收到。",
            scope="project:x",
            turn_key="activation-only",
        )
        before = {p["id"]: p for p in self.store.list_projections()}
        packet = self.store.recall("保留来源", current_scope="project:x")
        after = {p["id"]: p for p in self.store.list_projections()}

        self.assertTrue(packet)
        self.assertTrue(any(after[item["id"]]["access_count"] > before[item["id"]]["access_count"] for item in packet))
        self.assertTrue(all(after[item["id"]]["strength"] == before[item["id"]]["strength"] for item in packet))

    def test_recall_enforces_scope_and_budget(self) -> None:
        self.store.ingest_turn("s1", "项目火星必须保留来源。", "确认。", scope="project:mars")
        self.store.ingest_turn("s2", "项目金星必须保留来源。", "确认。", scope="project:venus")
        packet = self.store.recall("保留来源", current_scope="project:mars", limit=10, max_chars=420)
        text = json.dumps(packet, ensure_ascii=False)
        self.assertIn("火星", text)
        self.assertNotIn("金星", text)
        self.assertLessEqual(len(self.store.render_packet(packet, max_chars=420)), 420)

    def test_scope_matrix_only_includes_exact_scope_plus_global(self) -> None:
        scopes = {
            "session:s1": "会话甲",
            "task:t1": "任务乙",
            "project:p1": "项目丙",
            "user:u1": "用户丁",
            "domain:d1": "领域戊",
        }
        for index, (scope, marker) in enumerate(scopes.items()):
            self.store.ingest_turn(
                f"s{index}", f"{marker}必须保留边界。", "确认。", scope=scope, turn_key=str(index)
            )
        self.store.ingest_turn("global", "全局己必须保留边界。", "确认。", scope="global", turn_key="g")
        for scope, marker in scopes.items():
            with self.subTest(scope=scope):
                packet = self.store.recall("保留边界", current_scope=scope, limit=20)
                text = json.dumps(packet, ensure_ascii=False)
                self.assertIn(marker, text)
                self.assertIn("全局己", text)
                for other in set(scopes.values()) - {marker}:
                    self.assertNotIn(other, text)

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

    def test_correction_targets_the_replaced_subject_not_any_shared_token(self) -> None:
        self.store.ingest_turn(
            "s1",
            "我偏好 React 函数组件。",
            "记录为候选。",
            scope="user:u1",
            turn_key="react-functions",
        )
        self.store.ingest_turn(
            "s1",
            "我偏好 React 深色主题。",
            "记录为候选。",
            scope="user:u1",
            turn_key="react-theme",
        )
        self.store.ingest_turn(
            "s1",
            "纠正：不要 React 深色主题，改用浅色主题。",
            "已按新要求处理。",
            scope="user:u1",
            turn_key="react-theme-correction",
        )
        preferences = [p for p in self.store.list_projections() if p["module"] == "preference"]
        functions = [p for p in preferences if "函数组件" in p["claim"]]
        dark_theme = [p for p in preferences if "深色主题" in p["claim"]]
        self.assertTrue(functions)
        self.assertTrue(dark_theme)
        self.assertTrue(all(p["status"] != "contradicted" for p in functions))
        self.assertTrue(all(p["status"] == "contradicted" for p in dark_theme))

    def test_consolidation_requires_same_claim_from_two_independent_sessions(self) -> None:
        self.store.ingest_turn("s1", "必须保留来源。", "收到。", scope="project:x", turn_key="1")
        first = self.store.consolidate(min_sessions=2)
        self.assertEqual(0, first["consolidated"])
        self.store.ingest_turn("s2", "必须保留来源。", "收到。", scope="project:x", turn_key="1")
        second = self.store.consolidate(min_sessions=2)
        self.assertGreaterEqual(second["consolidated"], 1)
        matching = [p for p in self.store.list_projections() if p["module"] == "constraint"]
        self.assertTrue(any(p["status"] == "consolidated" for p in matching))

    def test_recall_does_not_promote_single_source_to_supported(self) -> None:
        self.store.ingest_turn("s1", "必须保留来源。", "收到。", scope="project:x", turn_key="1")
        self.store.recall("保留来源", current_scope="project:x")
        result = self.store.consolidate(min_sessions=2)
        matching = [p for p in self.store.list_projections() if p["module"] == "constraint"]
        self.assertEqual(0, result["supported"])
        self.assertTrue(all(p["status"] == "candidate" for p in matching))

    def test_two_sources_in_one_session_can_be_supported_but_not_consolidated(self) -> None:
        self.store.ingest_turn("s1", "必须保留来源。", "收到。", scope="project:x", turn_key="1")
        self.store.ingest_turn("s1", "必须保留来源。", "再次确认。", scope="project:x", turn_key="2")
        result = self.store.consolidate(min_sessions=2)
        matching = [p for p in self.store.list_projections() if p["module"] == "constraint"]
        self.assertGreaterEqual(result["supported"], 1)
        self.assertEqual(0, result["consolidated"])
        self.assertTrue(all(p["status"] == "supported" for p in matching))

    def test_active_contradiction_blocks_consolidation(self) -> None:
        self.store.ingest_turn("s1", "必须保留来源。", "收到。", scope="project:x", turn_key="1")
        self.store.ingest_turn("s2", "必须保留来源。", "收到。", scope="project:x", turn_key="1")
        self.store.ingest_turn("s3", "不能保留来源。", "收到。", scope="project:x", turn_key="1")
        positive = next(
            p for p in self.store.list_projections()
            if p["module"] == "constraint" and p["claim"] == "必须保留来源。"
        )
        negative = next(
            p for p in self.store.list_projections()
            if p["module"] == "constraint" and p["claim"] == "不能保留来源。"
        )
        self.store.conn.execute(
            "INSERT INTO edges(source_projection_id,target_projection_id,relation,created_at) VALUES(?,?, 'contradicts', ?)",
            (positive["id"], negative["id"], "2026-01-01T00:00:00+00:00"),
        )
        self.store.conn.commit()
        result = self.store.consolidate(min_sessions=2)
        matching = [
            p for p in self.store.list_projections()
            if p["module"] == "constraint" and p["claim"] == "必须保留来源。"
        ]
        self.assertEqual(0, result["consolidated"])
        self.assertTrue(all(p["status"] != "consolidated" for p in matching))

    def test_assistant_decision_requires_direct_evidence_before_consolidation(self) -> None:
        for session in ("s1", "s2"):
            self.store.ingest_turn(
                session,
                "请检查部署。",
                "决定：已完成部署。",
                scope="project:x",
                turn_key="without-evidence",
            )
        first = self.store.consolidate(min_sessions=2)
        decisions = [p for p in self.store.list_projections() if p["module"] == "decision"]
        self.assertEqual(0, first["consolidated"])
        self.assertTrue(all(p["status"] != "consolidated" for p in decisions))

        for session in ("s3", "s4"):
            self.store.ingest_turn(
                session,
                "请选择存储方案。",
                "决定采用事件存储。测试通过。",
                scope="project:x",
                turn_key="with-evidence",
            )
        second = self.store.consolidate(min_sessions=2)
        verified = [
            p for p in self.store.list_projections()
            if p["module"] == "decision" and "事件存储" in p["claim"]
        ]
        self.assertGreaterEqual(second["consolidated"], 1)
        self.assertTrue(all(p["status"] == "consolidated" for p in verified))

    def test_high_risk_consolidation_requires_evidence_in_every_supporting_session(self) -> None:
        for session in ("s1", "s2", "s3"):
            self.store.ingest_turn(
                session,
                "请选择存储方案。",
                "决定采用事件存储。测试通过。",
                scope="project:x",
                turn_key="per-session-evidence",
            )
        third_decision = next(
            p
            for p in self.store.list_projections()
            if p["module"] == "decision" and p["session_id"] == "s3"
        )
        self.store.conn.execute(
            "UPDATE projections SET module='episodic' WHERE source_event_id=? AND module='evidence'",
            (third_decision["source_event_id"],),
        )
        self.store.conn.commit()

        result = self.store.consolidate(min_sessions=2)
        decisions = [
            p
            for p in self.store.list_projections()
            if p["module"] == "decision" and p["semantic_key"] == third_decision["semantic_key"]
        ]
        self.assertEqual(0, result["consolidated"])
        self.assertTrue(all(p["status"] != "consolidated" for p in decisions))

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

    def test_decay_is_incremental_and_idempotent_at_the_same_timestamp(self) -> None:
        created = datetime(2025, 1, 1, tzinfo=UTC)
        self.store.ingest_turn(
            "s1", "记录普通事项。", "普通响应。", scope="session:s1", turn_key="1", observed_at=created
        )
        projection_id = self.store.list_projections()[0]["id"]
        initial = float(
            self.store.conn.execute("SELECT strength FROM projections WHERE id=?", (projection_id,)).fetchone()[0]
        )

        first_now = created + timedelta(days=10)
        self.store.decay(now=first_now, half_life_days=10, archive_threshold=0.0)
        after_first = float(
            self.store.conn.execute("SELECT strength FROM projections WHERE id=?", (projection_id,)).fetchone()[0]
        )
        self.store.decay(now=first_now, half_life_days=10, archive_threshold=0.0)
        after_repeat = float(
            self.store.conn.execute("SELECT strength FROM projections WHERE id=?", (projection_id,)).fetchone()[0]
        )
        self.store.decay(
            now=created + timedelta(days=20), half_life_days=10, archive_threshold=0.0
        )
        after_second_interval = float(
            self.store.conn.execute("SELECT strength FROM projections WHERE id=?", (projection_id,)).fetchone()[0]
        )

        self.assertAlmostEqual(initial * 0.5, after_first)
        self.assertAlmostEqual(after_first, after_repeat)
        self.assertAlmostEqual(initial * 0.25, after_second_interval)

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

    def test_pattern_completion_reuses_reference_and_expiry_gates(self) -> None:
        result = self.store.ingest_turn(
            "s1",
            "请设计方案，必须本地运行。",
            "采用事件存储。",
            scope="session:s1",
            turn_key="gated-siblings",
        )
        self.store.conn.execute(
            "UPDATE projections SET reference_only=0 WHERE source_event_id=? AND module='episodic'",
            (result["user_event_id"],),
        )
        self.store.conn.execute(
            "UPDATE projections SET expires_at=? WHERE source_event_id=? AND module='intent'",
            ("2020-01-01T00:00:00+00:00", result["user_event_id"]),
        )
        self.store.conn.commit()
        packet = self.store.recall(
            "本地运行",
            current_scope="session:s1",
            limit=6,
            complete_siblings=True,
            now=datetime(2026, 1, 1, tzinfo=UTC),
        )
        self.assertTrue(packet)
        self.assertTrue(all(item["reference_only"] == 1 for item in packet))
        self.assertTrue(
            all(item["expires_at"] is None or item["expires_at"] >= "2026-01-01T00:00:00+00:00" for item in packet)
        )

    def test_recall_rejects_missing_provenance_in_primary_and_sibling_paths(self) -> None:
        self.store.ingest_turn(
            "s1",
            "请设计方案，必须本地运行。",
            "采用事件存储。",
            scope="project:x",
            turn_key="provenance-gates",
        )
        user_event = next(e for e in self.store.list_events() if e["role"] == "user")
        self.store.conn.execute(
            "UPDATE projections SET source_hash=? WHERE source_event_id=? AND module IN ('constraint','episodic')",
            ("z" * 64, user_event["id"]),
        )
        self.store.conn.commit()
        packet = self.store.recall("本地运行", current_scope="project:x", limit=10)
        modules = {entry["module"] for entry in packet}
        self.assertNotIn("constraint", modules)
        self.assertNotIn("episodic", modules)

    def test_recall_rejects_well_formed_hash_that_does_not_match_source_event(self) -> None:
        self.store.ingest_turn(
            "s1",
            "必须保留来源。",
            "收到。",
            scope="project:x",
            turn_key="mismatched-provenance",
        )
        constraint = next(
            p for p in self.store.list_projections() if p["module"] == "constraint"
        )
        self.store.conn.execute(
            "UPDATE projections SET source_hash=? WHERE id=?",
            ("a" * 64, constraint["id"]),
        )
        self.store.conn.commit()

        packet = self.store.recall(
            "保留来源",
            current_scope="project:x",
            complete_siblings=False,
        )
        self.assertNotIn(constraint["id"], {item["id"] for item in packet})

    def test_fts_failure_returns_empty_instead_of_scanning_the_scope(self) -> None:
        self.store.ingest_turn(
            "s1",
            "必须保留来源。",
            "收到。",
            scope="project:x",
            turn_key="fts-fail-closed",
        )
        self.store.conn.execute("DROP TABLE projections_fts")
        self.store.conn.commit()
        self.assertEqual([], self.store.recall("保留来源", current_scope="project:x"))


class ProviderTests(unittest.TestCase):
    def test_provider_tracks_builtin_memory_writes_without_duplicate_projection(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            provider = NeuralModularMemoryProvider(
                {
                    "brainctl_path": str(home / "missing-brainctl.py"),
                    "store_path": str(home / "memory.sqlite3"),
                }
            )
            provider.initialize(
                "s1",
                hermes_home=str(home),
                platform="cli",
                agent_context="primary",
                agent_identity="default",
            )
            provider.on_memory_write(
                "add",
                "user",
                "User prefers concise replies",
                metadata={"session_id": "s1", "write_origin": "memory_tool"},
            )
            self.assertEqual("", provider.prefetch("concise replies", session_id="s1"))
            provider.shutdown()

            store = MemoryStore(home / "memory.sqlite3")
            receipts = store.list_memory_write_receipts()
            self.assertEqual(1, len(receipts))
            self.assertEqual("add", receipts[0]["action"])
            self.assertEqual("user", receipts[0]["target"])
            self.assertEqual(0, store.stats()["events"])
            self.assertEqual(0, store.stats()["projections"])
            store.close()

    def test_memory_manager_bridge_records_only_committed_builtin_writes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            provider = NeuralModularMemoryProvider(
                {
                    "brainctl_path": str(home / "missing-brainctl.py"),
                    "store_path": str(home / "memory.sqlite3"),
                }
            )
            provider.initialize(
                "s1",
                hermes_home=str(home),
                agent_context="primary",
                agent_identity="default",
            )
            manager = MemoryManager()
            manager.add_provider(provider)
            manager.notify_memory_tool_write(
                json.dumps({"success": True}),
                {
                    "target": "memory",
                    "operations": [
                        {"action": "replace", "content": "new value", "old_text": "old value"},
                        {"action": "remove", "old_text": "obsolete value"},
                    ],
                },
                build_metadata=lambda: {"session_id": "s1", "write_origin": "memory_tool"},
            )
            manager.notify_memory_tool_write(
                json.dumps({"success": False}),
                {"action": "add", "target": "memory", "content": "must not be mirrored"},
            )
            provider.shutdown()

            store = MemoryStore(home / "memory.sqlite3")
            receipts = store.list_memory_write_receipts()
            self.assertEqual(["replace", "remove"], [item["action"] for item in receipts])
            self.assertIn("old value", receipts[0]["metadata_redacted"])
            self.assertIn("obsolete value", receipts[1]["metadata_redacted"])
            self.assertNotIn("must not be mirrored", json.dumps(receipts))
            store.close()

    def test_provider_skips_non_primary_turn_writes_and_tracks_session_switch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            config = {
                "brainctl_path": str(home / "missing-brainctl.py"),
                "store_path": str(home / "memory.sqlite3"),
            }
            provider = NeuralModularMemoryProvider(config)
            provider.initialize(
                "child",
                hermes_home=str(home),
                agent_context="subagent",
                agent_identity="default",
            )
            provider.sync_turn("必须不落盘。", "收到。", session_id="child")
            provider.on_memory_write("add", "memory", "must not be mirrored")
            maintenance_calls = []
            store_handle = provider._store
            self.assertIsNotNone(store_handle)
            if store_handle is None:
                self.fail("provider store was not initialized")
            with patch.object(
                store_handle,
                "consolidate",
                side_effect=lambda **kwargs: maintenance_calls.append(("consolidate", kwargs)),
            ), patch.object(
                store_handle,
                "decay",
                side_effect=lambda **kwargs: maintenance_calls.append(("decay", kwargs)),
            ):
                provider.on_session_end([])
            self.assertEqual([], maintenance_calls)
            provider.shutdown()

            store = MemoryStore(home / "memory.sqlite3")
            self.assertEqual(0, store.stats()["events"])
            self.assertEqual(0, store.stats()["memory_write_receipts"])
            store.close()

            primary = NeuralModularMemoryProvider(config)
            primary.initialize(
                "s1",
                hermes_home=str(home),
                agent_context="primary",
                agent_identity="default",
            )
            primary.on_session_switch("s2", parent_session_id="s1", reset=True)
            primary.sync_turn("必须记录新会话。", "收到。")
            primary.shutdown()

            store = MemoryStore(home / "memory.sqlite3")
            self.assertEqual({"s2"}, {event["session_id"] for event in store.list_events()})
            store.close()

    def test_provider_consolidates_explicit_durable_preference_across_sessions(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            config = {
                "brainctl_path": str(home / "missing-brainctl.py"),
                "store_path": str(home / "memory.sqlite3"),
            }
            first = NeuralModularMemoryProvider(config)
            first.initialize("s1", hermes_home=str(home), agent_identity="default")
            first.sync_turn("我偏好蓝色主题。", "收到。", session_id="s1")
            first.shutdown()

            second = NeuralModularMemoryProvider(config)
            second.initialize("s2", hermes_home=str(home), agent_identity="default")
            second.sync_turn("我偏好蓝色主题。", "再次确认。", session_id="s2")
            second.on_session_end([])
            second.shutdown()

            store = MemoryStore(home / "memory.sqlite3")
            preferences = [p for p in store.list_projections() if p["module"] == "preference"]
            episodic = [p for p in store.list_projections() if p["module"] == "episodic"]
            self.assertTrue(preferences)
            self.assertEqual({"s1", "s2"}, {p["session_id"] for p in preferences})
            self.assertEqual(1, len({p["scope"] for p in preferences}))
            self.assertTrue(all(p["scope"].startswith("user:") for p in preferences))
            self.assertTrue(all("default" not in p["scope"] for p in preferences))
            self.assertTrue(all(p["status"] == "consolidated" for p in preferences))
            self.assertEqual({"session:s1", "session:s2"}, {p["scope"] for p in episodic})
            store.close()

            third = NeuralModularMemoryProvider(config)
            third.initialize("s3", hermes_home=str(home), agent_identity="default")
            recalled = third.prefetch("蓝色主题", session_id="s3")
            self.assertIn("蓝色主题", recalled)
            self.assertIn("scope=user:", recalled)
            third.shutdown()

            other_user = NeuralModularMemoryProvider(config)
            other_user.initialize("s4", hermes_home=str(home), agent_identity="other")
            self.assertNotIn("蓝色主题", other_user.prefetch("蓝色主题", session_id="s4"))
            other_user.shutdown()

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

    def test_provider_enforces_one_budget_across_brain_and_modular_recall(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            script = home / "brainctl.py"
            hit = {
                "path": "canonical.md",
                "line_start": 1,
                "line_end": 2,
                "content_hash": "b" * 64,
                "excerpt": "evidence " * 200,
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
                    "limit": 6,
                    "max_chars": 500,
                }
            )
            provider.initialize("s1", hermes_home=str(home))
            provider.sync_turn("必须保留本地来源。", "决定使用事件溯源。", session_id="s1")
            recalled = provider.prefetch("保留本地来源", session_id="s1")
            self.assertTrue(recalled)
            self.assertLessEqual(len(recalled), 500)
            self.assertIn("authority-neutral", recalled)
            provider.shutdown()

    def test_exact_local_brain_excerpt_suppresses_duplicate_modular_claims(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            script = home / "brainctl.py"
            hit = {
                "path": "canonical.md",
                "line_start": 1,
                "line_end": 1,
                "content_hash": "c" * 64,
                "excerpt": "必须保留本地来源。",
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
                    "limit": 6,
                    "max_chars": 2000,
                }
            )
            provider.initialize("s1", hermes_home=str(home))
            provider.sync_turn("必须保留本地来源。", "收到。", session_id="s1")
            recalled = provider.prefetch("保留本地来源", session_id="s1")
            self.assertEqual(1, recalled.count("必须保留本地来源。"))
            self.assertIn("canonical.md:1-1", recalled)
            self.assertNotIn("Neural modular memory", recalled)
            provider.shutdown()

    def test_truncated_uninjected_brain_hit_does_not_suppress_modular_claim(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            script = home / "brainctl.py"
            hits = [
                {
                    "path": "large.md",
                    "line_start": 1,
                    "line_end": 1,
                    "content_hash": "d" * 64,
                    "excerpt": "unrelated " * 200,
                },
                {
                    "path": "not-injected.md",
                    "line_start": 2,
                    "line_end": 2,
                    "content_hash": "e" * 64,
                    "excerpt": "必须保留本地来源。",
                },
            ]
            script.write_text(
                "import json\nprint(json.dumps(" + repr(hits) + "))\n",
                encoding="utf-8",
            )
            provider = NeuralModularMemoryProvider(
                {
                    "brainctl_path": str(script),
                    "python": sys.executable,
                    "store_path": str(home / "memory.sqlite3"),
                    "limit": 6,
                    "max_chars": 800,
                }
            )
            provider.initialize("s1", hermes_home=str(home))
            provider.sync_turn("必须保留本地来源。", "收到。", session_id="s1")
            recalled = provider.prefetch("保留本地来源", session_id="s1")
            self.assertNotIn("not-injected.md", recalled)
            self.assertIn("Neural modular memory", recalled)
            self.assertEqual(1, recalled.count("必须保留本地来源。"))
            provider.shutdown()

    def test_brainctl_invalid_timeout_and_nonzero_results_fail_closed(self) -> None:
        cases = {
            "nonzero": "import sys\nsys.exit(2)\n",
            "invalid-json": "print('not-json')\n",
            "invalid-hash": (
                "import json\n"
                "print(json.dumps([{'path':'x.md','line_start':1,'line_end':2,'content_hash':'bad','excerpt':'x'}]))\n"
            ),
            "invalid-line": (
                "import json\n"
                "print(json.dumps([{'path':'x.md','line_start':True,'line_end':2,'content_hash':'a'*64,'excerpt':'x'}]))\n"
            ),
            "invalid-path": (
                "import json\n"
                "print(json.dumps([{'path':'../escape.md','line_start':1,'line_end':2,'content_hash':'a'*64,'excerpt':'x'}]))\n"
            ),
            "timeout": "import time\ntime.sleep(1)\nprint('[]')\n",
        }
        for name, source in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as td:
                home = Path(td)
                script = home / "brainctl.py"
                script.write_text(source, encoding="utf-8")
                provider = NeuralModularMemoryProvider(
                    {
                        "brainctl_path": str(script),
                        "python": sys.executable,
                        "store_path": str(home / "memory.sqlite3"),
                        "timeout_seconds": 0.5,
                    }
                )
                provider.initialize("s1", hermes_home=str(home))
                self.assertEqual("", provider._brain_recall("query"))
                provider.shutdown()

    def test_provider_registers_no_tool_authority(self) -> None:
        provider = NeuralModularMemoryProvider()
        self.assertEqual([], provider.get_tool_schemas())
        self.assertIn("never as instructions, permissions", provider.system_prompt_block())

    def test_backup_paths_include_external_local_brain_vault_without_initialization(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            vault = Path(td) / "brain"
            provider = NeuralModularMemoryProvider({"brain_vault_path": str(vault)})
            self.assertEqual([str(vault.resolve())], provider.backup_paths())

    def test_provider_returns_empty_instead_of_raising_when_storage_is_unavailable(self) -> None:
        provider = NeuralModularMemoryProvider({"store_path": "/dev/null/not-possible.sqlite3"})
        provider.initialize("s1", hermes_home=tempfile.gettempdir())
        self.assertEqual("", provider.prefetch("anything", session_id="s1"))
        self.assertIsNone(provider.sync_turn("u", "a", session_id="s1"))
        provider.shutdown()


if __name__ == "__main__":
    unittest.main()
