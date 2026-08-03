from __future__ import annotations

import re
import unicodedata
import uuid as uuidlib
from datetime import datetime
from typing import Any, Mapping, Set

_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z")


class ProtocolValidationError(ValueError):
    pass


def _require_nfc(value: str, label: str) -> None:
    if not isinstance(value, str):
        raise ProtocolValidationError(f"{label} must be a string")
    if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
        raise ProtocolValidationError(f"{label} contains a surrogate")
    if unicodedata.normalize("NFC", value) != value:
        raise ProtocolValidationError(f"{label} must be NFC")


def validate_timestamp(value: str) -> str:
    if not isinstance(value, str) or not _TIMESTAMP.fullmatch(value):
        raise ProtocolValidationError("timestamp must be UTC RFC3339 seconds")
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise ProtocolValidationError("timestamp is not a real calendar time") from exc
    return value


def validate_relative_path(value: str) -> str:
    _require_nfc(value, "path")
    if not value or value.startswith("/") or "\\" in value or "\x00" in value:
        raise ProtocolValidationError("path is not protocol-relative")
    if any(component in {"", ".", ".."} for component in value.split("/")):
        raise ProtocolValidationError("path contains an unsafe component")
    return value


def validate_digest(value: str) -> str:
    if not isinstance(value, str) or not _DIGEST.fullmatch(value):
        raise ProtocolValidationError("digest must be lowercase SHA-256 hex")
    return value


def validate_uuid(value: str) -> str:
    if not isinstance(value, str) or value != value.lower():
        raise ProtocolValidationError("UUID must be lowercase canonical text")
    try:
        parsed = uuidlib.UUID(value)
    except (ValueError, AttributeError) as exc:
        raise ProtocolValidationError("invalid UUID") from exc
    if str(parsed) != value:
        raise ProtocolValidationError("UUID must be lowercase canonical text")
    return value


def require_exact_fields(value: Mapping[str, Any], expected: Set[str]) -> None:
    if not isinstance(value, Mapping):
        raise ProtocolValidationError("object must be a mapping")
    actual = set(value)
    if actual != expected:
        raise ProtocolValidationError(f"field mismatch: missing={sorted(expected-actual)}, unknown={sorted(actual-expected)}")
