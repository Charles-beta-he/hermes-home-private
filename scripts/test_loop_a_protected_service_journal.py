from __future__ import annotations

import pytest

from loop_a_protected.schedule import finalize_schedule, nightly_transaction_uuid, scheduled_window_id
from loop_a_protected.service_journal import (
    ServiceJournalError,
    finalize_service_record,
    finalize_state_evidence,
    validate_service_chain,
)

D0 = "0" * 64
D1 = "1" * 64
D2 = "2" * 64
INSTANCE = "123e4567-e89b-42d3-a456-426614174001"
OCCURRENCE = "2026-08-03T01:00:00Z"
SCHEDULE = finalize_schedule("01:00", 300)
WINDOW = scheduled_window_id(SCHEDULE["schedule_digest"], OCCURRENCE)
TXN = nightly_transaction_uuid(WINDOW)


HAPPY = ["PREPARED", "SOURCE_CAPTURED", "SMOKE_STARTED", "CANDIDATE_STAGED",
         "CANDIDATE_WRITTEN", "RECEIPT_WRITTEN", "VERIFIED", "COMMITTED"]


def fields(state, sequence, prior):
    source = D0 if state not in {"PREPARED"} else None
    candidate = D1 if state in {"CANDIDATE_WRITTEN", "RECEIPT_WRITTEN", "VERIFIED", "COMMITTED"} else None
    receipt = D2 if state in {"RECEIPT_WRITTEN", "VERIFIED", "COMMITTED"} else None
    evidence = finalize_state_evidence(TXN, sequence, state, [
        {"name": "held-fd-readback", "passed": True, "detail_digest": D0}
    ])
    return {
        "schema": 1, "transaction_uuid": TXN, "sequence": sequence, "purpose": "nightly",
        "schedule_digest": SCHEDULE["schedule_digest"], "scheduled_occurrence": OCCURRENCE,
        "scheduled_window_id": WINDOW, "service_epoch": 1, "service_instance": INSTANCE,
        "prior_record_digest": prior, "state": state,
        "recorded_at": f"2026-08-03T01:00:{sequence:02d}Z",
        "runtime_manifest_digest": D0, "skill_manifest_digest": D1,
        "source_digest": source, "candidate_digest": candidate, "receipt_digest": receipt,
        "inventory": [], "evidence": evidence, "record_digest": None,
    }


def happy_chain():
    result = []
    prior = None
    for sequence, state in enumerate(HAPPY, 1):
        record = finalize_service_record(fields(state, sequence, prior))
        result.append(record)
        prior = record["record_digest"]
    return result


EXPECTED_RECORD_FIELDS = {
    "schema", "transaction_uuid", "sequence", "purpose", "schedule_digest", "scheduled_occurrence",
    "scheduled_window_id", "service_epoch", "service_instance", "prior_record_digest", "state",
    "recorded_at", "runtime_manifest_digest", "skill_manifest_digest", "source_digest",
    "candidate_digest", "receipt_digest", "inventory", "evidence", "record_digest",
}


def test_service_record_uses_frozen_v7_exact_field_vocabulary():
    assert set(fields("PREPARED", 1, None)) == EXPECTED_RECORD_FIELDS


def test_exact_eight_state_committed_chain_is_digest_bound_and_valid():
    chain = happy_chain()
    validate_service_chain(chain)
    assert [record["state"] for record in chain] == HAPPY
    assert chain[-1]["record_digest"]


def test_chain_rejects_gap_prior_substitution_and_immutable_change():
    chain = happy_chain()
    for index, replacement in ((2, {"prior_record_digest": D0}), (3, {"service_epoch": 2})):
        forged = list(chain)
        forged[index] = dict(forged[index], **replacement)
        with pytest.raises(ServiceJournalError):
            validate_service_chain(forged)
    with pytest.raises(ServiceJournalError):
        validate_service_chain(chain[:3] + chain[4:])


def test_state_dependent_digest_rules_and_forbidden_shortcuts_fail_closed():
    bad = fields("CANDIDATE_WRITTEN", 1, None)
    bad["candidate_digest"] = None
    with pytest.raises(ServiceJournalError, match="candidate"):
        finalize_service_record(bad)

    prepared = finalize_service_record(fields("PREPARED", 1, None))
    direct = finalize_service_record(fields("COMMITTED", 2, prepared["record_digest"]))
    with pytest.raises(ServiceJournalError):
        validate_service_chain([prepared, direct])


def test_recovery_required_can_only_terminate_as_rolled_back():
    prepared = finalize_service_record(fields("PREPARED", 1, None))
    recovery = finalize_service_record(fields("RECOVERY_REQUIRED", 2, prepared["record_digest"]))
    committed_fields = fields("COMMITTED", 3, recovery["record_digest"])
    committed_fields.update(source_digest=D0, candidate_digest=D1, receipt_digest=D2)
    committed = finalize_service_record(committed_fields)
    with pytest.raises(ServiceJournalError):
        validate_service_chain([prepared, recovery, committed])

    rolled_fields = fields("ROLLED_BACK", 3, recovery["record_digest"])
    rolled = finalize_service_record(rolled_fields)
    validate_service_chain([prepared, recovery, rolled])


def test_nightly_identifiers_are_recomputed_not_trusted():
    bad = fields("PREPARED", 1, None)
    bad["transaction_uuid"] = INSTANCE
    bad["evidence"] = finalize_state_evidence(INSTANCE, 1, "PREPARED", [])
    with pytest.raises(ServiceJournalError, match="deterministic"):
        finalize_service_record(bad)
