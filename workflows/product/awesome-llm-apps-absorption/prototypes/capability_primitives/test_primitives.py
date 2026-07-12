import json
import tempfile
import unittest
from pathlib import Path

from primitives import GovernedToolRegistry, JsonMemoryStore, LocalEvidenceRetriever, ToolSpec


class FakeClock:
    def __init__(self): self.value = 1000.0
    def __call__(self): return self.value


class RetrieverTests(unittest.TestCase):
    def test_returns_source_bound_evidence(self):
        retriever = LocalEvidenceRetriever.from_texts({
            "rag": "RAG retrieves source chunks and requires citations.",
            "memory": "Memory records need owner isolation and TTL.",
        }, chunk_chars=100)
        result = retriever.search("RAG citations")
        self.assertEqual(result[0]["source_id"], "rag")
        self.assertIn("chunk_id", result[0])
        self.assertGreater(result[0]["score"], 0)

    def test_min_score_abstains(self):
        retriever = LocalEvidenceRetriever.from_texts({"rag": "RAG retrieves evidence."}, chunk_chars=100)
        self.assertEqual(retriever.search("retrieves", min_score=99), [])
        with self.assertRaises(ValueError):
            retriever.search("retrieves", min_score=-1)

    def test_empty_query_and_invalid_chunk_size_fail_closed(self):
        self.assertEqual(LocalEvidenceRetriever.from_texts({"a": "some text"}).search(""), [])
        with self.assertRaises(ValueError):
            LocalEvidenceRetriever.from_texts({"a": "text"}, chunk_chars=10)


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.clock = FakeClock()
        self.store = JsonMemoryStore(Path(self.tmp.name) / "memory.json", self.clock)

    def tearDown(self): self.tmp.cleanup()

    def test_owner_isolation_dedup_and_search(self):
        first = self.store.add("alice", "prefers evidence first")
        second = self.store.add("alice", "prefers   evidence first")
        self.store.add("bob", "prefers evidence first")
        self.assertEqual(first.id, second.id)
        self.assertEqual(len(self.store.list("alice")), 1)
        self.assertEqual(len(self.store.list("bob")), 1)
        self.assertEqual(self.store.search("alice", "evidence")[0].owner, "alice")

    def test_ttl_expires_and_invalid_ttl_rejected(self):
        self.store.add("alice", "temporary fact", ttl_seconds=5)
        self.clock.value += 6
        self.assertEqual(self.store.list("alice"), [])
        with self.assertRaises(ValueError): self.store.add("alice", "bad", ttl_seconds=0)

    def test_file_remains_valid_json(self):
        self.store.add("alice", "one")
        json.loads((Path(self.tmp.name) / "memory.json").read_text())

    def test_scoped_metadata_idempotency_and_deletion(self):
        metadata = {"domain": "research", "conversation_id": "c1", "role": "user", "provenance": "event-1"}
        first = self.store.add("alice", "first text", metadata=metadata, idempotency_key="event-1")
        second = self.store.add("alice", "retry text", metadata=metadata, idempotency_key="event-1")
        self.assertEqual(first.id, second.id)
        self.assertEqual(self.store.clear("alice", "other"), 0)
        self.assertTrue(self.store.delete("alice", first.id))
        self.assertFalse(self.store.delete("alice", first.id))

    def test_partial_scope_metadata_is_rejected(self):
        with self.assertRaises(ValueError):
            self.store.add("alice", "fact", metadata={"domain": "research"})


class ToolRegistryTests(unittest.TestCase):
    def test_discovery_and_read_only_invoke(self):
        reg = GovernedToolRegistry()
        reg.register(ToolSpec("length", "Return text length", "none", lambda text: len(text)))
        self.assertEqual(reg.discover()[0]["side_effect"], "none")
        self.assertEqual(reg.invoke("length", {"text": "abc"}), 3)

    def test_side_effect_denied_without_exact_allowance(self):
        reg = GovernedToolRegistry()
        reg.register(ToolSpec("write", "Writes", "local_write", lambda: "written"))
        with self.assertRaises(PermissionError): reg.invoke("write", {})
        self.assertEqual(reg.invoke("write", {}, allowed_effects={"local_write"}), "written")

    def test_unknown_duplicate_and_invalid_effect_fail_closed(self):
        reg = GovernedToolRegistry()
        reg.register(ToolSpec("x", "x", "none", lambda: None))
        with self.assertRaises(ValueError): reg.register(ToolSpec("x", "x", "none", lambda: None))
        with self.assertRaises(ValueError): reg.register(ToolSpec("y", "y", "magic", lambda: None))
        with self.assertRaises(KeyError): reg.invoke("missing", {})


if __name__ == "__main__": unittest.main()
