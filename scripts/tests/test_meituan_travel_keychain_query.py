import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parents[1] / "meituan_travel_keychain_query.py"
spec = importlib.util.spec_from_file_location("meituan_adapter", MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot load adapter from {MODULE_PATH}")
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


class MeituanKeychainAdapterTests(unittest.TestCase):
    @patch.object(adapter.shutil, "which", return_value="/opt/homebrew/bin/npx")
    @patch.object(adapter.subprocess, "run")
    def test_check_reports_ready_without_external_query(self, run, _which):
        run.return_value = subprocess.CompletedProcess([], 0, stdout="secret-token\n", stderr="")
        out = io.StringIO()
        with patch.dict(os.environ, {"USER": "charles"}, clear=False), redirect_stdout(out):
            rc = adapter.check_status()
        payload = json.loads(out.getvalue())
        self.assertEqual(rc, 0)
        self.assertTrue(payload["credential_present"])
        self.assertFalse(payload["external_query_executed"])
        self.assertNotIn("secret-token", out.getvalue())
        run.assert_called_once()

    @patch.object(adapter.Path, "exists", return_value=True)
    def test_resolve_adapter_prefers_managed_local_binary(self, _exists):
        self.assertEqual(
            adapter.resolve_adapter_command(),
            [str(adapter.MANAGED_BINARY)],
        )

    @patch.object(adapter.Path, "exists", return_value=True)
    @patch.object(adapter.subprocess, "run")
    def test_query_injects_token_only_into_child_environment(self, run, _exists):
        captured = {}

        def fake_run(*args, **kwargs):
            if args[0][0] == "/usr/bin/security":
                return subprocess.CompletedProcess([], 0, stdout="secret-token\n", stderr="")
            captured["cmd"] = list(args[0])
            captured["env"] = dict(kwargs["env"])
            return subprocess.CompletedProcess([], 0, stdout="result", stderr="")

        run.side_effect = fake_run
        rc = adapter.run_query("昭苏晚餐", "昭苏", None, 30)
        self.assertEqual(rc, 0)
        self.assertEqual(captured["cmd"][0], str(adapter.MANAGED_BINARY))
        self.assertEqual(captured["env"]["MEITUAN_HT_TOKEN"], "secret-token")
        self.assertNotIn("secret-token", " ".join(captured["cmd"]))

    @patch.object(adapter.subprocess, "run")
    def test_missing_keychain_item_fails_closed(self, run):
        run.return_value = subprocess.CompletedProcess([], 44, stdout="", stderr="not found")
        err = io.StringIO()
        with patch.dict(os.environ, {"USER": "charles"}, clear=False), redirect_stderr(err):
            rc = adapter.run_query("test", None, None, 30)
        self.assertEqual(rc, 3)
        self.assertEqual(json.loads(err.getvalue())["error"], "credential_missing")


if __name__ == "__main__":
    unittest.main()
