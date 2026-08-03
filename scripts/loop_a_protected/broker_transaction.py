from __future__ import annotations

import hashlib
import os
import stat
from typing import Callable, Optional

from .broker_coordinator import CommittedCandidate, LiveGate, TransactionBinding
from .candidate_payload import CandidatePayloadError, validate_candidate_payload
from .canonical import canonical_bytes, with_self_digest
from .fd_gateway import CleanMetadataAdapter
from .journal_store import append_journal_record, read_journal_records
from .publication import FaultHook, PublicationError, PublishedFile, publish_directory_tree
from .service_journal import finalize_service_record, finalize_state_evidence
from .validation import validate_digest, validate_timestamp, validate_uuid


class BrokerTransactionError(RuntimeError):
    pass


class BrokerTransactionRecoveryRequired(BrokerTransactionError):
    pass


class JournalCandidateTransaction:
    def __init__(self, *, records_fd: int, candidates_fd: int, uid: int, gid: int,
                 worker_uid: int, metadata: CleanMetadataAdapter, transaction_uuid: str,
                 skill_name: str, runtime_inventory_digest: str, source_byte_count: int,
                 timestamp: Callable[[], str], fault_hook: Optional[FaultHook] = None) -> None:
        validate_uuid(transaction_uuid)
        if not isinstance(skill_name, str) or not skill_name:
            raise BrokerTransactionError("candidate skill identity is invalid")
        validate_digest(runtime_inventory_digest)
        if (isinstance(source_byte_count, bool) or not isinstance(source_byte_count, int)
                or source_byte_count <= 0):
            raise BrokerTransactionError("source byte count is invalid")
        for fd, label in ((records_fd, "records"), (candidates_fd, "candidates")):
            try:
                status = os.fstat(fd)
            except OSError as exc:
                raise BrokerTransactionError(f"{label} descriptor cannot be inspected") from exc
            if not stat.S_ISDIR(status.st_mode):
                raise BrokerTransactionError(f"{label} descriptor is not a directory")
        if not callable(timestamp):
            raise BrokerTransactionError("timestamp source is not callable")
        if (isinstance(uid, bool) or not isinstance(uid, int) or uid < 0
                or isinstance(gid, bool) or not isinstance(gid, int) or gid < 0
                or isinstance(worker_uid, bool) or not isinstance(worker_uid, int) or worker_uid <= 0):
            raise BrokerTransactionError("broker or worker ownership identity is invalid")
        if uid != os.geteuid() or uid == worker_uid:
            raise BrokerTransactionError("canonical publisher must be the distinct effective broker UID")
        for fd, label in ((records_fd, "records"), (candidates_fd, "candidates")):
            status = os.fstat(fd)
            if (status.st_uid, status.st_gid) != (uid, gid):
                raise BrokerTransactionError(f"{label} directory is not broker-owned")
        self.records_fd = records_fd
        self.candidates_fd = candidates_fd
        self.uid = uid
        self.gid = gid
        self.worker_uid = worker_uid
        self.metadata = metadata
        self.transaction_uuid = transaction_uuid
        self.skill_name = skill_name
        self.runtime_inventory_digest = runtime_inventory_digest
        self.source_byte_count = source_byte_count
        self.timestamp = timestamp
        self.fault_hook = fault_hook

    def _records(self):
        records = read_journal_records(
            self.records_fd, self.uid, self.gid, self.metadata,
            journal_kind="service",
        )
        if not records or records[-1].get("transaction_uuid") != self.transaction_uuid:
            raise BrokerTransactionError("service journal transaction differs")
        return records

    def snapshot(self) -> TransactionBinding:
        latest = self._records()[-1]
        source_digest = latest.get("source_digest")
        runtime_manifest_digest = latest.get("runtime_manifest_digest")
        try:
            validate_digest(source_digest)
            validate_digest(runtime_manifest_digest)
        except Exception as exc:
            raise BrokerTransactionError("service journal binding is incomplete") from exc
        return TransactionBinding(
            transaction_uuid=self.transaction_uuid,
            state=latest["state"],
            source_digest=source_digest,
            runtime_manifest_digest=runtime_manifest_digest,
            runtime_inventory_digest=self.runtime_inventory_digest,
        )

    @staticmethod
    def _inventory_item(role: str, relative_path: str, published: PublishedFile):
        return {
            "role": role,
            "relative_path": relative_path,
            "device": published.device,
            "inode": published.inode,
            "mode": published.mode,
            "uid": published.uid,
            "gid": published.gid,
            "link_count": 1,
            "byte_count": published.byte_count,
            "sha256": published.sha256,
        }

    def commit_candidate(self, candidate_bytes: bytes, candidate_sha256: str,
                         gate: LiveGate) -> CommittedCandidate:
        if not isinstance(candidate_bytes, bytes) or not candidate_bytes:
            raise BrokerTransactionError("candidate payload is empty or not bytes")
        validate_digest(candidate_sha256)
        observed_digest = hashlib.sha256(candidate_bytes).hexdigest()
        if observed_digest != candidate_sha256:
            raise BrokerTransactionError("candidate payload digest differs")
        records = self._records()
        latest = records[-1]
        if latest.get("state") != "CANDIDATE_STAGED":
            raise BrokerTransactionError("candidate commit requires exact CANDIDATE_STAGED state")
        try:
            validated_payload = validate_candidate_payload(
                candidate_bytes,
                expected_run_id=self.transaction_uuid,
                expected_skill_name=self.skill_name,
                expected_source_sha256=latest["source_digest"],
            )
        except (CandidatePayloadError, KeyError) as exc:
            raise BrokerTransactionError("candidate payload semantic validation failed") from exc
        if validated_payload.envelope_sha256 != candidate_sha256:
            raise BrokerTransactionError("candidate envelope digest differs after semantic validation")
        if os.listdir(self.candidates_fd):
            raise BrokerTransactionError("candidate directory is not empty before fixed publication")

        generated_at = self.timestamp()
        validate_timestamp(generated_at)
        candidate = with_self_digest({
            "schema": 1,
            "transaction_uuid": self.transaction_uuid,
            "purpose": latest["purpose"],
            "source_digest": latest["source_digest"],
            "source_byte_count": self.source_byte_count,
            "generated_at": generated_at,
            "payload_digest": candidate_sha256,
            "candidate_digest": None,
        }, "candidate_digest")
        candidate_data = canonical_bytes(candidate)
        try:
            gate.assert_live()
            published = publish_directory_tree(
                self.candidates_fd,
                "candidate",
                {
                    "candidate.json": (candidate_data, 0o400),
                    "payload.bin": (candidate_bytes, 0o400),
                },
                0o500,
                self.uid,
                self.gid,
                self.transaction_uuid,
                fault_hook=self.fault_hook,
                metadata=self.metadata,
                gate=gate,
            )
        except PublicationError as exc:
            sequence = latest["sequence"] + 1
            evidence = finalize_state_evidence(
                self.transaction_uuid,
                sequence,
                "RECOVERY_REQUIRED",
                [{"name": "candidate-publication-failed", "passed": False,
                  "detail_digest": candidate_sha256}],
            )
            recovery = dict(latest)
            recovery.update({
                "sequence": sequence,
                "prior_record_digest": latest["record_digest"],
                "state": "RECOVERY_REQUIRED",
                "recorded_at": generated_at,
                "evidence": evidence,
                "record_digest": None,
            })
            recovery = finalize_service_record(recovery)
            try:
                gate.assert_live()
                append_journal_record(
                    self.records_fd, recovery, self.uid, self.gid,
                    self.transaction_uuid, self.metadata, journal_kind="service", gate=gate,
                )
            except Exception as journal_exc:
                raise BrokerTransactionRecoveryRequired(
                    f"candidate publication and durable recovery append failed; reconcile {exc.temp_name}"
                ) from journal_exc
            raise BrokerTransactionRecoveryRequired(
                f"candidate publication failed; reconcile temporary entry {exc.temp_name}"
            ) from exc

        inventory = list(latest["inventory"])
        inventory.extend((
            self._inventory_item(
                "candidate-payload", "candidates/candidate/payload.bin",
                published.children["payload.bin"],
            ),
            self._inventory_item(
                "candidate-record", "candidates/candidate/candidate.json",
                published.children["candidate.json"],
            ),
        ))
        inventory.sort(key=lambda item: item["relative_path"].encode("utf-8"))
        sequence = latest["sequence"] + 1
        evidence = finalize_state_evidence(
            self.transaction_uuid,
            sequence,
            "CANDIDATE_WRITTEN",
            [
                {"name": "broker-result-validated", "passed": True,
                 "detail_digest": candidate_sha256},
                {"name": "candidate-publication-readback", "passed": True,
                 "detail_digest": candidate["candidate_digest"]},
            ],
        )
        next_record = dict(latest)
        next_record.update({
            "sequence": sequence,
            "prior_record_digest": latest["record_digest"],
            "state": "CANDIDATE_WRITTEN",
            "recorded_at": generated_at,
            "candidate_digest": candidate["candidate_digest"],
            "inventory": inventory,
            "evidence": evidence,
            "record_digest": None,
        })
        next_record = finalize_service_record(next_record)
        try:
            gate.assert_live()
            append_journal_record(
                self.records_fd,
                next_record,
                self.uid,
                self.gid,
                self.transaction_uuid,
                self.metadata,
                journal_kind="service",
                gate=gate,
            )
        except Exception as exc:
            try:
                durable_after_failure = self._records()
            except Exception as read_exc:
                raise BrokerTransactionRecoveryRequired(
                    "candidate was published and journal state cannot be reconciled"
                ) from read_exc
            if durable_after_failure[-1] == next_record:
                durable = durable_after_failure
            elif durable_after_failure[-1] == latest:
                recovery_evidence = finalize_state_evidence(
                    self.transaction_uuid,
                    sequence,
                    "RECOVERY_REQUIRED",
                    [{"name": "candidate-written-journal-append-failed", "passed": False,
                      "detail_digest": candidate["candidate_digest"]}],
                )
                recovery = dict(next_record)
                recovery.update({
                    "state": "RECOVERY_REQUIRED",
                    "evidence": recovery_evidence,
                    "record_digest": None,
                })
                recovery = finalize_service_record(recovery)
                try:
                    gate.assert_live()
                    append_journal_record(
                        self.records_fd, recovery, self.uid, self.gid,
                        self.transaction_uuid, self.metadata, journal_kind="service", gate=gate,
                    )
                except Exception as recovery_exc:
                    raise BrokerTransactionRecoveryRequired(
                        "candidate was published and durable recovery append failed"
                    ) from recovery_exc
                raise BrokerTransactionRecoveryRequired(
                    "candidate was published and durably marked RECOVERY_REQUIRED"
                ) from exc
            else:
                raise BrokerTransactionRecoveryRequired(
                    "candidate was published and journal advanced to an unexpected state"
                ) from exc
        else:
            durable = self._records()
        if durable[-1] != next_record:
            raise BrokerTransactionRecoveryRequired("CANDIDATE_WRITTEN durable readback differs")
        payload = published.children["payload.bin"]
        if payload.byte_count != len(candidate_bytes) or payload.sha256 != candidate_sha256:
            raise BrokerTransactionRecoveryRequired("candidate payload publication readback differs")
        return CommittedCandidate(payload.byte_count, payload.sha256)
