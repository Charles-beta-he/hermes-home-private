from __future__ import annotations

import pytest

from loop_a_protected.service_journal import finalize_service_record
from loop_a_protected.service_reconciler import ReconciliationError, reconcile_service_state
from test_loop_a_protected_service_journal import HAPPY, fields, happy_chain


def records_at(state):
    if state in HAPPY:
        chain = happy_chain()
        return chain[:HAPPY.index(state) + 1]
    prepared = finalize_service_record(fields("PREPARED", 1, None))
    second = finalize_service_record(fields(state, 2, prepared["record_digest"]))
    return [prepared, second]

BASE = {
    "source": "absent", "candidate_temp": "absent", "candidate": "absent", "receipt": "absent",
    "namespace_exact": True, "runtime_converges": False, "same_live_invocation": False,
}


def observed(**changes):
    return dict(BASE, **changes)


@pytest.mark.parametrize("state,observation,actions", [
    ("PREPARED", observed(), ("APPEND_ABORTED",)),
    ("PREPARED", observed(source="exact"), ("APPEND_SOURCE_CAPTURED", "APPEND_ABORTED")),
    ("SOURCE_CAPTURED", observed(source="exact"), ("APPEND_ABORTED",)),
    ("SOURCE_CAPTURED", observed(source="exact", same_live_invocation=True), ("CONTINUE_SMOKE",)),
    ("SMOKE_STARTED", observed(source="exact"), ("APPEND_ABORTED",)),
    ("CANDIDATE_STAGED", observed(source="exact", candidate_temp="exact"),
     ("DELETE_HELD_TEMP", "FSYNC_PARENT", "APPEND_ABORTED")),
    ("CANDIDATE_WRITTEN", observed(source="exact", candidate="exact"),
     ("PUBLISH_DETERMINISTIC_FAIL_RECEIPT", "FSYNC_PARENT", "APPEND_RECEIPT_WRITTEN", "APPEND_ABORTED")),
    ("CANDIDATE_WRITTEN", observed(source="exact", candidate="exact", receipt="exact-fail"),
     ("APPEND_RECEIPT_WRITTEN", "APPEND_ABORTED")),
    ("RECEIPT_WRITTEN", observed(source="exact", candidate="exact", receipt="exact-pass"),
     ("APPEND_VERIFIED",)),
    ("RECEIPT_WRITTEN", observed(source="exact", candidate="exact", receipt="exact-fail"),
     ("APPEND_ABORTED",)),
    ("VERIFIED", observed(source="exact", candidate="exact", receipt="exact-pass", runtime_converges=True),
     ("APPEND_COMMITTED",)),
])
def test_frozen_v7_service_reconciliation_table(state, observation, actions):
    assert reconcile_service_state(records_at(state), observation) == actions


@pytest.mark.parametrize("state,observation", [
    ("PREPARED", observed(source="other")),
    ("CANDIDATE_STAGED", observed(source="exact", candidate_temp="other")),
    ("CANDIDATE_WRITTEN", observed(source="exact", candidate="exact", receipt="other")),
    ("RECEIPT_WRITTEN", observed(source="exact", candidate="exact", receipt="other")),
    ("VERIFIED", observed(source="exact", candidate="exact", receipt="exact-pass", runtime_converges=False)),
])
def test_mismatch_appends_recovery_required(state, observation):
    assert reconcile_service_state(records_at(state), observation) == ("APPEND_RECOVERY_REQUIRED",)


def test_terminal_or_recovery_state_requires_valid_chain_and_exact_committed_closure():
    committed = records_at("COMMITTED")
    assert reconcile_service_state(committed, observed()) == ("HUMAN_RECOVERY",)
    exact = observed(source="exact", candidate="exact", receipt="exact-pass", runtime_converges=True)
    assert reconcile_service_state(committed, exact) == ("NO_ACTION",)
    assert reconcile_service_state(records_at("RECOVERY_REQUIRED"), observed()) == ("HUMAN_RECOVERY",)
    assert reconcile_service_state(records_at("ABORTED"), observed(namespace_exact=False)) == ("HUMAN_RECOVERY",)
    forged = list(committed)
    forged[-1] = dict(forged[-1], prior_record_digest="0" * 64)
    with pytest.raises(ReconciliationError, match="chain"):
        reconcile_service_state(forged, exact)


def test_observation_shape_is_exact_and_unknown_values_fail_closed():
    with pytest.raises(ReconciliationError):
        reconcile_service_state(records_at("PREPARED"), dict(BASE, extra=True))
    with pytest.raises(ReconciliationError):
        reconcile_service_state(records_at("PREPARED"), observed(source="maybe"))
