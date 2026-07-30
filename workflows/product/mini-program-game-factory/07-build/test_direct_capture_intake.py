import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from direct_capture_intake import IntakeError, bind_direct_media


class DirectCaptureIntakeTests(unittest.TestCase):
    def snapshot(self, media_path: str, digest=None):
        source = {
            "source_id": "rank-capture",
            "source_type": "direct_app_rank_capture",
            "publisher": "Douyin client chart",
            "independence_key": "rank-capture-lineage",
            "published_at": "2026-07-26T12:00:00+08:00",
            "accessed_at": "2026-07-26T12:00:00+08:00",
            "evidence_level": "direct",
            "local_media_path": media_path,
        }
        if digest is not None:
            source["evidence_digest"] = digest
        return {
            "schema_version": 1,
            "snapshot_id": "capture-test",
            "observed_at": "2026-07-26T12:00:00+08:00",
            "sources": [source],
            "observations": [],
        }

    def test_binds_absolute_path_digest_and_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            media = Path(tmp) / "rank.png"
            media.write_bytes(b"rank-capture")
            bound = bind_direct_media(self.snapshot(str(media)))
            source = bound["sources"][0]
            self.assertEqual(source["local_media_path"], str(media.resolve()))
            self.assertEqual(source["evidence_digest"], hashlib.sha256(b"rank-capture").hexdigest())
            self.assertEqual(source["media_size_bytes"], len(b"rank-capture"))

    def test_resolves_relative_path_from_declared_base(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            media = root / "capture.mp4"
            media.write_bytes(b"video")
            bound = bind_direct_media(self.snapshot("capture.mp4"), base_dir=root)
            self.assertEqual(bound["sources"][0]["local_media_path"], str(media.resolve()))

    def test_predeclared_mismatched_digest_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            media = Path(tmp) / "rank.png"
            media.write_bytes(b"rank-capture")
            with self.assertRaises(IntakeError):
                bind_direct_media(self.snapshot(str(media), "0" * 64))

    def test_missing_media_fails_closed(self):
        with self.assertRaises(IntakeError):
            bind_direct_media(self.snapshot("/missing/capture.png"))

    def test_non_direct_source_is_not_allowed_to_bind_local_media(self):
        with tempfile.TemporaryDirectory() as tmp:
            media = Path(tmp) / "report.html"
            media.write_text("report", encoding="utf-8")
            snapshot = self.snapshot(str(media))
            snapshot["sources"][0]["source_type"] = "third_party_rank_report"
            snapshot["sources"][0]["evidence_level"] = "third_party_claim"
            with self.assertRaises(IntakeError):
                bind_direct_media(snapshot)

    def test_predeclared_content_review_is_rejected_before_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            media = Path(tmp) / "rank.png"
            media.write_bytes(b"rank-capture")
            snapshot = self.snapshot(str(media))
            snapshot["sources"][0]["content_review"] = {
                "reviewer_kind": "human",
                "reviewer_id": "forged-before-intake",
            }
            with self.assertRaises(IntakeError):
                bind_direct_media(snapshot)

    def test_input_is_not_mutated(self):
        with tempfile.TemporaryDirectory() as tmp:
            media = Path(tmp) / "rank.png"
            media.write_bytes(b"rank-capture")
            original = self.snapshot(str(media))
            before = json.dumps(original, sort_keys=True)
            bind_direct_media(original)
            self.assertEqual(json.dumps(original, sort_keys=True), before)


if __name__ == "__main__":
    unittest.main()
