import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from batch_compile import compile_batch


class BatchCompileTests(unittest.TestCase):
    def setUp(self):
        self.routing = json.loads((ROOT.parent / "model-routing.json").read_text(encoding="utf-8"))
        self.valid = json.loads((ROOT / "sample-seed.json").read_text(encoding="utf-8"))

    def test_mixed_batch_isolates_invalid_candidate(self):
        invalid = copy.deepcopy(self.valid)
        invalid["content"]["content_id"] = "invalid-oversized-grid"
        invalid["content"]["level_parameters"]["grid_size"] = 100
        result = compile_batch([self.valid, invalid], self.routing)
        self.assertEqual(result["summary"], {"accepted": 1, "rejected": 1, "total": 2})
        self.assertEqual(len(result["accepted"]), 1)
        self.assertEqual(result["rejected"][0]["candidate_id"], "invalid-oversized-grid")
        self.assertIn("out of bounds", result["rejected"][0]["error"])

    def test_batch_receipt_is_deterministic(self):
        first = compile_batch([self.valid], self.routing)
        second = compile_batch([copy.deepcopy(self.valid)], self.routing)
        self.assertEqual(first, second)

    def test_batch_never_grants_publish_authority(self):
        result = compile_batch([self.valid], self.routing)
        self.assertFalse(result["authority"]["may_publish"])
        self.assertFalse(result["authority"]["may_submit_platform"])


if __name__ == "__main__":
    unittest.main()
