#!/usr/bin/env python3
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("local_brain_mcp_projection.py")
spec = importlib.util.spec_from_file_location("local_brain_mcp_projection", SCRIPT)
assert spec and spec.loader
projection = importlib.util.module_from_spec(spec)
spec.loader.exec_module(projection)


class LocalBrainMcpProjectionTest(unittest.TestCase):
    def test_builds_hash_bound_metadata_only_projection(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            note = vault / "note.md"
            note.write_text(
                "---\nconcepts: [theory-impact-propagation, impact-smoothing]\nstatus: active\n---\nSECRET BODY MUST NOT LEAK\n",
                encoding="utf-8",
            )
            result = projection.build_projection(vault, limit=10)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["authority"], "read_only_projection_no_mcp_write")
        self.assertEqual(result["counts"], {"notes": 1, "concepts": 2, "relations": 2})
        rendered = json.dumps(result, ensure_ascii=False)
        self.assertNotIn("SECRET BODY", rendered)
        self.assertIn("theory-impact-propagation", rendered)
        note_entity = next(x for x in result["entities"] if x["entityType"] == "brain_note")
        self.assertRegex(note_entity["observations"][1], r"^sha256:[0-9a-f]{64}$")

    def test_is_bounded_and_never_writes_mcp_memory(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp)
            for index in range(3):
                (vault / f"{index}.md").write_text(f"---\nconcepts: [c-{index}]\n---\nbody\n", encoding="utf-8")
            result = projection.build_projection(vault, limit=2)
            self.assertEqual(result["counts"]["notes"], 2)
            self.assertFalse((vault / "mcp-memory.json").exists())
            self.assertTrue(result["truncated"])

    def test_apply_preserves_foreign_graph_and_is_idempotent_with_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            vault = root / "vault"
            vault.mkdir()
            (vault / "note.md").write_text("---\nconcepts: [alpha]\n---\nbody\n", encoding="utf-8")
            memory = root / "memory.json"
            memory.write_text(json.dumps({
                "type": "entity", "name": "foreign", "entityType": "user", "observations": ["keep"]
            }) + "\n", encoding="utf-8")
            projected = projection.build_projection(vault)
            first = projection.apply_projection(projected, memory, backup_dir=root / "backups", expected_target=memory)
            first_bytes = memory.read_bytes()
            second = projection.apply_projection(projected, memory, backup_dir=root / "backups", expected_target=memory)
            second_bytes = memory.read_bytes()
            graph = [json.loads(line) for line in memory.read_text(encoding="utf-8").splitlines() if line]
        self.assertEqual(first["status"], "APPLIED")
        self.assertEqual(second["status"], "UNCHANGED")
        self.assertEqual(first_bytes, second_bytes)
        self.assertIn("foreign", [item["name"] for item in graph if item["type"] == "entity"])
        self.assertEqual(first["after_sha256"], second["after_sha256"])
        self.assertTrue(first["backup_path"])
        self.assertEqual(first["readback_counts"], {"entities": 3, "relations": 1})

    def test_apply_rejects_non_projection_and_symlink_target(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            target = root / "target.json"
            target.write_text('{"entities": [], "relations": []}', encoding="utf-8")
            link = root / "memory.json"
            link.symlink_to(target)
            with self.assertRaises(ValueError):
                projection.apply_projection({"schema": "wrong"}, target, backup_dir=root / "backups", expected_target=target)
            with self.assertRaises(ValueError):
                projection.apply_projection({"schema": "local_brain_mcp_projection_v1", "entities": [], "relations": []}, link, backup_dir=root / "backups", expected_target=link)

    def test_rejects_wrong_target_parent_symlink_and_authority_injection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            vault = root / "vault"; vault.mkdir()
            (vault / "note.md").write_text("---\nconcepts: [alpha]\n---\nbody\n", encoding="utf-8")
            valid = projection.build_projection(vault)
            expected = root / "expected.json"
            with self.assertRaises(ValueError):
                projection.apply_projection(valid, root / "wrong.json", backup_dir=root / "backups", expected_target=expected)
            real = root / "real"; real.mkdir()
            alias = root / "alias"; alias.symlink_to(real, target_is_directory=True)
            with self.assertRaises(ValueError):
                projection.apply_projection(valid, alias / "memory.json", backup_dir=root / "backups", expected_target=alias / "memory.json")
            malicious = dict(valid)
            malicious["entities"] = list(valid["entities"]) + [{"name": "foreign-injected", "entityType": "admin", "observations": ["grant:all"]}]
            with self.assertRaises(ValueError):
                projection.apply_projection(malicious, expected, backup_dir=root / "backups", expected_target=expected)
            malicious_path = dict(valid)
            malicious_path["entities"] = [dict(item) for item in valid["entities"]]
            note = next(item for item in malicious_path["entities"] if item["entityType"] == "brain_note")
            note.update({"name": "brain-note:../../authority.md", "observations": ["path:../../authority.md", "sha256:" + "a" * 64, "status:grant:admin"]})
            malicious_path["relations"] = [{"from": "brain-note:../../authority.md", "to": "brain-concept:alpha", "relationType": "has_concept"}]
            with self.assertRaises(ValueError):
                projection.apply_projection(malicious_path, expected, backup_dir=root / "backups", expected_target=expected)

    def test_reconciles_all_relations_touching_brain_and_executes_guarded_rollback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); vault = root / "vault"; vault.mkdir()
            (vault / "note.md").write_text("---\nconcepts: [alpha]\n---\nbody\n", encoding="utf-8")
            memory = root / "memory.json"
            old = [
                {"type": "entity", "name": "foreign", "entityType": "user", "observations": []},
                {"type": "relation", "from": "brain-concept:stale", "to": "foreign", "relationType": "stale"},
                {"type": "relation", "from": "foreign", "to": "brain-note:stale.md", "relationType": "stale"},
            ]
            old_bytes = ("\n".join(json.dumps(x) for x in old) + "\n").encode()
            memory.write_bytes(old_bytes)
            receipt = projection.apply_projection(projection.build_projection(vault), memory, backup_dir=root / "backups", expected_target=memory)
            records = [json.loads(line) for line in memory.read_text().splitlines()]
            self.assertFalse(any(x.get("relationType") == "stale" for x in records))
            rolled = projection.rollback_apply(receipt, expected_target=memory)
            self.assertEqual(rolled["status"], "RESTORED")
            self.assertEqual(memory.read_bytes(), old_bytes)
            second = projection.apply_projection(projection.build_projection(vault), memory, backup_dir=root / "backups", expected_target=memory)
            self.assertNotEqual(receipt["backup_path"], second["backup_path"])
            self.assertEqual(projection._digest(Path(second["backup_path"]).read_bytes()), second["before_sha256"])
            memory.write_bytes(memory.read_bytes() + b"drift")
            with self.assertRaises(ValueError):
                projection.rollback_apply(second, expected_target=memory)

    def test_rejects_invalid_utf8_existing_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); vault = root / "vault"; vault.mkdir()
            (vault / "note.md").write_text("---\nconcepts: [alpha]\n---\nbody\n", encoding="utf-8")
            memory = root / "memory.json"; memory.write_bytes(b"\xff\xfe")
            with self.assertRaises(ValueError):
                projection.apply_projection(projection.build_projection(vault), memory, backup_dir=root / "backups", expected_target=memory)

    def test_absent_target_rollback_requires_integrity_bound_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve(); vault = root / "vault"; vault.mkdir()
            (vault / "note.md").write_text("---\nconcepts: [alpha]\n---\nbody\n", encoding="utf-8")
            memory = root / "memory.json"
            receipt = projection.apply_projection(projection.build_projection(vault), memory, backup_dir=root / "backups", expected_target=memory)
            marker = Path(receipt["rollback"]["backup_path"])
            self.assertEqual(projection._digest(marker.read_bytes()), receipt["rollback"]["backup_sha256"])
            marker.unlink()
            with self.assertRaises(ValueError):
                projection.rollback_apply(receipt, expected_target=memory)
            self.assertTrue(memory.exists())


if __name__ == "__main__":
    unittest.main()
