from __future__ import annotations

import hashlib
import inspect
import io
import os
import plistlib
import tarfile
from pathlib import Path

import pytest

from loop_a_protected.canonical import canonical_bytes, with_self_digest
from loop_a_protected.darwin_launchd import (
    build_root_broker_plist,
    build_worker_plist,
    serialize_root_broker_plist,
    serialize_worker_plist,
)
from loop_a_protected.manifests import finalize_inventory, finalize_manifest


VERSION = "a" * 64
ROOT = "/private/var/db/hermes-loop-a"
BUNDLE_PATH = "/private/var/tmp/hermes-loop-a-deployment/loop-a-v10.bundle.tar"
WORKER_PLIST_PATH = "/Library/LaunchDaemons/com.nous.hermes-loop-a.worker.plist"
BROKER_PLIST_PATH = "/Library/LaunchDaemons/com.nous.hermes-loop-a.root-broker.plist"


def runtime_inputs(tmp_path: Path):
    tmp_path.mkdir(parents=True, exist_ok=True)
    content = b"python\n"
    worker_entrypoint = b"worker\n"
    broker_entrypoint = b"broker\n"
    entries = [
        {"relative_path": "bin", "type": "directory", "mode": 0o555, "uid": 0, "gid": 0,
         "size": None, "sha256": None, "executable": False},
        {"relative_path": "bin/python3", "type": "file", "mode": 0o555, "uid": 0, "gid": 0,
         "size": len(content), "sha256": hashlib.sha256(content).hexdigest(), "executable": True},
        {"relative_path": "libexec/loop_a_protected", "type": "directory", "mode": 0o555,
         "uid": 0, "gid": 0, "size": None, "sha256": None, "executable": False},
        {"relative_path": "libexec/root-broker-entrypoint.py", "type": "file", "mode": 0o444,
         "uid": 0, "gid": 0, "size": len(broker_entrypoint),
         "sha256": hashlib.sha256(broker_entrypoint).hexdigest(), "executable": False},
        {"relative_path": "libexec/worker-bootstrap.py", "type": "file", "mode": 0o444,
         "uid": 0, "gid": 0, "size": len(worker_entrypoint),
         "sha256": hashlib.sha256(worker_entrypoint).hexdigest(), "executable": False},
    ]
    inventory = finalize_inventory("runtime", "123e4567-e89b-42d3-a456-426614174000", 10, entries)
    manifest = finalize_manifest(
        "runtime", "123e4567-e89b-42d3-a456-426614174000", 10,
        "2026-08-03T01:02:03Z", 10, entries, inventory["inventory_digest"],
        {"protected_roles": ["bin/python3"], "external_dependencies": [],
         "platform_build": "26A123", "snapshot_uuid": "123e4567-e89b-42d3-a456-426614174010",
         "seal_identity": "sealed", "cryptex_generation": "1",
         "dyld_cache_uuid": "123e4567-e89b-42d3-a456-426614174011", "sip_enabled": True},
    )
    # The real version is manifest-derived; use it in all launchd paths and archive names.
    version = manifest["version_digest"]
    archive = tmp_path / "runtime.tar"
    with tarfile.open(archive, "w", format=tarfile.GNU_FORMAT) as value:
        for name, mode, data, kind in (
            (f"runtime/versions/{version}/bin", 0o555, None, tarfile.DIRTYPE),
            (f"runtime/versions/{version}/bin/python3", 0o555, content, tarfile.REGTYPE),
            (f"runtime/versions/{version}/libexec/loop_a_protected/", 0o555, None, tarfile.DIRTYPE),
            (f"runtime/versions/{version}/libexec/root-broker-entrypoint.py", 0o444,
             broker_entrypoint, tarfile.REGTYPE),
            (f"runtime/versions/{version}/libexec/worker-bootstrap.py", 0o444,
             worker_entrypoint, tarfile.REGTYPE),
            (f"metadata/runtime-{version}.manifest.json", 0o444, canonical_bytes(manifest), tarfile.REGTYPE),
            (f"metadata/runtime-{version}.inventory.json", 0o444, canonical_bytes(inventory), tarfile.REGTYPE),
        ):
            info = tarfile.TarInfo(name)
            info.uid = info.gid = info.mtime = 0
            info.uname, info.gname, info.mode, info.type = "root", "wheel", mode, kind
            if data is not None:
                info.size = len(data)
                value.addfile(info, io.BytesIO(data))
            else:
                value.addfile(info)
    interpreter = f"{ROOT}/runtime/versions/{version}/bin/python3"
    worker = serialize_worker_plist(build_worker_plist(
        interpreter_path=interpreter,
        entrypoint_path=f"{ROOT}/runtime/versions/{version}/libexec/worker-bootstrap.py",
    ))
    broker = serialize_root_broker_plist(build_root_broker_plist(
        interpreter_path=interpreter,
        entrypoint_path=f"{ROOT}/runtime/versions/{version}/libexec/root-broker-entrypoint.py",
    ))
    return archive, manifest, inventory, worker, broker


def compose(tmp_path: Path, **overrides):
    from loop_a_protected.darwin_installer import compose_darwin_deployment_bundle

    archive, manifest, inventory, worker, broker = runtime_inputs(tmp_path)
    values = {
        "runtime_archive": archive,
        "expected_runtime_archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "runtime_manifest_bytes": canonical_bytes(manifest),
        "expected_runtime_manifest_digest": manifest["version_digest"],
        "runtime_inventory_bytes": canonical_bytes(inventory),
        "expected_runtime_inventory_digest": inventory["inventory_digest"],
        "authorized_uid": 399,
        "authorized_gid": 399,
        "worker_plist_bytes": worker,
        "root_broker_plist_bytes": broker,
        "target_root": ROOT,
        "bundle_path": BUNDLE_PATH,
        "prior_worker_plist_bytes": None,
        "prior_root_broker_plist_bytes": None,
        "prior_active_version": None,
    }
    values.update(overrides)
    return compose_darwin_deployment_bundle(**values)


def test_composer_emits_deterministic_exact_bundle_and_digest(tmp_path):
    first = compose(tmp_path / "one")
    second = compose(tmp_path / "two")
    assert first.artifact_bytes == second.artifact_bytes
    assert first.artifact_sha256 == hashlib.sha256(first.artifact_bytes).hexdigest()
    assert first.plan_bytes == canonical_bytes(first.plan)
    with tarfile.open(fileobj=io.BytesIO(first.artifact_bytes), mode="r:") as archive:
        names = archive.getnames()
        assert names == sorted(names, key=lambda value: value.encode("utf-8"))
        assert set(names) == {
            "HUMAN-APPLY-VERIFY-ROLLBACK.txt",
            "deployment/plan.json",
            "deployment/preimage-receipt.json",
            "deployment/rollback-receipt-template.json",
            "payload/root-broker.plist",
            "payload/runtime-inventory.json",
            "payload/runtime-manifest.json",
            "payload/runtime.tar",
            "payload/worker.plist",
        }
        assert all(m.uid == 0 and m.gid == 0 and m.mtime == 0 for m in archive.getmembers())


def test_plan_has_exact_apply_verify_rollback_boundary_and_receipts(tmp_path):
    bundle = compose(tmp_path)
    plan = bundle.plan
    assert plan["authority"] == "human-execution-required"
    assert plan["host_mutation_performed"] is False
    assert plan["target_root"] == ROOT
    assert plan["account"]["uid"] == 399 and plan["account"]["gid"] == 399
    assert plan["preimage_receipt_sha256"] == hashlib.sha256(bundle.preimage_receipt_bytes).hexdigest()
    assert plan["rollback_receipt_template_sha256"] == hashlib.sha256(bundle.rollback_receipt_template_bytes).hexdigest()
    assert plan["preimage_readback"] == [
        {"id": "P01", "argv": ["/bin/test", "!", "-e", WORKER_PLIST_PATH],
         "required_readback": "absent"},
        {"id": "P02", "argv": ["/bin/test", "!", "-e", BROKER_PLIST_PATH],
         "required_readback": "absent"},
        {"id": "P03", "argv": ["/bin/test", "!", "-e", f"{BUNDLE_PATH}.expanded"],
         "required_readback": "absent"},
    ]
    assert plan["apply"][0]["gate"] == "preimage-receipt-readback"
    assert plan["apply"][1]["argv"] == [
        "/usr/bin/install", "-d", "-o", "root", "-g", "wheel", "-m", "0700",
        f"{BUNDLE_PATH}.expanded",
    ]
    assert plan["apply"][2]["argv"] == [
        "/usr/bin/tar", "-xpf", BUNDLE_PATH, "-C", f"{BUNDLE_PATH}.expanded"
    ]
    required_layout = {
        ("0755", ROOT),
        ("0755", f"{ROOT}/active-skills"),
        ("0755", f"{ROOT}/authorizations"),
        ("0750", f"{ROOT}/control"),
        ("0700", f"{ROOT}/installer-transactions"),
        ("0755", f"{ROOT}/locks"),
        ("0755", f"{ROOT}/metadata"),
        ("0755", f"{ROOT}/policy"),
        ("0755", f"{ROOT}/runtime"),
        ("0755", f"{ROOT}/runtime/versions"),
        ("0700", f"{ROOT}/service"),
        ("0700", f"{ROOT}/service-transactions"),
    }
    install_dirs = {
        (argv[7], argv[8])
        for step in plan["apply"]
        if (argv := step.get("argv")) and argv[:7] == [
            "/usr/bin/install", "-d", "-o", "root", "-g", "wheel", "-m"
        ]
    }
    assert required_layout <= install_dirs
    assert plan["apply"][-1]["argv"] == [
        "/bin/launchctl", "bootstrap", "system", BROKER_PLIST_PATH
    ]
    verify_argv = [step["argv"] for step in plan["verify"]]
    assert ["/bin/launchctl", "print", "system/com.nous.hermes-loop-a.worker"] in verify_argv
    assert ["/usr/bin/shasum", "-a", "256", WORKER_PLIST_PATH] in verify_argv
    assert plan["rollback"][0]["argv"] == [
        "/bin/launchctl", "bootout", f"system/{'com.nous.hermes-loop-a.root-broker'}"
    ]
    rollback_argv = [step["argv"] for step in plan["rollback"] if "argv" in step]
    version = plan["runtime_manifest_digest"]
    assert ["/bin/rm", "-rf", f"{ROOT}/runtime/versions/{version}"] in rollback_argv
    assert rollback_argv[-3] == ["/bin/rmdir", ROOT]
    assert ["/bin/test", "!", "-e", WORKER_PLIST_PATH] in rollback_argv
    assert plan["rollback"][-1]["gate"] == "rollback-receipt-readback"
    assert all(isinstance(step["argv"], list) for phase in ("apply", "verify", "rollback")
               for step in plan[phase] if "argv" in step)


def test_predecessor_plists_are_snapshot_bound_for_exact_rollback(tmp_path):
    old_worker = b"old worker plist\n"
    old_broker = b"old broker plist\n"
    bundle = compose(
        tmp_path,
        prior_worker_plist_bytes=old_worker,
        prior_root_broker_plist_bytes=old_broker,
        prior_active_version="b" * 64,
    )
    assert bundle.preimage_receipt["prior_active_version"] == "b" * 64
    assert bundle.preimage_receipt["worker_plist_sha256"] == hashlib.sha256(old_worker).hexdigest()
    with tarfile.open(fileobj=io.BytesIO(bundle.artifact_bytes), mode="r:") as archive:
        assert archive.extractfile("preimage/worker.plist").read() == old_worker
        assert archive.extractfile("preimage/root-broker.plist").read() == old_broker
    rollback_argv = [item.get("argv") for item in bundle.plan["rollback"]]
    assert ["/usr/bin/install", "-o", "root", "-g", "wheel", "-m", "0444",
            f"{BUNDLE_PATH}.expanded/preimage/worker.plist", WORKER_PLIST_PATH] in rollback_argv


@pytest.mark.parametrize("field", ["archive", "manifest", "inventory"])
def test_composer_fails_closed_on_any_explicit_digest_drift(tmp_path, field):
    archive, manifest, inventory, worker, broker = runtime_inputs(tmp_path)
    kwargs = {}
    if field == "archive":
        kwargs["expected_runtime_archive_sha256"] = "0" * 64
    elif field == "manifest":
        kwargs["expected_runtime_manifest_digest"] = "0" * 64
    else:
        kwargs["expected_runtime_inventory_digest"] = "0" * 64
    with pytest.raises(ValueError, match="digest"):
        compose(tmp_path / "nested", **kwargs)


def test_composer_rejects_archive_payload_that_disagrees_with_inventory_even_when_archive_digest_is_authorized(tmp_path):
    archive, _, _, _, _ = runtime_inputs(tmp_path / "source")
    corrupt = tmp_path / "corrupt.tar"
    changed = archive.read_bytes().replace(b"python\n", b"broken\n", 1)
    assert changed != archive.read_bytes()
    corrupt.write_bytes(changed)
    with pytest.raises(ValueError, match="content"):
        compose(
            tmp_path / "candidate",
            runtime_archive=corrupt,
            expected_runtime_archive_sha256=hashlib.sha256(changed).hexdigest(),
        )


def test_composer_rejects_nonproduction_root_nonexact_plist_and_partial_preimage(tmp_path):
    with pytest.raises(ValueError, match="target root"):
        compose(tmp_path / "root", target_root="/tmp/hermes-loop-a")
    with pytest.raises(ValueError, match="worker plist"):
        compose(tmp_path / "plist", worker_plist_bytes=plistlib.dumps({"Label": "wrong"}))
    with pytest.raises(ValueError, match="preimage"):
        compose(tmp_path / "prior", prior_worker_plist_bytes=b"old", prior_root_broker_plist_bytes=None,
                prior_active_version="b" * 64)


def test_composer_rejects_symlinked_or_multiply_linked_runtime_archive(tmp_path):
    archive, _manifest, _inventory, _worker, _broker = runtime_inputs(tmp_path / "source")
    alias = tmp_path / "alias.tar"
    alias.symlink_to(archive)
    with pytest.raises(ValueError, match="regular no-follow"):
        compose(tmp_path / "symlink", runtime_archive=alias)

    hardlink = tmp_path / "hardlink.tar"
    os.link(archive, hardlink)
    with pytest.raises(ValueError, match="single-link"):
        compose(tmp_path / "hardlink", runtime_archive=hardlink)


def test_loader_derives_exact_deployment_inputs_from_one_verified_runtime_archive(tmp_path):
    from loop_a_protected.darwin_installer import load_darwin_runtime_archive_inputs

    archive, manifest, inventory, worker, broker = runtime_inputs(tmp_path / "source")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    loaded = load_darwin_runtime_archive_inputs(archive, digest)
    assert loaded.archive_path == archive
    assert loaded.archive_sha256 == digest
    assert loaded.manifest == manifest
    assert loaded.inventory == inventory
    assert loaded.manifest_bytes == canonical_bytes(manifest)
    assert loaded.inventory_bytes == canonical_bytes(inventory)
    assert loaded.worker_plist_bytes == worker
    assert loaded.root_broker_plist_bytes == broker


def test_loader_rejects_runtime_archive_digest_mismatch(tmp_path):
    from loop_a_protected.darwin_installer import load_darwin_runtime_archive_inputs

    archive, _manifest, _inventory, _worker, _broker = runtime_inputs(tmp_path / "source")
    with pytest.raises(ValueError, match="digest differs"):
        load_darwin_runtime_archive_inputs(archive, "f" * 64)


def test_module_is_pure_planning_without_process_or_host_mutation_calls():
    import loop_a_protected.darwin_installer as module

    source = inspect.getsource(module)
    assert "subprocess" not in source
    assert "os.system" not in source
    assert "os.chown" not in source
    assert "os.chmod" not in source
    assert "os.mkdir" not in source
    assert "os.replace" not in source
