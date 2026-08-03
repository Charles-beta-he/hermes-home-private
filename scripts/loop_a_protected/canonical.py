from __future__ import annotations

import hashlib
import json
import unicodedata
from typing import Any, Dict, List, Tuple

MAX_SAFE_INTEGER = 2**53 - 1


class CanonicalJSONError(ValueError):
    pass


def _check_string(value: str) -> None:
    if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
        raise CanonicalJSONError("unpaired Unicode surrogate")
    if unicodedata.normalize("NFC", value) != value:
        raise CanonicalJSONError("string is not NFC")


def _validated(value: Any) -> Any:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int):
        if value < 0 or value > MAX_SAFE_INTEGER:
            raise CanonicalJSONError("integer outside protocol range")
        return value
    if isinstance(value, str):
        _check_string(value)
        return value
    if isinstance(value, list):
        return [_validated(item) for item in value]
    if isinstance(value, dict):
        ordered: Dict[str, Any] = {}
        for key in value:
            if not isinstance(key, str):
                raise CanonicalJSONError("object key is not a string")
            _check_string(key)
        for key in sorted(value, key=lambda item: item.encode("utf-16-be")):
            ordered[key] = _validated(value[key])
        return ordered
    raise CanonicalJSONError(f"unsupported JSON value: {type(value).__name__}")


def canonical_bytes(value: Any) -> bytes:
    try:
        body = json.dumps(_validated(value), ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")
    except (UnicodeError, ValueError) as exc:
        raise CanonicalJSONError(str(exc)) from exc
    return body + b"\n"


def _reject_duplicate_pairs(pairs: List[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CanonicalJSONError(f"duplicate key: {key}")
        result[key] = value
    return result


def _parse_int(token: str) -> int:
    value = int(token)
    if value < 0 or value > MAX_SAFE_INTEGER:
        raise CanonicalJSONError("integer outside protocol range")
    return value


def _reject_number(token: str) -> None:
    raise CanonicalJSONError(f"forbidden numeric value: {token}")


def parse_canonical_bytes(data: bytes) -> Any:
    if not isinstance(data, bytes) or not data.endswith(b"\n") or data.endswith(b"\n\n"):
        raise CanonicalJSONError("canonical JSON must end in exactly one LF")
    try:
        text = data[:-1].decode("utf-8")
        if text.startswith("\ufeff"):
            raise CanonicalJSONError("UTF-8 BOM is forbidden")
        value = json.loads(text, object_pairs_hook=_reject_duplicate_pairs, parse_int=_parse_int,
                           parse_float=_reject_number, parse_constant=_reject_number)
    except (UnicodeError, json.JSONDecodeError, CanonicalJSONError) as exc:
        if isinstance(exc, CanonicalJSONError):
            raise
        raise CanonicalJSONError(str(exc)) from exc
    if canonical_bytes(value) != data:
        raise CanonicalJSONError("JSON bytes are not canonical")
    return value


def with_self_digest(value: Dict[str, Any], field: str) -> Dict[str, Any]:
    if field not in value or value[field] is not None:
        raise CanonicalJSONError(f"{field} must be explicit null in digest preimage")
    finalized = dict(value)
    finalized[field] = hashlib.sha256(canonical_bytes(value)).hexdigest()
    canonical_bytes(finalized)
    return finalized
