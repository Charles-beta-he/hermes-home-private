from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .service_journal import ServiceJournalError, validate_service_chain


class ReconciliationError(ValueError):
    pass


_FIELDS = {
    "source", "candidate_temp", "candidate", "receipt", "namespace_exact",
    "runtime_converges", "same_live_invocation",
}
_VALUES = {
    "source": {"absent", "exact", "other"},
    "candidate_temp": {"absent", "exact", "other"},
    "candidate": {"absent", "exact", "other"},
    "receipt": {"absent", "exact-pass", "exact-fail", "other"},
}
_TERMINAL = {"COMMITTED", "ABORTED", "ROLLED_BACK"}


def _validate_observation(value: Dict[str, Any]) -> None:
    if not isinstance(value, dict) or set(value) != _FIELDS:
        raise ReconciliationError("service observation fields differ from exact schema")
    for field, allowed in _VALUES.items():
        if value[field] not in allowed:
            raise ReconciliationError(f"unknown service observation value for {field}")
    for field in ("namespace_exact", "runtime_converges", "same_live_invocation"):
        if not isinstance(value[field], bool):
            raise ReconciliationError(f"{field} must be boolean")


def _recovery() -> Tuple[str, ...]:
    return ("APPEND_RECOVERY_REQUIRED",)


def reconcile_service_state(records: List[Dict[str, Any]], observation: Dict[str, Any]) -> Tuple[str, ...]:
    _validate_observation(observation)
    try:
        validate_service_chain(records)
    except ServiceJournalError as exc:
        raise ReconciliationError("service chain is invalid") from exc
    state = records[-1]["state"]
    if state == "COMMITTED":
        complete = (
            observation["namespace_exact"] and observation["source"] == "exact" and
            observation["candidate_temp"] == "absent" and observation["candidate"] == "exact" and
            observation["receipt"] == "exact-pass" and observation["runtime_converges"]
        )
        return ("NO_ACTION",) if complete else ("HUMAN_RECOVERY",)
    if state in {"ABORTED", "ROLLED_BACK"}:
        return ("NO_ACTION",) if observation["namespace_exact"] else ("HUMAN_RECOVERY",)
    if state == "RECOVERY_REQUIRED":
        return ("HUMAN_RECOVERY",)
    if state == "PREPARED":
        if not observation["namespace_exact"] or any(observation[field] != "absent" for field in ("candidate_temp", "candidate", "receipt")):
            return _recovery()
        if observation["source"] == "absent":
            return ("APPEND_ABORTED",)
        if observation["source"] == "exact":
            return ("APPEND_SOURCE_CAPTURED", "APPEND_ABORTED")
        return _recovery()
    if state == "SOURCE_CAPTURED":
        if (not observation["namespace_exact"] or observation["source"] != "exact" or
                any(observation[field] != "absent" for field in ("candidate_temp", "candidate", "receipt"))):
            return _recovery()
        return ("CONTINUE_SMOKE",) if observation["same_live_invocation"] else ("APPEND_ABORTED",)
    if state == "SMOKE_STARTED":
        if (observation["namespace_exact"] and observation["source"] == "exact" and
                all(observation[field] == "absent" for field in ("candidate_temp", "candidate", "receipt"))):
            return ("APPEND_ABORTED",)
        return _recovery()
    if state == "CANDIDATE_STAGED":
        if (observation["namespace_exact"] and observation["source"] == "exact" and
                observation["candidate_temp"] == "exact" and observation["candidate"] == "absent" and
                observation["receipt"] == "absent"):
            return ("DELETE_HELD_TEMP", "FSYNC_PARENT", "APPEND_ABORTED")
        return _recovery()
    if state == "CANDIDATE_WRITTEN":
        if (not observation["namespace_exact"] or observation["source"] != "exact" or
                observation["candidate_temp"] != "absent" or observation["candidate"] != "exact"):
            return _recovery()
        if observation["receipt"] == "absent":
            return ("PUBLISH_DETERMINISTIC_FAIL_RECEIPT", "FSYNC_PARENT", "APPEND_RECEIPT_WRITTEN", "APPEND_ABORTED")
        if observation["receipt"] == "exact-fail":
            return ("APPEND_RECEIPT_WRITTEN", "APPEND_ABORTED")
        return _recovery()
    if state == "RECEIPT_WRITTEN":
        if (not observation["namespace_exact"] or observation["source"] != "exact" or
                observation["candidate_temp"] != "absent" or observation["candidate"] != "exact"):
            return _recovery()
        if observation["receipt"] == "exact-pass":
            return ("APPEND_VERIFIED",)
        if observation["receipt"] == "exact-fail":
            return ("APPEND_ABORTED",)
        return _recovery()
    if state == "VERIFIED":
        if (observation["namespace_exact"] and observation["source"] == "exact" and
                observation["candidate_temp"] == "absent" and observation["candidate"] == "exact" and
                observation["receipt"] == "exact-pass" and observation["runtime_converges"]):
            return ("APPEND_COMMITTED",)
        return _recovery()
    raise ReconciliationError("unknown service state")
