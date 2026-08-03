from __future__ import annotations

import hashlib
import pytest
from loop_a_protected.canonical import CanonicalJSONError, canonical_bytes, parse_canonical_bytes, with_self_digest


def test_canonical_bytes_uses_utf8_jcs_and_one_lf():
    assert canonical_bytes({"z": 1, "é": "✓"}) == '{"z":1,"é":"✓"}\n'.encode()


def test_canonical_bytes_sorts_keys_by_utf16_code_units():
    assert canonical_bytes({"\ue000": 1, "\U00010000": 2}) == '{"𐀀":2,"":1}\n'.encode()


@pytest.mark.parametrize("value", [1.0, -1, 2**53, "e\u0301", "\ud800"])
def test_canonical_bytes_rejects_forbidden_values(value):
    with pytest.raises(CanonicalJSONError): canonical_bytes({"value": value})


def test_parse_rejects_duplicate_keys():
    with pytest.raises(CanonicalJSONError): parse_canonical_bytes(b'{"x":1,"x":2}\n')


def test_parse_rejects_noncanonical_bytes():
    with pytest.raises(CanonicalJSONError): parse_canonical_bytes(b'{"z":1, "a":2}\n')


def test_self_digest_hashes_explicit_null_preimage():
    value = {"schema": 1, "record_digest": None}
    expected = hashlib.sha256(b'{"record_digest":null,"schema":1}\n').hexdigest()
    assert with_self_digest(value, "record_digest") == {"schema": 1, "record_digest": expected}


def test_self_digest_requires_explicit_null_field():
    with pytest.raises(CanonicalJSONError): with_self_digest({"schema": 1}, "record_digest")
