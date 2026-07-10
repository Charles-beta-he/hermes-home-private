#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
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

    def test_durable_oauth_recovery_grant_enables_auto_authorize_without_task_scope(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            grant = root / "grant.json"
            profile = root / "profile.json"
            grant.write_text(json.dumps({
                "schema": "lark_oauth_recovery_authority_grant_v1",
                "status": "active",
                "action": "auto_singleflight_oauth_recovery",
                "scope": "oauth_recovery_only",
                "ordinary_selfcheck_may_execute": False,
                "no_task_read": True,
                "no_lark_write": True,
                "no_secret_entry": True,
                "no_password_or_otp_entry": True,
                "no_external_message_send": True,
                "max_concurrent_recoveries": 1,
                "max_oauth_pages_per_execution": 1,
                "per_execution_authorization_ttl_seconds": 300,
                "expires_at": None,
            }), encoding="utf-8")
            profile.write_text(json.dumps({
                "schema": "profile_policy_contract_v1",
                "automation_policy": {
                    "lark_oauth_recovery": {
                        "status": "enabled",
                        "authority_grant_ref": str(grant),
                        "ordinary_selfcheck_may_execute": False,
                        "task_read_authorized": False,
                        "lark_write_authorized": False,
                    }
                },
            }), encoding="utf-8")
            self.assertTrue(self.mod.oauth_recovery_auto_authorized(profile, root))
            revoked = json.loads(grant.read_text(encoding="utf-8"))
            revoked["status"] = "revoked"
            grant.write_text(json.dumps(revoked), encoding="utf-8")
            self.assertFalse(self.mod.oauth_recovery_auto_authorized(profile, root))

    def test_oauth_recovery_policy_rejects_grant_outside_allowed_root(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "authority-grants"
            root.mkdir()
            outside = base / "outside-grant.json"
            outside.write_text(json.dumps({
                "schema": "lark_oauth_recovery_authority_grant_v1",
                "status": "active",
            }), encoding="utf-8")
            profile = base / "lark.json"
            profile.write_text(json.dumps({
                "schema": "profile_policy_contract_v1",
                "automation_policy": {
                    "lark_oauth_recovery": {
                        "status": "enabled",
                        "authority_grant_ref": str(outside),
                        "ordinary_selfcheck_may_execute": False,
                        "task_read_authorized": False,
                        "lark_write_authorized": False,
                    }
                },
            }), encoding="utf-8")
            self.assertFalse(self.mod.oauth_recovery_auto_authorized(profile, root))

    def test_oauth_recovery_policy_fails_closed_without_valid_grant(self):
        with tempfile.TemporaryDirectory() as td:
            profile = Path(td) / "profile.json"
            profile.write_text(json.dumps({
                "schema": "profile_policy_contract_v1",
                "automation_policy": {"lark_oauth_recovery": {"status": "enabled", "authority_grant_ref": ""}},
            }), encoding="utf-8")
            self.assertFalse(self.mod.oauth_recovery_auto_authorized(profile))

    def test_parser_uses_durable_policy_but_explicit_disable_wins(self):
        with mock.patch.object(self.mod, "oauth_recovery_auto_authorized", return_value=True):
            enabled = self.mod.build_parser().parse_args(["--auth-only"])
            disabled = self.mod.build_parser().parse_args(["--auth-only", "--no-auto-authorize"])
        self.assertTrue(enabled.auto_authorize)
        self.assertFalse(disabled.auto_authorize)

    def test_auth_only_uses_durable_auto_authorize_without_reading_tasks(self):
        fake = FakeReader()
        observed = {}

        def guard(args):
            observed["auto_authorize"] = args.auto_authorize
            return {"ok": True, "action": "login_success"}

        with mock.patch.object(self.mod, "oauth_recovery_auto_authorized", return_value=True), \
             mock.patch.object(self.mod, "load_reader", return_value=fake), \
             mock.patch.object(self.mod, "run_guard", side_effect=guard):
            out = io.StringIO()
            with redirect_stdout(out):
                code = self.mod.main(["--auth-only"])
        payload = json.loads(out.getvalue())
        self.assertEqual(code, 0)
        self.assertTrue(observed["auto_authorize"])
        self.assertEqual(fake.calls, [])
        self.assertEqual(payload["side_effect_boundary"], {
            "auto_authorize_enabled": True,
            "task_read_executed": False,
            "lark_write_executed": False,
        })

    def test_health_check_guard_command_never_enables_stale_cleanup(self):
        args = self.mod.build_parser().parse_args(["--health-check"])
        args.auth_only = True
        args.no_open = True
        args.auto_authorize = False
        args.force_refresh = False
        args.auth_timeout = 5
        completed = mock.Mock(returncode=0, stdout='{"ok": true, "action": "token_valid"}', stderr="")
        with mock.patch.object(self.mod.subprocess, "run", return_value=completed) as run:
            result = self.mod.run_guard(args)
        cmd = run.call_args.args[0]
        self.assertTrue(result["ok"])
        self.assertNotIn("--cleanup-stale", cmd)
        self.assertIn("--status-only", cmd)
        self.assertIn("--no-open", cmd)
        self.assertNotIn("--auto-authorize", cmd)

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
