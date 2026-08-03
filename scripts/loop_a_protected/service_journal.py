from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from .canonical import with_self_digest
from .schedule import ScheduleError, nightly_transaction_uuid, scheduled_window_id
from .schema_bundle import SchemaBundleError, validate_instance
from .states import StateTransitionError, require_service_transition
from .validation import ProtocolValidationError, validate_relative_path


class ServiceJournalError(ValueError):
    pass


COMMITTED_CHAIN = [
    "PREPARED", "SOURCE_CAPTURED", "SMOKE_STARTED", "CANDIDATE_STAGED",
    "CANDIDATE_WRITTEN", "RECEIPT_WRITTEN", "VERIFIED", "COMMITTED",
]
IMMUTABLE_FIELDS = (
    "transaction_uuid", "purpose", "schedule_digest", "scheduled_occurrence", "scheduled_window_id",
    "service_epoch", "service_instance", "runtime_manifest_digest", "skill_manifest_digest",
)


def finalize_state_evidence(transaction_uuid: str, sequence: int, state: str,
                            assertions: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    preimage = {"schema": 1, "transaction_uuid": transaction_uuid, "sequence": sequence, "state": state,
                "assertions": list(assertions), "evidence_digest": None}
    try:
        validate_instance("state-evidence-preimage-v1", preimage)
        finalized = with_self_digest(preimage, "evidence_digest")
        validate_instance("state-evidence-final-v1", finalized)
        return finalized
    except SchemaBundleError as exc:
        raise ServiceJournalError(str(exc)) from exc


def _presence(value: Dict[str, Any], field: str) -> bool:
    return value[field] is not None


def _validate_state_semantics(value: Dict[str, Any]) -> None:
    evidence = value["evidence"]
    try:
        validate_instance("state-evidence-final-v1", evidence)
    except SchemaBundleError as exc:
        raise ServiceJournalError(str(exc)) from exc
    if (evidence["transaction_uuid"], evidence["sequence"], evidence["state"]) != (
        value["transaction_uuid"], value["sequence"], value["state"]
    ):
        raise ServiceJournalError("state evidence binding mismatch")
    inventory = value["inventory"]
    paths = []
    roles = []
    identities = []
    try:
        for item in inventory:
            validate_relative_path(item["relative_path"])
            paths.append(item["relative_path"])
            roles.append(item["role"])
            identities.append((item["device"], item["inode"]))
    except (ProtocolValidationError, KeyError, TypeError) as exc:
        raise ServiceJournalError(str(exc)) from exc
    if paths != sorted(paths, key=lambda path: path.encode("utf-8")) or len(paths) != len(set(paths)):
        raise ServiceJournalError("inventory must be uniquely path-sorted")
    if len(roles) != len(set(roles)) or len(identities) != len(set(identities)):
        raise ServiceJournalError("inventory roles and inode identities must be unique")
    state = value["state"]
    source = _presence(value, "source_digest")
    candidate = _presence(value, "candidate_digest")
    receipt = _presence(value, "receipt_digest")
    if state == "PREPARED" and (source or candidate or receipt):
        raise ServiceJournalError("PREPARED cannot bind source/candidate/receipt")
    if state in {"SOURCE_CAPTURED", "SMOKE_STARTED", "CANDIDATE_STAGED"}:
        if not source or candidate or receipt:
            raise ServiceJournalError(f"{state} has invalid source/candidate/receipt binding")
    if state == "CANDIDATE_WRITTEN" and (not source or not candidate or receipt):
        raise ServiceJournalError("CANDIDATE_WRITTEN requires source and candidate only")
    if state in {"RECEIPT_WRITTEN", "VERIFIED", "COMMITTED"} and not (source and candidate and receipt):
        raise ServiceJournalError(f"{state} requires source, candidate, and receipt")
    purpose = value["purpose"]
    if purpose == "nightly":
        try:
            expected_window = scheduled_window_id(value["schedule_digest"], value["scheduled_occurrence"])
            expected_uuid = nightly_transaction_uuid(expected_window)
        except ScheduleError as exc:
            raise ServiceJournalError(str(exc)) from exc
        if value["scheduled_window_id"] != expected_window or value["transaction_uuid"] != expected_uuid:
            raise ServiceJournalError("nightly deterministic identifiers mismatch")
    elif purpose == "initial-cutover-smoke":
        if any(value[field] is not None for field in ("schedule_digest", "scheduled_occurrence", "scheduled_window_id")):
            raise ServiceJournalError("initial smoke schedule fields must be null")
    else:
        raise ServiceJournalError("unknown service purpose")


def validate_service_record(value: Dict[str, Any]) -> None:
    try:
        validate_instance("service-record-final-v1", value)
    except SchemaBundleError as exc:
        raise ServiceJournalError(str(exc)) from exc
    _validate_state_semantics(value)


def finalize_service_record(preimage: Dict[str, Any]) -> Dict[str, Any]:
    try:
        validate_instance("service-record-preimage-v1", preimage)
    except SchemaBundleError as exc:
        raise ServiceJournalError(str(exc)) from exc
    _validate_state_semantics(preimage)
    finalized = with_self_digest(preimage, "record_digest")
    validate_service_record(finalized)
    return finalized


def validate_service_chain(records: List[Dict[str, Any]]) -> None:
    if not isinstance(records, list) or not records:
        raise ServiceJournalError("service record chain must be nonempty")
    first = records[0]
    for record in records:
        validate_service_record(record)
    if first["sequence"] != 1 or first["prior_record_digest"] is not None or first["state"] != "PREPARED":
        raise ServiceJournalError("service chain must start with PREPARED sequence 1")
    immutable = {field: first[field] for field in IMMUTABLE_FIELDS}
    for index, record in enumerate(records):
        if record["sequence"] != index + 1:
            raise ServiceJournalError("service sequence gap or duplicate")
        if any(record[field] != expected for field, expected in immutable.items()):
            raise ServiceJournalError("immutable service field changed")
        if index:
            prior = records[index - 1]
            if record["prior_record_digest"] != prior["record_digest"]:
                raise ServiceJournalError("service prior-record digest mismatch")
            try:
                require_service_transition(prior["state"], record["state"])
            except StateTransitionError as exc:
                raise ServiceJournalError(str(exc)) from exc
    states = [record["state"] for record in records]
    if records[-1]["state"] == "COMMITTED" and states != COMMITTED_CHAIN:
        raise ServiceJournalError("COMMITTED requires the exact eight-state chain")
    if "RECOVERY_REQUIRED" in states and records[-1]["state"] not in {"RECOVERY_REQUIRED", "ROLLED_BACK"}:
        raise ServiceJournalError("recovery chain can only remain fenced or roll back")
