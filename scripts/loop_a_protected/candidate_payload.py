from __future__ import annotations

import base64
import hashlib
import json
import re
from dataclasses import dataclass


class CandidatePayloadError(ValueError):
    pass


_SCHEMA = "hermes.dreaming.candidate.v2"
_KEYS = {
    "candidate_bytes_b64",
    "candidate_sha256",
    "candidate_size",
    "run_id",
    "schema_version",
    "skill_name",
    "source_sha256",
}
_DIGEST = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True)
class ValidatedCandidatePayload:
    envelope_sha256: str
    candidate_sha256: str
    candidate_size: int
    candidate_bytes: bytes


def canonical_candidate_payload(*, run_id: str, skill_name: str,
                                source_sha256: str, candidate_bytes: bytes) -> bytes:
    if not isinstance(run_id, str) or not run_id:
        raise CandidatePayloadError("candidate run identity is invalid")
    if not isinstance(skill_name, str) or not skill_name:
        raise CandidatePayloadError("candidate skill identity is invalid")
    if not isinstance(source_sha256, str) or _DIGEST.fullmatch(source_sha256) is None:
        raise CandidatePayloadError("candidate source digest is invalid")
    if not isinstance(candidate_bytes, bytes) or not candidate_bytes:
        raise CandidatePayloadError("candidate content is empty or not bytes")
    try:
        candidate_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CandidatePayloadError("candidate content is not UTF-8") from exc
    value = {
        "candidate_bytes_b64": base64.b64encode(candidate_bytes).decode("ascii"),
        "candidate_sha256": hashlib.sha256(candidate_bytes).hexdigest(),
        "candidate_size": len(candidate_bytes),
        "run_id": run_id,
        "schema_version": _SCHEMA,
        "skill_name": skill_name,
        "source_sha256": source_sha256,
    }
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def validate_candidate_payload(envelope: bytes, *, expected_run_id: str,
                               expected_skill_name: str,
                               expected_source_sha256: str,
                               maximum_candidate_bytes: int = 8_388_608) -> ValidatedCandidatePayload:
    if not isinstance(envelope, bytes) or not 1 <= len(envelope) <= maximum_candidate_bytes:
        raise CandidatePayloadError("candidate envelope byte count is outside the fixed bound")
    try:
        text = envelope.decode("utf-8")
        if not text.endswith("\n") or "\n" in text[:-1]:
            raise CandidatePayloadError("candidate envelope framing is not canonical")
        value = json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CandidatePayloadError("candidate envelope is not canonical UTF-8 JSON") from exc
    if not isinstance(value, dict) or set(value) != _KEYS:
        raise CandidatePayloadError("candidate envelope fields are not exact")
    if value.get("schema_version") != _SCHEMA:
        raise CandidatePayloadError("candidate envelope schema differs")
    if value.get("run_id") != expected_run_id or not isinstance(value.get("run_id"), str):
        raise CandidatePayloadError("candidate run identity differs")
    if value.get("skill_name") != expected_skill_name or not isinstance(value.get("skill_name"), str):
        raise CandidatePayloadError("candidate skill identity differs")
    if (value.get("source_sha256") != expected_source_sha256
            or not isinstance(value.get("source_sha256"), str)
            or _DIGEST.fullmatch(value["source_sha256"]) is None):
        raise CandidatePayloadError("candidate source digest differs")
    if (not isinstance(value.get("candidate_sha256"), str)
            or _DIGEST.fullmatch(value["candidate_sha256"]) is None):
        raise CandidatePayloadError("candidate content digest is invalid")
    size = value.get("candidate_size")
    if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
        raise CandidatePayloadError("candidate content size is invalid")
    encoded = value.get("candidate_bytes_b64")
    if not isinstance(encoded, str):
        raise CandidatePayloadError("candidate content encoding is invalid")
    try:
        candidate = base64.b64decode(encoded, validate=True)
        candidate.decode("utf-8")
    except (ValueError, UnicodeDecodeError) as exc:
        raise CandidatePayloadError("candidate content is not strict Base64 UTF-8") from exc
    if len(candidate) != size or hashlib.sha256(candidate).hexdigest() != value["candidate_sha256"]:
        raise CandidatePayloadError("candidate content size or digest differs")
    rebuilt = canonical_candidate_payload(
        run_id=expected_run_id,
        skill_name=expected_skill_name,
        source_sha256=expected_source_sha256,
        candidate_bytes=candidate,
    )
    if rebuilt != envelope:
        raise CandidatePayloadError("candidate envelope bytes are not canonical")
    return ValidatedCandidatePayload(
        envelope_sha256=hashlib.sha256(envelope).hexdigest(),
        candidate_sha256=value["candidate_sha256"],
        candidate_size=size,
        candidate_bytes=candidate,
    )
