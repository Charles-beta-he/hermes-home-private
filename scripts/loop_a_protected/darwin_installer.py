from __future__ import annotations

import hashlib
import io
import os
import plistlib
import re
import stat
import tarfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from .canonical import canonical_bytes, parse_canonical_bytes, with_self_digest
from .darwin_account import ACCOUNT_NAME, GROUP_NAME, build_account_provisioning_plan
from .darwin_launchd import (
    build_root_broker_plist,
    build_worker_plist,
    serialize_root_broker_plist,
    serialize_worker_plist,
)
from .manifests import validate_manifest_inventory_pair
from .validation import ProtocolValidationError, validate_digest


PRODUCTION_ROOT = "/private/var/db/hermes-loop-a"
DEPLOYMENT_STAGING_ROOT = "/private/var/tmp/hermes-loop-a-deployment"
WORKER_LABEL = "com.nous.hermes-loop-a.worker"
BROKER_LABEL = "com.nous.hermes-loop-a.root-broker"
WORKER_PLIST_PATH = f"/Library/LaunchDaemons/{WORKER_LABEL}.plist"
BROKER_PLIST_PATH = f"/Library/LaunchDaemons/{BROKER_LABEL}.plist"


class DarwinInstallerError(ValueError):
    """Deployment inputs cannot produce an exact fail-closed Darwin plan."""


@dataclass(frozen=True)
class DarwinRuntimeArchiveInputs:
    archive_path: Path
    archive_sha256: str
    manifest: Mapping[str, Any]
    manifest_bytes: bytes
    inventory: Mapping[str, Any]
    inventory_bytes: bytes
    worker_plist_bytes: bytes
    root_broker_plist_bytes: bytes


@dataclass(frozen=True)
class DarwinDeploymentBundle:
    artifact_bytes: bytes
    artifact_sha256: str
    plan: Mapping[str, Any]
    plan_bytes: bytes
    preimage_receipt: Mapping[str, Any]
    preimage_receipt_bytes: bytes
    rollback_receipt_template: Mapping[str, Any]
    rollback_receipt_template_bytes: bytes


def _digest(value: Any, label: str) -> str:
    try:
        return validate_digest(value)
    except ProtocolValidationError as exc:
        raise DarwinInstallerError(f"{label} digest is invalid") from exc


def _regular_bytes(path: Path, label: str) -> bytes:
    if not path.is_absolute():
        raise DarwinInstallerError(f"{label} must be one absolute regular no-follow file")
    fd = -1
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise DarwinInstallerError(
                f"{label} must be one absolute regular no-follow file"
            )
        if before.st_nlink != 1:
            raise DarwinInstallerError(f"{label} must be one single-link file")
        chunks = bytearray()
        offset = 0
        while offset < before.st_size:
            chunk = os.pread(fd, min(131072, before.st_size - offset), offset)
            if not chunk:
                break
            chunks.extend(chunk)
            offset += len(chunk)
        after = os.fstat(fd)
        stable = lambda value: (
            value.st_dev,
            value.st_ino,
            value.st_mode,
            value.st_uid,
            value.st_gid,
            value.st_nlink,
            value.st_size,
            value.st_mtime_ns,
            value.st_ctime_ns,
            getattr(value, "st_flags", 0),
        )
        if stable(before) != stable(after) or len(chunks) != before.st_size:
            raise DarwinInstallerError(f"{label} changed during held-FD read")
        return bytes(chunks)
    except DarwinInstallerError:
        raise
    except OSError as exc:
        raise DarwinInstallerError(
            f"{label} must be one absolute regular no-follow file"
        ) from exc
    finally:
        if fd >= 0:
            os.close(fd)


def _parse_runtime_metadata(data: bytes, expected: str, label: str) -> dict[str, Any]:
    try:
        value = parse_canonical_bytes(data)
    except Exception as exc:
        raise DarwinInstallerError(f"runtime {label} bytes are not canonical") from exc
    if not isinstance(value, dict):
        raise DarwinInstallerError(f"runtime {label} is not an object")
    field = "version_digest" if label == "manifest" else "inventory_digest"
    if value.get(field) != _digest(expected, f"runtime {label}"):
        raise DarwinInstallerError(f"runtime {label} digest differs")
    return value


def _verify_runtime_archive(
    data: bytes, expected_sha256: str, manifest: Mapping[str, Any], inventory: Mapping[str, Any]
) -> None:
    if hashlib.sha256(data).hexdigest() != _digest(expected_sha256, "runtime archive"):
        raise DarwinInstallerError("runtime archive digest differs")
    version = manifest["version_digest"]
    expected: dict[str, tuple[str, int, int | None, str | None, bytes | None]] = {}
    prefix = f"runtime/versions/{version}"
    for entry in inventory["entries"]:
        name = f"{prefix}/{entry['relative_path']}"
        expected[name] = (
            entry["type"], entry["mode"], entry["size"], entry["sha256"], None
        )
    manifest_data = canonical_bytes(dict(manifest))
    inventory_data = canonical_bytes(dict(inventory))
    expected[f"metadata/runtime-{version}.manifest.json"] = (
        "file", 0o444, len(manifest_data), hashlib.sha256(manifest_data).hexdigest(), manifest_data
    )
    expected[f"metadata/runtime-{version}.inventory.json"] = (
        "file", 0o444, len(inventory_data), hashlib.sha256(inventory_data).hexdigest(), inventory_data
    )
    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:") as archive:
            members = archive.getmembers()
            names = [item.name.rstrip("/") if item.isdir() else item.name for item in members]
            if len(names) != len(set(names)) or set(names) != set(expected):
                raise DarwinInstallerError("runtime archive member inventory differs")
            for member, canonical_name in zip(members, names):
                kind, mode, size, sha256, exact = expected[canonical_name]
                if (
                    member.uid != 0 or member.gid != 0 or member.uname != "root"
                    or member.gname != "wheel" or member.mtime != 0 or member.mode != mode
                    or (kind == "file") != member.isfile()
                    or (kind == "directory") != member.isdir()
                    or member.issym() or member.islnk()
                ):
                    raise DarwinInstallerError("runtime archive member metadata differs")
                if kind == "file":
                    stream = archive.extractfile(member)
                    observed = b"" if stream is None else stream.read(member.size + 1)
                    if (
                        size is None or sha256 is None or member.size != size
                        or len(observed) != size
                        or hashlib.sha256(observed).hexdigest() != sha256
                        or (exact is not None and observed != exact)
                    ):
                        raise DarwinInstallerError("runtime archive file content differs")
    except DarwinInstallerError:
        raise
    except (tarfile.TarError, OSError) as exc:
        raise DarwinInstallerError("runtime archive is invalid") from exc


def load_darwin_runtime_archive_inputs(
    runtime_archive: str | Path, expected_runtime_archive_sha256: str
) -> DarwinRuntimeArchiveInputs:
    """Load and verify every deployment input from one immutable runtime archive."""
    path = Path(runtime_archive)
    archive_bytes = _regular_bytes(path, "runtime archive")
    archive_sha256 = _digest(expected_runtime_archive_sha256, "runtime archive")
    if hashlib.sha256(archive_bytes).hexdigest() != archive_sha256:
        raise DarwinInstallerError("runtime archive digest differs")
    try:
        with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:") as archive:
            members = archive.getmembers()
            names = [item.name.rstrip("/") if item.isdir() else item.name for item in members]
            manifest_rows = [
                (item, match.group(1))
                for item, name in zip(members, names)
                if (match := re.fullmatch(r"metadata/runtime-([0-9a-f]{64})\.manifest\.json", name))
            ]
            inventory_rows = [
                (item, match.group(1))
                for item, name in zip(members, names)
                if (match := re.fullmatch(r"metadata/runtime-([0-9a-f]{64})\.inventory\.json", name))
            ]
            if (
                len(manifest_rows) != 1
                or len(inventory_rows) != 1
                or manifest_rows[0][1] != inventory_rows[0][1]
            ):
                raise DarwinInstallerError("runtime archive metadata identity is not exact")

            def read_metadata(member: tarfile.TarInfo, label: str) -> bytes:
                if not member.isfile() or member.size < 2 or member.size > 8_388_608:
                    raise DarwinInstallerError(f"runtime archive {label} member is invalid")
                stream = archive.extractfile(member)
                data = b"" if stream is None else stream.read(member.size + 1)
                if len(data) != member.size:
                    raise DarwinInstallerError(f"runtime archive {label} member is invalid")
                return data

            manifest_bytes = read_metadata(manifest_rows[0][0], "manifest")
            inventory_bytes = read_metadata(inventory_rows[0][0], "inventory")
    except DarwinInstallerError:
        raise
    except (tarfile.TarError, OSError) as exc:
        raise DarwinInstallerError("runtime archive is invalid") from exc

    version = manifest_rows[0][1]
    manifest = _parse_runtime_metadata(manifest_bytes, version, "manifest")
    try:
        inventory_value = parse_canonical_bytes(inventory_bytes)
    except Exception as exc:
        raise DarwinInstallerError("runtime inventory bytes are not canonical") from exc
    if not isinstance(inventory_value, dict):
        raise DarwinInstallerError("runtime inventory is not an object")
    inventory_digest = _digest(inventory_value.get("inventory_digest"), "runtime inventory")
    inventory = _parse_runtime_metadata(inventory_bytes, inventory_digest, "inventory")
    try:
        validate_manifest_inventory_pair(manifest, inventory)
    except Exception as exc:
        raise DarwinInstallerError("runtime manifest/inventory pair differs") from exc
    _verify_runtime_archive(archive_bytes, archive_sha256, manifest, inventory)

    prefix = f"{PRODUCTION_ROOT}/runtime/versions/{version}"
    worker_plist = serialize_worker_plist(
        build_worker_plist(
            interpreter_path=f"{prefix}/bin/python3",
            entrypoint_path=f"{prefix}/libexec/worker-bootstrap.py",
            worker_user=ACCOUNT_NAME,
            worker_group=GROUP_NAME,
        )
    )
    root_broker_plist = serialize_root_broker_plist(
        build_root_broker_plist(
            interpreter_path=f"{prefix}/bin/python3",
            entrypoint_path=f"{prefix}/libexec/root-broker-entrypoint.py",
        )
    )
    return DarwinRuntimeArchiveInputs(
        archive_path=path,
        archive_sha256=archive_sha256,
        manifest=manifest,
        manifest_bytes=manifest_bytes,
        inventory=inventory,
        inventory_bytes=inventory_bytes,
        worker_plist_bytes=worker_plist,
        root_broker_plist_bytes=root_broker_plist,
    )


def _exact_plist(data: bytes, *, root: bool, version: str) -> bytes:
    label = "root broker plist" if root else "worker plist"
    try:
        value = plistlib.loads(data)
        arguments = value["ProgramArguments"]
        interpreter = arguments[0]
        entrypoint = value["StandardInPath"]
        expected_prefix = f"{PRODUCTION_ROOT}/runtime/versions/{version}/"
        if not interpreter.startswith(expected_prefix) or not entrypoint.startswith(expected_prefix):
            raise DarwinInstallerError(f"{label} does not bind the runtime digest")
        if root:
            rebuilt = build_root_broker_plist(
                interpreter_path=interpreter, entrypoint_path=entrypoint
            )
            return serialize_root_broker_plist(rebuilt) if value == rebuilt else _raise_plist(label)
        rebuilt = build_worker_plist(
            interpreter_path=interpreter,
            entrypoint_path=entrypoint,
            worker_user=ACCOUNT_NAME,
            worker_group=GROUP_NAME,
        )
        return serialize_worker_plist(rebuilt) if value == rebuilt else _raise_plist(label)
    except DarwinInstallerError:
        raise
    except Exception as exc:
        raise DarwinInstallerError(f"{label} is not exact") from exc


def _raise_plist(label: str) -> bytes:
    raise DarwinInstallerError(f"{label} is not exact")


def _step(step_id: str, argv: list[str], *, readback: str | None = None) -> dict[str, Any]:
    value: dict[str, Any] = {"id": step_id, "argv": argv}
    if readback is not None:
        value["required_readback"] = readback
    return value


def _receipt(preimage: dict[str, Any], field: str) -> tuple[dict[str, Any], bytes]:
    finalized = with_self_digest(preimage, field)
    return finalized, canonical_bytes(finalized)


def _tar_bytes(members: Mapping[str, tuple[bytes, int]]) -> bytes:
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w", format=tarfile.GNU_FORMAT) as archive:
        for name in sorted(members, key=lambda value: value.encode("utf-8")):
            data, mode = members[name]
            info = tarfile.TarInfo(name)
            info.uid = info.gid = info.mtime = 0
            info.uname, info.gname = "root", "wheel"
            info.mode, info.type, info.size = mode, tarfile.REGTYPE, len(data)
            archive.addfile(info, io.BytesIO(data))
    return output.getvalue()


def compose_darwin_deployment_bundle(
    *,
    runtime_archive: str | Path,
    expected_runtime_archive_sha256: str,
    runtime_manifest_bytes: bytes,
    expected_runtime_manifest_digest: str,
    runtime_inventory_bytes: bytes,
    expected_runtime_inventory_digest: str,
    authorized_uid: int,
    authorized_gid: int,
    worker_plist_bytes: bytes,
    root_broker_plist_bytes: bytes,
    target_root: str,
    bundle_path: str,
    prior_worker_plist_bytes: bytes | None,
    prior_root_broker_plist_bytes: bytes | None,
    prior_active_version: str | None,
) -> DarwinDeploymentBundle:
    """Validate all deployment inputs and compose bytes plus inert exact argv plans.

    This function performs no process execution and no host mutation. The returned
    boundary remains in ``human-execution-required`` state until an operator has
    captured the preimage and executed each argv with its required readback.
    """
    if target_root != PRODUCTION_ROOT:
        raise DarwinInstallerError("target root is not the exact production root")
    bundle = PurePosixPath(bundle_path)
    if (
        not bundle.is_absolute()
        or str(bundle).startswith(DEPLOYMENT_STAGING_ROOT + "/") is False
        or bundle.parent != PurePosixPath(DEPLOYMENT_STAGING_ROOT)
        or any(component in {"", ".", ".."} for component in bundle.parts[1:])
    ):
        raise DarwinInstallerError(
            "bundle path must be exact, absolute, and directly below the deployment staging root"
        )
    if bundle.name in {"", ".", ".."}:
        raise DarwinInstallerError("bundle path is invalid")

    archive_bytes = _regular_bytes(Path(runtime_archive), "runtime archive")
    manifest = _parse_runtime_metadata(
        runtime_manifest_bytes, expected_runtime_manifest_digest, "manifest"
    )
    inventory = _parse_runtime_metadata(
        runtime_inventory_bytes, expected_runtime_inventory_digest, "inventory"
    )
    try:
        validate_manifest_inventory_pair(manifest, inventory)
    except Exception as exc:
        raise DarwinInstallerError("runtime manifest/inventory pair differs") from exc
    version = manifest["version_digest"]
    _verify_runtime_archive(
        archive_bytes, expected_runtime_archive_sha256, manifest, inventory
    )
    worker_plist = _exact_plist(worker_plist_bytes, root=False, version=version)
    broker_plist = _exact_plist(root_broker_plist_bytes, root=True, version=version)
    runtime_files = {
        entry["relative_path"] for entry in inventory["entries"] if entry["type"] == "file"
    }
    for label, plist_bytes in (("worker plist", worker_plist), ("root broker plist", broker_plist)):
        entrypoint = plistlib.loads(plist_bytes)["StandardInPath"]
        relative = entrypoint.removeprefix(f"{target_root}/runtime/versions/{version}/")
        if relative not in runtime_files:
            raise DarwinInstallerError(f"{label} entrypoint is absent from runtime inventory")
    account_plan = build_account_provisioning_plan(
        authorized_uid=authorized_uid, authorized_gid=authorized_gid
    )

    prior_values = (
        prior_worker_plist_bytes,
        prior_root_broker_plist_bytes,
        prior_active_version,
    )
    if any(value is not None for value in prior_values) != all(value is not None for value in prior_values):
        raise DarwinInstallerError("preimage must be wholly absent or wholly present")
    if prior_active_version is not None:
        _digest(prior_active_version, "preimage active version")
        if prior_active_version == version:
            raise DarwinInstallerError("preimage active version must differ from new runtime version")
    preimage, preimage_bytes = _receipt(
        {
            "schema": 1,
            "target_root": target_root,
            "worker_plist_path": WORKER_PLIST_PATH,
            "worker_plist_sha256": None if prior_worker_plist_bytes is None else hashlib.sha256(prior_worker_plist_bytes).hexdigest(),
            "root_broker_plist_path": BROKER_PLIST_PATH,
            "root_broker_plist_sha256": None if prior_root_broker_plist_bytes is None else hashlib.sha256(prior_root_broker_plist_bytes).hexdigest(),
            "prior_active_version": prior_active_version,
            "new_runtime_version": version,
            "receipt_digest": None,
        },
        "receipt_digest",
    )
    rollback_receipt, rollback_receipt_bytes = _receipt(
        {
            "schema": 1,
            "target_root": target_root,
            "preimage_receipt_sha256": hashlib.sha256(preimage_bytes).hexdigest(),
            "expected_restored_version": prior_active_version,
            "status": "pending-human-execution",
            "post_action_readback_sha256": None,
            "receipt_digest": None,
        },
        "receipt_digest",
    )

    expanded = f"{bundle_path}.expanded"
    if prior_active_version is None:
        preimage_readback = [
            _step("P01", ["/bin/test", "!", "-e", WORKER_PLIST_PATH], readback="absent"),
            _step("P02", ["/bin/test", "!", "-e", BROKER_PLIST_PATH], readback="absent"),
        ]
    else:
        assert prior_worker_plist_bytes is not None and prior_root_broker_plist_bytes is not None
        preimage_readback = [
            _step("P01", ["/usr/bin/shasum", "-a", "256", WORKER_PLIST_PATH],
                  readback=hashlib.sha256(prior_worker_plist_bytes).hexdigest()),
            _step("P02", ["/usr/bin/shasum", "-a", "256", BROKER_PLIST_PATH],
                  readback=hashlib.sha256(prior_root_broker_plist_bytes).hexdigest()),
        ]
    preimage_readback.append(
        _step("P03", ["/bin/test", "!", "-e", expanded], readback="absent")
    )
    layout = (
        ("0755", target_root),
        ("0755", f"{target_root}/active-skills"),
        ("0755", f"{target_root}/authorizations"),
        ("0750", f"{target_root}/control"),
        ("0700", f"{target_root}/installer-transactions"),
        ("0755", f"{target_root}/locks"),
        ("0755", f"{target_root}/metadata"),
        ("0755", f"{target_root}/policy"),
        ("0755", f"{target_root}/runtime"),
        ("0755", f"{target_root}/runtime/versions"),
        ("0700", f"{target_root}/service"),
        ("0700", f"{target_root}/service-transactions"),
    )
    layout_steps = [
        _step(
            f"A{index:02d}",
            [
                "/usr/bin/install", "-d", "-o", "root", "-g", "wheel",
                "-m", mode, path,
            ],
        )
        for index, (mode, path) in enumerate(layout, 20)
    ]
    apply = [
        {"id": "A00", "gate": "preimage-receipt-readback",
         "expected_sha256": hashlib.sha256(preimage_bytes).hexdigest()},
        _step(
            "A01",
            [
                "/usr/bin/install", "-d", "-o", "root", "-g", "wheel",
                "-m", "0700", expanded,
            ],
        ),
        _step("A02", ["/usr/bin/tar", "-xpf", bundle_path, "-C", expanded]),
        _step("A03", ["/bin/test", "!", "-e", f"{target_root}/runtime/versions/{version}"],
              readback="absent-before-install"),
        *[_step(f"A{index:02d}", list(argv)) for index, argv in enumerate(account_plan, 10)],
        *layout_steps,
        _step("A40", ["/usr/bin/tar", "-xpf", f"{expanded}/payload/runtime.tar", "-C", target_root]),
        _step("A41", ["/usr/bin/install", "-o", "root", "-g", "wheel", "-m", "0444",
                       f"{expanded}/payload/worker.plist", WORKER_PLIST_PATH]),
        _step("A42", ["/usr/bin/install", "-o", "root", "-g", "wheel", "-m", "0444",
                       f"{expanded}/payload/root-broker.plist", BROKER_PLIST_PATH]),
        _step("A43", ["/bin/launchctl", "bootstrap", "system", WORKER_PLIST_PATH]),
        _step("A44", ["/bin/launchctl", "bootstrap", "system", BROKER_PLIST_PATH]),
    ]
    verify = [
        _step("V01", ["/usr/bin/shasum", "-a", "256", WORKER_PLIST_PATH], readback=hashlib.sha256(worker_plist).hexdigest()),
        _step("V02", ["/usr/bin/shasum", "-a", "256", BROKER_PLIST_PATH], readback=hashlib.sha256(broker_plist).hexdigest()),
        _step("V03", ["/usr/bin/shasum", "-a", "256", f"{target_root}/metadata/runtime-{version}.manifest.json"], readback=hashlib.sha256(runtime_manifest_bytes).hexdigest()),
        _step("V04", ["/bin/launchctl", "print", f"system/{WORKER_LABEL}"], readback=WORKER_LABEL),
        _step("V05", ["/bin/launchctl", "print", f"system/{BROKER_LABEL}"], readback=BROKER_LABEL),
        _step("V06", ["/usr/bin/dscl", ".", "-read", f"/Users/{ACCOUNT_NAME}"], readback=f"uid={authorized_uid};gid={authorized_gid}"),
    ]
    rollback = [
        _step("R01", ["/bin/launchctl", "bootout", f"system/{BROKER_LABEL}"]),
        _step("R02", ["/bin/launchctl", "bootout", f"system/{WORKER_LABEL}"]),
    ]
    if prior_active_version is None:
        rollback.extend([
            _step("R03", ["/bin/rm", "-f", BROKER_PLIST_PATH]),
            _step("R04", ["/bin/rm", "-f", WORKER_PLIST_PATH]),
            _step("R05", ["/usr/bin/dscl", ".", "-delete", f"/Users/{ACCOUNT_NAME}"]),
            _step("R06", ["/usr/bin/dscl", ".", "-delete", f"/Groups/{GROUP_NAME}"]),
        ])
    else:
        rollback.extend([
            _step("R03", ["/usr/bin/install", "-o", "root", "-g", "wheel", "-m", "0444",
                           f"{expanded}/preimage/root-broker.plist", BROKER_PLIST_PATH]),
            _step("R04", ["/usr/bin/install", "-o", "root", "-g", "wheel", "-m", "0444",
                           f"{expanded}/preimage/worker.plist", WORKER_PLIST_PATH]),
            _step("R05", ["/bin/launchctl", "bootstrap", "system", WORKER_PLIST_PATH]),
            _step("R06", ["/bin/launchctl", "bootstrap", "system", BROKER_PLIST_PATH]),
        ])
    rollback.extend([
        _step("R80", ["/bin/rm", "-rf", f"{target_root}/runtime/versions/{version}"]),
        _step("R81", ["/bin/rm", "-f", f"{target_root}/metadata/runtime-{version}.manifest.json",
                       f"{target_root}/metadata/runtime-{version}.inventory.json"]),
    ])
    if prior_active_version is None:
        for index, path in enumerate(
            (
                f"{target_root}/runtime/versions",
                f"{target_root}/runtime",
                f"{target_root}/metadata",
                f"{target_root}/service-transactions",
                f"{target_root}/service",
                f"{target_root}/policy",
                f"{target_root}/locks",
                f"{target_root}/installer-transactions",
                f"{target_root}/control",
                f"{target_root}/authorizations",
                f"{target_root}/active-skills",
                target_root,
            ),
            82,
        ):
            rollback.append(_step(f"R{index:02d}", ["/bin/rmdir", path]))
        rollback.extend([
            _step("R94", ["/bin/test", "!", "-e", WORKER_PLIST_PATH], readback="absent"),
            _step("R95", ["/bin/test", "!", "-e", BROKER_PLIST_PATH], readback="absent"),
        ])
    else:
        assert prior_worker_plist_bytes is not None and prior_root_broker_plist_bytes is not None
        rollback.extend([
            _step("R90", ["/usr/bin/shasum", "-a", "256", WORKER_PLIST_PATH],
                  readback=hashlib.sha256(prior_worker_plist_bytes).hexdigest()),
            _step("R91", ["/usr/bin/shasum", "-a", "256", BROKER_PLIST_PATH],
                  readback=hashlib.sha256(prior_root_broker_plist_bytes).hexdigest()),
        ])
    rollback.append({"id": "R99", "gate": "rollback-receipt-readback",
                     "expected_template_sha256": hashlib.sha256(rollback_receipt_bytes).hexdigest()})

    plan, plan_bytes = _receipt(
        {
            "schema": 1,
            "authority": "human-execution-required",
            "host_mutation_performed": False,
            "target_root": target_root,
            "bundle_path": bundle_path,
            "expanded_bundle_root": expanded,
            "runtime_archive_sha256": hashlib.sha256(archive_bytes).hexdigest(),
            "runtime_manifest_digest": version,
            "runtime_inventory_digest": inventory["inventory_digest"],
            "account": {"name": ACCOUNT_NAME, "group": GROUP_NAME, "uid": authorized_uid, "gid": authorized_gid},
            "worker_plist_sha256": hashlib.sha256(worker_plist).hexdigest(),
            "root_broker_plist_sha256": hashlib.sha256(broker_plist).hexdigest(),
            "preimage_receipt_sha256": hashlib.sha256(preimage_bytes).hexdigest(),
            "rollback_receipt_template_sha256": hashlib.sha256(rollback_receipt_bytes).hexdigest(),
            "preimage_readback": preimage_readback,
            "apply": apply,
            "verify": verify,
            "rollback": rollback,
            "plan_digest": None,
        },
        "plan_digest",
    )
    human = (
        b"HERMES LOOP A DARWIN DEPLOYMENT BOUNDARY\n"
        b"STATUS: HUMAN EXECUTION REQUIRED; NO HOST MUTATION HAS OCCURRED.\n"
        b"1. Verify this bundle SHA-256 against the separately delivered digest.\n"
        b"2. Expand it at the exact expanded_bundle_root recorded in deployment/plan.json.\n"
        b"3. Execute each apply argv directly, in order; do not interpolate or combine commands.\n"
        b"4. Require every verify readback before declaring smoke readiness.\n"
        b"5. On any failure, execute rollback argv in order and finalize the rollback receipt.\n"
    )
    members: dict[str, tuple[bytes, int]] = {
        "HUMAN-APPLY-VERIFY-ROLLBACK.txt": (human, 0o444),
        "deployment/plan.json": (plan_bytes, 0o444),
        "deployment/preimage-receipt.json": (preimage_bytes, 0o444),
        "deployment/rollback-receipt-template.json": (rollback_receipt_bytes, 0o444),
        "payload/root-broker.plist": (broker_plist, 0o444),
        "payload/runtime-inventory.json": (runtime_inventory_bytes, 0o444),
        "payload/runtime-manifest.json": (runtime_manifest_bytes, 0o444),
        "payload/runtime.tar": (archive_bytes, 0o444),
        "payload/worker.plist": (worker_plist, 0o444),
    }
    if prior_worker_plist_bytes is not None and prior_root_broker_plist_bytes is not None:
        members["preimage/worker.plist"] = (prior_worker_plist_bytes, 0o444)
        members["preimage/root-broker.plist"] = (prior_root_broker_plist_bytes, 0o444)
    artifact = _tar_bytes(members)
    return DarwinDeploymentBundle(
        artifact_bytes=artifact,
        artifact_sha256=hashlib.sha256(artifact).hexdigest(),
        plan=plan,
        plan_bytes=plan_bytes,
        preimage_receipt=preimage,
        preimage_receipt_bytes=preimage_bytes,
        rollback_receipt_template=rollback_receipt,
        rollback_receipt_template_bytes=rollback_receipt_bytes,
    )
