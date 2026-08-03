from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

from loop_a_protected.canonical import canonical_bytes, parse_canonical_bytes, with_self_digest
from loop_a_protected.fd_gateway import CleanMetadataAdapter
from loop_a_protected.publication import PublicationError, swap_reserved_regular_file
from loop_a_protected.root_gate import RootGateError, acquire_root_mutation_gate
from test_loop_a_protected_swap_support import (
    make_authorization,
    make_swap_evidence,
    provision_swap_journal,
)


class CleanMetadata(CleanMetadataAdapter):
    def xattr_bytes(self, fd: int) -> int:
        return 0

    def has_extended_acl(self, fd: int) -> bool:
        return False


class SchedulerProbe:
    def old_job_is_inhibited(self): return True
    def launchd_is_disabled_and_booted_out(self): return True
    def matching_service_processes(self): return ()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def provision(path: Path):
    uid, gid = os.getuid(), os.getgid()
    os.chmod(path, 0o755)
    for name, mode in (("locks", 0o755), ("service", 0o700), ("policy", 0o700)):
        (path / name).mkdir(mode=mode)
    (path / "locks" / "installer.lock").write_bytes(b"")
    (path / "service" / "lease.lock").write_bytes(b"")
    (path / "FENCED").write_bytes(b"")
    os.chmod(path / "locks" / "installer.lock", 0o640)
    os.chmod(path / "service" / "lease.lock", 0o600)
    os.chmod(path / "FENCED", 0o444)
    current = b'{"generation":1}\n'
    staged = b'{"generation":2}\n'
    (path / "policy" / "rollback-floor.json").write_bytes(current)
    (path / "policy" / ".rollback-floor.json.txn-123e4567-e89b-42d3-a456-426614174000.tmp").write_bytes(staged)
    os.chmod(path / "policy" / "rollback-floor.json", 0o400)
    os.chmod(path / "policy" / ".rollback-floor.json.txn-123e4567-e89b-42d3-a456-426614174000.tmp", 0o400)
    return uid, gid, current, staged


def opened(path: Path, *, with_journal=True):
    uid, gid, current, staged = provision(path)
    root_fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    policy_fd = os.open(path / "policy", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    root_identity = (os.fstat(root_fd).st_dev, os.fstat(root_fd).st_ino)
    policy_identity = (os.fstat(policy_fd).st_dev, os.fstat(policy_fd).st_ino)
    authorization = make_authorization("update-floor", "rollback-floor")
    if with_journal:
        staged_name = ".rollback-floor.json.txn-123e4567-e89b-42d3-a456-426614174000.tmp"
        evidence = make_swap_evidence(
            authorization=authorization, sequence=3, state="FLOOR_STAGED", role="rollback-floor",
            parent_status=os.fstat(policy_fd), current_name="rollback-floor.json",
            current_status=os.stat("rollback-floor.json", dir_fd=policy_fd, follow_symlinks=False),
            staged_name=staged_name,
            staged_status=os.stat(staged_name, dir_fd=policy_fd, follow_symlinks=False),
            current_digest=digest(current), staged_digest=digest(staged),
        )
        provision_swap_journal(path, authorization, "FLOOR_STAGED", "rollback-floor", evidence)
    gate = acquire_root_mutation_gate(
        root_fd, root_identity, uid, gid, uid, gid, SchedulerProbe(), CleanMetadata(), nonblocking=True,
    )
    return uid, gid, current, staged, root_fd, policy_fd, policy_identity, authorization, gate


def invoke(policy_fd, policy_identity, gate, authorization, uid, gid, current, staged, **changes):
    values = dict(
        parent_fd=policy_fd,
        expected_parent_identity=policy_identity,
        gate=gate,
        authorization=authorization,
        role="rollback-floor",
        current_name="rollback-floor.json",
        staged_name=".rollback-floor.json.txn-123e4567-e89b-42d3-a456-426614174000.tmp",
        expected_current_digest=digest(current),
        expected_staged_digest=digest(staged),
        required_journal_state="FLOOR_STAGED",
        uid=uid,
        gid=gid,
        mode=0o400,
        metadata=CleanMetadata(),
    )
    values.update(changes)
    return swap_reserved_regular_file(**values)


def test_reserved_floor_swap_requires_live_root_gate_and_preserves_old_at_staged_name(tmp_path):
    uid, gid, current, staged, root_fd, policy_fd, identity, authorization, gate_context = opened(tmp_path)
    try:
        with gate_context as gate:
            result = invoke(policy_fd, identity, gate, authorization, uid, gid, current, staged)
            assert result.role == "rollback-floor"
            assert (tmp_path / "policy" / "rollback-floor.json").read_bytes() == staged
            assert (tmp_path / "policy" / result.retained_name).read_bytes() == current
    finally:
        os.close(policy_fd)
        os.close(root_fd)


def test_reserved_swap_rejects_unbound_digest_without_mutation(tmp_path):
    uid, gid, current, staged, root_fd, policy_fd, identity, authorization, gate_context = opened(tmp_path)
    try:
        with gate_context as gate:
            with pytest.raises(PublicationError, match="digest"):
                invoke(policy_fd, identity, gate, authorization, uid, gid, current, staged,
                       expected_staged_digest="0" * 64)
            assert (tmp_path / "policy" / "rollback-floor.json").read_bytes() == current
            assert (tmp_path / "policy" / ".rollback-floor.json.txn-123e4567-e89b-42d3-a456-426614174000.tmp").read_bytes() == staged
    finally:
        os.close(policy_fd)
        os.close(root_fd)


def test_reserved_swap_rejects_missing_durable_evidence(tmp_path):
    root = tmp_path / "missing"
    root.mkdir()
    uid, gid, current, staged, root_fd, policy_fd, identity, authorization, gate_context = opened(
        root, with_journal=False,
    )
    try:
        with gate_context as gate:
            with pytest.raises(PublicationError, match="durable swap evidence"):
                invoke(policy_fd, identity, gate, authorization, uid, gid, current, staged)
        assert (root / "policy" / "rollback-floor.json").read_bytes() == current
    finally:
        os.close(policy_fd)
        os.close(root_fd)


@pytest.mark.parametrize("mutation", ["noncanonical", "bad-self-digest", "unbound-valid", "extra-child"])
def test_reserved_swap_rejects_malformed_unbound_or_ambiguous_evidence(tmp_path, mutation):
    root = tmp_path / mutation
    root.mkdir()
    uid, gid, current, staged, root_fd, policy_fd, identity, authorization, gate_context = opened(root)
    transaction = root / "installer-transactions" / authorization["authorization_payload"]["transaction_uuid"]
    evidence_path = transaction / "evidence" / "00000003-rollback-floor-swap.json"
    try:
        if mutation == "extra-child":
            (transaction / "unexpected").write_bytes(b"")
        else:
            value = parse_canonical_bytes(evidence_path.read_bytes())
            os.chmod(evidence_path, 0o600)
            if mutation == "noncanonical":
                evidence_path.write_bytes(canonical_bytes(value) + b" ")
            elif mutation == "bad-self-digest":
                value["record_digest"] = "0" * 64
                evidence_path.write_bytes(canonical_bytes(value))
            else:
                value["parent_inode"] += 1
                value["record_digest"] = None
                evidence_path.write_bytes(canonical_bytes(with_self_digest(value, "record_digest")))
            os.chmod(evidence_path, 0o400)
        with gate_context as gate:
            with pytest.raises(PublicationError, match="evidence|namespace"):
                invoke(policy_fd, identity, gate, authorization, uid, gid, current, staged)
        assert (root / "policy" / "rollback-floor.json").read_bytes() == current
    finally:
        os.close(policy_fd)
        os.close(root_fd)


def test_reserved_swap_rejects_inode_replacement_after_durable_evidence(tmp_path):
    uid, gid, current, staged, root_fd, policy_fd, identity, authorization, gate_context = opened(tmp_path)
    staged_name = ".rollback-floor.json.txn-123e4567-e89b-42d3-a456-426614174000.tmp"
    try:
        os.unlink(staged_name, dir_fd=policy_fd)
        replacement_fd = os.open(staged_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400, dir_fd=policy_fd)
        try:
            os.write(replacement_fd, staged)
            os.fsync(replacement_fd)
        finally:
            os.close(replacement_fd)
        with gate_context as gate:
            with pytest.raises(PublicationError, match="inode"):
                invoke(policy_fd, identity, gate, authorization, uid, gid, current, staged)
        assert (tmp_path / "policy" / "rollback-floor.json").read_bytes() == current
    finally:
        os.close(policy_fd)
        os.close(root_fd)


def test_reserved_swap_rejects_gate_after_context_exit(tmp_path):
    uid, gid, current, staged, root_fd, policy_fd, identity, authorization, gate_context = opened(tmp_path)
    try:
        with gate_context as gate:
            pass
        with pytest.raises((PublicationError, RootGateError), match="gate|active"):
            invoke(policy_fd, identity, gate, authorization, uid, gid, current, staged)
        assert (tmp_path / "policy" / "rollback-floor.json").read_bytes() == current
    finally:
        os.close(policy_fd)
        os.close(root_fd)
