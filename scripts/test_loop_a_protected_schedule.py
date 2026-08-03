from __future__ import annotations

from datetime import datetime, timezone

import pytest

from loop_a_protected.schedule import (
    ScheduleError,
    admit_nightly,
    finalize_schedule,
    nightly_transaction_uuid,
    scheduled_window_id,
)


def test_nightly_admission_is_half_open_and_deterministic():
    schedule = finalize_schedule("01:30", 600)
    occurrence = "2026-08-03T01:30:00Z"
    expected_window = scheduled_window_id(schedule["schedule_digest"], occurrence)
    expected_uuid = nightly_transaction_uuid(expected_window)
    at_start = admit_nightly(schedule, datetime(2026, 8, 3, 1, 30, tzinfo=timezone.utc))
    before_end = admit_nightly(schedule, datetime(2026, 8, 3, 1, 39, 59, tzinfo=timezone.utc))
    assert at_start == before_end == (occurrence, expected_window, expected_uuid)
    assert admit_nightly(schedule, datetime(2026, 8, 3, 1, 40, tzinfo=timezone.utc)) is None


def test_same_occurrence_identity_does_not_accept_epoch_or_service_instance():
    schedule = finalize_schedule("01:30", 600)
    occurrence = "2026-08-03T01:30:00Z"
    first = nightly_transaction_uuid(scheduled_window_id(schedule["schedule_digest"], occurrence))
    second = nightly_transaction_uuid(scheduled_window_id(schedule["schedule_digest"], occurrence))
    assert first == second


@pytest.mark.parametrize("hhmm,seconds", [("1:30", 10), ("24:00", 10), ("23:59", 61), ("00:00", 0), ("00:00", 3601)])
def test_schedule_rejects_noncanonical_or_cross_day_windows(hhmm, seconds):
    with pytest.raises(ScheduleError):
        finalize_schedule(hhmm, seconds)


def test_schedule_rejects_naive_or_non_utc_clock():
    schedule = finalize_schedule("01:30", 600)
    with pytest.raises(ScheduleError):
        admit_nightly(schedule, datetime(2026, 8, 3, 1, 30))
    with pytest.raises(ScheduleError):
        scheduled_window_id(schedule["schedule_digest"], "2026-08-03T01:30:01Z")
