from __future__ import annotations

import hashlib
import re
import uuid
from typing import Any, Dict

from .canonical import canonical_bytes
from .schema_bundle import SchemaBundleError, validate_instance


class BrokerResultError(ValueError):
    pass


_KEYS = {
    "schema", "nonce", "child_pid", "transaction_uuid", "source_digest",
    "runtime_manifest_digest", "runtime_inventory_digest",
    "candidate_sha256", "candidate_byte_count", "result_digest",
}
_DIGEST = re.compile(r"[0-9a-f]{64}")


def validate_worker_result(*, record: Dict[str, Any], candidate_bytes: bytes,
                           expected_nonce: str, expected_child_pid: int,
                           expected_transaction_uuid: str,
                           expected_source_digest: str,
                           expected_runtime_manifest_digest: str,
                           expected_runtime_inventory_digest: str,
                           maximum_candidate_bytes: int = 8_388_608) -> Dict[str, Any]:
    if not isinstance(record, dict) or set(record) != _KEYS:
        raise BrokerResultError("worker result fields are not exact")
    try:
        validate_instance("broker-result-final-v1", record)
    except SchemaBundleError as exc:
        raise BrokerResultError("worker result schema or self-digest is invalid") from exc
    if record["schema"] != 1 or isinstance(record["schema"], bool):
        raise BrokerResultError("worker result schema is invalid")
    if (not isinstance(record["nonce"], str) or record["nonce"] != expected_nonce
            or _DIGEST.fullmatch(record["nonce"]) is None):
        raise BrokerResultError("worker result nonce differs")
    if record["child_pid"] != expected_child_pid or isinstance(record["child_pid"], bool) or expected_child_pid <= 0:
        raise BrokerResultError("worker result PID differs")
    try:
        parsed_transaction = str(uuid.UUID(record["transaction_uuid"]))
    except (ValueError, TypeError, AttributeError) as exc:
        raise BrokerResultError("worker result transaction UUID is invalid") from exc
    if parsed_transaction != expected_transaction_uuid or record["transaction_uuid"] != parsed_transaction:
        raise BrokerResultError("worker result transaction differs")
    if (not isinstance(record["source_digest"], str)
            or record["source_digest"] != expected_source_digest
            or _DIGEST.fullmatch(record["source_digest"]) is None):
        raise BrokerResultError("worker result source digest differs")
    for field, expected, label in (
        ("runtime_manifest_digest", expected_runtime_manifest_digest, "runtime manifest"),
        ("runtime_inventory_digest", expected_runtime_inventory_digest, "runtime inventory"),
    ):
        if (not isinstance(record[field], str) or record[field] != expected
                or _DIGEST.fullmatch(record[field]) is None):
            raise BrokerResultError(f"worker result {label} digest differs")
    if not isinstance(candidate_bytes, bytes) or not 1 <= len(candidate_bytes) <= maximum_candidate_bytes:
        raise BrokerResultError("worker candidate byte count is outside the fixed bound")
    if record["candidate_byte_count"] != len(candidate_bytes) or isinstance(record["candidate_byte_count"], bool):
        raise BrokerResultError("worker candidate byte count differs")
    observed_digest = hashlib.sha256(candidate_bytes).hexdigest()
    if record["candidate_sha256"] != observed_digest:
        raise BrokerResultError("worker candidate digest differs")
    canonical_bytes(record)
    return dict(record)
