import hashlib
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from cocos_delivery_gate import DeliveryGateError, build_preflight, verify_devtools_handoff

BUILD_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BUILD_DIR.parent
GENERATED_PROJECT = PROJECT_ROOT / "evidence" / "cocos-creator-project-candidate"


class CocosDeliveryGateTests(unittest.TestCase):
    def _handoff(self, artifact: Path):
        manifest = json.loads((GENERATED_PROJECT / "project-manifest.json").read_text())
        creator_executable = artifact.parent / "CocosCreator"
        creator_executable.write_bytes(b"creator-editor-binary-fixture")
        creator_executable.chmod(0o755)
        build_config = artifact.parent / "wechat-build-config.json"
        build_config.write_text(json.dumps({"taskName": "wechatgame"}))
        return {
            "schema_version": 1,
            "status": "human_verified",
            "platform": "wechat",
            "project_digest": manifest["project_digest"],
            "serialization_creator_version": manifest["creator_version"],
            "creator_editor_version_readback": "3.8.8",
            "creator_build_target": "wechatgame",
            "build_binding": {
                "creator_executable_path": str(creator_executable),
                "creator_executable_sha256": hashlib.sha256(creator_executable.read_bytes()).hexdigest(),
                "build_config_path": str(build_config),
                "build_config_sha256": hashlib.sha256(build_config.read_bytes()).hexdigest(),
                "creator_editor_version_readback": "3.8.8",
            },
            "artifact": {
                "path": str(artifact),
                "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                "bytes": artifact.stat().st_size,
            },
            "readbacks": {
                "creator_build_exit_code": 36,
                "devtools_import": True,
                "simulator_compile": True,
                "real_device_preview": True,
            },
            "external_stages": {
                "upload": "not_started",
                "review": "not_started",
                "publish": "not_started",
                "rollback": "not_started",
            },
            "authority": {
                "may_invoke_devtools": False,
                "may_submit_platform": False,
                "may_publish": False,
            },
        }

    def test_preflight_fails_closed_with_all_current_blockers(self):
        receipt = build_preflight(GENERATED_PROJECT, "douyin")
        self.assertEqual(receipt["closure_state"], "build_preflight_blocked")
        self.assertEqual(receipt["creator_build_target"], "bytedance-mini-game")
        self.assertEqual(
            set(receipt["blocking_reasons"]),
            {
                "creator_cli_unavailable",
                "creator_editor_version_unverified",
                "appid_required",
                "creator_build_config_export_required",
                "build_authority_closed",
            },
        )
        self.assertIsNone(receipt["command"])
        self.assertFalse(receipt["authority"]["may_build"])

    def test_preflight_never_uses_an_unknown_platform(self):
        with self.assertRaisesRegex(DeliveryGateError, "unsupported platform"):
            build_preflight(GENERATED_PROJECT, "unknown")

    def test_ready_plan_requires_executable_appid_and_exact_authority(self):
        with tempfile.TemporaryDirectory() as tmp:
            executable = Path(tmp) / "CocosCreator"
            executable.write_text("#!/bin/sh\nexit 99\n")
            executable.chmod(0o755)
            config = Path(tmp) / "wechat-build-config.json"
            config.write_text(json.dumps({
                "taskName": "wechatgame",
                "packages": {"wechatgame": {"appid": "wx-test-app-id"}},
            }))
            blocked = build_preflight(
                GENERATED_PROJECT, "wechat", creator_executable=executable,
                creator_editor_version_readback="3.8.8", build_config=config,
                app_id="wx-test-app-id", authority_granted=False,
            )
            self.assertIn("build_authority_closed", blocked["blocking_reasons"])
            self.assertIsNone(blocked["command"])
            ready = build_preflight(
                GENERATED_PROJECT, "wechat", creator_executable=executable,
                creator_editor_version_readback="3.8.8", build_config=config,
                app_id="wx-test-app-id", authority_granted=True,
            )
            self.assertEqual(ready["closure_state"], "ready_to_build")
            self.assertEqual(ready["serialization_creator_version"], "3.8.0")
            self.assertEqual(ready["creator_editor_version_readback"], "3.8.8")
            self.assertEqual(ready["creator_executable_sha256"], hashlib.sha256(executable.read_bytes()).hexdigest())
            self.assertEqual(ready["build_config_sha256"], hashlib.sha256(config.read_bytes()).hexdigest())
            self.assertEqual(
                ready["command"][:3],
                [str(executable.resolve()), "--project", str(GENERATED_PROJECT.resolve())],
            )
            self.assertIn(f"configPath={config.resolve()}", ready["command"][-1])

    def test_preflight_rejects_non_38_version_and_appid_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            executable = Path(tmp) / "CocosCreator"
            executable.write_text("#!/bin/sh\nexit 99\n")
            executable.chmod(0o755)
            config = Path(tmp) / "build-config.json"
            config.write_text(json.dumps({
                "taskName": "wechatgame",
                "packages": {"wechatgame": {"appid": "wx-id"}},
            }))
            receipt = build_preflight(
                GENERATED_PROJECT, "wechat", creator_executable=executable,
                creator_editor_version_readback="3.7.4", build_config=config,
                app_id="wrong-id", authority_granted=True,
            )
            self.assertEqual(
                set(receipt["blocking_reasons"]),
                {"creator_editor_version_unverified", "creator_build_config_target_or_appid_mismatch"},
            )
            self.assertIsNone(receipt["command"])

    def test_preflight_rejects_symlinks_without_executing_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / "executed"
            real_executable = Path(tmp) / "real-creator"
            real_executable.write_text(f"#!/bin/sh\ntouch {marker}\n")
            real_executable.chmod(0o755)
            executable = Path(tmp) / "CocosCreator"
            executable.symlink_to(real_executable)
            real_config = Path(tmp) / "real-config.json"
            real_config.write_text(json.dumps({
                "taskName": "wechatgame",
                "packages": {"wechatgame": {"appid": "wx-id"}},
            }))
            config = Path(tmp) / "build-config.json"
            config.symlink_to(real_config)
            receipt = build_preflight(
                GENERATED_PROJECT, "wechat", creator_executable=executable,
                creator_editor_version_readback="3.8.8", build_config=config,
                app_id="wx-id", authority_granted=True,
            )
            self.assertEqual(
                set(receipt["blocking_reasons"]),
                {"creator_cli_unavailable", "creator_build_config_symlink_rejected"},
            )
            self.assertFalse(marker.exists())

    def test_handoff_verifier_accepts_complete_local_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "game.zip"
            artifact.write_bytes(b"verified-artifact")
            receipt = self._handoff(artifact)
            verified = verify_devtools_handoff(receipt, GENERATED_PROJECT)
            self.assertEqual(verified["closure_state"], "devtools_handoff_receipt_integrity_verified")
            self.assertIn("does not independently observe", verified["claim_boundary"])
            self.assertEqual(verified["artifact"]["sha256"], receipt["artifact"]["sha256"])
            self.assertEqual(verified["serialization_creator_version"], "3.8.0")
            self.assertEqual(verified["creator_editor_version_readback"], "3.8.8")
            self.assertEqual(
                verified["build_binding"]["creator_executable_path"],
                str(Path(receipt["build_binding"]["creator_executable_path"]).resolve()),
            )
            self.assertEqual(
                verified["build_binding"]["build_config_path"],
                str(Path(receipt["build_binding"]["build_config_path"]).resolve()),
            )
            self.assertEqual(
                verified["build_binding"]["creator_executable_sha256"],
                receipt["build_binding"]["creator_executable_sha256"],
            )
            self.assertEqual(
                verified["build_binding"]["build_config_sha256"],
                receipt["build_binding"]["build_config_sha256"],
            )

    def test_handoff_rejects_serialization_or_editor_build_binding_version_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "game.zip"
            artifact.write_bytes(b"verified-artifact")
            receipt = self._handoff(artifact)
            receipt["serialization_creator_version"] = "3.8.8"
            with self.assertRaisesRegex(DeliveryGateError, "serialization_creator_version"):
                verify_devtools_handoff(receipt, GENERATED_PROJECT)
            for invalid in ("3.8", "3.8.x", "3.9.0", ""):
                receipt = self._handoff(artifact)
                receipt["creator_editor_version_readback"] = invalid
                receipt["build_binding"]["creator_editor_version_readback"] = invalid
                with self.assertRaisesRegex(DeliveryGateError, "exact 3.8.x patch"):
                    verify_devtools_handoff(receipt, GENERATED_PROJECT)
            receipt = self._handoff(artifact)
            receipt["build_binding"]["creator_editor_version_readback"] = "3.8.7"
            with self.assertRaisesRegex(DeliveryGateError, "editor version binding mismatch"):
                verify_devtools_handoff(receipt, GENERATED_PROJECT)

    def test_handoff_rejects_build_executable_or_config_digest_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "game.zip"
            artifact.write_bytes(b"verified-artifact")
            receipt = self._handoff(artifact)
            receipt["build_binding"]["creator_executable_sha256"] = "0" * 64
            with self.assertRaisesRegex(DeliveryGateError, "creator executable digest"):
                verify_devtools_handoff(receipt, GENERATED_PROJECT)
            receipt = self._handoff(artifact)
            receipt["build_binding"]["build_config_sha256"] = "0" * 64
            with self.assertRaisesRegex(DeliveryGateError, "build config digest"):
                verify_devtools_handoff(receipt, GENERATED_PROJECT)

    def test_handoff_verifier_rejects_creator_exit_zero_because_official_success_is_36(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "game.zip"
            artifact.write_bytes(b"verified-artifact")
            receipt = self._handoff(artifact)
            receipt["readbacks"]["creator_build_exit_code"] = 0
            with self.assertRaisesRegex(DeliveryGateError, "creator_build_exit_code"):
                verify_devtools_handoff(receipt, GENERATED_PROJECT)

    def test_handoff_verifier_rejects_missing_real_device_readback(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "game.zip"
            artifact.write_bytes(b"verified-artifact")
            receipt = self._handoff(artifact)
            receipt["readbacks"]["real_device_preview"] = False
            with self.assertRaisesRegex(DeliveryGateError, "real_device_preview"):
                verify_devtools_handoff(receipt, GENERATED_PROJECT)

    def test_handoff_rejects_digest_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "game.zip"
            artifact.write_bytes(b"verified-artifact")
            receipt = self._handoff(artifact)
            receipt["artifact"]["sha256"] = "0" * 64
            with self.assertRaisesRegex(DeliveryGateError, "digest"):
                verify_devtools_handoff(receipt, GENERATED_PROJECT)

    def test_handoff_rejects_platform_mismatch_and_extra_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "game.zip"
            artifact.write_bytes(b"verified-artifact")
            receipt = self._handoff(artifact)
            receipt["creator_build_target"] = "bytedance-mini-game"
            with self.assertRaisesRegex(DeliveryGateError, "target"):
                verify_devtools_handoff(receipt, GENERATED_PROJECT)
            receipt = deepcopy(self._handoff(artifact))
            receipt["unexpected"] = True
            with self.assertRaisesRegex(DeliveryGateError, "unknown fields"):
                verify_devtools_handoff(receipt, GENERATED_PROJECT)

    def test_handoff_rejects_relative_artifact_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "game.zip"
            artifact.write_bytes(b"verified-artifact")
            receipt = self._handoff(artifact)
            receipt["artifact"]["path"] = "game.zip"
            with self.assertRaisesRegex(DeliveryGateError, "must be absolute"):
                verify_devtools_handoff(receipt, GENERATED_PROJECT)

    def test_handoff_rejects_symlink_artifact_and_open_authority(self):
        with tempfile.TemporaryDirectory() as tmp:
            real_artifact = Path(tmp) / "real-game.zip"
            real_artifact.write_bytes(b"verified-artifact")
            artifact = Path(tmp) / "game.zip"
            artifact.symlink_to(real_artifact)
            with self.assertRaisesRegex(DeliveryGateError, "symlink"):
                verify_devtools_handoff(self._handoff(artifact), GENERATED_PROJECT)
            receipt = self._handoff(real_artifact)
            receipt["authority"]["may_publish"] = True
            with self.assertRaisesRegex(DeliveryGateError, "authority"):
                verify_devtools_handoff(receipt, GENERATED_PROJECT)

    def test_handoff_rejects_claimed_external_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifact = Path(tmp) / "game.zip"
            artifact.write_bytes(b"verified-artifact")
            receipt = self._handoff(artifact)
            receipt["external_stages"]["upload"] = "completed"
            with self.assertRaisesRegex(DeliveryGateError, "cannot claim"):
                verify_devtools_handoff(receipt, GENERATED_PROJECT)


if __name__ == "__main__":
    unittest.main()
