from __future__ import annotations

import argparse
import os
from pathlib import Path

from loop_a_protected.canonical import canonical_bytes
from loop_a_protected.darwin_account import ACCOUNT_NAME, GROUP_NAME
from loop_a_protected.darwin_installer import (
    PRODUCTION_ROOT,
    compose_darwin_deployment_bundle,
    load_darwin_runtime_archive_inputs,
)


def _write_new(path: Path, data: bytes, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
    fd = os.open(path, flags, mode)
    try:
        view = memoryview(data)
        while view:
            written = os.write(fd, view)
            if written <= 0:
                raise OSError("short deployment artifact write")
            view = view[written:]
        os.fsync(fd)
    except BaseException:
        os.close(fd)
        path.unlink(missing_ok=True)
        raise
    else:
        os.close(fd)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compose one immutable, fresh-install Darwin Loop A deployment bundle"
    )
    parser.add_argument("--runtime", required=True, type=Path)
    parser.add_argument("--runtime-sha256", required=True)
    parser.add_argument("--authorized-uid", required=True, type=int)
    parser.add_argument("--authorized-gid", required=True, type=int)
    parser.add_argument("--bundle-path", required=True)
    parser.add_argument("--target-root", default=PRODUCTION_ROOT)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument(
        "--fresh-install",
        required=True,
        action="store_true",
        help="Assert that no prior account, group, plist, or active runtime preimage will be replaced",
    )
    args = parser.parse_args()

    inputs = load_darwin_runtime_archive_inputs(
        args.runtime.resolve(), args.runtime_sha256
    )
    bundle = compose_darwin_deployment_bundle(
        runtime_archive=inputs.archive_path,
        expected_runtime_archive_sha256=inputs.archive_sha256,
        runtime_manifest_bytes=inputs.manifest_bytes,
        expected_runtime_manifest_digest=inputs.manifest["version_digest"],
        runtime_inventory_bytes=inputs.inventory_bytes,
        expected_runtime_inventory_digest=inputs.inventory["inventory_digest"],
        authorized_uid=args.authorized_uid,
        authorized_gid=args.authorized_gid,
        worker_plist_bytes=inputs.worker_plist_bytes,
        root_broker_plist_bytes=inputs.root_broker_plist_bytes,
        target_root=args.target_root,
        bundle_path=args.bundle_path,
        prior_worker_plist_bytes=None,
        prior_root_broker_plist_bytes=None,
        prior_active_version=None,
    )
    report = {
        "schema": 1,
        "authority": "local-reversible-candidate-only",
        "fresh_install_preimage_required": True,
        "account_name": ACCOUNT_NAME,
        "group_name": GROUP_NAME,
        "authorized_uid": args.authorized_uid,
        "authorized_gid": args.authorized_gid,
        "target_root": args.target_root,
        "runtime_archive_sha256": inputs.archive_sha256,
        "runtime_manifest_digest": inputs.manifest["version_digest"],
        "runtime_inventory_digest": inputs.inventory["inventory_digest"],
        "deployment_bundle_path": args.bundle_path,
        "deployment_artifact_path": str(args.output.resolve()),
        "deployment_artifact_byte_count": len(bundle.artifact_bytes),
        "deployment_artifact_sha256": bundle.artifact_sha256,
        "plan_digest": bundle.plan["plan_digest"],
        "preimage_receipt_digest": bundle.preimage_receipt["receipt_digest"],
        "rollback_receipt_template_digest": bundle.rollback_receipt_template["receipt_digest"],
    }
    _write_new(args.output.resolve(), bundle.artifact_bytes)
    try:
        _write_new(args.report.resolve(), canonical_bytes(report))
    except BaseException:
        args.output.resolve().unlink(missing_ok=True)
        raise
    print(canonical_bytes(report).decode("utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
