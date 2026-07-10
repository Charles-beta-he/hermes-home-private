#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

MODULE_PATH = Path.home() / ".hermes" / "scripts" / "lark_task_flow.py"


def load_module():
    spec = importlib.util.spec_from_file_location("hermes_lark_task_flow", MODULE_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


class FakeReader:
    VALID_SCOPE_MODES = {"prefer", "only", "off"}
    DEFAULT_IMAGE_CACHE_DIR = Path("/tmp/lark-images")

    def __init__(self):
        self.calls = []

    def get_token(self, auto_auth=None, auto_authorize=None):
        self.calls.append(("get_token", auto_auth, auto_authorize))
        return "tok"

    def collect_tasks(self, **kwargs):
        self.calls.append(("collect_tasks", kwargs))
        return [{"summary": "任务", "lark_task_guid": "guid-1", "lark_task_scope": "UVISA", "description": "desc"}]


class LarkTaskFlowTest(unittest.TestCase):
    def setUp(self):
        self.mod = load_module()

    def test_extract_guid_from_applink(self):
        self.assertEqual(
            self.mod.extract_guid("https://applink.larksuite.com/client/todo/detail?guid=066bb866-d2b8-459e-bb11-ed8ce742f32d&suite_entity_num=t104234"),
            "066bb866-d2b8-459e-bb11-ed8ce742f32d",
        )

    def test_list_flow_runs_guard_then_reader_without_second_auto_auth(self):
        fake = FakeReader()
        with mock.patch.object(self.mod, "load_reader", return_value=fake), \
             mock.patch.object(self.mod, "run_guard", return_value={"ok": True, "action": "token_valid"}):
            out = io.StringIO()
            with redirect_stdout(out):
                code = self.mod.main(["--scope-mode", "only", "--summary"])
        self.assertEqual(code, 0)
        self.assertIn("tasks=1", out.getvalue())
        self.assertEqual(fake.calls[0], ("get_token", False, None))
        self.assertEqual(fake.calls[1][0], "collect_tasks")
        self.assertFalse(fake.calls[1][1]["auto_auth"])
        self.assertFalse(fake.calls[1][1]["auto_authorize"])
        self.assertEqual(fake.calls[1][1]["scope_mode"], "only")

    def test_auth_failure_stops_before_reader(self):
        fake = FakeReader()
        with mock.patch.object(self.mod, "load_reader", return_value=fake), \
             mock.patch.object(self.mod, "run_guard", return_value={"ok": False, "action": "port_busy"}):
            out = io.StringIO()
            with redirect_stdout(out):
                code = self.mod.main(["--summary"])
        self.assertEqual(code, 1)
        self.assertIn('"stage": "auth"', out.getvalue())
        self.assertEqual(fake.calls, [])

    def test_health_check_is_status_only_and_never_opens_browser_or_reads_tasks(self):
        fake = FakeReader()
        observed = {}

        def guard(args):
            observed.update({"no_open": args.no_open, "auto_authorize": args.auto_authorize, "auth_only": args.auth_only, "auth_timeout": args.auth_timeout})
            return {"ok": True, "action": "token_valid"}

        with mock.patch.object(self.mod, "load_reader", return_value=fake), mock.patch.object(self.mod, "run_guard", side_effect=guard):
            out = io.StringIO()
            with redirect_stdout(out):
                code = self.mod.main(["--health-check"])

        self.assertEqual(code, 0)
        self.assertEqual(observed, {"no_open": True, "auto_authorize": False, "auth_only": True, "auth_timeout": 5})
        self.assertEqual(fake.calls, [])
        self.assertIn('"stage": "auth"', out.getvalue())


if __name__ == "__main__":
    unittest.main()
