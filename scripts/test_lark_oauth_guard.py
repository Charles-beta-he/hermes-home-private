#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

MODULE_PATH = Path.home() / ".hermes" / "scripts" / "lark_oauth_guard.py"


def load_module():
    spec = importlib.util.spec_from_file_location("hermes_lark_oauth_guard", MODULE_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


class LarkOAuthGuardTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module()

    def test_extract_auth_url_from_noisy_login_output(self):
        output = """
🔗 Authorization URL:
http://localhost:3010/authorize?client_id=client_id_for_local_auth&code_challenge=abc&state=reauthorize

⏳ Waiting
"""
        self.assertEqual(
            self.mod.extract_auth_url(output),
            "http://localhost:3010/authorize?client_id=client_id_for_local_auth&code_challenge=abc&state=reauthorize",
        )

    def test_token_snapshot_prefers_valid_local_token_for_app(self):
        now = time.time()
        snapshot = {
            "tokens": {
                "tok-valid": {"expiresAt": now + 3600},
                "tok-expired": {"expiresAt": now - 1},
            },
            "localTokens": {"cli_a96f6a6211f91ed2": "tok-valid"},
        }
        status = self.mod.token_status_from_snapshot(snapshot, app_id="cli_a96f6a6211f91ed2", now=now)
        self.assertTrue(status.valid)
        self.assertEqual(status.reason, "valid_local_token")
        self.assertEqual(status.token_key, "tok-valid")

    def test_token_snapshot_rejects_expired_local_token_even_when_present(self):
        now = time.time()
        snapshot = {
            "tokens": {"tok-expired": {"expiresAt": now - 1}},
            "localTokens": {"cli_a96f6a6211f91ed2": "tok-expired"},
        }
        status = self.mod.token_status_from_snapshot(snapshot, app_id="cli_a96f6a6211f91ed2", now=now)
        self.assertFalse(status.valid)
        self.assertIn("expired", status.reason)

    def test_token_snapshot_falls_back_to_any_valid_token(self):
        now = time.time()
        snapshot = {"tokens": {"tok-any": {"expiresAt": now + 600}}, "localTokens": {}}
        status = self.mod.token_status_from_snapshot(snapshot, app_id="missing", now=now)
        self.assertTrue(status.valid)
        self.assertEqual(status.reason, "valid_any_token")

    def test_credentials_from_snapshot_accepts_feishu_env_aliases(self):
        with mock.patch.dict(
            "os.environ",
            {"FEISHU_APP_ID": "cli_test", "FEISHU_APP_SECRET": "secret_test"},
            clear=True,
        ):
            self.assertEqual(self.mod.credentials_from_snapshot({}), ("cli_test", "secret_test"))

    def test_credentials_from_snapshot_normalizes_tuple_values(self):
        snapshot = {
            "clients": {
                "client": {
                    "appId": ("cli_tuple",),
                    "appSecret": ("secret_tuple",),
                }
            }
        }
        with mock.patch.dict("os.environ", {}, clear=True):
            self.assertEqual(self.mod.credentials_from_snapshot(snapshot, app_id="cli_tuple"), ("cli_tuple", "secret_tuple"))

    def test_scalar_string_takes_first_non_empty_nested_value(self):
        self.assertEqual(self.mod._scalar_string((None, "", ["cli_nested"])), "cli_nested")

    def test_run_login_normalizes_subprocess_arguments(self):
        class FakeProc:
            stdout = None
            returncode = 0

            def poll(self):
                return 0
        snapshot = {"clients": {"client": {"appId": "cli_test", "appSecret": "secret_test"}}}
        with mock.patch.dict("os.environ", {}, clear=True), \
             mock.patch.object(self.mod.subprocess, "Popen", return_value=FakeProc()) as popen:
            result = self.mod.run_login(snapshot, "cli_test", ("https://open.larksuite.com",), 8765, ("auth:user.id:read",), False, 1)
        self.assertTrue(result["ok"])
        launched_args = popen.call_args.args[0]
        self.assertTrue(all(isinstance(item, str) for item in launched_args))
        self.assertEqual(launched_args[launched_args.index("--domain") + 1], "https://open.larksuite.com")
        self.assertEqual(launched_args[launched_args.index("--scope") + 1], "auth:user.id:read")

    def test_blue_authorize_button_bbox_prefers_large_bottom_button(self):
        try:
            from PIL import Image, ImageDraw
        except Exception as exc:
            self.skipTest(f"PIL unavailable: {exc}")
        with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
            img = Image.new("RGB", (800, 600), "white")
            draw = ImageDraw.Draw(img)
            draw.rectangle((620, 120, 760, 140), fill=(51, 112, 255))  # top link; ignored by search band/height
            draw.rounded_rectangle((560, 500, 760, 555), radius=12, fill=(51, 112, 255))
            img.save(tmp.name)
            bbox = self.mod._blue_authorize_button_bbox(Path(tmp.name))
        self.assertIsNotNone(bbox)
        self.assertGreaterEqual(bbox[0], 550)
        self.assertGreaterEqual(bbox[1], 490)
        self.assertGreaterEqual(bbox[2], 740)
        self.assertGreaterEqual(bbox[3], 540)

    def test_run_login_invokes_auto_authorize_after_opening_url(self):
        class FakeStdout:
            def __init__(self):
                self.lines = ["http://localhost:8765/authorize?client_id=x&state=y\n", ""]

            def readline(self):
                return self.lines.pop(0) if self.lines else ""

        class FakeProc:
            def __init__(self):
                self.stdout = FakeStdout()
                self.returncode = 0
                self.polled = 0

            def poll(self):
                self.polled += 1
                return None if self.polled == 1 else 0

        snapshot = {"clients": {"client": {"appId": "cli_test", "appSecret": "secret_test"}}}
        with mock.patch.dict("os.environ", {}, clear=True), \
             mock.patch.object(self.mod.subprocess, "Popen", return_value=FakeProc()), \
             mock.patch.object(self.mod.subprocess, "run"), \
             mock.patch.object(self.mod, "auto_click_authorize", return_value={"ok": True, "reason": "clicked"}) as clicker:
            result = self.mod.run_login(snapshot, "cli_test", "https://open.larksuite.com", 8765, "auth:user.id:read", True, 5, True, 1)
        self.assertTrue(result["opened"])
        self.assertEqual(result["auto_authorize"], {"ok": True, "reason": "clicked"})
        clicker.assert_called_once()

    def test_auto_authorize_parser_env_default(self):
        with mock.patch.dict("os.environ", {"LARK_AUTO_AUTHORIZE": "1"}, clear=True):
            args = self.mod.build_parser().parse_args(["--json"])
        self.assertTrue(args.auto_authorize)

    def test_plan_skips_spawn_when_token_valid(self):
        plan = self.mod.plan_login(token_valid=True, lock_active=True, port_busy=True, cleanup_stale=True)
        self.assertEqual(plan.action, "token_valid")
        self.assertFalse(plan.should_spawn)
        self.assertFalse(plan.should_kill_stale)

    def test_plan_force_refresh_spawns_even_when_token_valid(self):
        plan = self.mod.plan_login(token_valid=True, lock_active=False, port_busy=False, cleanup_stale=True, force_refresh=True)
        self.assertEqual(plan.action, "force_refresh_login")
        self.assertTrue(plan.should_spawn)
        self.assertFalse(plan.should_kill_stale)

    def test_plan_waits_instead_of_spawning_second_login_when_lock_active(self):
        plan = self.mod.plan_login(token_valid=False, lock_active=True, port_busy=False, cleanup_stale=True)
        self.assertEqual(plan.action, "login_already_in_progress")
        self.assertFalse(plan.should_spawn)

    def test_plan_does_not_spawn_on_port_busy_without_cleanup(self):
        plan = self.mod.plan_login(token_valid=False, lock_active=False, port_busy=True, cleanup_stale=False)
        self.assertEqual(plan.action, "port_busy")
        self.assertFalse(plan.should_spawn)
        self.assertFalse(plan.should_kill_stale)

    def test_plan_cleanup_stale_port_then_spawn_when_allowed(self):
        plan = self.mod.plan_login(token_valid=False, lock_active=False, port_busy=True, cleanup_stale=True)
        self.assertEqual(plan.action, "cleanup_stale_then_login")
        self.assertTrue(plan.should_kill_stale)
        self.assertTrue(plan.should_spawn)

    def test_public_result_redacts_token_key(self):
        original_token = "eyJhbGci-verylongtokenpayload-7890"
        result = {"ok": True, "token_status": {"token_key": original_token}}
        public = self.mod.redact_result(result)
        redacted = public["token_status"]["token_key"]
        self.assertIn("...", redacted)
        self.assertLess(len(redacted), len(original_token))
        self.assertTrue(redacted.startswith("eyJhbGci"))
        self.assertTrue(redacted.endswith("7890"))
        self.assertNotIn("verylongtokenpayload", redacted)
        self.assertNotEqual(redacted, original_token)

    def test_redact_secret_boundary_preserves_short_values_only(self):
        self.assertEqual(self.mod.redact_secret("x" * 15), "x" * 15)
        self.assertEqual(self.mod.redact_secret("a" * 16), "aaaaaaaa...aaaa")

    def test_public_result_redacts_top_level_secrets(self):
        result = {
            "ok": True,
            "app_secret": "secret-value",
            "access_token": "access-value",
            "refresh_token": "refresh-value",
            "client_secret": "client-secret-value",
        }
        public = self.mod.redact_result(result)
        self.assertEqual(public["app_secret"], "***")
        self.assertEqual(public["access_token"], "***")
        self.assertEqual(public["refresh_token"], "***")
        self.assertEqual(public["client_secret"], "***")

    def test_unexpired_boundaries_fail_closed_for_epoch_zero(self):
        now = 1000.0
        self.assertTrue(self.mod._is_unexpired({"expiresAt": None}, now))
        self.assertTrue(self.mod._is_unexpired({"expiresAt": ""}, now))
        self.assertTrue(self.mod._is_unexpired({"expiresAt": now + 0.001}, now))
        self.assertFalse(self.mod._is_unexpired({"expiresAt": now}, now))
        self.assertFalse(self.mod._is_unexpired({"expiresAt": 0}, now))
        self.assertFalse(self.mod._is_unexpired({"expiresAt": "0"}, now))
        self.assertFalse(self.mod._is_unexpired({"expiresAt": "not-a-number"}, now))

    def test_ensure_login_entrypoint_skips_spawn_when_token_valid(self):
        args = self.mod.build_parser().parse_args(["--json", "--no-open"])
        snapshot = {
            "tokens": {"tok-valid": {"expiresAt": time.time() + 3600}},
            "localTokens": {"cli_a96f6a6211f91ed2": "tok-valid"},
        }
        with mock.patch.object(self.mod, "auth_snapshot", return_value=snapshot), \
             mock.patch.object(self.mod, "port_busy", return_value=False), \
             mock.patch.object(self.mod, "run_login") as run_login:
            result = self.mod.ensure_login(args)
        self.assertTrue(result["ok"])
        self.assertEqual(result["action"], "token_valid")
        run_login.assert_not_called()

    def test_status_only_never_spawns_login_when_token_is_invalid(self):
        args = self.mod.build_parser().parse_args(["--json", "--status-only", "--no-open"])
        snapshot = {"tokens": {}, "localTokens": {}}
        with mock.patch.object(self.mod, "auth_snapshot", return_value=snapshot), \
             mock.patch.object(self.mod, "port_busy", return_value=False), \
             mock.patch.object(self.mod.SingleFlightLock, "is_active", return_value=False), \
             mock.patch.object(self.mod.SingleFlightLock, "acquire") as acquire, \
             mock.patch.object(self.mod, "run_login") as run_login:
            result = self.mod.ensure_login(args)
        self.assertFalse(result["ok"])
        self.assertEqual(result["action"], "auth_required")
        self.assertEqual(result["planned_action"], "start_login")
        self.assertTrue(result["status_only"])
        acquire.assert_not_called()
        run_login.assert_not_called()

    def test_ensure_login_force_refresh_does_not_skip_valid_token(self):
        args = self.mod.build_parser().parse_args(["--json", "--no-open", "--force-refresh"])
        snapshot = {
            "tokens": {"tok-valid": {"expiresAt": time.time() + 3600}},
            "localTokens": {"cli_a96f6a6211f91ed2": "tok-valid"},
            "clients": {"client": {"appId": "cli_a96f6a6211f91ed2", "appSecret": "secret_test"}},
        }
        login_result = {"ok": True, "action": "login_completed", "returncode": 0}
        with mock.patch.object(self.mod, "auth_snapshot", return_value=snapshot), \
             mock.patch.object(self.mod, "port_busy", return_value=False), \
             mock.patch.object(self.mod, "run_login", return_value=login_result) as run_login:
            result = self.mod.ensure_login(args)
        self.assertTrue(result["ok"])
        self.assertEqual(result["action"], "login_success")
        run_login.assert_called_once()

    def test_ensure_login_force_refresh_rejects_no_open_auto_authorize(self):
        args = self.mod.build_parser().parse_args(["--json", "--no-open", "--force-refresh", "--auto-authorize"])
        snapshot = {
            "tokens": {"tok-valid": {"expiresAt": time.time() + 3600}},
            "localTokens": {"cli_a96f6a6211f91ed2": "tok-valid"},
            "clients": {"client": {"appId": "cli_a96f6a6211f91ed2", "appSecret": "secret_test"}},
        }
        with mock.patch.object(self.mod, "auth_snapshot", return_value=snapshot), \
             mock.patch.object(self.mod, "port_busy", return_value=False), \
             mock.patch.object(self.mod, "run_login") as run_login:
            result = self.mod.ensure_login(args)
        self.assertFalse(result["ok"])
        self.assertEqual(result["action"], "invalid_args")
        self.assertIn("requires opening", result["error"])
        run_login.assert_not_called()

    def test_json_main_output_redacts_token_key(self):
        token = "eyJhbGciOiJmainentrypointtokenpayload1234567890"
        with mock.patch.object(self.mod, "ensure_login", return_value={"ok": True, "token_status": {"token_key": token}}):
            buf = io.StringIO()
            with redirect_stdout(buf):
                exit_code = self.mod.main(["--json", "--no-open"])
        self.assertEqual(exit_code, 0)
        payload = json.loads(buf.getvalue())
        self.assertIn("...", payload["token_status"]["token_key"])
        self.assertNotIn("mainentrypointtokenpayload", payload["token_status"]["token_key"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
