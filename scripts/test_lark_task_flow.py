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


def verified_auth(action="token_valid"):
    return {
        "ok": True,
        "action": action,
        "token_status": {"valid": True},
        "lock_active_after": False,
        "port_busy_after": False,
    }


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
             mock.patch.object(self.mod, "run_guard", return_value=verified_auth()):
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
            root = Path(td).resolve()
            grant = root / "grant.json"
            profile = root / "profile.json"
            grant.write_text(json.dumps({
                "schema": "lark_oauth_recovery_authority_grant_v1",
                "grant_id": "grant",
                "status": "active",
                "action": "auto_singleflight_oauth_recovery",
                "scope": "oauth_recovery_only",
                "trigger": "token_missing_invalid_or_expired_during_non_health_lark_flow",
                "allowed_entrypoints": [str(MODULE_PATH)],
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
                "subject": {
                    "profile_id": "lark",
                    "profile_ref": str(profile.absolute()),
                },
            }), encoding="utf-8")
            profile.write_text(json.dumps({
                "schema": "profile_policy_contract_v1",
                "project": "lark",
                "automation_policy": {
                    "lark_oauth_recovery": {
                        "status": "enabled",
                        "authority_grant_ref": str(grant),
                        "trigger": "token_missing_invalid_or_expired_during_non_health_lark_flow",
                        "ordinary_selfcheck_may_execute": False,
                        "task_read_authorized": False,
                        "lark_write_authorized": False,
                    }
                },
            }), encoding="utf-8")
            self.assertTrue(self.mod.oauth_recovery_auto_authorized(profile, root))
            subject_mismatch = json.loads(grant.read_text(encoding="utf-8"))
            subject_mismatch["subject"]["profile_id"] = "another-profile"
            grant.write_text(json.dumps(subject_mismatch), encoding="utf-8")
            self.assertFalse(self.mod.oauth_recovery_auto_authorized(profile, root))
            subject_mismatch["subject"]["profile_id"] = "lark"
            subject_mismatch["status"] = "revoked"
            grant.write_text(json.dumps(subject_mismatch), encoding="utf-8")
            self.assertFalse(self.mod.oauth_recovery_auto_authorized(profile, root))

    def test_oauth_recovery_policy_rejects_wrong_entrypoint_or_trigger(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve()
            grant = root / "grant.json"
            profile = root / "profile.json"
            base_grant = {
                "schema": "lark_oauth_recovery_authority_grant_v1",
                "grant_id": "grant",
                "status": "active",
                "action": "auto_singleflight_oauth_recovery",
                "scope": "oauth_recovery_only",
                "trigger": "wrong_trigger",
                "allowed_entrypoints": [str(MODULE_PATH)],
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
            }
            grant.write_text(json.dumps(base_grant), encoding="utf-8")
            profile.write_text(json.dumps({
                "schema": "profile_policy_contract_v1",
                "automation_policy": {"lark_oauth_recovery": {
                    "status": "enabled",
                    "authority_grant_ref": str(grant),
                    "trigger": "token_missing_invalid_or_expired_during_non_health_lark_flow",
                    "ordinary_selfcheck_may_execute": False,
                    "task_read_authorized": False,
                    "lark_write_authorized": False,
                }},
            }), encoding="utf-8")
            self.assertFalse(self.mod.oauth_recovery_auto_authorized(profile, root))
            base_grant["trigger"] = "token_missing_invalid_or_expired_during_non_health_lark_flow"
            base_grant["allowed_entrypoints"] = ["/tmp/not-the-entrypoint.py"]
            grant.write_text(json.dumps(base_grant), encoding="utf-8")
            self.assertFalse(self.mod.oauth_recovery_auto_authorized(profile, root))

    def test_oauth_recovery_policy_returns_false_for_non_object_json(self):
        with tempfile.TemporaryDirectory() as td:
            profile = Path(td) / "profile.json"
            profile.write_text("[]", encoding="utf-8")
            self.assertFalse(self.mod.oauth_recovery_auto_authorized(profile, Path(td)))

    def test_oauth_recovery_policy_rejects_symlinked_ancestor_of_allowed_root(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td).resolve()
            real_parent = base / "real-parent"
            real_root = real_parent / "authority-grants"
            real_root.mkdir(parents=True)
            alias_parent = base / "alias-parent"
            alias_parent.symlink_to(real_parent, target_is_directory=True)
            configured_root = alias_parent / "authority-grants"
            profile = base / "profile.json"
            grant = configured_root / "grant.json"
            grant.write_text(json.dumps({
                "schema": "lark_oauth_recovery_authority_grant_v1",
                "grant_id": "grant",
                "status": "active",
                "action": "auto_singleflight_oauth_recovery",
                "scope": "oauth_recovery_only",
                "trigger": self.mod.DURABLE_RECOVERY_TRIGGER,
                "allowed_entrypoints": [str(MODULE_PATH)],
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
                "subject": {"profile_id": "lark", "profile_ref": str(profile.absolute())},
            }), encoding="utf-8")
            profile.write_text(json.dumps({
                "schema": "profile_policy_contract_v1",
                "project": "lark",
                "automation_policy": {"lark_oauth_recovery": {
                    "status": "enabled",
                    "authority_grant_ref": str(grant),
                    "trigger": self.mod.DURABLE_RECOVERY_TRIGGER,
                    "ordinary_selfcheck_may_execute": False,
                    "task_read_authorized": False,
                    "lark_write_authorized": False,
                }},
            }), encoding="utf-8")
            self.assertFalse(self.mod.oauth_recovery_auto_authorized(profile, configured_root))

    def test_oauth_recovery_policy_rejects_intermediate_symlink_in_grant_path(self):
        actual_root = self.mod.LARK_AUTHORITY_GRANT_ROOT
        actual_grant = actual_root / "lark-oauth-recovery-persistent-20260710.json"
        with tempfile.TemporaryDirectory() as td:
            alias = Path(td) / "authority-grants-alias"
            alias.symlink_to(actual_root, target_is_directory=True)
            profile = Path(td) / "profile.json"
            profile.write_text(json.dumps({
                "schema": "profile_policy_contract_v1",
                "automation_policy": {"lark_oauth_recovery": {
                    "status": "enabled",
                    "authority_grant_ref": str(alias / actual_grant.name),
                    "trigger": "token_missing_invalid_or_expired_during_non_health_lark_flow",
                    "ordinary_selfcheck_may_execute": False,
                    "task_read_authorized": False,
                    "lark_write_authorized": False,
                }},
            }), encoding="utf-8")
            self.assertFalse(self.mod.oauth_recovery_auto_authorized(profile, actual_root))

    def test_oauth_recovery_policy_rejects_symlinked_allowed_root(self):
        actual_root = self.mod.LARK_AUTHORITY_GRANT_ROOT
        actual_grant = actual_root / "lark-oauth-recovery-persistent-20260710.json"
        with tempfile.TemporaryDirectory() as td:
            alias = Path(td) / "authority-grants-alias"
            alias.symlink_to(actual_root, target_is_directory=True)
            profile = Path(td) / "profile.json"
            profile.write_text(json.dumps({
                "schema": "profile_policy_contract_v1",
                "automation_policy": {"lark_oauth_recovery": {
                    "status": "enabled",
                    "authority_grant_ref": str(alias / actual_grant.name),
                    "trigger": "token_missing_invalid_or_expired_during_non_health_lark_flow",
                    "ordinary_selfcheck_may_execute": False,
                    "task_read_authorized": False,
                    "lark_write_authorized": False,
                }},
            }), encoding="utf-8")
            self.assertFalse(self.mod.oauth_recovery_auto_authorized(profile, alias))

    def test_oauth_recovery_policy_rejects_grant_outside_allowed_root(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "authority-grants"
            root.mkdir()
            outside = base / "outside-grant.json"
            outside.write_text(json.dumps({
                "schema": "lark_oauth_recovery_authority_grant_v1",
                "grant_id": "grant",
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
            return verified_auth("login_success")

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

    def test_force_refresh_does_not_consume_durable_recovery_grant(self):
        observed = {}

        def guard(args):
            observed["auto_authorize"] = args.auto_authorize
            return verified_auth()

        with mock.patch.object(self.mod, "oauth_recovery_auto_authorized", return_value=True), \
             mock.patch.object(self.mod, "run_guard", side_effect=guard):
            with redirect_stdout(io.StringIO()):
                code = self.mod.main(["--auth-only", "--force-refresh"])
        self.assertEqual(code, 0)
        self.assertFalse(observed["auto_authorize"])

    def test_durable_recovery_grant_does_not_authorize_task_read_lane(self):
        fake = FakeReader()
        observed = {}

        def guard(args):
            observed["auto_authorize"] = args.auto_authorize
            return verified_auth()

        with mock.patch.object(self.mod, "oauth_recovery_auto_authorized", return_value=True), \
             mock.patch.object(self.mod, "load_reader", return_value=fake), \
             mock.patch.object(self.mod, "run_guard", side_effect=guard):
            with redirect_stdout(io.StringIO()):
                code = self.mod.main(["--summary"])
        self.assertEqual(code, 0)
        self.assertFalse(observed["auto_authorize"])
        self.assertEqual(fake.calls[0][0], "get_token")

    def test_unverified_guard_success_is_rejected(self):
        with mock.patch.object(self.mod, "run_guard", return_value={"ok": True, "action": "login_success"}):
            out = io.StringIO()
            with redirect_stdout(out):
                code = self.mod.main(["--auth-only", "--no-auto-authorize"])
        self.assertEqual(code, 1)
        self.assertIn("guard_post_action_unverified", out.getvalue())

    def test_durable_recovery_timeout_is_clamped_to_grant_ttl(self):
        observed = {}

        def guard(args):
            observed["auth_timeout"] = args.auth_timeout
            observed["auto_authorize_timeout"] = args.auto_authorize_timeout
            return verified_auth("login_success")

        with mock.patch.object(self.mod, "oauth_recovery_auto_authorized", return_value=True), \
             mock.patch.object(self.mod, "run_guard", side_effect=guard):
            with redirect_stdout(io.StringIO()):
                code = self.mod.main(["--auth-only", "--auth-timeout", "999", "--auto-authorize-timeout", "999"])
        self.assertEqual(code, 0)
        self.assertLessEqual(observed["auth_timeout"], 300)
        self.assertLessEqual(observed["auto_authorize_timeout"], observed["auth_timeout"])

    def test_main_unhandled_exception_does_not_expose_exception_text(self):
        secret = "access_token=TOP_SECRET"
        with mock.patch.object(self.mod, "extract_guid", side_effect=RuntimeError(secret)):
            out = io.StringIO()
            with redirect_stdout(out):
                code = self.mod.main(["--auth-only", "--no-auto-authorize"])
        payload = json.loads(out.getvalue())
        self.assertEqual(code, 1)
        self.assertEqual(payload, {
            "ok": False,
            "stage": "error",
            "error_code": "unhandled_flow_error",
        })
        self.assertNotIn(secret, out.getvalue())

    def test_terminate_process_group_kills_surviving_descendants_after_parent_exits(self):
        proc = mock.Mock(pid=4242)
        proc.wait.return_value = 0
        with mock.patch.object(self.mod.os, "killpg") as killpg:
            self.mod._terminate_process_group(proc, grace_seconds=1)
        self.assertEqual(
            killpg.call_args_list,
            [
                mock.call(4242, self.mod.signal.SIGTERM),
                mock.call(4242, 0),
                mock.call(4242, self.mod.signal.SIGKILL),
            ],
        )

    def test_terminate_process_group_escalates_after_grace_timeout(self):
        proc = mock.Mock(pid=4242)
        proc.wait.side_effect = [self.mod.subprocess.TimeoutExpired(cmd="guard", timeout=1), 0]
        with mock.patch.object(self.mod.os, "killpg") as killpg:
            self.mod._terminate_process_group(proc, grace_seconds=1)
        self.assertEqual(
            killpg.call_args_list,
            [
                mock.call(4242, self.mod.signal.SIGTERM),
                mock.call(4242, 0),
                mock.call(4242, self.mod.signal.SIGKILL),
            ],
        )

    def test_terminate_process_group_reaps_child_when_group_already_gone(self):
        proc = mock.Mock(pid=4242)
        proc.wait.return_value = 0
        with mock.patch.object(
            self.mod.os,
            "killpg",
            side_effect=[ProcessLookupError(), ProcessLookupError()],
        ) as killpg:
            self.mod._terminate_process_group(proc, grace_seconds=1)
        self.assertEqual(
            killpg.call_args_list,
            [mock.call(4242, self.mod.signal.SIGTERM), mock.call(4242, 0)],
        )
        self.assertEqual(proc.wait.call_count, 2)

    def test_terminate_process_group_reaps_child_when_kill_races_with_exit(self):
        proc = mock.Mock(pid=4242)
        proc.wait.return_value = 0
        with mock.patch.object(
            self.mod.os,
            "killpg",
            side_effect=[None, None, ProcessLookupError()],
        ):
            self.mod._terminate_process_group(proc, grace_seconds=1)
        self.assertEqual(proc.wait.call_count, 2)

    def test_run_guard_process_uses_isolated_process_group(self):
        proc = mock.Mock(returncode=0)
        proc.communicate.return_value = ('{"ok": true}', "")
        with mock.patch.object(self.mod.subprocess, "Popen", return_value=proc) as popen:
            completed = self.mod._run_guard_process(["guard"], timeout_seconds=2)
        self.assertTrue(popen.call_args.kwargs["start_new_session"])
        self.assertEqual(completed.stdout, '{"ok": true}')
        self.assertEqual(completed.returncode, 0)

    def test_run_guard_process_includes_sigterm_ignoring_cleanup_in_deadline(self):
        child = [
            self.mod.sys.executable,
            "-c",
            "import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(30)",
        ]
        started = self.mod.time.monotonic()
        result = self.mod._run_guard_process(child, timeout_seconds=0.5)
        elapsed = self.mod.time.monotonic() - started
        self.assertIsNone(result)
        self.assertLess(elapsed, 1.0)

    def test_run_guard_total_deadline_includes_cleanup_and_readback(self):
        with tempfile.TemporaryDirectory() as td:
            guard = Path(td) / "guard.py"
            guard.write_text(
                "import signal,time\n"
                "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
                "time.sleep(30)\n",
                encoding="utf-8",
            )
            args = self.mod.build_parser().parse_args([
                "--auth-only", "--no-auto-authorize", "--auth-timeout", "1",
            ])
            with mock.patch.object(self.mod, "GUARD", guard):
                started = self.mod.time.monotonic()
                result = self.mod.run_guard(args)
                elapsed = self.mod.time.monotonic() - started
        self.assertEqual(result["action"], "guard_timeout")
        self.assertLess(elapsed, 1.2)

    def test_post_timeout_readback_uses_isolated_status_only_group(self):
        completed = mock.Mock(
            returncode=1,
            stdout=json.dumps({
                "ok": False,
                "action": "auth_required",
                "token_status": {"valid": False},
                "lock_active_after": False,
                "port_busy_after": False,
            }),
            stderr="",
        )
        with mock.patch.object(self.mod, "_run_guard_process", return_value=completed) as runner:
            result = self.mod._post_timeout_guard_readback(3)
        command, timeout_seconds = runner.call_args.args
        self.assertIn("--status-only", command)
        self.assertIn("--no-open", command)
        self.assertIn("--no-auto-authorize", command)
        self.assertEqual(timeout_seconds, 3)
        self.assertEqual(result["token_status"], {"valid": False})
        self.assertFalse(result["lock_active_after"])
        self.assertFalse(result["port_busy_after"])

    def test_run_guard_timeout_terminates_process_group_and_returns_bounded_readback(self):
        args = self.mod.build_parser().parse_args([
            "--auth-only", "--no-auto-authorize", "--auth-timeout", "30",
        ])
        readback = {
            "ok": False,
            "action": "auth_required",
            "token_status": {"valid": False},
            "lock_active_after": False,
            "port_busy_after": False,
        }
        with mock.patch.object(self.mod, "_run_guard_process", return_value=None) as runner, \
             mock.patch.object(self.mod, "_post_timeout_guard_readback", return_value=readback) as post:
            result = self.mod.run_guard(args)
        self.assertEqual(result["action"], "guard_timeout")
        self.assertEqual(result["token_status"], {"valid": False})
        self.assertFalse(result["lock_active_after"])
        self.assertFalse(result["port_busy_after"])
        self.assertLess(runner.call_args.args[1], 30)
        self.assertIn("--bound-defaults", runner.call_args.args[0])
        post.assert_called_once()

    def test_run_guard_error_does_not_expose_raw_child_output(self):
        args = self.mod.build_parser().parse_args(["--auth-only", "--no-auto-authorize"])
        exc = self.mod.subprocess.TimeoutExpired(
            cmd=["guard"], timeout=1, output="access_token=SECRET", stderr="refresh_token=SECRET"
        )
        with mock.patch.object(self.mod, "_run_guard_process", return_value=None), \
             mock.patch.object(self.mod, "_post_timeout_guard_readback", return_value={"ok": False, "action": "auth_required"}):
            result = self.mod.run_guard(args)
        rendered = json.dumps(result)
        self.assertNotIn("SECRET", rendered)
        self.assertNotIn("stdout_tail", result)
        self.assertNotIn("stderr_tail", result)

    def test_run_guard_non_object_json_fails_closed(self):
        args = self.mod.build_parser().parse_args(["--auth-only", "--no-auto-authorize"])
        completed = mock.Mock(returncode=0, stdout="[]", stderr="")
        with mock.patch.object(self.mod, "_run_guard_process", return_value=completed):
            result = self.mod.run_guard(args)
        self.assertEqual(result, {"ok": False, "action": "invalid_guard_payload"})

    def test_run_guard_allowlists_fields_and_drops_auth_url_and_child_output(self):
        args = self.mod.build_parser().parse_args(["--auth-only", "--no-auto-authorize"])
        payload = verified_auth("login_success") | {
            "auth_url": "https://example.invalid/oauth?state=SECRET",
            "output_tail": ["access_token=SECRET"],
        }
        completed = mock.Mock(returncode=0, stdout=json.dumps(payload), stderr="refresh_token=SECRET")
        with mock.patch.object(self.mod, "_run_guard_process", return_value=completed):
            result = self.mod.run_guard(args)
        rendered = json.dumps(result)
        self.assertNotIn("SECRET", rendered)
        self.assertNotIn("auth_url", result)
        self.assertNotIn("output_tail", result)

    def test_run_guard_explicitly_disables_child_auto_authorize_and_bounds_total_timeout(self):
        args = self.mod.build_parser().parse_args([
            "--auth-only", "--no-auto-authorize", "--auth-timeout", "300",
        ])
        completed = mock.Mock(returncode=1, stdout=json.dumps({"ok": False, "action": "auth_required"}), stderr="")
        with mock.patch.object(self.mod, "_run_guard_process", return_value=completed) as run:
            self.mod.run_guard(args)
        command, process_timeout = run.call_args.args
        self.assertIn("--no-auto-authorize", command)
        child_timeout = int(command[command.index("--timeout") + 1])
        self.assertLess(child_timeout, 300)
        self.assertLess(process_timeout, 300)

    def test_health_check_guard_command_never_enables_stale_cleanup(self):
        args = self.mod.build_parser().parse_args(["--health-check"])
        args.auth_only = True
        args.no_open = True
        args.auto_authorize = False
        args.force_refresh = False
        args.auth_timeout = 5
        completed = mock.Mock(returncode=0, stdout='{"ok": true, "action": "token_valid"}', stderr="")
        with mock.patch.object(self.mod, "_run_guard_process", return_value=completed) as run:
            result = self.mod.run_guard(args)
        cmd = run.call_args.args[0]
        self.assertTrue(result["ok"])
        self.assertNotIn("--cleanup-stale", cmd)
        self.assertIn("--status-only", cmd)
        self.assertIn("--no-open", cmd)
        self.assertNotIn("--auto-authorize", cmd)

    def test_health_check_auth_required_still_reports_zero_side_effect_boundary(self):
        fake = FakeReader()
        guard_result = {
            "ok": False,
            "action": "auth_required",
            "status_only": True,
            "token_status": {"valid": False},
            "lock_active_after": False,
            "port_busy_after": False,
        }
        with mock.patch.object(self.mod, "load_reader", return_value=fake), \
             mock.patch.object(self.mod, "run_guard", return_value=guard_result):
            out = io.StringIO()
            with redirect_stdout(out):
                code = self.mod.main(["--health-check"])
        result = json.loads(out.getvalue())
        self.assertEqual(code, 1)
        self.assertFalse(result["ok"])
        self.assertEqual(result["stage"], "auth")
        self.assertEqual(result["side_effect_boundary"], {
            "auto_authorize_enabled": False,
            "task_read_executed": False,
            "lark_write_executed": False,
        })
        self.assertEqual(fake.calls, [])

    def test_health_check_is_status_only_and_never_opens_browser_or_reads_tasks(self):
        fake = FakeReader()
        observed = {}

        def guard(args):
            observed.update({"no_open": args.no_open, "auto_authorize": args.auto_authorize, "auth_only": args.auth_only, "auth_timeout": args.auth_timeout})
            return verified_auth()

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
