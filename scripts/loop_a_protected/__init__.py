"""Hostile-UID protected-runtime protocol kernel (local implementation candidate)."""

from .canonical import CanonicalJSONError, canonical_bytes, parse_canonical_bytes, with_self_digest

__all__ = ["CanonicalJSONError", "canonical_bytes", "parse_canonical_bytes", "with_self_digest"]
