#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
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

    def test_token_snapshot_rejects_valid_token_not_bound_to_requested_app(self):
        now = time.time()
        snapshot = {"tokens": {"tok-any": {"expiresAt": now + 600}}, "localTokens": {}}
        status = self.mod.token_status_from_snapshot(snapshot, app_id="missing", now=now)
        self.assertFalse(status.valid)
        self.assertEqual(status.reason, "local_token_unbound")

    def test_credentials_from_snapshot_accepts_feishu_env_aliases(self):
        with mock.patch.dict(
            "os.environ",
            {"FEISHU_APP_ID": "cli_test", "FEISHU_APP_SECRET": "secret_test"},
            clear=True,
        ):
            self.assertEqual(self.mod.credentials_from_snapshot({}, app_id="cli_test"), ("cli_test", "secret_test"))

    def test_credentials_from_snapshot_rejects_ambient_identity_mismatch(self):
        with mock.patch.dict(
            "os.environ",
            {"LARK_APP_ID": "ambient_other_app", "LARK_APP_SECRET": "private_secret"},
            clear=True,
        ):
            self.assertEqual(self.mod.credentials_from_snapshot({}, app_id="bound_app"), ("", ""))

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

    def test_terminate_login_tree_kills_nested_descendants(self):
        class FakeProc:
            pid = 4200

            def __init__(self):
                self.returncode = None
                self.terminated = False

            def terminate(self):
                self.terminated = True

            def wait(self, timeout=None):
                self.returncode = -15
                return self.returncode

            def poll(self):
                return self.returncode

            def kill(self):
                self.returncode = -9

        proc = FakeProc()
        with mock.patch.object(self.mod.os, "killpg") as killpg:
            self.mod._terminate_login_tree(proc)
        self.assertEqual(killpg.call_args_list, [
            mock.call(4200, self.mod.signal.SIGTERM),
            mock.call(4200, 0),
            mock.call(4200, self.mod.signal.SIGKILL),
        ])

    def test_run_login_checks_deadline_before_blocking_stdout_read(self):
        class BlockingStdout:
            def readline(self):
                raise AssertionError("readline must not run after the deadline")

        class FakeProc:
            pid = 4200
            stdout = BlockingStdout()
            stdin = mock.Mock()
            returncode = None

            def poll(self):
                return self.returncode

            def terminate(self):
                return None

            def kill(self):
                self.returncode = -9

            def wait(self, timeout=None):
                self.returncode = -15
                return self.returncode

        snapshot = {"clients": {"client": {"appId": "cli_test", "appSecret": "secret_test"}}}
        with mock.patch.dict("os.environ", {}, clear=True), \
             mock.patch.object(self.mod.subprocess, "Popen", return_value=FakeProc()), \
             mock.patch.object(self.mod.time, "time", side_effect=AssertionError("deadline must be monotonic")), \
             mock.patch.object(self.mod.time, "monotonic", side_effect=[100.0, 102.0, 102.0, 102.0]):
            result = self.mod.run_login(
                snapshot, "cli_test", "https://open.larksuite.com", 8765,
                "auth:user.id:read", False, 1,
            )
        self.assertEqual(result["action"], "login_timeout")

    def test_run_login_normalizes_subprocess_arguments(self):
        class FakeStdin:
            def __init__(self):
                self.payload = ""

            def write(self, value):
                self.payload += value

            def close(self):
                return None

        class FakeProc:
            stdout = None
            stdin = FakeStdin()
            returncode = 0

            def poll(self):
                return 0
        snapshot = {"clients": {"client": {"appId": "cli_test", "appSecret": "secret_test"}}}
        with mock.patch.dict("os.environ", {
            "LARK_APP_SECRET": "ambient_secret",
            "FEISHU_APP_SECRET": "ambient_secret_2",
            "APP_SECRET": "ambient_secret_3",
            "LARK_DOMAIN": "https://ambient.invalid",
            "LARK_OAUTH_SCOPE": "task:task:write",
            "UNRELATED_PRIVATE_SENTINEL": "must_not_reach_child",
        }, clear=True), \
             mock.patch.object(self.mod.subprocess, "Popen", return_value=FakeProc()) as popen:
            result = self.mod.run_login(snapshot, "cli_test", ("https://open.larksuite.com",), 8765, ("auth:user.id:read",), False, 1)
        self.assertTrue(result["ok"])
        launched_args = popen.call_args.args[0]
        launched_env = popen.call_args.kwargs["env"]
        self.assertTrue(all(isinstance(item, str) for item in launched_args))
        self.assertNotIn("secret_test", launched_args)
        self.assertNotIn("LARK_APP_SECRET", launched_env)
        self.assertNotIn("FEISHU_APP_SECRET", launched_env)
        self.assertNotIn("APP_SECRET", launched_env)
        self.assertNotIn("LARK_DOMAIN", launched_env)
        self.assertNotIn("LARK_OAUTH_SCOPE", launched_env)
        self.assertNotIn("UNRELATED_PRIVATE_SENTINEL", launched_env)
        payload = json.loads(FakeProc.stdin.payload)
        self.assertEqual(payload["domain"], "https://open.larksuite.com")
        self.assertEqual(payload["scope"], "auth:user.id:read")
        self.assertEqual(payload["appSecret"], "secret_test")

    def test_run_login_reaps_child_when_stdin_delivery_breaks(self):
        class BrokenStdin:
            def write(self, _value):
                raise BrokenPipeError()

        proc = mock.Mock(pid=4242, stdin=BrokenStdin(), stdout=None, returncode=None)
        snapshot = {"clients": {"client": {"appId": "cli_test", "appSecret": "secret_test"}}}
        with mock.patch.object(self.mod.subprocess, "Popen", return_value=proc), \
             mock.patch.object(self.mod, "_terminate_login_tree") as terminate:
            result = self.mod.run_login(
                snapshot, "cli_test", "https://open.larksuite.com", 8765,
                "auth:user.id:read", False, 1,
            )
        self.assertEqual(result, {"ok": False, "action": "login_failed"})
        terminate.assert_called_once()
        self.assertIs(terminate.call_args.args[0], proc)
        self.assertIsInstance(terminate.call_args.kwargs["deadline"], float)

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
            def fileno(self):
                return 99

        class FakeStdin:
            def write(self, value):
                return len(value)

            def close(self):
                return None

        class FakeProc:
            def __init__(self):
                self.stdout = FakeStdout()
                self.stdin = FakeStdin()
                self.returncode = 0
                self.polled = 0

            def poll(self):
                self.polled += 1
                return None if self.polled <= 2 else 0

        snapshot = {"clients": {"client": {"appId": "cli_test", "appSecret": "secret_test"}}}
        proc = FakeProc()
        with mock.patch.dict("os.environ", {}, clear=True), \
             mock.patch.object(self.mod.subprocess, "Popen", return_value=proc), \
             mock.patch.object(self.mod.select, "select", return_value=([proc.stdout], [], [])), \
             mock.patch.object(self.mod.os, "read", side_effect=[
                 b"http://local",
                 b"host:8765/authorize?client_id=x&state=y",
             ]), \
             mock.patch.object(self.mod.subprocess, "run"), \
             mock.patch.object(self.mod, "auto_click_authorize", return_value={"ok": True, "reason": "clicked"}) as clicker:
            result = self.mod.run_login(snapshot, "cli_test", "https://open.larksuite.com", 8765, "auth:user.id:read", True, 5, True, 1)
        self.assertTrue(result["opened"])
        self.assertEqual(result["auto_authorize"], {"ok": True, "reason": "clicked"})
        clicker.assert_called_once()

    def test_auto_authorize_parser_ignores_ambient_environment(self):
        with mock.patch.dict(self.mod.os.environ, {"LARK_AUTO_AUTHORIZE": "1"}, clear=False):
            args = self.mod.build_parser().parse_args([])
        self.assertFalse(args.auto_authorize)

    def test_direct_guard_cli_cannot_enable_auto_authorize(self):
        with self.assertRaises(SystemExit):
            self.mod.build_parser().parse_args(["--auto-authorize"])

    def test_internal_auto_authorize_requires_guard_side_durable_grant_validation(self):
        argv = [
            "--json",
            "--authorized-auto-authorize-profile", "/tmp/profile.json",
            "--authorized-auto-authorize-grant-root", "/tmp/grants",
        ]
        with mock.patch.object(self.mod, "_durable_auto_authorize_valid", return_value=False), \
             mock.patch.object(self.mod, "ensure_login") as ensure_login, \
             mock.patch.object(self.mod.SingleFlightLock, "is_active", return_value=False), \
             mock.patch.object(self.mod, "port_busy", return_value=False), \
             redirect_stdout(io.StringIO()) as out:
            code = self.mod.main(argv)
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(out.getvalue())["action"], "authority_grant_invalid")
        ensure_login.assert_not_called()

    def test_internal_auto_authorize_valid_grant_reaches_guard_with_capability_enabled(self):
        argv = [
            "--json",
            "--authorized-auto-authorize-profile", "/tmp/profile.json",
            "--authorized-auto-authorize-grant-root", "/tmp/grants",
        ]
        observed = {}

        def ensure_login(args):
            observed["auto_authorize"] = args.auto_authorize
            return {"ok": True, "action": "token_valid"}

        with mock.patch.object(self.mod, "_durable_auto_authorize_valid", return_value=True), \
             mock.patch.object(self.mod, "ensure_login", side_effect=ensure_login), \
             mock.patch.object(self.mod.SingleFlightLock, "is_active", return_value=False), \
             mock.patch.object(self.mod, "port_busy", return_value=False), \
             redirect_stdout(io.StringIO()):
            code = self.mod.main(argv)
        self.assertEqual(code, 0)
        self.assertTrue(observed["auto_authorize"])

    def test_internal_auto_authorize_is_rejected_for_status_only(self):
        argv = [
            "--json", "--status-only",
            "--authorized-auto-authorize-profile", "/tmp/profile.json",
            "--authorized-auto-authorize-grant-root", "/tmp/grants",
        ]
        with mock.patch.object(self.mod, "_durable_auto_authorize_valid") as validate, \
             mock.patch.object(self.mod, "ensure_login") as ensure_login, \
             mock.patch.object(self.mod.SingleFlightLock, "is_active", return_value=False), \
             mock.patch.object(self.mod, "port_busy", return_value=False), \
             redirect_stdout(io.StringIO()) as out:
            code = self.mod.main(argv)
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(out.getvalue())["action"], "authority_grant_invalid")
        validate.assert_not_called()
        ensure_login.assert_not_called()

    def test_no_auto_authorize_parser_flag_overrides_ambient_environment(self):
        with mock.patch.dict(self.mod.os.environ, {"LARK_AUTO_AUTHORIZE": "1"}, clear=False):
            args = self.mod.build_parser().parse_args(["--no-auto-authorize"])
        self.assertFalse(args.auto_authorize)

    def test_stale_lock_is_not_reclaimed_while_owner_pid_is_alive(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "oauth.lock"
            path.write_text(json.dumps({"pid": self.mod.os.getpid(), "created_at": 1}), encoding="utf-8")
            self.mod.os.utime(path, (1, 1))
            lock = self.mod.SingleFlightLock(path, stale_seconds=180)
            self.assertTrue(lock.is_active(now=182))
            self.assertTrue(path.exists())

    def test_stale_lock_is_not_reclaimed_when_owner_probe_is_permission_denied(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "oauth.lock"
            path.write_text(json.dumps({"pid": 424242, "created_at": 1}), encoding="utf-8")
            self.mod.os.utime(path, (1, 1))
            lock = self.mod.SingleFlightLock(path, stale_seconds=180)
            with mock.patch.object(self.mod.os, "kill", side_effect=PermissionError()):
                self.assertTrue(lock.is_active(now=182))
            self.assertTrue(path.exists())

    def test_stale_lock_is_reclaimed_only_when_owner_pid_is_dead(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "oauth.lock"
            path.write_text(json.dumps({"pid": 99999999, "created_at": 1}), encoding="utf-8")
            self.mod.os.utime(path, (1, 1))
            lock = self.mod.SingleFlightLock(path, stale_seconds=180)
            self.assertFalse(lock.is_active(now=182))
            self.assertFalse(path.exists())

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

    def test_redact_secret_boundary_never_returns_nonempty_secret_verbatim(self):
        self.assertEqual(self.mod.redact_secret(""), "")
        self.assertEqual(self.mod.redact_secret("x" * 15), "***")
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

    def test_public_result_redacts_nested_auto_authorize_error_reason(self):
        public = self.mod.redact_result({
            "ok": False,
            "action": "login_failed",
            "auto_authorize": {"ok": False, "reason": "access_token=SECRET", "attempts": 2},
        })
        rendered = json.dumps(public)
        self.assertNotIn("SECRET", rendered)
        self.assertEqual(public["auto_authorize"], {
            "ok": False,
            "reason": "auto_authorize_failed",
            "attempts": 2,
        })

    def test_main_unhandled_error_never_prints_exception_text(self):
        secret = "refresh_token=TOP_SECRET"
        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch.object(self.mod, "ensure_login", side_effect=RuntimeError(secret)), \
             mock.patch.object(self.mod.SingleFlightLock, "is_active", return_value=False), \
             mock.patch.object(self.mod, "port_busy", return_value=False), \
             redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = self.mod.main(["--no-open"])
        self.assertEqual(exit_code, 1)
        self.assertNotIn(secret, stdout.getvalue())
        self.assertNotIn(secret, stderr.getvalue())

    def test_non_json_main_never_prints_auth_url_or_raw_error(self):
        secret = "refresh_token=TOP_SECRET"
        auth_url = "https://example.invalid/oauth?state=TOP_SECRET"
        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch.object(self.mod, "ensure_login", return_value={
                 "ok": False,
                 "action": "login_failed",
                 "auth_url": auth_url,
                 "error": secret,
             }), \
             mock.patch.object(self.mod.SingleFlightLock, "is_active", return_value=False), \
             mock.patch.object(self.mod, "port_busy", return_value=False), \
             redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = self.mod.main(["--no-open"])
        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue().strip(), "login_failed")
        self.assertEqual(stderr.getvalue(), "")
        self.assertNotIn("TOP_SECRET", stdout.getvalue() + stderr.getvalue())

    def test_public_result_omits_raw_child_output_auth_url_and_error_text(self):
        public = self.mod.redact_result({
            "ok": False,
            "action": "login_failed",
            "output_tail": ["access_token=SECRET"],
            "auth_url": "https://example.invalid/oauth?state=SECRET",
            "error": "refresh_token=SECRET",
        })
        rendered = json.dumps(public)
        self.assertNotIn("SECRET", rendered)
        self.assertNotIn("output_tail", public)
        self.assertNotIn("auth_url", public)
        self.assertNotIn("error", public)

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

    def test_status_only_preserves_stale_lock_file_byte_for_byte(self):
        with tempfile.TemporaryDirectory() as td:
            lock_path = Path(td) / "oauth.lock"
            original = json.dumps({"pid": 99999999, "created_at": 1})
            lock_path.write_text(original, encoding="utf-8")
            self.mod.os.utime(lock_path, (1, 1))
            before = lock_path.stat()
            args = self.mod.build_parser().parse_args([
                "--json", "--status-only", "--no-open",
                "--lock", str(lock_path), "--lock-stale-seconds", "1",
            ])
            snapshot = {"tokens": {}, "localTokens": {}}
            with mock.patch.object(self.mod, "auth_snapshot", return_value=snapshot), \
                 mock.patch.object(self.mod, "port_busy", return_value=False), \
                 mock.patch.object(self.mod, "run_login") as run_login:
                result = self.mod.ensure_login(args)
            after = lock_path.stat()
            self.assertEqual(result["action"], "auth_required")
            self.assertFalse(result["lock_active"])
            self.assertEqual(lock_path.read_text(encoding="utf-8"), original)
            self.assertEqual(after.st_mtime_ns, before.st_mtime_ns)
            run_login.assert_not_called()

    def test_main_status_only_preserves_stale_lock_during_post_readback(self):
        with tempfile.TemporaryDirectory() as td:
            lock_path = Path(td) / "oauth.lock"
            original = json.dumps({"pid": 99999999, "created_at": 1})
            lock_path.write_text(original, encoding="utf-8")
            before = lock_path.stat()
            with mock.patch.object(self.mod, "ensure_login", return_value={"ok": False, "action": "auth_required", "status_only": True}), \
                 mock.patch.object(self.mod, "port_busy", return_value=False), \
                 redirect_stdout(io.StringIO()):
                code = self.mod.main(["--json", "--status-only", "--lock", str(lock_path)])
            after = lock_path.stat()
            self.assertEqual(code, 1)
            self.assertEqual(lock_path.read_text(encoding="utf-8"), original)
            self.assertEqual(after.st_mtime_ns, before.st_mtime_ns)

    def test_status_only_never_spawns_login_when_token_is_invalid(self):
        args = self.mod.build_parser().parse_args(["--json", "--status-only", "--no-open"])
        snapshot = {"tokens": {}, "localTokens": {}}
        with mock.patch.object(self.mod, "auth_snapshot", return_value=snapshot) as auth_snapshot, \
             mock.patch.object(self.mod, "port_busy", return_value=False), \
             mock.patch.object(self.mod.SingleFlightLock, "is_active", return_value=False), \
             mock.patch.object(self.mod.SingleFlightLock, "acquire") as acquire, \
             mock.patch.object(self.mod, "run_login") as run_login:
            result = self.mod.ensure_login(args)
        self.assertFalse(result["ok"])
        self.assertEqual(result["action"], "auth_required")
        self.assertEqual(result["planned_action"], "start_login")
        self.assertTrue(result["status_only"])
        auth_snapshot.assert_called_once()
        acquire.assert_not_called()
        run_login.assert_not_called()

    def test_status_only_attests_valid_bound_token_without_spawning(self):
        args = self.mod.build_parser().parse_args(["--json", "--status-only", "--no-open", "--app-id", "cli_test"])
        snapshot = {
            "tokens": {"user-1": {"accessToken": "tok", "expiresAt": 4_102_444_800_000}},
            "localTokens": {"cli_test": "user-1"},
        }
        with mock.patch.object(self.mod, "auth_snapshot", return_value=snapshot), \
             mock.patch.object(self.mod, "port_busy", return_value=False), \
             mock.patch.object(self.mod.SingleFlightLock, "is_active", return_value=False), \
             mock.patch.object(self.mod.SingleFlightLock, "acquire") as acquire, \
             mock.patch.object(self.mod, "run_login") as run_login:
            result = self.mod.ensure_login(args)
        self.assertTrue(result["ok"])
        self.assertEqual(result["action"], "token_valid")
        self.assertEqual(result["planned_action"], "token_valid")
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
        args = self.mod.build_parser().parse_args(["--json", "--no-open", "--force-refresh"])
        # Internal callers may request auto-authorization only after their own
        # durable-grant check; the guard still rejects an impossible no-open pair.
        args.auto_authorize = True
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

    def test_json_main_output_includes_post_action_lock_and_port_readback(self):
        result = {"ok": True, "action": "login_success", "token_status": {"valid": True}}
        with mock.patch.object(self.mod, "ensure_login", return_value=result), \
             mock.patch.object(self.mod.SingleFlightLock, "is_active", return_value=False), \
             mock.patch.object(self.mod, "port_busy", return_value=False):
            buf = io.StringIO()
            with redirect_stdout(buf):
                exit_code = self.mod.main(["--json", "--no-open"])
        self.assertEqual(exit_code, 0)
        payload = json.loads(buf.getvalue())
        self.assertFalse(payload["lock_active_after"])
        self.assertFalse(payload["port_busy_after"])

    def test_json_main_sanitizes_post_action_readback_failures(self):
        for failing in ("lock", "port"):
            with self.subTest(failing=failing):
                result = {"ok": False, "action": "auth_required"}
                lock_probe = mock.Mock(side_effect=OSError("private lock path")) if failing == "lock" else mock.Mock(return_value=False)
                port_probe = mock.Mock(side_effect=OSError("private port detail")) if failing == "port" else mock.Mock(return_value=False)
                with mock.patch.object(self.mod, "ensure_login", return_value=result), \
                     mock.patch.object(self.mod.SingleFlightLock, "is_active", new=lock_probe), \
                     mock.patch.object(self.mod, "port_busy", new=port_probe):
                    buf = io.StringIO()
                    with redirect_stdout(buf):
                        exit_code = self.mod.main(["--json", "--status-only"])
                payload = json.loads(buf.getvalue())
                self.assertEqual(exit_code, 1)
                self.assertEqual(payload["action"], "error")
                self.assertNotIn("private", buf.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)
