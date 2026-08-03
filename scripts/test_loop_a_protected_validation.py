from __future__ import annotations

import pytest
from loop_a_protected.validation import ProtocolValidationError, require_exact_fields, validate_digest, validate_relative_path, validate_timestamp, validate_uuid


def test_timestamp_accepts_real_utc_second():
    assert validate_timestamp("2026-08-03T01:02:03Z") == "2026-08-03T01:02:03Z"


@pytest.mark.parametrize("value", ["2026-02-29T00:00:00Z", "2026-08-03T01:02:03.1Z", "2026-08-03T01:02:03+00:00", ""])
def test_timestamp_rejects_noncanonical_or_impossible_values(value):
    with pytest.raises(ProtocolValidationError): validate_timestamp(value)


def test_relative_path_accepts_nfc_components():
    assert validate_relative_path("skills/café/SKILL.md") == "skills/café/SKILL.md"


@pytest.mark.parametrize("value", ["", "/tmp/x", "a//b", "a/./b", "a/../b", "a\\b", "a\x00b", "cafe\u0301"])
def test_relative_path_rejects_unsafe_or_noncanonical_values(value):
    with pytest.raises(ProtocolValidationError): validate_relative_path(value)


def test_digest_requires_lowercase_sha256_hex():
    value = "ab" * 32
    assert validate_digest(value) == value
    with pytest.raises(ProtocolValidationError): validate_digest(value.upper())


def test_uuid_requires_lowercase_canonical_rfc4122_text():
    value = "123e4567-e89b-42d3-a456-426614174000"
    assert validate_uuid(value) == value
    with pytest.raises(ProtocolValidationError): validate_uuid(value.upper())


def test_exact_fields_rejects_unknown_and_omitted_optional_fields():
    require_exact_fields({"schema": 1, "note": None}, {"schema", "note"})
    with pytest.raises(ProtocolValidationError): require_exact_fields({"schema": 1}, {"schema", "note"})
    with pytest.raises(ProtocolValidationError): require_exact_fields({"schema": 1, "note": None, "extra": 1}, {"schema", "note"})
