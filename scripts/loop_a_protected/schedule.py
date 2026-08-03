from __future__ import annotations

import hashlib
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

from .canonical import canonical_bytes, with_self_digest
from .validation import ProtocolValidationError, require_exact_fields, validate_digest

_NAMESPACE = uuid.UUID("62cc109f-5d56-5a4d-b6e9-1357d0d25dcf")
_HHMM = re.compile(r"([01][0-9]|2[0-3]):([0-5][0-9])\Z")
_OCCURRENCE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:00Z\Z")
_FIELDS = {"schema", "daily_utc_hhmm", "admission_seconds", "schedule_digest"}


class ScheduleError(ValueError):
    pass


def _validate_schedule(value: Dict[str, Any], finalized: bool) -> Tuple[int, int, int]:
    try:
        require_exact_fields(value, _FIELDS)
    except ProtocolValidationError as exc:
        raise ScheduleError(str(exc)) from exc
    if value["schema"] != 1:
        raise ScheduleError("unknown schedule schema")
    match = _HHMM.fullmatch(value["daily_utc_hhmm"]) if isinstance(value["daily_utc_hhmm"], str) else None
    if match is None:
        raise ScheduleError("daily_utc_hhmm must be zero-padded UTC HH:MM")
    hour, minute = map(int, match.groups())
    seconds = value["admission_seconds"]
    if isinstance(seconds, bool) or not isinstance(seconds, int) or not 1 <= seconds <= 3600:
        raise ScheduleError("admission_seconds outside 1..3600")
    if hour * 3600 + minute * 60 + seconds > 86400:
        raise ScheduleError("admission window crosses next UTC day")
    if finalized:
        try:
            digest = validate_digest(value["schedule_digest"])
        except ProtocolValidationError as exc:
            raise ScheduleError(str(exc)) from exc
        preimage = dict(value)
        preimage["schedule_digest"] = None
        if hashlib.sha256(canonical_bytes(preimage)).hexdigest() != digest:
            raise ScheduleError("schedule_digest mismatch")
    elif value["schedule_digest"] is not None:
        raise ScheduleError("schedule_digest must be null in preimage")
    return hour, minute, seconds


def finalize_schedule(daily_utc_hhmm: str, admission_seconds: int) -> Dict[str, Any]:
    preimage = {"schema": 1, "daily_utc_hhmm": daily_utc_hhmm,
                "admission_seconds": admission_seconds, "schedule_digest": None}
    _validate_schedule(preimage, finalized=False)
    return with_self_digest(preimage, "schedule_digest")


def scheduled_window_id(schedule_digest: str, occurrence: str) -> str:
    try:
        validate_digest(schedule_digest)
    except ProtocolValidationError as exc:
        raise ScheduleError(str(exc)) from exc
    if not isinstance(occurrence, str) or not _OCCURRENCE.fullmatch(occurrence):
        raise ScheduleError("occurrence must be an exact UTC minute")
    try:
        datetime.strptime(occurrence, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise ScheduleError("occurrence is not a real calendar minute") from exc
    preimage = b"nightly-v1\0" + schedule_digest.encode("ascii") + b"\0" + occurrence.encode("ascii")
    return hashlib.sha256(preimage).hexdigest()


def nightly_transaction_uuid(window_id: str) -> str:
    try:
        validate_digest(window_id)
    except ProtocolValidationError as exc:
        raise ScheduleError(str(exc)) from exc
    return str(uuid.uuid5(_NAMESPACE, window_id))


def admit_nightly(schedule: Dict[str, Any], now: datetime) -> Optional[Tuple[str, str, str]]:
    hour, minute, seconds = _validate_schedule(schedule, finalized=True)
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() != timedelta(0):
        raise ScheduleError("trusted clock must be timezone-aware UTC")
    now = now.astimezone(timezone.utc)
    occurrence_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if occurrence_dt > now:
        occurrence_dt -= timedelta(days=1)
    if not occurrence_dt <= now < occurrence_dt + timedelta(seconds=seconds):
        return None
    occurrence = occurrence_dt.strftime("%Y-%m-%dT%H:%M:00Z")
    window = scheduled_window_id(schedule["schedule_digest"], occurrence)
    return occurrence, window, nightly_transaction_uuid(window)
